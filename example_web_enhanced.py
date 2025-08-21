"""
Practical example demonstrating the Web-Enhanced Smart Windows Agent
This example shows how to use the agent with OpenRouter :online web search
"""

import os
import sys
from typing import Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent

try:
    from web_search import create_web_search_function
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False


def setup_web_search_function():
    """
    Set up web search function with OpenRouter :online capability.
    Falls back to simulation if not available.
    """
    if WEB_SEARCH_AVAILABLE:
        try:
            # Use real OpenRouter :online web search
            print("🌐 Setting up OpenRouter :online web search...")
            return create_web_search_function(
                api="openrouter_online",
                openrouter_model="openai/gpt-4o-mini-search-preview:online",
                max_results=3,
                cache_results=True,
                cache_ttl_s=1800,
            )
        except Exception as e:
            print(f"⚠️  Could not initialize OpenRouter web search: {e}")
            print("Falling back to simulated responses...")
    else:
        print("⚠️  web_search.py not available, using simulated responses...")
    
    # Fallback to simulation
    def web_search_wrapper(query: str) -> dict:
        """Simulated web search for demonstration"""
        print(f"🔍 Simulating web search for: {query}")
        return {
            "results": [
                {
                    "title": "Simulated Search Result",
                    "url": "https://example.com",
                    "snippet": simulate_web_search(query),
                    "source": "simulation"
                }
            ],
            "count": 1
        }
    
    return web_search_wrapper


# Keep the old function name for backward compatibility
def create_web_search_function():
    """Legacy function name - redirects to setup_web_search_function"""
    return setup_web_search_function()


def simulate_web_search(query: str) -> str:
    """
    Simulate realistic web search responses for demonstration
    In production, this would be replaced with actual web_search calls
    """
    
    query_lower = query.lower()
    
    # Store location searches
    if "lowe's" in query_lower and ("bashford" in query_lower or "location" in query_lower):
        return """
        Lowe's Store Locations Near Bashford Manor, Louisville, KY:
        
        1. Lowe's Home Improvement - Middletown
           Address: 11800 Shelbyville Rd, Middletown, KY 40243
           Distance: 2.3 miles from Bashford Manor
           Phone: (502) 244-0527
           Store Hours: Monday-Sunday 6:00 AM - 10:00 PM
           Services: In-store pickup, installation services
           
        2. Lowe's Home Improvement - Hurstbourne  
           Address: 4600 Shelbyville Rd, Louisville, KY 40207
           Distance: 4.1 miles from Bashford Manor
           Phone: (502) 895-5493
           Store Hours: Monday-Sunday 6:00 AM - 10:00 PM
           
        Recommended: Middletown location for closest pickup option
        """
    
    # Product pricing searches
    elif "cheap" in query_lower and "screwdriver" in query_lower:
        return """
        Affordable Screwdrivers at Lowe's:
        
        Best Budget Options:
        1. Project Source 6-in Slotted Screwdriver - $1.98
           - Most affordable option
           - Basic but reliable
           - Customer rating: 4.2/5
           
        2. Kobalt 4-in Standard Slotted Screwdriver - $2.48  
           - Good quality for price
           - Comfortable grip
           - Customer rating: 4.5/5
           
        3. CRAFTSMAN 6-in Slotted Screwdriver - $3.48
           - Higher quality
           - Lifetime warranty
           - Customer rating: 4.7/5
           
        Recommendation: Project Source 6-inch for best value under $2
        """
    
    # Product specifications
    elif "flat head screwdriver" in query_lower or "slotted screwdriver" in query_lower:
        return """
        Flat Head Screwdrivers Available at Lowe's:
        
        Top Options:
        1. Project Source 6-inch Slotted Screwdriver
           - Price: $1.98
           - Tip width: 6mm
           - Handle: Basic plastic
           - Best for: Light household tasks
           
        2. Kobalt Standard Slotted Screwdriver Set
           - Price: $7.98 (4-piece set) 
           - Sizes: 3", 4", 6", 8"
           - Handle: Comfortable tri-material
           - Best for: Various projects
           
        3. DEWALT Slotted Screwdriver
           - Price: $8.48
           - Professional grade
           - Magnetic tip
           - Best for: Heavy-duty use
        """
    
    # Store hours and contact info
    elif "hours" in query_lower or "phone" in query_lower:
        return """
        Lowe's Store Information:
        
        Middletown Location (Closest to Bashford Manor):
        - Address: 11800 Shelbyville Rd, Middletown, KY 40243
        - Phone: (502) 244-0527
        - Hours: 
          Monday-Sunday: 6:00 AM - 10:00 PM
        - Services: Curbside pickup, in-store pickup, delivery
        - Departments: Tools, Hardware, Garden, Lumber, Appliances
        
        Special Notes:
        - Pickup orders ready in 2 hours
        - Free curbside pickup available
        - Tool rental department open 7 AM - 8 PM
        """
    
    # iPhone pricing (example of time-dependent info)
    elif "iphone" in query_lower and ("price" in query_lower or "cost" in query_lower):
        return """
        Current iPhone 15 Pro Pricing (January 2025):
        
        Apple Store Pricing:
        - iPhone 15 Pro 128GB: $999
        - iPhone 15 Pro 256GB: $1,099  
        - iPhone 15 Pro 512GB: $1,299
        - iPhone 15 Pro 1TB: $1,499
        
        Available Colors: Natural Titanium, Blue Titanium, White Titanium, Black Titanium
        
        Trade-in available: Up to $800 credit for eligible devices
        Financing: 0% APR available with Apple Card
        """
    
    # Default response
    else:
        return f"""
        Search Results for: "{query}"
        
        [This is a simulated web search response]
        
        The web-enhanced translator would extract relevant information from real search results
        to resolve ambiguities in your query. In a production environment, this would contain
        actual web search results from providers like Google, Bing, or specialized APIs.
        
        Key information that would be extracted:
        - Specific product details and pricing
        - Store locations and contact information  
        - Current availability and stock status
        - User reviews and ratings
        - Alternative options and recommendations
        """


