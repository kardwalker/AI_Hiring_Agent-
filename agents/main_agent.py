"""
AI Resume & Portfolio Assistant - Complete Multi-Agent Implementation
Using LangChain v0.3.x+, LangGraph v0.2.x+, Azure OpenAI, and Redis
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from enum import Enum

# Core Dependencies
from langchain.agents import create_openai_tools_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import JsonOutputParser

# LangGraph Dependencies
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.redis import RedisSaver
from langgraph.prebuilt import ToolNode

# Additional Libraries
import redis.asyncio as redis
from pydantic import BaseModel, Field
import requests
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
import ast
import subprocess
import tempfile
import base64

# State Management
class AnalysisState(TypedDict):
    """Main state object for the multi-agent workflow"""
    user_id: str
    session_id: str
    
    # Input Documents & Data
    resume_content: Optional[str]
    linkedin_profile: Optional[Dict]
    github_username: Optional[str]
    target_job_description: Optional[str]
    user_preferences: Dict
    
    # Analysis Results
    resume_analysis: Optional[Dict]
    linkedin_analysis: Optional[Dict]
    github_analysis: Optional[Dict]
    portfolio_analysis: Optional[Dict]
    job_matching_results: Optional[Dict]
    cover_letter_variations: Optional[List[Dict]]
    
    # Workflow Management
    current_step: str
    completed_steps: List[str]
    errors: List[str]
    recommendations: List[Dict]
    
    # Memory References
    long_term_memory: Dict
    session_memory: Dict

# Configuration
@dataclass
class Config:
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION: str = "2024-05-01-preview"
    AZURE_MODEL_NAME: str = "gpt-4o"
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # GitHub API Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN")
    
    # LinkedIn API Configuration (if available)
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET")

config = Config()

# Initialize Azure OpenAI
llm = AzureChatOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
    azure_deployment=config.AZURE_MODEL_NAME,
    temperature=0.3,
    max_tokens=4000
)

# Initialize Redis for checkpointing
async def get_redis_saver():
    redis_client = redis.from_url(config.REDIS_URL)
    return RedisSaver(redis_client)

# Document Processing Tools
@tool
async def parse_pdf_resume(file_path: str) -> str:
    """Parse PDF resume and extract text content"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

@tool
async def parse_docx_resume(file_path: str) -> str:
    """Parse DOCX resume and extract text content"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error parsing DOCX: {str(e)}"

@tool
async def fetch_github_profile(username: str) -> Dict:
    """Fetch comprehensive GitHub profile data"""
    headers = {"Authorization": f"token {config.GITHUB_TOKEN}"} if config.GITHUB_TOKEN else {}
    
    try:
        # Get user profile
        user_response = requests.get(f"https://api.github.com/users/{username}", headers=headers)
        user_data = user_response.json()
        
        # Get repositories
        repos_response = requests.get(f"https://api.github.com/users/{username}/repos", 
                                    headers=headers, params={"per_page": 100})
        repos_data = repos_response.json()
        
        # Get detailed repo analysis for top repositories
        detailed_repos = []
        for repo in repos_data[:10]:  # Analyze top 10 repos
            repo_detail = await analyze_repository_details(username, repo['name'], headers)
            detailed_repos.append(repo_detail)
        
        return {
            "profile": user_data,
            "repositories": repos_data,
            "detailed_analysis": detailed_repos
        }
    except Exception as e:
        return {"error": f"GitHub API error: {str(e)}"}

@tool
async def analyze_repository_details(owner: str, repo_name: str, headers: Dict) -> Dict:
    """Analyze individual repository for detailed technical insights"""
    try:
        # Get repository details
        repo_response = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}", headers=headers)
        repo_data = repo_response.json()
        
        # Get languages
        languages_response = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}/languages", headers=headers)
        languages_data = languages_response.json()
        
        # Get commits (last 30)
        commits_response = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}/commits", 
                                      headers=headers, params={"per_page": 30})
        commits_data = commits_response.json()
        
        # Get README content
        try:
            readme_response = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}/readme", headers=headers)
            readme_data = readme_response.json()
            readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
        except:
            readme_content = ""
        
        return {
            "repository": repo_data,
            "languages": languages_data,
            "recent_commits": commits_data,
            "readme_content": readme_content,
            "analysis_metadata": {
                "commit_frequency": len(commits_data),
                "language_diversity": len(languages_data),
                "documentation_quality": len(readme_content) > 100
            }
        }
    except Exception as e:
        return {"error": f"Repository analysis error: {str(e)}"}

# Agent Implementations

class ResumeAnalyzerAgent:
    """Agent 1: Resume Content & Structure Analyst"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
ROLE: Resume Content & Structure Analyst

