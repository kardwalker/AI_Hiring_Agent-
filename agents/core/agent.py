
from pydantic import Field, BaseModel
from typing import TypedDict, List, Optional, Any, Dict
from dotenv import load_dotenv
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
from langchain_openai import AzureOpenAIEmbeddings
import sys
import os
import asyncio
import operator
import logging
import json
import hashlib
import re
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Resume_Praser'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Github_Praser'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Linkedin_Praser'))

from improved_resume import process_resume_with_github_analysis, create_vector_embeddings, get_resume_file_from_user
from github_agent import analyze_github_from_resume
from linkedin_praser import linkedin_profile_summary

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Azure OpenAI
AZURE_OPENAI_API_KEY = os.getenv("AZURE_API_KEY") 
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_ENDPOINT") 

chat_model = AzureChatOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name="gpt-4o-mini",
    api_version="2024-05-01-preview",
    temperature=0.2,
    max_tokens=1000
)

# Initialize embedding model for Chroma
embedding_model = AzureOpenAIEmbeddings(
    api_key=os.getenv("Embedding_api_key"),
    azure_endpoint="https://agentic-keran-framework.openai.azure.com/",
    deployment="text-embedding-ada-002",
    api_version="2023-05-15"
)

class ResumeState(TypedDict):
    """State for the resume processing workflow."""
    resume_file: str
    user_query: str
    username: Optional[str]
    resume_data: Optional[Dict[str, Any]]
    github_analysis: Optional[Dict[str, Any]]
    linkedin_analysis: Optional[Dict[str, Any]]
    vectorstore_path: Optional[str]  # Path to saved vectorstore instead of object
    bm25_texts: Optional[List[str]]  # Store texts instead of BM25Retriever object
    documents: Optional[List[Document]]
    retrieved_docs: Optional[List[Document]]
    final_answer: Optional[str]
    conversation_history: List[Dict[str, str]]
    session_id: str

def extract_username_from_resume(resume_file: str) -> str:
    """Extract username from resume filename or generate a hash-based identifier."""
    try:
        # Get filename without extension
        base_name = os.path.splitext(os.path.basename(resume_file))[0]
        
        # Clean the filename to use as username
        username = re.sub(r'[^\w\-_]', '_', base_name.lower())
        
        # If still too generic, create hash-based identifier
        if username in ['resume', 'cv', 'document'] or len(username) < 3:
            # Create hash from file path and modification time
            file_stat = os.stat(resume_file)
            hash_input = f"{resume_file}_{file_stat.st_mtime}_{file_stat.st_size}"
            username = f"user_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
        
        return username
        
    except Exception as e:
        logger.warning(f"Could not extract username from {resume_file}: {e}")
        # Fallback to timestamp-based username
        return f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

async def load_existing_vectorstore(username: str) -> Optional[Chroma]:
    """Load existing persistent Chroma vector store for the user."""
    try:
        persist_directory = f"./resume_{username}"
        
        if not os.path.exists(persist_directory):
            logger.info(f"No existing vector store found for user: {username}")
            return None
        
        logger.info(f"Loading existing vector store for user: {username}")
        
        # Load existing Chroma vector store
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_model,
            collection_name=f"resume_collection_{username}"
        )
        
        # Check if collection has documents
        collection_count = vectorstore._collection.count()
        
        if collection_count > 0:
            logger.info(f"✅ Loaded existing vector store with {collection_count} documents")
            return vectorstore
        else:
            logger.warning(f"Vector store exists but has no documents for user: {username}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error loading existing vector store: {e}")
        return None

async def create_persistent_vectorstore(documents: List[Document], username: str) -> Optional[Chroma]:
    """Create or load persistent Chroma vector store for the user."""
    if not documents:
        logger.warning("No documents provided for vector store creation")
        return None
    
    try:
        # Create persist directory path
        persist_directory = f"./resume_{username}"
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        logger.info(f"Creating/loading persistent vector store for user: {username}")
        logger.info(f"Persist directory: {persist_directory}")
        
        # Create or load Chroma vector store with persistence
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_model,
            collection_name=f"resume_collection_{username}"
        )
        
        # Check if collection already has documents
        collection_count = vectorstore._collection.count()
        
        if collection_count == 0:
            # Filter complex metadata before adding to Chroma
            logger.info(f"Adding {len(documents)} documents to new collection")
            filtered_documents = filter_complex_metadata(documents)
            await vectorstore.aadd_documents(filtered_documents)
            logger.info("✅ Documents added to persistent vector store")
        else:
            logger.info(f"✅ Loaded existing vector store with {collection_count} documents")
        
        return vectorstore
        
    except Exception as e:
        logger.error(f"❌ Error creating persistent vector store: {e}")
        return None

