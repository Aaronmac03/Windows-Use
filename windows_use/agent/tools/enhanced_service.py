from windows_use.agent.tools.views import Click, Type, Launch, Scroll, Drag, Move, Shortcut, Key, Wait, Scrape,Done, Clipboard, Shell, Switch, Resize
from windows_use.desktop.service import Desktop
from humancursor import SystemCursor
from markdownify import markdownify
from langchain.tools import tool
from typing import Literal, Dict, List, Optional, Tuple
import uiautomation as uia
import pyperclip as pc
import pyautogui as pg
import requests
import time
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

cursor=SystemCursor()
pg.FAILSAFE=False
pg.PAUSE=0.5  # Reduced pause for faster interactions

class InteractionStrategy(Enum):
    DIRECT_CLICK = "direct_click"
    KEYBOARD_NAV = "keyboard_nav"
    TEXT_BASED = "text_based"
    ELEMENT_SEARCH = "element_search"
    ALTERNATIVE_COORDINATES = "alternative_coordinates"

@dataclass
class ActionResult:
    success: bool
    message: str
    strategy_used: InteractionStrategy
    element_info: Optional[str] = None
    retry_count: int = 0

@dataclass
class InteractionTracker:
    """Tracks interaction attempts and failures for adaptive behavior"""
    location_attempts: Dict[Tuple[int, int], int] = field(default_factory=dict)
    action_history: List[Dict] = field(default_factory=list)
    failed_strategies: Dict[Tuple[int, int], List[InteractionStrategy]] = field(default_factory=dict)
    consecutive_failures: int = 0
    last_successful_strategy: Optional[InteractionStrategy] = None
    
    def record_attempt(self, location: Tuple[int, int], strategy: InteractionStrategy, success: bool):
        """Record an interaction attempt"""
        self.location_attempts[location] = self.location_attempts.get(location, 0) + 1
        
        if not success:
            if location not in self.failed_strategies:
                self.failed_strategies[location] = []
            self.failed_strategies[location].append(strategy)
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
            self.last_successful_strategy = strategy
        
        self.action_history.append({
            'location': location,
            'strategy': strategy,
            'success': success,
            'timestamp': time.time()
        })
        
        # Keep only last 10 actions to prevent memory bloat
        if len(self.action_history) > 10:
            self.action_history = self.action_history[-10:]
    
    def should_try_alternative(self, location: Tuple[int, int]) -> bool:
        """Determine if we should try alternative strategies"""
        return self.location_attempts.get(location, 0) >= 2 or self.consecutive_failures >= 3
    
    def get_available_strategies(self, location: Tuple[int, int]) -> List[InteractionStrategy]:
        """Get strategies that haven't failed for this location"""
        failed = self.failed_strategies.get(location, [])
        all_strategies = list(InteractionStrategy)
        return [s for s in all_strategies if s not in failed]

# Global interaction tracker
interaction_tracker = InteractionTracker()

