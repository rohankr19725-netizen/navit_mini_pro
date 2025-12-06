#!/bin/bash
# Brain Tumor Detection - Streamlit App Startup Script
# For macOS and Linux Users

echo ""
echo "========================================"
echo "Brain Tumor Detection - Streamlit App"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ using:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python: $PYTHON_VERSION"

# Check if requirements are installed
echo ""
echo "Checking dependencies..."
python3 -c "import streamlit; import tensorflow; import pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Installing dependencies from requirements.txt..."
    echo ""
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

# Check if model file exists
if [ ! -f "model.keras" ]; then
    echo ""
    echo "WARNING: model.keras file not found in current directory"
    echo "The app will fail when trying to load the model"
    echo ""
    echo "Please ensure model.keras is in: $(pwd)"
    echo ""
fi

# Run the Streamlit app
echo ""
echo "========================================"
echo "Starting Streamlit Application..."
echo "========================================"
echo ""
echo "The app will open in your default browser"
echo "If it doesn't, visit: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run app.py