# Initialize memory saver for checkpointing
memory = MemorySaver()

# Create StateGraph
workflow = StateGraph(ResumeState)

# Define workflow nodes
async def process_resume_node(state: ResumeState) -> ResumeState:
    """Process the resume file and extract basic information."""
    logger.info(f"🔄 Processing resume: {state['resume_file']}")
    
    try:
        # Extract username from resume file
        if not state.get('username'):
            state['username'] = extract_username_from_resume(state['resume_file'])
            logger.info(f"Extracted username: {state['username']}")
        
        # Process resume with GitHub analysis
        resume_result = await process_resume_with_github_analysis(state['resume_file'])
        
        if resume_result.get('error'):
            logger.error(f"Resume processing failed: {resume_result['error']}")
            state['final_answer'] = f"❌ Error processing resume: {resume_result['error']}"
            return state
        
        # Update state with resume data
        state['resume_data'] = resume_result
        state['documents'] = resume_result.get('documents', [])
        
        # Remove vectorstore from resume_data to avoid serialization issues
        if 'vectorstore' in state['resume_data']:
            del state['resume_data']['vectorstore']
        
        # Create persistent vector store using Chroma
        if state['documents']:
            vectorstore = await create_persistent_vectorstore(
                state['documents'], 
                state['username']
            )
            
            if vectorstore:
                # Store the persist directory path instead of the object
                state['vectorstore_path'] = f"./resume_{state['username']}"
            
            # Create BM25 retriever from documents
            texts = [doc.page_content for doc in state['documents']]
            state['bm25_texts'] = texts  # Store texts instead of retriever object
        
        logger.info("✅ Resume processing completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Error in resume processing: {e}")
        state['final_answer'] = f"❌ Error processing resume: {str(e)}"
        return state

async def analyze_github_node(state: ResumeState) -> ResumeState:
    """Analyze GitHub profiles and repositories."""
    logger.info("🔄 Analyzing GitHub profiles...")
    
    try:
        if not state.get('resume_data'):
            logger.warning("No resume data available for GitHub analysis")
            return state
        
        # Analyze GitHub from resume
        github_result = await analyze_github_from_resume(state['resume_file'])
        state['github_analysis'] = github_result
        
        logger.info("✅ GitHub analysis completed")
        return state
        
    except Exception as e:
        logger.error(f"Error in GitHub analysis: {e}")
        state['github_analysis'] = {'error': str(e)}
        return state

async def analyze_linkedin_node(state: ResumeState) -> ResumeState:
    """Analyze LinkedIn profile."""
    logger.info("🔄 Analyzing LinkedIn profile...")
    
    try:
        # Analyze LinkedIn from resume
        linkedin_result = await linkedin_profile_summary(resume_file_path=state['resume_file'])
        state['linkedin_analysis'] = linkedin_result
        
        logger.info("✅ LinkedIn analysis completed")
        return state
        
    except Exception as e:
        logger.error(f"Error in LinkedIn analysis: {e}")
        state['linkedin_analysis'] = {'error': str(e)}
        return state