RESPONSIBILITIES:
1. Parse resume content (PDF, DOCX, TXT formats)
2. Evaluate ATS compatibility (formatting, keywords, structure)
3. Assess content quality (achievements vs responsibilities)
4. Identify gaps and improvement opportunities
5. Generate quantified feedback scores

EVALUATION CRITERIA:
- Content Quality: Impact statements, quantifiable achievements (weight: 30%)
- ATS Optimization: Keyword relevance, formatting compliance (weight: 25%)
- Structure & Flow: Logical organization, readability (weight: 20%)
- Completeness: Required sections, contact info (weight: 15%)
- Industry Alignment: Role-specific requirements (weight: 10%)

OUTPUT FORMAT: Return valid JSON only with this structure:
{{
  "overall_score": int (1-10),
  "section_scores": {{
    "contact_info": int (1-10),
    "professional_summary": int (1-10),
    "experience": int (1-10),
    "skills": int (1-10),
    "education": int (1-10),
    "additional_sections": int (1-10)
  }},
  "ats_compatibility": {{
    "score": int (1-10),
    "issues": [list of issues],
    "recommendations": [list of recommendations]
  }},
  "content_analysis": {{
    "strengths": [list of strengths],
    "weaknesses": [list of weaknesses],
    "missing_elements": [list of missing elements],
    "keyword_analysis": {{}}
  }},
  "improvement_suggestions": [list of suggestions]
}}
            """),
            ("human", "Resume Content: {resume_content}\n\nTarget Job Description: {job_description}\n\nAnalyze this resume:")
        ])
        
    async def analyze(self, resume_content: str, job_description: str = "") -> Dict:
        """Analyze resume content and structure"""
        try:
            chain = self.prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "resume_content": resume_content,
                "job_description": job_description
            })
            return result
        except Exception as e:
            return {"error": f"Resume analysis error: {str(e)}"}

class LinkedInOptimizerAgent:
    """Agent 2: LinkedIn Profile Optimization Specialist"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
ROLE: LinkedIn Profile Optimization Specialist

RESPONSIBILITIES:
1. Analyze LinkedIn profile completeness and optimization
2. Evaluate headline, summary, and experience sections
3. Assess networking potential and content strategy
4. Provide SEO optimization recommendations
5. Compare profile strength against industry benchmarks

ANALYSIS DIMENSIONS:
- Profile Completeness: All sections filled, media uploads (weight: 25%)
- Headline Optimization: Keywords, value proposition clarity (weight: 20%)
- Summary Effectiveness: Storytelling, call-to-action (weight: 20%)
- Experience Descriptions: Achievement-focused, keyword-rich (weight: 15%)
- Skills & Endorsements: Relevant skills, endorsement count (weight: 10%)
- Network & Activity: Connection count, post engagement (weight: 10%)

OUTPUT: Return detailed optimization plan with specific text recommendations in JSON format.
            """),
            ("human", "LinkedIn Profile Data: {linkedin_data}\n\nTarget Industry: {target_industry}\n\nProvide optimization recommendations:")
        ])
        
    async def optimize(self, linkedin_data: Dict, target_industry: str = "") -> Dict:
        """Optimize LinkedIn profile"""
        try:
            chain = self.prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "linkedin_data": json.dumps(linkedin_data),
                "target_industry": target_industry
            })
            return result
        except Exception as e:
            return {"error": f"LinkedIn optimization error: {str(e)}"}

class GitHubParserAgent:
    """Agent 3: GitHub Repository Deep Analysis Specialist"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
ROLE: GitHub Repository Deep Analysis Specialist

RESPONSIBILITIES:
1. Parse GitHub profiles and extract comprehensive repository data
2. Analyze code quality, architecture patterns, and technical depth
3. Evaluate commit history, contribution patterns, and collaboration
4. Assess documentation quality and project completeness
5. Generate technical skill proficiency matrix from code analysis

TECHNICAL ANALYSIS FRAMEWORK:
- Code Quality: Clean code principles, design patterns, testing coverage (weight: 25%)
- Architecture: System design, scalability patterns, modularity (weight: 20%)
- Technology Proficiency: Language mastery, framework usage, modern practices (weight: 20%)
- Project Scope: Problem complexity, feature completeness, innovation (weight: 15%)
- Collaboration: Team projects, code reviews, open source contributions (weight: 10%)
- Documentation: READMEs, inline comments, API documentation (weight: 10%)

OUTPUT: Return comprehensive analysis in JSON format with skill proficiency matrix.
            """),
            ("human", "GitHub Profile Data: {github_data}\n\nAnalyze technical skills and project quality:")
        ])
        
    async def analyze_github(self, github_data: Dict) -> Dict:
        """Analyze GitHub profile and repositories"""
        try:
            chain = self.prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "github_data": json.dumps(github_data, indent=2)
            })
            return result
        except Exception as e:
            return {"error": f"GitHub analysis error: {str(e)}"}

class PortfolioEvaluatorAgent:
    """Agent 4: Portfolio Presentation & Professional Brand Analyst"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
