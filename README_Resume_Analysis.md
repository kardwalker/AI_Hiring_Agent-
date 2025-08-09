# AI Hiring Agent - Resume Analysis System

## Overview
This system provides comprehensive resume analysis with integrated GitHub and LinkedIn profile parsing capabilities. It extracts contact information, analyzes social media profiles, and generates professional summaries using AI.

## Features

### 1. Resume Processing (`improved_resume.py`)
- **Multi-format Support**: PDF, TXT, DOCX, MD files
- **Hyperlink Extraction**: Extracts clickable links from PDFs using PyMuPDF
- **Section Parsing**: Automatically identifies resume sections (experience, education, skills, projects, etc.)
- **Contact Information**: Extracts emails, phones, LinkedIn profiles, GitHub repositories
- **Vector Embeddings**: Creates searchable embeddings using Azure OpenAI
- **GitHub Integration**: Built-in GitHub link analysis

### 2. GitHub Analysis (`github_agent.py`)
- **Profile Analysis**: Fetches GitHub user profiles with comprehensive stats
- **Repository Details**: Analyzes individual repositories with languages, stars, forks
- **Link Extraction**: Automatically extracts GitHub links from resumes
- **Rate Limiting**: Handles GitHub API rate limits gracefully
- **Multiple Link Types**: Supports both profile and repository links

### 3. LinkedIn Analysis (`linkedin_praser.py`)
- **Profile Scraping**: Extracts LinkedIn profile information (with limitations)
- **AI-Powered Summaries**: Generates professional assessments using Azure OpenAI
- **Resume Integration**: Automatically finds LinkedIn links in resumes
- **Comprehensive Analysis**: 7-point professional assessment framework
- **Mock Data**: Demonstration data when scraping is limited

## Usage Examples

### Basic Resume Processing
```python
# Process resume with GitHub analysis
python agents/Resume_Praser/improved_resume.py resume.pdf --github

# Interactive mode
python agents/Resume_Praser/improved_resume.py -i

# With search demo
python agents/Resume_Praser/improved_resume.py resume.pdf --demo --github
```

### LinkedIn Analysis
```python
# Interactive LinkedIn analyzer
python agents/Linkedin_Praser/linkedin_praser.py

# Programmatic usage
from linkedin_praser import linkedin_profile_summary

# From resume file
result = await linkedin_profile_summary(resume_file_path="resume.pdf")

# From direct URL
result = await linkedin_profile_summary(linkedin_url="https://linkedin.com/in/username")
```

### GitHub Analysis
```python
# Interactive GitHub analyzer
python agents/Github_Praser/github_agent.py

# Programmatic usage
from github_agent import analyze_github_from_resume
result = await analyze_github_from_resume("resume.pdf")
```

### Comprehensive Demo
```python
# Run complete analysis demo
python demo_resume_parsing.py
```

## System Architecture

### Core Components

1. **Resume Parser** (`ResumeProcessor` class)
   - Text cleaning and section identification
   - Contact information extraction with regex patterns
   - Document chunking for vector embeddings
   - Hyperlink categorization

2. **GitHub Parser** (`GitHubLinkParser` class)
   - URL pattern matching for profiles/repositories
   - GitHub API integration with error handling
   - Comprehensive profile and repository analysis
   - Link deduplication and categorization