class AdaptiveUIHandler:
    """Enhanced UI interaction handler with multiple strategies and retry logic"""
    
    @staticmethod
    def validate_click_result(location: Tuple[int, int], desktop: Desktop, expected_change: Optional[str] = None) -> bool:
        """Validate if a click produced expected results"""
        try:
            # Wait a moment for UI to update
            time.sleep(0.5)
            
            # Check if the element under cursor changed or became active
            control = desktop.get_element_under_cursor()
            
            # Basic validation: check if we clicked on something interactive
            interactive_types = ['ButtonControl', 'ComboBoxControl', 'ListItemControl', 'MenuItemControl', 'TabItemControl']
            
            if control.ControlTypeName in interactive_types:
                return True
                
            # For dropdown/combobox scenarios, check if a dropdown opened
            root = uia.GetRootControl()
            dropdowns = root.GetChildren(lambda c: c.ControlType == uia.ControlType.ComboBoxControl or 
                                                   c.ControlType == uia.ControlType.ListControl and c.IsEnabled)
            
            for dropdown in dropdowns:
                if dropdown.BoundingRectangle.width > 0 and dropdown.IsVisible:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Click validation failed: {e}")
            return False
    
    @staticmethod
    def click_with_direct_strategy(location: Tuple[int, int], button: str, clicks: int, desktop: Desktop) -> ActionResult:
        """Original direct click strategy"""
        try:
            x, y = location
            cursor.move_to(location)
            control = desktop.get_element_under_cursor()
            parent = control.GetParentControl()
            
            if parent.Name == "Desktop":
                pg.click(x=x, y=y, button=button, clicks=clicks)
            else:
                pg.mouseDown()
                pg.click(button=button, clicks=clicks)
                pg.mouseUp()
            
            time.sleep(1.0)
            
            # Validate the click worked
            success = AdaptiveUIHandler.validate_click_result(location, desktop)
            
            num_clicks = {1: 'Single', 2: 'Double', 3: 'Triple'}
            message = f'{num_clicks.get(clicks)} {button} clicked on {control.Name} Element with ControlType {control.ControlTypeName} at ({x},{y}).'
            
            return ActionResult(success=success, message=message, strategy_used=InteractionStrategy.DIRECT_CLICK, element_info=f"{control.Name}:{control.ControlTypeName}")
            
        except Exception as e:
            return ActionResult(success=False, message=f"Direct click failed: {e}", strategy_used=InteractionStrategy.DIRECT_CLICK)
    
    @staticmethod
    def click_with_keyboard_nav(location: Tuple[int, int], desktop: Desktop) -> ActionResult:
        """Try keyboard navigation to select element"""
        try:
            x, y = location
            cursor.move_to(location)
            
            # Try Tab navigation to reach the element
            for _ in range(5):  # Try up to 5 tabs
                pg.press('tab')
                time.sleep(0.3)
                current_control = desktop.get_element_under_cursor()
                if abs(current_control.BoundingRectangle.centerX - x) < 50 and abs(current_control.BoundingRectangle.centerY - y) < 50:
                    pg.press('enter')
                    time.sleep(0.5)
                    success = AdaptiveUIHandler.validate_click_result(location, desktop)
                    return ActionResult(success=success, message=f"Keyboard navigation successful to {current_control.Name}", strategy_used=InteractionStrategy.KEYBOARD_NAV)
            
            # Try arrow key navigation for lists/dropdowns
            pg.press('down')
            time.sleep(0.3)
            pg.press('enter')
            success = AdaptiveUIHandler.validate_click_result(location, desktop)
            return ActionResult(success=success, message="Arrow key navigation attempted", strategy_used=InteractionStrategy.KEYBOARD_NAV)
            
        except Exception as e:
            return ActionResult(success=False, message=f"Keyboard navigation failed: {e}", strategy_used=InteractionStrategy.KEYBOARD_NAV)
    
    @staticmethod
    def click_with_element_search(location: Tuple[int, int], desktop: Desktop) -> ActionResult:
        """Search for similar elements near the location and try clicking them"""
        try:
            x, y = location
            
            # Get the root control and search for elements in the area
            root = uia.GetRootControl()
            search_radius = 50
            
            # Find all clickable elements near the target location
            clickable_elements = []
            
            def find_nearby_elements(control):
                try:
                    rect = control.BoundingRectangle
                    if (abs(rect.centerX - x) <= search_radius and 
                        abs(rect.centerY - y) <= search_radius and
                        control.IsEnabled and control.IsVisible):
                        
                        clickable_types = ['ButtonControl', 'ComboBoxControl', 'ListItemControl', 'MenuItemControl']
                        if control.ControlTypeName in clickable_types:
                            clickable_elements.append(control)
                except:
                    pass
                
                # Recurse to children
                for child in control.GetChildren():
                    find_nearby_elements(child)
            
            find_nearby_elements(root)
            
            # Try clicking the most promising element
            for element in clickable_elements:
                try:
                    element.Click()
                    time.sleep(0.5)
                    success = AdaptiveUIHandler.validate_click_result((element.BoundingRectangle.centerX, element.BoundingRectangle.centerY), desktop)
                    if success:
                        return ActionResult(success=True, message=f"Element search successful - clicked {element.Name}", strategy_used=InteractionStrategy.ELEMENT_SEARCH, element_info=f"{element.Name}:{element.ControlTypeName}")
                except:
                    continue
            
            return ActionResult(success=False, message="No clickable elements found nearby", strategy_used=InteractionStrategy.ELEMENT_SEARCH)
            
        except Exception as e:
            return ActionResult(success=False, message=f"Element search failed: {e}", strategy_used=InteractionStrategy.ELEMENT_SEARCH)
    
    @staticmethod
    def click_with_alternative_coordinates(location: Tuple[int, int], button: str, clicks: int, desktop: Desktop) -> ActionResult:
        """Try clicking at slightly different coordinates"""
        try:
            x, y = location
            
            # Try different offsets around the original location
            offsets = [(0, 0), (5, 0), (-5, 0), (0, 5), (0, -5), (10, 0), (-10, 0), (0, 10), (0, -10)]
            
            for dx, dy in offsets:
                try:
                    new_location = (x + dx, y + dy)
                    cursor.move_to(new_location)
                    
                    # Quick validation that we're still on a valid element
                    control = desktop.get_element_under_cursor()
                    if control.ControlTypeName in ['ButtonControl', 'ComboBoxControl', 'ListItemControl', 'MenuItemControl']:
                        pg.click(x=x+dx, y=y+dy, button=button, clicks=clicks)
                        time.sleep(0.5)
                        
                        success = AdaptiveUIHandler.validate_click_result(new_location, desktop)
                        if success:
                            return ActionResult(success=True, message=f"Alternative coordinates successful at ({x+dx},{y+dy})", strategy_used=InteractionStrategy.ALTERNATIVE_COORDINATES)
                except:
                    continue
            
            return ActionResult(success=False, message="All alternative coordinates failed", strategy_used=InteractionStrategy.ALTERNATIVE_COORDINATES)
            
        except Exception as e:
            return ActionResult(success=False, message=f"Alternative coordinates failed: {e}", strategy_used=InteractionStrategy.ALTERNATIVE_COORDINATES)

