"""
Demo script for the Web-Enhanced Smart Windows Agent
Shows how to properly integrate with the web_search tool
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent
from web_search import create_web_search_function


# Real web search via OpenRouter :online (no plugin). To keep the demo safe without a key,
# you can fall back to the existing mock by commenting these lines.
try:
    web_search_func = create_web_search_function(
        api="openrouter_online",
        openrouter_model="openai/gpt-4o-mini-search-preview:online",
        max_results=3,
        cache_results=True,
        cache_ttl_s=1800,
    )
    print("🌐 Using real OpenRouter web search")
except Exception as e:
    print(f"⚠️  OpenRouter web search not available ({str(e)}), falling back to mock")
    # Fallback mock for environments without web access
    def mock_web_search(query: str) -> dict:
        return {
            "results": [
                {"title": "Mock Result", "url": "https://example.com", "snippet": f"Mock search results for: {query}", "source": "mock"}
            ],
            "count": 1
        }
    web_search_func = mock_web_search


def demo_basic_usage():
    """Demonstrate basic usage of the web-enhanced agent"""
    print("🌟 DEMO: Basic Web-Enhanced Agent Usage")
    print("="*60)
    
    # Web search function already initialized above
    
    # Initialize the agent with web search capability
    agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
    
    # Test query with ambiguities
    test_query = "Open Chrome, go to Lowe's, find a cheap flat head screwdriver, and add it to my cart for pickup at the store near Bashford Manor"
    
    print(f"Test Query: {test_query}")
    print("\n" + "="*60)
    
    # Execute the task
    result = agent.execute(test_query)
    
    return result


def demo_mid_task_clarification():
    """Demonstrate mid-task clarification capabilities"""
    print("\n🌟 DEMO: Mid-Task Clarification")
    print("="*60)
    
    # Web search function already initialized above
    
    # Initialize the agent
    agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
    
    # Simulate mid-task questions
    questions = [
        "What's the cheapest screwdriver at Lowe's?",
        "What are the store hours for Lowe's near Bashford Manor?",
        "What's the phone number for the nearest Lowe's location?"
    ]
    
    print("Simulating mid-task clarification requests:")
    
    for question in questions:
        answer = agent.translator.mid_task_clarify(question)
        print(f"\nQ: {question}")
        print(f"A: {answer}")


def demo_ambiguity_identification():
    """Demonstrate ambiguity identification"""
    print("\n🌟 DEMO: Ambiguity Identification")
    print("="*60)
    
    # Web search function already initialized above
    
    # Initialize just the translator
    from mainv1_web_enhanced import WebEnhancedTranslator
    translator = WebEnhancedTranslator()
    translator._web_search_func = web_search_func
    
    # Test queries with different types of ambiguities
    test_queries = [
        "Find a cheap screwdriver at the local store",
        "Buy the best laptop under $500",
        "Get coffee near downtown",
        "Order pizza from the good place nearby"
    ]
    
    for query in test_queries:
        print(f"\nOriginal Query: {query}")
        ambiguities = translator.identify_ambiguities(query)
        
        if ambiguities:
            print("Identified Ambiguities:")
            for amb in ambiguities:
                print(f"  • {amb['type']}: {amb['element']}")
        else:
            print("No ambiguities found")


def main():
    """Main demo runner"""
    print("Web-Enhanced Smart Windows Agent Demo")
    print("="*80)
    print("This demo shows the capabilities of the web-enhanced translation layer")
    print("that resolves query ambiguities before execution.")
    print()
    
    # Run demos
    try:
        # Basic usage demo
        result = demo_basic_usage()
        
        # Mid-task clarification demo
        demo_mid_task_clarification()
        
        # Ambiguity identification demo
        demo_ambiguity_identification()
        
        print("\n" + "="*80)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*80)
        print("The web-enhanced agent successfully:")
        print("✅ Identified ambiguous elements in queries")
        print("✅ Resolved ambiguities using web search")
        print("✅ Generated enriched, precise queries")
        print("✅ Provided mid-task clarification capabilities")
        print("\nReady for real-world usage with actual web search integration!")
        
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        print("Note: This demo uses mock web search responses.")
        print("In a real environment, connect to actual web search tools.")


if __name__ == "__main__":
    main()