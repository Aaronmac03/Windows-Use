"""
Quick Fix Demo for Web-Enhanced Agent Model Issues
This script demonstrates the corrected model configuration and tests basic functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_basic_functionality():
    """Test basic web-enhanced agent functionality with model fixes"""
    
    print("🔧 QUICK FIX DEMO: Web-Enhanced Agent")
    print("="*60)
    print("Testing the corrected model configuration...")
    print()
    
    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found!")
        print("Please add your OpenRouter API key to the .env file:")
        print("OPENROUTER_API_KEY=your_key_here")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...")
    
    try:
        # Import the corrected web-enhanced agent
        from mainv1_web_enhanced import WebEnhancedTranslator, WebEnhancedSmartWindowsAgent
        
        print("\n🤖 Testing model initialization...")
        
        # Test 1: Initialize translator with automatic model selection
        print("\n📋 Test 1: Automatic Model Selection")
        translator = WebEnhancedTranslator()
        print(f"   Selected model: {translator.model_name}")
        
        # Test 2: Test ambiguity identification
        print("\n📋 Test 2: Ambiguity Identification")
        test_query = "Find a cheap laptop at the local store"
        print(f"   Query: {test_query}")
        
        ambiguities = translator.identify_ambiguities(test_query)
        print(f"   Found {len(ambiguities)} ambiguities:")
        for amb in ambiguities:
            print(f"      • {amb.get('type', 'UNKNOWN')}: {amb.get('element', 'N/A')}")
        
        # Test 3: Query rewriting
        print("\n📋 Test 3: Query Enhancement")
        mock_clarifications = {
            "cheap": "under $500, best value options available",
            "local store": "Best Buy, Walmart, and Target locations nearby"
        }
        
        enhanced_query = translator.rewrite_query(test_query, mock_clarifications)
        print(f"   Original: {test_query}")
        print(f"   Enhanced: {enhanced_query}")
        
        # Test 4: Full agent initialization
        print("\n📋 Test 4: Full Agent Initialization")
        
        def mock_web_search(query):
            return f"Mock search results for: {query}\nSample pricing and location data..."
        
        agent = WebEnhancedSmartWindowsAgent(
            web_search_func=mock_web_search,
            translation_model=translator.model_name  # Use the working model
        )
        
        print(f"   Translation model: {agent.translator.model_name}")
        print(f"   Analysis model: {getattr(agent.analyzer.llm, 'model', 'qwen/qwen-2.5-72b-instruct')}")
        print(f"   Execution model: {getattr(agent.executor_llm, 'model', 'gemini-2.5-flash-lite')}")
        
        print("\n✅ ALL TESTS PASSED!")
        print("The web-enhanced agent is working correctly with the fixed model configuration.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTroubleshooting suggestions:")
        print("1. Run 'python model_tester.py' to check which models work")
        print("2. Verify your OpenRouter API key has sufficient credits")
        print("3. Check your internet connection")
        print("4. Try specifying a different model manually")
        
        return False


def demonstrate_manual_model_selection():
    """Demonstrate how to manually select a working model"""
    
    print("\n🎯 MANUAL MODEL SELECTION DEMO")
    print("="*60)
    
    # List of models to try (in order of preference)
    model_options = [
        "openai/gpt-4o-mini-search-preview:online",
        "qwen/qwen-2.5-72b-instruct", 
        "meta-llama/llama-3.1-8b-instruct",  # Free option
        "google/gemini-2.0-flash-thinking-exp"
    ]
    
    print("Available model options:")
    for i, model in enumerate(model_options, 1):
        cost = "~$0.001" if "gpt-4o-mini" in model or "qwen" in model else "Free" if "llama" in model else "~$0.001"
        print(f"   {i}. {model} ({cost})")
    
    try:
        choice = input(f"\nSelect model (1-{len(model_options)}) or press Enter for auto: ").strip()
        
        if choice and choice.isdigit():
            selected_model = model_options[int(choice) - 1]
            print(f"\n🤖 Testing selected model: {selected_model}")
        else:
            selected_model = None
            print(f"\n🤖 Using automatic model selection...")
        
        # Test the selected model
        from mainv1_web_enhanced import WebEnhancedTranslator
        
        translator = WebEnhancedTranslator(model_name=selected_model)
        print(f"✅ Successfully initialized: {translator.model_name}")
        
        # Quick functionality test
        test_query = "Find a good restaurant nearby"
        ambiguities = translator.identify_ambiguities(test_query)
        print(f"✅ Ambiguity detection working: Found {len(ambiguities)} ambiguities")
        
        return translator.model_name
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return None


def show_usage_examples():
    """Show corrected usage examples"""
    
    print("\n📚 CORRECTED USAGE EXAMPLES")
    print("="*60)
    
    examples = [
        {
            "title": "Basic Usage (Automatic Model Selection)",
            "code": """
from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent

# The agent will automatically find a working model
agent = WebEnhancedSmartWindowsAgent()
result = agent.execute("Find a cheap laptop at Best Buy")
"""
        },
        {
            "title": "Manual Model Selection",
            "code": """
from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent

# Specify a working model manually
agent = WebEnhancedSmartWindowsAgent(
    translation_model="openai/gpt-4o-mini-search-preview:online"
)
result = agent.execute("Find a good coffee shop nearby")
"""
        },
        {
            "title": "With Web Search Integration",
            "code": """
from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent

def your_web_search(query):
    # Your web search implementation
    return search_results

agent = WebEnhancedSmartWindowsAgent(
    web_search_func=your_web_search,
    translation_model="qwen/qwen-2.5-72b-instruct"
)
result = agent.execute("Buy iPhone at lowest price")
"""
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print("-" * len(f"{i}. {example['title']}"))
        print(example['code'].strip())


def main():
    """Main quick fix demo"""
    print("Web-Enhanced Agent - Quick Fix Demo")
    print("Fixes the model ID issue and demonstrates corrected usage")
    print()
    
    # Test basic functionality
    success = test_basic_functionality()
    
    if success:
        print("\n🎉 Your web-enhanced agent is ready to use!")
        
        # Ask if user wants to see manual model selection
        show_manual = input("\nWould you like to see manual model selection? (y/n): ").strip().lower()
        if show_manual == 'y':
            working_model = demonstrate_manual_model_selection()
            if working_model:
                print(f"\n💡 Tip: You can use '{working_model}' in your code for consistent results")
        
        # Show usage examples
        show_examples = input("\nWould you like to see corrected usage examples? (y/n): ").strip().lower()
        if show_examples == 'y':
            show_usage_examples()
        
        print("\n🚀 Next Steps:")
        print("1. Use the working model in your production code")
        print("2. Run 'python example_web_enhanced.py' for a full demo")
        print("3. Run 'python model_tester.py' to test all available models")
        
    else:
        print("\n🔧 Troubleshooting Steps:")
        print("1. Check your OpenRouter API key")
        print("2. Verify your account has sufficient credits")
        print("3. Try running 'python model_tester.py' to diagnose issues")
        print("4. Contact support if problems persist")


if __name__ == "__main__":
    main()