ROLE: Portfolio Presentation & Professional Brand Analyst

RESPONSIBILITIES:
1. Evaluate overall portfolio presentation across platforms
2. Assess personal website/portfolio site effectiveness
3. Analyze project showcase strategy and narrative
4. Review professional branding consistency
5. Provide presentation enhancement recommendations

EVALUATION FRAMEWORK:
- Visual Presentation: Design quality, user experience, mobile responsiveness (weight: 25%)
- Content Strategy: Project selection, storytelling, impact communication (weight: 25%)
- Technical Demonstration: Live demos, code samples, architecture diagrams (weight: 20%)
- Professional Branding: Consistency across platforms, personal brand clarity (weight: 15%)
- Accessibility & Performance: Site speed, SEO, accessibility compliance (weight: 15%)

OUTPUT: Comprehensive portfolio optimization strategy with specific implementation steps in JSON format.
            """),
            ("human", "Portfolio Data: {portfolio_data}\n\nGitHub Analysis: {github_analysis}\n\nEvaluate portfolio presentation:")
        ])
        
    async def evaluate_portfolio(self, portfolio_data: Dict, github_analysis: Dict) -> Dict:
        """Evaluate portfolio presentation"""
        try:
            chain = self.prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "portfolio_data": json.dumps(portfolio_data),
                "github_analysis": json.dumps(github_analysis)
            })
            return result
        except Exception as e:
            return {"error": f"Portfolio evaluation error: {str(e)}"}

class JobMatcherAgent:
    """Agent 5: Job Market Intelligence & Matching Specialist"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
ROLE: Job Market Intelligence & Matching Specialist

RESPONSIBILITIES:
1. Analyze target job descriptions and requirements
2. Calculate profile-to-job compatibility scores using GitHub data
3. Identify skill gaps and market trends
4. Provide salary benchmarking insights
5. Generate job search strategy recommendations

MATCHING ALGORITHM:
- Technical Skills Match: Programming languages, frameworks, tools from GitHub (weight: 40%)
- Experience Level: Years, seniority, project complexity from repository analysis (weight: 25%)
- Industry Fit: Domain-specific projects, business problem solving (weight: 15%)
- Collaboration Skills: Open source contributions, team project involvement (weight: 10%)
- Innovation Factor: Unique projects, cutting-edge technology usage (weight: 10%)

OUTPUT: Comprehensive job market report with GitHub-validated skill assessments in JSON format.
            """),
            ("human", "Job Description: {job_description}\n\nCandidate Profile: {candidate_profile}\n\nGitHub Analysis: {github_analysis}\n\nCalculate match score and provide recommendations:")
        ])
        
    async def match_job(self, job_description: str, candidate_profile: Dict, github_analysis: Dict) -> Dict:
        """Match candidate profile with job requirements"""
        try:
            chain = self.prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "job_description": job_description,
                "candidate_profile": json.dumps(candidate_profile),
                "github_analysis": json.dumps(github_analysis)
            })
            return result
        except Exception as e:
            return {"error": f"Job matching error: {str(e)}"}

class CoverLetterGeneratorAgent:
    """Agent 6: Personalized Cover Letter Creation Specialist"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
ROLE: Personalized Cover Letter Creation Specialist

RESPONSIBILITIES:
1. Generate tailored cover letters for specific job applications
2. Integrate resume highlights with GitHub project demonstrations
3. Craft compelling narrative connecting technical experience to role
4. Ensure proper formatting and professional tone
5. Create multiple versions for A/B testing

GENERATION FRAMEWORK:
- Opening Hook: Attention-grabbing first paragraph with specific technical achievement
- Technical Value Proposition: 2-3 key projects from GitHub aligned with role requirements
- Problem-Solving Demonstration: Specific examples from repository analysis
- Cultural Fit: Company research integration with relevant project connections
- Call to Action: Professional closing with portfolio/GitHub references