3. **LinkedIn Parser** (`LinkedInProfileScraper` class)
   - LinkedIn URL pattern extraction
   - Basic web scraping (limited by LinkedIn's restrictions)
   - AI-powered professional summary generation
   - Mock data for demonstration purposes

### Integration Flow

1. **Resume Upload** → Resume file processed and parsed
2. **Contact Extraction** → Email, phone, LinkedIn, GitHub links identified
3. **GitHub Analysis** → API calls to fetch profile and repository data
4. **LinkedIn Analysis** → Profile scraping and AI summary generation
5. **Combined Report** → Comprehensive professional assessment

## AI Integration

### Azure OpenAI Services
- **Chat Model**: GPT-4o-mini for generating professional summaries
- **Embeddings**: text-embedding-ada-002 for vector search
- **Temperature**: 0.2 for consistent, professional outputs

### Professional Summary Framework
1. **Professional Overview**: Key strengths and career focus
2. **Technical Skills**: Programming languages, frameworks, tools
3. **Experience Highlights**: Notable positions and achievements
4. **Education & Qualifications**: Academic background
5. **Professional Network**: Connection level and industry presence
6. **Career Trajectory**: Growth pattern and specializations
7. **Recommendations**: Suitable roles or next career steps

## Technical Features

### Error Handling
- Graceful fallbacks for missing dependencies
- API rate limiting and timeout handling
- File format validation and error reporting
- Network connectivity error handling

### Data Processing
- Regex patterns for contact information extraction
- URL categorization and validation
- Duplicate detection and removal
- JSON serialization for data export

### Performance Optimizations
- Async/await patterns for concurrent API calls
- Chunked text processing for large documents
- Efficient vector embedding creation
- Rate limiting for API compliance

## Configuration

### Environment Variables
```bash
# Azure OpenAI Configuration
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=your_azure_endpoint
Embedding_api_key=your_embedding_api_key

# Optional: GitHub Token for higher rate limits
GITHUB_TOKEN=your_github_token
```

### Dependencies
```bash
# Core dependencies
pip install langchain-openai langchain-community
pip install httpx PyMuPDF faiss-cpu
pip install python-docx python-dotenv
```

## Output Examples

### Resume Processing Summary
```
==================================================
RESUME PROCESSING SUMMARY
==================================================
✓ File: resume.pdf
✓ Pages loaded: 2
✓ Document chunks created: 20
✓ Vector embeddings: Created

📧 CONTACT INFORMATION:
  Email(s): john.doe@email.com
  Phone(s): +1-555-123-4567
  LinkedIn: johndoe
  GitHub: octocat

📝 SECTIONS FOUND:
  Summary: 1 chunks
  Experience: 5 chunks
  Education: 2 chunks
  Skills: 1 chunks
  Projects: 3 chunks
==================================================
```

### GitHub Analysis Results
```
📊 GITHUB ANALYSIS RESULTS
==================================================
✓ Unique users found: 1
✓ Profiles analyzed: 1
✓ Repositories analyzed: 3

👤 GITHUB PROFILES:
  📋 octocat
      Name: The Octocat
      Company: @github
      Public Repos: 8
      Followers: 19014
      Top Repositories:
        - portfolio-website (JavaScript) ⭐42
        - ml-classifier (Python) ⭐156
        - data-viz-dashboard (JavaScript) ⭐89
```

### LinkedIn Professional Summary
```
### Professional Assessment

#### 1. Professional Overview
John Doe is an accomplished software engineer with over 5 years of experience 
in full-stack development. His career is characterized by a strong passion for 
creating scalable applications and a commitment to contributing to open-source projects.

#### 2. Technical Skills
- Programming Languages: Python, JavaScript, Java, TypeScript
- Frameworks: React, Node.js, Django, Flask
- Cloud Platforms: AWS, GCP, Azure
- Databases: PostgreSQL, MongoDB, Redis

[... detailed 7-point assessment continues ...]
```

## Limitations and Considerations

### LinkedIn Scraping
- LinkedIn actively prevents automated scraping
- System uses mock data for demonstration
- Production systems should use LinkedIn's official API

### GitHub API
- Rate limits: 60 requests/hour (unauthenticated), 5000/hour (authenticated)
- Public repositories and profiles only
- API token recommended for higher limits

### File Processing
- PDF hyperlink extraction requires PyMuPDF
- Large files may take longer to process
- OCR not included for scanned documents

## Future Enhancements

1. **LinkedIn API Integration**: Replace scraping with official API
2. **OCR Support**: Process scanned resume images
3. **Additional Platforms**: Twitter, Stack Overflow, personal websites
4. **Resume Scoring**: AI-powered resume quality assessment
5. **Job Matching**: Match resumes to job descriptions
6. **Batch Processing**: Handle multiple resumes simultaneously
7. **Web Interface**: User-friendly web dashboard
8. **Database Integration**: Store and search processed resumes

## Error Handling Examples

```python
# Handle missing LinkedIn links
if not result.get('linkedin_found'):
    print(result.get('message', 'LinkedIn link not provided'))

# Handle GitHub API errors
if 'error' in github_result:
    print(f"GitHub analysis failed: {github_result['error']}")

# Handle file processing errors
try:
    result = await process_resume_from_file(file_path)
except FileNotFoundError:
    print("Resume file not found")
except Exception as e:
    print(f"Processing error: {e}")
```

This system provides a robust foundation for AI-powered resume analysis and can be extended for various hiring and recruitment use cases.
