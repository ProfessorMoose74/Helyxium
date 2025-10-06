# Helyxium Development Makefile

.PHONY: help install test lint format clean build docker run dev

# Default target
help:
	@echo "Helyxium Development Commands"
	@echo "============================="
	@echo "install       Install dependencies"
	@echo "install-dev   Install development dependencies"
	@echo "test          Run tests"
	@echo "test-cov      Run tests with coverage report"
	@echo "lint          Run all linters"
	@echo "format        Format code with black and isort"
	@echo "type-check    Run type checking with mypy"
	@echo "security      Run security checks"
	@echo "clean         Clean build artifacts"
	@echo "build         Build standalone executable"
	@echo "docker        Build Docker image"
	@echo "docker-run    Run in Docker container"
	@echo "run           Run the application"
	@echo "dev           Run in development mode"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-mock black flake8 mypy isort bandit pre-commit
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Code Quality
lint: lint-flake8 lint-black lint-isort

lint-flake8:
	flake8 src/ --max-line-length=88 --extend-ignore=E203,W503

lint-black:
	black --check .

lint-isort:
	isort --check-only .

format:
	black .
	isort .

type-check:
	mypy src/

security:
	bandit -r src/ -c pyproject.toml

pre-commit:
	pre-commit run --all-files

# Building
clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.spec" -delete

build: clean
	python build.py

build-installer:
	python create_installer_bundle.py

# Docker
docker:
	docker build -t helyxium:latest .

docker-dev:
	docker-compose --profile dev up helyxium-dev

docker-run:
	docker-compose up helyxium

docker-stop:
	docker-compose down

docker-clean:
	docker-compose down -v
	docker rmi helyxium:latest

# Running
run:
	python main.py

dev:
	HELYXIUM_ENV=development LOG_LEVEL=DEBUG python main.py

# Release
release-check:
	@echo "Running all checks before release..."
	make lint
	make type-check
	make security
	make test-cov
	@echo "All checks passed! Ready for release."

# CI simulation
ci: lint type-check security test-cov
	@echo "CI checks completed successfully!"
