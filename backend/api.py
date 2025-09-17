from flask import Flask, request, jsonify
from flask_cors import CORS
from crud import Database
from ai_service import AIService
import json

app = Flask(__name__)
CORS(app)

class TemporalAPI:
    def __init__(self):
        self.db = Database()
        self.ai_service = AIService()
    
    def add_and_process_text(self, text_input, title=None, metadata=None, context_limit=5):
        try:
            similar_cards = self.db.vector_search(text_input, limit=context_limit)
            context_text = self._build_context_from_cards(similar_cards)
            prompt = self._create_enhanced_prompt(text_input, context_text)
            ai_response = self.ai_service.generate_text(prompt, max_tokens=1000)
            card_title = title or self._generate_card_title(ai_response, text_input)
            card_metadata = metadata or {
                "type": "knowledge_card",
                "processed": True,
                "similar_cards_referenced": len(similar_cards),
                "original_input_length": len(text_input)
            }
            
            card_id = self.db.add_card(
                title=card_title,
                content=ai_response,
                metadata=card_metadata
            )
            
            return {
                "success": True,
                "card_id": card_id,
                "original_input": text_input,
                "knowledge_card_content": ai_response,
                "similar_cards_found": len(similar_cards),
                "context_used": context_text,
                "card_title": card_title
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_card_title(self, knowledge_card_content, original_input):
        """Extract title from HTML-formatted knowledge card content"""
        import re
        
        # Try to extract title from <h3 class='card-heading'> tag
        heading_match = re.search(r"<h3 class='card-heading'>(.*?)</h3>", knowledge_card_content, re.IGNORECASE | re.DOTALL)
        if heading_match:
            title = heading_match.group(1).strip()
            if len(title) > 60:
                return f"{title[:57]}..."
            return title
        
        # Fallback to original logic
        lines = knowledge_card_content.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not any(tag in line.lower() for tag in ['<h3', '<h4', '<p', '<div']):
                if len(line) > 60:
                    return f"{line[:57]}..."
                else:
                    return line
        
        return f"Knowledge from: {original_input[:40]}..."

    def _build_context_from_cards(self, cards):
        if not cards:
            return "No similar content found in database."
        
        context_parts = []
        for i, card in enumerate(cards, 1):
            context_parts.append(f"Context {i}:")
            context_parts.append(f"Title: {card.title}")
            context_parts.append(f"Content: {card.content}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _create_enhanced_prompt(self, user_input, context):
        return f"""You are a knowledge card curator. Your job is to create concise, unique knowledge cards that build upon existing information without repeating it.

Create a knowledge card that follows this EXACT HTML template structure:

<h3 class='card-heading'>{{Main Topic or Key Concept}}</h3>
<h4 class='card-subheading'>{{Specific Focus or Application}}</h4>
<p class='card-description'>{{2-3 sentences explaining the NEW information, insights, or connections not covered in existing cards}}</p>
<div class='card-insights'>
<h5>Key Insights:</h5>
<ul>
<li>{{Novel insight 1}}</li>
<li>{{Novel insight 2}}</li>
<li>{{Novel insight 3 (if applicable)}}</li>
</ul>
</div>
<div class='card-meta'>
<span class='novelty-indicator'>{{High/Medium/Low}} Novelty</span>
</div>

Rules:
1. Extract ONLY NEW information not already covered in existing cards
2. Focus on what's unique or additive about this input
3. Keep each insight concise (1 sentence max)
4. If input largely duplicates existing knowledge, focus only on new nuances
5. Set novelty as High (completely new), Medium (some new aspects), or Low (minor additions)

New Input:
{user_input}

Existing Knowledge in Database:
{context}

Generate the HTML-formatted knowledge card:"""
# Initialize API instance
temporal_api = TemporalAPI()

@app.route('/add-text', methods=['POST'])
def add_text():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text_input = data['text']
        title = data.get('title')
        metadata = data.get('metadata')
        context_limit = data.get('context_limit', 5)
        
        result = temporal_api.add_and_process_text(
            text_input=text_input,
            title=title,
            metadata=metadata,
            context_limit=context_limit
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/knowledge-preview', methods=['POST'])
def preview_knowledge_card():
    """Preview what knowledge card would be created without actually saving it"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text_input = data['text']
        context_limit = data.get('context_limit', 5)
        
        similar_cards = temporal_api.db.vector_search(text_input, limit=context_limit)
        context_text = temporal_api._build_context_from_cards(similar_cards)
        prompt = temporal_api._create_enhanced_prompt(text_input, context_text)
        preview_content = temporal_api.ai_service.generate_text(prompt, max_tokens=1000)
        
        return jsonify({
            "success": True,
            "original_input": text_input,
            "knowledge_card_preview": preview_content,
            "similar_cards_count": len(similar_cards),
            "would_create_card": len(preview_content.strip()) > 50,  # Only create if substantial new content
            "similar_cards": [
                {
                    "id": card.id,
                    "title": card.title,
                    "content": card.content[:100] + "..." if len(card.content) > 100 else card.content
                }
                for card in similar_cards[:3]  # Show top 3 similar cards
            ]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cards', methods=['GET'])
def get_all_cards():
    try:
        cards = temporal_api.db.get_all_cards()
        
        results = []
        for card in cards:
            results.append({
                "id": card.id,
                "title": card.title,
                "content": card.content,
                "metadata": card.card_metadata,
                "created_at": card.created_at.isoformat()
            })
        
        return jsonify({
            "success": True,
            "cards": results,
            "count": len(results)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    try:
        # Check if card exists first
        card = temporal_api.db.get_card_by_id(card_id)
        if not card:
            return jsonify({
                "success": False,
                "error": f"Card with ID {card_id} not found"
            }), 404
        
        # Delete the card
        deleted = temporal_api.db.delete_card(card_id)
        
        if deleted:
            return jsonify({
                "success": True,
                "message": f"Card {card_id} deleted successfully",
                "deleted_card": {
                    "id": card.id,
                    "title": card.title
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to delete card with ID {card_id}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/cards/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Extract update fields
        title = data.get('title')
        content = data.get('content')
        metadata = data.get('metadata')
        
        # At least one field must be provided
        if title is None and content is None and metadata is None:
            return jsonify({
                "success": False,
                "error": "At least one field (title, content, or metadata) must be provided"
            }), 400
        
        # Update the card
        updated_card = temporal_api.db.update_card(card_id, title=title, content=content, metadata=metadata)
        
        if updated_card:
            return jsonify({
                "success": True,
                "message": f"Card {card_id} updated successfully",
                "updated_card": {
                    "id": updated_card.id,
                    "title": updated_card.title,
                    "content": updated_card.content,
                    "metadata": updated_card.card_metadata,
                    "created_at": updated_card.created_at.isoformat()
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"Card with ID {card_id} not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
