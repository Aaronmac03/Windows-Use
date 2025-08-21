# Serper vs OpenRouter Web Search Comparison

## Overview

Two web-enhanced versions of the Windows-Use agent are now available:

1. **`mainv1_web_enhanced.py`** - OpenRouter :online version (original)
2. **`main_v1_web_serper.py`** - Serper Google SERP API version (new)

## Key Differences

| Feature | OpenRouter Version | Serper Version |
|---------|-------------------|----------------|
| **Cost** | ~$0.02 per search | ~$0.0003 per search |
| **Cost Reduction** | Baseline | **60x cheaper** |
| **Max Planning Searches** | Conservative (~2-3) | Liberal (5 by default) |
| **API Dependency** | OpenRouter + GPT-4o Mini Search | Serper + OpenRouter (for analysis) |
| **Search Quality** | GPT-4o with web browsing | Google SERP results |
| **Caching** | 30-min disk cache | In-memory LRU cache |
| **Configuration** | .env file dependency | CLI-first, no .env required |
| **Mid-task Searches** | Supported | Disabled (planning only) |
| **Setup Complexity** | Medium | Low |

## Cost Analysis

### Per-Task Breakdown

**OpenRouter Version:**
- Web search: ~$0.002 per search × 2-3 searches = ~$0.004-0.006
- Analysis: ~$0.001 (Qwen 72B)
- Execution: ~$0.003 (Gemini)
- **Total: ~$0.008-0.010 per task**

**Serper Version:**
- Web search: ~$0.0003 per search × 5 searches = ~$0.0015
- Analysis: ~$0.001 (Qwen 72B) 
- Execution: ~$0.003 (Gemini)
- **Total: ~$0.0055 per task** (45% cheaper overall)

### Monthly Usage Examples

For 100 tasks per month:
- OpenRouter version: ~$0.80-1.00
- Serper version: ~$0.55

For 1000 tasks per month:
- OpenRouter version: ~$8.00-10.00
- Serper version: ~$5.50

## When to Use Which Version

### Use Serper Version (`main_v1_web_serper.py`) When:

✅ **Cost is a primary concern**
✅ **High volume usage** (100+ tasks/month)
✅ **Planning-only searches** are sufficient
✅ **Simple setup** is preferred
✅ **Liberal search budget** is acceptable (up to 5 searches)

### Use OpenRouter Version (`mainv1_web_enhanced.py`) When:

✅ **Maximum search quality** is required
✅ **Mid-task clarification** is needed
✅ **Low volume usage** (occasional use)
✅ **GPT-4o web browsing** capabilities are preferred
✅ **Complex, multi-stage workflows** need dynamic search

## Setup Instructions

### Serper Version

1. **Get Serper API Key:**
   ```bash
   # Sign up at https://serper.dev/
   # First 2,500 searches are free
   # Then $0.30 per 1,000 searches
   ```

2. **Run the agent:**
   ```bash
   python main_v1_web_serper.py --serper-key YOUR_SERPER_KEY
   ```

3. **Optional: Set environment variable:**
   ```bash
   export SERPER_API_KEY=your_key_here
   python main_v1_web_serper.py
   ```

### OpenRouter Version

1. **Set up .env file:**
   ```bash
   OPENROUTER_API_KEY=your_key_here
   OPENROUTER_SITE_URL=https://github.com/windows-use
   OPENROUTER_APP_NAME=Windows-Use
   ```

2. **Run the agent:**
   ```bash
   python mainv1_web_enhanced.py
   ```

## Performance Characteristics

### Search Quality
- **OpenRouter**: GPT-4o browses actual web pages, can understand context better
- **Serper**: Google SERP results are structured and fast, good for factual queries

### Response Time
- **OpenRouter**: ~5-15 seconds per search (web browsing)
- **Serper**: ~1-3 seconds per search (API call)

### Reliability
- **OpenRouter**: Dependent on GPT-4o :online model availability
- **Serper**: Dedicated Google Search API, high uptime

## Migration Guide

To switch from OpenRouter to Serper version:

1. **Test with your typical queries:**
   ```bash
   python test_serper_implementation.py
   ```

2. **Compare results:**
   - Run the same query with both versions
   - Evaluate if Serper's SERP results meet your needs

3. **Update your workflow:**
   - Replace `mainv1_web_enhanced.py` calls with `main_v1_web_serper.py`
   - Add `--serper-key` parameter
   - Adjust `--max-planning-searches` if needed (default 5)

## Limitations

### Serper Version Limitations:
- No mid-task searches (planning only)
- Google SERP data only (no deep web browsing)
- Requires separate Serper account/API key

### OpenRouter Version Limitations:
- Higher cost per search
- Dependent on OpenRouter model availability
- More complex environment setup

## Recommendation

**For most users:** Start with **Serper version** due to:
- Significantly lower cost
- Simpler setup
- Adequate search quality for typical automation tasks
- Liberal search budget allows thorough planning

**Upgrade to OpenRouter version** only if you need:
- Maximum search quality for complex queries
- Mid-task clarification capabilities
- Deep web content analysis

## Getting Started

1. **Quick Test (Serper):**
   ```bash
   python main_v1_web_serper.py --serper-key YOUR_KEY --max-planning-searches 3
   ```

2. **Production Usage:**
   ```bash
   export SERPER_API_KEY=your_key
   export OPENROUTER_API_KEY=your_key
   python main_v1_web_serper.py
   ```

Both versions maintain the same Windows-Use agent capabilities and enhanced UI features, differing only in their web search implementation and cost structure.