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
class TaskStage:
    """Represents one stage of a multi-stage task"""
    goal: str                    # Simple goal statement for Windows-Use
    description: str             # Human-readable description
    success_indicator: str       # What to look for to confirm success
    focus_app: str              # Primary app this stage works with
    context_from_previous: str = ""  # Context carried from previous stages

@dataclass
class StageResult:
    """Result of executing a stage"""
    stage_num: int
    description: str
    goal: str
    execution_result: str
    validation: Dict[str, any]
    success: bool
    context_for_next: str = ""  # Context to pass to next stage

class TaskDecomposer:
    """Breaks complex tasks into executable goal-oriented stages"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct",
            temperature=0.1,
            max_tokens=800,
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

CRITICAL RULES for Windows-Use Agent:
- Each stage = ONE clear, achievable goal
- Focus on WHAT to achieve, not HOW to do it
- Keep goals simple and atomic
- Windows-Use figuring out the implementation details
- Each stage should build logically on previous stages
- Include clear success indicators

Task: {query}

Return JSON with this structure:
{{
  "stages": [
    {{
      "goal": "Clear goal for Windows-Use agent - focus on outcome, not process",
      "description": "Human-readable explanation of this stage", 
      "success_indicator": "Specific, observable outcome that confirms success",
      "focus_app": "primary app name (chrome/notepad/settings/explorer/etc)"
    }}
  ]
}}

Example for "Research iPhone prices and create comparison spreadsheet":
{{
  "stages": [
    {{
      "goal": "Find current iPhone 15 pricing information online",
      "description": "Research iPhone 15 prices from retailer websites",
      "success_indicator": "Browser showing iPhone 15 prices from at least one retailer",
      "focus_app": "chrome"
    }},
    {{
      "goal": "Create a spreadsheet with iPhone price comparison data",  
      "description": "Open Excel and input the price information found online",
      "success_indicator": "Excel spreadsheet open with iPhone price data entered",
      "focus_app": "excel"
    }}
  ]
}}

IMPORTANT: Keep goals outcome-focused, not process-focused. Let Windows-Use figure out HOW.

Stages:"""

        try:
            response = self.llm.invoke(prompt)
            return self._parse_stages(response.content)
        except Exception as e:
            print(f"❌ Failed to decompose task: {e}")
            return []
    
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
    """Validates stage completion using intelligent analysis"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0,
            max_tokens=300
        )
    
    def validate_stage(self, stage: TaskStage, execution_result: str, previous_context: str = "") -> Dict[str, any]:
        """Check if stage was completed successfully"""
        
        prompt = f"""Analyze if this stage completed successfully. Be practical and flexible - focus on whether the GOAL was achieved, even if the exact method differed.

STAGE GOAL: {stage.goal}
SUCCESS INDICATOR: {stage.success_indicator}
PREVIOUS CONTEXT: {previous_context}

EXECUTION RESULT:
{execution_result[:2500]}  

Return JSON only:
{{
  "success": true/false,
  "confidence": 0.0-1.0,
  "reason": "brief explanation of why success/failure",
  "context_for_next": "key information that next stage might need"
}}

Be PRACTICAL:
- If the goal was substantially achieved, mark as success
- Don't fail on minor deviations from the exact success indicator
- Consider partial success as success if the core objective was met
- Focus on functional outcomes, not perfect process adherence"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            result = json.loads(content)
            # Ensure all required fields are present
            return {
                "success": result.get("success", False),
                "confidence": result.get("confidence", 0.0),
                "reason": result.get("reason", "No reason provided"),
                "context_for_next": result.get("context_for_next", "")
            }
        except Exception as e:
            print(f"⚠️ Validation parsing failed: {e}")
            # Default to conservative success if execution result looks positive
            execution_lower = execution_result.lower()
            likely_success = any(word in execution_lower for word in ['success', 'completed', 'done', 'finished', 'opened', 'created'])
            
            return {
                "success": likely_success,
                "confidence": 0.5 if likely_success else 0.0,
                "reason": "Validation parsing failed - inferred from execution result",
                "context_for_next": ""
            }

