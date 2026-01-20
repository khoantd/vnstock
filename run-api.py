#!/usr/bin/env python3
"""
Python wrapper script to run vnstock FastAPI server
This avoids shell spawn issues by executing Python directly
"""

import sys
import os
import subprocess

def main():
    # Check if venv exists and activate it
    venv_python = None
    if os.path.exists("venv"):
        venv_python = os.path.join("venv", "bin", "python")
        if not os.path.exists(venv_python):
            venv_python = None
    
    # Use venv python if available, otherwise system python
    python_exe = venv_python or sys.executable
    
    # Run the uvicorn command
    cmd = [
        python_exe, "-m", "uvicorn", 
        "vnstock.api.rest_api:app", 
        "--host", "0.0.0.0", 
        "--port", "8002", 
        "--reload"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
