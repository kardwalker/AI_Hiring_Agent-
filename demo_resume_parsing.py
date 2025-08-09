"""
Demo script showing GitHub and LinkedIn parsing from resume files.
"""
import asyncio
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Resume_Praser'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'Linkedin_Praser'))

async def demo_comprehensive_resume_analysis():
    """Demonstrate comprehensive resume analysis with GitHub and LinkedIn parsing."""
    
    print("🚀 COMPREHENSIVE RESUME ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Import functions
        from improved_resume import process_resume_with_github_analysis
        from linkedin_praser import linkedin_profile_summary
        
        resume_file = "test_resume_with_github.txt"
        
        if not os.path.exists(resume_file):
            print(f"❌ Test resume file not found: {resume_file}")
            return
        
        print(f"📄 Analyzing resume: {resume_file}")
        print()
        
        # 1. Process resume with GitHub analysis
        print("🔗 STEP 1: GitHub Analysis")
        print("-" * 30)
        github_result = await process_resume_with_github_analysis(resume_file)
        
        if github_result.get('github_analysis'):
            github_summary = github_result['github_analysis']['summary']
            print(f"✅ GitHub Analysis Complete:")
            print(f"   - Links found: {github_summary['total_links']}")
            print(f"   - Profiles: {github_summary['profiles_found']}")
            print(f"   - Repositories: {github_summary['repositories_found']}")
            print(f"   - Unique users: {github_summary['unique_users']}")
        else:
            print("⚠️  No GitHub links found in resume")
        
        print()
        
        # 2. LinkedIn Analysis
        print("👤 STEP 2: LinkedIn Analysis")
        print("-" * 30)
        linkedin_result = await linkedin_profile_summary(resume_file_path=resume_file)
        
        if linkedin_result.get('linkedin_found'):
            print(f"✅ LinkedIn Analysis Complete:")
            print(f"   - Profile URL: {linkedin_result['linkedin_url']}")
            print(f"   - Name: {linkedin_result['profile_data'].get('name', 'N/A')}")
            print(f"   - Headline: {linkedin_result['profile_data'].get('headline', 'N/A')}")
            print(f"   - Summary length: {len(linkedin_result['professional_summary'])} characters")
        else:
            print(f"❌ LinkedIn Analysis Failed: {linkedin_result.get('message')}")
        
        print()
        
        # 3. Combined Summary
        print("📊 STEP 3: Combined Analysis Summary")
        print("-" * 30)
        
        # Contact information
        contact_info = github_result.get('contact_info', {})
        print(f"📧 Contact Information:")
        print(f"   - Email: {', '.join(contact_info.get('emails', ['Not found']))}")
        print(f"   - Phone: {', '.join(contact_info.get('phones', ['Not found']))}")
        print(f"   - LinkedIn: {', '.join(contact_info.get('linkedin', ['Not found']))}")
        print(f"   - GitHub: {', '.join(contact_info.get('github_profiles', ['Not found']))}")
        
        print()
        
        # Technical analysis
        print(f"🛠️  Technical Profile:")
        if github_result.get('github_analysis', {}).get('analysis', {}).get('profiles'):
            profiles = github_result['github_analysis']['analysis']['profiles']
            for username, profile in profiles.items():
                repos = profile.get('top_repositories', [])
                if repos:
                    languages = [repo.get('language') for repo in repos if repo.get('language')]
                    unique_languages = list(set(filter(None, languages)))
                    print(f"   - GitHub ({username}): {len(repos)} repos, languages: {', '.join(unique_languages[:5])}")
        
        if linkedin_result.get('profile_data', {}).get('skills'):
            skills = linkedin_result['profile_data']['skills']
            print(f"   - LinkedIn Skills: {', '.join(skills[:5])}...")
        
        print()
        print("✅ Comprehensive analysis complete!")
        
        return {
            'github_analysis': github_result,
            'linkedin_analysis': linkedin_result,
            'combined_contact': contact_info
        }
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
    except Exception as e:
        print(f"❌ Analysis error: {e}")

async def demo_individual_functions():
    """Demonstrate individual parsing functions."""
    
    print("\n🧪 INDIVIDUAL FUNCTION DEMOS")
    print("="*60)
    
    try:
        from linkedin_praser import linkedin_profile_summary
        
        # Test with direct LinkedIn URL
        print("🔗 Testing direct LinkedIn URL...")
        result = await linkedin_profile_summary(linkedin_url="https://linkedin.com/in/test-user")
        
        if result.get('linkedin_found'):
            print("✅ Direct URL analysis successful")
        else:
            print(f"❌ Direct URL failed: {result.get('message')}")
        
        print()
        
        # Test with no LinkedIn provided
        print("❌ Testing with no LinkedIn provided...")
        result = await linkedin_profile_summary()
        print(f"Expected result: {result.get('message')}")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")

async def main():
    """Main demo function."""
    print("🎯 AI HIRING AGENT - RESUME PARSING DEMO")
    print("="*70)
    print("This demo shows GitHub and LinkedIn parsing from resume files.")
    print()
    
    # Run comprehensive analysis
    await demo_comprehensive_resume_analysis()
    
    # Run individual function demos
    await demo_individual_functions()
    
    print("\n🎉 Demo completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
