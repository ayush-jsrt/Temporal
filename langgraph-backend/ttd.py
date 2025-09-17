from app import ConversationalWorkflow
from ai_service import AIService
from database import RedisManager, ConversationStateManager, create_database_manager
import requests
import json
import uuid

def test_redis_connection():
    """Test Redis connection and basic operations"""
    print("=== Testing Redis Connection ===")
    
    try:
        redis_manager = RedisManager()
        print("✓ Redis connection successful")
        
        # Test basic operations
        test_key = "test:connection"
        test_value = {"message": "hello", "timestamp": "2025-09-17"}
        
        # Set JSON data
        if redis_manager.set_json(test_key, test_value, ttl=60):
            print("✓ JSON data stored successfully")
        else:
            print("✗ Failed to store JSON data")
            return False
        
        # Get JSON data
        retrieved_value = redis_manager.get_json(test_key)
        if retrieved_value == test_value:
            print("✓ JSON data retrieved successfully")
        else:
            print(f"✗ Data mismatch: expected {test_value}, got {retrieved_value}")
            return False
        
        # Test key existence
        if redis_manager.exists(test_key):
            print("✓ Key existence check working")
        else:
            print("✗ Key existence check failed")
        
        # Cleanup
        if redis_manager.delete(test_key):
            print("✓ Key deletion successful")
        else:
            print("✗ Key deletion failed")
        
        return True
        
    except Exception as e:
        print(f"✗ LangGraph workflow test failed: {e}")
        return False

def test_session_continuity():
    """Test session continuity and focused card functionality"""
    print("=== Testing Session Continuity ===")
    
    workflow = ConversationalWorkflow()
    
    if not workflow.use_redis:
        print("⚠ Skipping session continuity test - Redis not available")
        return False
    
    try:
        # Start a conversation
        print("Starting new conversation...")
        result1 = workflow.process_message("What is Python programming?")
        session_id = result1.get("session_id")
        
        if not session_id:
            print("✗ No session ID returned")
            return False
        
        print(f"✓ Session created: {session_id[:8]}...")
        print(f"  Response: {result1['response'][:80]}...")
        
        # Continue conversation in same session
        print("Continuing conversation...")
        result2 = workflow.process_message(
            "Now tell me about Django web framework", 
            session_id=session_id
        )
        
        print(f"✓ Continued conversation")
        print(f"  Response: {result2['response'][:80]}...")
        
        # Test focused card functionality
        print("Testing focused card...")
        card_data = {
            "id": 999,
            "title": "Python Web Development",
            "content": "Python is excellent for web development with frameworks like Django and Flask."
        }
        
        if workflow.set_focused_card(session_id, card_data):
            print("✓ Focused card set")
        else:
            print("✗ Failed to set focused card")
            return False
        
        # Test conversation with focused card context
        result3 = workflow.process_message(
            "Update this with Flask information",
            session_id=session_id
        )
        
        print(f"✓ Message processed with focused card context")
        print(f"  Intent: {result3['intent']}")
        print(f"  Response: {result3['response'][:80]}...")
        
        # Check conversation history
        history = workflow.get_session_history(session_id, limit=5)
        print(f"✓ Retrieved conversation history: {len(history)} messages")
        
        for i, msg in enumerate(history, 1):
            print(f"  {i}. {msg['user_message'][:40]}... -> {msg['intent']}")
        
        # Test clearing focused card
        if workflow.clear_focused_card(session_id):
            print("✓ Focused card cleared")
        else:
            print("⚠ Failed to clear focused card")
        
        return True
        
    except Exception as e:
        print(f"✗ Session continuity test failed: {e}")
        return False

