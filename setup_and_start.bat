@echo off
setlocal enabledelayedexpansion
echo ====================================================
echo   Sign Language AI Service - Automated Setup ^& Start
echo ====================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in system PATH.
    echo [*] Downloading Python 3.11.9 installer...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python_installer.exe'"
    
    echo [*] Installing Python silently... (Please wait about 1-2 minutes)
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 AssociateFiles=0 Shortcuts=0
    del python_installer.exe
    
    echo [*] Refreshing PATH variable...
    set "PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python311;%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts;%PATH%"
    
    python --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo [X] Automated Python installation failed or requires system restart.
        echo [!] Please install Python 3.10+ manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [OK] Python installed successfully!
) else (
    echo [OK] Python is already installed.
    python --version
)

echo.
:: Navigate to ai_service folder
cd /d "%~dp0ai_service"

:: Verify if existing venv is working
if exist "venv\" (
    echo [*] Verifying existing virtual environment...
    venv\Scripts\python.exe --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo [!] Existing virtual environment is broken or belongs to another user.
        echo [*] Deleting broken virtual environment...
        rmdir /s /q venv
    ) else (
        echo [OK] Existing virtual environment is healthy!
    )
)

:: Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [*] Creating fresh virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [X] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate and install/update requirements
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [*] Installing dependencies from requirements.txt... (This might take a moment)
pip install -r requirements.txt --quiet
if !errorlevel! neq 0 (
    echo [X] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully!

echo.
:: Check for weights file
set "WEIGHTS_FILE=D:\Model_weights.pth"
if not exist "%WEIGHTS_FILE%" (
    set "WEIGHTS_FILE=D:\Model_weights.pth.zip"
    if not exist "!WEIGHTS_FILE!" (
        set "WEIGHTS_FILE=%~dp0ai_service\Model_weights.pth"
        if not exist "!WEIGHTS_FILE!" (
            echo ====================================================
            echo [WARNING] Model weights file not found!
            echo Expected at: D:\Model_weights.pth
            echo.
            echo Please place your 'Model_weights.pth' file inside:
            echo 1. The D:\ drive (D:\Model_weights.pth)
            echo OR
            echo 2. The ai_service folder (%~dp0ai_service\Model_weights.pth)
            echo ====================================================
            echo.
        )
    )
)

:: Set environment variables
set AI_PORT=5000
if exist "%~dp0ai_service\Model_weights.pth.zip" (
    set "MODEL_WEIGHTS_PATH=%~dp0ai_service\Model_weights.pth.zip"
) else if exist "%~dp0ai_service\Model_weights.pth" (
    set "MODEL_WEIGHTS_PATH=%~dp0ai_service\Model_weights.pth"
) else (
    set "MODEL_WEIGHTS_PATH=D:\Model_weights.pth"
)

:: Run Flask server
echo ====================================================
echo   AI Service is starting on http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo ====================================================
echo.
python app.py
pause
