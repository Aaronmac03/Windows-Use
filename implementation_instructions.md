# Implementation Instructions for Windows-Use Enhancement

## Pre-Implementation Checklist

1. **Keep `main.py` unchanged** - This is the baseline reference
2. `mainv1_failed.py` - Preserve the failed attempt for reference
3. **Update `repo.md`** after each implementation with results and learnings

---

## Task 1: Implement V1 - Smart Instructions Generator

### What You're Building
A wrapper that uses a cheap model (Qwen 72B) to analyze tasks and generate specific instructions that help an even cheaper model (Gemini Flash Lite) successfully execute Windows automation tasks.

### Implementation Steps

1. **Create new `mainv1.py`** with this exact structure:

```python
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
```

2. **Test with these exact queries** (in order):
   - "Open Notepad and type Hello World"
   - "Open Chrome and go to google.com"
   - "Open Settings and search for display"

3. **Update `repo.md`** with:
   ```markdown
   ## 2024-XX-XX — V1 Smart Instructions
   - **What changed**: Added TaskAnalyzer to generate specific instructions
   - **Files**: Created new mainv1.py (working version)
   - **Models**: Qwen 72B for analysis, Gemini Flash Lite for execution
   - **Result**: [Document success/failure rate from tests]
   - **Cost**: ~$0.004 per task
   - **Next**: V2 multi-stage decomposition
   ```

---

## Task 2: Implement V2 - Multi-Stage Execution

### What You're Building
Break complex tasks into stages, execute each with focused instructions, verify completion before proceeding.

### Create `mainv2.py`:

```python
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class TaskStage:
    """Represents one stage of a multi-stage task"""
    description: str
    instructions: List[str]
    success_criteria: str
    focus_app: str  # Which app this stage focuses on

class TaskDecomposer:
    """Breaks complex tasks into executable stages"""
    
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
        """Break task into stages"""
        
        prompt = f"""Break this Windows task into 1-3 sequential stages.
Each stage should focus on ONE application or ONE clear objective.

Task: {query}

Return JSON with this structure:
{{
  "stages": [
    {{
      "description": "Stage goal",
      "focus_app": "notepad|chrome|settings|explorer|etc",
      "instructions": ["step1", "step2"],
      "success_criteria": "What confirms this stage is done"
    }}
  ]
}}

Stages:"""

        response = self.llm.invoke(prompt)
        return self._parse_stages(response.content)
    
    def _parse_stages(self, content: str) -> List[TaskStage]:
        """Parse stages from response"""
        try:
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            
            data = json.loads(content.strip())
            stages = []
            
            for stage_data in data.get('stages', [])[:3]:  # Max 3 stages
                stages.append(TaskStage(
                    description=stage_data.get('description', ''),
                    instructions=stage_data.get('instructions', [])[:7],
                    success_criteria=stage_data.get('success_criteria', ''),
                    focus_app=stage_data.get('focus_app', 'explorer')
                ))
            
            return stages
        except:
            return []

class MultiStageAgent:
    """Executes tasks in stages with verification"""
    
    def __init__(self):
        self.decomposer = TaskDecomposer()
        self.executor_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0
        )
        
    def execute(self, query: str) -> str:
        """Execute multi-stage task"""
        
        # Decompose into stages
        print(f"Analyzing task: {query}")
        stages = self.decomposer.decompose(query)
        
        if not stages:
            print("Could not decompose task")
            return "Failed to understand task"
        
        print(f"\nTask decomposed into {len(stages)} stages:")
        for i, stage in enumerate(stages, 1):
            print(f"\nStage {i}: {stage.description}")
            print(f"  Focus: {stage.focus_app}")
            print(f"  Success: {stage.success_criteria}")
        
        # Execute each stage
        results = []
        for i, stage in enumerate(stages, 1):
            print(f"\n{'='*50}")
            print(f"Executing Stage {i}: {stage.description}")
            print(f"{'='*50}")
            
            agent = Agent(
                llm=self.executor_llm,
                instructions=stage.instructions,
                browser='chrome',
                use_vision=False,
                max_steps=20  # Lower limit per stage
            )
            
            # Execute stage with its specific goal
            stage_result = agent.invoke(stage.description)
            
            if stage_result.error:
                print(f"❌ Stage {i} failed: {stage_result.error}")
                return f"Failed at stage {i}: {stage_result.error}"
            
            print(f"✅ Stage {i} completed")
            results.append(stage_result.content)
        
        return "\n\n".join(results)

def main():
    agent = MultiStageAgent()
    query = input("Enter your task: ")
    result = agent.execute(query)
    print(f"\n{'='*50}")
    print("FINAL RESULT:")
    print(f"{'='*50}")
    print(result)

if __name__ == "__main__":
    main()
```

---

## Task 3: Implement V3 - Adaptive Model Selection

### What You're Building
Classify task complexity and route to the cheapest capable model.

### Create `mainv3.py`:

```python
import json
import time
from typing import Dict, Tuple
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv
import os

load_dotenv()

class TaskComplexity(Enum):
    SIMPLE = "simple"     # Single app, <5 steps
    MEDIUM = "medium"     # Multi-app or 5-10 steps  
    COMPLEX = "complex"   # Research, complex coordination

class ComplexityClassifier:
    """Classifies task complexity for model selection"""
    
    def __init__(self):
        # Use cheapest model for classification
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash-lite',
            temperature=0.0,
            max_tokens=100
        )
    
    def classify(self, query: str) -> TaskComplexity:
        """Determine task complexity"""
        
        prompt = f"""Classify this Windows task complexity:

SIMPLE: Single app, basic actions (open, type, click)
MEDIUM: Multiple apps or web search
COMPLEX: Research, data analysis, multi-step workflows

Task: {query}

Reply with ONLY one word: SIMPLE, MEDIUM, or COMPLEX"""

        response = self.llm.invoke(prompt)
        text = response.content.strip().upper()
        
        if "COMPLEX" in text:
            return TaskComplexity.COMPLEX
        elif "MEDIUM" in text:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.SIMPLE

class AdaptiveAgent:
    """Selects optimal model based on task complexity"""
    
    # Model configurations by complexity
    MODEL_CONFIGS = {
        TaskComplexity.SIMPLE: {
            "analyzer": "gemini-2.5-flash-lite",  # Cheapest
            "executor": "gemini-2.5-flash-lite",
            "cost_per_1k": 0.001
        },
        TaskComplexity.MEDIUM: {
            "analyzer": "qwen/qwen-2.5-72b-instruct",
            "executor": "gemini-2.5-flash-lite", 
            "cost_per_1k": 0.003
        },
        TaskComplexity.COMPLEX: {
            "analyzer": "qwen/qwen-2.5-72b-instruct",
            "executor": "openai/gpt-oss-120b",  # Strongest
            "cost_per_1k": 0.010
        }
    }
    
    def __init__(self, track_costs=True):
        self.classifier = ComplexityClassifier()
        self.track_costs = track_costs
        self.total_cost = 0.0
        
    def _get_llm(self, model_name: str):
        """Get LLM instance for model name"""
        if model_name == "gemini-2.5-flash-lite":
            return ChatGoogleGenerativeAI(
                model='gemini-2.5-flash-lite',
                temperature=0.0
            )
        else:
            return ChatOpenAI(
                model=model_name,
                temperature=0.0,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                    "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Enhanced")
                }
            )
    
    def _generate_instructions(self, query: str, analyzer_model: str) -> List[str]:
        """Generate task-specific instructions"""
        
        analyzer = self._get_llm(analyzer_model)
        
        prompt = f"""Convert this Windows task into specific steps:

Task: {query}

Return a JSON array of exact instructions:"""

        response = analyzer.invoke(prompt)
        
        try:
            content = response.content
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            return json.loads(content.strip())
        except:
            return []
    
    def execute(self, query: str) -> str:
        """Execute with optimal model selection"""
        
        start_time = time.time()
        
        # Classify complexity
        print(f"Analyzing task: {query}")
        complexity = self.classifier.classify(query)
        config = self.MODEL_CONFIGS[complexity]
        
        print(f"Complexity: {complexity.value.upper()}")
        print(f"Using models:")
        print(f"  Analyzer: {config['analyzer']}")
        print(f"  Executor: {config['executor']}")
        print(f"  Est. cost: ${config['cost_per_1k']:.3f}/1k tokens")
        
        # Generate instructions
        instructions = self._generate_instructions(query, config['analyzer'])
        
        if not instructions:
            return "Failed to analyze task"
        
        print(f"\nGenerated {len(instructions)} instructions")
        
        # Execute
        executor = self._get_llm(config['executor'])
        
        agent = Agent(
            llm=executor,
            instructions=instructions,
            browser='chrome',
            use_vision=False,
            max_steps=40 if complexity == TaskComplexity.COMPLEX else 20
        )
        
        result = agent.invoke(query)
        
        # Track costs
        elapsed = time.time() - start_time
        if self.track_costs:
            # Rough estimate
            est_tokens = len(str(instructions)) + len(query) + len(str(result))
            est_cost = (est_tokens / 1000) * config['cost_per_1k']
            self.total_cost += est_cost
            
            print(f"\n📊 Execution Stats:")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Est. tokens: {est_tokens}")
            print(f"  Est. cost: ${est_cost:.4f}")
            print(f"  Total session cost: ${self.total_cost:.4f}")
        
        return result.content or result.error or "No response"

def main():
    agent = AdaptiveAgent(track_costs=True)
    
    while True:
        query = input("\nEnter task (or 'quit'): ")
        if query.lower() == 'quit':
            break
            
        result = agent.execute(query)
        print(f"\nResult: {result}")
        
    print(f"\n💰 Total session cost: ${agent.total_cost:.4f}")

if __name__ == "__main__":
    main()
```

---

## Testing Protocol

### V1 Tests:
1. "Open Notepad and type Hello World"
2. "Open Chrome and search for Python"
3. "Open Settings and turn on dark mode"

### V2 Tests:
1. "Search for weather and write it in Notepad"
2. "Find Python documentation and bookmark it"

### V3 Tests:
1. Simple: "Open Calculator"
2. Medium: "Open two Notepad windows side by side"  
3. Complex: "Research laptop prices and create a comparison"

---

## Success Criteria

- **V1**: Instructions make the cheap model succeed >70% of the time
- **V2**: Multi-stage tasks complete without breaking
- **V3**: Correctly routes 8/10 tasks to appropriate model tier

---

## Common Pitfalls to Avoid

1. **DON'T modify Windows-Use internals** - Only use its public API
2. **DON'T over-engineer prompts** - Keep instructions simple and direct
3. **DON'T use vision unless necessary** - It's expensive
4. **DON'T generate >10 instructions** - The agent gets confused
5. **DON'T forget to test with actual Windows tasks** - Not just theory

---

## After Each Version

Update `repo.md` with:
- Actual test results
- Cost measurements  
- What worked/failed
- Ideas for improvement