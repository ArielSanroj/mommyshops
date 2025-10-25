# Makefile for MommyShops

.PHONY: help install test lint format clean docker

# Default target
help:
	@echo "MommyShops - Available Commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make test           - Run all tests"
	@echo "  make test-python    - Run Python tests"
	@echo "  make test-java      - Run Java tests"
	@echo "  make lint           - Run all linters"
	@echo "  make lint-python    - Run Python linters"
	@echo "  make lint-java      - Run Java linters"
	@echo "  make format         - Format all code"
	@echo "  make format-python  - Format Python code"
	@echo "  make format-java    - Format Java code"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make run-python     - Run Python backend"
	@echo "  make run-java       - Run Java backend"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker containers"

# Installation
install: install-python install-java

install-python:
	@echo "Installing Python dependencies..."
	python3 -m venv venv
	. venv/bin/activate && pip install -r backend-python/requirements.txt

install-java:
	@echo "Installing Java dependencies..."
	cd backend-java && mvn clean install -DskipTests

# Testing
test: test-python test-java

test-python:
	@echo "Running Python tests..."
	. venv/bin/activate && pytest --cov=backend-python/app --cov-report=html --cov-report=term

test-java:
	@echo "Running Java tests..."
	cd backend-java && mvn test

test-integration:
	@echo "Running integration tests..."
	. venv/bin/activate && pytest tests/integration/ -v

# Linting
lint: lint-python lint-java

lint-python:
	@echo "Running Python linters..."
	. venv/bin/activate && flake8 backend-python/app/
	. venv/bin/activate && pylint backend-python/app/
	. venv/bin/activate && mypy backend-python/app/
	. venv/bin/activate && bandit -r backend-python/app/

lint-java:
	@echo "Running Java linters..."
	cd backend-java && mvn checkstyle:check

# Formatting
format: format-python format-java

format-python:
	@echo "Formatting Python code..."
	. venv/bin/activate && black backend-python/app/
	. venv/bin/activate && isort backend-python/app/

format-java:
	@echo "Formatting Java code..."
	cd backend-java && mvn fmt:format

# Pre-commit
precommit-install:
	@echo "Installing pre-commit hooks..."
	. venv/bin/activate && pip install pre-commit
	. venv/bin/activate && pre-commit install

precommit-run:
	@echo "Running pre-commit hooks..."
	. venv/bin/activate && pre-commit run --all-files

# Run services
run-python:
	@echo "Starting Python backend on port 8000..."
	. venv/bin/activate && uvicorn backend-python.app.main:app --host 0.0.0.0 --port 8000 --reload

run-java:
	@echo "Starting Java backend on port 8080..."
	cd backend-java && mvn spring-boot:run

# Docker
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Database
db-migrate:
	@echo "Running database migrations..."
	. venv/bin/activate && alembic upgrade head

db-reset:
	@echo "Resetting database..."
	psql -U postgres -c "DROP DATABASE IF EXISTS mommyshops;"
	psql -U postgres -c "CREATE DATABASE mommyshops;"
	. venv/bin/activate && alembic upgrade head

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	cd backend-java && mvn clean

clean-all: clean
	@echo "Cleaning all artifacts including venv..."
	rm -rf venv/
	rm -rf node_modules/

# Documentation
docs-build:
	@echo "Building documentation..."
	. venv/bin/activate && mkdocs build

docs-serve:
	@echo "Serving documentation..."
	. venv/bin/activate && mkdocs serve

# Coverage
coverage-python:
	@echo "Generating Python coverage report..."
	. venv/bin/activate && pytest --cov=backend --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

coverage-java:
	@echo "Generating Java coverage report..."
	cd backend-java && mvn clean test jacoco:report
	@echo "Coverage report: backend-java/target/site/jacoco/index.html"

# Security scan
security-scan:
	@echo "Running security scans..."
	. venv/bin/activate && bandit -r backend-python/app/ -f json -o security-report.json
	. venv/bin/activate && safety check --json
	cd backend-java && mvn dependency-check:check

# Performance
benchmark:
	@echo "Running performance benchmarks..."
	. venv/bin/activate && pytest tests/benchmarks/ -v

# CI/CD
ci: lint test coverage-python coverage-java
	@echo "CI pipeline completed successfully!"

# All checks before commit
check-all: format lint test
	@echo "All checks passed! Ready to commit."
