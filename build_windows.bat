@echo off
echo ======================================
echo   Building Helyxium for Windows
echo ======================================
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist __pycache__ rmdir /s /q __pycache__
echo.

REM Install dependencies if needed
echo Installing dependencies...
poetry install --only main
echo.

REM Build the executable
echo Building executable...
poetry run pyinstaller helyxium.spec --clean
echo.

if exist dist\Helyxium.exe (
    echo ======================================
    echo   Build successful!
    echo   Executable: dist\Helyxium.exe
    echo ======================================
) else (
    echo ======================================
    echo   Build failed!
    echo   Check the error messages above
    echo ======================================
    exit /b 1
)