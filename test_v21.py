"""
Test script for Enhanced Multi-Stage Agent (V2.1)
Tests the improved multi-stage execution with better error handling and state management
"""

import sys
import os
from mainv21 import EnhancedMultiStageAgent

def test_simple_task():
    """Test a simple multi-stage task"""
    print("="*60)
    print("TEST 1: Simple Multi-Stage Task")
    print("="*60)
    
    agent = EnhancedMultiStageAgent()
    query = "Open Notepad and type 'Hello from V2.1 Enhanced Agent'"
    
    print(f"Query: {query}")
    result = agent.execute(query)
    
    print("\n" + "="*40)
    print("RESULT:")
    print("="*40)
    print(result)
    return result

def test_medium_complexity():
    """Test a medium complexity multi-stage task"""
    print("\n" + "="*60)
    print("TEST 2: Medium Complexity Task")
    print("="*60)
    
    agent = EnhancedMultiStageAgent()
    query = "Open Chrome, go to google.com, and search for 'Python automation'"
    
    print(f"Query: {query}")
    result = agent.execute(query)
    
    print("\n" + "="*40)
    print("RESULT:")
    print("="*40)
    print(result)
    return result

def test_complex_task():
    """Test a complex multi-stage task"""
    print("\n" + "="*60)
    print("TEST 3: Complex Multi-Stage Task")
    print("="*60)
    
    agent = EnhancedMultiStageAgent()
    query = "Open Chrome, search for 'Windows automation tools', then open Notepad and write a summary of what I found"
    
    print(f"Query: {query}")
    result = agent.execute(query)
    
    print("\n" + "="*40)
    print("RESULT:")
    print("="*40)
    print(result)
    return result

def interactive_test():
    """Run interactive test with user input"""
    print("\n" + "="*60)
    print("INTERACTIVE TEST: Enter Your Own Task")
    print("="*60)
    
    agent = EnhancedMultiStageAgent()
    
    while True:
        query = input("\nEnter a multi-stage task (or 'quit' to exit): ")
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query.strip():
            continue
            
        print(f"\nExecuting: {query}")
        result = agent.execute(query)
        
        print(f"\n{'='*40}")
        print("RESULT:")
        print(f"{'='*40}")
        print(result)
        
        continue_test = input("\nRun another test? (y/n): ")
        if continue_test.lower() not in ['y', 'yes']:
            break

def main():
    """Main test runner"""
    print("Enhanced Multi-Stage Agent (V2.1) - Test Suite")
    print("Models: Qwen 72B (decomposition), Gemini Flash Lite (execution), Gemini Flash Lite (validation)")
    print("This tests the improved multi-stage execution capabilities")
    print("Key improvements: better error handling, state management, validation")
    
    test_mode = input("\nSelect test mode:\n1. Run all automated tests\n2. Interactive testing\n3. Single test\nChoice (1/2/3): ")
    
    if test_mode == "1":
        print("\nRunning all automated tests...")
        try:
            test_simple_task()
            test_medium_complexity() 
            test_complex_task()
            print("\n" + "="*60)
            print("ALL TESTS COMPLETED")
            print("="*60)
        except Exception as e:
            print(f"\nTest suite error: {e}")
    
    elif test_mode == "2":
        interactive_test()
    
    elif test_mode == "3":
        test_choice = input("\nWhich test?\n1. Simple task\n2. Medium complexity\n3. Complex task\nChoice (1/2/3): ")
        
        try:
            if test_choice == "1":
                test_simple_task()
            elif test_choice == "2":
                test_medium_complexity()
            elif test_choice == "3":
                test_complex_task()
            else:
                print("Invalid choice")
        except Exception as e:
            print(f"\nTest error: {e}")
    
    else:
        print("Invalid selection")

if __name__ == "__main__":
    main()