"""
Test script for mainv1_web_enhanced.py with a moderately complex query
Tests multiple ambiguity types: LOCATION, SUBJECTIVE, BUSINESS, TIME_DEPENDENT
"""

import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent
from web_search import create_web_search_function

def run_complex_test():
    """Run a moderately complex test case"""
    
    print("🧪 TESTING: Web-Enhanced Smart Windows Agent V1.1 - Complex Query Test")
    print(f"Testing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # Test query with multiple ambiguity types
    test_query = (
        "Find a highly rated coffee shop near downtown Louisville that has excellent reviews "
        "and serves specialty drinks, get their current phone number and hours, then open "
        "Notepad and write down this information including their most popular drink"
    )
    
    print("TEST QUERY:")
    print(f"'{test_query}'")
    print()
    print("EXPECTED AMBIGUITIES:")
    print("- LOCATION: 'near downtown Louisville' (needs specific location)")
    print("- SUBJECTIVE: 'highly rated' and 'excellent reviews' (needs criteria)")
    print("- BUSINESS: 'current phone number and hours' (needs up-to-date info)")
    print("- PRODUCT: 'most popular drink' (needs current menu/popularity info)")
    print("- TIME_DEPENDENT: 'current' information (needs recent data)")
    print()
    print("="*80)
    
    try:
        # Set up web search integration
        print("🔧 Setting up web search integration...")
        web_search_func = None
        
        try:
            # Try to set up real web search
            web_search_func = create_web_search_function(
                api="openrouter_online",
                openrouter_model="openai/gpt-4o-mini-search-preview:online",
                max_results=3,
                cache_results=True,
                cache_ttl_s=1800,
            )
            print("✅ Real web search integration enabled")
        except Exception as e:
            print(f"⚠️  Web search setup failed: {e}")
            print("📋 Using mock web search responses")
        
        # Create the web-enhanced agent
        print("\n🤖 Initializing Web-Enhanced Smart Windows Agent...")
        agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
        print("✅ Agent initialized successfully")
        
        print("\n" + "="*80)
        print("EXECUTION STARTING...")
        print("="*80)
        
        # Execute the complex query
        result = agent.execute(test_query)
        
        print("\n" + "="*80)
        print("FINAL RESULT:")
        print("="*80)
        print(result)
        
        print("\n" + "="*80)
        print("TEST ANALYSIS:")
        print("="*80)
        print("✅ Test completed successfully")
        print("📊 Check the output above for:")
        print("   - Ambiguity detection results")
        print("   - Web search resolutions")
        print("   - Enhanced query generation")
        print("   - Windows-Use agent execution")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = run_complex_test()
    sys.exit(0 if success else 1)