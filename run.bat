@echo off
REM Quick start script for TracerTemplateMaker (Windows)
pushd "%~dp0"

echo TracerTemplateMaker - Quick Start
echo ==================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import cv2" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install --upgrade pip
    pip install -e .
    echo Dependencies installed
)

REM Run the application
echo Starting TracerTemplateMaker...
python main.py

popd
pause