@tool('Click Tool', args_schema=Click)
def enhanced_click_tool(loc: tuple[int, int], button: Literal['left', 'right', 'middle'] = 'left', clicks: int = 1, desktop: Desktop = None) -> str:
    """Enhanced click tool with adaptive behavior and multiple strategies"""
    global interaction_tracker
    
    # Check if we should try alternative strategies
    should_try_alternative = interaction_tracker.should_try_alternative(loc)
    
    if should_try_alternative:
        logger.info(f"🔄 Attempting alternative strategies for location {loc} (failed {interaction_tracker.location_attempts.get(loc, 0)} times)")
        
        # Get available strategies (excluding those that already failed)
        available_strategies = interaction_tracker.get_available_strategies(loc)
        
        if not available_strategies:
            # If all strategies failed, reset and try direct click one more time
            logger.warning(f"⚠️ All strategies exhausted for {loc}, resetting and trying direct click")
            interaction_tracker.failed_strategies[loc] = []
            available_strategies = [InteractionStrategy.DIRECT_CLICK]
        
        # Try strategies in order of preference
        strategy_order = [
            InteractionStrategy.ELEMENT_SEARCH,
            InteractionStrategy.KEYBOARD_NAV, 
            InteractionStrategy.ALTERNATIVE_COORDINATES,
            InteractionStrategy.DIRECT_CLICK
        ]
        
        for strategy in strategy_order:
            if strategy in available_strategies:
                logger.info(f"🎯 Trying strategy: {strategy.value}")
                
                result = None
                if strategy == InteractionStrategy.DIRECT_CLICK:
                    result = AdaptiveUIHandler.click_with_direct_strategy(loc, button, clicks, desktop)
                elif strategy == InteractionStrategy.KEYBOARD_NAV:
                    result = AdaptiveUIHandler.click_with_keyboard_nav(loc, desktop)
                elif strategy == InteractionStrategy.ELEMENT_SEARCH:
                    result = AdaptiveUIHandler.click_with_element_search(loc, desktop)
                elif strategy == InteractionStrategy.ALTERNATIVE_COORDINATES:
                    result = AdaptiveUIHandler.click_with_alternative_coordinates(loc, button, clicks, desktop)
                
                if result:
                    interaction_tracker.record_attempt(loc, strategy, result.success)
                    
                    if result.success:
                        logger.info(f"✅ Strategy {strategy.value} succeeded!")
                        return f"SUCCESS with {strategy.value}: {result.message}"
                    else:
                        logger.info(f"❌ Strategy {strategy.value} failed: {result.message}")
                        continue
        
        # If we get here, all strategies failed
        interaction_tracker.record_attempt(loc, InteractionStrategy.DIRECT_CLICK, False)
        return f"FAILED: All interaction strategies exhausted for location {loc}. Consider using different coordinates or manual intervention."
    
    else:
        # Use direct click strategy first
        result = AdaptiveUIHandler.click_with_direct_strategy(loc, button, clicks, desktop)
        interaction_tracker.record_attempt(loc, InteractionStrategy.DIRECT_CLICK, result.success)
        
        if result.success:
            return result.message
        else:
            return f"Initial click failed: {result.message}. Will try alternatives on next attempt."

