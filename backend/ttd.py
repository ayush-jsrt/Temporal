from crud import Database
from ai_service import AIService
import json

def test_database():
    print("Testing Database class...")
    
    # Initialize database
    db = Database()
    print("✓ Database initialized")
    
    # Test add_card (now generates embeddings automatically)
    card_id = db.add_card(
        title="Test Card",
        content="This is test content for the card",
        metadata={"tags": ["test", "example"], "category": "testing"}
    )
    print(f"✓ Card added with ID: {card_id}")
    
    # Test get_card_by_id
    retrieved_card = db.get_card_by_id(card_id)
    if retrieved_card:
        print(f"✓ Retrieved card by ID: {retrieved_card.title}")
    else:
        print("✗ Failed to retrieve card by ID")
    
    # Test get_all_cards
    all_cards = db.get_all_cards()
    print(f"✓ Retrieved {len(all_cards)} cards")
    
    # Test vector search with text query
    similar_cards = db.vector_search("test content", limit=3)
    print(f"✓ Vector search returned {len(similar_cards)} similar cards")
    
    # Test delete_card
    delete_success = db.delete_card(card_id)
    if delete_success:
        print(f"✓ Successfully deleted card with ID: {card_id}")
        
        # Verify deletion
        deleted_card = db.get_card_by_id(card_id)
        if deleted_card is None:
            print("✓ Confirmed card was deleted")
        else:
            print("✗ Card still exists after deletion")
    else:
        print("✗ Failed to delete card")
    
    # Test deleting non-existent card
    non_existent_delete = db.delete_card(99999)
    if not non_existent_delete:
        print("✓ Correctly handled deletion of non-existent card")
    else:
        print("✗ Incorrectly reported success for non-existent card deletion")
    
    print("Database tests completed!\n")

def test_ai_service():
    print("Testing AIService class...")
    
    # Initialize AI service
    ai_service = AIService()
    print("✓ AIService initialized")
    
    # Test generate_embedding
    test_text = "This is a test sentence for embedding generation."
    embedding = ai_service.generate_embedding(test_text)
    
    if embedding:
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
        print(f"  First 5 values: {embedding[:5]}")
    else:
        print("✗ Failed to generate embedding")
    
    print("AIService tests completed!\n")

if __name__ == "__main__":
    print("Running tests...\n")
    
    try:
        test_ai_service()
        test_database()
        print("All tests completed!")
    except Exception as e:
        print(f"Error during testing: {e}")