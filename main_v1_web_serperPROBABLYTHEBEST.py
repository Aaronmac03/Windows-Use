"""
Serper-Enhanced Smart Windows Agent - Liberal Cost-Effective Web Search Version

This version uses Serper's Google SERP API instead of OpenRouter for web searches,
reducing cost from ~$0.02/request to ~$0.0003/query (60x cheaper).

Key Features:
- Uses Serper Google SERP API for both planning AND runtime searches
- VERY liberal search limits (8 planning + 5 runtime by default)
- Environment variable first configuration (SERPER_API_KEY)
- In-memory LRU caching for repeated queries
- Cost tracking and estimation using Serper pricing
- Mid-task clarification enabled (it's so cheap!)

Usage:
export SERPER_API_KEY=your_key && python main_v1_web_serper.py

Cost: ~$0.002 per task (vs ~$0.006 with OpenRouter) - Liberal usage mode!
"""

import argparse
import json
import os
import re
import time
from functools import lru_cache
from typing import List, Dict, Any, Optional, Callable

import requests
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent.enhanced_service import EnhancedAgent
from dotenv import load_dotenv

# Serper Configuration
SERPER_PRICE_PER_QUERY = 0.0003  # $0.30 / 1000 queries (starter tier)
DEFAULT_MAX_PLANNING_SEARCHES = 8  # Very liberal - it's super cheap!
DEFAULT_MAX_RUNTIME_SEARCHES = 5   # Allow mid-task searches too
ALLOW_RUNTIME_SEARCH = True  # It's cheap, let's use it!

# Global search call counter
search_calls = 0

