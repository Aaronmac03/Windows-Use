# Web-Enhanced Smart Windows Agent Documentation

## Overview

The Web-Enhanced Smart Windows Agent is an advanced translation layer built on top of the existing Windows-Use v1 architecture. It resolves ambiguities in user queries by leveraging web search before task execution, resulting in more precise and actionable instructions for the Windows automation agent.

## Architecture

```
User Query → WebEnhancedTranslator → TaskAnalyzer → SmartWindowsAgent → Windows-Use Agent
```

### Components

1. **WebEnhancedTranslator**: Core component that identifies and resolves query ambiguities
2. **TaskAnalyzer**: Original v1 component for generating high-level instructions (unchanged)
3. **WebEnhancedSmartWindowsAgent**: Orchestrates the enhanced workflow
4. **Integration Layer**: Connects with web search tools and handles callbacks

## Key Features

### 1. Ambiguity Detection
Automatically identifies ambiguous elements in user queries:

- **Location references**: "near X", "local", "nearby"
- **Subjective terms**: "cheap", "best", "good", "popular"
- **Product specifications**: Vague product descriptions
- **Time-dependent info**: "current prices", "latest"
- **Business details**: Store hours, locations, contact info

### 2. Web Search Resolution
Uses web search to clarify ambiguous elements:
- Formats appropriate search queries
- Extracts relevant information from results
- Caches results to avoid duplicate searches
- Handles search errors gracefully

### 3. Query Enhancement
Creates enriched, precise queries:
- Replaces ambiguous terms with specific information
- Adds contextual details for better agent performance
- Maintains original query intent
- Optimizes for Windows-Use agent compatibility

### 4. Mid-Task Clarification
Provides additional information during execution:
- Agent can request clarification during task execution
- Performs on-demand web searches
- Leverages cached information when available
- Returns structured information to guide the agent

## Installation & Setup

### Prerequisites
- Python 3.12+
- Windows-Use package installed
- API keys configured in `.env` file:
  - `OPENROUTER_API_KEY` (for Claude 3 Haiku and Qwen 72B)
  - `GOOGLE_API_KEY` (for Gemini Flash Lite)

### Files Structure
```
c:\Windows-Use\
├── mainv1_web_enhanced.py      # Core web-enhanced agent
├── web_enhanced_production.py  # Production-ready integration
├── demo_web_enhanced.py        # Demo with mock web search
├── test_web_enhanced.py        # Comprehensive test suite
└── WEB_ENHANCED_DOCUMENTATION.md # This documentation
```

## Usage Examples

### Basic Usage

```python
from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent

# Initialize with web search function
def my_web_search(query):
    # Your web search implementation
    return search_results

agent = WebEnhancedSmartWindowsAgent(web_search_func=my_web_search)

# Execute task with automatic ambiguity resolution
query = "Find a cheap screwdriver at Lowe's near Bashford Manor"
result = agent.execute(query)
```

### Production Integration

```python
from web_enhanced_production import ZencoderWebSearchIntegrator

# Initialize with automatic web search integration
integrator = ZencoderWebSearchIntegrator()

# Execute task
result = integrator.execute_task(
    "Open Chrome, go to Lowe's, find a cheap flat head screwdriver, "
    "and add it to my cart for pickup at the store near Bashford Manor"
)
```

### Standalone Translation

```python
from mainv1_web_enhanced import WebEnhancedTranslator

translator = WebEnhancedTranslator()
translator._web_search_func = my_web_search_function

# Translate query with web enhancement
original = "Find a cheap laptop at the local store"
enhanced = translator.translate(original)
```

## Model Configuration

### Translation Layer (WebEnhancedTranslator)
- **Model**: Claude 3 Haiku via OpenRouter
- **Cost**: ~$0.001 per query analysis
- **Purpose**: Ambiguity identification and web search result processing
- **Temperature**: 0.1 (precise, consistent results)

### Task Analysis (TaskAnalyzer)
- **Model**: Qwen 2.5 72B Instruct via OpenRouter
- **Cost**: ~$0.001 per task analysis
- **Purpose**: Convert enhanced queries into step-by-step instructions
- **Temperature**: 0.1 (structured output)

### Execution (SmartWindowsAgent)
- **Model**: Gemini 2.5 Flash Lite
- **Cost**: ~$0.003 per execution
- **Purpose**: Windows automation actions
- **Temperature**: 0.0 (deterministic actions)

**Total Cost**: ~$0.005 per web-enhanced task

## API Reference

### WebEnhancedTranslator

#### Methods

##### `translate(query: str) -> str`
Main translation method that enriches queries with web-resolved ambiguities.

**Parameters:**
- `query`: Original user query

**Returns:**
- Enhanced query with resolved ambiguities

**Example:**
```python
translator = WebEnhancedTranslator()
enhanced = translator.translate("Find a cheap screwdriver near me")
```

##### `identify_ambiguities(query: str) -> List[Dict[str, str]]`
Detects ambiguous elements in queries.

**Returns:**
```python
[
    {
        "type": "SUBJECTIVE",
        "element": "cheap",
        "search_hint": "affordable screwdriver prices"
    }
]
```

##### `resolve_with_search(ambiguity: Dict[str, str]) -> Optional[str]`
Resolves ambiguous elements using web search.

**Parameters:**
- `ambiguity`: Ambiguity dictionary from `identify_ambiguities`

**Returns:**
- Resolved information or None if resolution fails

##### `rewrite_query(original_query: str, clarifications: Dict[str, str]) -> str`
Creates enhanced query with clarifications.

