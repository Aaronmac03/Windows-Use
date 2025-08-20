# Windows-Use Agent Enhancement - **Blueprint**
ADDEDNDUM: 
after beginning implementation of this blueprint, we learned:
Windows-Use is designed to figure out the HOW by itself. When we give it instructions like "Click the Start button in the bottom-left corner", we're overriding its own decision-making, causing conflicts. The agent works better with goals rather than step-by-step instructions.


> **Goal**: Create a highly capable, cost-effective Windows automation agent that leverages cheap models through intelligent task decomposition and validation
> **Core Insight**: Work WITH Windows-Use's XML protocol, not against it. Enhance through better instructions and pre/post processing.

---

## 0) Key Learnings from Failed attempts

* Windows-Use expects XML-formatted agent responses with specific structure
* The Agent class has its own internal state machine (reason→action→answer)
* Trying to wrap the agent's invoke() method breaks its validation
* Windows-Use already handles retries and error recovery internally
* The real opportunity is in INSTRUCTION ENGINEERING, not execution wrapping

---

## 1) Revised Architecture

Instead of Planner→Actor→Critic wrapping execution, we use:

**Pre-Processing** (Task Analysis) → **Enhanced Windows-Use Agent** → **Post-Processing** (Validation)

* **Task Analyzer**: Cheap model that breaks down complex tasks into structured instructions
* **Windows-Use Agent**: Stock agent with dynamically generated, highly specific instructions
* **Result Validator**: Cheap model that verifies task completion from the agent's output

---

## 2) Implementation Strategy

### V1 - **Smart Instructions Generator**

**Purpose**: Prove that better instructions improve success rate with cheap models

**Architecture**:
```
User Query → Task Analyzer (cheap) → Instruction Set → Windows-Use Agent → Output
```

**Implementation**:
```python
# mainv1.py
class SmartAgent:
    def __init__(self):
        self.analyzer = ChatOpenAI(model="qwen/qwen-2.5-72b-instruct", temp=0.1)
        self.executor = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite', temp=0.0)
        
    def analyze_task(self, query):
        # Generate specific, actionable instructions
        return structured_instructions
        
    def execute(self, query):
        instructions = self.analyze_task(query)
        agent = Agent(llm=self.executor, instructions=instructions)
        return agent.invoke(query)
```

**What it does**:
- Takes user query
- Uses cheap model to generate SPECIFIC step-by-step instructions
- Passes these as Windows-Use agent instructions
- Returns result

---

### V2 - **Multi-Stage Decomposition**

**Purpose**: Handle complex multi-app tasks through staged execution

**Architecture**:
```
Query → Decomposer → [Stage1 → Verify] → [Stage2 → Verify] → Combined Result
```

**Implementation approach**:
- Break complex tasks into atomic stages
- Execute each stage with focused instructions
- Verify stage completion before proceeding
- Combine results

**Example**:
"Research iPhone prices and create a comparison spreadsheet"
- Stage 1: Research prices online (browser focus)
- Stage 2: Create spreadsheet with data (Excel focus)

---

### V3 - **Adaptive Model Selection**

**Purpose**: Use the cheapest model that can handle each task type

**Features**:
- Task complexity classifier
- Model routing based on task type
- Cost tracking and optimization
- Fallback to stronger models on failure

**Model Tiers**:
1. **Simple UI tasks** → Gemini Flash Lite (cheapest)
2. **Multi-step browser** → Qwen 72B 
3. **Complex coordination** → GPT-OSS-120B (only when needed)

---

## 3) Specific Implementation for V1

### File: `mainv1.py`

```python
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
```

---

## 4) Why This Approach Works

1. **Works WITH Windows-Use**: We're enhancing its capabilities through better instructions, not fighting its architecture
2. **Leverages Cheap Models**: Task analysis doesn't need expensive models
3. **Maintains Compatibility**: The Windows-Use agent remains unchanged
4. **Incremental Value**: Each version adds clear value without breaking previous work
5. **Observable**: Clear separation of concerns makes debugging easier

---

## 5) Testing Strategy

### Test Cases for V1:

1. **Simple**: "Open Notepad and type 'Hello World'"
   - Should generate 3-4 specific instructions
   - Should complete in <10 steps

2. **Medium**: "Open Chrome and search for Python documentation"
   - Should generate 5-7 specific instructions
   - Should handle browser startup time

3. **Complex**: "Check the weather for tomorrow and write it in Notepad"
   - Should generate 8-10 instructions
   - Should handle multi-app coordination

---

## 6) Cost Optimization Targets

**V1 Baseline** (per task):
- Task Analysis: ~$0.001 (Qwen 72B, 500 tokens)
- Execution: ~$0.003 (Gemini Flash Lite, 2000 tokens)
- Total: ~$0.004 per simple task

**V3 Target** (adaptive):
- Simple tasks: $0.002
- Medium tasks: $0.005
- Complex tasks: $0.015

---

## 7) Migration Path from Failed V1

1. Keep `main.py` as baseline
2. Rename failed `mainv1.py` to `mainv1_failed.py` for reference
3. Implement new `mainv1.py` as specified above
4. Update `repo.md` with learnings and new approach

---

## 8) Environment Variables

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
GOOGLE_API_KEY=...  # For Gemini Flash Lite

# Optional for V2/V3
ENABLE_VISION=false
MAX_STEPS=30
DEFAULT_BROWSER=chrome
```

---

## 9) Success Metrics

- **Reliability**: >80% success rate on standard tasks
- **Cost**: <$0.01 per average task
- **Clarity**: Clear instruction generation visible in logs
- **Compatibility**: Zero modifications to Windows-Use internals

---

## 10) Next Steps After V1

**V2 Ideas**:
- Add result validation with screenshots
- Implement checkpoint/resume for long tasks
- Add task memory for repeated operations

**V3 Ideas**:
- Dynamic model selection based on task complexity
- Cost tracking and optimization
- Parallel execution for independent subtasks