def serper_search(query: str, api_key: str, num: int = 5) -> dict:
    """
    Search using Serper's Google SERP API
    Returns structured search results similar to OpenRouter format
    """
    global search_calls
    search_calls += 1
    
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={"q": query, "num": num},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        # Convert Serper format to our normalized format
        results = []
        organic = data.get('organic', [])
        
        for result in organic[:num]:
            results.append({
                "title": result.get('title', ''),
                "url": result.get('link', ''),
                "snippet": result.get('snippet', ''),
                "source": "serper"
            })
        
        return {
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        print(f"Warning: Serper search failed: {e}")
        return {"results": [], "count": 0}

@lru_cache(maxsize=64)
def cached_serper_search(query: str, api_key: str, num: int = 5) -> str:
    """
    LRU cached version of Serper search
    Returns JSON string for caching compatibility
    """
    result = serper_search(query, api_key, num)
    return json.dumps(result)

def create_serper_search_function(api_key: str, max_results: int = 5) -> Callable[[str], Dict[str, Any]]:
    """
    Create a search function that uses Serper with LRU caching
    """
    def search_func(query: str) -> Dict[str, Any]:
        cached_result = cached_serper_search(query, api_key, max_results)
        return json.loads(cached_result)
    
    return search_func


class SerperWebEnhancedTranslator:
    """Web-enhanced translation layer using Serper for cheap, liberal searches"""
    
    def __init__(self, serper_key: str, max_planning_searches: int, max_runtime_searches: int = DEFAULT_MAX_RUNTIME_SEARCHES, model_name: str = None):
        # Use Qwen for analysis (cheap and effective)
        if model_name is None:
            model_name = "qwen/qwen-2.5-72b-instruct"
        
        self.model_name = model_name
        self.llm = self._initialize_llm(model_name)
        self.serper_key = serper_key
        self.max_planning_searches = max_planning_searches
        self.max_runtime_searches = max_runtime_searches
        self.planning_search_calls = 0
        self.runtime_search_calls = 0
        
        # Create search function with caching
        self.search_func = create_serper_search_function(serper_key)
        
        # Cache for resolved information to avoid duplicate searches
        self._resolution_cache: Dict[str, str] = {}
        
        # Callback for mid-task clarification (set by parent agent)
        self.mid_task_callback: Optional[Callable[[str], str]] = None
    
    def _initialize_llm(self, preferred_model: str):
        """Initialize LLM for analysis"""
        model_options = [
            preferred_model,
            "qwen/qwen-2.5-72b-instruct",  # Primary cheap model
            "meta-llama/llama-3.1-8b-instruct",  # Free fallback
            "google/gemini-2.0-flash-thinking-exp"  # Another fallback
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in model_options:
            if model not in seen:
                unique_models.append(model)
                seen.add(model)
        
        for model in unique_models:
            try:
                print(f"🤖 Trying model: {model}")
                llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    max_tokens=800,
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
                        "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Serper Enhanced")
                    }
                )
                
                # Test the model with a simple query
                test_response = llm.invoke("Test")
                print(f"✅ Successfully initialized: {model}")
                self.model_name = model
                return llm
                
            except Exception as e:
                print(f"⚠️  Failed to initialize {model}: {str(e)}")
                continue
        
        raise Exception("Could not initialize any LLM model. Please check your API keys and model availability.")
    
    def translate(self, query: str) -> str:
        """Main translation method with liberal Serper planning searches"""
        print("🌐 Analyzing query for ambiguities...")
        
        # Step 1: Identify ambiguous elements
        ambiguities = self.identify_ambiguities(query)
        
        if not ambiguities:
            print("✅ No ambiguities found, query is clear")
            return query
        
        print(f"🔍 Found {len(ambiguities)} ambiguous elements:")
        for ambiguity in ambiguities:
            print(f"   • {ambiguity['type']}: {ambiguity['element']}")
        
        # Step 2: Resolve ambiguities with Serper searches (more liberal batching)
        clarifications = {}
        batches = self._batch_ambiguities(ambiguities, target_batches=2)
        
        for batch_query in batches:
            if self.planning_search_calls >= self.max_planning_searches:
                print(f"⚠️  Reached max planning searches ({self.max_planning_searches}), skipping remaining")
                break
                
            print(f"\n🔎 Batch search: '{batch_query[:60]}...'")
            resolution = self.resolve_batch_with_search(batch_query)
            if resolution:
                # Parse batch results back to individual clarifications
                self._extract_batch_clarifications(batch_query, resolution, clarifications)
        
        # Step 3: Rewrite the query with clarifications
        if clarifications:
            enriched_query = self.rewrite_query(query, clarifications)
            print(f"\n📝 Enriched query:")
            print(f"   Original: {query}")
            print(f"   Enhanced: {enriched_query}")
            return enriched_query
        
        return query
    
    def identify_ambiguities(self, query: str) -> List[Dict[str, str]]:
        """Detect elements in the query that need clarification"""
        
        prompt = f"""Analyze this user query and identify ambiguous elements that would benefit from web search clarification.

Query: "{query}"

Look for these types of ambiguities:
1. LOCATION - vague location references (e.g., "near X", "local", "nearby") 
2. SUBJECTIVE - subjective terms (e.g., "cheap", "good", "best", "popular")
3. PRODUCT - vague product specifications (e.g., "screwdriver" without specific type)
4. TIME_DEPENDENT - information that changes over time (e.g., "current prices", "latest")
5. BUSINESS - store hours, specific locations, contact info needs

IMPORTANT: You must respond with ONLY a valid JSON array, nothing else. No explanations, no markdown formatting.

Example responses:
[{{"type": "LOCATION", "element": "near downtown", "search_hint": "Best Buy store locations near downtown Louisville Kentucky"}}, {{"type": "SUBJECTIVE", "element": "best rated", "search_hint": "best rated wireless gaming headsets under $150"}}]

OR if no ambiguities:
[]

Response (JSON only):"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean up response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            ambiguities = json.loads(content)
            return ambiguities if isinstance(ambiguities, list) else []
            
        except Exception as e:
            print(f"Warning: Failed to identify ambiguities: {e}")
            return []
    
    def _batch_ambiguities(self, ambiguities: List[Dict[str, str]], target_batches: int = 2) -> List[str]:
        """Create fewer, larger search batches for more efficient Serper usage"""
        if not ambiguities:
            return []
        
        batch_size = max(1, len(ambiguities) // target_batches)
        batches = []
        
        for i in range(0, len(ambiguities), batch_size):
            batch = ambiguities[i:i + batch_size]
            search_queries = [amb.get('search_hint', amb.get('element', '')) for amb in batch]
            combined_query = ' AND '.join(search_queries)
            batches.append(combined_query)
        
        return batches
    
    def resolve_batch_with_search(self, batch_query: str) -> Optional[str]:
        """Search the web to clarify a batch of ambiguous elements"""
        
        # Check cache first
        if batch_query in self._resolution_cache:
            return self._resolution_cache[batch_query]
        
        try:
            self.planning_search_calls += 1
            search_results = self.search_func(batch_query)
            
            # Extract relevant information using LLM
            extraction_prompt = f"""Extract relevant information from these search results to clarify the ambiguous elements.