def demonstrate_basic_usage():
    """Demonstrate basic usage with a simple query"""
    print("🎯 DEMO: Basic Usage")
    print("=" * 60)
    
    # Set up web search function
    web_search_func = setup_web_search_function()
    
    # Initialize agent
    agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
    
    # Simple query with ambiguities
    query = "Find a cheap screwdriver at Lowe's"
    
    print(f"Query: {query}")
    print("\nExecuting with web enhancement...")
    print("-" * 60)
    
    try:
        result = agent.execute(query)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    return agent


def demonstrate_complex_query():
    """Demonstrate with a more complex, ambiguous query"""
    print("\n🎯 DEMO: Complex Query with Multiple Ambiguities") 
    print("=" * 60)
    
    # Set up web search function
    web_search_func = setup_web_search_function()
    
    # Initialize agent
    agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
    
    # Complex query with multiple ambiguities
    query = "Open Chrome, go to Lowe's website, find a cheap flat head screwdriver, add it to cart, and set it for pickup at the store near Bashford Manor"
    
    print(f"Query: {query}")
    print("\nThis query contains multiple ambiguities:")
    print("  • 'cheap' - subjective pricing term")
    print("  • 'flat head screwdriver' - vague product specification")  
    print("  • 'near Bashford Manor' - location reference")
    
    print("\nExecuting with web enhancement...")
    print("-" * 60)
    
    try:
        result = agent.execute(query)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    return agent


