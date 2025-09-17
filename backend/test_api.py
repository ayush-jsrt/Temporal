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

    print("\n" + "="*50 + "\n")

    # Test 5: Update card endpoint
    print("5. Testing update card endpoint:")
    # Get current cards to find one to update
    try:
        response = requests.get(f"{base_url}/cards")
        if response.status_code == 200 and response.json().get('success'):
            current_cards = response.json()['cards']
            if current_cards:
                card_to_update = current_cards[0]
                card_id = card_to_update['id']
                original_title = card_to_update['title']
                
                print(f"Updating card ID: {card_id}")
                print(f"Original title: {original_title}")
                
                # Test 5a: Update title only
                print("\n5a. Testing title-only update:")
                update_data = {
                    "title": f"Updated: {original_title}"
                }
                
                response = requests.put(f"{base_url}/cards/{card_id}", json=update_data)
                print(f"Status: {response.status_code}")
                result = response.json()
                
                if result.get('success'):
                    print(f"✓ Title updated successfully")
                    print(f"✓ New title: {result['updated_card']['title']}")
                else:
                    print(f"✗ Update failed: {result.get('error')}")
                
                # Test 5b: Update content and metadata
                print("\n5b. Testing content and metadata update:")
                update_data = {
                    "content": "<h3 class='card-heading'>Updated Knowledge Card</h3><p class='card-description'>This card has been updated via API test.</p>",
                    "metadata": {
                        "updated_by": "api_test",
                        "test_timestamp": "2025-09-17",
                        "version": "2.0"
                    }
                }
                
                response = requests.put(f"{base_url}/cards/{card_id}", json=update_data)
                print(f"Status: {response.status_code}")
                result = response.json()
                
                if result.get('success'):
                    print(f"✓ Content and metadata updated successfully")
                    print(f"✓ Updated metadata: {result['updated_card']['metadata']}")
                    print(f"✓ Content length: {len(result['updated_card']['content'])}")
                else:
                    print(f"✗ Update failed: {result.get('error')}")
                
                # Test 5c: Update non-existent card
                print("\n5c. Testing update of non-existent card:")
                response = requests.put(f"{base_url}/cards/99999", json={"title": "This should fail"})
                print(f"Status: {response.status_code}")
                
                if response.status_code == 404:
                    print(f"✓ Correctly returned 404 for non-existent card")
                else:
                    print(f"✗ Expected 404, got {response.status_code}")
                
                # Test 5d: Update with empty data
                print("\n5d. Testing update with no data:")
                response = requests.put(f"{base_url}/cards/{card_id}", json={})
                print(f"Status: {response.status_code}")
                
                if response.status_code == 400:
                    print(f"✓ Correctly returned 400 for empty update data")
                else:
                    print(f"✗ Expected 400, got {response.status_code}")
                    
            else:
                print("No cards available to update. Create some cards first.")
        else:
            print("Could not retrieve cards for update test")
    except Exception as e:
        print(f"✗ Update test failed: {e}")

if __name__ == "__main__":
    print("Make sure the API server is running first:")
    print("python backend/api.py")
    print("\nThen run this test in another terminal.\n")
    
    input("Press Enter to continue with API tests...")
    test_api()
