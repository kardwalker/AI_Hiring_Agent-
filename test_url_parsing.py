"""
Test script to verify GitHub URL parsing fixes
"""
import sys
import os
import re
from urllib.parse import urlparse

# Add the Resume_Parser directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Resume_Praser'))

def test_url_parsing():
    """Test the improved URL parsing logic."""
    
    # Test URLs
    test_urls = [
        "https://github.com/kardwalker",
        "https://github.com/kardwalker/fine-tuning-a-pretrained-model",
        "https://github.com/kardwalker/Malaria-model-",  # The problematic URL
        "https://github.com/user123/repo-name",
        "https://github.com/user-with-dash/repo_with_underscore",
        "https://github.com/user.with.dots/repo.with.dots",
    ]
    
    print("🧪 Testing GitHub URL Parsing")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        
        # Simplified parsing logic based on the updated patterns
        github_info = {'username': None, 'repository': None, 'url_type': 'unknown'}
        
        # Clean the URL
        clean_url = url.strip().rstrip('/')
        
        # GitHub repository patterns - Simplified to allow trailing dashes
        repo_patterns = [
            r'github\.com/([A-Za-z0-9][A-Za-z0-9._-]*)/([A-Za-z0-9][A-Za-z0-9._-]*)/?$',
            r'github\.com/([A-Za-z0-9][A-Za-z0-9._-]*)/([A-Za-z0-9][A-Za-z0-9._-]*)/.*$'
        ]
        
        # GitHub profile patterns - Simplified to allow more flexibility
        profile_patterns = [
            r'github\.com/([A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]|[A-Za-z0-9])/?$',
            r'github\.com/([A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]|[A-Za-z0-9])/?\?.*$'
        ]
        
        # Check for repository patterns first
        for pattern in repo_patterns:
            match = re.search(pattern, clean_url, re.IGNORECASE)
            if match:
                username = match.group(1).rstrip('.')
                repository = match.group(2).rstrip('.')
                
                if (1 <= len(username) <= 39 and 1 <= len(repository) <= 100 and
                    re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$', username) and
                    re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$', repository)):
                    github_info['username'] = username
                    github_info['repository'] = repository
                    github_info['url_type'] = 'repository'
                    break
        
        # If no repository match, check for profile patterns
        if github_info['url_type'] == 'unknown':
            for pattern in profile_patterns:
                match = re.search(pattern, clean_url, re.IGNORECASE)
                if match:
                    username = match.group(1).rstrip('.')
                    if (1 <= len(username) <= 39 and
                        re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$', username)):
                        github_info['username'] = username
                        github_info['url_type'] = 'profile'
                        break
        
        # Fallback parsing if patterns don't work
        if github_info['url_type'] == 'unknown':
            try:
                parsed = urlparse(clean_url)
                path_parts = [part for part in parsed.path.strip('/').split('/') if part]
                
                if len(path_parts) >= 1:
                    username = path_parts[0].rstrip('.')
                    if (1 <= len(username) <= 39 and
                        re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$', username)):
                        github_info['username'] = username
                        
                        if len(path_parts) >= 2:
                            repository = path_parts[1].rstrip('.')
                            if (1 <= len(repository) <= 100 and
                                re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$', repository)):
                                github_info['repository'] = repository
                                github_info['url_type'] = 'repository'
                            else:
                                github_info['url_type'] = 'profile'
                        else:
                            github_info['url_type'] = 'profile'
            except Exception as e:
                print(f"   ❌ Fallback parsing failed: {e}")
        
        # Display results
        if github_info['url_type'] != 'unknown':
            print(f"   ✅ Type: {github_info['url_type']}")
            print(f"   👤 Username: {github_info['username']}")
            if github_info['repository']:
                print(f"   📂 Repository: {github_info['repository']}")
        else:
            print(f"   ❌ Could not parse URL")

if __name__ == "__main__":
    test_url_parsing()
