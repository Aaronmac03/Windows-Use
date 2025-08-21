from windows_use.agent.tools.enhanced_service import enhanced_click_tool, type_tool, launch_tool, shell_tool, clipboard_tool, done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool, key_tool, wait_tool, scrape_tool, switch_tool, resize_tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from windows_use.agent.utils import extract_agent_data, image_message
from langchain_core.language_models.chat_models import BaseChatModel
from windows_use.agent.registry.views import ToolResult
from windows_use.agent.registry.service import Registry
from windows_use.agent.prompt.service import Prompt
from live_inspect.watch_cursor import WatchCursor
from langgraph.graph import START,END,StateGraph
from windows_use.agent.views import AgentResult
from windows_use.agent.state import AgentState
from langchain_core.tools import BaseTool
from windows_use.desktop.service import Desktop
from rich.markdown import Markdown
from rich.console import Console
from termcolor import colored
from textwrap import shorten
from typing import Literal, List, Dict, Optional
import logging
from collections import deque
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@dataclass
class ActionPattern:
    """Track patterns in agent actions to detect infinite loops"""
    action_name: str
    params: Dict
    timestamp: float

class LoopDetector:
    """Detects when agent is stuck in repetitive patterns"""
    
    def __init__(self, max_history: int = 10, pattern_threshold: int = 3):
        self.action_history = deque(maxlen=max_history)
        self.pattern_threshold = pattern_threshold
        
    def add_action(self, action_name: str, params: Dict) -> bool:
        """Add action to history and return True if loop detected"""
        pattern = ActionPattern(action_name, params, time.time())
        self.action_history.append(pattern)
        
        # Check for repetitive patterns
        if len(self.action_history) >= self.pattern_threshold:
            # Check if last N actions are identical
            recent_actions = list(self.action_history)[-self.pattern_threshold:]
            
            # Compare actions (ignoring timestamps)
            if all(self._actions_identical(recent_actions[0], action) for action in recent_actions):
                return True
                
            # Check for alternating patterns (A-B-A-B)
            if len(recent_actions) >= 4 and self._detect_alternating_pattern(recent_actions):
                return True
                
        return False
    
    def _actions_identical(self, action1: ActionPattern, action2: ActionPattern) -> bool:
        """Check if two actions are identical (excluding timestamp)"""
        return (action1.action_name == action2.action_name and 
                action1.params == action2.params)
    
    def _detect_alternating_pattern(self, actions: List[ActionPattern]) -> bool:
        """Detect A-B-A-B alternating patterns"""
        if len(actions) < 4:
            return False
            
        # Check if we have A-B-A-B pattern
        return (self._actions_identical(actions[0], actions[2]) and
                self._actions_identical(actions[1], actions[3]) and
                not self._actions_identical(actions[0], actions[1]))
    
    def get_suggested_alternatives(self) -> List[str]:
        """Get suggested alternative actions when loop detected"""
        return [
            "Try a different click location nearby",
            "Use keyboard navigation (Tab, Enter, Arrow keys)",
            "Search for alternative UI elements",
            "Use text-based input methods",
            "Wait for UI to stabilize before retrying",
            "Consider if the task approach needs to be changed"
        ]

