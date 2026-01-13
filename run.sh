#!/bin/bash
# Quick start script for TracerTemplateMaker (macOS/Linux)

echo "TracerTemplateMaker - Quick Start"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import cv2" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -e .
    echo "✓ Dependencies installed"
fi

# Run the application
echo "Starting TracerTemplateMaker..."
python main.py
