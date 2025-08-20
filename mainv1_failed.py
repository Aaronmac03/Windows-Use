import json
import os
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from windows_use.agent import Agent
from dotenv import load_dotenv

load_dotenv()

class PlannerActorCritic:
    def __init__(self):
        # Model configurations per blueprint
        self.planner_llm = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct",
            temperature=0.2,
            max_tokens=400,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Personal")
            }
        )
        
        self.critic_llm = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct", 
            temperature=0.0,
            max_tokens=200,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Personal")
            }
        )
        
        self.actor_llm = ChatOpenAI(
            model="openai/gpt-oss-120b",
            temperature=0.0,
            max_tokens=800,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Personal")
            }
        )

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text with fallback handling"""
        # Remove code fences
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Try to find JSON object
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to fix common issues like trailing commas
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {}

    def plan(self, user_request: str) -> Dict[str, Any]:
        """Generate plan with objective, steps, and success_probe"""
        prompt = f"""Return JSON ONLY as {{"objective": str, "steps": [str...], "success_probe": str}}.
- 2–7 literal UI steps (buttons/fields/menus)
- success_probe: ONE short phrase that appears on screen when the task is done

User request:
{user_request}"""
        
        response = self.planner_llm.invoke([{"role": "system", "content": "You are a Windows task planner."}, 
                                           {"role": "user", "content": prompt}])
        
        plan = self.extract_json(response.content)
        print(f"PLAN: {json.dumps(plan, indent=2)}")
        return plan

    def act(self, plan: Dict[str, Any]) -> str:
        """Execute plan using Windows-Use agent and return transcript"""
        if not plan or 'objective' not in plan or 'steps' not in plan:
            return "Error: Invalid plan received"
            
        # Build actor prompt - keep it short per blueprint
        steps_text = "\n".join([f"{i+1}) {step}" for i, step in enumerate(plan.get('steps', []))])
        actor_prompt = f"""Perform these Windows actions now. Interact with the UI directly.
Do not explain. Do not output JSON. Take actions.

Goal: {plan.get('objective', '')}
Steps:
{steps_text}
Stop when you see on screen: "{plan.get('success_probe', '')}" """

        # Create Windows-Use agent and get response
        agent = Agent(llm=self.actor_llm, browser='chrome', use_vision=False)
        
        # Use invoke method to get proper response
        try:
            result = agent.invoke(actor_prompt)
            return result.content or result.error or "No response received"
            
        except Exception as e:
            return f"Actor execution error: {str(e)}"

    def critique(self, transcript: str, success_probe: str) -> Dict[str, Any]:
        """Evaluate transcript and determine if task succeeded"""
        prompt = f"""You are a strict evaluator. PASS if the RAW_TRANSCRIPT contains the exact success_probe
(case-insensitive substring ok). If not, FAIL and give one short next UI action.

Return JSON only: {{"verdict":"PASS"|"FAIL","next_action": "<one short step or empty when PASS>"}}

Success probe to find: "{success_probe}"

RAW_TRANSCRIPT:
{transcript}"""

        response = self.critic_llm.invoke([{"role": "user", "content": prompt}])
        critique = self.extract_json(response.content)
        print(f"CRITIC: {json.dumps(critique, indent=2)}")
        return critique

    def run(self, user_request: str) -> str:
        """Main execution loop: Plan -> Act -> Critique (with one retry)"""
        print(f"\n=== Processing: {user_request} ===")
        
        # Step 1: Plan
        plan = self.plan(user_request)
        if not plan:
            return "Failed to generate valid plan"
        
        # Step 2: Act
        transcript = self.act(plan)
        print(f"\nTRANSCRIPT:\n{transcript}\n")
        
        # Step 3: Critique
        success_probe = plan.get('success_probe', '')
        critique = self.critique(transcript, success_probe)
        
        # Step 4: One micro-retry if needed
        if critique.get('verdict') == 'FAIL' and critique.get('next_action'):
            print(f"\nRetrying with: {critique.get('next_action')}")
            retry_transcript = self.act({'objective': critique.get('next_action'), 
                                       'steps': [critique.get('next_action')], 
                                       'success_probe': success_probe})
            print(f"\nRETRY TRANSCRIPT:\n{retry_transcript}\n")
            
            # Final critique
            final_critique = self.critique(retry_transcript, success_probe)
            print(f"FINAL CRITIC: {json.dumps(final_critique, indent=2)}")
            
            return f"Final result: {final_critique.get('verdict', 'UNKNOWN')}"
        
        return f"Result: {critique.get('verdict', 'UNKNOWN')}"

def main():
    pac = PlannerActorCritic()
    query = input("Enter your query: ")
    result = pac.run(query)
    print(f"\n=== Final Result: {result} ===")

if __name__ == "__main__":
    main()