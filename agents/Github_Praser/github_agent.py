import sys
import os
import asyncio
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
load_dotenv()
# Add the Resume_Parser directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Resume_Praser'))

try:
    from improved_resume import process_resume_with_github_analysis, parse_github_links_from_resume, GitHubLinkParser
    print("✓ Successfully imported GitHub parsing functions from improved_resume.py")
except ImportError as e:
    print(f"❌ Could not import from improved_resume.py: {e}")
    print("Make sure improved_resume.py is in the Resume_Praser folder")

load_dotenv()


async def analyze_github_from_resume(resume_file_path: str) -> Dict[str, Any]:
    """
    Main function to extract and analyze GitHub links from a resume file.
    
    Args:
        resume_file_path: Path to the resume file (.pdf, .txt, .docx, .md)
    
    Returns:
        Dictionary containing resume analysis and GitHub data
    """
    try:
        print(f"🚀 Starting GitHub analysis for resume: {resume_file_path}")
        print("="*60)
        
        # Process resume with GitHub analysis
        result = await process_resume_with_github_analysis(resume_file_path)
        
        if result.get('error'):
            return {'error': result['error']}
        
        # Extract GitHub-specific data
        github_analysis = result.get('github_analysis', {})
        
        # Create summary report
        summary_report = {
            'resume_file': resume_file_path,
            'processing_timestamp': str(asyncio.get_event_loop().time()),
            'github_links_found': github_analysis.get('github_links', []),
            'github_profiles': {},
            'github_repositories': {},
            'analysis_summary': github_analysis.get('summary', {}),
            'contact_information': result.get('contact_info', {}),
            'resume_sections': result.get('sections', {}),
            'errors': []
        }
        
        # Extract detailed GitHub data
        if github_analysis.get('analysis'):
            analysis = github_analysis['analysis']
            summary_report['github_profiles'] = analysis.get('profiles', {})
            summary_report['github_repositories'] = analysis.get('repositories', {})
            summary_report['errors'] = analysis.get('analysis_summary', {}).get('errors', [])
        
        return summary_report
        
    except Exception as e:
        return {'error': f'Failed to analyze GitHub links: {str(e)}'}


async def get_github_profile_summary(username: str) -> Dict[str, Any]:
    """
    Get a quick summary of a GitHub profile.
    
    Args:
        username: GitHub username
    
    Returns:
        Profile summary dictionary
    """
    parser = GitHubLinkParser()
    return await parser.fetch_github_profile(username)


async def get_github_repo_summary(username: str, repo_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific GitHub repository.
    
    Args:
        username: Repository owner's username
        repo_name: Repository name
    
    Returns:
        Repository details dictionary
    """
    parser = GitHubLinkParser()
    return await parser.fetch_repository_details(username, repo_name)


def save_github_analysis_to_json(analysis_result: Dict[str, Any], output_file: str = None) -> str:
    """
    Save GitHub analysis results to a JSON file.
    
    Args:
        analysis_result: The analysis result dictionary
        output_file: Optional output file path
    
    Returns:
        Path to the saved file
    """
    if output_file is None:
        resume_file = analysis_result.get('resume_file', 'resume')
        base_name = os.path.splitext(os.path.basename(resume_file))[0]
        output_file = f"{base_name}_github_analysis.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 GitHub analysis saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")
        return ""


async def main():
    """
    Interactive GitHub analysis from resume.
    """
    print("🔍 GitHub Resume Analyzer")
    print("="*40)
    print("This tool extracts GitHub links from resumes and analyzes the profiles/repositories.")
    print()
    
    # Get resume file path from user
    while True:
        resume_path = input("📁 Enter path to resume file (.pdf/.txt/.docx/.md): ").strip().strip('"\'')
        
        if not resume_path:
            print("Please enter a file path.")
            continue
        
        if not os.path.exists(resume_path):
            print(f"❌ File not found: {resume_path}")
            continue
        
        break
    
    # Analyze the resume
    print(f"\n🔄 Analyzing resume and GitHub links...")
    result = await analyze_github_from_resume(resume_path)
    
    if result.get('error'):
        print(f"❌ Analysis failed: {result['error']}")
        return
    
    # Display results summary
    print(f"\n📊 ANALYSIS COMPLETE")
    print("="*50)
    
    summary = result.get('analysis_summary', {})
    print(f"✓ GitHub links found: {summary.get('total_links', 0)}")
    print(f"✓ Profiles analyzed: {summary.get('profiles_found', 0)}")
    print(f"✓ Repositories analyzed: {summary.get('repositories_found', 0)}")
    print(f"✓ Unique users: {summary.get('unique_users', 0)}")
    
    # Show GitHub profiles
    profiles = result.get('github_profiles', {})
    if profiles:
        print(f"\n👤 GITHUB PROFILES FOUND:")
        for username, profile in profiles.items():
            print(f"  • {username}: {profile.get('name', 'N/A')} | {profile.get('public_repos', 0)} repos | {profile.get('followers', 0)} followers")
    
    # Show repositories
    repositories = result.get('github_repositories', {})
    if repositories:
        print(f"\n📂 REPOSITORIES FOUND:")
        for repo_name, repo in repositories.items():
            language = repo.get('language', 'N/A')
            stars = repo.get('stars', 0)
            print(f"  • {repo_name} ({language}) - ⭐{stars}")
    
    # Ask if user wants to save results
    save_choice = input(f"\n💾 Save analysis to JSON file? (y/n): ").strip().lower()
    if save_choice in ['y', 'yes']:
        output_file = save_github_analysis_to_json(result)
        if output_file:
            print(f"✅ Analysis saved successfully!")
    
    print(f"\n✅ GitHub analysis complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

