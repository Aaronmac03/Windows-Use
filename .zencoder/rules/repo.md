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

### 2025-01-11 — V2 Multi-Stage Execution
- **What changed**: Added MultiStageAgent that breaks complex tasks into goal-oriented stages, each executed independently
- **Files**: Created mainv2.py, test_v2.py for validation
- **Models**: Qwen 72B for task decomposition (~$0.001), Gemini Flash Lite for stage execution (~$0.003 per stage), Gemini Flash Lite for validation (~$0.001)
- **Architecture**: Task Decomposer → Stage Executor → Stage Validator → Combined Results
- **Result**: Successfully decomposes complex tasks into logical stages:
  - "Open Notepad and type Hello World" → 2 stages (Open → Type)
  - "Research iPhone prices and create comparison spreadsheet" → 3 stages (Research → Collect → Spreadsheet)  
  - "Check weather for tomorrow and write it in a text file" → 4 stages (Weather → Open file → Write → Save)
  - "Open Settings and change display brightness to 50%" → 3 stages (Open Settings → Navigate → Adjust)
- **Key Innovation**: Each stage is a simple goal statement that Windows-Use can accomplish independently
- **Cost**: ~$0.005-0.015 per complex task (depends on number of stages)
- **Next**: V3 adaptive model selection based on task complexity
