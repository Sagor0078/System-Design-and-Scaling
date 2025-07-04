import pandas as pd
import numpy as np
import re
from typing import List, Dict, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

from config import Config


class JaccardEvaluator:
    
    def __init__(self):
        self.results = {}
        
    def preprocess_text(self, text: str) -> str:
    
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[,\s]+', ' ', text)
        return text
    
    def extract_table_cells(self, markdown_table: str, detailed: bool = False) -> List[str]:
        cells = []
        lines = markdown_table.strip().split('\n')
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            
            if not line or '---' in line or line.startswith('|-'):
                continue
                
            if '|' in line:
                if line.startswith('|'):
                    line = line[1:]
                if line.endswith('|'):
                    line = line[:-1]
                
                row_cells = line.split('|')
                for cell_idx, cell in enumerate(row_cells):
                    cell = cell.strip()
                    if detailed:
                        cells.append({
                            'content': cell,
                            'row': line_idx,
                            'col': cell_idx,
                            'original_line': lines[line_idx]
                        })
                    else:
                        cells.append(cell)
        
        return cells
    
    def calculate_jaccard_similarity(self, str1: str, str2: str, 
                                   method: str = 'words') -> float:
        
        str1 = self.preprocess_text(str1)
        str2 = self.preprocess_text(str2)
        
        if method == 'words':
            set1 = set(str1.split())
            set2 = set(str2.split())
        elif method == 'chars':
            set1 = set(str1)
            set2 = set(str2)
        elif method == 'tokens':
            # Tokenize including numbers and punctuation
            tokens1 = re.findall(r'\w+|\d+|[^\w\s]', str1)
            tokens2 = re.findall(r'\w+|\d+|[^\w\s]', str2)
            set1 = set(tokens1)
            set2 = set(tokens2)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 1.0 if len(set1) == 0 and len(set2) == 0 else 0.0
        
        return intersection / union
    
    def evaluate_single_pair(self, corrected: str, reference: str) -> Dict[str, Any]:
        
        corrected_cells = self.extract_table_cells(corrected)
        reference_cells = self.extract_table_cells(reference)
        
        # Calculate similarities using different methods
        similarities = {
            'words': [],
            'chars': [],
            'tokens': []
        }
        
        max_len = max(len(corrected_cells), len(reference_cells))
        cell_pairs = []
        
        for i in range(max_len):
            cell1 = corrected_cells[i] if i < len(corrected_cells) else ""
            cell2 = reference_cells[i] if i < len(reference_cells) else ""
            cell_pairs.append((cell1, cell2))
            
            # Calculate similarities for each method
            for method in similarities.keys():
                sim = self.calculate_jaccard_similarity(cell1, cell2, method)
                similarities[method].append(sim)
        
        metrics = {}
        for method, sims in similarities.items():
            metrics[f'{method}_jaccard_mean'] = np.mean(sims)
            metrics[f'{method}_jaccard_std'] = np.std(sims)
            metrics[f'{method}_jaccard_min'] = np.min(sims)
            metrics[f'{method}_jaccard_max'] = np.max(sims)
            metrics[f'{method}_jaccard_median'] = np.median(sims)
        
        metrics.update({
            'total_cells_corrected': len(corrected_cells),
            'total_cells_reference': len(reference_cells),
            'cell_count_difference': abs(len(corrected_cells) - len(reference_cells)),
            'perfect_matches': sum(1 for c1, c2 in cell_pairs if c1.strip() == c2.strip()),
            'empty_cell_matches': sum(1 for c1, c2 in cell_pairs if not c1.strip() and not c2.strip()),
            'non_empty_pairs': sum(1 for c1, c2 in cell_pairs if c1.strip() and c2.strip())
        })
        
        return metrics
    
    def evaluate_dataset(self, df: pd.DataFrame, methods: List[str] = None) -> Dict[str, Any]:
        if methods is None:
            methods = ['rule_based', 'prompt_engineering', 'fine_tuned']
        
        results = {}
        
        for method in methods:
            if f'{method}_corrected' not in df.columns:
                print(f"Warning: Column '{method}_corrected' not found. Skipping {method}")
                continue
                
            method_metrics = []
            
            for idx, row in df.iterrows():
                corrected = str(row[f'{method}_corrected'])
                reference = str(row['response'])
                
                metrics = self.evaluate_single_pair(corrected, reference)
                metrics['sample_id'] = idx
                method_metrics.append(metrics)
            
            results[method] = {
                'individual_scores': method_metrics,
                'aggregate_metrics': self._aggregate_metrics(method_metrics)
            }
        
        return results
    
    def _aggregate_metrics(self, individual_metrics: List[Dict]) -> Dict[str, float]:
        if not individual_metrics:
            return {}
        
        metric_keys = set()
        for metrics in individual_metrics:
            metric_keys.update(metrics.keys())
        
        numeric_keys = {k for k in metric_keys 
                       if k not in ['sample_id'] and 
                       all(isinstance(m.get(k, 0), (int, float)) for m in individual_metrics)}
        
        aggregated = {}
        for key in numeric_keys:
            values = [m[key] for m in individual_metrics if key in m]
            if values:
                aggregated[f'{key}_mean'] = np.mean(values)
                aggregated[f'{key}_std'] = np.std(values)
                aggregated[f'{key}_min'] = np.min(values)
                aggregated[f'{key}_max'] = np.max(values)
        
        return aggregated
    
    def create_evaluation_report(self, results: Dict[str, Any], 
                               output_path: str = "evaluation_report.json") -> None:
        report = {
            'evaluation_summary': {},
            'method_comparison': {},
            'detailed_results': results
        }
        
        for method, method_results in results.items():
            if 'aggregate_metrics' in method_results:
                agg_metrics = method_results['aggregate_metrics']
                report['evaluation_summary'][method] = {
                    'primary_jaccard_score': agg_metrics.get('words_jaccard_mean_mean', 0),
                    'score_stability': agg_metrics.get('words_jaccard_mean_std', 0),
                    'perfect_match_rate': agg_metrics.get('perfect_matches_mean', 0),
                    'structural_accuracy': 1 - (agg_metrics.get('cell_count_difference_mean', 0) / 
                                               max(agg_metrics.get('total_cells_reference_mean', 1), 1))
                }
        
        primary_scores = {}
        for method in results.keys():
            if method in report['evaluation_summary']:
                primary_scores[method] = report['evaluation_summary'][method]['primary_jaccard_score']
        
        if primary_scores:
            best_method = max(primary_scores.keys(), key=lambda x: primary_scores[x])
            report['method_comparison'] = {
                'best_performing_method': best_method,
                'method_rankings': sorted(primary_scores.items(), key=lambda x: x[1], reverse=True),
                'score_differences': {
                    method: primary_scores[best_method] - score 
                    for method, score in primary_scores.items()
                }
            }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Evaluation report saved to {output_path}")
        
        self._print_evaluation_summary(report)
    
    def _print_evaluation_summary(self, report: Dict[str, Any]) -> None:
       
        print("\n" + "="*60)
        print("MARKDOWN TABLE CORRECTION EVALUATION SUMMARY")
        print("="*60)
        
        if 'method_comparison' in report and report['method_comparison']:
            print(f"\nBest Performing Method: {report['method_comparison']['best_performing_method']}")
            print("\nMethod Rankings (by Jaccard Score):")
            for i, (method, score) in enumerate(report['method_comparison']['method_rankings'], 1):
                print(f"  {i}. {method}: {score:.4f}")
        
        print("\nDetailed Method Performance:")
        for method, metrics in report['evaluation_summary'].items():
            print(f"\n{method.upper()}:")
            print(f"  Primary Jaccard Score: {metrics['primary_jaccard_score']:.4f}")
            print(f"  Score Stability (std): {metrics['score_stability']:.4f}")
            print(f"  Perfect Match Rate: {metrics['perfect_match_rate']:.4f}")
            print(f"  Structural Accuracy: {metrics['structural_accuracy']:.4f}")
    
    def visualize_results(self, results: Dict[str, Any], output_dir: str = "plots") -> None:
        
        Path(output_dir).mkdir(exist_ok=True)
        
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        methods = []
        scores = []
        
        for method, method_results in results.items():
            if 'aggregate_metrics' in method_results:
                methods.append(method.replace('_', ' ').title())
                agg_metrics = method_results['aggregate_metrics']
                scores.append(agg_metrics.get('words_jaccard_mean_mean', 0))
        
        if methods and scores:
            plt.figure(figsize=(10, 6))
            bars = plt.bar(methods, scores, alpha=0.8)
            plt.title('Jaccard Similarity Scores by Correction Method', fontsize=14, fontweight='bold')
            plt.ylabel('Average Jaccard Similarity Score', fontsize=12)
            plt.xlabel('Correction Method', fontsize=12)
            plt.ylim(0, 1)
            
            for bar, score in zip(bars, scores):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/method_comparison.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        fig, axes = plt.subplots(1, len(results), figsize=(5*len(results), 6))
        if len(results) == 1:
            axes = [axes]
        
        for idx, (method, method_results) in enumerate(results.items()):
            if 'individual_scores' in method_results:
                individual_scores = method_results['individual_scores']
                jaccard_scores = [score.get('words_jaccard_mean', 0) for score in individual_scores]
                
                axes[idx].violinplot([jaccard_scores], positions=[0], showmeans=True, showmedians=True)
                axes[idx].set_title(f'{method.replace("_", " ").title()}', fontweight='bold')
                axes[idx].set_ylabel('Jaccard Similarity Score')
                axes[idx].set_ylim(0, 1)
                axes[idx].set_xticks([])
        
        plt.suptitle('Score Distribution by Method', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/score_distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        all_metrics = {}
        for method, method_results in results.items():
            if 'individual_scores' in method_results:
                for score_dict in method_results['individual_scores']:
                    for key, value in score_dict.items():
                        if isinstance(value, (int, float)) and key != 'sample_id':
                            metric_key = f"{method}_{key}"
                            if metric_key not in all_metrics:
                                all_metrics[metric_key] = []
                            all_metrics[metric_key].append(value)
        
        if all_metrics:
            max_len = max(len(values) for values in all_metrics.values())
            for key in all_metrics:
                while len(all_metrics[key]) < max_len:
                    all_metrics[key].append(np.nan)
            
            df_metrics = pd.DataFrame(all_metrics)
            correlation_matrix = df_metrics.corr()
            
            plt.figure(figsize=(12, 10))
            mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
            sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5, cbar_kws={"shrink": .8})
            plt.title('Metric Correlation Heatmap', fontsize=14, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/correlation_heatmap.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"Visualizations saved to {output_dir}/")
    
    def benchmark_methods(self, sample_data: List[Tuple[str, str]]) -> Dict[str, Any]:
        
        from markdown_table_corrector import MarkdownTableCorrector
        
        corrector = MarkdownTableCorrector()
        benchmark_results = {}
        
        for i, (raw_table, reference_table) in enumerate(sample_data):
            corrections = corrector.run_all_corrections(raw_table)
            
            sample_results = {}
            for method, corrected_table in corrections.items():
                metrics = self.evaluate_single_pair(corrected_table, reference_table)
                sample_results[method] = metrics
            
            benchmark_results[f'sample_{i}'] = sample_results
        
        return benchmark_results


