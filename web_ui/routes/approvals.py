"""
Approval Routes - API endpoints for approval management
"""

from flask import Blueprint, jsonify, request, current_app
from web_ui.services.approval_service import ApprovalService
from utils.logger import get_logger

logger = get_logger(__name__)

approvals_bp = Blueprint('approvals', __name__)
service = ApprovalService()


@approvals_bp.route('/pending', methods=['GET'])
def get_pending():
    """Get all pending approvals"""
    try:
        approvals = service.get_pending_approvals()
        return jsonify({
            'success': True,
            'count': len(approvals),
            'approvals': approvals
        })
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        return jsonify({'error': str(e)}), 500


@approvals_bp.route('/<approval_id>', methods=['GET'])
def get_approval(approval_id):
    """Get approval details by ID"""
    try:
        approval = service.get_approval(approval_id)

        if not approval:
            return jsonify({'error': 'Approval not found'}), 404

        return jsonify({
            'success': True,
            'approval': approval
        })
    except Exception as e:
        logger.error(f"Error getting approval {approval_id}: {e}")
        return jsonify({'error': str(e)}), 500


@approvals_bp.route('/<approval_id>/approve', methods=['POST'])
def approve(approval_id):
    """Approve an approval request"""
    try:
        data = request.json or {}
        approved_by = data.get('approved_by', 'Web UI User')
        comments = data.get('comments')

        result = service.approve_approval(approval_id, approved_by, comments)

        # Broadcast event to WebSocket clients
        if 'success' in result:
            current_app.broadcast_event('approval_updated', {
                'approval_id': approval_id,
                'status': 'approved',
                'approved_by': approved_by
            })

        # Return appropriate status code
        status_code = result.pop('status', 200)
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error approving {approval_id}: {e}")
        return jsonify({'error': str(e)}), 500


@approvals_bp.route('/<approval_id>/reject', methods=['POST'])
def reject(approval_id):
    """Reject an approval request"""
    try:
        data = request.json or {}
        approved_by = data.get('approved_by', 'Web UI User')
        rejection_reason = data.get('rejection_reason', 'No reason provided')

        result = service.reject_approval(approval_id, approved_by, rejection_reason)

        # Broadcast event to WebSocket clients
        if 'success' in result:
            current_app.broadcast_event('approval_updated', {
                'approval_id': approval_id,
                'status': 'rejected',
                'approved_by': approved_by,
                'rejection_reason': rejection_reason
            })

        # Return appropriate status code
        status_code = result.pop('status', 200)
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error rejecting {approval_id}: {e}")
        return jsonify({'error': str(e)}), 500


@approvals_bp.route('/<approval_id>/modify', methods=['POST'])
def modify(approval_id):
    """Approve with modifications"""
    try:
        data = request.json or {}
        approved_by = data.get('approved_by', 'Web UI User')
        modifications = data.get('modifications', {})
        comments = data.get('comments')

        if not modifications:
            return jsonify({'error': 'Modifications required'}), 400

        result = service.modify_approval(approval_id, approved_by, modifications, comments)

        # Broadcast event to WebSocket clients
        if 'success' in result:
            current_app.broadcast_event('approval_updated', {
                'approval_id': approval_id,
                'status': 'modified',
                'approved_by': approved_by
            })

        # Return appropriate status code
        status_code = result.pop('status', 200)
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error modifying {approval_id}: {e}")
        return jsonify({'error': str(e)}), 500


@approvals_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get approval statistics"""
    try:
        stats = service.get_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': str(e)}), 500
