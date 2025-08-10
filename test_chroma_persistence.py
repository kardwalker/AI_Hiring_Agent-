"""
Test script for Chroma persistence functionality
"""
import asyncio
import os
import sys
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'core'))

async def test_chroma_persistence():
    """Test the Chroma persistence functionality."""
    try:
        from agent import ResumeAnalysisAgent, extract_username_from_resume, load_existing_vectorstore
        
        print("🧪 TESTING CHROMA PERSISTENCE FUNCTIONALITY")
        print("=" * 50)
        
        agent = ResumeAnalysisAgent()
        
        # Test username extraction
        test_files = [
            "john_doe_resume.pdf",
            "Jane_Smith_CV.docx", 
            "resume.txt",
            "/path/to/Sarah_Wilson_2024.pdf"
        ]
        
        print("1. Testing username extraction:")
        for file_path in test_files:
            username = extract_username_from_resume(file_path)
            print(f"   {file_path} → {username}")
        
        print("\n2. Testing existing vector stores:")
        existing_users = agent.list_existing_users()
        if existing_users:
            print(f"   Found existing users: {', '.join(existing_users)}")
            
            # Test loading an existing vector store
            for user in existing_users[:1]:  # Test first user only
                print(f"   Testing load for user: {user}")
                vectorstore = await load_existing_vectorstore(user)
                if vectorstore:
                    print(f"   ✅ Successfully loaded vector store for {user}")
                    # Test a simple search
                    try:
                        results = await vectorstore.asimilarity_search("skills", k=2)
                        print(f"   📊 Sample search returned {len(results)} results")
                    except Exception as e:
                        print(f"   ⚠️  Search test failed: {e}")
                else:
                    print(f"   ❌ Failed to load vector store for {user}")
        else:
            print("   No existing vector stores found")
        
        print("\n3. Testing directory structure:")
        current_dir = "."
        resume_dirs = [d for d in os.listdir(current_dir) if os.path.isdir(d) and d.startswith("resume_")]
        if resume_dirs:
            print(f"   Found resume directories: {resume_dirs}")
            for dir_name in resume_dirs:
                files = os.listdir(dir_name)
                print(f"   {dir_name}/: {len(files)} files")
        else:
            print("   No resume_* directories found")
        
        print("\n✅ Chroma persistence test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the agent.py file is in agents/core/ directory")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chroma_persistence())