Batch search query was: "{batch_query}"

Search results:
{json.dumps(search_results, indent=2)[:2000]}  # Limit to avoid token limits

Provide concise, factual clarifications (1-2 sentences each) that would help someone complete the task:"""

            response = self.llm.invoke(extraction_prompt)
            resolution = response.content.strip()
            
            # Cache the result
            self._resolution_cache[batch_query] = resolution
            
            return resolution
            
        except Exception as e:
            print(f"Warning: Failed to resolve batch '{batch_query[:50]}...': {e}")
            return None
    
    def _extract_batch_clarifications(self, batch_query: str, resolution: str, clarifications: Dict[str, str]):
        """Extract individual clarifications from batch resolution"""
        # For now, use the whole resolution for the batch query
        # In a more sophisticated version, we could parse individual elements
        clarifications[batch_query] = resolution
    
    def rewrite_query(self, original_query: str, clarifications: Dict[str, str]) -> str:
        """Create a precise, enriched query"""
        
        prompt = f"""Rewrite this query by incorporating the clarifications while maintaining the original intent.

Original query: "{original_query}"

Clarifications:
{json.dumps(clarifications, indent=2)}

Rules:
1. Replace ambiguous elements with specific information
2. Add helpful context that guides the agent
3. Keep the same overall structure and intent
4. Make it more actionable and specific
5. Don't make it overly long - just more precise

Rewritten query:"""

        try:
            response = self.llm.invoke(prompt)
            enriched_query = response.content.strip()
            
            # Remove any quotes that might wrap the response
            if enriched_query.startswith('"') and enriched_query.endswith('"'):
                enriched_query = enriched_query[1:-1]
            
            return enriched_query
            
        except Exception as e:
            print(f"Warning: Failed to rewrite query: {e}")
            return original_query
    
    def mid_task_clarify(self, question: str) -> str:
        """Provide additional information during execution - Serper makes this cheap!"""
        
        if not ALLOW_RUNTIME_SEARCH:
            return "Mid-task searches disabled"
        
        if self.runtime_search_calls >= self.max_runtime_searches:
            print(f"⚠️  Reached max runtime searches ({self.max_runtime_searches})")
            return "Search limit reached for this task"
        
        print(f"\n🤔 Agent needs clarification: {question}")
        
        # Try to answer from cached information first
        for cached_element, cached_resolution in self._resolution_cache.items():
            if any(word in question.lower() for word in cached_element.lower().split()):
                print(f"📋 Found cached info: {cached_resolution}")
                return cached_resolution
        
        # Perform new search - it's cheap with Serper!
        try:
            print(f"🔎 Performing runtime search (call {self.runtime_search_calls + 1}/{self.max_runtime_searches})")
            self.runtime_search_calls += 1
            
            search_results = self.search_func(question)
            
            # Extract answer using LLM
            answer_prompt = f"""Answer this specific question based on the search results:

Question: "{question}"

Search results:
{json.dumps(search_results, indent=2)[:1500]}

