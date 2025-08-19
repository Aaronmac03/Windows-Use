# Windows-Use Project Log

This is the running project log tracking the evolution from baseline main.py to a reliable Windows automation agent.

## Project Status
- **Current Version**: V1
- **Next Step**: Create V2 with vote-of-3 planner and CSV logging

## 2024-12-19 — V1 Summary
- **What changed**: Replaced baseline main.py with mainv1.py with Planner→Actor→Critic outer wrapper
- **Files touched**: mainv1.py (complete rewrite), repo.md (created)
- **Diff summary**:
  - Added PlannerActorCritic class with plan/act/critique methods
  - Integrated OpenRouter via ChatOpenAI for all models (no DeepSeek)  
  - Planner: qwen-2.5-72b-instruct (temp 0.2, max 400 tokens)
  - Critic: same model (temp 0.0, max 200 tokens)
  - Actor: openai/gpt-oss-120b (temp 0.0, max 800 tokens)
  - Added JSON extraction with fallback error handling
  - Implemented one micro-retry logic as specified
- **Why**: Establish outer-loop architecture per blueprint while keeping Windows-Use internals untouched
- **Known limitations**: 
  - Transcript capture using stdout redirection (basic approach)
  - No logging to CSV yet (V2 feature)
  - No secret guard or budget controls (V3 features)
- **Next step**: Implement V2 vote-of-3 planner and CSV logging

## 2024-12-19 — V1 Hotfix Summary  
- **What changed**: Fixed OpenAI authentication error by uncommenting OPENROUTER_API_KEY in .env
- **Files touched**: .env (uncommented API key), .env-example (created per blueprint spec)  
- **Diff summary**:
  - Uncommented OPENROUTER_API_KEY=sk-or-v1-... in .env file
  - Added blueprint-compliant .env-example with OpenRouter configs and V3 placeholders
- **Why**: V1 was failing with 401 auth error because OPENROUTER_API_KEY was commented out
- **Known limitations**: Same as V1 - no CSV logging, no secret guard, basic transcript capture
- **Next step**: Implement V2 vote-of-3 planner and CSV logging

## 2024-12-19 — V1 Hotfix #2 Summary
- **What changed**: Fixed Pydantic validation error by replacing stdout redirection with `agent.invoke()` method
- **Files touched**: mainv1.py (act method modification)
- **Diff summary**:
  - Removed stdout redirection approach using redirect_stdout
  - Replaced `agent.print_response()` with `agent.invoke()` which returns proper `AgentResult`
  - Simplified error handling and response extraction
- **Why**: The agent.print_response() method was not compatible with the outer-loop wrapper. Windows-Use expects structured XML responses from LLM, but our approach was bypassing this.
- **Known limitations**: Same as V1 - no CSV logging, no secret guard, basic transcript capture
- **Next step**: Implement V2 vote-of-3 planner and CSV logging

## 2024-12-19 — V1 Still Not Working
- **What discovered**: mainv1.py still has validation errors despite Hotfix #2
- **Error details**: 
  ```
  Error: 2 validation errors for AgentData
  action.name
    Field required [type=missing, input_value={}, input_type=dict]
  action.params
    Field required [type=missing, input_value={}, input_type=dict]
  ```
- **Test case**: "Open Chrome, go to lowes, and add a cheap flat head screwdriver to my cart. Use the Lowe's near bashford manor and set it for pickup."
- **Observed behavior**: 
  - Initial action fails with validation errors
  - Retry mechanism somehow works and completes task
  - Final critic reports "PASS" despite initial failure
- **Root cause**: The `agent.invoke()` method is still not compatible with our outer-loop wrapper
- **Impact**: Unreliable execution - depends on retry logic to recover from validation failures
- **Next step**: Need V2 implementation or deeper integration fix

## Run Notes
**Command**: `python mainv1.py` 
**Expected success probe**: User prompted for query, visible PLAN JSON printed, CRITIC verdict shown, final transcript displayed
**Actual behavior**: Validation errors on first attempt, recovers through retry mechanism