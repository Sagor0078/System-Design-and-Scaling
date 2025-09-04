.PHONY: help install lint format type-check test test-cov security clean docker-build docker-test run-local

help: ## show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## install dependencies with uv
	uv sync --dev
	cd app && uv sync --dev

lint: ## run ruff linter
	uv run ruff check .
	cd app && uv run ruff check .

format: ## format code with ruff
	uv run ruff format .
	cd app && uv run ruff format .

type-check: ## run mypy type checking
	uv run pyright app/

test-integration: ## run integration tests (requires running system)
	@echo "Starting system for integration tests..."
	docker-compose up -d --build
	@echo "Waiting for system to be ready..."
	sleep 30
	uv run python tests/test_system.py
	docker-compose down

test: ## run unit tests (default)
	uv run pytest tests/test_app.py -v

test-cov: ## run unit tests with coverage
	uv add pytest-cov
	uv run pytest tests/test_app.py --cov=app --cov-report=term-missing --cov-report=html

security: ## run security checks (optional)
	@echo "Installing security tools..."
	uv add safety bandit --group dev || echo "Warning: Could not install security tools"
	@echo "Running safety check..."
	uv run safety scan || echo "Warning: Safety check failed"
	@echo "Running bandit security scan..."
	uv run bandit -r app/ -f json -o bandit-report.json || echo "Warning: Bandit scan failed"

clean: ## clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ bandit-report.json

docker-build: ## build Docker image
	docker build -t scaling-system-app ./app

docker-test: ## test docker image
	docker run --rm -d --name test-app -p 8000:8000 scaling-system-app:latest
	sleep 5
	curl -f http://localhost:8000/health || exit 1
	docker stop test-app

run-local: ## run the system locally with Docker Compose
	docker-compose up --build

run-tests-local: ## run integration tests locally
	docker-compose up -d --build
	sleep 30
	uv run python tests/test_system.py
	docker-compose down

ci-check: lint format type-check test ## run all CI checks locally

dev-setup: install ## set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make help' to see available commands"
