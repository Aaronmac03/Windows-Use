import json
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv
import os

load_dotenv()

class TaskAnalyzer:
    """Analyzes tasks and generates specific Windows-Use instructions"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct",
            temperature=0.1,
            max_tokens=500,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/windows-use",
                "X-Title": "Windows-Use Enhanced"
            }
        )
    
    def analyze(self, query: str) -> List[str]:
        """Generate specific step-by-step instructions for Windows-Use"""
        
        prompt = f"""You are a Windows automation expert. Convert this user request into SPECIFIC, 
ACTIONABLE instructions for a Windows automation agent.

Rules:
1. Be extremely specific about UI elements (exact button names, menu paths)
2. Include verification steps (what to look for to confirm success)
3. Handle common edge cases (popups, delays, alternate paths)
4. Use exact Windows terminology

User request: {query}

Return a JSON array of instruction strings. Each instruction should be a complete, 
specific directive. Example:
["Click on the Start button in the bottom-left corner",
 "Type 'notepad' in the search box",
 "Press Enter to launch Notepad",
 "Wait for Notepad window to appear (look for 'Untitled - Notepad' in title bar)",
 "Type the requested text"]

Instructions:"""

        response = self.llm.invoke(prompt)
        
        try:
            # Extract JSON from response
            content = response.content
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            instructions = json.loads(content.strip())
            return instructions if isinstance(instructions, list) else []
        except:
            # Fallback: split by newlines if JSON parsing fails
            lines = response.content.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip()]

class SmartWindowsAgent:
    """Enhanced Windows-Use agent with task analysis"""
    
    def __init__(self, use_vision=False):
        self.analyzer = TaskAnalyzer()
        self.executor_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0
        )
        self.use_vision = use_vision
        
    def execute(self, query: str) -> str:
        """Execute task with enhanced instructions"""
        
        print(f"\n{'='*60}")
        print(f"TASK: {query}")
        print(f"{'='*60}\n")
        
        # Step 1: Analyze and generate instructions
        print("🔍 Analyzing task...")
        instructions = self.analyzer.analyze(query)
        
        if not instructions:
            print("❌ Failed to analyze task")
            return "Error: Could not understand the task"
        
        print(f"\n📋 Generated {len(instructions)} instructions:")
        for i, inst in enumerate(instructions, 1):
            print(f"   {i}. {inst}")
        
        # Step 2: Execute with Windows-Use
        print(f"\n🤖 Executing with Windows-Use agent...")
        print(f"   Model: {self.executor_llm.model_name}")
        print(f"   Vision: {self.use_vision}")
        
        try:
            agent = Agent(
                llm=self.executor_llm,
                instructions=instructions,
                browser='chrome',
                use_vision=self.use_vision,
                max_steps=30
            )
            
            result = agent.invoke(query)
            
            if result.error:
                print(f"\n❌ Execution error: {result.error}")
                return f"Error: {result.error}"
            
            print(f"\n✅ Task completed successfully")
            return result.content
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            return f"Error: {str(e)}"

def main():
    """Main entry point"""
    agent = SmartWindowsAgent(use_vision=False)
    
    # Get query from user
    query = input("Enter your task: ")
    
    # Execute
    result = agent.execute(query)
    
    print(f"\n{'='*60}")
    print("FINAL RESULT:")
    print(f"{'='*60}")
    print(result)

if __name__ == "__main__":
    main()