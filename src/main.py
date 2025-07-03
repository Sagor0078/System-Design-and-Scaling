import pandas as pd
import re
import numpy as np
from typing import List, Tuple, Dict, Any
import google.generativeai as genai
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
from pathlib import Path
import logging

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarkdownTableCorrector:
    
    def __init__(self, GEMINI_API_KEY: str = None):
        self.GEMINI_API_KEY = GEMINI_API_KEY
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def load_data(self, csv_path: str = None, data: pd.DataFrame = None) -> pd.DataFrame:
        if data is not None:
            return data
        elif csv_path and os.path.exists("/home/sagor/ML/error-free-markdown/data.csv"):
            return pd.read_csv("/home/sagor/ML/error-free-markdown/data.csv")
        else:
            raise ValueError("Either csv_path or data must be provided")
    

    def calculate_jaccard_similarity(self, str1: str, str2: str) -> float:
       
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 1.0 if len(set1) == 0 and len(set2) == 0 else 0.0
        
        return intersection / union
    
    def evaluate_table_similarity(self, corrected_table: str, reference_table: str) -> Dict[str, float]:
        
        corrected_cells = self.extract_table_cells(corrected_table)
        reference_cells = self.extract_table_cells(reference_table)
        
        similarities = []
        max_len = max(len(corrected_cells), len(reference_cells))
        
        for i in range(max_len):
            cell1 = corrected_cells[i] if i < len(corrected_cells) else ""
            cell2 = reference_cells[i] if i < len(reference_cells) else ""
            similarity = self.calculate_jaccard_similarity(cell1, cell2)
            similarities.append(similarity)
        
        return {
            'average_jaccard_similarity': np.mean(similarities),
            'min_similarity': np.min(similarities),
            'max_similarity': np.max(similarities),
            'std_similarity': np.std(similarities),
            'total_cells_compared': len(similarities)
        }
    
    def extract_table_cells(self, markdown_table: str) -> List[str]:
        cells = []
        lines = markdown_table.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('|---') and not line.startswith('|-'):
                if line.startswith('|'):
                    line = line[1:]
                if line.endswith('|'):
                    line = line[:-1]
                
                row_cells = [cell.strip() for cell in line.split('|')]
                cells.extend(row_cells)
        
        return [cell for cell in cells if cell]  # Remove empty cells
    
    def rule_based_correction(self, raw_response: str) -> str:
        logger.info("Applying rule-based correction...")
        
        lines = raw_response.strip().split('\n')
        corrected_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if '|' in line:
                line = re.sub(r'\|+', '|', line)
                
                if not line.startswith('|'):
                    line = '|' + line
                if not line.endswith('|'):
                    line = line + '|'
                
                cells = line.split('|')
                cleaned_cells = []
                
                for cell in cells:
                    cell = cell.strip()
                    cell = re.sub(r'\s+', ' ', cell)
                    cell = re.sub(r'(\d),(\d)', r'\1,\2', cell)
                    cleaned_cells.append(cell)
                
                line = '|'.join(cleaned_cells)
                
            elif '---' in line or line.startswith('-'):
                if not line.startswith('|'):
                    line = '|' + line
                if not line.endswith('|'):
                    line = line + '|'
                
                line = re.sub(r'-+', '---', line)
                
            corrected_lines.append(line)
        
        max_columns = 0
        table_lines = []
        separator_indices = []
        
        for i, line in enumerate(corrected_lines):
            if '|' in line:
                columns = len(line.split('|')) - 2  # Subtract 2 for leading/trailing empty splits
                max_columns = max(max_columns, columns)
                table_lines.append((i, line, columns))
                
                if '---' in line:
                    separator_indices.append(i)
        
        final_lines = []
        for i, line, col_count in table_lines:
            if col_count < max_columns:
                missing = max_columns - col_count
                line = line[:-1] + ('|' * missing) + '|'
            
            final_lines.append(line)
        
        if not separator_indices and final_lines:
            separator = '|' + '---|' * max_columns
            final_lines.insert(1, separator)
        
        return '\n'.join(final_lines)
    
    def prompt_engineering_correction(self, raw_response: str) -> str:
        if not self.GEMINI_API_KEY:
            logger.warning("Gemini API key not provided. Returning rule-based correction.")
            return self.rule_based_correction(raw_response)
        
        logger.info("Applying prompt engineering correction with Gemini...")
        
        prompt = f"""
You are an expert in markdown table formatting. Please correct the following erroneous markdown table and return ONLY the corrected table without any additional text or explanation.

Requirements:
1. Ensure proper pipe (|) alignment and formatting
2. Add proper separator line with dashes (---) after the header
3. Clean up cell content and remove extra whitespace
4. Ensure consistent column count across all rows
5. Format numbers properly with appropriate comma separators
6. Maintain the original data content while fixing structural issues

Erroneous markdown table:
{raw_response}

Return only the corrected markdown table:
"""
        
        try:
            response = self.model.generate_content(prompt)
            corrected_table = response.text.strip()
            
            # Clean up any extra text that might be included
            lines = corrected_table.split('\n')
            table_lines = []
            in_table = False
            
            for line in lines:
                if '|' in line:
                    in_table = True
                    table_lines.append(line)
                elif in_table and line.strip() == '':
                    break
                elif in_table:
                    table_lines.append(line)
            
            return '\n'.join(table_lines) if table_lines else corrected_table
            
        except Exception as e:
            logger.error(f"Error with Gemini API: {e}")
            logger.info("Falling back to rule-based correction")
            return self.rule_based_correction(raw_response)
    
    # TASK 3: Fine-tuned Model (Bonus)
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
       
        logger.info("Preparing training data for fine-tuning...")
        
        features = []
        targets = []
        
        for _, row in df.iterrows():
            raw_table = str(row['raw_response'])
            correct_table = str(row['response'])
            
            feature_vector = self.extract_table_features(raw_table)
            features.append(feature_vector)
            
            targets.append(correct_table)
        
        return features, targets
    
    def extract_table_features(self, table_str: str) -> str:
        features = []
        
        features.append(f"line_count:{len(table_str.split(chr(10)))}")
        features.append(f"pipe_count:{table_str.count('|')}")
        features.append(f"dash_count:{table_str.count('-')}")
        features.append(f"total_length:{len(table_str)}")
        
        has_header_separator = 1 if '---' in table_str else 0
        features.append(f"has_separator:{has_header_separator}")
        
        lines = table_str.strip().split('\n')
        column_counts = []
        for line in lines:
            if '|' in line:
                column_counts.append(len(line.split('|')))
        
        if column_counts:
            features.append(f"avg_columns:{np.mean(column_counts):.2f}")
            features.append(f"column_std:{np.std(column_counts):.2f}")
        
        return ' '.join(features)
    
    def train_fine_tuned_model(self, df: pd.DataFrame, test_size: float = 0.2):
        
        logger.info("Training fine-tuned model...")
        
        features, targets = self.prepare_training_data(df)
        
        X_train, X_test, y_train, y_test = train_test_split(
            features, targets, test_size=test_size, random_state=42
        )
        
        self.vectorizer = TfidfVectorizer(max_features=1000)
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        
        y_train_simple = [1 if '---' in target else 0 for target in y_train]
        y_test_simple = [1 if '---' in target else 0 for target in y_test]
        
        self.classifier.fit(X_train_vec, y_train_simple)
        
        train_score = self.classifier.score(X_train_vec, y_train_simple)
        test_score = self.classifier.score(X_test_vec, y_test_simple)
        
        logger.info(f"Training accuracy: {train_score:.4f}")
        logger.info(f"Testing accuracy: {test_score:.4f}")
        
        self.save_model()
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'n_features': X_train_vec.shape[1]
        }
    
    def fine_tuned_correction(self, raw_response: str) -> str:
        
        if not hasattr(self, 'classifier') or not hasattr(self, 'vectorizer'):
            logger.warning("Fine-tuned model not available. Using rule-based correction.")
            return self.rule_based_correction(raw_response)
        
        logger.info("Applying fine-tuned model correction...")
        
        features = self.extract_table_features(raw_response)
        features_vec = self.vectorizer.transform([features])
        
        prediction = self.classifier.predict(features_vec)[0]
        
        corrected = self.rule_based_correction(raw_response)
        
        if prediction == 1 and '---' not in corrected:
            lines = corrected.split('\n')
            if len(lines) > 1:
                separator = '|' + '---|' * (lines[0].count('|') - 1)
                lines.insert(1, separator)
                corrected = '\n'.join(lines)
        
        return corrected
    
    def save_model(self, model_path: str = "models"):
        Path(models).mkdir(exist_ok=True)
        
        with open(f"models/classifier.pkl", "wb") as f:
            pickle.dump(self.classifier, f)
        
        with open(f"models/vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)
        
        logger.info(f"Model saved to {model_path}/")
    
    def load_model(self, model_path: str = "models"):
        """Load a pre-trained model and vectorizer"""
        try:
            with open(f"models/classifier.pkl", "rb") as f:
                self.classifier = pickle.load(f)
            
            with open(f"models/vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
            
            logger.info(f"Model loaded from {model_path}/")
            return True
        except FileNotFoundError:
            logger.warning(f"Model files not found in {model_path}/")
            return False
    
    def run_all_corrections(self, raw_response: str) -> Dict[str, str]:
        
        results = {}
        
        results['rule_based'] = self.rule_based_correction(raw_response)
        
        results['prompt_engineering'] = self.prompt_engineering_correction(raw_response)
        
        results['fine_tuned'] = self.fine_tuned_correction(raw_response)
        
        return results


def main():
    
    print("Markdown Table Correction Solution")
    print("=" * 50)
    
    corrector = MarkdownTableCorrector(GEMINI_API_KEY=Config.GEMINI_API_KEY)
    
    raw_table = """
| Assets
| Non-current assets  |  |  |  | 
| Property, plant and equipment | 8 | 31,504,309 | 29,571,253 |
Right of use (ROU) assets | 9 | 1,960,283 | 1,440,480
| Total non-current assets | | 33,464,592 | 31,011,733 |
"""
    
    print("Original erroneous table:")
    print(raw_table)
    print("\n" + "="*50 + "\n")
    
    results = corrector.run_all_corrections(raw_table)
    
    for method, corrected_table in results.items():
        print(f"{method.upper()} CORRECTION:")
        print(corrected_table)
        print("\n" + "-"*30 + "\n")
    
    reference_table = """|Assets|Value 2021|Value 2020|
|---|---|---|
|Non-current assets|||
|Property, plant and equipment|31,504,309|29,571,253|
|Right of use (ROU) assets|1,960,283|1,440,480|
|Total non-current assets|33,464,592|31,011,733|"""
    
    print("EVALUATION RESULTS:")
    for method, corrected_table in results.items():
        evaluation = corrector.evaluate_table_similarity(corrected_table, reference_table)
        print(f"{method.upper()}:")
        for metric, value in evaluation.items():
            print(f"  {metric}: {value:.4f}")
        print()


if __name__ == "__main__":
    main()