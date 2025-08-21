"""
Production-ready Web-Enhanced Smart Windows Agent
Uses OpenRouter :online models for real-time web search capabilities
"""

import sys
import os
import traceback
from typing import Optional

# Import the web-enhanced agent and search function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent

try:
    from web_search import create_web_search_function
except ImportError:
    create_web_search_function = None


class ProductionWebSearchIntegrator:
    """Production-ready integrator for web-enhanced Windows automation"""
    
    def __init__(self, fallback_to_mock: bool = True):
        self.agent = None
        self.fallback_to_mock = fallback_to_mock
        self._setup_web_search()
    
    def _setup_web_search(self):
        """Set up the OpenRouter :online web search integration"""
        try:
            if create_web_search_function is not None:
                # Primary: Use OpenRouter :online web search
                web_search_func = create_web_search_function(
                    api="openrouter_online",
                    openrouter_model="openai/gpt-4o-mini-search-preview:online",
                    max_results=3,
                    cache_results=True,
                    cache_ttl_s=1800,  # 30-minute cache
                )
                print("🌐 Production agent initialized with OpenRouter :online web search")
                
            else:
                # Fallback: Mock search or error
                if self.fallback_to_mock:
                    def mock_web_search(query: str) -> dict:
                        return {
                            "results": [
                                {
                                    "title": "Mock Production Result", 
                                    "url": "https://example.com", 
                                    "snippet": f"Production mock search results for: {query}",
                                    "source": "mock"
                                }
                            ],
                            "count": 1
                        }
                    web_search_func = mock_web_search
                    print("⚠️  OpenRouter web search not available, using mock fallback")
                else:
                    raise RuntimeError("OpenRouter web search required but not available")
            
            # Initialize the agent with web search capability
            self.agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
            print("✅ Production web-enhanced agent ready")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not set up web search integration: {e}")
            # Initialize without web search (will use fallback mock responses)
            self.agent = WebEnhancedSmartWindowsAgent()
            print("✅ Web-enhanced agent initialized with mock web search")
    
    def execute_task(self, query: str) -> str:
        """Execute a task with web-enhanced capabilities"""
        if not self.agent:
            return "Error: Agent not initialized"
        
        try:
            return self.agent.execute(query)
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"❌ Execution error: {error_details}")
            return f"Error executing task: {str(e)}"
    
    def test_web_search(self, test_query: str = "Lowe's store locations Louisville KY") -> bool:
        """Test if web search is working properly"""
        print(f"🧪 Testing web search with query: '{test_query}'")
        
        try:
            if self.agent and hasattr(self.agent.translator, '_web_search_func'):
                result = self.agent.translator._web_search_func(test_query)
                print(f"✅ Web search test successful. Result preview: {str(result)[:200]}...")
                return True
            else:
                print("❌ Web search function not available")
                return False
        except Exception as e:
            print(f"❌ Web search test failed: {e}")
            return False


def interactive_mode(integrator: ProductionWebSearchIntegrator):
    """Interactive mode for testing the web-enhanced agent"""
    print("\n🎯 INTERACTIVE MODE")
    print("="*60)
    print("Enter tasks to test the web-enhanced agent.")
    print("Examples:")
    print("  • 'Find a cheap screwdriver at Lowe's near Bashford Manor'")
    print("  • 'Open Chrome and search for iPhone prices'")
    print("  • 'Get the phone number for the nearest Home Depot'")
    print("Type 'quit' to exit.")
    print()
    
    while True:
        try:
            query = input("Enter your task: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            print("\n" + "="*80)
            result = integrator.execute_task(query)
            print("\n" + "="*80)
            print("RESULT:")
            print(result)
            print("\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_example_tasks(integrator: ProductionWebSearchIntegrator):
    """Run some example tasks to demonstrate capabilities"""
    print("\n🌟 EXAMPLE TASKS")
    print("="*60)
    
    example_tasks = [
        {
            "title": "Shopping Task with Location Ambiguity",
            "query": "Open Chrome, go to Lowe's, find a cheap flat head screwdriver, and add it to my cart for pickup at the store near Bashford Manor",
            "description": "This task contains location ambiguity ('near Bashford Manor') and subjective terms ('cheap')"
        },
        {
            "title": "Research Task",
            "query": "Find the current price of iPhone 15 Pro and open a text document to write it down",
            "description": "This task requires current/time-dependent information"
        },
        {
            "title": "Store Information Task", 
            "query": "Get the phone number and hours for the Home Depot closest to downtown Louisville",
            "description": "This task requires specific business information"
        }
    ]
    
    for i, task in enumerate(example_tasks, 1):
        print(f"\n📋 Example {i}: {task['title']}")
        print(f"Description: {task['description']}")
        print(f"Query: {task['query']}")
        
        proceed = input("Run this example? (y/n): ").strip().lower()
        if proceed == 'y':
            print("\n" + "-"*80)
            result = integrator.execute_task(task['query'])
            print("-"*80)
            print("RESULT:")
            print(result)
            print()
        
        continue_examples = input("Continue with more examples? (y/n): ").strip().lower()
        if continue_examples != 'y':
            break


def main():
    """Main entry point for production web-enhanced agent"""
    print("🚀 Web-Enhanced Smart Windows Agent (Production)")
    print("="*80)
    print("Uses OpenRouter :online models to resolve query ambiguities")
    print("Models: GPT-4o Mini Search (translation & web search), Qwen 72B (analysis), Gemini Flash Lite (execution)")
    print()
    
    # Initialize the integrator
    print("🔧 Initializing web-enhanced agent...")
    integrator = ProductionWebSearchIntegrator()
    
    # Test web search capability
    print("\n🧪 Testing web search integration...")
    web_search_works = integrator.test_web_search()
    
    if web_search_works:
        print("✅ Web search integration successful!")
    else:
        print("⚠️  Web search not available, using fallback mock responses")
    
    print("\n" + "="*80)
    
    # Choose mode
    mode = input("Choose mode: (1) Interactive, (2) Examples, (3) Single task: ").strip()
    
    if mode == "1":
        interactive_mode(integrator)
    elif mode == "2":
        run_example_tasks(integrator)
    elif mode == "3":
        query = input("Enter your task: ").strip()
        if query:
            print("\n" + "="*80)
            result = integrator.execute_task(query)
            print("\n" + "="*80)
            print("FINAL RESULT:")
            print("="*80)
            print(result)
    else:
        print("Invalid mode selected")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()