async def retrieve_and_answer_node(state: ResumeState) -> ResumeState:
    """Retrieve relevant information and answer user query using BM25 and vector search."""
    logger.info(f"🔄 Processing query: {state['user_query']}")
    
    try:
        retrieved_docs = []
        
        # BM25 Retrieval
        if state.get('bm25_texts'):
            try:
                # Recreate BM25 retriever from stored texts
                bm25_retriever = BM25Retriever.from_texts(state['bm25_texts'])
                bm25_retriever.k = 5  # Top 5 results
                bm25_docs = bm25_retriever.invoke(state['user_query'])
                retrieved_docs.extend(bm25_docs[:3])  # Top 3 BM25 results
                logger.info(f"Retrieved {len(bm25_docs)} documents using BM25")
            except Exception as e:
                logger.warning(f"BM25 retrieval failed: {e}")
        
        # Vector Search with MMR using Chroma
        if state.get('vectorstore_path'):
            try:
                # Load vectorstore from path
                username = state.get('username') or 'default'
                vectorstore = await load_existing_vectorstore(username)
                
                if vectorstore:
                    # Use Chroma's max_marginal_relevance_search
                    vector_docs = await vectorstore.amax_marginal_relevance_search(
                        state['user_query'], 
                        k=3,
                        fetch_k=10
                    )
                    retrieved_docs.extend(vector_docs)
                    logger.info(f"Retrieved {len(vector_docs)} documents using Chroma vector search with MMR")
                else:
                    logger.warning("Could not load vectorstore from path")
            except Exception as e:
                logger.warning(f"Chroma vector search failed: {e}")
                # Fallback to regular similarity search
                try:
                    username = state.get('username') or 'default'
                    vectorstore = await load_existing_vectorstore(username)
                    if vectorstore:
                        vector_docs = await vectorstore.asimilarity_search(
                            state['user_query'], 
                            k=3
                        )
                        retrieved_docs.extend(vector_docs)
                        logger.info(f"Retrieved {len(vector_docs)} documents using Chroma similarity search")
                except Exception as e2:
                    logger.warning(f"Chroma similarity search also failed: {e2}")
        
        state['retrieved_docs'] = retrieved_docs
        
        # Generate answer using retrieved context
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Add GitHub and LinkedIn context if available
        additional_context = ""
        if state.get('github_analysis') and not state['github_analysis'].get('error'):
            github_summary = state['github_analysis'].get('summary', {})
            additional_context += f"\nGitHub Analysis: {github_summary.get('total_links', 0)} links found, {github_summary.get('profiles_found', 0)} profiles analyzed"
        
        if state.get('linkedin_analysis') and state['linkedin_analysis'].get('linkedin_found'):
            linkedin_data = state['linkedin_analysis'].get('profile_data', {})
            additional_context += f"\nLinkedIn Profile: {linkedin_data.get('name', 'N/A')} - {linkedin_data.get('headline', 'N/A')}"
        
        # Create prompt for answering
        answer_prompt = ChatPromptTemplate.from_template("""
You are an AI assistant specializing in resume analysis and professional profile assessment.

Resume Context:
{context}

Additional Profile Information:
{additional_context}

Conversation History:
{conversation_history}

User Query: {query}

Instructions:
1. Answer the user's query based on the provided resume content and profile information
2. Be specific and cite relevant information from the resume/profiles
3. If the information doesn't exist in the provided context, clearly state "This information is not available in the provided resume/profile data"
4. Provide helpful insights and analysis when possible
5. Keep responses concise but comprehensive

Answer:
""")
        
        # Format conversation history
        conv_history = "\n".join([
            f"User: {turn['user']}\nAssistant: {turn['assistant']}" 
            for turn in state.get('conversation_history', [])
        ])
        
        # Generate response
        chain = answer_prompt | chat_model | StrOutputParser()
        
        response = await chain.ainvoke({
            "context": context,
            "additional_context": additional_context,
            "conversation_history": conv_history,
            "query": state['user_query']
        })
        
        state['final_answer'] = response
        
        # Update conversation history
        if 'conversation_history' not in state:
            state['conversation_history'] = []
        
        state['conversation_history'].append({
            "user": state['user_query'],
            "assistant": response,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info("✅ Query processed and answer generated")
        return state
        
    except Exception as e:
        logger.error(f"Error in retrieval and answering: {e}")
        state['final_answer'] = f"❌ Error processing query: {str(e)}"
        return state

def should_continue(state: ResumeState) -> str:
    """Determine next step based on current state."""
    if state.get('final_answer'):
        return "end"
    return "continue"

# Add nodes to workflow
workflow.add_node("process_resume", process_resume_node)
workflow.add_node("analyze_github", analyze_github_node)
workflow.add_node("analyze_linkedin", analyze_linkedin_node)
workflow.add_node("retrieve_and_answer", retrieve_and_answer_node)

# Define edges
workflow.add_edge(START, "process_resume")
workflow.add_edge("process_resume", "analyze_github")
workflow.add_edge("analyze_github", "analyze_linkedin")
workflow.add_edge("analyze_linkedin", "retrieve_and_answer")
workflow.add_edge("retrieve_and_answer", END)

# Compile the workflow
app = workflow.compile(checkpointer=memory)

class ResumeAnalysisAgent:
    """Main agent class for resume analysis and conversation."""
    
    def __init__(self):
        self.app = app
        self.session_configs = {}
    
    async def process_resume_and_query(self, resume_file: str, query: str, session_id: str = "default", username: str = None) -> Dict[str, Any]:
        """Process resume and answer query."""
        config = {"configurable": {"thread_id": session_id}}
        
        # Extract username if not provided
        if not username:
            username = extract_username_from_resume(resume_file)
        
        # Check if we have existing state for this session
        existing_state = None
        try:
            # Try to get existing state
            state_history = self.app.get_state_history(config)
            for state in state_history:
                if (state.values.get('resume_file') == resume_file or 
                    state.values.get('username') == username):
                    existing_state = state.values
                    break
        except:
            pass
        
        if existing_state and existing_state.get('vectorstore_path'):
            # Use existing processed data, just update query
            logger.info(f"🔄 Using existing resume analysis data for user: {username}")
            input_state = {
                **existing_state,
                'user_query': query,
                'username': username
            }
            # Skip to query processing
            result = await self.app.ainvoke({'user_query': query, **existing_state}, config)
        else:
            # Process new resume
            logger.info(f"🔄 Processing new resume for user: {username}")
            input_state = {
                'resume_file': resume_file,
                'user_query': query,
                'username': username,
                'session_id': session_id,
                'conversation_history': []
            }
            result = await self.app.ainvoke(input_state, config)
        
        return result
    
    async def continue_conversation(self, query: str, session_id: str = "default", username: str = None) -> Dict[str, Any]:
        """Continue existing conversation with new query."""
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            # Get latest state
            current_state = self.app.get_state(config)
            if current_state and current_state.values:
                # Update query and process
                updated_state = {
                    **current_state.values,
                    'user_query': query
                }
                
                # If username is provided but not in state, add it
                if username and not updated_state.get('username'):
                    updated_state['username'] = username
                
                # If no vectorstore path in state but username available, set it
                if not updated_state.get('vectorstore_path') and updated_state.get('username'):
                    persist_dir = f"./resume_{updated_state['username']}"
                    if os.path.exists(persist_dir):
                        updated_state['vectorstore_path'] = persist_dir
                        logger.info(f"Found existing vector store path for continuing conversation")
                
                # Only run retrieval and answer for continuing conversation
                result = await retrieve_and_answer_node(updated_state)
                return result
            else:
                return {'final_answer': "❌ No active session found. Please start with a resume file first."}
        except Exception as e:
            return {'final_answer': f"❌ Error continuing conversation: {str(e)}"}
    
    def list_existing_users(self) -> List[str]:
        """List all existing users with persistent vector stores."""
        users = []
        try:
            current_dir = "."
            for item in os.listdir(current_dir):
                if os.path.isdir(item) and item.startswith("resume_"):
                    username = item.replace("resume_", "")
                    users.append(username)
            return users
        except Exception as e:
            logger.error(f"Error listing existing users: {e}")
            return []
    
    async def load_user_vectorstore(self, username: str) -> bool:
        """Load existing vector store for a specific user."""
        try:
            vectorstore = await load_existing_vectorstore(username)
            return vectorstore is not None
        except Exception as e:
            logger.error(f"Error loading vector store for {username}: {e}")
            return False

async def main():
    """Interactive main function for testing the agent."""
    agent = ResumeAnalysisAgent()
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("🤖 AI Resume Analysis Agent")
    print("=" * 50)
    print("I can analyze resumes, extract GitHub/LinkedIn profiles, and answer questions!")
    print()
    
    # Get resume file
    resume_file = input("📁 Enter path to resume file: ").strip().strip('"\'')
    
    if not os.path.exists(resume_file):
        print(f"❌ File not found: {resume_file}")
        return
    
    print(f"\n🔄 Processing resume: {os.path.basename(resume_file)}")
    print("This may take a moment as I analyze the resume, GitHub, and LinkedIn profiles...")
    
    # First query
    query = input("\n❓ What would you like to know about this resume? ").strip()
    
    try:
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
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())


