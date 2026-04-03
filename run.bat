@echo off
REM ================================================
REM ApplyGenius — Windows Start Script
REM ================================================

echo.
echo ╔══════════════════════════════════════════╗
echo ║   ApplyGenius — Autonomous Job Agent     ║
echo ╚══════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

REM Create venv if missing
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install deps if not done
if not exist venv\Lib\site-packages\flask (
    echo Installing dependencies...
    pip install -r backend\requirements.txt
)

REM Copy env template if missing
if not exist backend\.env (
    copy backend\.env.example backend\.env
    echo.
    echo IMPORTANT: Edit backend\.env with your API keys before continuing!
    echo   1. NVIDIA_API_KEY   - https://build.nvidia.com
    echo   2. GOOGLE_SHEETS_ID - Your Google Sheet ID
    echo   3. EMAIL_SENDER     - Your Gmail address (optional)
    echo.
    pause
)

REM Create required folders
if not exist backend\uploads mkdir backend\uploads
if not exist backend\outputs mkdir backend\outputs

REM Start Flask backend
echo Starting backend on http://localhost:5000 ...
start "ApplyGenius Backend" cmd /k "cd backend && python app.py"

timeout /t 2 /nobreak >nul

REM Start frontend server
echo Starting frontend on http://localhost:3000 ...
start "ApplyGenius Frontend" cmd /k "cd frontend && python -m http.server 3000"

timeout /t 2 /nobreak >nul

REM Open browser
echo Opening browser...
start http://localhost:3000

echo.
echo ╔══════════════════════════════════════════╗
echo ║  ApplyGenius is running!                 ║
echo ║                                          ║
echo ║  Frontend: http://localhost:3000         ║
echo ║  Backend:  http://localhost:5000         ║
echo ║                                          ║
echo ║  Close the terminal windows to stop.    ║
echo ╚══════════════════════════════════════════╝
echo.
pause
