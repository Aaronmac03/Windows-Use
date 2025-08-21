#!/usr/bin/env python3
"""
Quick test to verify Click Tool fix in Enhanced Agent
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_tool_availability():
    """Test that both agents have Click Tool available"""
    
    print("🔍 TESTING TOOL AVAILABILITY")
    print("=" * 50)
    
    try:
        # Import both agents
        from windows_use.agent.service import Agent
        from windows_use.agent.enhanced_service import EnhancedAgent
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Initialize a basic LLM for testing
        llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', temperature=0.1)
        
        # Test Base Agent
        print("1. Testing Base Agent...")
        base_agent = Agent(llm=llm, browser='chrome')
        base_tools = list(base_agent.registry.tools_registry.keys())
        print(f"   Base Agent Tools: {base_tools}")
        print(f"   Has 'Click Tool': {'Click Tool' in base_tools}")
        
        # Test Enhanced Agent
        print("\n2. Testing Enhanced Agent...")
        enhanced_agent = EnhancedAgent(llm=llm, browser='chrome')
        enhanced_tools = list(enhanced_agent.registry.tools_registry.keys())
        print(f"   Enhanced Agent Tools: {enhanced_tools}")
        print(f"   Has 'Click Tool': {'Click Tool' in enhanced_tools}")
        
        # Compare tools
        print(f"\n3. Tool Comparison:")
        print(f"   Base has {len(base_tools)} tools")
        print(f"   Enhanced has {len(enhanced_tools)} tools")
        
        missing_from_enhanced = set(base_tools) - set(enhanced_tools)
        extra_in_enhanced = set(enhanced_tools) - set(base_tools)
        
        if missing_from_enhanced:
            print(f"   ⚠️  Missing from Enhanced: {missing_from_enhanced}")
        if extra_in_enhanced:
            print(f"   ✅ Extra in Enhanced: {extra_in_enhanced}")
            
        # Specific Click Tool test
        print(f"\n4. Click Tool Test:")
        try:
            base_click_tool = base_agent.registry.tools_registry.get('Click Tool')
            enhanced_click_tool = enhanced_agent.registry.tools_registry.get('Click Tool')
            
            if base_click_tool and enhanced_click_tool:
                print(f"   ✅ Base Agent Click Tool: {base_click_tool.name}")
                print(f"   ✅ Enhanced Agent Click Tool: {enhanced_click_tool.name}")
                print(f"   🎯 FIX SUCCESSFUL: Both agents have 'Click Tool'")
                return True
            else:
                print(f"   ❌ Click Tool missing: Base={base_click_tool is not None}, Enhanced={enhanced_click_tool is not None}")
                return False
            
        except Exception as e:
            print(f"   ❌ Click Tool Error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_enhanced_execution():
    """Test simple execution with Enhanced Agent"""
    
    print("\n\n🚀 TESTING SIMPLE ENHANCED EXECUTION")
    print("=" * 50)
    
    try:
        from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent
        from web_search import create_web_search_function
        
        # Simple task that requires clicking
        test_query = "Open Notepad and type 'Click Tool Fix Test - SUCCESS!'"
        
        print(f"Task: {test_query}")
        print("-" * 50)
        
        # Create web search function
        web_search_func = create_web_search_function()
        
        # Initialize the web-enhanced agent
        agent = WebEnhancedSmartWindowsAgent(
            web_search_func=web_search_func,
            translation_model="openai/gpt-4o-mini-search-preview:online"
        )
        
        # Execute the task
        result = agent.execute(test_query)
        
        print("✅ EXECUTION COMPLETED SUCCESSFULLY")
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 SUPPORT TICKET #002 - CLICK TOOL FIX VALIDATION")
    print("=" * 60)
    
    # Test 1: Tool availability
    tool_test_passed = test_tool_availability()
    
    if tool_test_passed:
        print("\n" + "="*60)
        # Test 2: Simple execution
        execution_test_passed = test_simple_enhanced_execution()
        
        print("\n" + "="*60)
        print("🎯 FINAL RESULTS:")
        print(f"   Tool Availability: {'✅ PASSED' if tool_test_passed else '❌ FAILED'}")
        print(f"   Simple Execution: {'✅ PASSED' if execution_test_passed else '❌ FAILED'}")
        
        if tool_test_passed and execution_test_passed:
            print("\n🎉 SUPPORT TICKET #002 RESOLVED!")
            print("   Enhanced Agent now has Click Tool available")
            print("   Ready for full enhanced UI testing")
        else:
            print("\n⚠️  Additional fixes needed")
    else:
        print("\n⚠️  Tool availability test failed - execution test skipped")