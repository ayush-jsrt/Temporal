import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    print("Testing Temporal Knowledge Card API...\n")
    
    # Test 1: Preview knowledge card
    print("1. Testing knowledge-preview endpoint:")
    test_data = {
        "text": "Machine learning algorithms require large datasets for training to achieve good performance",
        "context_limit": 3
    }
    
    try:
        response = requests.post(f"{base_url}/knowledge-preview", json=test_data)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"✓ Preview generated")
            print(f"✓ Similar cards found: {result['similar_cards_count']}")
            print(f"✓ Would create card: {result['would_create_card']}")
            print(f"✓ Preview content: {result['knowledge_card_preview'][:100]}...")
        else:
            print(f"✗ Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Create knowledge card
    print("2. Testing add-text endpoint (Knowledge Card Creation):")
    test_data = {
        "text": "Neural networks learn through backpropagation, adjusting weights based on error gradients",
        "title": "Neural Network Learning",
        "metadata": {"category": "deep_learning", "tags": ["neural_networks", "backpropagation"]}
    }
    
    try:
        response = requests.post(f"{base_url}/add-text", json=test_data)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"✓ Knowledge card created with ID: {result['card_id']}")
            print(f"✓ Card title: {result['card_title']}")
            print(f"✓ Knowledge content: {result['knowledge_card_content'][:100]}...")
            print(f"✓ Similar cards referenced: {result['similar_cards_found']}")
        else:
            print(f"✗ Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Search for similar content
    print("2. Testing search endpoint:")
    search_data = {
        "query": "data processing",
        "limit": 3
    }
    
    try:
        response = requests.post(f"{base_url}/search", json=search_data)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"✓ Found {result['count']} similar cards")
            for i, card in enumerate(result['results'][:2], 1):
                print(f"  {i}. {card['title']}: {card['content'][:50]}...")
        else:
            print(f"✗ Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Get all cards
    print("3. Testing get all cards endpoint:")
    try:
        response = requests.get(f"{base_url}/cards")
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"✓ Retrieved {result['count']} total cards")
            for i, card in enumerate(result['cards'][:3], 1):
                print(f"  {i}. {card['title']}: {card['content'][:50]}...")
        else:
            print(f"✗ Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ Request failed: {e}")

if __name__ == "__main__":
    print("Make sure the API server is running first:")
    print("python backend/api.py")
    print("\nThen run this test in another terminal.\n")
    
    input("Press Enter to continue with API tests...")
    test_api()
