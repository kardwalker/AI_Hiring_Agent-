@echo off
REM AI Resume Analyzer - Windows Startup Script
echo ========================================
echo   AI Resume Analyzer - Startup Script
echo ========================================

REM Colors for Windows
set GREEN=[92m
set BLUE=[94m
set YELLOW=[93m
set RED=[91m
set NC=[0m

echo %BLUE%Checking prerequisites...%NC%

REM Check if Python exists
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%Python not found. Please install Python 3.8+%NC%
    pause
    exit /b 1
)

REM Check if Node.js exists
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%Node.js not found. Please install Node.js 18+%NC%
    pause
    exit /b 1
)

echo %GREEN%Prerequisites check passed%NC%

REM Get current directory
set PROJECT_ROOT=%~dp0

echo %BLUE%Starting AI Resume Analyzer...%NC%

REM Start backend in new window
echo %YELLOW%Starting Backend (FastAPI)...%NC%
start "AI Resume Analyzer - Backend" cmd /k "cd /d %PROJECT_ROOT%backend && %PROJECT_ROOT%.venv\Scripts\activate.bat && python main.py"

REM Wait a bit for backend to start
timeout /t 5 /nobreak

REM Start frontend in new window
echo %YELLOW%Starting Frontend (React)...%NC%
start "AI Resume Analyzer - Frontend" cmd /k "cd /d %PROJECT_ROOT%frontend && npm run dev"

echo.
echo %GREEN%AI Resume Analyzer is starting up!%NC%
echo %BLUE%================================%NC%
echo %BLUE%Frontend:  http://localhost:3000%NC%
echo %BLUE%Backend:   http://localhost:8000%NC%
echo %BLUE%API Docs:  http://localhost:8000/docs%NC%
echo %BLUE%================================%NC%
echo.
echo %YELLOW%Two new command windows have opened:%NC%
echo %YELLOW%- Backend server (FastAPI)%NC%
echo %YELLOW%- Frontend server (React)%NC%
echo.
echo %YELLOW%Close this window or press any key to continue...%NC%
pause
