import sys
import os
import asyncio
import json
import httpx
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.schema import Document
from langchain.prompts import PromptTemplate

# Add the Resume_Parser directory to the path for importing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Resume_Praser'))

try:
    from improved_resume import process_resume_from_file, parse_github_links_from_resume
    print("✓ Successfully imported functions from improved_resume.py")
except ImportError as e:
    print(f"❌ Could not import from improved_resume.py: {e}")
    print("Make sure improved_resume.py is in the Resume_Praser folder")

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_API_KEY") 
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_ENDPOINT") 

# BrightData WebScraper API configuration
BRIGHTDATA_API_TOKEN = os.getenv("BRIGHTDATA_API_TOKEN")
BRIGHTDATA_API_ENDPOINT = os.getenv("BRIGHTDATA_API_ENDPOINT", "https://api.brightdata.com") 

# Initialize Azure OpenAI model for summarization
try:
    chat_model = AzureChatOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        deployment_name="gpt-4o-mini",
        api_version="2024-05-01-preview",
        temperature=0.2,
        max_tokens=1000
    )
    logger.info("✓ Azure OpenAI chat model initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Azure OpenAI chat model: {e}")
    chat_model = None


class BrightDataScraper:
    """BrightData WebScraper API implementation for LinkedIn scraping."""
    
    def __init__(self):
        self.api_token = BRIGHTDATA_API_TOKEN
        self.endpoint = BRIGHTDATA_API_ENDPOINT
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    async def scrape_linkedin_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """Scrape LinkedIn profile using BrightData API."""
        if not self.api_token:
            logger.warning("BrightData API token not configured, falling back to basic scraping")
            return {'error': 'BrightData API token not configured'}
        
        try:
            # BrightData WebScraper API request
            scrape_request = {
                "url": linkedin_url,
                "format": "json",
                "wait_for": "networkidle",
                "extract": {
                    "name": {"selector": "h1", "type": "text"},
                    "headline": {"selector": ".text-body-medium", "type": "text"},
                    "location": {"selector": ".text-body-small.inline.t-black--light", "type": "text"},
                    "connections": {"selector": ".link-without-visited-state", "type": "text"},
                    "about": {"selector": ".pv-about__summary-text", "type": "text"},
                    "experience": {
                        "selector": ".pv-entity__summary-info",
                        "type": "list",
                        "extract": {
                            "title": {"selector": "h3", "type": "text"},
                            "company": {"selector": ".pv-entity__secondary-title", "type": "text"},
                            "duration": {"selector": ".pv-entity__bullet-item", "type": "text"}
                        }
                    },
                    "education": {
                        "selector": ".pv-education-entity",
                        "type": "list", 
                        "extract": {
                            "school": {"selector": "h3", "type": "text"},
                            "degree": {"selector": ".pv-entity__secondary-title", "type": "text"},
                            "field": {"selector": ".pv-entity__comma-item", "type": "text"}
                        }
                    },
                    "skills": {
                        "selector": ".pv-skill-category-entity__name",
                        "type": "list"
                    }
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.endpoint}/webscraperapi/request",
                    headers=self.headers,
                    json=scrape_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ Successfully scraped LinkedIn profile using BrightData")
                    return {
                        'url': linkedin_url,
                        'data': result,
                        'extracted_at': datetime.now().isoformat(),
                        'status': 'success',
                        'method': 'brightdata_api'
                    }
                else:
                    logger.error(f"BrightData API error: {response.status_code}")
                    return {'error': f'BrightData API error: {response.status_code}'}
                    
        except Exception as e:
            logger.error(f"Error with BrightData scraping: {e}")
            return {'error': f'BrightData scraping failed: {str(e)}'}


class LinkedInProfileScraper:
    """LinkedIn profile scraper and analyzer with BrightData integration."""
    
    def __init__(self):
        self.brightdata_scraper = BrightDataScraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def scrape_linkedin_profile_enhanced(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Enhanced LinkedIn profile scraping using BrightData API with fallback.
        """
        logger.info(f"🔍 Attempting to scrape LinkedIn profile: {linkedin_url}")
        
        # First, try BrightData API
        if BRIGHTDATA_API_TOKEN:
            logger.info("🚀 Using BrightData WebScraper API...")
            brightdata_result = await self.brightdata_scraper.scrape_linkedin_profile(linkedin_url)
            
            if 'error' not in brightdata_result:
                logger.info("✅ BrightData scraping successful")
                return self._process_brightdata_result(brightdata_result)
            else:
                logger.warning(f"⚠️ BrightData scraping failed: {brightdata_result['error']}")
        
        # Fallback to basic scraping
        logger.info("🔄 Falling back to basic scraping...")
        basic_result = await self.scrape_linkedin_profile_basic(linkedin_url)
        
        if 'error' not in basic_result:
            return basic_result
        
        # Return access denied instead of mock data
        logger.warning("⚠️ All scraping methods failed. LinkedIn access denied.")
        return {
            'error': 'LinkedIn access denied',
            'message': 'Unable to parse LinkedIn profile due to access restrictions',
            'url': linkedin_url,
            'status': 'access_denied'
        }
    
    def _process_brightdata_result(self, brightdata_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize BrightData scraping result."""
        try:
            data = brightdata_result.get('data', {})
            username = self.extract_linkedin_username(brightdata_result.get('url', ''))
            
            processed_data = {
                'url': brightdata_result.get('url'),
                'username': username,
                'name': data.get('name', 'N/A'),
                'headline': data.get('headline', 'N/A'),
                'location': data.get('location', 'N/A'),
                'connections': data.get('connections', 'N/A'),
                'about': data.get('about', 'N/A'),
                'experience': data.get('experience', []),
                'education': data.get('education', []),
                'skills': data.get('skills', []),
                'extracted_at': brightdata_result.get('extracted_at'),
                'status': 'success_brightdata',
                'method': 'brightdata_api'
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing BrightData result: {e}")
            return {'error': f'Failed to process BrightData result: {str(e)}'}
    
    def extract_linkedin_username(self, linkedin_url: str) -> Optional[str]:
        """Extract LinkedIn username from URL."""
        if not linkedin_url:
            return None
        
        # Clean the URL
        url = linkedin_url.strip().rstrip('/')
        
        # LinkedIn profile patterns
        patterns = [
            r'linkedin\.com/in/([A-Za-z0-9-_.]+)',
            r'linkedin\.com/profile/view\?id=([A-Za-z0-9-_.]+)',
            r'linkedin\.com/pub/([A-Za-z0-9-_.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def scrape_linkedin_profile_basic(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Basic LinkedIn profile scraping (limited due to LinkedIn's anti-scraping measures).
        This is a simplified version that extracts what's publicly available.
        """
        try:
            username = self.extract_linkedin_username(linkedin_url)
            if not username:
                return {'error': 'Invalid LinkedIn URL format'}
            
            # Note: LinkedIn heavily restricts scraping. This is a basic implementation
            # In production, you'd want to use LinkedIn's official API
            async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
                try:
                    response = await client.get(linkedin_url)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Extract basic information using regex (very limited)
                        profile_data = {
                            'url': linkedin_url,
                            'username': username,
                            'extracted_at': datetime.now().isoformat(),
                            'status': 'partially_extracted',
                            'method': 'basic_scraping'
                        }
                        
                        # Try to extract some basic info (this is very limited due to LinkedIn's structure)
                        name_match = re.search(r'<title>([^|]+)', content)
                        if name_match:
                            profile_data['name'] = name_match.group(1).strip()
                        
                        # Extract meta description if available
                        desc_match = re.search(r'<meta name="description" content="([^"]+)"', content)
                        if desc_match:
                            profile_data['description'] = desc_match.group(1).strip()
                        
                        return profile_data
                    
                    elif response.status_code == 429:
                        return {'error': 'Rate limited by LinkedIn'}
                    elif response.status_code == 403:
                        return {'error': 'Access forbidden by LinkedIn'}
                    else:
                        return {'error': f'HTTP {response.status_code}: Could not access LinkedIn profile'}
                
                except httpx.TimeoutException:
                    return {'error': 'Request timeout when accessing LinkedIn'}
                
        except Exception as e:
            return {'error': f'Failed to scrape LinkedIn profile: {str(e)}'}
    
    async def create_mock_linkedin_data(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Create mock LinkedIn data for demonstration purposes.
        In a real implementation, this would use LinkedIn's official API.
        """
        username = self.extract_linkedin_username(linkedin_url)
        
        return {
            'url': linkedin_url,
            'username': username,
            'name': f"Professional User ({username})",
            'headline': "Software Engineer | Full Stack Developer | Open Source Contributor",
            'location': "San Francisco, CA",
            'industry': "Technology",
            'summary': f"""Experienced software engineer with 5+ years in full-stack development. 
            Passionate about creating scalable applications and contributing to open-source projects. 
            
            🔧 Technical Skills:
            • Programming: Python, JavaScript, Java, TypeScript
            • Frameworks: React, Node.js, Django, Flask
            • Cloud: AWS, GCP, Azure
            • Databases: PostgreSQL, MongoDB, Redis
            
            💼 Current Focus:
            • Leading development of microservices architecture
            • Mentoring junior developers
            • Contributing to open-source machine learning projects
            
            Connect with me to discuss technology, collaboration opportunities, or just to chat about the latest in software development!
            
            LinkedIn Profile: {linkedin_url}""",
            'experience': [
                {
                    'title': 'Senior Software Engineer',
                    'company': 'Tech Innovations Inc.',
                    'duration': 'Jan 2022 - Present',
                    'description': 'Lead development of cloud-based applications serving 100K+ users'
                },
                {
                    'title': 'Software Developer',
                    'company': 'StartupXYZ',
                    'duration': 'Jun 2020 - Dec 2021',
                    'description': 'Developed REST APIs and implemented CI/CD pipelines'
                }
            ],
            'education': [
                {
                    'degree': 'Bachelor of Science in Computer Science',
                    'school': 'University of Technology',
                    'year': '2020'
                }
            ],
            'skills': [
                'Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 
                'Kubernetes', 'Machine Learning', 'Data Science', 'DevOps'
            ],
            'connections': '500+',
            'extracted_at': datetime.now().isoformat(),
            'status': 'mock_data',
            'method': 'demonstration'
        }
    
    async def generate_linkedin_summary(self, profile_data: Dict[str, Any]) -> str:
        """Generate a comprehensive summary of LinkedIn profile using Azure OpenAI."""
        if not chat_model:
            return "❌ Azure OpenAI not available for summary generation"
        
        try:
            # Create a prompt for summarizing LinkedIn profile
            summary_prompt = PromptTemplate(
                input_variables=["profile_data"],
                template="""
You are an expert HR analyst. Analyze the following LinkedIn profile data and provide a comprehensive professional summary.

LinkedIn Profile Data:
{profile_data}

Please provide a detailed analysis including:

1. **Professional Overview**: Key strengths and career focus
2. **Technical Skills**: Programming languages, frameworks, tools mentioned
3. **Experience Highlights**: Notable positions and achievements
4. **Education & Qualifications**: Academic background and certifications
5. **Professional Network**: Connection level and industry presence
6. **Career Trajectory**: Growth pattern and specializations
7. **Recommendations**: Suitable roles or next career steps

Format the response as a well-structured professional assessment that could be used for recruitment purposes.
Make it comprehensive but concise, highlighting the most important aspects for potential employers.
"""
            )
            
            # Format profile data as string
            profile_str = json.dumps(profile_data, indent=2, default=str)
            
            # Generate summary
            formatted_prompt = summary_prompt.format(profile_data=profile_str)
            response = await chat_model.ainvoke(formatted_prompt)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating LinkedIn summary: {e}")
            return f"❌ Error generating summary: {str(e)}"


async def extract_linkedin_from_resume(resume_file_path: str) -> List[str]:
    """Extract LinkedIn profile URLs from a resume file."""
    try:
        # Process the resume to extract LinkedIn links
        result = await process_resume_from_file(resume_file_path)
        
        if result.get('error'):
            logger.error(f"Error processing resume: {result['error']}")
            return []
        
        linkedin_links = []
        contact_info = result.get('contact_info', {})
        
        # Get LinkedIn links from hyperlinks
        hyperlinks = contact_info.get('hyperlinks', {})
        if hyperlinks.get('linkedin_links'):
            linkedin_links.extend(hyperlinks['linkedin_links'])
        
        # Get LinkedIn profiles from contact extraction
        if contact_info.get('linkedin'):
            for profile in contact_info['linkedin']:
                # Add full URL if just username
                if not profile.startswith('http'):
                    linkedin_links.append(f"https://linkedin.com/in/{profile}")
                else:
                    linkedin_links.append(profile)
        
        # Remove duplicates
        return list(set(linkedin_links))
        
    except Exception as e:
        logger.error(f"Error extracting LinkedIn from resume: {e}")
        return []


async def analyze_linkedin_profile(linkedin_url: str = None, resume_file_path: str = None) -> Dict[str, Any]:
    """
    Main function to analyze LinkedIn profile with comprehensive summary.
    
    Args:
        linkedin_url: Direct LinkedIn profile URL
        resume_file_path: Path to resume file to extract LinkedIn from
    
    Returns:
        Dictionary with LinkedIn analysis and summary
    """
    scraper = LinkedInProfileScraper()
    
    # Determine LinkedIn URL source
    linkedin_links = []
    
    if linkedin_url:
        linkedin_links.append(linkedin_url)
    elif resume_file_path:
        print(f"📄 Extracting LinkedIn profile from resume: {resume_file_path}")
        linkedin_links = await extract_linkedin_from_resume(resume_file_path)
        
        if not linkedin_links:
            return {
                'error': 'No LinkedIn profile found in resume',
                'message': 'LinkedIn link not provided and none found in resume',
                'resume_processed': True,
                'linkedin_found': False
            }
    else:
        return {
            'error': 'No LinkedIn URL or resume file provided',
            'message': 'Please provide either a LinkedIn URL or a resume file path',
            'linkedin_found': False
        }
    
    # Process first LinkedIn profile found
    primary_linkedin = linkedin_links[0]
    print(f"\n🔍 ANALYZING LINKEDIN PROFILE")
    print(f"{'='*50}")
    print(f"URL: {primary_linkedin}")
    
    # Attempt to scrape profile (will likely be limited)
    profile_data = await scraper.scrape_linkedin_profile_enhanced(primary_linkedin)
    
    # If scraping fails or is limited, return access denied message
    if profile_data.get('error') or profile_data.get('status') == 'partially_extracted':
        print(f"⚠️  LinkedIn access denied. Cannot parse profile due to access restrictions.")
        result = {
            'error': 'LinkedIn access denied',
            'message': 'Cannot parse LinkedIn profile due to access restrictions',
            'url': primary_linkedin,
            'profile_data': None,
            'summary': 'LinkedIn profile analysis unavailable due to access restrictions.'
        }
        return result
    
    # Generate comprehensive summary
    print(f"\n📊 GENERATING PROFESSIONAL SUMMARY...")
    summary = await scraper.generate_linkedin_summary(profile_data)
    
    # Compile results
    result = {
        'linkedin_url': primary_linkedin,
        'additional_links': linkedin_links[1:] if len(linkedin_links) > 1 else [],
        'profile_data': profile_data,
        'professional_summary': summary,
        'extraction_method': 'resume' if resume_file_path else 'direct_url',
        'analysis_timestamp': datetime.now().isoformat(),
        'linkedin_found': True
    }
    
    # Display results
    print(f"\n👤 LINKEDIN PROFILE ANALYSIS")
    print(f"{'='*60}")
    print(f"Name: {profile_data.get('name', 'N/A')}")
    print(f"Username: {profile_data.get('username', 'N/A')}")
    print(f"Headline: {profile_data.get('headline', 'N/A')}")
    print(f"Location: {profile_data.get('location', 'N/A')}")
    print(f"Connections: {profile_data.get('connections', 'N/A')}")
    
    if profile_data.get('skills'):
        print(f"\nTop Skills: {', '.join(profile_data['skills'][:5])}")
    
    print(f"\n📝 PROFESSIONAL SUMMARY:")
    print(f"{'-'*40}")
    print(summary)
    
    return result


async def scrape_linkedin_from_resume_file(resume_file_path: str) -> Dict[str, Any]:
    """
    Convenience function to scrape LinkedIn from resume file.
    
    Args:
        resume_file_path: Path to resume file
    
    Returns:
        LinkedIn analysis results
    """
    if not os.path.exists(resume_file_path):
        return {
            'error': f'Resume file not found: {resume_file_path}',
            'message': 'Please check the file path and try again',
            'linkedin_found': False
        }
    
    return await analyze_linkedin_profile(resume_file_path=resume_file_path)


async def scrape_linkedin_from_url(linkedin_url: str) -> Dict[str, Any]:
    """
    Convenience function to scrape LinkedIn from direct URL.
    
    Args:
        linkedin_url: LinkedIn profile URL
    
    Returns:
        LinkedIn analysis results
    """
    if not linkedin_url:
        return {
            'error': 'LinkedIn URL not provided',
            'message': 'Please provide a valid LinkedIn profile URL',
            'linkedin_found': False
        }
    
    return await analyze_linkedin_profile(linkedin_url=linkedin_url)


def save_linkedin_analysis_to_json(analysis_result: Dict[str, Any], output_file: str = None) -> str:
    """Save LinkedIn analysis results to JSON file."""
    if output_file is None:
        linkedin_url = analysis_result.get('linkedin_url', '')
        username = analysis_result.get('profile_data', {}).get('username', 'linkedin_user')
        output_file = f"{username}_linkedin_analysis.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 LinkedIn analysis saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")
        return ""


async def main():
    """Interactive LinkedIn profile analyzer."""
    print("🔗 LinkedIn Profile Analyzer")
    print("="*50)
    print("This tool analyzes LinkedIn profiles and generates comprehensive summaries.")
    print("You can provide either:")
    print("1. A direct LinkedIn profile URL")
    print("2. A resume file (will extract LinkedIn URL from it)")
    print()
    
    # Get input method choice
    while True:
        choice = input("Choose input method:\n1. LinkedIn URL\n2. Resume file\nEnter choice (1 or 2): ").strip()
        
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2.")
    
    result = None
    
    if choice == '1':
        # Direct LinkedIn URL
        while True:
            linkedin_url = input("\n🔗 Enter LinkedIn profile URL: ").strip()
            if linkedin_url:
                result = await scrape_linkedin_from_url(linkedin_url)
                break
            print("Please enter a valid LinkedIn URL.")
    
    elif choice == '2':
        # Resume file
        while True:
            resume_path = input("\n📁 Enter resume file path: ").strip().strip('"\'')
            if resume_path and os.path.exists(resume_path):
                result = await scrape_linkedin_from_resume_file(resume_path)
                break
            print("File not found. Please check the path and try again.")
    
    # Display results
    if result and result.get('error'):
        print(f"\n❌ Analysis failed: {result['error']}")
        print(f"💡 {result.get('message', '')}")
        return
    elif result and result.get('linkedin_found'):
        print(f"\n✅ LinkedIn analysis completed successfully!")
        
        # Ask if user wants to save results
        save_choice = input(f"\n💾 Save analysis to JSON file? (y/n): ").strip().lower()
        if save_choice in ['y', 'yes']:
            output_file = save_linkedin_analysis_to_json(result)
            if output_file:
                print(f"✅ Analysis saved successfully!")
    else:
        print(f"\n❌ No LinkedIn profile found or analysis failed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


# Simplified function for direct use
async def linkedin_profile_summary(linkedin_url: str = None, resume_file_path: str = None) -> Dict[str, Any]:
    """
    Simplified function to get LinkedIn profile summary.
    
    Args:
        linkedin_url: Direct LinkedIn profile URL
        resume_file_path: Path to resume file to extract LinkedIn from
    
    Returns:
        Dictionary with LinkedIn analysis and summary
    
    Usage:
        # From URL
        result = await linkedin_profile_summary(linkedin_url="https://linkedin.com/in/username")
        
        # From resume file  
        result = await linkedin_profile_summary(resume_file_path="path/to/resume.pdf")
        
        # Check result
        if result.get('linkedin_found'):
            print(result['professional_summary'])
        else:
            print(result.get('message', 'LinkedIn link not provided'))
    """
    return await analyze_linkedin_profile(linkedin_url=linkedin_url, resume_file_path=resume_file_path)


