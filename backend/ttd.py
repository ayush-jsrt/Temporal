from crud import Database
from EmbeddingGenerator import EmbeddingGenerator
import json

def test_database():
    print("Testing Database class...")
    
    # Initialize database
    db = Database()
    print("✓ Database initialized")
    
    # Initialize embedder for test data
    embedder = EmbeddingGenerator()
    
    # Test add_card
    test_embedding = embedder.generate_embedding("Test content for embedding")
    card_id = db.add_card(
        title="Test Card",
        content="This is test content for the card",
        metadata={"tags": ["test", "example"], "category": "testing"},
        embedding=test_embedding
    )
    print(f"✓ Card added with ID: {card_id}")
    
    # Test get_all_cards
    all_cards = db.get_all_cards()
    print(f"✓ Retrieved {len(all_cards)} cards")
    
    # Test get_card_by_id (if method exists)
    try:
        card = db.get_card_by_id(card_id)
        if card:
            print(f"✓ Retrieved card by ID: {card.title}")
        else:
            print("✗ Card not found by ID")
    except AttributeError:
        print("ℹ get_card_by_id method not implemented yet")
    
    # Test vector search (if method exists)
    try:
        query_embedding = embedder.generate_embedding("test query")
        similar_cards = db.vector_search(query_embedding, limit=3)
        print(f"✓ Vector search returned {len(similar_cards)} similar cards")
    except AttributeError:
        print("ℹ vector_search method not implemented yet")
    
    print("Database tests completed!\n")

def test_embedding_generator():
    print("Testing EmbeddingGenerator class...")
    
    # Initialize embedder
    embedder = EmbeddingGenerator()
    print("✓ EmbeddingGenerator initialized")
    
    # Test generate_embedding
    test_text = "This is a test sentence for embedding generation."
    embedding = embedder.generate_embedding(test_text)
    
    if embedding:
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
        print(f"  First 5 values: {embedding[:5]}")
    else:
        print("✗ Failed to generate embedding")
    
    # Test generate_card_embedding
    card_embedding = embedder.generate_card_embedding(
        "Sample Card Title",
        "This is sample content for a card that we want to embed."
    )
    
    if card_embedding:
        print(f"✓ Generated card embedding with {len(card_embedding)} dimensions")
        print(f"  First 5 values: {card_embedding[:5]}")
    else:
        print("✗ Failed to generate card embedding")
    
    print("EmbeddingGenerator tests completed!\n")

if __name__ == "__main__":
    print("Running tests...\n")
    
    try:
        test_embedding_generator()
        test_database()
        print("All tests completed!")
    except Exception as e:
        print(f"Error during testing: {e}")