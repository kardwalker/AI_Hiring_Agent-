# AI Resume Analyzer - Web Application

A comprehensive web application for AI-powered resume analysis with GitHub and LinkedIn integration.

## Architecture

### Frontend (React + Vite)
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **File Upload**: React Dropzone
- **Notifications**: React Hot Toast
- **Icons**: Lucide React

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **AI Integration**: Custom agent system
- **File Processing**: Multi-format resume support
- **Session Management**: In-memory session storage
- **CORS**: Configured for frontend integration

## Features

✅ **Multi-format Resume Support**: PDF, TXT, DOCX, MD  
✅ **AI-Powered Analysis**: Advanced text processing and insights  
✅ **GitHub Integration**: Repository and profile analysis  
✅ **LinkedIn Integration**: Professional profile insights  
✅ **Real-time Processing**: Async processing with status updates  
✅ **Conversation Memory**: Multi-turn question answering  
✅ **Responsive Design**: Mobile-friendly interface  
✅ **Session Management**: File upload and conversation persistence  

## Quick Start

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.8+ (for backend)
- Virtual environment activated

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies (ensure main project venv is activated)
pip install -r requirements.txt

# Start the FastAPI server
python main.py
```

Backend will run on: http://localhost:8000

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on: http://localhost:3000

## API Endpoints

### File Management
- `POST /upload-resume` - Upload resume file
- `GET /session/{session_id}` - Get session info
- `DELETE /session/{session_id}` - Delete session
- `GET /sessions` - List active sessions

### Analysis
- `POST /analyze-resume` - Analyze resume with query
- `POST /continue-conversation` - Continue conversation

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## Usage Flow

1. **Upload Resume**: Drag & drop or select resume file
2. **Ask Questions**: Use suggested queries or custom questions
3. **Get Insights**: Receive AI-powered analysis
4. **Continue Conversation**: Ask follow-up questions
5. **Reset**: Upload new resume for fresh analysis

## Development

### Frontend Development
```bash
cd frontend
npm run dev    # Start dev server
npm run build  # Build for production
npm run preview # Preview production build
```

### Backend Development
```bash
cd backend
python main.py  # Start with auto-reload
```

## Environment Variables

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
VITE_DEV_MODE=true
```

### Backend
Uses the main project's `.env` file for AI service configuration.

## File Structure

```
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Backend dependencies
│   └── temp_uploads/        # Temporary file storage
│
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API service layer
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
```

## Error Handling

- **File Upload**: Validates file types and size
- **API Errors**: User-friendly error messages
- **Network Issues**: Retry mechanisms and timeouts
- **Session Management**: Graceful session cleanup

## Security Considerations

- File type validation
- CORS configuration
- Session isolation
- Temporary file cleanup
- Input sanitization

## Performance

- Lazy loading components
- Optimized file uploads
- Async processing
- Response caching
- Minimal bundle size

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

This project is licensed under the MIT License.
