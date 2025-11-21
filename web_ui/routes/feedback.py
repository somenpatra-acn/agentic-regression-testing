"""
Feedback Routes - API endpoints for feedback submission
"""

from flask import Blueprint, jsonify, request, current_app
from pathlib import Path
from datetime import datetime

from models.approval import Feedback
from utils.helpers import save_json, load_json
from utils.logger import get_logger

logger = get_logger(__name__)

feedback_bp = Blueprint('feedback', __name__)

# Feedback directory
FEEDBACK_DIR = Path("feedback")
FEEDBACK_DIR.mkdir(exist_ok=True)


@feedback_bp.route('/', methods=['POST'])
def submit_feedback():
    """Submit feedback on a test result or approval"""
    try:
        data = request.json or {}

        # Create feedback object
        feedback = Feedback(
            item_id=data.get('item_id'),
            item_type=data.get('item_type', 'test_result'),
            rating=data.get('rating'),
            comment=data.get('comment', ''),
            corrections=data.get('corrections'),
            is_false_positive=data.get('is_false_positive', False),
            is_false_negative=data.get('is_false_negative', False),
            is_known_issue=data.get('is_known_issue', False),
            needs_investigation=data.get('needs_investigation', False),
            provided_by=data.get('provided_by', 'Web UI User'),
            provided_at=datetime.now()
        )

        # Save feedback
        feedback_file = FEEDBACK_DIR / f"{feedback.id}.json"
        save_json(str(feedback_file), feedback.dict())

        logger.info(f"Feedback submitted: {feedback.id}")

        # Broadcast event to WebSocket clients
        current_app.broadcast_event('feedback_submitted', {
            'feedback_id': feedback.id,
            'item_id': feedback.item_id,
            'item_type': feedback.item_type
        })

        return jsonify({
            'success': True,
            'feedback': {
                'id': feedback.id,
                'item_id': feedback.item_id,
                'provided_at': feedback.provided_at.isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'error': str(e)}), 500


@feedback_bp.route('/<feedback_id>', methods=['GET'])
def get_feedback(feedback_id):
    """Get feedback by ID"""
    try:
        feedback_file = FEEDBACK_DIR / f"{feedback_id}.json"

        if not feedback_file.exists():
            return jsonify({'error': 'Feedback not found'}), 404

        feedback_data = load_json(str(feedback_file))

        return jsonify({
            'success': True,
            'feedback': feedback_data
        })

    except Exception as e:
        logger.error(f"Error getting feedback {feedback_id}: {e}")
        return jsonify({'error': str(e)}), 500


@feedback_bp.route('/item/<item_id>', methods=['GET'])
def get_feedback_for_item(item_id):
    """Get all feedback for a specific item"""
    try:
        feedback_list = []

        for feedback_file in FEEDBACK_DIR.glob("*.json"):
            feedback_data = load_json(str(feedback_file))
            if feedback_data.get('item_id') == item_id:
                feedback_list.append(feedback_data)

        # Sort by provided_at (newest first)
        feedback_list.sort(key=lambda x: x.get('provided_at', ''), reverse=True)

        return jsonify({
            'success': True,
            'count': len(feedback_list),
            'feedback': feedback_list
        })

    except Exception as e:
        logger.error(f"Error getting feedback for item {item_id}: {e}")
        return jsonify({'error': str(e)}), 500
