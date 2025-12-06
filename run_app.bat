@echo off
REM Brain Tumor Detection - Streamlit App Startup Script
REM For Windows Users

echo.
echo ========================================
echo Brain Tumor Detection - Streamlit App
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
python -c "import streamlit; import tensorflow; import pandas" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing dependencies from requirements.txt...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if model file exists
if not exist "model.keras" (
    echo.
    echo WARNING: model.keras file not found in current directory
    echo The app will fail when trying to load the model
    echo.
    echo Please ensure model.keras is in: %CD%
    echo.
    pause
)

REM Run the Streamlit app
echo.
echo ========================================
echo Starting Streamlit Application...
echo ========================================
echo.
echo The app will open in your default browser
echo If it doesn't, visit: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run app.py

pause
