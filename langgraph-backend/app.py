from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from ai_service import AIService
from database import create_database_manager, ConversationStateManager
import json
import requests
import uuid

# Define the state structure
class ConversationState(TypedDict):
    user_message: str
    session_id: Optional[str]
    intent: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]
    response: Optional[str]
    card_id: Optional[int]
    updated_card: Optional[dict]
    focused_card: Optional[dict]

class ConversationalWorkflow:
    def __init__(self, backend_url="http://backend-service:5000", use_redis=True):
        self.ai_service = AIService()
        self.backend_url = backend_url
        self.use_redis = use_redis
        
        # Initialize Redis state manager if enabled
        self.state_manager = None
        if use_redis:
            try:
                self.state_manager = create_database_manager()
                print("✓ Redis state management enabled")
            except Exception as e:
                print(f"⚠ Redis unavailable, using in-memory state: {e}")
                self.use_redis = False
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("load_session", self.load_session_node)
        workflow.add_node("analyze_intent", self.analyze_intent_node)
        workflow.add_node("generate_response", self.generate_response_node)
        workflow.add_node("create_card", self.create_card_node)
        workflow.add_node("update_card", self.update_card_node)
        workflow.add_node("save_session", self.save_session_node)
        
        # Define the flow
        workflow.set_entry_point("load_session")
        
        # After loading session, analyze intent
        workflow.add_edge("load_session", "analyze_intent")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "analyze_intent",
            self.route_based_on_intent,
            {
                "NO_ACTION": "generate_response",
                "CREATE_NEW": "create_card",        # Route to create node
                "UPDATE": "update_card"             # Route to update node
            }
        )
        
        # After creating or updating, generate response
        workflow.add_edge("create_card", "generate_response")
        workflow.add_edge("update_card", "generate_response")
        
        # After generating response, save session
        workflow.add_edge("generate_response", "save_session")
        
        # End after saving session
        workflow.add_edge("save_session", END)
        
        return workflow.compile()
    
    def load_session_node(self, state: ConversationState) -> ConversationState:
        """Load session context and focused card from Redis"""
        session_id = state.get("session_id")
        focused_card_from_request = state.get("focused_card")  # From process_message parameter
        
        if not self.use_redis or not session_id:
            # Create new session if none provided
            if self.use_redis and self.state_manager:
                new_session_id = self.state_manager.create_new_session()
                state["session_id"] = new_session_id
                print(f"Created new session: {new_session_id[:8]}...")
                
                # If focused card was provided in request, save it to the new session
                if focused_card_from_request:
                    self.state_manager.save_focused_card(new_session_id, focused_card_from_request)
                    print(f"✓ Set focused card for new session: {focused_card_from_request.get('title', 'Untitled')}")
            return state
        
        print(f"Loading session: {session_id[:8]}...")
        
        # Load previous conversation state
        previous_state = self.state_manager.load_conversation_state(session_id)
        if previous_state:
            print(f"✓ Loaded previous conversation state")
            # Merge relevant fields from previous state, but don't override focused_card from request
            if "focused_card" in previous_state and not focused_card_from_request:
                state["focused_card"] = previous_state["focused_card"]
        
        # Load focused card from Redis (unless we have one from the request)
        if not focused_card_from_request:
            focused_card = self.state_manager.load_focused_card(session_id)
            if focused_card:
                state["focused_card"] = focused_card
                print(f"✓ Loaded focused card from Redis: {focused_card.get('title', 'Untitled')}")
            else:
                print("⚠ No focused card found in session")
        else:
            # Update Redis with the focused card from the request
            self.state_manager.save_focused_card(session_id, focused_card_from_request)
            print(f"✓ Updated focused card from request: {focused_card_from_request.get('title', 'Untitled')}")
        
        # Update session activity
        self.state_manager.update_session_activity(session_id)
        
        return state
    
    def save_session_node(self, state: ConversationState) -> ConversationState:
        """Save conversation state and history to Redis"""
        if not self.use_redis or not state.get("session_id"):
            return state
        
        session_id = state["session_id"]
        
        # Save conversation state
        conversation_state = {
            "intent": state.get("intent"),
            "confidence": state.get("confidence"),
            "reasoning": state.get("reasoning"),
            "focused_card": state.get("focused_card"),
            "last_message": state.get("user_message")
        }
        
        self.state_manager.save_conversation_state(session_id, conversation_state)
        
        # Add message to history
        message_entry = {
            "user_message": state["user_message"],
            "intent": state.get("intent"),
            "confidence": state.get("confidence"),
            "response": state.get("response"),
            "card_id": state.get("card_id")
        }
        
        self.state_manager.add_message_to_history(session_id, message_entry)
        
        # Update focused card if we updated one
        if state.get("updated_card"):
            focused_card_data = {
                "id": state["updated_card"]["id"],
                "title": state["updated_card"]["title"],
                "content": state["updated_card"]["content"][:200] + "..." if len(state["updated_card"]["content"]) > 200 else state["updated_card"]["content"]
            }
            self.state_manager.save_focused_card(session_id, focused_card_data)
        
        print(f"✓ Session state saved: {session_id[:8]}...")
        return state
    
    def analyze_intent_node(self, state: ConversationState) -> ConversationState:
        """Analyze the user's intent with focused card context"""
        user_message = state["user_message"]
        focused_card = state.get("focused_card")
        
        # Build context for intent analysis
        context = ""
        if focused_card:
            context = f"""
Currently focused card:
Title: {focused_card.get('title', 'Untitled')}
Content: {focused_card.get('content', 'No content')[:150]}...
"""
        
        # Enhanced prompt with context
        prompt = f"""Analyze this user message and determine their intent. Consider the context of any focused card.

Classification categories:
1. NO_ACTION - User is asking a question or wants information (no card changes needed)
2. CREATE_NEW - User wants to create a new knowledge card
3. UPDATE - User wants to modify/update the currently focused card or existing content

{context}
User message: "{user_message}"

Respond with ONLY a JSON object:
{{
  "action": "NO_ACTION|CREATE_NEW|UPDATE",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation considering focused card context"
}}"""

        response = self.ai_service.generate_text(prompt, max_tokens=200)
        
        try:
            result = json.loads(response)
            state["intent"] = result.get("action", "NO_ACTION")
            state["confidence"] = result.get("confidence", 0.5)
            state["reasoning"] = result.get("reasoning", "Analysis completed")
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            state["intent"] = "NO_ACTION"
            state["confidence"] = 0.5
            state["reasoning"] = "Failed to parse intent analysis"
        
        print(f"Intent: {state['intent']} (confidence: {state['confidence']})")
        print(f"Reasoning: {state['reasoning']}")
        
        return state
    
    def create_card_node(self, state: ConversationState) -> ConversationState:
        """Create a new knowledge card based on user input"""
        user_message = state["user_message"]
        
        try:
            # Use AI to extract title and content for the new card
            extraction_prompt = f"""Based on the user's message, create a structured knowledge card.

User message: "{user_message}"

Extract or generate:
1. A clear, descriptive title for the knowledge card
2. Well-structured content that captures the key information
3. Make the content informative and useful for future reference

Respond with ONLY a JSON object:
{{
  "title": "Clear, descriptive title",
  "content": "Well-structured content with key information, examples, and details",
  "category": "Suggested category (optional)",
  "tags": ["relevant", "tags", "for", "searchability"]
}}"""

            extraction_response = self.ai_service.generate_text(extraction_prompt, max_tokens=600)
            
            try:
                card_data = json.loads(extraction_response)
                title = card_data.get("title", "New Knowledge Card")
                content = card_data.get("content", user_message)
                
                # Format content with HTML structure for the backend
                formatted_content = f"<h3 class='card-heading'>{title}</h3><p class='card-description'>{content}</p>"
                
                # Prepare data for backend API
                create_data = {
                    "text": content,
                    "title": title
                }
                
                # Add metadata about the creation
                if card_data.get("category") or card_data.get("tags"):
                    create_data["metadata"] = {
                        "created_by": "langgraph_conversation",
                        "source_message": user_message,
                        "category": card_data.get("category"),
                        "tags": card_data.get("tags", [])
                    }
                
                # Make the creation request
                create_response = requests.post(
                    f"{self.backend_url}/add-text",
                    json=create_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if create_response.status_code == 200:
                    creation_result = create_response.json()
                    card_id = creation_result.get("card_id")
                    
                    state["card_id"] = card_id
                    state["response"] = f"✅ Successfully created new knowledge card: '{title}' (ID: {card_id})"
                    
                    # Set the created card as focused for the session
                    if self.use_redis and state.get("session_id"):
                        focused_card_data = {
                            "id": card_id,
                            "title": title,
                            "content": content[:200] + "..." if len(content) > 200 else content
                        }
                        if self.state_manager:
                            self.state_manager.save_focused_card(state["session_id"], focused_card_data)
                            print(f"✓ Set new card as focused: {title}")
                    
                else:
                    state["response"] = f"Failed to create card: {create_response.text}"
                    
            except json.JSONDecodeError:
                # Fallback: create with basic info
                title = f"Knowledge from conversation"
                create_data = {
                    "text": user_message,
                    "title": title
                }
                
                create_response = requests.post(
                    f"{self.backend_url}/add-text",
                    json=create_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if create_response.status_code == 200:
                    creation_result = create_response.json()
                    card_id = creation_result.get("card_id")
                    state["card_id"] = card_id
                    state["response"] = f"✅ Created knowledge card from your message (ID: {card_id})"
                else:
                    state["response"] = "I had trouble structuring the information for a new card."
                
        except requests.RequestException as e:
            state["response"] = f"Error connecting to the backend: {str(e)}"
        
        return state
    
    def update_card_node(self, state: ConversationState) -> ConversationState:
        """Update an existing card based on user input"""
        user_message = state["user_message"]
        
        try:
            # First, get all cards to find the most relevant one to update
            cards_response = requests.get(f"{self.backend_url}/cards")
            
            if cards_response.status_code != 200:
                state["response"] = "Sorry, I couldn't retrieve the existing cards to update."
                return state
            
            cards_data = cards_response.json()
            if not cards_data.get("success") or not cards_data.get("cards"):
                state["response"] = "No existing cards found to update."
                return state
            
            cards = cards_data["cards"]
            
            # Use AI to determine which card to update and how
            selection_prompt = f"""Based on the user's message, select which card should be updated and suggest the changes.

User message: "{user_message}"

Available cards:
{self._format_cards_for_selection(cards[:5])}  # Show top 5 cards

Respond with ONLY a JSON object:
{{
  "selected_card_id": card_id_number,
  "reasoning": "why this card was selected",
  "suggested_title": "new title or null if no change",
  "suggested_content": "enhanced content that incorporates the user's input",
  "update_summary": "brief description of what was changed"
}}"""

            selection_response = self.ai_service.generate_text(selection_prompt, max_tokens=800)
            
            try:
                update_plan = json.loads(selection_response)
                card_id = update_plan.get("selected_card_id")
                
                if not card_id:
                    state["response"] = "I couldn't determine which card to update based on your message."
                    return state
                
                # Prepare update data
                update_data = {}
                if update_plan.get("suggested_title"):
                    update_data["title"] = update_plan["suggested_title"]
                if update_plan.get("suggested_content"):
                    update_data["content"] = update_plan["suggested_content"]
                
                # Add metadata about the update
                update_data["metadata"] = {
                    "updated_by": "langgraph_conversation",
                    "update_reason": update_plan.get("update_summary", "Updated via conversation"),
                    "original_message": user_message
                }
                
                # Make the update request
                update_response = requests.put(
                    f"{self.backend_url}/cards/{card_id}",
                    json=update_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if update_response.status_code == 200:
                    update_result = update_response.json()
                    state["card_id"] = card_id
                    state["updated_card"] = update_result.get("updated_card")
                    state["response"] = f"✅ Successfully updated card: {update_plan.get('update_summary', 'Card updated')}"
                else:
                    state["response"] = f"Failed to update card: {update_response.text}"
                    
            except json.JSONDecodeError:
                state["response"] = "I had trouble understanding how to update the cards based on your message."
                
        except requests.RequestException as e:
            state["response"] = f"Error connecting to the backend: {str(e)}"
        
        return state
    
    def _format_cards_for_selection(self, cards: list) -> str:
        """Format cards for AI selection prompt"""
        formatted = []
        for card in cards:
            content_preview = card.get("content", "")[:150] + "..." if len(card.get("content", "")) > 150 else card.get("content", "")
            formatted.append(f"ID: {card['id']}\nTitle: {card['title']}\nContent: {content_preview}\n")
        return "\n".join(formatted)
    
    def route_based_on_intent(self, state: ConversationState) -> str:
        """Route to the next node based on intent"""
        intent = state.get("intent", "NO_ACTION")
        print(f"Routing to: {intent}")
        return intent
    
    def generate_response_node(self, state: ConversationState) -> ConversationState:
        """Generate a conversational response"""
        user_message = state["user_message"]
        intent = state.get("intent", "NO_ACTION")
        
        # If we just created a card, provide a confirmation response
        if intent == "CREATE_NEW" and state.get("card_id"):
            card_id = state.get("card_id")
            prompt = f"""The user requested to create new knowledge: "{user_message}"

A new knowledge card was successfully created with ID: {card_id}

Generate a helpful response that:
1. Confirms the card creation was successful
2. Mentions the card ID for reference
3. Is conversational and encouraging
4. Suggests they can ask questions about it or update it later

Keep it concise and positive."""
        
        # If we just updated a card, provide a summary response
        elif intent == "UPDATE" and state.get("updated_card"):
            updated_card = state["updated_card"]
            prompt = f"""The user requested an update: "{user_message}"

A card was successfully updated:
- Card ID: {state.get('card_id')}
- Title: {updated_card.get('title')}
- Content length: {len(updated_card.get('content', ''))} characters

Generate a helpful response that:
1. Confirms the update was successful
2. Briefly mentions what was changed
3. Is conversational and friendly

Keep it concise and positive."""
        
        # Different response styles based on intent
        elif intent == "NO_ACTION":
            focused_card = state.get("focused_card")
            if focused_card:
                print(f"🎯 Using focused card context: {focused_card.get('title', 'Untitled')}")
                # User is asking about information with a focused card context
                prompt = f"""You are a helpful AI assistant. The user asked: "{user_message}"

The user is currently viewing this knowledge card:
Title: {focused_card.get('title', 'Untitled')}
Content: {focused_card.get('content', 'No content')[:500]}...

This appears to be an informational question. If their question relates to the focused card, use that context to provide a more relevant response. If it's unrelated, provide a general helpful response.

Keep it concise and informative."""
            else:
                print("ℹ️ No focused card context available")
                # Standard informational response without card context
                prompt = f"""You are a helpful AI assistant. The user asked: "{user_message}"

This appears to be an informational question. Provide a helpful, conversational response.
Keep it concise and informative."""
            
        elif intent == "CREATE_NEW" and not state.get("card_id"):
            # Create was attempted but failed
            if state.get("response"):
                # Use the error message from create_card_node
                return state
            else:
                prompt = f"""The user wants to create new knowledge: "{user_message}"

There was an issue with the creation process. Provide a helpful message explaining that the card couldn't be created and suggest they try again with more specific information.

Keep it conversational and supportive."""
            
        elif intent == "UPDATE" and not state.get("updated_card"):
            # Update was attempted but failed
            if state.get("response"):
                # Use the error message from update_card_node
                return state
            else:
                prompt = f"""The user wants to update existing knowledge: "{user_message}"

There was an issue with the update process. Provide a helpful message explaining that the update couldn't be completed and suggest they try again or be more specific about what they want to update.

Keep it conversational and helpful."""
        
        else:
            prompt = f"""Respond helpfully to: "{user_message}"
            
Keep it conversational and concise."""
        
        response = self.ai_service.generate_text(prompt, max_tokens=300)
        state["response"] = response
        
        return state
    
    def process_message(self, user_message: str, session_id: Optional[str] = None, focused_card: Optional[dict] = None) -> dict:
        """Process a user message through the workflow with session management"""
        initial_state = {
            "user_message": user_message,
            "session_id": session_id,
            "intent": None,
            "confidence": None,
            "reasoning": None,
            "response": None,
            "card_id": None,
            "updated_card": None,
            "focused_card": focused_card  # Set focused card from parameter
        }
        
        print(f"\n=== Processing: '{user_message}' ===")
        if session_id:
            print(f"Session: {session_id[:8]}...")
        if focused_card:
            print(f"Focused card: {focused_card.get('title', 'Untitled')}")
        
        # Run the workflow
        final_state = self.graph.invoke(initial_state)
        
        return {
            "user_message": final_state["user_message"],
            "session_id": final_state.get("session_id"),
            "intent": final_state["intent"],
            "confidence": final_state["confidence"],
            "reasoning": final_state["reasoning"],
            "response": final_state["response"],
            "card_id": final_state.get("card_id"),
            "updated_card": final_state.get("updated_card"),
            "focused_card": final_state.get("focused_card")
        }
    
    def get_session_history(self, session_id: str, limit: int = 10) -> list:
        """Get conversation history for a session"""
        if not self.use_redis or not self.state_manager:
            return []
        
        return self.state_manager.get_conversation_history(session_id, limit)
    
    def set_focused_card(self, session_id: str, card_data: dict) -> bool:
        """Set the focused card for a session"""
        if not self.use_redis or not self.state_manager:
            return False
        
        return self.state_manager.save_focused_card(session_id, card_data)
    
    def clear_focused_card(self, session_id: str) -> bool:
        """Clear the focused card for a session"""
        if not self.use_redis or not self.state_manager:
            return False
        
        return self.state_manager.clear_focused_card(session_id)

# Test the workflow
if __name__ == "__main__":
    workflow = ConversationalWorkflow()
    
    # Test basic workflow
    print("Testing basic workflow...")
    result1 = workflow.process_message("What is machine learning?")
    print(f"Response: {result1['response'][:100]}...")
    
    # Test with session continuity
    if workflow.use_redis:
        print("\nTesting session continuity...")
        session_id = result1.get("session_id")
        
        # Continue conversation in same session
        result2 = workflow.process_message(
            "Create a card about neural networks", 
            session_id=session_id
        )
        print(f"Response: {result2['response'][:100]}...")
        
        # Get conversation history
        history = workflow.get_session_history(session_id)
        print(f"\nConversation history: {len(history)} messages")
        for i, msg in enumerate(history, 1):
            print(f"{i}. {msg['user_message']} -> {msg['intent']}")
    else:
        print("Redis not available - testing without session persistence")
        result2 = workflow.process_message("Create a card about neural networks")
        print(f"Response: {result2['response'][:100]}...")
    
    print("\n" + "="*60)