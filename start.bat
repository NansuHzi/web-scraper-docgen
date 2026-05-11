@echo off
chcp 65001 >nul
echo ================================================
echo          Web Scraper DocGen Start
echo ================================================
echo.

:: Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"

echo [1/3] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.13+
    pause
    exit /b 1
)

echo [2/3] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

echo.
echo [3/3] Starting services...
echo.

:: Create logs directory
if not exist logs mkdir logs

:: Start backend service
echo Starting backend...
start "Backend" cmd /k "cd /d ""%PROJECT_DIR%"" && pip install -e . >nul 2>&1 && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start frontend service
echo Starting frontend...
start "Frontend" cmd /k "cd /d ""%PROJECT_DIR%frontend\vue-project"" && npm install >nul 2>&1 && npm run dev"

echo.
echo Services starting...
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo.
pause