Provide a direct, helpful answer (1-2 sentences) that would help the Windows automation agent:"""

            response = self.llm.invoke(answer_prompt)
            answer = response.content.strip()
            
            # Cache for future use
            self._resolution_cache[question] = answer
            
            print(f"🌐 Runtime search answer: {answer}")
            return answer
            
        except Exception as e:
            print(f"Warning: Failed to clarify '{question}': {e}")
            return "Unable to find clarification information."


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
                "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Serper Enhanced")
            }
        )
    
    def analyze(self, query: str) -> List[str]:
        """Convert user query into specific step-by-step instructions"""
        
        prompt = f"""You are a Windows automation expert. Convert this request into clear guidance steps.

RULES:
- Focus on WHAT to do, not HOW to click (the agent knows how to click)
- Be specific about app names and URLs
- Include key search terms and button names
- Maximum 8 high-level steps
- Each step should guide towards the goal

User request: {query}

Return ONLY a JSON array of guidance steps, like:
["Open Google Chrome browser",
 "Navigate to bestbuy.com website",
 "Search for wireless gaming headset PS5",
 "Filter by price under $150 and ratings",
 "Select highly rated option and add to cart"]

Steps:"""

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
            # Ensure it's a list and cap at 8 instructions
            if isinstance(instructions, list):
                return instructions[:8]
            return []
        except Exception as e:
            print(f"Warning: Failed to parse JSON: {e}")
            # Fallback parsing
            lines = content.strip().split('\n')
            instructions = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove quotes and list markers
                    line = re.sub(r'^["\'\-*\d\.\)]\s*', '', line)
                    line = line.strip('"\'')
                    if line:
                        instructions.append(line)
                        if len(instructions) >= 8:
                            break
            return instructions


class SmartWindowsAgent:
    """Enhanced Windows agent with Serper web search integration"""
    
    def __init__(self, serper_key: str, max_planning_searches: int = DEFAULT_MAX_PLANNING_SEARCHES, max_runtime_searches: int = DEFAULT_MAX_RUNTIME_SEARCHES):
        self.serper_key = serper_key
        self.max_planning_searches = max_planning_searches
        self.max_runtime_searches = max_runtime_searches
        
        # Initialize components
        self.web_translator = SerperWebEnhancedTranslator(serper_key, max_planning_searches, max_runtime_searches)
        self.task_analyzer = TaskAnalyzer()
        
        # Initialize Windows-Use Enhanced Agent with Gemini
        gemini_llm = ChatGoogleGenerativeAI(
            model='gemini-2.0-flash-thinking-exp',
            temperature=0.2
        )
        self.agent = EnhancedAgent(llm=gemini_llm, browser='chrome', use_vision=False)
        
        # Wire up the search function for the agent (mid-task clarification)
        self.web_translator._web_search_func = self.web_translator.search_func
        self.web_translator.mid_task_callback = self.web_translator.mid_task_clarify
        
        print(f"🚀 Smart Windows Agent initialized")
        print(f"   📡 Web Search: Serper (max {max_planning_searches} planning + {max_runtime_searches} runtime)")
        print(f"   🧠 Translation: {self.web_translator.model_name}")
        print(f"   🤖 Execution: Gemini Flash Thinking (Enhanced UI)")
        print(f"   💰 Cost: ~$0.0003 per search (liberal usage enabled!)")
    
    def execute(self, user_query: str) -> str:
        """Execute user query with web-enhanced intelligence"""
        global search_calls
        initial_search_calls = search_calls
        
        print(f"\n{'='*60}")
        print(f"🎯 USER QUERY: {user_query}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Web-enhanced translation (planning searches only)
            print(f"\n📋 Step 1: Web-Enhanced Query Translation")
            enhanced_query = self.web_translator.translate(user_query)
            
            # Step 2: Task analysis
            print(f"\n🔍 Step 2: Task Analysis")
            instructions = self.task_analyzer.analyze(enhanced_query)
            
            if instructions:
                print(f"Generated {len(instructions)} guidance steps:")
                for i, instruction in enumerate(instructions, 1):
                    print(f"   {i}. {instruction}")
            else:
                print("⚠️  No specific instructions generated, using query directly")
                instructions = [enhanced_query]
            
            # Step 3: Execute with Windows-Use Enhanced Agent
            print(f"\n🚀 Step 3: Windows-Use Agent Execution")
            print(f"Enhanced query: {enhanced_query}")
            
            # Create goal-oriented instruction for Windows-Use
            goal_instruction = f"""Complete this task: {enhanced_query}