OUTPUT: Multiple cover letter variations with GitHub project integration in JSON format.
            """),
            ("human", "Job Description: {job_description}\n\nResume Analysis: {resume_analysis}\n\nGitHub Analysis: {github_analysis}\n\nCompany Info: {company_info}\n\nGenerate personalized cover letter:")
        ])
        
    async def generate_cover_letter(self, job_description: str, resume_analysis: Dict, 
                                  github_analysis: Dict, company_info: str = "") -> Dict:
        """Generate personalized cover letter"""
        try:
            chain = self.prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "job_description": job_description,
                "resume_analysis": json.dumps(resume_analysis),
                "github_analysis": json.dumps(github_analysis),
                "company_info": company_info
            })
            return result
        except Exception as e:
            return {"error": f"Cover letter generation error: {str(e)}"}

# Memory Management
class MemoryManager:
    """Manages long-term and session memory using Redis"""
    
    def __init__(self, redis_url: str):
        self.redis_client = None
        self.redis_url = redis_url
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
        
    async def save_long_term_memory(self, user_id: str, memory_data: Dict):
        """Save long-term user memory"""
        key = f"user_memory:{user_id}"
        await self.redis_client.set(key, json.dumps(memory_data), ex=86400*30)  # 30 days
        
    async def load_long_term_memory(self, user_id: str) -> Dict:
        """Load long-term user memory"""
        key = f"user_memory:{user_id}"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else {}
        
    async def save_session_memory(self, session_id: str, memory_data: Dict):
        """Save session memory"""
        key = f"session_memory:{session_id}"
        await self.redis_client.set(key, json.dumps(memory_data), ex=3600)  # 1 hour
        
    async def load_session_memory(self, session_id: str) -> Dict:
        """Load session memory"""
        key = f"session_memory:{session_id}"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else {}

# Workflow Nodes
async def initialize_analysis(state: AnalysisState) -> AnalysisState:
    """Initialize analysis session"""
    state["current_step"] = "initialized"
    state["completed_steps"] = ["initialize_analysis"]
    state["session_memory"] = {
        "start_time": datetime.now().isoformat(),
        "analysis_type": "comprehensive"
    }
    return state

async def process_resume(state: AnalysisState) -> AnalysisState:
    """Process and analyze resume"""
    if state["resume_content"]:
        resume_agent = ResumeAnalyzerAgent(llm)
        analysis = await resume_agent.analyze(
            state["resume_content"],
            state.get("target_job_description", "")
        )
        state["resume_analysis"] = analysis
        state["completed_steps"].append("process_resume")
    return state

async def process_linkedin(state: AnalysisState) -> AnalysisState:
    """Process and optimize LinkedIn profile"""
    if state["linkedin_profile"]:
        linkedin_agent = LinkedInOptimizerAgent(llm)
        analysis = await linkedin_agent.optimize(
            state["linkedin_profile"],
            state.get("user_preferences", {}).get("target_industry", "")
        )
        state["linkedin_analysis"] = analysis
        state["completed_steps"].append("process_linkedin")
    return state

async def process_github(state: AnalysisState) -> AnalysisState:
    """Process and analyze GitHub profile"""
    if state["github_username"]:
        # Fetch GitHub data
        github_data = await fetch_github_profile(state["github_username"])
        
        # Analyze with AI agent
        github_agent = GitHubParserAgent(llm)
        analysis = await github_agent.analyze_github(github_data)
        
        state["github_analysis"] = analysis
        state["completed_steps"].append("process_github")
    return state

async def evaluate_portfolio(state: AnalysisState) -> AnalysisState:
    """Evaluate portfolio presentation"""
    portfolio_agent = PortfolioEvaluatorAgent(llm)
    
    # Combine available data for portfolio evaluation
    portfolio_data = {
        "resume_analysis": state.get("resume_analysis", {}),
        "linkedin_analysis": state.get("linkedin_analysis", {}),
    }
    
    analysis = await portfolio_agent.evaluate_portfolio(
        portfolio_data,
        state.get("github_analysis", {})
    )
    
    state["portfolio_analysis"] = analysis
    state["completed_steps"].append("evaluate_portfolio")
    return state

async def match_jobs(state: AnalysisState) -> AnalysisState:
    """Match profile with job requirements"""
    if state.get("target_job_description"):
        job_matcher = JobMatcherAgent(llm)
        
        candidate_profile = {
            "resume_analysis": state.get("resume_analysis", {}),
            "linkedin_analysis": state.get("linkedin_analysis", {}),
        }
        
        analysis = await job_matcher.match_job(
            state["target_job_description"],
            candidate_profile,
            state.get("github_analysis", {})
        )
        
        state["job_matching_results"] = analysis
        state["completed_steps"].append("match_jobs")
    return state

async def generate_cover_letters(state: AnalysisState) -> AnalysisState:
    """Generate personalized cover letters"""
    if state.get("target_job_description"):
        cover_letter_agent = CoverLetterGeneratorAgent(llm)
        
        variations = await cover_letter_agent.generate_cover_letter(
            state["target_job_description"],
            state.get("resume_analysis", {}),
            state.get("github_analysis", {}),
            state.get("user_preferences", {}).get("company_info", "")
        )
        
        state["cover_letter_variations"] = [variations]
        state["completed_steps"].append("generate_cover_letters")
    return state

async def synthesize_results(state: AnalysisState) -> AnalysisState:
    """Synthesize all analysis results and generate final recommendations"""
    
    # Collect all recommendations
    all_recommendations = []
    
    # Resume recommendations
    if state.get("resume_analysis"):
        all_recommendations.extend(state["resume_analysis"].get("improvement_suggestions", []))
    
    # LinkedIn recommendations  
    if state.get("linkedin_analysis"):
        all_recommendations.extend(state["linkedin_analysis"].get("recommendations", []))
    
    # GitHub recommendations
    if state.get("github_analysis"):
        all_recommendations.extend(state["github_analysis"].get("recommendations", {}).get("portfolio_improvements", []))
    
    # Portfolio recommendations
    if state.get("portfolio_analysis"):
        all_recommendations.extend(state["portfolio_analysis"].get("recommendations", []))
    
    # Job matching recommendations
    if state.get("job_matching_results"):
        all_recommendations.extend(state["job_matching_results"].get("recommendations", []))
    
    state["recommendations"] = all_recommendations
    state["current_step"] = "completed"
    state["completed_steps"].append("synthesize_results")
    
    return state

# Conditional Logic
def should_process_resume(state: AnalysisState) -> str:
    """Decide whether to process resume"""
    return "process_resume" if state.get("resume_content") else "process_linkedin"

def should_process_linkedin(state: AnalysisState) -> str:
    """Decide whether to process LinkedIn"""
    return "process_linkedin" if state.get("linkedin_profile") else "process_github"

def should_process_github(state: AnalysisState) -> str:
    """Decide whether to process GitHub"""
    return "process_github" if state.get("github_username") else "evaluate_portfolio"

# Main Workflow Graph
def create_workflow_graph():
    """Create the main LangGraph workflow"""
    
    workflow = StateGraph(AnalysisState)
    
    # Add nodes
    workflow.add_node("initialize_analysis", initialize_analysis)
    workflow.add_node("process_resume", process_resume)
    workflow.add_node("process_linkedin", process_linkedin)
    workflow.add_node("process_github", process_github)
    workflow.add_node("evaluate_portfolio", evaluate_portfolio)
    workflow.add_node("match_jobs", match_jobs)
    workflow.add_node("generate_cover_letters", generate_cover_letters)
    workflow.add_node("synthesize_results", synthesize_results)
    
    # Add edges
    workflow.add_edge(START, "initialize_analysis")
    workflow.add_edge("initialize_analysis", "process_resume")
    workflow.add_edge("process_resume", "process_linkedin")
    workflow.add_edge("process_linkedin", "process_github")
    workflow.add_edge("process_github", "evaluate_portfolio")
    workflow.add_edge("evaluate_portfolio", "match_jobs")
    workflow.add_edge("match_jobs", "generate_cover_letters")
    workflow.add_edge("generate_cover_letters", "synthesize_results")
    workflow.add_edge("synthesize_results", END)
    
    return workflow

# Main Application Class
class ResumeAssistantApp:
    """Main application orchestrating the multi-agent system"""
    
    def __init__(self):
        self.memory_manager = MemoryManager(config.REDIS_URL)
        self.workflow = None
        self.compiled_workflow = None
        
    async def initialize(self):
        """Initialize the application"""
        await self.memory_manager.initialize()
        
        # Create and compile workflow
        self.workflow = create_workflow_graph()
        
        # Get Redis saver for checkpointing
        redis_saver = await get_redis_saver()
        
        # Compile workflow with checkpointing
        self.compiled_workflow = self.workflow.compile(
            checkpointer=redis_saver,
            interrupt_before=[],  # Can add nodes to interrupt before
            interrupt_after=[]    # Can add nodes to interrupt after
        )
        
    async def analyze_profile(self, 
                            user_id: str,
                            session_id: str,
                            resume_content: Optional[str] = None,
                            linkedin_profile: Optional[Dict] = None,
                            github_username: Optional[str] = None,
                            target_job_description: Optional[str] = None,
                            user_preferences: Dict = None) -> Dict:
        """Run complete profile analysis"""
        
        # Initialize state
        initial_state: AnalysisState = {
            "user_id": user_id,
            "session_id": session_id,
            "resume_content": resume_content,
            "linkedin_profile": linkedin_profile,
            "github_username": github_username,
            "target_job_description": target_job_description,
            "user_preferences": user_preferences or {},
            
            # Initialize other fields
            "resume_analysis": None,
            "linkedin_analysis": None,
            "github_analysis": None,
            "portfolio_analysis": None,
            "job_matching_results": None,
            "cover_letter_variations": None,
            
            "current_step": "starting",
            "completed_steps": [],
            "errors": [],
            "recommendations": [],
            
            "long_term_memory": await self.memory_manager.load_long_term_memory(user_id),
            "session_memory": {}
        }
        
        # Create thread config for checkpointing
        thread_config = {"configurable": {"thread_id": session_id}}
        
        try:
            # Run the workflow
            result = await self.compiled_workflow.ainvoke(
                initial_state,
                config=thread_config
            )
            
            # Save memories
            await self.memory_manager.save_long_term_memory(user_id, result["long_term_memory"])
            await self.memory_manager.save_session_memory(session_id, result["session_memory"])
            
            return {
                "success": True,
                "analysis_results": {
                    "resume_analysis": result.get("resume_analysis"),
                    "linkedin_analysis": result.get("linkedin_analysis"),
                    "github_analysis": result.get("github_analysis"),
                    "portfolio_analysis": result.get("portfolio_analysis"),
                    "job_matching_results": result.get("job_matching_results"),
                    "cover_letter_variations": result.get("cover_letter_variations")
                },
                "recommendations": result.get("recommendations", []),
                "completed_steps": result.get("completed_steps", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "completed_steps": initial_state.get("completed_steps", [])
            }

# Usage Example
async def main():
    """Example usage of the multi-agent system"""
    
    # Initialize application
    app = ResumeAssistantApp()
    await app.initialize()
    
    # Example analysis
    result = await app.analyze_profile(
        user_id="user123",
        session_id="session456", 
        resume_content="Sample resume content...",
        github_username="johndoe",
        target_job_description="Software Engineer position at tech company...",
        user_preferences={
            "target_industry": "Technology",
            "preferred_locations": ["San Francisco", "Remote"],
            "salary_expectations": {"min": 120000, "max": 180000}
        }
    )
    
    print("Analysis Results:")
    print(json.dumps(result, indent=2))

# FastAPI Integration for REST API
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import aiofiles

# Pydantic Models for API
class AnalysisRequest(BaseModel):
    user_id: str
    github_username: Optional[str] = None
    linkedin_profile_url: Optional[str] = None
    target_job_description: Optional[str] = None
    user_preferences: Dict = {}

class AnalysisResponse(BaseModel):
    success: bool
    session_id: str
    analysis_results: Optional[Dict] = None
    recommendations: List[Dict] = []
    error: Optional[str] = None

# Initialize FastAPI app
api_app = FastAPI(title="AI Resume & Portfolio Assistant API", version="1.0.0")

# Add CORS middleware
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global app instance
resume_app = None

@api_app.on_event("startup")
async def startup_event():
    """Initialize the resume assistant app on startup"""
    global resume_app
    resume_app = ResumeAssistantApp()
    await resume_app.initialize()

@api_app.post("/analyze", response_model=AnalysisResponse)
async def analyze_profile_endpoint(request: AnalysisRequest):
    """Analyze user profile endpoint"""
    try:
        session_id = str(uuid.uuid4())
        
        result = await resume_app.analyze_profile(
            user_id=request.user_id,
            session_id=session_id,
            github_username=request.github_username,
            target_job_description=request.target_job_description,
            user_preferences=request.user_preferences
        )
        
        return AnalysisResponse(
            success=result["success"],
            session_id=session_id,
            analysis_results=result.get("analysis_results"),
            recommendations=result.get("recommendations", []),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_app.post("/upload-resume")
async def upload_resume(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    github_username: Optional[str] = Form(None),
    target_job_description: Optional[str] = Form(None)
):
    """Upload and analyze resume file"""
    try:
        session_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        temp_file_path = f"/tmp/{file.filename}"
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Parse resume content based on file type
        resume_content = ""
        if file.filename.endswith('.pdf'):
            resume_content = await parse_pdf_resume(temp_file_path)
        elif file.filename.endswith('.docx'):
            resume_content = await parse_docx_resume(temp_file_path)
        else:
            resume_content = content.decode('utf-8')
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        # Run analysis
        result = await resume_app.analyze_profile(
            user_id=user_id,
            session_id=session_id,
            resume_content=resume_content,
            github_username=github_username,
            target_job_description=target_job_description
        )
        
        return AnalysisResponse(
            success=result["success"],
            session_id=session_id,
            analysis_results=result.get("analysis_results"),
            recommendations=result.get("recommendations", []),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_app.get("/analysis/{session_id}")
async def get_analysis_results(session_id: str):
    """Get analysis results by session ID"""
    try:
        # Load session memory
        session_memory = await resume_app.memory_manager.load_session_memory(session_id)
        
        if not session_memory:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return session_memory
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_app.post("/generate-cover-letter")
async def generate_cover_letter_endpoint(
    user_id: str = Form(...),
    job_description: str = Form(...),
    company_name: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Generate cover letter for specific job"""
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
            
        # Load previous analysis results
        session_memory = await resume_app.memory_manager.load_session_memory(session_id)
        
        if not session_memory:
            raise HTTPException(status_code=404, detail="Previous analysis not found")
        
        # Generate cover letter using previous analysis
        cover_letter_agent = CoverLetterGeneratorAgent(llm)
        
        cover_letter = await cover_letter_agent.generate_cover_letter(
            job_description=job_description,
            resume_analysis=session_memory.get("resume_analysis", {}),
            github_analysis=session_memory.get("github_analysis", {}),
            company_info=company_name
        )
        
        return {
            "success": True,
            "cover_letter": cover_letter,
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_app.get("/user-profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user's long-term profile and history"""
    try:
        memory = await resume_app.memory_manager.load_long_term_memory(user_id)
        return {
            "success": True,
            "profile": memory
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Batch Processing for Multiple Job Applications
class BatchJobMatcher:
    """Handle batch job matching for multiple positions"""
    
    def __init__(self, resume_app: ResumeAssistantApp):
        self.resume_app = resume_app
        
    async def match_multiple_jobs(self, 
                                user_id: str, 
                                job_descriptions: List[str], 
                                user_profile: Dict) -> List[Dict]:
        """Match user profile against multiple job descriptions"""
        
        results = []
        job_matcher = JobMatcherAgent(llm)
        
        # Load user's GitHub analysis if available
        long_term_memory = await self.resume_app.memory_manager.load_long_term_memory(user_id)
        github_analysis = long_term_memory.get("github_analysis_cache", {})
        
        for i, job_desc in enumerate(job_descriptions):
            try:
                match_result = await job_matcher.match_job(
                    job_description=job_desc,
                    candidate_profile=user_profile,
                    github_analysis=github_analysis
                )
                
                results.append({
                    "job_index": i,
                    "job_description_preview": job_desc[:200] + "...",
                    "match_results": match_result
                })
                
            except Exception as e:
                results.append({
                    "job_index": i,
                    "error": str(e)
                })
                
        return results

@api_app.post("/batch-job-match")
async def batch_job_match_endpoint(
    user_id: str = Form(...),
    job_descriptions: List[str] = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Match user profile against multiple job descriptions"""
    try:
        # Load user profile
        if session_id:
            session_memory = await resume_app.memory_manager.load_session_memory(session_id)
            user_profile = {
                "resume_analysis": session_memory.get("resume_analysis", {}),
                "linkedin_analysis": session_memory.get("linkedin_analysis", {})
            }
        else:
            long_term_memory = await resume_app.memory_manager.load_long_term_memory(user_id)
            user_profile = long_term_memory.get("user_profile", {})
            
        # Run batch matching
        batch_matcher = BatchJobMatcher(resume_app)
        results = await batch_matcher.match_multiple_jobs(
            user_id=user_id,
            job_descriptions=job_descriptions,
            user_profile=user_profile
        )
        
        return {
            "success": True,
            "matches": results,
            "total_jobs": len(job_descriptions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Job Board Integration
class JobBoardIntegrator:
    """Integrate with popular job boards for real-time job matching"""
    
    def __init__(self):
        self.supported_boards = ["indeed", "linkedin", "glassdoor"]
        
    async def search_jobs(self, keywords: str, location: str, board: str = "indeed") -> List[Dict]:
        """Search for jobs on specified job board (placeholder implementation)"""
        
        # This would integrate with actual job board APIs
        # For now, returning mock data
        
        mock_jobs = [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": location,
                "description": f"Looking for experienced engineer with {keywords} skills...",
                "url": "https://example.com/job1",
                "salary_range": "$120k - $180k",
                "posted_date": "2024-01-15"
            },
            {
                "title": "Full Stack Developer",
                "company": "Startup Inc",
                "location": location,
                "description": f"Dynamic startup seeking {keywords} developer...",
                "url": "https://example.com/job2",
                "salary_range": "$100k - $150k",
                "posted_date": "2024-01-14"
            }
        ]
        
        return mock_jobs

@api_app.get("/job-search")
async def search_jobs_endpoint(
    keywords: str,
    location: str,
    job_board: str = "indeed",
    user_id: Optional[str] = None
):
    """Search for relevant jobs and optionally match against user profile"""
    try:
        job_integrator = JobBoardIntegrator()
        jobs = await job_integrator.search_jobs(keywords, location, job_board)
        
        # If user_id provided, calculate match scores
        if user_id:
            long_term_memory = await resume_app.memory_manager.load_long_term_memory(user_id)
            user_profile = {
                "resume_analysis": long_term_memory.get("resume_analysis", {}),
                "github_analysis": long_term_memory.get("github_analysis_cache", {})
            }
            
            job_matcher = JobMatcherAgent(llm)
            
            # Add match scores to jobs
            for job in jobs:
                try:
                    match_result = await job_matcher.match_job(
                        job_description=job["description"],
                        candidate_profile=user_profile,
                        github_analysis=user_profile["github_analysis"]
                    )
                    job["match_score"] = match_result.get("overall_match_score", 0)
                    job["match_details"] = match_result
                except:
                    job["match_score"] = 0
            
            # Sort by match score
            jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return {
            "success": True,
            "jobs": jobs,
            "total_found": len(jobs),
            "search_params": {
                "keywords": keywords,
                "location": location,
                "job_board": job_board
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Insights
class AnalyticsEngine:
    """Provide analytics and insights on user's career progress"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        
    async def generate_career_insights(self, user_id: str) -> Dict:
        """Generate comprehensive career insights for user"""
        
        long_term_memory = await self.memory_manager.load_long_term_memory(user_id)
        
        # Analyze improvement trends
        improvement_history = long_term_memory.get("improvement_tracking", {})
        
        # Calculate skill growth
        github_cache = long_term_memory.get("github_analysis_cache", {})
        skill_matrix = github_cache.get("skill_matrix", {})
        
        # Generate market positioning insights
        insights = {
            "skill_proficiency_trends": self._analyze_skill_trends(improvement_history),
            "market_positioning": self._analyze_market_position(skill_matrix),
            "career_recommendations": self._generate_career_recommendations(long_term_memory),
            "interview_preparation": self._generate_interview_prep(long_term_memory),
            "salary_insights": self._analyze_salary_potential(skill_matrix, long_term_memory)
        }
        
        return insights
    
    def _analyze_skill_trends(self, improvement_history: Dict) -> Dict:
        """Analyze skill development trends"""
        # Implementation for skill trend analysis
        return {
            "trending_up": ["Python", "React", "AWS"],
            "needs_attention": ["System Design", "Leadership"],
            "newly_acquired": ["Docker", "Kubernetes"]
        }
    
    def _analyze_market_position(self, skill_matrix: Dict) -> Dict:
        """Analyze market positioning"""
        return {
            "competitiveness": "Strong",
            "unique_strengths": ["Full-stack expertise", "Open source contributions"],
            "market_demand": "High",
            "differentiation_opportunities": ["AI/ML specialization", "DevOps expertise"]
        }
    
    def _generate_career_recommendations(self, memory: Dict) -> List[str]:
        """Generate career advancement recommendations"""
        return [
            "Consider pursuing cloud architecture certification",
            "Contribute to more open source projects in AI/ML",
            "Build portfolio showcasing system design skills",
            "Network with industry leaders in target companies"
        ]
    
    def _generate_interview_prep(self, memory: Dict) -> Dict:
        """Generate interview preparation recommendations"""
        return {
            "technical_focus_areas": ["System Design", "Data Structures", "API Design"],
            "behavioral_preparation": ["Leadership examples", "Project management stories"],
            "company_research": ["Recent product launches", "Engineering culture", "Tech stack"]
        }
    
    def _analyze_salary_potential(self, skill_matrix: Dict, memory: Dict) -> Dict:
        """Analyze salary potential based on skills and market"""
        return {
            "estimated_range": "$140k - $200k",
            "market_percentile": "75th",
            "salary_growth_factors": ["AWS certification", "Team leadership experience"],
            "negotiation_strengths": ["Unique skill combination", "Strong GitHub profile"]
        }

@api_app.get("/analytics/{user_id}")
async def get_career_analytics(user_id: str):
    """Get comprehensive career analytics for user"""
    try:
        analytics_engine = AnalyticsEngine(resume_app.memory_manager)
        insights = await analytics_engine.generate_career_insights(user_id)
        
        return {
            "success": True,
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check and System Status
@api_app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        await resume_app.memory_manager.redis_client.ping()
        
        # Test Azure OpenAI connection
        test_response = await llm.ainvoke("Test connection")
        
        return {
            "status": "healthy",
            "services": {
                "redis": "connected",
                "azure_openai": "connected",
                "workflow": "ready"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Run the application
if __name__ == "__main__":
    import uvicorn
    # For development - run with: python agents/main_agent.py
    # Module path should reference this file's module (agents.main_agent:api_app)
    uvicorn.run(
        "agents.main_agent:api_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Deployment Configuration
"""
Production deployment configuration:

1. Environment Variables:
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_API_KEY
   - REDIS_URL
   - GITHUB_TOKEN
   - LINKEDIN_CLIENT_ID (optional)
   - LINKEDIN_CLIENT_SECRET (optional)

2. Docker Compose:
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  resume_assistant:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    depends_on:
      - redis

volumes:
  redis_data:

3. Kubernetes Deployment:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: resume-assistant
  template:
    metadata:
      labels:
        app: resume-assistant
    spec:
      containers:
      - name: resume-assistant
        image: resume-assistant:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_OPENAI_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: endpoint
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: api-key

4. Monitoring & Observability:
   - Prometheus metrics
   - Grafana dashboards
   - ELK stack for logging
   - Health check endpoints
   - Performance monitoring

5. Security:
   - API rate limiting
   - Authentication/Authorization
   - Input validation
   - Data encryption
   - GDPR compliance
"""