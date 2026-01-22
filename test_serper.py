"""Test Serper API integration"""
import os
from dotenv import load_dotenv
from src.utils.serper_client import serper_client

# Load environment variables
load_dotenv()

def test_serper_api():
    """Test Serper API search functionality"""
    
    # Check if API key is configured
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key or api_key == "your_serper_api_key_here":
        print("⚠️  SERPER_API_KEY is not configured in .env file")
        print("   Please get an API key from https://serper.dev/")
        print("   The system will work without it, but Explorer Agent won't have real-time search data.")
        return
    
    print("🔍 Testing Serper API...")
    print(f"   API Key: {api_key[:10]}...")
    
    # Test search
    query = "運動習慣 健康"
    print(f"\n📝 Search Query: {query}")
    
    results = serper_client.search(query, num_results=3)
    
    if results:
        print(f"\n✅ Successfully retrieved {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('title', '')}")
            print(f"   {result.get('snippet', '')[:100]}...")
            print(f"   🔗 {result.get('link', '')}\n")
    else:
        print("\n❌ No results returned. Please check:")
        print("   1. Your SERPER_API_KEY is valid")
        print("   2. You have remaining API credits")
        print("   3. Your internet connection is working")

if __name__ == "__main__":
    test_serper_api()