# Re-export all other tools unchanged for compatibility
@tool('Done Tool',args_schema=Done)
def done_tool(answer:str,desktop:Desktop=None):
    '''To indicate that the task is completed'''
    return answer

@tool('Launch Tool',args_schema=Launch)
def launch_tool(name: str,desktop:Desktop=None) -> str:
    'Launch an application present in start menu (e.g., "notepad", "calculator", "chrome")'
    _,status=desktop.launch_app(name)
    pg.sleep(1.25)
    if status!=0:
        return f'Failed to launch {name.title()}.'
    else:
        return f'Launched {name.title()}.'

@tool('Shell Tool',args_schema=Shell)
def shell_tool(command: str,desktop:Desktop=None) -> str:
    'Execute PowerShell commands and return the output with status code'
    response,status=desktop.execute_command(command)
    return f'Status Code: {status}\nResponse: {response}'

@tool('Clipboard Tool',args_schema=Clipboard)
def clipboard_tool(mode: Literal['copy', 'paste'], text: str = None,desktop:Desktop=None)->str:
    'Copy text to clipboard or retrieve current clipboard content. Use "copy" mode with text parameter to copy, "paste" mode to retrieve.'
    if mode == 'copy':
        if text:
            pc.copy(text)  # Copy text to system clipboard
            return f'Copied "{text}" to clipboard'
        else:
            raise ValueError("No text provided to copy")
    elif mode == 'paste':
        clipboard_content = pc.paste()  # Get text from system clipboard
        return f'Clipboard Content: "{clipboard_content}"'
    else:
        raise ValueError('Invalid mode. Use "copy" or "paste".')
    
@tool('Switch Tool',args_schema=Switch)
def switch_tool(name: str,desktop:Desktop=None) -> str:
    'Switch to a specific application window (e.g., "notepad", "calculator", "chrome", etc.) and bring to foreground.'
    response,status=desktop.switch_app(name)
    if status!=0:
        return f'Failed to switch to {name.title()} window.'
    else:
        return f'Switched to {name.title()} window.'
    
@tool("Resize Tool",args_schema=Resize)
def resize_tool(name: str,loc:tuple[int,int]=None,size:tuple[int,int]=None,desktop:Desktop=None) -> str:
    'Resize a specific application window (e.g., "notepad", "calculator", "chrome", etc.) to a specific size and location.'
    response,_=desktop.resize_app(name,loc,size)
    return response

@tool('Type Tool',args_schema=Type)
def type_tool(loc:tuple[int,int],text:str,clear:Literal['true','false']='false',caret_position:Literal['start','idle','end']='idle',press_enter:Literal['true','false']='false',desktop:Desktop=None):
    'Type text into input fields, text areas, or focused elements. Set clear=True to replace existing text, False to append. Click on target element coordinates first and start typing.'
    x,y=loc
    cursor.click_on(loc)
    control=desktop.get_element_under_cursor()
    if caret_position == 'start':
        pg.press('home')
    elif caret_position == 'end':
        pg.press('end')
    else:
        pass
    if clear=='true':
        pg.hotkey('ctrl','a')
        pg.press('backspace')
    pg.typewrite(text,interval=0.1)
    if press_enter=='true':
        pg.press('enter')
    return f'Typed {text} on {control.Name} Element with ControlType {control.ControlTypeName} at ({x},{y}).'