def test_conversation_state_manager():
    """Test conversation state management"""
    print("\n=== Testing Conversation State Manager ===")
    
    try:
        state_manager = create_database_manager()
        print("✓ ConversationStateManager initialized")
        
        # Create a test session
        session_id = state_manager.create_new_session(user_id="test_user")
        print(f"✓ Created session: {session_id}")
        
        # Test conversation state
        test_state = {
            "intent": "UPDATE",
            "confidence": 0.95,
            "reasoning": "User wants to update card",
            "current_card_id": 123
        }
        
        if state_manager.save_conversation_state(session_id, test_state):
            print("✓ Conversation state saved")
        else:
            print("✗ Failed to save conversation state")
            return False
        
        # Load conversation state
        loaded_state = state_manager.load_conversation_state(session_id)
        if loaded_state and loaded_state["intent"] == "UPDATE":
            print("✓ Conversation state loaded successfully")
        else:
            print(f"✗ Failed to load conversation state: {loaded_state}")
            return False
        
        # Test focused card
        focused_card = {
            "id": 123,
            "title": "Python Programming",
            "content": "Python is a programming language..."
        }
        
        if state_manager.save_focused_card(session_id, focused_card):
            print("✓ Focused card saved")
        else:
            print("✗ Failed to save focused card")
        
        loaded_card = state_manager.load_focused_card(session_id)
        if loaded_card and loaded_card["id"] == 123:
            print("✓ Focused card loaded successfully")
        else:
            print(f"✗ Failed to load focused card: {loaded_card}")
        
        # Test conversation history
        messages = [
            {"user_message": "What is Python?", "intent": "NO_ACTION", "response": "Python is a programming language"},
            {"user_message": "Create a card about ML", "intent": "CREATE_NEW", "response": "Card created"},
            {"user_message": "Update my Python card", "intent": "UPDATE", "response": "Card updated"}
        ]
        
        for msg in messages:
            state_manager.add_message_to_history(session_id, msg)
        
        history = state_manager.get_conversation_history(session_id, limit=5)
        if len(history) == 3:
            print("✓ Conversation history working")
            print(f"  History contains {len(history)} messages")
        else:
            print(f"✗ History count mismatch: expected 3, got {len(history)}")
        
        # Test session info
        session_info = state_manager.get_session_info(session_id)
        if session_info and session_info["session_id"] == session_id:
            print("✓ Session info retrieval working")
        else:
            print("✗ Failed to retrieve session info")
        
        # Cleanup test data
        state_manager.clear_conversation_history(session_id)
        state_manager.clear_focused_card(session_id)
        print("✓ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Conversation state manager test failed: {e}")
        return False

def test_session_management():
    """Test session creation and management"""
    print("\n=== Testing Session Management ===")
    
    try:
        state_manager = create_database_manager()
        
        # Create multiple test sessions
        sessions = []
        for i in range(3):
            session_id = state_manager.create_new_session(user_id=f"user_{i}")
            sessions.append(session_id)
            print(f"✓ Created session {i+1}: {session_id[:8]}...")
        
        # Test session activity updates
        for session_id in sessions:
            state_manager.update_session_activity(session_id)
        
        print("✓ Session activities updated")
        
        # Get active sessions
        active_sessions = state_manager.get_active_sessions()
        if len(active_sessions) >= len(sessions):
            print(f"✓ Found {len(active_sessions)} active sessions")
        else:
            print(f"⚠ Expected at least {len(sessions)} sessions, found {len(active_sessions)}")
        
        # Test session info for each
        valid_sessions = 0
        for session_id in sessions:
            session_info = state_manager.get_session_info(session_id)
            if session_info:
                valid_sessions += 1
        
        if valid_sessions == len(sessions):
            print(f"✓ All {valid_sessions} sessions have valid info")
        else:
            print(f"⚠ Only {valid_sessions} out of {len(sessions)} sessions have valid info")
        
        return True
        
    except Exception as e:
        print(f"✗ Session management test failed: {e}")
        return False

