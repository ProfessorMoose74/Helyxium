#!/bin/bash
# Helyxium Quick Setup Script for Linux/macOS

set -e

echo "========================================"
echo "Helyxium Setup Script"
echo "========================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

echo "[OK] Python found"
python3 --version
echo

# Check Python version
python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" || {
    echo "[ERROR] Python 3.9 or higher is required"
    exit 1
}

echo "[OK] Python version compatible"
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment already exists"
fi
echo

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip
echo

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "[OK] Dependencies installed"
echo

# Install development dependencies (optional)
read -p "Install development dependencies? (y/n): " install_dev
if [[ "$install_dev" =~ ^[Yy]$ ]]; then
    echo "Installing development dependencies..."
    pip install pytest pytest-cov pytest-mock black flake8 mypy isort bandit pre-commit
    pre-commit install
    echo "[OK] Development dependencies installed"
fi
echo

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "[OK] .env file created - please edit it with your settings"
else
    echo "[OK] .env file already exists"
fi
echo

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo "[OK] Logs directory created"
fi
echo

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo
echo "To run Helyxium:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run: python main.py"
echo
echo "Or simply run: ./run.sh"
echo
