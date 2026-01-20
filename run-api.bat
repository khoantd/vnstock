@echo off
REM Script to run vnstock FastAPI server on Windows
REM Activates venv if it exists, otherwise uses system Python

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

python -m uvicorn vnstock.api.rest_api:app --host 0.0.0.0 --port 8001 --reload

