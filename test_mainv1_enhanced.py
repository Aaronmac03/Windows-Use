#!/usr/bin/env python3
"""
Test script for Web-Enhanced Smart Windows Agent with a complex challenging task
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent
from web_search import create_web_search_function

def test_complex_task():
    """Test the agent with a complex e-commerce task"""
    
    print("=" * 80)
    print("TESTING: Web-Enhanced Smart Windows Agent V1.1")
    print("Complex Task: Multi-step e-commerce with location and product research")
    print("=" * 80)
    
    # Complex test query that requires web enhancement
    test_query = """Find and compare the top 3 wireless earbuds under $100 on Amazon that are compatible with both iPhone and Android. Look for models with at least 4.5 star ratings, active noise cancellation, and over 20 hours of battery life. Check customer reviews from the past month for any recurring issues. Add the best value option to your cart but don't complete the purchase. Also check if there are any current discount codes or promotions available."""
    
    print(f"TASK: {test_query}")
    print("-" * 80)
    
    try:
        # Create web search function
        web_search_func = create_web_search_function()
        
        # Initialize the web-enhanced agent
        agent = WebEnhancedSmartWindowsAgent(
            web_search_func=web_search_func,
            translation_model="openai/gpt-4o-mini-search-preview:online"
        )
        
        # Execute the task
        print("🚀 Starting execution...")
        result = agent.execute(test_query)
        
        print("=" * 80)
        print("EXECUTION COMPLETED")
        print("=" * 80)
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_simple_task():
    """Test with a simpler task first to verify basic functionality"""
    
    print("=" * 80)
    print("TESTING: Web-Enhanced Smart Windows Agent V1.1 - Simple Task")
    print("=" * 80)
    
    # Simple test query
    test_query = "Open Notepad and type 'Hello World from Windows-Use Enhanced Agent!'"
    
    print(f"TASK: {test_query}")
    print("-" * 80)
    
    try:
        # Create web search function
        web_search_func = create_web_search_function()
        
        # Initialize the web-enhanced agent
        agent = WebEnhancedSmartWindowsAgent(
            web_search_func=web_search_func,
            translation_model="openai/gpt-4o-mini-search-preview:online"
        )
        
        # Execute the task
        print("🚀 Starting execution...")
        result = agent.execute(test_query)
        
        print("=" * 80)
        print("EXECUTION COMPLETED")
        print("=" * 80)
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # First test simple task
    print("🧪 STARTING SIMPLE TASK TEST")
    test_simple_task()
    
    print("\n" + "="*80 + "\n")
    
    # Then test complex task
    print("🧪 STARTING COMPLEX TASK TEST")
    test_complex_task()