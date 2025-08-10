#!/usr/bin/env python3
"""
Test script for the Resume Analysis Agent with StateGraph workflow.
"""
import asyncio
import sys
import os

# Add the agents directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

async def test_agent():
    """Test the resume analysis agent."""
    try:
        from agents.core.agent import ResumeAnalysisAgent
        
        agent = ResumeAnalysisAgent()
        
        # Test with existing resume file
        resume_file = "test_resume_with_github.txt"
        
        if not os.path.exists(resume_file):
            print(f"❌ Test resume file not found: {resume_file}")
            return
        
        print("🧪 Testing Resume Analysis Agent")
        print("=" * 50)
        
        # Test queries
        queries = [
            "What are the main technical skills mentioned in this resume?",
            "Tell me about the GitHub repositories and projects",
            "What is the educational background?",
            "Summarize the work experience"
        ]
        
        session_id = "test_session"
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Test Query {i}: {query}")
            print("-" * 40)
            
            if i == 1:
                # First query - process full resume
                result = await agent.process_resume_and_query(resume_file, query, session_id)
            else:
                # Subsequent queries - continue conversation
                result = await agent.continue_conversation(query, session_id)
            
            print("📝 Answer:")
            print(result.get('final_answer', 'No answer generated'))
            print()
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are installed and paths are correct")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
