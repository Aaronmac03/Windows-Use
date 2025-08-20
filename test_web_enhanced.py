"""
Comprehensive test suite for the Web-Enhanced Smart Windows Agent
Tests all components and integration points
"""

import sys
import os
import json
from typing import List, Dict

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mainv1_web_enhanced import WebEnhancedTranslator, TaskAnalyzer, WebEnhancedSmartWindowsAgent


class WebEnhancedTester:
    """Test suite for the web-enhanced agent components"""
    
    def __init__(self):
        self.results = {}
        self.mock_search_responses = {
            "lowe's store locations near bashford manor": {
                "status": "success",
                "data": "Lowe's locations: Middletown (2.3 miles), Hurstbourne (4.1 miles)"
            },
            "cheap flat head screwdriver": {
                "status": "success", 
                "data": "Affordable options: Project Source 6-inch ($1.98), Kobalt Standard ($2.48)"
            },
            "current iphone 15 pro price": {
                "status": "success",
                "data": "iPhone 15 Pro pricing: 128GB $999, 256GB $1099, 512GB $1299"
            }
        }
    
    def mock_web_search(self, query: str) -> str:
        """Mock web search function for testing"""
        query_lower = query.lower()
        
        for key, response in self.mock_search_responses.items():
            if any(word in query_lower for word in key.split()):
                return response["data"]
        
        return f"Mock search results for: {query}"
    
    def test_ambiguity_identification(self) -> Dict:
        """Test the ambiguity identification functionality"""
        print("🧪 Testing Ambiguity Identification...")
        
        translator = WebEnhancedTranslator()
        
        test_cases = [
            {
                "query": "Find a cheap screwdriver at the store near Bashford Manor",
                "expected_ambiguities": ["cheap", "near Bashford Manor"]
            },
            {
                "query": "Buy the best laptop under $500 from a local retailer", 
                "expected_ambiguities": ["best", "local retailer"]
            },
            {
                "query": "Open Chrome and go to google.com",
                "expected_ambiguities": []  # Should be clear
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                ambiguities = translator.identify_ambiguities(case["query"])
                
                result = {
                    "query": case["query"],
                    "found_ambiguities": [amb.get("element", "") for amb in ambiguities],
                    "expected_ambiguities": case["expected_ambiguities"],
                    "status": "success"
                }
                
                # Check if we found reasonable ambiguities
                if case["expected_ambiguities"]:
                    found_any_expected = any(
                        expected in str(ambiguities).lower() 
                        for expected in case["expected_ambiguities"]
                    )
                    result["reasonable"] = found_any_expected
                else:
                    result["reasonable"] = len(ambiguities) == 0
                
                results.append(result)
                print(f"  ✅ {case['query'][:50]}... - Found {len(ambiguities)} ambiguities")
                
            except Exception as e:
                results.append({
                    "query": case["query"],
                    "status": "error",
                    "error": str(e)
                })
                print(f"  ❌ {case['query'][:50]}... - Error: {e}")
        
        return {"test_name": "ambiguity_identification", "results": results}
    
    def test_web_search_resolution(self) -> Dict:
        """Test the web search resolution functionality"""
        print("🧪 Testing Web Search Resolution...")
        
        translator = WebEnhancedTranslator()
        translator._web_search_func = self.mock_web_search
        
        test_ambiguities = [
            {
                "type": "LOCATION",
                "element": "near Bashford Manor",
                "search_hint": "Lowe's store locations near Bashford Manor"
            },
            {
                "type": "SUBJECTIVE",
                "element": "cheap",
                "search_hint": "cheap flat head screwdriver"
            }
        ]
        
        results = []
        for ambiguity in test_ambiguities:
            try:
                resolution = translator.resolve_with_search(ambiguity)
                
                result = {
                    "ambiguity": ambiguity["element"],
                    "resolution": resolution,
                    "status": "success" if resolution else "no_resolution"
                }
                results.append(result)
                
                if resolution:
                    print(f"  ✅ Resolved '{ambiguity['element']}': {resolution[:50]}...")
                else:
                    print(f"  ⚠️  Could not resolve '{ambiguity['element']}'")
                    
            except Exception as e:
                results.append({
                    "ambiguity": ambiguity["element"],
                    "status": "error",
                    "error": str(e)
                })
                print(f"  ❌ Error resolving '{ambiguity['element']}': {e}")
        
        return {"test_name": "web_search_resolution", "results": results}
    
    def test_query_rewriting(self) -> Dict:
        """Test the query rewriting functionality"""
        print("🧪 Testing Query Rewriting...")
        
        translator = WebEnhancedTranslator()
        
        test_cases = [
            {
                "original": "Find a cheap screwdriver at the store near Bashford Manor",
                "clarifications": {
                    "cheap": "Under $3, best value is Project Source 6-inch at $1.98",
                    "near Bashford Manor": "Lowe's Middletown (2.3 miles away)"
                }
            },
            {
                "original": "Buy the latest iPhone",
                "clarifications": {
                    "latest iPhone": "iPhone 15 Pro, available in 128GB ($999), 256GB ($1099), 512GB ($1299)"
                }
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                enriched = translator.rewrite_query(case["original"], case["clarifications"])
                
                result = {
                    "original_query": case["original"],
                    "clarifications": case["clarifications"],
                    "enriched_query": enriched,
                    "status": "success",
                    "improved": len(enriched) > len(case["original"]) and enriched != case["original"]
                }
                results.append(result)
                
                print(f"  ✅ Original: {case['original']}")
                print(f"     Enhanced: {enriched}")
                
            except Exception as e:
                results.append({
                    "original_query": case["original"],
                    "status": "error", 
                    "error": str(e)
                })
                print(f"  ❌ Error rewriting query: {e}")
        
        return {"test_name": "query_rewriting", "results": results}
    
    def test_task_analyzer_integration(self) -> Dict:
        """Test integration with the TaskAnalyzer"""
        print("🧪 Testing TaskAnalyzer Integration...")
        
        # Note: This test may require API keys to work properly
        try:
            analyzer = TaskAnalyzer()
            
            test_queries = [
                "Open Chrome and navigate to lowes.com to find Project Source 6-inch flat head screwdriver for $1.98",
                "Launch Google Chrome browser and go to Apple website to check iPhone 15 Pro pricing"
            ]
            
            results = []
            for query in test_queries:
                try:
                    instructions = analyzer.analyze(query)
                    
                    result = {
                        "query": query,
                        "instructions": instructions,
                        "instruction_count": len(instructions),
                        "status": "success" if instructions else "no_instructions"
                    }
                    results.append(result)
                    
                    if instructions:
                        print(f"  ✅ Generated {len(instructions)} instructions for: {query[:50]}...")
                        for i, inst in enumerate(instructions[:3], 1):  # Show first 3
                            print(f"     {i}. {inst}")
                    else:
                        print(f"  ⚠️  No instructions generated for: {query[:50]}...")
                        
                except Exception as e:
                    results.append({
                        "query": query,
                        "status": "error",
                        "error": str(e)
                    })
                    print(f"  ❌ Error analyzing query: {e}")
            
            return {"test_name": "task_analyzer_integration", "results": results}
            
        except Exception as e:
            return {
                "test_name": "task_analyzer_integration",
                "status": "error",
                "error": f"Could not initialize TaskAnalyzer: {e}"
            }
    
    def test_end_to_end_translation(self) -> Dict:
        """Test the complete end-to-end translation process"""
        print("🧪 Testing End-to-End Translation...")
        
        translator = WebEnhancedTranslator()
        translator._web_search_func = self.mock_web_search
        
        test_query = "Find a cheap screwdriver at Lowe's near Bashford Manor and add to cart"
        
        try:
            # Run complete translation
            enriched_query = translator.translate(test_query)
            
            result = {
                "original_query": test_query,
                "enriched_query": enriched_query,
                "status": "success",
                "improvement": len(enriched_query) > len(test_query),
                "cache_entries": len(translator._resolution_cache)
            }
            
            print(f"  ✅ Translation completed")
            print(f"     Original: {test_query}")
            print(f"     Enhanced: {enriched_query}")
            print(f"     Cache entries: {result['cache_entries']}")
            
            return {"test_name": "end_to_end_translation", "results": [result]}
            
        except Exception as e:
            return {
                "test_name": "end_to_end_translation",
                "status": "error",
                "error": str(e)
            }
    
    def test_mid_task_clarification(self) -> Dict:
        """Test the mid-task clarification functionality"""
        print("🧪 Testing Mid-Task Clarification...")
        
        translator = WebEnhancedTranslator()
        translator._web_search_func = self.mock_web_search
        
        # Pre-populate cache
        translator._resolution_cache["cheap screwdriver"] = "Project Source 6-inch at $1.98"
        
        test_questions = [
            "What's the cheapest screwdriver available?",
            "What are the store hours for Lowe's?", 
            "How much does the iPhone 15 Pro cost?"
        ]
        
        results = []
        for question in test_questions:
            try:
                answer = translator.mid_task_clarify(question)
                
                result = {
                    "question": question,
                    "answer": answer,
                    "status": "success",
                    "used_cache": "cheapest screwdriver" in question and "Project Source" in answer
                }
                results.append(result)
                
                print(f"  ✅ Q: {question}")
                print(f"     A: {answer[:100]}...")
                
            except Exception as e:
                results.append({
                    "question": question,
                    "status": "error",
                    "error": str(e)
                })
                print(f"  ❌ Error with question '{question}': {e}")
        
        return {"test_name": "mid_task_clarification", "results": results}
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return comprehensive results"""
        print("🚀 Running Web-Enhanced Agent Test Suite")
        print("="*80)
        
        all_results = {
            "test_suite": "web_enhanced_agent",
            "timestamp": "test_run",
            "tests": []
        }
        
        # Run individual tests
        test_methods = [
            self.test_ambiguity_identification,
            self.test_web_search_resolution, 
            self.test_query_rewriting,
            self.test_mid_task_clarification,
            self.test_end_to_end_translation,
            self.test_task_analyzer_integration
        ]
        
        for test_method in test_methods:
            try:
                result = test_method()
                all_results["tests"].append(result)
                print()  # Add spacing between tests
                
            except Exception as e:
                all_results["tests"].append({
                    "test_name": test_method.__name__,
                    "status": "error",
                    "error": str(e)
                })
                print(f"❌ Test {test_method.__name__} failed: {e}\n")
        
        # Calculate summary
        total_tests = len(all_results["tests"])
        successful_tests = sum(1 for test in all_results["tests"] 
                             if test.get("status") != "error")
        
        all_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
        }
        
        print("="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Success Rate: {all_results['summary']['success_rate']}")
        
        # Show test details
        for test in all_results["tests"]:
            status_emoji = "✅" if test.get("status") != "error" else "❌"
            print(f"{status_emoji} {test.get('test_name', 'Unknown Test')}")
        
        return all_results


def main():
    """Main test runner"""
    print("Web-Enhanced Smart Windows Agent - Test Suite")
    print("This will test all components of the web-enhanced translation layer")
    print()
    
    tester = WebEnhancedTester()
    results = tester.run_all_tests()
    
    # Optionally save results to file
    save_results = input("\nSave detailed test results to file? (y/n): ").strip().lower()
    if save_results == 'y':
        results_file = "web_enhanced_test_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✅ Results saved to {results_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


if __name__ == "__main__":
    main()