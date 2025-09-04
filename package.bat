@echo off
echo ==========================================
echo  Helyxium Universal Installer Packager
echo ==========================================
echo.

cd /d "%~dp0"
python installer/package_installer.py
pause