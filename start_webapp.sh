#!/bin/bash

# AI Resume Analyzer - Development Startup Script

echo "🚀 Starting AI Resume Analyzer Development Environment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists python; then
    echo -e "${RED}❌ Python not found. Please install Python 3.8+${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm not found. Please install npm${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Function to start backend
start_backend() {
    echo -e "${BLUE}🔧 Starting Backend (FastAPI)...${NC}"
    cd "$PROJECT_ROOT/backend"
    
    # Check if virtual environment is activated
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        echo -e "${YELLOW}⚠️  Virtual environment not detected. Trying to activate...${NC}"
        if [ -f "../.venv/bin/activate" ]; then
            source "../.venv/bin/activate"
            echo -e "${GREEN}✅ Virtual environment activated${NC}"
        elif [ -f "../.venv/Scripts/activate" ]; then
            source "../.venv/Scripts/activate"
            echo -e "${GREEN}✅ Virtual environment activated${NC}"
        else
            echo -e "${RED}❌ Virtual environment not found. Please set up venv first.${NC}"
            exit 1
        fi
    fi
    
    # Install backend dependencies
    echo -e "${YELLOW}📦 Installing backend dependencies...${NC}"
    pip install -r requirements.txt
    
    # Start backend server
    echo -e "${GREEN}🌟 Starting FastAPI server on http://localhost:8000${NC}"
    python main.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}⚛️  Starting Frontend (React + Vite)...${NC}"
    cd "$PROJECT_ROOT/frontend"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}📝 Creating .env file...${NC}"
        cp .env.example .env
    fi
    
    # Install frontend dependencies
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
    
    # Start frontend server
    echo -e "${GREEN}🌟 Starting React dev server on http://localhost:3000${NC}"
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
}

# Function to cleanup processes
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up processes...${NC}"
    
    if [ -f "$PROJECT_ROOT/backend/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/backend/backend.pid")
        kill $BACKEND_PID 2>/dev/null
        rm "$PROJECT_ROOT/backend/backend.pid"
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    
    if [ -f "$PROJECT_ROOT/frontend/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$PROJECT_ROOT/frontend/frontend.pid")
        kill $FRONTEND_PID 2>/dev/null
        rm "$PROJECT_ROOT/frontend/frontend.pid"
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    
    echo -e "${GREEN}🎉 Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
case "${1:-all}" in
    "backend")
        start_backend
        echo -e "${GREEN}🎉 Backend started successfully!${NC}"
        echo -e "${BLUE}📱 API Documentation: http://localhost:8000/docs${NC}"
        wait
        ;;
    "frontend")
        start_frontend
        echo -e "${GREEN}🎉 Frontend started successfully!${NC}"
        echo -e "${BLUE}🌐 Application: http://localhost:3000${NC}"
        wait
        ;;
    "all"|*)
        # Start both services
        start_backend
        sleep 3  # Give backend time to start
        start_frontend
        
        echo -e "\n${GREEN}🎉 AI Resume Analyzer is now running!${NC}"
        echo -e "${BLUE}================================${NC}"
        echo -e "${BLUE}🌐 Frontend:  http://localhost:3000${NC}"
        echo -e "${BLUE}🔧 Backend:   http://localhost:8000${NC}"
        echo -e "${BLUE}📚 API Docs:  http://localhost:8000/docs${NC}"
        echo -e "${BLUE}================================${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
        
        # Wait for processes
        wait
        ;;
esac
