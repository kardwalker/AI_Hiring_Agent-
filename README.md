# 🤖 AI Resume Analyzer - Intelligent Hiring Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🌟 Overview

A sophisticated AI-powered web application that analyzes resumes using advanced natural language processing, GitHub integration, and LinkedIn profile analysis. Built with a modern tech stack featuring React frontend, FastAPI backend, and multi-agent AI architecture.

## ✨ Features

### 🔍 **Intelligent Resume Analysis**
- **Multi-format Support**: PDF, TXT, DOCX, and Markdown files
- **AI-Powered Extraction**: Advanced text processing and content analysis
- **Skills Detection**: Automatic identification of technical and soft skills
- **Experience Summary**: Comprehensive work history and education analysis

### 🌐 **GitHub Integration**
- **Repository Analysis**: Automatic fetching and analysis of GitHub repositories
- **Code Quality Assessment**: Analysis of coding patterns and project structure
- **Contribution Metrics**: Evaluation of GitHub activity and contributions
- **Technology Stack Detection**: Identification of programming languages and frameworks

### 💼 **LinkedIn Integration**
- **Profile Analysis**: LinkedIn profile data extraction and analysis
- **Professional Network**: Analysis of professional connections and endorsements
- **Career Progression**: Timeline analysis of career development
- **Skills Validation**: Cross-referencing skills across platforms

### 🖥️ **Modern Web Interface**
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Drag & Drop Upload**: Intuitive file upload with real-time feedback
- **Interactive Chat**: Conversational interface for resume analysis
- **Real-time Processing**: Live status updates during analysis

## 🏗️ Architecture

### Backend (FastAPI)
- **Multi-Agent System**: Specialized agents for different analysis tasks
- **Async Processing**: High-performance asynchronous request handling
- **Session Management**: Persistent conversation state
- **RESTful API**: Clean, documented API endpoints

### Frontend (React)
- **Modern UI**: Built with React 18 and Tailwind CSS
- **Component-Based**: Modular, reusable React components
- **State Management**: Efficient state handling with React hooks
- **HTTP Client**: Axios-based API communication with error handling

### AI Agents
- **Resume Parser**: Advanced text extraction and structured data creation
- **GitHub Analyzer**: Repository and code analysis capabilities
- **LinkedIn Parser**: Professional profile analysis and insights
- **Core Agent**: Orchestrates multi-agent workflows

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Git** for version control

### 1. Clone Repository
```bash
git clone https://github.com/kardwalker/AI_Hiring_Agent-.git
cd AI_Hiring_Agent-
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env with your API keys
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd ../frontend

# Install Node.js dependencies
npm install

# Create environment file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

### 4. Start Application
```bash
# Option A: Use startup scripts
start_webapp_windows.bat  # Windows
# ./start_webapp.sh  # Linux/Mac

# Option B: Manual start
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 5. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

### 1. **Upload Resume**
- Visit http://localhost:3000
- Drag and drop your resume file or click to browse
- Supported formats: PDF, TXT, DOCX, MD
- Wait for upload confirmation

### 2. **Analyze Resume**
- Use suggested questions or ask custom queries
- Examples:
  - "What are the main technical skills?"
  - "Analyze the GitHub repositories"
  - "Summarize work experience"
  - "What machine learning projects are there?"

### 3. **Review Results**
- Get comprehensive AI-powered analysis
- Explore different aspects through follow-up questions
- View GitHub repository insights
- Access LinkedIn profile analysis (when available)

## 🛠️ Development

### Project Structure
```
AI_Hiring_Agent/
├── 📁 backend/                 # FastAPI Backend
│   ├── main.py                # Main application
│   ├── requirements.txt       # Python dependencies
│   └── temp_uploads/          # Temporary file storage
│
├── 📁 frontend/               # React Frontend
│   ├── 📁 src/
│   │   ├── 📁 components/     # React components
│   │   ├── 📁 services/       # API services
│   │   └── App.jsx           # Main application
│   ├── package.json          # Node.js dependencies
│   └── vite.config.js        # Vite configuration
│
├── 📁 agents/                # AI Agent System
│   ├── 📁 core/              # Core agent logic
│   ├── 📁 Resume_Parser/     # Resume processing
│   ├── 📁 Github_Parser/     # GitHub analysis
│   └── 📁 Linkedin_Parser/   # LinkedIn integration
│
└── 📄 Configuration Files
    ├── .gitignore            # Git ignore patterns
    ├── README.md             # This file
    └── requirements.txt      # Python dependencies
```

### Adding New Features

#### Backend Endpoints
```python
# Add new endpoint in backend/main.py
@app.post("/new-endpoint")
async def new_endpoint(data: YourModel):
    # Your logic here
    return {"result": "success"}
```

#### Frontend Components
```jsx
// Add new component in frontend/src/components/
import React from 'react';

export default function NewComponent() {
    return <div>Your component</div>;
}
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload-resume` | Upload resume file |
| `POST` | `/analyze-resume` | Analyze resume with query |
| `POST` | `/continue-conversation` | Continue conversation |
| `GET` | `/session/{session_id}` | Get session info |
| `DELETE` | `/session/{session_id}` | Delete session |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | API documentation |

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Application Settings
DEBUG=True
PORT=8000
```

#### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_UPLOAD_MAX_SIZE=10485760
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing
1. Upload various resume formats
2. Test different query types
3. Verify GitHub integration
4. Check LinkedIn functionality
5. Test error handling

## 🚀 Deployment

### Production Build
```bash
# Frontend production build
cd frontend
npm run build

# Backend production settings
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript/React
- Write comprehensive tests
- Update documentation for new features
- Use conventional commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangGraph** for workflow orchestration
- **LlamaIndex** for RAG capabilities
- **Azure OpenAI** for AI processing
- **FastAPI** for backend framework
- **React** for frontend framework
- **Tailwind CSS** for styling

## 📞 Support

For support, questions, or feedback:

- **Issues**: [GitHub Issues](https://github.com/kardwalker/AI_Hiring_Agent-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kardwalker/AI_Hiring_Agent-/discussions)
- **Email**: [Support Contact](mailto:support@example.com)

## 🔄 Changelog

### Version 2.0.0 (Current)
- ✨ Complete web application with React frontend
- ✨ FastAPI backend with multi-agent integration
- ✨ Real-time chat interface
- ✨ GitHub repository analysis
- ✨ LinkedIn profile integration
- ✨ Session management and conversation history

### Version 1.0.0
- 🎯 Initial multi-agent architecture
- 🎯 Basic resume parsing capabilities
- 🎯 Command-line interface

---

**🚀 Ready to revolutionize your hiring process with AI-powered resume analysis!**
