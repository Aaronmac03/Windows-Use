import json
import os
from typing import List, Dict
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TaskStage:
    """Represents one stage of a multi-stage task"""
    goal: str                    # Simple goal statement for Windows-Use
    description: str             # Human-readable description
    success_indicator: str       # What to look for to confirm success
    focus_app: str              # Primary app this stage works with

class TaskDecomposer:
    """Breaks complex tasks into executable goal-oriented stages"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct",
            temperature=0.1,
            max_tokens=600,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Enhanced")
            }
        )
    
    def decompose(self, query: str) -> List[TaskStage]:
        """Break task into goal-oriented stages"""
        
        prompt = f"""Break this Windows task into 2-4 sequential stages. Each stage should be a simple GOAL that Windows-Use can accomplish independently.

CRITICAL RULES:
- Each stage = ONE clear goal for Windows-Use agent
- Focus on WHAT to achieve, not HOW to click
- Keep goals simple and atomic
- Stages should be sequential and logical
- Include what success looks like for each stage

Task: {query}

Return JSON with this structure:
{{
  "stages": [
    {{
      "goal": "Simple goal statement for Windows-Use agent",
      "description": "Human-readable explanation of this stage", 
      "success_indicator": "What confirms this stage succeeded",
      "focus_app": "primary app name (chrome/notepad/settings/explorer/etc)"
    }}
  ]
}}

Example for "Research iPhone prices and create comparison spreadsheet":
{{
  "stages": [
    {{
      "goal": "Search for iPhone 15 pricing information online",
      "description": "Research current iPhone 15 prices from multiple sources",
      "success_indicator": "Page showing iPhone prices is displayed",
      "focus_app": "chrome"
    }},
    {{
      "goal": "Create a new spreadsheet with iPhone price comparison data",  
      "description": "Open Excel and create comparison table with researched prices",
      "success_indicator": "Excel spreadsheet with price data is created",
      "focus_app": "excel"
    }}
  ]
}}

Stages:"""

        response = self.llm.invoke(prompt)
        return self._parse_stages(response.content)
    
    def _parse_stages(self, content: str) -> List[TaskStage]:
        """Parse stages from response"""
        try:
            # Clean JSON from response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            data = json.loads(content.strip())
            stages = []
            
            for stage_data in data.get('stages', [])[:4]:  # Max 4 stages
                stages.append(TaskStage(
                    goal=stage_data.get('goal', ''),
                    description=stage_data.get('description', ''),
                    success_indicator=stage_data.get('success_indicator', ''),
                    focus_app=stage_data.get('focus_app', 'explorer')
                ))
            
            return stages
        except Exception as e:
            print(f"❌ Failed to parse stages: {e}")
            return []

class StageValidator:
    """Validates stage completion using cheap model"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0,
            max_tokens=200
        )
    
    def validate_stage(self, stage: TaskStage, execution_result: str) -> Dict[str, any]:
        """Check if stage was completed successfully"""
        
        prompt = f"""Did this stage complete successfully? 

STAGE GOAL: {stage.goal}
SUCCESS INDICATOR: {stage.success_indicator}

EXECUTION RESULT:
{execution_result[:2000]}  

Return JSON only:
{{
  "success": true/false,
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}}

Be strict - only return true if there's clear evidence the goal was achieved."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            return json.loads(content)
        except:
            return {"success": False, "confidence": 0.0, "reason": "Validation failed"}

class MultiStageAgent:
    """Executes tasks in goal-oriented stages with validation"""
    
    def __init__(self):
        self.decomposer = TaskDecomposer()
        self.validator = StageValidator()
        self.executor_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0
        )
        
    def execute(self, query: str) -> str:
        """Execute multi-stage task"""
        
        print("="*70)
        print(f"MULTI-STAGE TASK: {query}")
        print("="*70)
        
        # Step 1: Decompose into stages
        print("\n🔍 Decomposing task into stages...")
        stages = self.decomposer.decompose(query)
        
        if not stages:
            print("❌ Could not decompose task into stages")
            return "Failed to understand task structure"
        
        print(f"\n📋 Task decomposed into {len(stages)} stages:")
        for i, stage in enumerate(stages, 1):
            print(f"\n   Stage {i}: {stage.description}")
            print(f"      Goal: {stage.goal}")
            print(f"      App: {stage.focus_app}")
            print(f"      Success: {stage.success_indicator}")
        
        # Step 2: Execute each stage
        stage_results = []
        
        for i, stage in enumerate(stages, 1):
            print(f"\n{'='*70}")
            print(f"EXECUTING STAGE {i}/{len(stages)}")
            print(f"{'='*70}")
            print(f"Goal: {stage.goal}")
            print(f"App Focus: {stage.focus_app}")
            
            # Execute stage with Windows-Use
            try:
                agent = Agent(
                    llm=self.executor_llm,
                    browser='chrome',
                    use_vision=False,
                    max_steps=25  # Reasonable limit per stage
                )
                
                # Pass the simple goal to Windows-Use - let it figure out HOW
                print(f"\n🤖 Executing with Windows-Use...")
                result = agent.invoke(stage.goal)
                
                if result.error:
                    print(f"\n❌ Stage {i} failed: {result.error}")
                    return f"Task failed at stage {i}: {result.error}"
                
                stage_result = result.content or "Stage completed"
                print(f"\n📄 Stage {i} result preview:")
                print(f"   {stage_result[:200]}{'...' if len(stage_result) > 200 else ''}")
                
                # Step 3: Validate stage completion
                print(f"\n🔍 Validating stage {i} completion...")
                validation = self.validator.validate_stage(stage, stage_result)
                
                print(f"   Success: {validation.get('success', False)}")
                print(f"   Confidence: {validation.get('confidence', 0.0):.2f}")
                print(f"   Reason: {validation.get('reason', 'Unknown')}")
                
                if not validation.get('success', False):
                    print(f"\n⚠️  Stage {i} validation failed - continuing anyway")
                    # Continue rather than fail completely - Windows-Use might have succeeded
                
                stage_results.append({
                    'stage': i,
                    'description': stage.description,
                    'result': stage_result,
                    'validation': validation
                })
                
                print(f"\n✅ Stage {i} completed")
                
            except Exception as e:
                print(f"\n❌ Stage {i} error: {str(e)}")
                return f"Task failed at stage {i} with error: {str(e)}"
        
        # Step 4: Combine results
        print(f"\n{'='*70}")
        print("TASK COMPLETION SUMMARY")
        print(f"{'='*70}")
        
        summary_parts = []
        for stage_result in stage_results:
            validation = stage_result['validation']
            status = "✅ Success" if validation.get('success') else "⚠️  Partial"
            summary_parts.append(
                f"Stage {stage_result['stage']}: {stage_result['description']} - {status}"
            )
        
        final_summary = "\n".join(summary_parts)
        print(f"\n{final_summary}")
        
        # Return combined results
        return f"""Multi-stage task completed:

{final_summary}

Total stages executed: {len(stage_results)}
"""

def main():
    """Main entry point"""
    agent = MultiStageAgent()
    
    print("Multi-Stage Windows Agent (V2)")
    print("Best for complex tasks involving multiple apps or steps")
    print("Example: 'Research iPhone prices and create comparison spreadsheet'")
    
    query = input("\nEnter your task: ")
    
    result = agent.execute(query)
    
    print(f"\n{'='*70}")
    print("FINAL RESULT")
    print(f"{'='*70}")
    print(result)

if __name__ == "__main__":
    main()