def run_evaluation_pipeline(csv_path: str = None, df: pd.DataFrame = None, 
                          gemini_api_key: str = None) -> None:
    print("Starting Markdown Table Correction Evaluation Pipeline")
    print("="*60)
    
    from markdown_table_corrector import MarkdownTableCorrector
    
    corrector = MarkdownTableCorrector(gemini_api_key=gemini_api_key)
    evaluator = JaccardEvaluator()
    
    # Load data
    if df is not None:
        data = df
    elif csv_path:
        data = pd.read_csv(csv_path)
    else:
        raise ValueError("Either csv_path or df must be provided")
    
    print(f"Loaded {len(data)} samples for evaluation")
    
    print("Generating corrections...")
    corrections_data = []
    
    for idx, row in data.iterrows():
        raw_table = str(row['raw_response'])
        reference = str(row['response'])
        
        corrections = corrector.run_all_corrections(raw_table)
        
        sample_data = {
            'sample_id': idx,
            'raw_response': raw_table,
            'response': reference,
        }
        
        for method, corrected in corrections.items():
            sample_data[f'{method}_corrected'] = corrected
        
        corrections_data.append(sample_data)
    
    corrections_df = pd.DataFrame(corrections_data)
    
    print("Evaluating corrections...")
    results = evaluator.evaluate_dataset(corrections_df)
    
    print("Generating evaluation report...")
    evaluator.create_evaluation_report(results, "evaluation_report.json")
    
    print("Creating visualizations...")
    evaluator.visualize_results(results, "evaluation_plots")
    
    corrections_df.to_csv("corrected_tables_with_evaluations.csv", index=False)
    print("Detailed results saved to corrected_tables_with_evaluations.csv")
    
    print("\nEvaluation pipeline completed successfully!")
    return results


