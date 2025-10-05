# Contributing to Helyxium

Thank you for your interest in contributing to Helyxium! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.9 - 3.13
- Git
- Poetry (recommended) or pip

### Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/helyxium.git
   cd helyxium
   ```

2. **Install dependencies**
   ```bash
   # Using Poetry (recommended)
   poetry install --with dev

   # Or using pip
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8 mypy pre-commit
   ```

3. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Copy environment template**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py

# Run integration tests only
pytest tests/integration -v
```

### Code Quality

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Check code style with Flake8
flake8 src/

# Type checking with mypy
mypy src/

# Security scanning with Bandit
bandit -r src/
```

### Running the Application

```bash
# Direct execution
python main.py

# Using Poetry
poetry run python main.py
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use Black for formatting (line length: 88)
- Use type hints for all functions
- Write docstrings for all public modules, classes, and functions

### Code Structure

```python
def example_function(param: str) -> bool:
    """
    Brief description of what the function does.

    Args:
        param: Description of the parameter

    Returns:
        Description of the return value

    Raises:
        ValueError: When and why this is raised
    """
    # Implementation
    return True
```

### Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage (aim for >80%)
- Use pytest fixtures for common test setups
- Follow the AAA pattern: Arrange, Act, Assert

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   # Run all checks
   pre-commit run --all-files
   pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `style:` Code style changes
   - `chore:` Build process or auxiliary tool changes

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure all CI checks pass

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- Helyxium version
- Operating system and version
- Python version
- VR hardware (if applicable)
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs

### Feature Requests

When requesting features:

- Describe the use case
- Explain why this feature would be valuable
- Provide examples if possible

## Code Review Process

- All submissions require review
- Reviewers will check for:
  - Code quality and style
  - Test coverage
  - Documentation
  - Security implications
  - Performance impact

## Community

- Be respectful and inclusive
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)
- Ask questions in GitHub Discussions
- Help others when you can

## License

By contributing to Helyxium, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue or reach out to the maintainers if you have questions about contributing.

Thank you for contributing to Helyxium! 🚀
