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
        
        prompt = f"""You are a Windows automation expert. Convert this request into EXACT steps.

CRITICAL RULES:
- Use EXACT button names and menu items (e.g., "Start button", not "Windows menu")
- Include what to wait for after each action
- Be specific about locations (e.g., "bottom-left corner", "top menu bar")
- Keep each instruction under 20 words
- Maximum 10 instructions total

User request: {query}

Return ONLY a JSON array of instruction strings, like:
["Click the Start button in the taskbar",
 "Wait for Start menu to appear",
 "Type 'notepad' in the search box",
 "Press Enter key"]

Instructions:"""

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
            return instructions[:10]  # Cap at 10 instructions
        except:
            # Fallback parsing
            return []

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
        
        # Generate instructions
        print(f"Analyzing task: {query}")
        instructions = self.analyzer.analyze(query)
        
        if not instructions:
            return "Failed to understand task"
        
        print(f"Generated {len(instructions)} instructions:")
        for i, inst in enumerate(instructions, 1):
            print(f"  {i}. {inst}")
        
        # Execute with Windows-Use
        print("\nExecuting...")
        agent = Agent(
            llm=self.executor_llm,
            instructions=instructions,  # Pass our generated instructions
            browser='chrome',
            use_vision=False,  # Keep vision off for cost
            max_steps=30
        )
        
        result = agent.invoke(query)
        return result.content or result.error or "No response"

def main():
    agent = SmartWindowsAgent()
    query = input("Enter your task: ")
    result = agent.execute(query)
    print(f"\nResult: {result}")

if __name__ == "__main__":
    main()