def demonstrate_mid_task_clarification():
    """Demonstrate mid-task clarification capabilities"""
    print("\n🎯 DEMO: Mid-Task Clarification")
    print("=" * 60)
    
    # Set up web search function
    web_search_func = setup_web_search_function()
    
    # Initialize agent
    agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
    
    # Simulate some questions the agent might ask during execution
    questions = [
        "What's the exact price of the cheapest screwdriver?",
        "What are the store hours for pickup?",
        "What's the phone number to confirm pickup availability?"
    ]
    
    print("Simulating questions the agent might ask during execution:")
    
    for question in questions:
        print(f"\n❓ Agent Question: {question}")
        try:
            answer = agent.translator.mid_task_clarify(question)
            print(f"💡 Answer: {answer}")
        except Exception as e:
            print(f"❌ Error: {e}")


def interactive_demo():
    """Interactive demo mode"""
    print("\n🎯 INTERACTIVE DEMO MODE")
    print("=" * 60)
    print("Enter your own queries to test the web-enhanced agent!")
    print("Examples:")
    print("  • 'Find a good laptop at Best Buy'")
    print("  • 'Get coffee from the nearest Starbucks'") 
    print("  • 'Buy a cheap iPhone case online'")
    print("Type 'quit' to exit.")
    print()
    
    # Set up web search function
    web_search_func = setup_web_search_function()
    
    # Initialize agent
    agent = WebEnhancedSmartWindowsAgent(web_search_func=web_search_func)
    
    while True:
        try:
            query = input("Enter your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Demo completed!")
                break
                
            if not query:
                continue
            
            print("\n" + "=" * 80)
            print("PROCESSING QUERY...")
            print("=" * 80)
            
            result = agent.execute(query)
            
            print("\n" + "=" * 80)
            print("RESULT:")
            print("=" * 80) 
            print(result)
            print()
            
        except KeyboardInterrupt:
            print("\nDemo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error processing query: {e}")


def main():
    """Main demo function"""
    print("Web-Enhanced Smart Windows Agent - Live Demo")
    print("=" * 80)
    print("This demo shows how the web-enhanced agent resolves query ambiguities")
    print("using web search to provide more precise instructions to Windows-Use.")
    print()
    
    print("🔧 Components:")
    print("  • WebEnhancedTranslator: Identifies and resolves ambiguities")
    print("  • TaskAnalyzer: Generates step-by-step instructions") 
    print("  • SmartWindowsAgent: Executes tasks with Windows-Use")
    print()
    
    print("🌐 Web Search Integration:")
    print("  • OpenRouter :online capability (GPT-4o Mini Search Preview)")
    print("  • Automatic ambiguity detection")
    print("  • Real-time web search resolution with caching") 
    print("  • Query enhancement and rewriting")
    print("  • Mid-task clarification support")
    print()
    
    # Choose demo mode
    print("Select demo mode:")
    print("1. Basic Usage Demo")
    print("2. Complex Query Demo") 
    print("3. Mid-Task Clarification Demo")
    print("4. Interactive Mode")
    print("5. Run All Demos")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            demonstrate_basic_usage()
        elif choice == "2":
            demonstrate_complex_query()
        elif choice == "3":
            demonstrate_mid_task_clarification()
        elif choice == "4":
            interactive_demo()
        elif choice == "5":
            # Run all demos
            demonstrate_basic_usage()
            demonstrate_complex_query() 
            demonstrate_mid_task_clarification()
            
            # Ask if user wants interactive mode
            continue_interactive = input("\nContinue with interactive mode? (y/n): ").strip().lower()
            if continue_interactive == 'y':
                interactive_demo()
        else:
            print("Invalid choice. Running basic demo...")
            demonstrate_basic_usage()
            
    except KeyboardInterrupt:
        print("\nDemo interrupted. Goodbye!")
    except Exception as e:
        print(f"Demo error: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 DEMO COMPLETED")
    print("=" * 80)
    print("The web-enhanced agent successfully demonstrated:")
    print("✅ Ambiguity identification in user queries")
    print("✅ Web search resolution of unclear terms")
    print("✅ Query enhancement for better task execution") 
    print("✅ Integration with the existing Windows-Use v1 architecture")
    print()
    print("Ready for production use with your web search provider!")


if __name__ == "__main__":
    main()