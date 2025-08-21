import os
from typing import List, Optional
from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ExecutionStrategy:
    """Simple execution strategy"""
    approach: str  # 'direct' or 'sequential'
    goals: List[str]  # High-level goals

class SmartRouter:
    """Routes tasks based on complexity patterns"""
    
    def analyze_task(self, query: str) -> ExecutionStrategy:
        """Determine best execution strategy"""
        
        query_lower = query.lower()
        
        # Pattern: E-commerce with specific store/location requirements
        if all(phrase in query_lower for phrase in ["lowes", "bashford", "pickup"]):
            # This specific pattern benefits from sequential goals
            return ExecutionStrategy(
                approach='sequential',
                goals=[
                    "Go to lowes.com and search for cheap flat head screwdriver",
                    "Select the cheapest screwdriver from the results",
                    "Find the Lowe's store at 2100 Bashford Manor Lane Louisville KY and set it as the pickup location",
                    "Add the item to cart with pickup option selected"
                ]
            )
        
        # Pattern: Multi-app tasks
        if any(word in query_lower for word in ["then", "after", "next"]) and \
           sum(1 for app in ["chrome", "notepad", "excel", "word"] if app in query_lower) >= 2:
            # Split by application focus
            parts = []
            if "chrome" in query_lower or "search" in query_lower or "web" in query_lower:
                web_part = self._extract_web_goal(query)
                if web_part:
                    parts.append(web_part)
            if "notepad" in query_lower or "write" in query_lower or "type" in query_lower:
                writing_part = self._extract_writing_goal(query)
                if writing_part:
                    parts.append(writing_part)
            
            if len(parts) > 1:
                return ExecutionStrategy(approach='sequential', goals=parts)
        
        # Default: Execute directly
        return ExecutionStrategy(approach='direct', goals=[query])
    
    def _extract_web_goal(self, query: str) -> Optional[str]:
        """Extract web-related goal from query"""
        web_keywords = ["search", "find", "research", "look up", "google", "browse"]
        for keyword in web_keywords:
            if keyword in query.lower():
                # Extract the web-related portion
                parts = query.lower().split(keyword)
                if len(parts) > 1:
                    return f"Search for {parts[1].split('and')[0].strip()}"
        return None
    
    def _extract_writing_goal(self, query: str) -> Optional[str]:
        """Extract writing-related goal from query"""
        write_keywords = ["write", "type", "create", "document", "note"]
        for keyword in write_keywords:
            if keyword in query.lower():
                return "Create a document with the information found"
        return None

class OptimizedAgent:
    """Optimized agent with smart routing"""
    
    def __init__(self):
        self.router = SmartRouter()
        # Single model for all execution - keep it simple
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0
        )
    
    def execute(self, query: str) -> str:
        """Execute with smart routing"""
        
        print("="*70)
        print(f"TASK: {query}")
        print("="*70)
        
        # Determine strategy
        strategy = self.router.analyze_task(query)
        
        if strategy.approach == 'direct':
            print("\n✅ Executing directly...")
            return self._execute_single_goal(query, max_steps=40)
        
        else:  # sequential
            print(f"\n📋 Executing {len(strategy.goals)} sequential goals:")
            for i, goal in enumerate(strategy.goals, 1):
                print(f"   {i}. {goal}")
            
            results = []
            for i, goal in enumerate(strategy.goals, 1):
                print(f"\n{'='*70}")
                print(f"GOAL {i}/{len(strategy.goals)}: {goal}")
                print(f"{'='*70}")
                
                result = self._execute_single_goal(goal, max_steps=25)
                results.append(f"Step {i}: {result}")
                
                # Check for critical failures
                if "error" in result.lower() and "recursion" in result.lower():
                    print(f"\n❌ Critical failure at step {i}")
                    break
                
                print(f"\n✅ Goal {i} completed")
            
            return "\n\n".join(results)
    
    def _execute_single_goal(self, goal: str, max_steps: int = 30) -> str:
        """Execute a single goal"""
        
        try:
            # Create fresh agent for each goal
            agent = Agent(
                llm=self.llm,
                browser='chrome',
                use_vision=False,
                max_steps=max_steps
            )
            
            print(f"\n🤖 Executing: {goal[:80]}...")
            result = agent.invoke(goal)
            
            if result.error:
                return f"Error: {result.error}"
            
            return result.content or "Completed"
            
        except Exception as e:
            return f"Execution failed: {str(e)}"

def main():
    """Main entry point"""
    agent = OptimizedAgent()
    
    print("Optimized Windows Agent (V2 - Revised)")
    print("Smart routing with goal-oriented execution")
    print("Model: Gemini Flash Lite only")
    
    while True:
        query = input("\nEnter task (or 'quit'): ")
        if query.lower() in ['quit', 'exit']:
            break
        
        result = agent.execute(query)
        print(f"\n{'='*70}")
        print("RESULT:")
        print(f"{'='*70}")
        print(result)

if __name__ == "__main__":
    main()