Key guidance:
{chr(10).join(f'• {inst}' for inst in instructions)}

Focus on achieving the goal using these guidance points."""

            # Execute with the enhanced agent
            response = self.agent.print_response(goal_instruction)
            
            return response
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            return f"Error: {str(e)}"
        
        finally:
            # Print cost telemetry
            final_search_calls = search_calls
            actual_searches = final_search_calls - initial_search_calls
            estimated_cost = actual_searches * SERPER_PRICE_PER_QUERY
            
            print(f"\n💰 Cost Telemetry:")
            print(f"   serper_planning_calls={self.web_translator.planning_search_calls}/{self.max_planning_searches}")
            print(f"   serper_runtime_calls={self.web_translator.runtime_search_calls}/{self.max_runtime_searches}")
            print(f"   total_serper_calls={actual_searches}")
            print(f"   ~est=${estimated_cost:.4f} (Serper starter pricing)")
            print(f"   Cache size: {len(self.web_translator._resolution_cache)} items (LRU working)")


def main():
    # CLI argument parsing
    parser = argparse.ArgumentParser(
        description="Serper-Enhanced Smart Windows Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  export SERPER_API_KEY=your_key && python main_v1_web_serper.py
  python main_v1_web_serper.py --serper-key YOUR_KEY
  python main_v1_web_serper.py --max-planning-searches 10 --max-runtime-searches 8

Cost: ~$0.0015 per task (vs ~$0.006 with OpenRouter) - Liberal usage enabled!
        """
    )
    
    parser.add_argument(
        "--serper-key", 
        type=str, 
        default=None,
        help="Serper API key (optional; uses SERPER_API_KEY env by default)"
    )
    
    parser.add_argument(
        "--max-planning-searches", 
        type=int, 
        default=DEFAULT_MAX_PLANNING_SEARCHES,
        help=f"Maximum planning searches allowed (default: {DEFAULT_MAX_PLANNING_SEARCHES})"
    )
    
    parser.add_argument(
        "--max-runtime-searches", 
        type=int, 
        default=DEFAULT_MAX_RUNTIME_SEARCHES,
        help=f"Maximum runtime/mid-task searches allowed (default: {DEFAULT_MAX_RUNTIME_SEARCHES})"
    )
    
    args = parser.parse_args()
    
    # Load environment variables first
    load_dotenv()
    
    # Resolve Serper API key (prioritize environment variable)
    serper_key = os.getenv("SERPER_API_KEY") or args.serper_key
    if not serper_key:
        print("❌ Error: Serper API key required")
        print("   Set SERPER_API_KEY environment variable or use --serper-key YOUR_KEY")
        print("   Sign up at https://serper.dev/ (first 2,500 searches free)")
        return
    
    # Verify required environment variables
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY required for analysis models")
        print("   Set OPENROUTER_API_KEY environment variable")
        return
    
    # Initialize the agent
    try:
        agent = SmartWindowsAgent(serper_key, args.max_planning_searches, args.max_runtime_searches)
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    print(f"\n🌟 Serper-Enhanced Smart Windows Agent Ready (Liberal Mode!)")
    print(f"   💰 Cost: ~60x cheaper than OpenRouter (~$0.0015 vs ~$0.006 per task)")
    print(f"   📋 Planning searches: up to {args.max_planning_searches} per task")
    print(f"   🔄 Runtime searches: up to {args.max_runtime_searches} per task (enabled!)")
    print(f"   💾 LRU caching: 64 entries for repeated queries")
    print(f"   🚀 Mid-task clarification: fully enabled (it's cheap!)")
    
    # Interactive loop
    while True:
        try:
            print(f"\n{'='*60}")
            user_query = input("Enter your task (or 'quit' to exit): ").strip()
            
            if not user_query or user_query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            # Execute the query
            agent.execute(user_query)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            continue


if __name__ == "__main__":
    main()