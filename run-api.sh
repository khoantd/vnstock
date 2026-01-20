#!/usr/bin/env bash

# Script to run vnstock FastAPI server
# Activates venv if it exists, otherwise uses system Python

# Exit on any error
set -e

# Check if venv exists and activate it
if [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Warning: venv directory exists but activate script not found"
    fi
fi

# Check if python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found in PATH"
    exit 1
fi

# Run the uvicorn command
exec "$PYTHON_CMD" -m uvicorn vnstock.api.rest_api:app --host 0.0.0.0 --port 8001 --reload
