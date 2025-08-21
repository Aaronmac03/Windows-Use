"""Test script with a challenging query for the Web-Enhanced Smart Windows Agent"""

from mainv1_web_enhanced import WebEnhancedSmartWindowsAgent

def main():
    print("Web-Enhanced Smart Windows Agent (V1.1) - Challenge Test")
    print("Models: GPT-4o Mini Search Preview :online (translation & web search), Qwen 72B (analysis), Gemini Flash Lite (execution)")
    print("="*80)
    
    # Challenging query with multiple ambiguities and complex requirements
    challenging_query = """
    Open Chrome and find the best rated wireless gaming headset under $150 on Best Buy that works with PlayStation 5. 
    It should have good reviews from this week, RGB lighting, and be available for same-day pickup at the store closest 
    to downtown Louisville Kentucky. Add it to cart but don't complete the purchase. Also check if there's any current 
    sale or promotion codes available.
    """
    
    print(f"CHALLENGING QUERY: {challenging_query.strip()}")
    print("="*80)
    
    # Create and execute with the challenging query
    agent = WebEnhancedSmartWindowsAgent()
    result = agent.execute(challenging_query.strip())
    
    print("\n" + "="*80)
    print("FINAL RESULT:")
    print("="*80)
    print(result)

if __name__ == "__main__":
    main()