class EnhancedAgent:
    '''
    Enhanced Windows Use Agent with adaptive UI interaction and loop detection

    An agent that can interact with GUI elements on Windows with improved error handling,
    retry logic, and infinite loop prevention.

    Args:
        instructions (list[str], optional): Instructions for the agent. Defaults to [].
        browser (Literal['edge', 'chrome', 'firefox'], optional): Browser the agent should use. Defaults to 'edge'.
        additional_tools (list[BaseTool], optional): Additional tools for the agent. Defaults to [].
        llm (BaseChatModel): Language model for the agent. Defaults to None.
        consecutive_failures (int, optional): Maximum number of consecutive failures. Defaults to 5.
        max_steps (int, optional): Maximum number of steps for the agent. Defaults to 100.
        use_vision (bool, optional): Whether to use vision for the agent. Defaults to False.
        loop_detection (bool, optional): Enable infinite loop detection. Defaults to True.
    
    Returns:
        EnhancedAgent
    '''
    def __init__(self, instructions: list[str] = [], additional_tools: list[BaseTool] = [], 
                 browser: Literal['edge','chrome','firefox'] = 'edge', llm: BaseChatModel = None,
                 consecutive_failures: int = 5, max_steps: int = 100, use_vision: bool = False,
                 loop_detection: bool = True):
        self.name = 'Enhanced Windows Use'
        self.description = 'An enhanced agent with adaptive UI interaction and loop detection'
        
        # Use enhanced click tool instead of regular click tool
        self.registry = Registry([
            enhanced_click_tool, type_tool, launch_tool, shell_tool, clipboard_tool,
            done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool,
            key_tool, wait_tool, scrape_tool, switch_tool, resize_tool
        ] + additional_tools)
        
        self.instructions = instructions
        self.browser = browser
        self.max_steps = max_steps
        self.consecutive_failures = consecutive_failures
        self.desktop = Desktop()
        self.watch_cursor = WatchCursor()
        self.console = Console()
        self.use_vision = use_vision
        self.llm = llm
        self.loop_detection = loop_detection
        self.loop_detector = LoopDetector() if loop_detection else None
        self.current_consecutive_failures = 0
        self.graph = self.create_graph()

    def reason(self, state: AgentState):
        steps = state.get('steps')
        max_steps = state.get('max_steps')
        language = self.desktop.get_default_language()
        tools_prompt = self.registry.get_tools_prompt()
        
        # Enhanced system prompt with loop detection guidance
        system_message_content = Prompt.system_prompt(
            browser=self.browser, 
            language=language, 
            instructions=self.instructions + [
                "IMPORTANT: If previous actions failed repeatedly, try different approaches:",
                "- Use keyboard navigation instead of clicking",
                "- Look for alternative UI elements",
                "- Try different coordinates or interaction methods",
                "- Consider if the current approach is fundamentally flawed"
            ],
            tools_prompt=tools_prompt, 
            max_steps=max_steps
        )
        
        messages = [SystemMessage(content=system_message_content)] + state.get('messages')
        message = self.llm.invoke(messages)
        logger.info(f"Iteration: {steps}")
        
        agent_data = extract_agent_data(message=message)
        logger.info(colored(f"📝: Evaluate: {agent_data.evaluate}", color='yellow', attrs=['bold']))
        logger.info(colored(f"📒: Memory: {agent_data.memory}", color='light_green', attrs=['bold']))
        logger.info(colored(f"📚: Plan: {agent_data.plan}", color='light_blue', attrs=['bold']))
        logger.info(colored(f"💭: Thought: {agent_data.thought}", color='light_magenta', attrs=['bold']))
        
        last_message = state.get('messages').pop()
        if isinstance(last_message, HumanMessage):
            message = HumanMessage(content=Prompt.previous_observation_prompt(
                steps=steps, 
                max_steps=max_steps, 
                observation=state.get('previous_observation')
            ))
            return {**state, 'agent_data': agent_data, 'messages': [message], 'steps': steps + 1}

    def action(self, state: AgentState):
        steps = state.get('steps')
        max_steps = state.get('max_steps')
        agent_data = state.get('agent_data')
        name = agent_data.action.name
        params = agent_data.action.params
        
        # Check for infinite loops before executing action
        if self.loop_detection and self.loop_detector:
            loop_detected = self.loop_detector.add_action(name, params)
            
            if loop_detected:
                logger.warning(colored("🔄 LOOP DETECTED: Agent is repeating the same actions!", color='red', attrs=['bold']))
                alternatives = self.loop_detector.get_suggested_alternatives()
                error_message = f"Infinite loop detected. Tried {name} with same parameters repeatedly. Suggested alternatives: {'; '.join(alternatives)}"
                
                # Force the agent to think of alternatives
                human_message = HumanMessage(content=f"CRITICAL: {error_message}. You must try a completely different approach now.")
                return {**state, 'agent_data': None, 'messages': [human_message], 'previous_observation': error_message}
        
        ai_message = AIMessage(content=Prompt.action_prompt(agent_data=agent_data))
        logger.info(colored(f"🔧: Action: {name}({', '.join(f'{k}={v}' for k, v in params.items())})", color='blue', attrs=['bold']))
        
        # Execute the tool with enhanced error handling
        try:
            tool_result = self.registry.execute(tool_name=name, desktop=self.desktop, **params)
            
            # Check for consecutive failures
            if not tool_result.is_success:
                self.current_consecutive_failures += 1
                logger.warning(colored(f"⚠️  Action failed ({self.current_consecutive_failures}/{self.consecutive_failures})", color='yellow', attrs=['bold']))
            else:
                self.current_consecutive_failures = 0
            
            # If we hit consecutive failure limit, provide guidance
            if self.current_consecutive_failures >= self.consecutive_failures:
                logger.error(colored(f"❌ Too many consecutive failures ({self.consecutive_failures}). Suggesting alternative approach.", color='red', attrs=['bold']))
                enhanced_observation = f"FAILURE LIMIT REACHED: {tool_result.error if not tool_result.is_success else tool_result.content}. You must try a fundamentally different approach - consider keyboard navigation, alternative UI elements, or different coordinates."
            else:
                enhanced_observation = tool_result.content if tool_result.is_success else tool_result.error
                
        except Exception as e:
            self.current_consecutive_failures += 1
            tool_result = ToolResult(is_success=False, content="", error=f"Tool execution failed: {e}")
            enhanced_observation = f"Tool execution error: {e}. Try alternative approaches."
        
        observation = enhanced_observation
        logger.info(colored(f"🔭: Observation: {shorten(observation, 500, placeholder='...')}", color='green', attrs=['bold']))
        
        desktop_state = self.desktop.get_state(use_vision=self.use_vision)
        prompt = Prompt.observation_prompt(
            query=state.get('input'), 
            steps=steps, 
            max_steps=max_steps, 
            tool_result=tool_result, 
            desktop_state=desktop_state
        )
        
        human_message = (image_message(prompt=prompt, image=desktop_state.screenshot) 
                        if self.use_vision and desktop_state.screenshot 
                        else HumanMessage(content=prompt))
        
        return {**state, 'agent_data': None, 'messages': [ai_message, human_message], 'previous_observation': observation}

    def answer(self, state: AgentState):
        agent_data = state.get('agent_data')
        name = agent_data.action.name
        params = agent_data.action.params
        tool_result = self.registry.execute(tool_name=name, desktop=None, **params)
        ai_message = AIMessage(content=Prompt.answer_prompt(agent_data=agent_data, tool_result=tool_result))
        logger.info(colored(f"📜: Final Answer: {tool_result.content}", color='cyan', attrs=['bold']))
        return {**state, 'agent_data': None, 'messages': [ai_message], 'previous_observation': None, 'output': tool_result.content}

    def main_controller(self, state: AgentState):
        if state.get('steps') < state.get('max_steps'):
            agent_data = state.get('agent_data')
            action_name = agent_data.action.name
            if action_name != 'Done Tool':
                return 'action'
        return 'answer'

    def create_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node('reason', self.reason)
        graph.add_node('action', self.action)
        graph.add_node('answer', self.answer)

        graph.add_edge(START, 'reason')
        graph.add_conditional_edges('reason', self.main_controller)
        graph.add_edge('action', 'reason')
        graph.add_edge('answer', END)

        return graph.compile(debug=False)

    def invoke(self, query: str) -> AgentResult:
        steps = 1
        max_steps = self.max_steps
        desktop_state = self.desktop.get_state(use_vision=self.use_vision)
        prompt = Prompt.observation_prompt(
            query=query, 
            steps=steps, 
            max_steps=max_steps,
            tool_result=ToolResult(is_success=True, content="No Action Taken"), 
            desktop_state=desktop_state
        )
        
        human_message = (image_message(prompt=prompt, image=desktop_state.screenshot) 
                        if self.use_vision and desktop_state.screenshot 
                        else HumanMessage(content=prompt))
        
        messages = [human_message]
        state = {
            'input': query,
            'steps': steps,
            'max_steps': max_steps,
            'output': '',
            'error': '',
            'consecutive_failures': 0,
            'agent_data': None,
            'messages': messages,
            'previous_observation': None
        }
        
        try:
            with self.watch_cursor:
                # Increased recursion limit with better error handling
                response = self.graph.invoke(state, config={'recursion_limit': max_steps + 20})
        except Exception as error:
            error_msg = str(error)
            if "Recursion limit" in error_msg:
                error_msg = f"Task complexity exceeded limits. The agent may have encountered challenging UI elements. Original error: {error_msg}"
            
            response = {
                'output': None,
                'error': f"Error: {error_msg}"
            }
            
        return AgentResult(content=response['output'], error=response['error'])

    def print_response(self, query: str):
        response = self.invoke(query)
        self.console.print(Markdown(response.content or response.error))

# For backward compatibility, create an alias
Agent = EnhancedAgent