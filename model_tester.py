"""
Model Testing Script for Web-Enhanced Agent
Tests which OpenRouter models are available and working with your API key
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

class ModelTester:
    """Test different OpenRouter models for compatibility"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_headers = {
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/windows-use"),
            "X-Title": os.getenv("OPENROUTER_X_TITLE", "Windows-Use Web Enhanced")
        }
    
    def test_model(self, model_name: str) -> dict:
        """Test a specific model"""
        print(f"🧪 Testing {model_name}...")
        
        try:
            llm = ChatOpenAI(
                model=model_name,
                temperature=0.1,
                max_tokens=50,
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers=self.default_headers
            )
            
            # Simple test query
            response = llm.invoke("Respond with 'OK' if you can understand this message.")
            
            result = {
                "model": model_name,
                "status": "success",
                "response": response.content.strip(),
                "error": None
            }
            
            print(f"✅ {model_name}: Working - Response: {response.content.strip()[:30]}...")
            return result
            
        except Exception as e:
            result = {
                "model": model_name,
                "status": "error",
                "response": None,
                "error": str(e)
            }
            
            print(f"❌ {model_name}: Failed - {str(e)}")
            return result
    
    def test_all_models(self) -> list:
        """Test all recommended models"""
        
        # Models to test (in order of preference for web-enhanced agent)
        models_to_test = [
            "openai/gpt-4o-mini-search-preview:online",  # Preferred for web analysis & search
            "qwen/qwen-2.5-72b-instruct",        # Good fallback
            "google/gemini-2.0-flash-thinking-exp",  # Alternative option
            "meta-llama/llama-3.1-8b-instruct",  # Free option
            "anthropic/claude-3.5-sonnet",       # Premium option
            "openai/gpt-4o-mini",                # OpenAI option
            "google/gemini-flash-1.5",           # Google option
            "mistralai/mistral-7b-instruct"      # Mistral option
        ]
        
        print("🚀 Testing OpenRouter Models for Web-Enhanced Agent")
        print("="*60)
        
        if not self.api_key:
            print("❌ ERROR: OPENROUTER_API_KEY not found in environment variables!")
            print("Please set your OpenRouter API key in the .env file.")
            return []
        
        print(f"✅ API Key found: {self.api_key[:8]}...")
        print()
        
        results = []
        working_models = []
        
        for model in models_to_test:
            result = self.test_model(model)
            results.append(result)
            
            if result["status"] == "success":
                working_models.append(model)
        
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        
        print(f"✅ Working models: {len(working_models)}")
        for model in working_models:
            print(f"   • {model}")
        
        failed_models = [r["model"] for r in results if r["status"] == "error"]
        print(f"\n❌ Failed models: {len(failed_models)}")
        for model in failed_models:
            print(f"   • {model}")
        
        if working_models:
            print(f"\n🎯 RECOMMENDED: Use '{working_models[0]}' for best performance")
        else:
            print(f"\n⚠️  WARNING: No models are working. Please check your API key and account status.")
        
        return results
    
    def get_recommended_model(self) -> str:
        """Get the best working model for the web-enhanced agent"""
        results = self.test_all_models()
        
        working_models = [r["model"] for r in results if r["status"] == "success"]
        
        if working_models:
            return working_models[0]  # Return the first working model (highest priority)
        else:
            return None


def main():
    """Main testing function"""
    print("Web-Enhanced Agent Model Tester")
    print("This script tests which OpenRouter models work with your API key")
    print()
    
    tester = ModelTester()
    
    # Test all models
    results = tester.test_all_models()
    
    # Ask if user wants to test the web-enhanced agent with the best model
    working_models = [r["model"] for r in results if r["status"] == "success"]
    
    if working_models:
        print(f"\n🔧 Would you like to test the web-enhanced agent with {working_models[0]}?")
        test_agent = input("Enter 'y' to test: ").strip().lower()
        
        if test_agent == 'y':
            print(f"\n🚀 Testing Web-Enhanced Agent with {working_models[0]}")
            print("-"*60)
            
            try:
                # Import and test the web-enhanced agent
                from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent
                
                # Simple mock web search for testing
                def mock_web_search(query):
                    return f"Mock search results for: {query}"
                
                # Initialize agent with the working model
                agent = WebEnhancedSmartWindowsAgent(
                    web_search_func=mock_web_search,
                    translation_model=working_models[0]
                )
                
                # Test with a simple query
                test_query = "Find a cheap laptop at the local store"
                print(f"Test query: {test_query}")
                print()
                
                # Just test the translation part
                enhanced_query = agent.translator.translate(test_query)
                print(f"Enhanced query: {enhanced_query}")
                
                print("\n✅ Web-Enhanced Agent test successful!")
                
            except Exception as e:
                print(f"❌ Web-Enhanced Agent test failed: {e}")
    
    # Save results to file
    save_results = input("\nSave test results to file? (y/n): ").strip().lower()
    if save_results == 'y':
        try:
            import json
            with open("model_test_results.json", "w") as f:
                json.dump(results, f, indent=2)
            print("✅ Results saved to model_test_results.json")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


if __name__ == "__main__":
    main()