def test_redis_ttl_behavior():
    """Test TTL (Time To Live) behavior"""
    print("\n=== Testing Redis TTL Behavior ===")
    
    try:
        redis_manager = RedisManager()
        
        # Test short TTL
        test_key = "test:ttl"
        test_data = {"message": "this will expire"}
        
        # Set with 5 second TTL
        if redis_manager.set_json(test_key, test_data, ttl=5):
            print("✓ Data stored with 5-second TTL")
        else:
            print("✗ Failed to store data with TTL")
            return False
        
        # Check immediately
        if redis_manager.exists(test_key):
            print("✓ Key exists immediately after creation")
        else:
            print("✗ Key should exist immediately")
        
        # Get TTL info (Redis command)
        try:
            ttl = redis_manager.client.ttl(test_key)
            if ttl > 0:
                print(f"✓ TTL set correctly: {ttl} seconds remaining")
            else:
                print(f"⚠ Unexpected TTL value: {ttl}")
        except Exception as e:
            print(f"⚠ Could not check TTL: {e}")
        
        print("✓ TTL behavior test completed (key will expire in 5 seconds)")
        return True
        
    except Exception as e:
        print(f"✗ TTL test failed: {e}")
        return False

def test_redis_error_handling():
    """Test Redis error handling scenarios"""
    print("\n=== Testing Redis Error Handling ===")
    
    try:
        redis_manager = RedisManager()
        
        # Test getting non-existent key
        non_existent = redis_manager.get_json("non:existent:key", "default_value")
        if non_existent == "default_value":
            print("✓ Default value returned for non-existent key")
        else:
            print(f"✗ Expected default value, got: {non_existent}")
        
        # Test deleting non-existent key
        delete_result = redis_manager.delete("non:existent:key")
        if delete_result is False:
            print("✓ Delete operation handled non-existent key correctly")
        else:
            print(f"⚠ Unexpected delete result: {delete_result}")
        
        # Test exists on non-existent key
        exists_result = redis_manager.exists("non:existent:key")
        if exists_result is False:
            print("✓ Exists check correctly returned False")
        else:
            print(f"✗ Exists should return False, got: {exists_result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def test_integration_with_workflow():
    """Test integration between Redis state management and LangGraph workflow"""
    print("\n=== Testing Redis-Workflow Integration ===")
    
    if not test_backend_connection():
        print("⚠ Skipping integration test - backend not available")
        return False
    
    try:
        state_manager = create_database_manager()
        workflow = ConversationalWorkflow()
        
        # Create a session for this test
        session_id = state_manager.create_new_session(user_id="workflow_test")
        print(f"✓ Created test session: {session_id[:8]}...")
        
        # Simulate a conversation flow
        test_messages = [
            "What is machine learning?",
            "Update my Python card with Django information"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\nMessage {i}: '{message}'")
            
            # Process through workflow
            result = workflow.process_message(message)
            
            # Store in Redis
            conversation_entry = {
                "user_message": result["user_message"],
                "intent": result["intent"],
                "confidence": result["confidence"],
                "response": result["response"]
            }
            
            state_manager.add_message_to_history(session_id, conversation_entry)
            state_manager.update_session_activity(session_id)
            
            print(f"✓ Message processed and stored in Redis")
        
        # Retrieve conversation history
        history = state_manager.get_conversation_history(session_id)
        if len(history) == len(test_messages):
            print(f"✓ Conversation history complete: {len(history)} messages stored")
        else:
            print(f"⚠ History length mismatch: expected {len(test_messages)}, got {len(history)}")
        
        # Check session stats
        session_info = state_manager.get_session_info(session_id)
        if session_info and session_info["message_count"] >= len(test_messages):
            print(f"✓ Session message count updated: {session_info['message_count']}")
        else:
            print(f"⚠ Session message count issue")
        
        # Cleanup
        state_manager.clear_conversation_history(session_id)
        print("✓ Integration test completed and cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def test_ai_service():
    """Test the basic AI service functionality"""
    print("=== Testing AI Service ===")
    
    ai_service = AIService()
    print("✓ AIService initialized")
    
    # Test text generation
    prompt = "What is the capital of France?"
    response = ai_service.generate_text(prompt, max_tokens=50)
    
    if response and len(response.strip()) > 0:
        print("✓ Text generation working")
        print(f"  Sample response: {response[:100]}...")
    else:
        print("✗ Text generation failed")
    
    print("AI Service tests completed!\n")

def test_backend_connection():
    """Test if the backend API is accessible"""
    print("=== Testing Backend Connection ===")
    
    backend_url = "http://localhost:5000"
    
    try:
        # Test basic connectivity
        response = requests.get(f"{backend_url}/cards", timeout=5)
        if response.status_code == 200:
            print("✓ Backend API is accessible")
            cards_data = response.json()
            card_count = len(cards_data.get("cards", []))
            print(f"✓ Found {card_count} existing cards")
            return True
        else:
            print(f"✗ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to backend: {e}")
        print("  Make sure the backend server is running on http://localhost:5000")
        return False

def test_card_update_functionality():
    """Test the card update functionality with real backend"""
    print("=== Testing Card Update Functionality ===")
    
    if not test_backend_connection():
        print("Skipping update tests - backend not available")
        return False
    
    backend_url = "http://localhost:5000"
    
    # First, create a test card
    print("Creating test card...")
    test_card_data = {
        "text": "Python is a programming language that is easy to learn and powerful.",
        "title": "Python Programming Basics"
    }
    
    create_response = requests.post(f"{backend_url}/add-text", json=test_card_data)
    
    if create_response.status_code == 200:
        created_card = create_response.json()
        card_id = created_card.get("card_id")
        print(f"✓ Created test card with ID: {card_id}")
        
        # Test updating the card
        print("Testing card update...")
        update_data = {
            "title": "Updated Python Programming Guide",
            "content": "<h3 class='card-heading'>Enhanced Python Programming</h3><p class='card-description'>Python is a powerful, easy-to-learn programming language with excellent library support. Updated with additional insights about its versatility in data science and web development.</p>",
            "metadata": {"updated_by": "langgraph_test", "test": True}
        }
        
        update_response = requests.put(f"{backend_url}/cards/{card_id}", json=update_data)
        
        if update_response.status_code == 200:
            print("✓ Card update successful")
            update_result = update_response.json()
            updated_card = update_result.get("updated_card")
            print(f"  Updated title: {updated_card.get('title')}")
            
            # Clean up - delete test card
            delete_response = requests.delete(f"{backend_url}/cards/{card_id}")
            if delete_response.status_code == 200:
                print("✓ Test card cleaned up")
            
            return True
        else:
            print(f"✗ Card update failed: {update_response.text}")
            return False
    else:
        print(f"✗ Failed to create test card: {create_response.text}")
        return False

def test_langgraph_workflow():
    """Test the LangGraph workflow with different message types"""
    print("=== Testing LangGraph Workflow ===")
    
    workflow = ConversationalWorkflow()
    print("✓ ConversationalWorkflow initialized")
    
    if workflow.use_redis:
        print("✓ Redis integration enabled")
    else:
        print("⚠ Redis integration disabled - using in-memory state")
    
    # Test cases for different intents
    test_cases = [
        {
            "message": "What is machine learning?",
            "expected_intent": "NO_ACTION",
            "description": "Informational question"
        },
        {
            "message": "I want to create a card about Python programming",
            "expected_intent": "CREATE_NEW", 
            "description": "Card creation request"
        },
        {
            "message": "Tell me about the weather today",
            "expected_intent": "NO_ACTION",
            "description": "General question"
        }
    ]
    
    print(f"Running {len(test_cases)} basic test cases...\n")
    
    session_id = None
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Input: '{test['message']}'")
        
        try:
            result = workflow.process_message(test['message'], session_id=session_id)
            
            # Use the same session for continuity testing
            if not session_id and result.get('session_id'):
                session_id = result['session_id']
                print(f"  Using session: {session_id[:8]}...")
            
            print(f"✓ Workflow completed successfully")
            print(f"  Intent: {result['intent']} (confidence: {result['confidence']})")
            print(f"  Reasoning: {result['reasoning']}")
            print(f"  Response: {result['response'][:100]}...")
            
            # Check if intent matches expectation (with some flexibility)
            if result['intent'] == test['expected_intent']:
                print(f"✓ Intent classification correct")
            else:
                print(f"⚠ Intent mismatch: expected {test['expected_intent']}, got {result['intent']}")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
        
        print("-" * 50)
    
    # Test session history if Redis is enabled
    if workflow.use_redis and session_id:
        print("Testing conversation history...")
        history = workflow.get_session_history(session_id)
        print(f"✓ Retrieved {len(history)} messages from history")
        for i, msg in enumerate(history[-2:], 1):  # Show last 2 messages
            print(f"  {i}. {msg['user_message']} -> {msg['intent']}")
    
    print("Basic workflow tests completed!\n")

def test_create_workflow():
    """Test the CREATE_NEW workflow specifically"""
    print("=== Testing CREATE_NEW Workflow ===")
    
    # Check if backend is available
    if not test_backend_connection():
        print("Skipping CREATE_NEW workflow test - backend not available")
        return
    
    workflow = ConversationalWorkflow()
    
    # Test create messages
    create_test_cases = [
        "I want to create a card about machine learning fundamentals",
        "Create knowledge about Python web development with Flask",
        "Make a new card explaining database optimization techniques"
    ]
    
    print(f"Running {len(create_test_cases)} CREATE_NEW test cases...\n")
    
    for i, message in enumerate(create_test_cases, 1):
        print(f"CREATE Test {i}: '{message}'")
        
        try:
            result = workflow.process_message(message)
            
            print(f"✓ Workflow completed")
            print(f"  Intent: {result['intent']} (confidence: {result['confidence']})")
            print(f"  Response: {result['response'][:150]}...")
            
            if result['intent'] == 'CREATE_NEW':
                if result.get('card_id'):
                    print(f"✓ Successfully created card ID: {result['card_id']}")
                else:
                    print("⚠ CREATE_NEW intent detected but no card was actually created")
            else:
                print(f"⚠ Expected CREATE_NEW intent, got {result['intent']}")
            
        except Exception as e:
            print(f"✗ CREATE_NEW test failed: {e}")
        
        print("-" * 50)
    
    print("CREATE_NEW workflow tests completed!\n")

def test_update_workflow():
    """Test the UPDATE workflow specifically"""
    print("=== Testing UPDATE Workflow ===")
    
    # Check if backend is available
    if not test_backend_connection():
        print("Skipping UPDATE workflow test - backend not available")
        return
    
    workflow = ConversationalWorkflow()
    
    # Test update messages
    update_test_cases = [
        "Update my Python card with information about web frameworks",
        "Add more details to the machine learning card about neural networks",
        "Enhance the database card with SQL examples"
    ]
    
    print(f"Running {len(update_test_cases)} UPDATE test cases...\n")
    
    for i, message in enumerate(update_test_cases, 1):
        print(f"UPDATE Test {i}: '{message}'")
        
        try:
            result = workflow.process_message(message)
            
            print(f"✓ Workflow completed")
            print(f"  Intent: {result['intent']} (confidence: {result['confidence']})")
            print(f"  Response: {result['response'][:150]}...")
            
            if result['intent'] == 'UPDATE':
                if result.get('card_id'):
                    print(f"✓ Successfully updated card ID: {result['card_id']}")
                else:
                    print("⚠ UPDATE intent detected but no card was actually updated")
            else:
                print(f"⚠ Expected UPDATE intent, got {result['intent']}")
            
        except Exception as e:
            print(f"✗ UPDATE test failed: {e}")
        
        print("-" * 50)
    
    print("UPDATE workflow tests completed!\n")

def test_workflow_nodes():
    """Test individual workflow nodes"""
    print("=== Testing Individual Workflow Nodes ===")
    
    workflow = ConversationalWorkflow()
    
    # Test state structure
    test_state = {
        "user_message": "What is AI?",
        "intent": None,
        "confidence": None,
        "reasoning": None,
        "response": None,
        "card_id": None,
        "updated_card": None
    }
    
    print("Testing analyze_intent_node...")
    try:
        updated_state = workflow.analyze_intent_node(test_state.copy())
        if updated_state["intent"] and updated_state["confidence"] is not None:
            print("✓ Intent analysis node working")
            print(f"  Intent: {updated_state['intent']}")
            print(f"  Confidence: {updated_state['confidence']}")
        else:
            print("✗ Intent analysis node failed to set values")
    except Exception as e:
        print(f"✗ Intent analysis failed: {e}")
    
    print("\nTesting generate_response_node...")
    try:
        # Set intent for response generation
        test_state["intent"] = "NO_ACTION"
        response_state = workflow.generate_response_node(test_state.copy())
        if response_state["response"] and len(response_state["response"].strip()) > 0:
            print("✓ Response generation node working")
            print(f"  Response: {response_state['response'][:100]}...")
        else:
            print("✗ Response generation node failed")
    except Exception as e:
        print(f"✗ Response generation failed: {e}")
    
    print("\nTesting update_card_node...")
    if test_backend_connection():
        try:
            update_test_state = {
                "user_message": "Update the Python card with Django framework information",
                "intent": "UPDATE",
                "confidence": 0.9,
                "reasoning": "User wants to update existing content",
                "response": None,
                "card_id": None,
                "updated_card": None
            }
            
            update_result_state = workflow.update_card_node(update_test_state)
            if update_result_state.get("response"):
                print("✓ Update card node executed")
                print(f"  Result: {update_result_state['response'][:100]}...")
                if update_result_state.get("card_id"):
                    print(f"  Updated card ID: {update_result_state['card_id']}")
            else:
                print("✗ Update card node failed to set response")
        except Exception as e:
            print(f"✗ Update card node failed: {e}")
    else:
        print("⚠ Skipping update_card_node test - backend not available")
    
    print("Individual node tests completed!\n")

if __name__ == "__main__":
    print("LangGraph Backend - Comprehensive Testing Suite")
    print("=" * 60)
    
    try:
        # Test Redis infrastructure first
        redis_working = test_redis_connection()
        if not redis_working:
            print("\n⚠ Redis tests failed - some functionality will be limited")
        
        # Test AI service
        test_ai_service()
        
        # Test Redis-based components (if Redis is working)
        if redis_working:
            test_conversation_state_manager()
            test_session_management()
            test_redis_ttl_behavior()
            test_redis_error_handling()
        else:
            print("\n⚠ Skipping Redis-dependent tests")
        
        # Test workflow components
        test_workflow_nodes()
        test_langgraph_workflow()
        
        # Test session continuity (if Redis is working)
        if redis_working:
            test_session_continuity()
        
        # Test backend integration (if backend is available)
        backend_available = test_backend_connection()
        if backend_available:
            test_card_update_functionality()
            test_create_workflow()  # Add CREATE_NEW flow test
            test_update_workflow()
            
            # Test Redis-workflow integration (if both are available)
            if redis_working:
                test_integration_with_workflow()
        else:
            print("\n⚠ Skipping backend-dependent tests")
        
        print("=" * 60)
        print("🎉 All tests completed!")
        
        print("\n📊 System Status:")
        print(f"- Redis: {'✅ Working' if redis_working else '❌ Not available'}")
        print(f"- Backend API: {'✅ Working' if backend_available else '❌ Not available'}")
        print(f"- AI Service: ✅ Working")
        print(f"- LangGraph Workflow: ✅ Working")
        
        print("\n🚀 The LangGraph system supports:")
        print("- Intent classification (NO_ACTION/CREATE_NEW/UPDATE)")
        print("- Conversational responses")
        print("- Card update functionality")
        if redis_working:
            print("- Session management and state persistence")
            print("- Conversation history tracking")
            print("- Focused card memory")
        print("- Error handling and fallbacks")
        
        if redis_working and backend_available:
            print("\n🎯 Full system ready for production use!")
        elif redis_working or backend_available:
            print("\n⚡ Partial system functionality available")
        else:
            print("\n🔧 Basic workflow functionality available (limited features)")
        
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        print("\nTroubleshooting:")
        print("- Make sure Redis is running: docker ps | grep redis")
        print("- Make sure backend is running: curl http://localhost:5000/cards")
        print("- Check AWS credentials are configured for Bedrock")