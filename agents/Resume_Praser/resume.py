from typing import List
import os
import asyncio
import logging
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import AzureChatOpenAI

# Load environment variables once
load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
    logging.warning("Azure OpenAI credentials not fully set. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env")

model = AzureChatOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=AZURE_DEPLOYMENT,
    api_version=AZURE_API_VERSION,
    temperature=0.2,
    max_tokens=512
)


def resume_loader(file_path: str) -> List[str]:
    loader = PyPDFLoader(file_path)
    return loader.load()

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
import re

class ResumeProcessor:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=50
        )
        
    def extract_contact_info(self, text):
        """Extract and return structured contact information"""
        contact_info = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['emails'] = emails
        
        # Phone pattern (various formats)
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, text)
        contact_info['phones'] = ['-'.join(phone) for phone in phones]
        
        # LinkedIn pattern
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile/view\?id=)([A-Za-z0-9-_.]+)'
        linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
        contact_info['linkedin'] = linkedin
        
        # GitHub pattern
        github_pattern = r'(?:github\.com/)([A-Za-z0-9-_.]+)(?:/([A-Za-z0-9-_.]+))?'
        github = re.findall(github_pattern, text, re.IGNORECASE)
        contact_info['github_profiles'] = [match[0] for match in github]
        contact_info['github_repos'] = [f"{match[0]}/{match[1]}" for match in github if match[1]]
        
        return contact_info
    
    def clean_text_for_splitting(self, text):
        """Remove or replace URLs/emails with placeholders to avoid splitting issues"""
        # Replace URLs with placeholders
        text = re.sub(r'https?://[^\s]+', '[URL]', text)
        text = re.sub(r'www\.[^\s]+', '[URL]', text)
        
        # Keep emails but ensure they don't break splitting
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     lambda m: f"[EMAIL: {m.group()}]", text)
        
        return text
    
    def split_resume(self, resume_text):
        documents = []
        
        # First extract contact info
        contact_info = self.extract_contact_info(resume_text)
        
        # Create a contact info document
        contact_doc = Document(
            page_content=str(contact_info),
            metadata={
                'section': 'contact_info',
                'doc_type': 'resume',
                **contact_info
            }
        )
        documents.append(contact_doc)
        
        # Define sections with better patterns
        sections = {
            'summary': r'(?:SUMMARY|OBJECTIVE|PROFILE).*?(?=\n(?:[A-Z\s]{3,}|EXPERIENCE|EDUCATION|SKILLS|PROJECTS))',
            'experience': r'(?:WORK\s+|PROFESSIONAL\s+)?EXPERIENCE.*?(?=\n(?:[A-Z\s]{3,}|EDUCATION|SKILLS|PROJECTS)|\Z)',
            'education': r'EDUCATION.*?(?=\n(?:[A-Z\s]{3,}|EXPERIENCE|SKILLS|PROJECTS)|\Z)',
            'skills': r'(?:TECHNICAL\s+)?SKILLS?.*?(?=\n(?:[A-Z\s]{3,}|EXPERIENCE|EDUCATION|PROJECTS)|\Z)',
            'projects': r'PROJECTS?.*?(?=\n(?:[A-Z\s]{3,}|EXPERIENCE|EDUCATION|SKILLS)|\Z)',
            'certifications': r'CERTIFICATIONS?.*?(?=\n(?:[A-Z\s]{3,}|EXPERIENCE|EDUCATION|SKILLS|PROJECTS)|\Z)'
        }
        
        # Clean text for better splitting
        cleaned_text = self.clean_text_for_splitting(resume_text)
        
        for section_name, pattern in sections.items():
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section_text = match.strip()
                if section_text:
                    # Extract URLs and repos from this section
                    section_contact = self.extract_contact_info(section_text)
                    
                    chunks = self.splitter.split_text(section_text)
                    for chunk in chunks:
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                'section': section_name,
                                'doc_type': 'resume',
                                'has_github': len(section_contact['github_repos']) > 0,
                                'has_linkedin': len(section_contact['linkedin']) > 0,
                                'github_repos': section_contact['github_repos'],
                                'section_emails': section_contact['emails']
                            }
                        )
                        documents.append(doc)
        
        return documents


async def demo_process(pdf_path: str):
    """Async demonstration helper to parse and split a PDF resume."""
    docs = resume_loader(pdf_path)
    full_text = "\n".join(d.page_content for d in docs)
    processor = ResumeProcessor()
    split_docs = processor.split_resume(full_text)
    print(f"Loaded {len(docs)} raw pages -> {len(split_docs)} logical chunks")
    # Show first few chunks summary
    for d in split_docs[:5]:
        print(f"Section={d.metadata.get('section')} chars={len(d.page_content)}")


if __name__ == "__main__":  # pragma: no cover
    import argparse
    parser = argparse.ArgumentParser(description="Resume PDF processor demo")
    parser.add_argument("pdf", help="Path to resume PDF file")
    args = parser.parse_args()
    asyncio.run(demo_process(args.pdf))


