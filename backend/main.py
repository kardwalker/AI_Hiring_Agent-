"""
FastAPI Backend for AI Resume Analysis Agent
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
import uuid
import asyncio
import logging
from pathlib import Path
import shutil

# Add the agents path to sys.path
current_dir = Path(__file__).parent
agents_path = current_dir.parent / "agents"
sys.path.append(str(agents_path))

# Import the agent components
from core.agent import ResumeAnalysisAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Resume Analysis Agent API",
    description="Backend API for AI-powered resume analysis with GitHub and LinkedIn integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
agent = ResumeAnalysisAgent()
active_sessions: Dict[str, Dict[str, Any]] = {}

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    status: str
    message: str

class AnalysisResponse(BaseModel):
    session_id: str
    status: str
    answer: str
    resume_data: Optional[Dict[str, Any]] = None
    github_analysis: Optional[Dict[str, Any]] = None
    linkedin_analysis: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    message: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Resume Analysis Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01"}

@app.post("/upload-resume", response_model=SessionResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and process a resume file
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.txt', '.docx', '.md'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create temporary directory for this session
        temp_dir = Path(f"temp_uploads/{session_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize session
        active_sessions[session_id] = {
            "file_path": str(file_path),
            "filename": file.filename,
            "status": "uploaded",
            "processed": False
        }
        
        logger.info(f"File uploaded successfully: {file.filename} (Session: {session_id})")
        
        return SessionResponse(
            session_id=session_id,
            status="uploaded",
            message=f"File '{file.filename}' uploaded successfully. Ready for analysis."
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-resume", response_model=AnalysisResponse)
async def analyze_resume(query_request: QueryRequest):
    """
    Analyze the uploaded resume and answer a query
    """
    try:
        session_id = query_request.session_id
        query = query_request.query
        
        # Check if session exists
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail="Session not found. Please upload a resume first."
            )
        
        session_data = active_sessions[session_id]
        file_path = session_data["file_path"]
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Resume file not found. Please upload again."
            )
        
        logger.info(f"Processing query for session {session_id}: {query}")
        
        # Process the resume and query using the agent
        result = await agent.process_resume_and_query(
            resume_file=file_path,
            query=query,
            session_id=session_id
        )
        
        # Update session status
        active_sessions[session_id]["processed"] = True
        active_sessions[session_id]["status"] = "completed"
        
        # Extract components from result
        final_answer = result.get("final_answer", "No answer available")
        resume_data = result.get("resume_data")
        github_analysis = result.get("github_analysis") 
        linkedin_analysis = result.get("linkedin_analysis")
        
        logger.info(f"Analysis completed for session {session_id}")
        
        return AnalysisResponse(
            session_id=session_id,
            status="completed",
            answer=final_answer,
            resume_data=resume_data,
            github_analysis=github_analysis,
            linkedin_analysis=linkedin_analysis
        )
        
    except Exception as e:
        logger.error(f"Error analyzing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/continue-conversation", response_model=AnalysisResponse)
async def continue_conversation(query_request: QueryRequest):
    """
    Continue conversation with follow-up questions
    """
    try:
        session_id = query_request.session_id
        query = query_request.query
        
        # Check if session exists and is processed
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail="Session not found. Please upload and analyze a resume first."
            )
        
        session_data = active_sessions[session_id]
        
        if not session_data.get("processed", False):
            raise HTTPException(
                status_code=400,
                detail="Resume not yet analyzed. Please analyze first."
            )
        
        file_path = session_data["file_path"]
        
        logger.info(f"Continuing conversation for session {session_id}: {query}")
        
        # Process follow-up query
        result = await agent.process_resume_and_query(
            resume_file=file_path,
            query=query,
            session_id=session_id
        )
        
        final_answer = result.get("final_answer", "No answer available")
        
        return AnalysisResponse(
            session_id=session_id,
            status="completed",
            answer=final_answer
        )
        
    except Exception as e:
        logger.error(f"Error in conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a session
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and cleanup files
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Clean up files
        temp_dir = Path(f"temp_uploads/{session_id}")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        # Remove from active sessions
        del active_sessions[session_id]
        
        return {"message": f"Session {session_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_active_sessions():
    """
    List all active sessions
    """
    return {
        "active_sessions": len(active_sessions),
        "sessions": {
            session_id: {
                "filename": data.get("filename"),
                "status": data.get("status"),
                "processed": data.get("processed", False)
            }
            for session_id, data in active_sessions.items()
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Create temp uploads directory
    os.makedirs("temp_uploads", exist_ok=True)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
