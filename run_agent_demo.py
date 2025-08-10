"""
Resume Analysis Agent - Complete Workflow Demo

This script demonstrates the full StateGraph workflow for resume analysis:
1. Process resume (PDF/TXT/DOCX)
2. Extract GitHub and LinkedIn links
3. Analyze profiles and repositories
4. Answer user queries using BM25 + Vector search
5. Multi-turn conversation capability
"""
import asyncio
import sys
import os
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Resume_Praser'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Github_Praser'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Linkedin_Praser'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'core'))

async def demo_workflow():
    """Demo the complete workflow."""
    try:
        from agent import ResumeAnalysisAgent
        
        print("🚀 AI RESUME ANALYSIS AGENT - STATEGRAPH WORKFLOW")
        print("=" * 60)
        print("Features:")
        print("✅ Multi-format resume processing (PDF, TXT, DOCX, MD)")
        print("✅ GitHub profile and repository analysis")
        print("✅ LinkedIn profile analysis with AI summaries")
        print("✅ BM25 + Vector search with Maximal Marginal Relevance")
        print("✅ Multi-turn conversations with memory")
        print("✅ StateGraph workflow orchestration")
        print("✅ Persistent Chroma vector storage in ./resume_username/")
        print()
        
        # Initialize agent
        agent = ResumeAnalysisAgent()
        session_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Show existing users if any
        existing_users = agent.list_existing_users()
        if existing_users:
            print(f"📁 Existing persistent vector stores found for users: {', '.join(existing_users)}")
            print("   These will be reused if processing the same resumes.")
        else:
            print("📁 No existing persistent vector stores found - will create new ones.")
        print()
        
        # Demo with test resume
        resume_file = "test_resume_with_github.txt"
        
        if not os.path.exists(resume_file):
            print(f"❌ Demo resume file not found: {resume_file}")
            print("Creating a simple test resume...")
            
            # Create a simple test resume
            test_content = """
JOHN DOE
Software Engineer

Contact: john.doe@email.com | +1-555-123-4567
GitHub: https://github.com/johndoe
LinkedIn: https://linkedin.com/in/johndoe

SUMMARY
Experienced software engineer with 5+ years in full-stack development.
Passionate about Python, machine learning, and cloud technologies.

EXPERIENCE
Senior Software Engineer - Tech Corp (2021-Present)
• Developed scalable web applications using Python and React
• Led team of 5 developers on cloud migration projects
• Implemented CI/CD pipelines reducing deployment time by 40%

Software Developer - StartupXYZ (2019-2021)
• Built REST APIs using Django and PostgreSQL
• Collaborated on machine learning projects
• Improved system performance by 25%

EDUCATION
BS Computer Science - University of Technology (2019)

SKILLS
Python, JavaScript, React, Django, AWS, Docker, PostgreSQL, Machine Learning

PROJECTS
• Personal Portfolio: https://github.com/johndoe/portfolio
• ML Classifier: https://github.com/johndoe/ml-project
• Web Scraper: https://github.com/johndoe/scraper-tool
"""
            with open(resume_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            print(f"✅ Created test resume: {resume_file}")
        
        print(f"\n🔄 WORKFLOW DEMONSTRATION")
        print(f"Resume: {resume_file}")
        print("-" * 40)
        
        # Demo queries
        demo_queries = [
            "What are the main technical skills and programming languages?",
            "Tell me about the GitHub repositories and projects",
            "What is the work experience and career progression?",
            "Summarize the educational background and qualifications",
            "What machine learning experience does this person have?"
        ]
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n🤖 QUERY {i}: {query}")
            print("🔄 Processing...")
            
            try:
                if i == 1:
                    # First query - process full resume
                    result = await agent.process_resume_and_query(resume_file, query, session_id)
                    
                    # Show workflow completion status
                    if result.get('resume_data'):
                        print("✅ Resume processed successfully")
                    if result.get('github_analysis'):
                        github_summary = result['github_analysis'].get('summary', {})
                        print(f"✅ GitHub analysis: {github_summary.get('total_links', 0)} links found")
                    if result.get('linkedin_analysis'):
                        if result['linkedin_analysis'].get('linkedin_found'):
                            print("✅ LinkedIn profile analyzed")
                        else:
                            print("ℹ️  LinkedIn profile not found or limited access")
                    
                else:
                    # Subsequent queries - continue conversation
                    result = await agent.continue_conversation(query, session_id)
                
                print("\n📝 **ANSWER:**")
                print(result.get('final_answer', 'No answer generated'))
                
                # Show retrieval info
                if result.get('retrieved_docs'):
                    print(f"\n📊 Retrieved {len(result['retrieved_docs'])} relevant document chunks")
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print(f"\n🎉 WORKFLOW DEMONSTRATION COMPLETED!")
        print("The agent successfully:")
        print("✅ Processed the resume and extracted sections")
        print("✅ Analyzed GitHub links and repositories") 
        print("✅ Processed LinkedIn profile information")
        print("✅ Used BM25 + Vector search for query answering")
        print("✅ Maintained conversation context across multiple queries")
        print("✅ Created persistent Chroma vector store in ./resume_username/")
        print()
        
        # Show created vector store info
        created_users = agent.list_existing_users()
        if created_users:
            print(f"📁 Persistent vector stores created for: {', '.join(created_users)}")
            print("   You can query these resumes again later without reprocessing!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install langgraph langchain-openai langchain-community rank-bm25 faiss-cpu")
    except Exception as e:
        print(f"❌ Demo error: {e}")

async def interactive_mode():
    """Run in interactive mode."""
    try:
        from agent import ResumeAnalysisAgent
        
        print("🤖 AI Resume Analysis Agent - Interactive Mode")
        print("=" * 50)
        
        agent = ResumeAnalysisAgent()
        session_id = f"interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Show existing users
        existing_users = agent.list_existing_users()
        if existing_users:
            print(f"📁 Found existing users: {', '.join(existing_users)}")
            print("   You can ask questions about previously processed resumes.")
            
            use_existing = input("Do you want to continue with an existing user? (y/n): ").strip().lower()
            if use_existing == 'y':
                print("Available users:")
                for i, user in enumerate(existing_users, 1):
                    print(f"  {i}. {user}")
                
                try:
                    choice = int(input("Select user number: ")) - 1
                    if 0 <= choice < len(existing_users):
                        username = existing_users[choice]
                        print(f"Selected user: {username}")
                        
                        # Continue conversation without processing new resume
                        while True:
                            query = input(f"\n❓ What would you like to know about {username}'s resume? ").strip()
                            if query.lower() in ['quit', 'exit', 'q']:
                                break
                            
                            result = await agent.continue_conversation(query, session_id, username)
                            print(f"\n🤖 **Answer:**")
                            print(result.get('final_answer', 'No answer generated'))
                        
                        print("\n👋 Session ended. Goodbye!")
                        return
                except (ValueError, IndexError):
                    print("Invalid selection. Continuing with new resume...")
        
        print()
        
        # Get resume file
        resume_file = input("📁 Enter path to resume file: ").strip().strip('"\'')
        
        if not os.path.exists(resume_file):
            print(f"❌ File not found: {resume_file}")
            return
        
        print(f"\n🔄 Initializing analysis for: {os.path.basename(resume_file)}")
        print("This includes processing resume, GitHub, and LinkedIn analysis...")
        
        # First query
        query = input("\n❓ What would you like to know about this resume? ").strip()
        
        # Process first query
        result = await agent.process_resume_and_query(resume_file, query, session_id)
        print(f"\n🤖 **Answer:**")
        print(result.get('final_answer', 'No answer generated'))
        
        # Continue conversation
        while True:
            print("\n" + "-" * 50)
            next_query = input("❓ Any other questions? (or 'quit' to exit): ").strip()
            
            if next_query.lower() in ['quit', 'exit', 'q']:
                break
            
            if next_query:
                result = await agent.continue_conversation(next_query, session_id)
                print(f"\n🤖 **Answer:**")
                print(result.get('final_answer', 'No answer generated'))
        
        print("\n👋 Session ended. Goodbye!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main function with mode selection."""
    print("🚀 AI Resume Analysis Agent")
    print("=" * 30)
    print("Select mode:")
    print("1. Demo workflow (automatic)")
    print("2. Interactive mode")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        await demo_workflow()
    elif choice == "2":
        await interactive_mode()
    else:
        print("Invalid choice. Running demo workflow...")
        await demo_workflow()

if __name__ == "__main__":
    asyncio.run(main())