**Parameters:**
- `original_query`: Original user query
- `clarifications`: Dictionary mapping ambiguous elements to clarifications

**Returns:**
- Rewritten, enhanced query

##### `mid_task_clarify(question: str) -> str`
Provides clarification during task execution.

**Parameters:**
- `question`: Specific question from the executing agent

**Returns:**
- Answer based on web search and cached information

### WebEnhancedSmartWindowsAgent

#### Methods

##### `__init__(web_search_func=None)`
Initialize the web-enhanced agent.

**Parameters:**
- `web_search_func`: Function that takes a query string and returns search results

##### `execute(query: str) -> str`
Execute task with web-enhanced translation.

**Parameters:**
- `query`: User query (may contain ambiguities)

**Returns:**
- Execution result or error message

## Testing

### Run Test Suite
```bash
python test_web_enhanced.py
```

### Test Components
- ✅ Ambiguity identification
- ✅ Web search resolution
- ✅ Query rewriting
- ✅ Mid-task clarification
- ✅ End-to-end translation
- ✅ TaskAnalyzer integration

### Demo Mode
```bash
python demo_web_enhanced.py
```

### Production Testing
```bash
python web_enhanced_production.py
```

## Integration with Web Search Tools

### Zencoder Environment
```python
# Automatic integration in Zencoder
from web_enhanced_production import ZencoderWebSearchIntegrator

integrator = ZencoderWebSearchIntegrator()
# Web search is automatically detected and configured
```

### Custom Web Search
```python
def my_web_search(query: str) -> str:
    # Your custom web search implementation
    # Could use SerpAPI, DuckDuckGo, etc.
    return search_results

agent = WebEnhancedSmartWindowsAgent(web_search_func=my_web_search)
```

### SerpAPI Integration Example
```python
import serpapi

def serpapi_search(query: str) -> str:
    search = serpapi.GoogleSearch({
        "q": query,
        "api_key": "your_serpapi_key"
    })
    results = search.get_dict()
    
    # Extract relevant information
    organic_results = results.get("organic_results", [])
    snippets = [result.get("snippet", "") for result in organic_results[:3]]
    
    return "\n".join(snippets)

agent = WebEnhancedSmartWindowsAgent(web_search_func=serpapi_search)
```

## Examples of Query Enhancement

### Shopping Task
**Original:** "Find a cheap screwdriver at the local store"

**Enhanced:** "Find a flat head screwdriver under $3 (Project Source 6-inch at $1.98) at Lowe's Middletown location (2.3 miles from Bashford Manor)"

### Research Task
**Original:** "Get the latest iPhone prices"

**Enhanced:** "Get current iPhone 15 Pro pricing: 128GB ($999), 256GB ($1099), 512GB ($1299) from Apple's official website"

### Location Task
**Original:** "Find the nearby Home Depot"

**Enhanced:** "Find Home Depot at 1000 N Hurstbourne Pkwy, Louisville, KY 40223 (3.2 miles from current location), phone: (502) 339-3300, hours: 6AM-10PM"

## Best Practices

### Query Design
- Use natural language with specific intent
- Include context that helps identify ambiguities
- Mention preferred brands or price ranges when relevant

### Web Search Optimization
- Implement caching to reduce API costs
- Handle search failures gracefully
- Format search queries for maximum relevance

### Error Handling
- Always provide fallback behavior
- Log search failures for debugging
- Validate API responses before processing

### Performance
- Cache frequently resolved ambiguities
- Limit search result processing to avoid token limits
- Use background processing for non-critical searches

## Troubleshooting

### Common Issues

#### "Web search not available"
- Ensure web search function is properly configured
- Check API keys and network connectivity
- Verify integration with Zencoder environment

#### "Failed to identify ambiguities"
- Check Claude 3 Haiku API access
- Verify OpenRouter configuration
- Ensure prompt formatting is correct

#### "No instructions generated"
- Verify Qwen 72B API access
- Check TaskAnalyzer integration
- Ensure enhanced query is well-formatted

#### "Execution failed"
- Verify Gemini Flash Lite configuration
- Check Windows-Use agent setup
- Ensure instructions are actionable

### Debug Mode
Enable verbose logging by setting environment variable:
```bash
export WEB_ENHANCED_DEBUG=1
```

### Log Analysis
Check execution logs for:
- Ambiguity detection results
- Web search queries and responses
- Query enhancement process
- Task execution details

## Future Enhancements

### Planned Features
- [ ] Multi-language query support
- [ ] Learning from user feedback
- [ ] Advanced caching strategies
- [ ] Integration with more web search providers
- [ ] Visual ambiguity detection (screenshots)

### Performance Improvements
- [ ] Parallel ambiguity resolution
- [ ] Smart search query optimization
- [ ] Result relevance scoring
- [ ] Adaptive model selection based on query type

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure API keys in `.env`
4. Run tests: `python test_web_enhanced.py`

### Adding New Ambiguity Types
1. Update `identify_ambiguities` method
2. Add corresponding search hint generation
3. Update test cases
4. Document the new ambiguity type

### Extending Web Search Integration
1. Create new search function wrapper
2. Handle provider-specific response formats
3. Add error handling for the provider
4. Update documentation and examples

## License

This project extends the Windows-Use library and follows the same licensing terms.

## Support

For issues and questions:
1. Check this documentation
2. Run the test suite to verify setup
3. Review the demo examples
4. Check the troubleshooting section

---

**Version**: 1.1  
**Last Updated**: January 2025  
**Compatible with**: Windows-Use v1 architecture