if __name__ == "__main__":
    sample_data = [
        (
            "| Assets | | | |\n| Non-current assets | | | |\nProperty, plant and equipment | 8 | 31,504,309 | 29,571,253",
            "|Assets|Column1|Column2|Column3|\n|---|---|---|---|\n|Non-current assets|||||\n|Property, plant and equipment|8|31,504,309|29,571,253|"
        ),
        (
            "Inventories | 10 | 34,425,100 | 23,780,680\nTrade and other receivables | 11 | 2,768,918 | 141,439",
            "|Item|Code|Value 2021|Value 2020|\n|---|---|---|---|\n|Inventories|10|34,425,100|23,780,680|\n|Trade and other receivables|11|2,768,918|141,439|"
        )
    ]
    
    test_df = pd.DataFrame({
        'raw_response': [item[0] for item in sample_data],
        'response': [item[1] for item in sample_data]
    })
    
    try:
        results = run_evaluation_pipeline(df=test_df, gemini_api_key=Config.GEMINI_API_KEY)
        print("Test evaluation completed successfully!")
    except Exception as e:
        print(f"Error during evaluation: {e}")
        
        # Fallback: demonstrate individual components
        print("\nDemonstrating individual evaluation components:")
        evaluator = JaccardEvaluator()
        
        for i, (raw, ref) in enumerate(sample_data):
            print(f"\nSample {i+1} Evaluation:")
            metrics = evaluator.evaluate_single_pair(raw, ref)
            print(f"  Jaccard Similarity (words): {metrics['words_jaccard_mean']:.4f}")
            print(f"  Perfect Matches: {metrics['perfect_matches']}")
            print(f"  Cell Count Difference: {metrics['cell_count_difference']}")