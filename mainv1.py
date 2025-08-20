import json
import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv

load_dotenv()

class TaskAnalyzer:
    """Generates specific Windows-Use instructions from user queries"""
    
    def __init__(self):
        # Use Qwen for cheap analysis
        self.llm = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct",
            temperature=0.1,
            max_tokens=500,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Enhanced")
            }
        )
    
    def analyze(self, query: str) -> List[str]:
        """Convert user query into specific step-by-step instructions"""
        
        # Simplified prompt that focuses on HIGH-LEVEL guidance
        prompt = f"""You are a Windows automation expert. Convert this request into clear guidance steps.

RULES:
- Focus on WHAT to do, not HOW to click (the agent knows how to click)
- Be specific about app names and URLs
- Include key search terms and button names
- Maximum 8 high-level steps
- Each step should guide towards the goal

User request: {query}

Return ONLY a JSON array of guidance steps, like:
["Open Google Chrome browser",
 "Navigate to lowes.com website",
 "Search for flat head screwdriver",
 "Select a cheap option and add to cart"]

Steps:"""

        response = self.llm.invoke(prompt)
        return self._parse_instructions(response.content)
    
    def _parse_instructions(self, content: str) -> List[str]:
        """Extract instructions from LLM response"""
        try:
            # Clean up response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            instructions = json.loads(content.strip())
            # Ensure it's a list and cap at 8 instructions
            if isinstance(instructions, list):
                return instructions[:8]
            return []
        except Exception as e:
            print(f"Warning: Failed to parse JSON: {e}")
            # Try basic line splitting as fallback
            lines = content.strip().split('\n')
            return [line.strip('- •123456789.[] "\'') for line in lines if line.strip()][:8]

class SmartWindowsAgent:
    """Enhanced Windows agent with instruction generation"""
    
    def __init__(self):
        self.analyzer = TaskAnalyzer()
        # Use cheapest model for execution
        self.executor_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0
        )
    
    def execute(self, query: str) -> str:
        """Execute task with generated instructions"""
        
        print("="*60)
        print(f"TASK: {query}")
        print("="*60)
        
        # Generate instructions
        print("\n🔍 Analyzing task...")
        instructions = self.analyzer.analyze(query)
        
        if not instructions:
            print("❌ Failed to understand task")
            return "Failed to understand task"
        
        print(f"\n📋 Generated {len(instructions)} instructions:")
        for i, inst in enumerate(instructions, 1):
            print(f"   {i}. {inst}")
        
        # Execute with Windows-Use
        print(f"\n🤖 Executing with Windows-Use agent...")
        print(f"   Model: gemini-2.5-flash-lite")
        print(f"   Vision: False")
        print(f"   Max steps: 30")
        print("\n" + "-"*60)
        
        try:
            agent = Agent(
                llm=self.executor_llm,
                instructions=instructions,  # Pass our generated instructions
                browser='chrome',
                use_vision=False,  # Keep vision off for cost
                max_steps=30
            )
            
            result = agent.invoke(query)
            
            print("-"*60)
            
            if result.error:
                print(f"\n❌ Execution error: {result.error}")
                return f"Error: {result.error}"
            
            print(f"\n✅ Task completed")
            return result.content or "Task completed successfully"
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            return f"Error: {str(e)}"

def main():
    """Main entry point"""
    agent = SmartWindowsAgent()
    
    # Get query from user
    query = input("Enter your task: ")
    
    # Execute
    result = agent.execute(query)
    
    print("\n" + "="*60)
    print("FINAL RESULT:")
    print("="*60)
    print(result)

if __name__ == "__main__":
    main()