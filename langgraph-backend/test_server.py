#!/usr/bin/env python3
"""
Quick test script for the LangGraph Flask server
"""

import requests
import json

SERVER_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_chat_endpoint():
    """Test the main chat endpoint"""
    print("\n🔍 Testing chat endpoint...")
    
    test_messages = [
        "What is machine learning?",
        "Create a card about Python programming",
        "Update my Python card with web frameworks"
    ]
    
    session_id = None
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test Message {i}: {message} ---")
        
        payload = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        
        try:
            response = requests.post(
                f"{SERVER_URL}/chat",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    result = data["data"]
                    session_id = result["session_id"]  # Use same session for continuity
                    
                    print(f"✅ Intent: {result['intent']} (confidence: {result['confidence']})")
                    print(f"📝 Response: {result['response'][:100]}...")
                    if result.get('card_id'):
                        print(f"🆔 Card ID: {result['card_id']}")
                else:
                    print(f"❌ Chat failed: {data['error']}")
            else:
                print(f"❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def test_workflow_status():
    """Test the workflow status endpoint"""
    print("\n🔍 Testing workflow status...")
    try:
        response = requests.get(f"{SERVER_URL}/workflow/status")
        if response.status_code == 200:
            print("✅ Workflow status retrieved:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status request failed: {e}")

def main():
    print("🚀 LangGraph Flask Server Test Suite")
    print("="*50)
    
    # Test basic connectivity first
    if not test_health_check():
        print("❌ Server is not responding. Make sure it's running on port 8000")
        return
    
    # Test main functionality
    test_chat_endpoint()
    test_workflow_status()
    
    print("\n" + "="*50)
    print("✅ Test suite completed!")
    print("\n💡 Frontend Integration Notes:")
    print("- Main chat endpoint: POST /chat")
    print("- Expected payload: {message: string, session_id?: string}")
    print("- Response includes: intent, response, session_id, card_id, etc.")
    print("- Session continuity supported via session_id")
    print("- CORS enabled for React frontend")

if __name__ == "__main__":
    main()
