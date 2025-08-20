"""
Test script for V2 Multi-Stage Agent
Tests the decomposition logic without full execution
"""

from mainv2 import TaskDecomposer, MultiStageAgent
import json

def test_decomposition():
    """Test task decomposition into stages"""
    print("Testing V2 Task Decomposition")
    print("="*50)
    
    decomposer = TaskDecomposer()
    
    test_cases = [
        "Open Notepad and type Hello World",
        "Research iPhone prices and create comparison spreadsheet", 
        "Check weather for tomorrow and write it in a text file",
        "Open Settings and change display brightness to 50%"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        print("-" * 60)
        
        try:
            stages = decomposer.decompose(test_case)
            
            if stages:
                print(f"✅ Generated {len(stages)} stages:")
                for j, stage in enumerate(stages, 1):
                    print(f"\n   Stage {j}:")
                    print(f"      Goal: {stage.goal}")
                    print(f"      Description: {stage.description}")
                    print(f"      App: {stage.focus_app}")
                    print(f"      Success: {stage.success_indicator}")
            else:
                print("❌ Failed to decompose task")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_simple_execution():
    """Test with a simple single-stage task"""
    print("\n" + "="*60)
    print("Testing Simple Task Execution")
    print("="*60)
    
    # Test with a simple task that should work
    simple_task = "Open Notepad"
    
    print(f"Testing: {simple_task}")
    print("Note: This will actually execute - make sure you want to test this")
    
    response = input("Proceed with execution test? (y/N): ")
    if response.lower() == 'y':
        agent = MultiStageAgent()
        result = agent.execute(simple_task)
        print(f"Result: {result}")
    else:
        print("Skipped execution test")

if __name__ == "__main__":
    # Test decomposition logic
    test_decomposition()
    
    # Optionally test simple execution
    test_simple_execution()