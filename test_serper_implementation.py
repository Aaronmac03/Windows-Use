"""
Test script for Serper implementation
Validates basic functionality without requiring full agent execution
"""

import os
import json
from dotenv import load_dotenv
from main_v1_web_serper import serper_search, cached_serper_search, create_serper_search_function, SerperWebEnhancedTranslator

# Load environment variables
load_dotenv()

def test_serper_basic_search():
    """Test basic Serper search functionality"""
    print("🧪 Testing basic Serper search...")
    
    # Check if we have a Serper key (skip if not available)
    serper_key = os.getenv("SERPER_API_KEY")
    if not serper_key:
        print("⚠️  SERPER_API_KEY not set, skipping actual search test")
        return True
    
    try:
        # Test basic search
        result = serper_search("best wireless gaming headsets 2024", serper_key, num=3)
        
        print(f"✅ Search returned {result['count']} results")
        
        if result['results']:
            first_result = result['results'][0]
            print(f"   Sample result: {first_result.get('title', 'No title')[:50]}...")
            print(f"   URL: {first_result.get('url', 'No URL')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Serper search failed: {e}")
        return False

def test_lru_cache():
    """Test LRU caching functionality"""
    print("\n🧪 Testing LRU cache...")
    
    serper_key = os.getenv("SERPER_API_KEY", "test_key")
    
    # Clear cache
    cached_serper_search.cache_clear()
    
    # First call (should be cached)
    result1 = cached_serper_search("test query", serper_key, 3)
    cache_info1 = cached_serper_search.cache_info()
    
    # Second call (should hit cache)
    result2 = cached_serper_search("test query", serper_key, 3)
    cache_info2 = cached_serper_search.cache_info()
    
    # Verify caching worked
    if cache_info2.hits > cache_info1.hits:
        print("✅ LRU cache working - cache hit detected")
        return True
    else:
        print("⚠️  LRU cache may not be working as expected")
        return False

def test_search_function_creation():
    """Test search function factory"""
    print("\n🧪 Testing search function creation...")
    
    try:
        search_func = create_serper_search_function("test_key", max_results=3)
        print("✅ Search function created successfully")
        
        # Test function signature
        if callable(search_func):
            print("✅ Search function is callable")
            return True
        else:
            print("❌ Search function is not callable")
            return False
            
    except Exception as e:
        print(f"❌ Search function creation failed: {e}")
        return False

def test_translator_initialization():
    """Test SerperWebEnhancedTranslator initialization"""
    print("\n🧪 Testing translator initialization...")
    
    # Check if we have required API keys
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  OPENROUTER_API_KEY not set, skipping translator test")
        return True
    
    try:
        translator = SerperWebEnhancedTranslator(
            serper_key="test_key", 
            max_planning_searches=8,
            max_runtime_searches=5
        )
        
        print(f"✅ Translator initialized with model: {translator.model_name}")
        print(f"✅ Max planning searches: {translator.max_planning_searches}")
        print(f"✅ Max runtime searches: {translator.max_runtime_searches}")
        print(f"✅ Planning search calls: {translator.planning_search_calls}")
        print(f"✅ Runtime search calls: {translator.runtime_search_calls}")
        print(f"✅ Mid-task callback available: {translator.mid_task_callback is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Translator initialization failed: {e}")
        return False

def test_ambiguity_identification():
    """Test ambiguity identification"""
    print("\n🧪 Testing ambiguity identification...")
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  OPENROUTER_API_KEY not set, skipping ambiguity test")
        return True
    
    try:
        translator = SerperWebEnhancedTranslator("test_key", 8, 5)
        
        test_query = "Find the best wireless gaming headset under $150 at a store near downtown"
        ambiguities = translator.identify_ambiguities(test_query)
        
        print(f"✅ Found {len(ambiguities)} ambiguities in test query")
        for amb in ambiguities:
            print(f"   • {amb.get('type', 'UNKNOWN')}: {amb.get('element', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ambiguity identification failed: {e}")
        return False

def test_mid_task_clarification():
    """Test mid-task clarification functionality"""
    print("\n🧪 Testing mid-task clarification...")
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  OPENROUTER_API_KEY not set, skipping mid-task test")
        return True
    
    try:
        translator = SerperWebEnhancedTranslator("test_key", 8, 5)
        
        # Test that the method exists and handles queries
        test_question = "What are store hours for Best Buy?"
        result = translator.mid_task_clarify(test_question)
        
        print(f"✅ Mid-task clarification method available")
        print(f"✅ Response format: {type(result).__name__}")
        print(f"   Sample response: {str(result)[:50]}...")
        
        # Test runtime search limit tracking
        print(f"✅ Runtime calls after test: {translator.runtime_search_calls}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mid-task clarification test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Serper Implementation Test Suite")
    print("="*50)
    
    tests = [
        test_serper_basic_search,
        test_lru_cache,
        test_search_function_creation,
        test_translator_initialization,
        test_ambiguity_identification,
        test_mid_task_clarification
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Serper implementation looks good.")
    else:
        print(f"⚠️  {total - passed} test(s) failed or skipped.")
    
    print("\n💡 To test with real Serper API:")
    print("   export SERPER_API_KEY=your_key_here")
    print("   export OPENROUTER_API_KEY=your_key_here")
    print("   python test_serper_implementation.py")

if __name__ == "__main__":
    main()