"""
Workflow Routes - API endpoints for workflow monitoring
"""

from flask import Blueprint, jsonify, current_app
from web_ui.services.workflow_service import WorkflowService
from utils.logger import get_logger

logger = get_logger(__name__)

workflow_bp = Blueprint('workflow', __name__)
service = WorkflowService()


@workflow_bp.route('/status', methods=['GET'])
def get_status():
    """Get current workflow status"""
    try:
        status = service.get_status()
        return jsonify({
            'success': True,
            'workflow': status
        })
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/stages', methods=['GET'])
def get_stages():
    """Get details for all stages"""
    try:
        stages = service.get_all_stages()
        return jsonify({
            'success': True,
            'stages': stages
        })
    except Exception as e:
        logger.error(f"Error getting stages: {e}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/stages/<stage_name>', methods=['GET'])
def get_stage(stage_name):
    """Get details for a specific stage"""
    try:
        stage = service.get_stage_details(stage_name)

        if not stage:
            return jsonify({'error': 'Stage not found'}), 404

        return jsonify({
            'success': True,
            'stage': stage
        })
    except Exception as e:
        logger.error(f"Error getting stage {stage_name}: {e}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/reset', methods=['POST'])
def reset_workflow():
    """Reset workflow to initial state"""
    try:
        service.reset_workflow()

        # Broadcast event to WebSocket clients
        current_app.broadcast_event('workflow_reset', {
            'message': 'Workflow has been reset'
        })

        return jsonify({
            'success': True,
            'message': 'Workflow reset successfully'
        })
    except Exception as e:
        logger.error(f"Error resetting workflow: {e}")
        return jsonify({'error': str(e)}), 500
