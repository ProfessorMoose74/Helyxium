#!/bin/bash
# Quick run script for Helyxium on Linux/macOS

set -e

echo "Starting Helyxium..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py

# Deactivate when done
deactivate
