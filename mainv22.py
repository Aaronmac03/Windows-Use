import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv
import time

load_dotenv()

@dataclass
class SimpleStage:
    """A simplified stage that focuses on goals, not process"""
    goal: str
    checkpoint: str  # What success looks like
    
class SimpleDecomposer:
    """Decomposes only when truly necessary"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct",
            temperature=0.1,
            max_tokens=400,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Enhanced")
            }
        )
    
    def should_decompose(self, query: str) -> bool:
        """Determine if task needs decomposition at all"""
        
        # Keywords that suggest multi-stage necessity
        multi_stage_indicators = [
            "and then", "after that", "followed by", "next",
            "multiple", "several", "various", "different apps",
            "research and create", "find and compare", "download and install"
        ]
        
        query_lower = query.lower()
        
        # Check for explicit multi-stage indicators
        has_indicators = any(indicator in query_lower for indicator in multi_stage_indicators)
        
        # Check for multiple verbs suggesting sequential actions
        action_verbs = ["open", "search", "create", "write", "copy", "paste", "save", "download", "install", "compare"]
        verb_count = sum(1 for verb in action_verbs if verb in query_lower)
        
        return has_indicators or verb_count >= 3
    
    def decompose(self, query: str) -> List[SimpleStage]:
        """Create minimal stages only when absolutely necessary"""
        
        prompt = f"""Analyze this task and break it into 2-3 HIGH-LEVEL stages ONLY if it involves DIFFERENT applications or CANNOT be done in one continuous flow.

Task: {query}

Rules:
1. Only decompose if the task REQUIRES switching between different apps
2. Each stage should be a complete, self-contained goal
3. DO NOT decompose simple tasks that can be done in one app
4. Maximum 3 stages

Return JSON:
{{
  "needs_decomposition": true/false,
  "stages": [
    {{
      "goal": "High-level goal that Windows-Use can figure out",
      "checkpoint": "Observable outcome when complete"
    }}
  ]
}}

If needs_decomposition is false, return empty stages array."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            
            data = json.loads(content)
            
            if not data.get('needs_decomposition', False):
                return []
            
            stages = []
            for stage_data in data.get('stages', [])[:3]:  # Max 3 stages
                stages.append(SimpleStage(
                    goal=stage_data.get('goal', ''),
                    checkpoint=stage_data.get('checkpoint', '')
                ))
            
            return stages
            
        except Exception as e:
            print(f"Decomposition failed: {e}")
            return []

class SimplifiedMultiStageAgent:
    """Simplified multi-stage execution - only when truly needed"""
    
    def __init__(self):
        self.decomposer = SimpleDecomposer()
        # Use cheapest model for execution
        self.executor_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0
        )
    
    def execute(self, query: str) -> str:
        """Execute with optional decomposition"""
        
        print("="*70)
        print(f"TASK: {query}")
        print("="*70)
        
        # Step 1: Check if decomposition is needed
        if not self.decomposer.should_decompose(query):
            print("\n✅ Simple task - executing directly without decomposition")
            return self._execute_simple(query)
        
        # Step 2: Try to decompose
        print("\n🔍 Complex task detected - attempting decomposition...")
        stages = self.decomposer.decompose(query)
        
        if not stages:
            print("📌 Decomposition not beneficial - executing as single task")
            return self._execute_simple(query)
        
        # Step 3: Execute stages
        print(f"\n📋 Task split into {len(stages)} stages:")
        for i, stage in enumerate(stages, 1):
            print(f"   Stage {i}: {stage.goal}")
            print(f"   Checkpoint: {stage.checkpoint}")
        
        results = []
        for i, stage in enumerate(stages, 1):
            print(f"\n{'='*70}")
            print(f"STAGE {i}/{len(stages)}: {stage.goal}")
            print(f"{'='*70}")
            
            result = self._execute_stage(stage.goal, max_steps=30)
            
            if "error" in result.lower() or "failed" in result.lower():
                print(f"\n⚠️ Stage {i} had issues but continuing...")
            else:
                print(f"\n✅ Stage {i} completed")
            
            results.append(f"Stage {i}: {result}")
            
            # Brief pause between stages
            if i < len(stages):
                time.sleep(2)
        
        return "\n\n".join(results)
    
    def _execute_simple(self, query: str) -> str:
        """Execute task without decomposition"""
        return self._execute_stage(query, max_steps=40)
    
    def _execute_stage(self, goal: str, max_steps: int = 30) -> str:
        """Execute a single stage or simple task"""
        
        try:
            agent = Agent(
                llm=self.executor_llm,
                browser='chrome',
                use_vision=False,
                max_steps=max_steps
            )
            
            print(f"\n🤖 Executing: {goal[:100]}...")
            result = agent.invoke(goal)
            
            if result.error:
                return f"Error: {result.error}"
            
            return result.content or "Task completed"
            
        except Exception as e:
            return f"Execution failed: {str(e)}"

def main():
    """Main entry point"""
    agent = SimplifiedMultiStageAgent()
    
    print("Simplified Multi-Stage Agent (V2 - Fixed)")
    print("Only decomposes when truly necessary")
    print("Models: Qwen 72B (decomposition), Gemini Flash Lite (execution)")
    
    # Test cases or interactive mode
    test_mode = input("\nMode:\n1. Test with examples\n2. Interactive\nChoice: ")
    
    if test_mode == "1":
        test_cases = [
            "Open Notepad and type Hello World",
            "Open Chrome and search for Python documentation",
            "Research laptop prices online and create a comparison in Notepad",
            "Open Chrome, go to lowes, and add a cheap flat head screwdriver to my cart. Use the Lowe's near bashford manor and set it for pickup."
        ]
        
        for test in test_cases:
            print(f"\n{'='*70}")
            print(f"TEST: {test}")
            print(f"{'='*70}")
            result = agent.execute(test)
            print(f"\nRESULT: {result}")
            input("\nPress Enter to continue...")
    
    else:
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