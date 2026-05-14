@echo off
echo ============================================
echo   Sign Language AI Service - Starting...
echo ============================================

cd /d "%~dp0"

:: Check if virtual environment exists, create if not
if not exist "venv\" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo [3/3] Installing dependencies...
pip install -r requirements.txt --quiet

:: Set environment variables
set AI_PORT=5000
set MODEL_WEIGHTS_PATH=D:\Model_weights.pth

:: Start Flask server
echo.
echo ============================================
echo   AI Service running on http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo ============================================
echo.
python app.py

pause