@tool('Scroll Tool',args_schema=Scroll)
def scroll_tool(loc:tuple[int,int]=None,type:Literal['horizontal','vertical']='vertical',direction:Literal['up','down','left','right']='down',wheel_times:int=1,desktop:Desktop=None)->str:
    'Move cursor to a specific location or current location, start scrolling in the specified direction. Use wheel_times to control scroll amount (1 wheel = ~3-5 lines). Essential for navigating lists, web pages, and long content.'
    if loc:
        cursor.move_to(loc)
    match type:
        case 'vertical':
            match direction:
                case 'up':
                    uia.WheelUp(wheel_times)
                case 'down':
                    uia.WheelDown(wheel_times)
                case _:
                    return 'Invalid direction. Use "up" or "down".'
        case 'horizontal':
            match direction:
                case 'left':
                    pg.keyDown('Shift')
                    pg.sleep(0.05)
                    uia.WheelUp(wheel_times)
                    pg.sleep(0.05)
                    pg.keyUp('Shift')
                case 'right':
                    pg.keyDown('Shift')
                    pg.sleep(0.05)
                    uia.WheelDown(wheel_times)
                    pg.sleep(0.05)
                    pg.keyUp('Shift')
                case _:
                    return 'Invalid direction. Use "left" or "right".'
        case _:
            return 'Invalid type. Use "horizontal" or "vertical".'
    return f'Scrolled {type} {direction} by {wheel_times} wheel times.'

@tool('Drag Tool',args_schema=Drag)
def drag_tool(from_loc:tuple[int,int],to_loc:tuple[int,int],desktop:Desktop=None)->str:
    'Drag and drop operation from source coordinates to destination coordinates. Useful for moving files, resizing windows, or drag-and-drop interactions.'
    control=desktop.get_element_under_cursor()
    x1,y1=from_loc
    x2,y2=to_loc
    cursor.drag_and_drop(from_loc,to_loc)
    return f'Dragged the {control.Name} element with ControlType {control.ControlTypeName} from ({x1},{y1}) to ({x2},{y2}).'

@tool('Move Tool',args_schema=Move)
def move_tool(to_loc:tuple[int,int],desktop:Desktop=None)->str:
    'Move mouse cursor to specific coordinates without clicking. Useful for hovering over elements or positioning cursor before other actions.'
    x,y=to_loc
    cursor.move_to(to_loc)
    return f'Moved the mouse pointer to ({x},{y}).'

@tool('Shortcut Tool',args_schema=Shortcut)
def shortcut_tool(shortcut:list[str],desktop:Desktop=None):
    'Execute keyboard shortcuts using key combinations. Pass keys as list (e.g., ["ctrl", "c"] for copy, ["alt", "tab"] for app switching, ["win", "r"] for Run dialog).'
    pg.hotkey(*shortcut)
    return f'Pressed {'+'.join(shortcut)}.'

@tool('Key Tool',args_schema=Key)
def key_tool(key:str='',desktop:Desktop=None)->str:
    'Press individual keyboard keys. Supports special keys like "enter", "escape", "tab", "space", "backspace", "delete", arrow keys ("up", "down", "left", "right"), function keys ("f1"-"f12").'
    pg.press(key)
    return f'Pressed the key {key}.'

@tool('Wait Tool',args_schema=Wait)
def wait_tool(duration:int,desktop:Desktop=None)->str:
    'Pause execution for specified duration in seconds. Useful for waiting for applications to load, animations to complete, or adding delays between actions.'
    pg.sleep(duration)
    return f'Waited for {duration} seconds.'

@tool('Scrape Tool',args_schema=Scrape)
def scrape_tool(url:str,desktop:Desktop=None)->str:
    'Fetch and convert webpage content to markdown format. Provide full URL including protocol (http/https). Returns structured text content suitable for analysis.'
    response=requests.get(url,timeout=10)
    html=response.text
    content=markdownify(html=html)
    return f'Scraped the contents of the entire webpage:\n{content}'