class EnhancedMultiStageAgent:
    """Enhanced multi-stage execution with better state management and error handling"""
    
    def __init__(self):
        self.decomposer = TaskDecomposer()
        self.validator = StageValidator()
        # Use Gemini Flash Lite for execution - better Windows-Use compatibility
        self.executor_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0
        )
        
    def execute(self, query: str) -> str:
        """Execute multi-stage task with enhanced error handling"""
        
        print("="*80)
        print(f"ENHANCED MULTI-STAGE TASK: {query}")
        print("="*80)
        
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
        
        # Step 2: Execute stages with context preservation
        stage_results: List[StageResult] = []
        accumulated_context = ""
        
        for i, stage in enumerate(stages, 1):
            print(f"\n{'='*80}")
            print(f"EXECUTING STAGE {i}/{len(stages)}")
            print(f"{'='*80}")
            print(f"Goal: {stage.goal}")
            print(f"App Focus: {stage.focus_app}")
            
            if accumulated_context:
                print(f"Context from previous stages: {accumulated_context[:200]}...")
            
            # Add context to stage goal if we have it
            enhanced_goal = stage.goal
            if accumulated_context:
                enhanced_goal = f"{stage.goal}\n\nContext from previous stages: {accumulated_context}"
            
            # Execute stage with retry logic
            stage_result = self._execute_stage_with_retry(i, stage, enhanced_goal)
            
            if not stage_result.success:
                print(f"\n❌ Stage {i} failed - stopping execution")
                return f"Task failed at stage {i}: {stage_result.validation.get('reason', 'Unknown error')}"
            
            # Update accumulated context
            if stage_result.context_for_next:
                accumulated_context += f" Stage {i}: {stage_result.context_for_next}."
            
            stage_results.append(stage_result)
            print(f"\n✅ Stage {i} completed successfully")
        
        # Step 3: Generate final summary
        return self._generate_final_summary(stage_results, query)
    
    def _execute_stage_with_retry(self, stage_num: int, stage: TaskStage, enhanced_goal: str, max_retries: int = 1) -> StageResult:
        """Execute a single stage with retry logic"""
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"\n🔄 Retry attempt {attempt} for stage {stage_num}")
                time.sleep(2)  # Brief pause between retries
            
            try:
                # Execute stage with Windows-Use
                print(f"\n🤖 Executing with Windows-Use...")
                agent = Agent(
                    llm=self.executor_llm,
                    browser='chrome',
                    use_vision=False,
                    max_steps=30  # Increased step limit
                )
                
                result = agent.invoke(enhanced_goal)
                
                if result.error:
                    print(f"\n⚠️ Stage {stage_num} execution error: {result.error}")
                    if attempt < max_retries:
                        continue
                    # On final attempt, treat error as failure
                    return StageResult(
                        stage_num=stage_num,
                        description=stage.description,
                        goal=stage.goal,
                        execution_result=f"Error: {result.error}",
                        validation={"success": False, "confidence": 0.0, "reason": f"Execution error: {result.error}", "context_for_next": ""},
                        success=False
                    )
                
                stage_result_text = result.content or "Stage completed"
                print(f"\n📄 Stage {stage_num} result preview:")
                print(f"   {stage_result_text[:250]}{'...' if len(stage_result_text) > 250 else ''}")
                
                # Validate stage completion
                print(f"\n🔍 Validating stage {stage_num} completion...")
                validation = self.validator.validate_stage(stage, stage_result_text)
                
                print(f"   Success: {validation.get('success', False)}")
                print(f"   Confidence: {validation.get('confidence', 0.0):.2f}")
                print(f"   Reason: {validation.get('reason', 'Unknown')}")
                
                # Create stage result
                stage_result = StageResult(
                    stage_num=stage_num,
                    description=stage.description,
                    goal=stage.goal,
                    execution_result=stage_result_text,
                    validation=validation,
                    success=validation.get('success', False),
                    context_for_next=validation.get('context_for_next', '')
                )
                
                # If successful or final attempt, return result
                if stage_result.success or attempt >= max_retries:
                    return stage_result
                
                print(f"\n⚠️ Stage {stage_num} validation failed, retrying...")
                
            except Exception as e:
                print(f"\n❌ Stage {stage_num} exception: {str(e)}")
                if attempt >= max_retries:
                    return StageResult(
                        stage_num=stage_num,
                        description=stage.description,
                        goal=stage.goal,
                        execution_result=f"Exception: {str(e)}",
                        validation={"success": False, "confidence": 0.0, "reason": f"Exception: {str(e)}", "context_for_next": ""},
                        success=False
                    )
        
        # Should never reach here, but just in case
        return StageResult(
            stage_num=stage_num,
            description=stage.description,
            goal=stage.goal,
            execution_result="Unknown error",
            validation={"success": False, "confidence": 0.0, "reason": "Unknown error", "context_for_next": ""},
            success=False
        )
    
    def _generate_final_summary(self, stage_results: List[StageResult], original_query: str) -> str:
        """Generate a comprehensive final summary"""
        
        print(f"\n{'='*80}")
        print("TASK COMPLETION SUMMARY")
        print(f"{'='*80}")
        
        successful_stages = sum(1 for result in stage_results if result.success)
        total_stages = len(stage_results)
        
        summary_parts = []
        detailed_results = []
        
        for result in stage_results:
            validation = result.validation
            status = "✅ Success" if result.success else "❌ Failed"
            confidence = validation.get('confidence', 0.0)
            
            summary_parts.append(
                f"Stage {result.stage_num}: {result.description} - {status} (confidence: {confidence:.2f})"
            )
            
            detailed_results.append(f"""
Stage {result.stage_num}: {result.description}
Goal: {result.goal}
Result: {result.execution_result[:300]}{'...' if len(result.execution_result) > 300 else ''}
Status: {status}
Reason: {validation.get('reason', 'N/A')}
""")
        
        final_summary = "\n".join(summary_parts)
        print(f"\n{final_summary}")
        
        # Calculate overall success
        success_rate = successful_stages / total_stages
        overall_status = "✅ COMPLETED" if success_rate >= 0.8 else "⚠️ PARTIALLY COMPLETED" if success_rate >= 0.5 else "❌ FAILED"
        
        print(f"\nOverall Status: {overall_status} ({successful_stages}/{total_stages} stages successful)")
        
        return f"""Enhanced Multi-stage Task: {original_query}

{overall_status} - {successful_stages}/{total_stages} stages completed

STAGE SUMMARY:
{final_summary}

SUCCESS RATE: {success_rate:.1%}

DETAILED RESULTS:
{''.join(detailed_results)}
"""

def main():
    """Main entry point"""
    agent = EnhancedMultiStageAgent()
    
    print("Enhanced Multi-Stage Windows Agent (V2.1)")
    print("Improved error handling, state management, and validation")
    print("Models: Qwen 72B (decomposition), Gemini Flash Lite (execution), Gemini Flash Lite (validation)")
    print("Best for complex tasks involving multiple apps or steps")
    print("Example: 'Research iPhone prices and create comparison spreadsheet'")
    
    query = input("\nEnter your task: ")
    
    result = agent.execute(query)
    
    print(f"\n{'='*80}")
    print("FINAL RESULT")
    print(f"{'='*80}")
    print(result)

if __name__ == "__main__":
    main()