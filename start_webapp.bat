@echo off
REM AI Resume Analyzer - Development Startup Script for Windows

echo 🚀 Starting AI Resume Analyzer Development Environment
echo ==================================================

REM Check prerequisites
echo 📋 Checking prerequisites...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js 18+
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ npm not found. Please install npm
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Get current directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%

REM Function to start backend
echo 🔧 Starting Backend (FastAPI)...
cd "%PROJECT_ROOT%backend"

REM Check if virtual environment exists and activate it
if exist "%PROJECT_ROOT%.venv\Scripts\activate.bat" (
    echo ⚠️  Activating virtual environment...
    call "%PROJECT_ROOT%.venv\Scripts\activate.bat"
    echo ✅ Virtual environment activated
) else (
    echo ❌ Virtual environment not found. Please set up venv first.
    exit /b 1
)

REM Install backend dependencies
echo 📦 Installing backend dependencies...
pip install -r requirements.txt

REM Start backend server in background
echo 🌟 Starting FastAPI server on http://localhost:8000
start "Backend Server" python main.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo ⚛️  Starting Frontend (React + Vite)...
cd "%PROJECT_ROOT%frontend"

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file...
    copy .env.example .env
)

REM Install frontend dependencies
echo 📦 Installing frontend dependencies...
npm install

REM Start frontend server
echo 🌟 Starting React dev server on http://localhost:3000
start "Frontend Server" npm run dev

REM Display success message
echo.
echo 🎉 AI Resume Analyzer is now running!
echo ================================
echo 🌐 Frontend:  http://localhost:3000
echo 🔧 Backend:   http://localhost:8000
echo 📚 API Docs:  http://localhost:8000/docs
echo ================================
echo.
echo Press any key to open the application in your browser...
pause >nul

REM Open application in default browser
start http://localhost:3000

echo.
echo Application opened in browser. Keep this window open to maintain servers.
echo Press Ctrl+C to stop servers when done.
pause
