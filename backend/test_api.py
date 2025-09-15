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
    
    # Test 3: Get all cards
    print("3. Testing get all cards endpoint:")
    cards_before_delete = []
    try:
        response = requests.get(f"{base_url}/cards")
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            cards_before_delete = result['cards']
            print(f"✓ Retrieved {result['count']} total cards")
            for i, card in enumerate(result['cards'][:3], 1):
                print(f"  {i}. ID:{card['id']} {card['title']}: {card['content'][:50]}...")
        else:
            print(f"✗ Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Delete a card (if any cards exist)
    print("4. Testing delete card endpoint:")
    if cards_before_delete:
        card_to_delete = cards_before_delete[0]  # Delete the first card
        card_id = card_to_delete['id']
        
        try:
            response = requests.delete(f"{base_url}/cards/{card_id}")
            print(f"Status: {response.status_code}")
            result = response.json()
            
            if result.get('success'):
                print(f"✓ Successfully deleted card ID: {card_id}")
                print(f"✓ Deleted card title: {result['deleted_card']['title']}")
                
                # Verify deletion by getting all cards again
                verify_response = requests.get(f"{base_url}/cards")
                if verify_response.status_code == 200:
                    verify_result = verify_response.json()
                    if verify_result.get('success'):
                        new_count = verify_result['count']
                        old_count = len(cards_before_delete)
                        if new_count == old_count - 1:
                            print(f"✓ Confirmed deletion: card count reduced from {old_count} to {new_count}")
                        else:
                            print(f"✗ Card count mismatch: expected {old_count - 1}, got {new_count}")
            else:
                print(f"✗ Error: {result.get('error')}")
        except Exception as e:
            print(f"✗ Request failed: {e}")
        
        print("\n" + "-"*30 + "\n")
        
        # Test 4b: Try to delete non-existent card
        print("4b. Testing delete non-existent card:")
        try:
            response = requests.delete(f"{base_url}/cards/99999")
            print(f"Status: {response.status_code}")
            result = response.json()
            
            if response.status_code == 404 and not result.get('success'):
                print(f"✓ Correctly handled non-existent card: {result['error']}")
            else:
                print(f"✗ Unexpected response for non-existent card")
        except Exception as e:
            print(f"✗ Request failed: {e}")
    else:
        print("No cards available to delete. Create some cards first.")

if __name__ == "__main__":
    print("Make sure the API server is running first:")
    print("python backend/api.py")
    print("\nThen run this test in another terminal.\n")
    
    input("Press Enter to continue with API tests...")
    test_api()
