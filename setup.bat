@echo off
REM Helyxium Quick Setup Script for Windows

echo ========================================
echo Helyxium Setup Script
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.9 or higher is required
    pause
    exit /b 1
)

echo [OK] Python version compatible
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Install development dependencies (optional)
set /p install_dev="Install development dependencies? (y/n): "
if /i "%install_dev%"=="y" (
    echo Installing development dependencies...
    pip install pytest pytest-cov pytest-mock black flake8 mypy isort bandit pre-commit
    pre-commit install
    echo [OK] Development dependencies installed
)
echo.

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo [OK] .env file created - please edit it with your settings
) else (
    echo [OK] .env file already exists
)
echo.

REM Create logs directory
if not exist "logs" (
    mkdir logs
    echo [OK] Logs directory created
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run Helyxium:
echo   1. Activate the virtual environment: venv\Scripts\activate
echo   2. Run: python main.py
echo.
echo Or simply run: run.bat
echo.
pause
