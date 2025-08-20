---
description: Repository Information Overview
alwaysApply: true
---

# Windows-Use Information

## Summary
Windows-Use is a powerful automation agent that interacts directly with Windows at the GUI layer. It enables AI agents to perform tasks such as opening apps, clicking buttons, typing, executing shell commands, and capturing UI state without relying on traditional computer vision models.

## Structure
- **windows_use/**: Main package directory
  - **agent/**: Core agent implementation with tools, registry, and prompt handling
  - **desktop/**: Desktop interaction functionality
  - **tree/**: UI element tree navigation and manipulation
- **tests/**: Test directory with unit tests mirroring the main package structure
- **static/**: Contains screenshots and images for documentation
- **main.py**: Example entry point for running the agent

## Language & Runtime
**Language**: Python
**Version**: 3.13 (requires Python 3.12+)
**Build System**: Hatchling
**Package Manager**: UV/pip

## Dependencies
**Main Dependencies**:
- langchain (>=0.3.25)
- langchain-community (>=0.3.25)
- langchain-google-genai (>=2.1.5)
- langchain-groq (>=0.3.4)
- langchain-ollama (>=0.3.3)
- langchain-openai (>=0.3.27)
- langgraph (>=0.6.4)
- pyautogui (>=0.9.54)
- pydantic (>=2.11.7)
- uiautomation (>=2.0.28)

**Development Dependencies**:
- pytest (>=8.4.1)
- ruff (>=0.12.1)

## Build & Installation
```bash
# Install using UV (recommended)
uv pip install windows-use

# Or with pip
pip install windows-use

# For development installation
uv pip install -e ".[dev]"
```

## Testing
**Framework**: pytest
**Test Location**: tests/unit/
**Naming Convention**: test_*.py
**Run Command**:
```bash
pytest tests/
```

## Usage
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite', temperature=0.2)

# Create agent
agent = Agent(llm=llm, browser='chrome', use_vision=False)

# Run agent with user query
query = input("Enter your query: ")
agent.print_response(query)
```

## Implementation History

### 2025-01-11 — V1 Smart Instructions Generator
- **What changed**: Added TaskAnalyzer to generate specific instructions using Qwen 72B, feeding into Windows-Use agent with Gemini Flash Lite
- **Files**: Created new mainv1.py (working version), test_v1.py for validation
- **Models**: Qwen 72B for analysis (~$0.001), Gemini Flash Lite for execution (~$0.003)
- **Result**: Successfully generated clear, specific instructions for all test cases:
  - "Open Notepad and type Hello World" → 6 precise instructions
  - "Open Chrome and go to google.com" → 7 step-by-step actions
  - "Open Settings and search for display" → 7 specific UI steps
- **Cost**: ~$0.004 per task
- **Key Learning**: Windows-Use works better with goals rather than detailed step-by-step instructions. Revised approach focuses on WHAT to do, not HOW to click.

### 2025-01-11 — V2 Multi-Stage Execution [IN PROGRESS - NOT YET SUCCESSFUL]
- **What changed**: Attempting to add MultiStageAgent that breaks complex tasks into goal-oriented stages, each executed independently
- **Files**: mainv2.py (in development), test_v2.py for validation (planned)
- **Models**: Qwen 72B for task decomposition (~$0.001), Gemini Flash Lite for stage execution (~$0.003 per stage)
- **Architecture**: Task Decomposer → Stage Executor → Stage Validator → Combined Results
- **Current Challenges**:
  - Stage coordination complexity higher than anticipated
  - Difficulty in programmatic validation of stage completion
  - Balancing goal-oriented vs step-by-step instructions per stage
  - State management between stages needs refinement
- **Key Learnings So Far**:
  - Windows-Use works best with atomic, focused goals per stage
  - Complex multi-step coordination within a single stage causes conflicts
  - Each stage requires clear, verifiable success criteria
  - Stage transitions need more sophisticated error handling
- **Status**: Implementation in progress, requires further refinement before success

### 2025-01-11 — V2.1 Enhanced Multi-Stage Execution [IMPLEMENTATION COMPLETE]
- **What changed**: Created enhanced multi-stage agent addressing V2 challenges with improved error handling, state management, and validation
- **Files**: mainv21.py (enhanced implementation), test_v21.py for validation
- **Models**: Qwen 72B for task decomposition (~$0.001), Gemini Flash Lite for execution (~$0.003 per stage), Gemini Flash Lite for validation (~$0.001)
- **Architecture**: Enhanced Task Decomposer → Stage Executor with Retry → Intelligent Validator → State-Aware Results
- **Key Improvements**:
  - Better Windows COM error handling and recovery
  - Context preservation and state management between stages
  - More intelligent and flexible validation (practical vs strict)
  - Retry mechanisms for failed stages with exponential backoff
  - Enhanced stage goal construction with accumulated context
  - Improved logging and debugging information
- **Technical Enhancements**:
  - StageResult dataclass for better result tracking
  - Accumulated context passing between stages
  - Fallback validation when JSON parsing fails
  - Enhanced error handling with try/catch and graceful degradation
  - Success rate calculation and overall task status
- **Model Compatibility Note**: GPT OSS 120B attempted but incompatible with Windows-Use action format. Gemini Flash Lite provides better compatibility with Windows-Use's expected XML/structured response format.
- **Status**: Implementation complete, ready for testing
- **Next**: Test V2.1 extensively, then proceed to V3 adaptive model selection
