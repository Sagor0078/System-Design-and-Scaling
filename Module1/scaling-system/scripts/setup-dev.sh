#!/bin/bash

# development setup script for the scaling system project

set -e

echo "Setting up development environment for Scaling System..."

# check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo " uv is installed"

# install Python if needed
echo "Installing Python 3.11..."
uv python install 3.11

# install dependencies
echo "Installing project dependencies..."
uv sync --dev

# install dependencies in app folder
echo "Installing app dependencies..."
cd app && uv sync --dev && cd ..

# install pre-commit hooks
echo "Setting up pre-commit hooks..."
uv run pre-commit install

# run initial checks
echo "Running initial code quality checks..."
echo "  - Linting with ruff..."
uv run ruff check . --fix

echo "  - Formatting with ruff..."
uv run ruff format .

echo "  - Type checking with mypy..."
uv run mypy app/ tests/ || echo "Some type issues found - you may want to fix them"

# run tests
echo "Running tests..."
uv run pytest tests/ -v

echo ""
echo "Development environment setup complete!"
echo ""
echo "Available commands:"
echo "  make help          - Show all available commands"
echo "  make lint          - Run linting"
echo "  make format        - Format code"
echo "  make test          - Run tests"
echo "  make run-local     - Start the system with Docker"
echo "  make ci-check      - Run all CI checks locally"
echo ""
echo "To start developing:"
echo "1. Run 'make run-local' to start the system"
echo "2. Run 'make test' to run tests"
echo "3. Use 'make ci-check' before committing"
echo ""
echo "Happy coding!!"
