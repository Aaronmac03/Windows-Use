"""Test script for V1 Smart Instructions Generator"""
from mainv1 import SmartWindowsAgent
import sys

def test_task_analyzer():
    """Test the TaskAnalyzer component"""
    print("=== Testing V1 Smart Instructions Generator ===\n")
    
    # Test queries from implementation instructions
    test_queries = [
        "Open Notepad and type Hello World",
        "Open Chrome and go to google.com", 
        "Open Settings and search for display"
    ]
    
    agent = SmartWindowsAgent()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {query}")
        print(f"{'='*60}")
        
        try:
            # Test just the instruction generation first
            print("🔍 Analyzing task...")
            instructions = agent.analyzer.analyze(query)
            
            if not instructions:
                print("❌ Failed to generate instructions")
                continue
                
            print(f"✅ Generated {len(instructions)} instructions:")
            for j, inst in enumerate(instructions, 1):
                print(f"   {j}. {inst}")
                
            # Uncomment below to test full execution
            # print("\n🤖 Executing...")
            # result = agent.execute(query)
            # print(f"Result: {result}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_task_analyzer()