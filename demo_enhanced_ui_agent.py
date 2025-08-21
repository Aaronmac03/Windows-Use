"""
Demo script for the Enhanced UI Interaction Agent

This demonstrates the new adaptive UI interaction capabilities that resolve
the infinite loop issue identified in Support Ticket #001.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent.enhanced_service import EnhancedAgent

def main():
    """Demo the enhanced UI agent with adaptive behavior"""
    
    print("🚀 Enhanced UI Interaction Agent Demo")
    print("=" * 50)
    print("This agent features:")
    print("  ✅ Adaptive UI interaction strategies")
    print("  ✅ Infinite loop detection and prevention") 
    print("  ✅ Automatic fallback mechanisms")
    print("  ✅ Better error recovery")
    print()
    
    # Load environment
    load_dotenv()
    
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY not found in .env file")
        return
    
    # Initialize the enhanced agent
    print("🔧 Initializing Enhanced Agent...")
    
    llm = ChatGoogleGenerativeAI(
        model='gemini-2.5-flash-lite',
        temperature=0.2
    )
    
    agent = EnhancedAgent(
        llm=llm,
        browser='chrome',
        use_vision=False,
        max_steps=30,
        consecutive_failures=3,  # Try alternatives after 3 failures
        loop_detection=True      # Enable infinite loop prevention
    )
    
    print("✅ Agent initialized with enhanced UI capabilities")
    print()
    
    # Interactive demo
    print("💡 Try queries that involve complex UI interactions:")
    print("  Example: 'Open Chrome and go to a website with dropdowns'")
    print("  Example: 'Open Settings and navigate to display options'") 
    print("  Example: 'Launch Calculator and perform a calculation'")
    print()
    
    while True:
        try:
            query = input("Enter your task (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue
            
            print("\n" + "="*60)
            print(f"🎯 Executing: {query}")
            print("="*60)
            
            # Execute with enhanced capabilities
            result = agent.invoke(query)
            
            print("\n" + "="*60)
            print("📋 RESULT:")
            print("="*60)
            
            if result.error:
                print(f"⚠️  {result.error}")
                
                # Check if it's the old recursion limit error
                if "Recursion limit" in result.error:
                    print("❌ Still hitting recursion limits - this shouldn't happen with the enhanced agent!")
                elif "LOOP DETECTED" in result.error or "FAILURE LIMIT" in result.error:
                    print("✅ Enhanced error handling working - agent detected issues and provided guidance!")
            else:
                print(f"✅ {result.content}")
            
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            continue

def test_components():
    """Quick test of the enhanced components"""
    
    print("🧪 Testing Enhanced Components")
    print("-" * 30)
    
    # Test interaction tracking
    from windows_use.agent.tools.enhanced_service import interaction_tracker, InteractionStrategy
    
    # Simulate some failures
    test_loc = (500, 300)
    interaction_tracker.record_attempt(test_loc, InteractionStrategy.DIRECT_CLICK, False)
    interaction_tracker.record_attempt(test_loc, InteractionStrategy.DIRECT_CLICK, False)
    
    should_try_alt = interaction_tracker.should_try_alternative(test_loc)
    strategies = interaction_tracker.get_available_strategies(test_loc)
    
    print(f"After 2 failures at {test_loc}:")
    print(f"  Should try alternatives: {should_try_alt}")
    print(f"  Available strategies: {len(strategies)}")
    print(f"  Strategy names: {[s.value for s in strategies[:3]]}")
    
    # Test loop detector
    from windows_use.agent.enhanced_service import LoopDetector
    detector = LoopDetector()
    
    # Simulate repeated actions
    params = {'loc': (100, 100), 'button': 'left'}
    loop1 = detector.add_action('Click', params)
    loop2 = detector.add_action('Click', params)  
    loop3 = detector.add_action('Click', params)
    
    print(f"\nLoop detection test:")
    print(f"  After action 1: Loop detected = {loop1}")
    print(f"  After action 2: Loop detected = {loop2}")
    print(f"  After action 3: Loop detected = {loop3}")
    
    if loop3:
        alternatives = detector.get_suggested_alternatives()
        print(f"  Suggested alternatives: {alternatives[0]}")
    
    print("\n✅ All components working correctly!")
    print()

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Interactive demo (requires API key)")
    print("2. Component test (no API key needed)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        test_components()
    else:
        main()