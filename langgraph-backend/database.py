import redis
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

class RedisManager:
    def __init__(self, host="langgraph-service", port=6379, db=0, decode_responses=True):
        """Initialize Redis connection"""
        self.host = host
        self.port = port
        self.db = db
        self.client = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            decode_responses=decode_responses
        )
        
        # Test connection
        try:
            self.client.ping()
            print(f"✓ Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            print(f"✗ Failed to connect to Redis: {e}")
            raise
    
    def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store JSON data in Redis with optional TTL"""
        try:
            json_data = json.dumps(value)
            if ttl:
                return self.client.setex(key, ttl, json_data)
            else:
                return self.client.set(key, json_data)
        except Exception as e:
            print(f"Error storing JSON data: {e}")
            return False
    
    def get_json(self, key: str, default: Any = None) -> Any:
        """Retrieve and parse JSON data from Redis"""
        try:
            data = self.client.get(key)
            if data is None:
                return default
            return json.loads(data)
        except Exception as e:
            print(f"Error retrieving JSON data: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Error deleting key: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Error checking key existence: {e}")
            return False

class ConversationStateManager:
    def __init__(self, redis_manager: RedisManager):
        """Initialize conversation state management"""
        self.redis = redis_manager
        self.session_ttl = 3600  # 1 hour session timeout
        self.history_ttl = 86400  # 24 hours history retention
    
    def save_conversation_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Save conversation state for a session"""
        key = f"conversation_state:{session_id}"
        
        # Add timestamp
        state_with_timestamp = {
            **state,
            "last_updated": datetime.now().isoformat(),
            "session_id": session_id
        }
        
        return self.redis.set_json(key, state_with_timestamp, ttl=self.session_ttl)
    
    def load_conversation_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state for a session"""
        key = f"conversation_state:{session_id}"
        return self.redis.get_json(key)
    
    def save_focused_card(self, session_id: str, card_data: Dict[str, Any]) -> bool:
        """Save the currently focused card for a session"""
        key = f"focused_card:{session_id}"
        
        focused_card_data = {
            **card_data,
            "focused_at": datetime.now().isoformat(),
            "session_id": session_id
        }
        
        return self.redis.set_json(key, focused_card_data, ttl=self.session_ttl)
    
    def load_focused_card(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load the currently focused card for a session"""
        key = f"focused_card:{session_id}"
        return self.redis.get_json(key)
    
    def clear_focused_card(self, session_id: str) -> bool:
        """Clear the focused card for a session"""
        key = f"focused_card:{session_id}"
        return self.redis.delete(key)
    
    def add_message_to_history(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Add a message to conversation history"""
        history_key = f"conversation_history:{session_id}"
        
        # Get existing history
        history = self.redis.get_json(history_key, [])
        
        # Add new message with timestamp
        message_with_timestamp = {
            **message,
            "timestamp": datetime.now().isoformat()
        }
        
        history.append(message_with_timestamp)
        
        # Keep only last 50 messages to prevent unlimited growth
        history = history[-50:]
        
        return self.redis.set_json(history_key, history, ttl=self.history_ttl)
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        history_key = f"conversation_history:{session_id}"
        history = self.redis.get_json(history_key, [])
        
        # Return the most recent messages
        return history[-limit:] if limit > 0 else history
    
    def clear_conversation_history(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        history_key = f"conversation_history:{session_id}"
        return self.redis.delete(history_key)
    
    def create_new_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session"""
        import uuid
        
        session_id = str(uuid.uuid4())
        
        # Initialize session data
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0
        }
        
        session_key = f"session:{session_id}"
        self.redis.set_json(session_key, session_data, ttl=self.session_ttl)
        
        return session_id
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update last activity timestamp for a session"""
        session_key = f"session:{session_id}"
        session_data = self.redis.get_json(session_key)
        
        if session_data:
            session_data["last_activity"] = datetime.now().isoformat()
            session_data["message_count"] = session_data.get("message_count", 0) + 1
            return self.redis.set_json(session_key, session_data, ttl=self.session_ttl)
        
        return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session_key = f"session:{session_id}"
        return self.redis.get_json(session_key)
    
    def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions and related data"""
        # This would typically be run as a background task
        # For now, just return 0 as Redis TTL handles expiration
        return 0
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        try:
            session_keys = self.redis.client.keys("session:*")
            return [key.split(":", 1)[1] for key in session_keys]
        except Exception as e:
            print(f"Error getting active sessions: {e}")
            return []

# Convenience function to create a database instance
def create_database_manager(host="localhost", port=6379, db=0) -> ConversationStateManager:
    """Create a conversation state manager with Redis backend"""
    redis_manager = RedisManager(host=host, port=port, db=db)
    return ConversationStateManager(redis_manager)
