from flask import Flask, request, jsonify
from flask_cors import CORS
from app import ConversationalWorkflow
import json
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize the LangGraph workflow
workflow = ConversationalWorkflow()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "LangGraph Backend",
        "redis_enabled": workflow.use_redis,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for processing user messages"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'message' field"
            }), 400
        
        user_message = data['message']
        session_id = data.get('session_id')  # Optional session ID for continuity
        focused_card = data.get('focused_card')  # Optional focused card context
        
        # If a focused card is provided and we have Redis, set it in the session before processing
        if focused_card and workflow.use_redis:
            if session_id:
                # Set focused card for existing session
                workflow.set_focused_card(session_id, focused_card)
                print(f"🎯 Set focused card for session {session_id[:8]}...: {focused_card.get('title', 'Untitled')}")
            else:
                # For new sessions, we'll handle this in the process_message method
                print(f"🎯 Focused card provided for new session: {focused_card.get('title', 'Untitled')}")
        
        # Process the message through LangGraph workflow, passing the focused card
        result = workflow.process_message(user_message, session_id, focused_card)
        
        return jsonify({
            "success": True,
            "data": {
                "message": result["user_message"],
                "response": result["response"],
                "intent": result["intent"],
                "confidence": result["confidence"],
                "reasoning": result["reasoning"],
                "session_id": result["session_id"],
                "card_id": result.get("card_id"),
                "updated_card": result.get("updated_card"),
                "focused_card": result.get("focused_card"),
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """Get conversation history for a session"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        if not workflow.use_redis:
            return jsonify({
                "success": False,
                "error": "Session history requires Redis to be enabled"
            }), 400
        
        history = workflow.get_session_history(session_id, limit)
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "history": history,
                "count": len(history)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/sessions/<session_id>/focused-card', methods=['POST'])
def set_focused_card(session_id):
    """Set a focused card for the session"""
    try:
        data = request.get_json()
        
        if not data or 'card' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'card' field"
            }), 400
        
        card_data = data['card']
        
        # Validate card data
        required_fields = ['id', 'title']
        for field in required_fields:
            if field not in card_data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field '{field}' in card data"
                }), 400
        
        success = workflow.set_focused_card(session_id, card_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Focused card set successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to set focused card"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/sessions/<session_id>/focused-card', methods=['DELETE'])
def clear_focused_card(session_id):
    """Clear the focused card for a session"""
    try:
        success = workflow.clear_focused_card(session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Focused card cleared successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to clear focused card"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/sessions/active', methods=['GET'])
def get_active_sessions():
    """Get list of active sessions"""
    try:
        if not workflow.use_redis or not workflow.state_manager:
            return jsonify({
                "success": False,
                "error": "Session management requires Redis to be enabled"
            }), 400
        
        active_sessions = workflow.state_manager.get_active_sessions()
        
        # Get session info for each active session
        session_details = []
        for session_id in active_sessions:
            session_info = workflow.state_manager.get_session_info(session_id)
            if session_info:
                session_details.append(session_info)
        
        return jsonify({
            "success": True,
            "data": {
                "active_sessions": session_details,
                "count": len(session_details)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/workflow/intents', methods=['GET'])
def get_supported_intents():
    """Get list of supported workflow intents"""
    return jsonify({
        "success": True,
        "data": {
            "intents": [
                {
                    "name": "NO_ACTION",
                    "description": "Informational questions that don't require card operations"
                },
                {
                    "name": "CREATE_NEW",
                    "description": "User wants to create a new knowledge card"
                },
                {
                    "name": "UPDATE",
                    "description": "User wants to update an existing knowledge card"
                }
            ]
        }
    })

@app.route('/workflow/status', methods=['GET'])
def get_workflow_status():
    """Get workflow system status"""
    return jsonify({
        "success": True,
        "data": {
            "workflow_initialized": workflow is not None,
            "redis_enabled": workflow.use_redis,
            "backend_url": workflow.backend_url,
            "ai_service_model": workflow.ai_service.llm_model,
            "supported_flows": ["NO_ACTION", "CREATE_NEW", "UPDATE"],
            "features": {
                "session_management": workflow.use_redis,
                "conversation_history": workflow.use_redis,
                "focused_card_memory": workflow.use_redis,
                "card_creation": True,
                "card_updates": True,
                "intent_analysis": True
            }
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    print("🚀 Starting LangGraph Backend Server...")
    print(f"✓ Redis enabled: {workflow.use_redis}")
    print(f"✓ Backend URL: {workflow.backend_url}")
    print(f"✓ AI Model: {workflow.ai_service.llm_model}")
    print("🌐 Server will be available at: http://localhost:8000")
    print("\n📋 Available Endpoints:")
    print("  GET  /health                           - Health check")
    print("  POST /chat                            - Process chat messages")
    print("  GET  /sessions/<id>/history           - Get conversation history")
    print("  POST /sessions/<id>/focused-card      - Set focused card")
    print("  DEL  /sessions/<id>/focused-card      - Clear focused card")
    print("  GET  /sessions/active                 - Get active sessions")
    print("  GET  /workflow/intents               - Get supported intents")
    print("  GET  /workflow/status                - Get workflow status")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
