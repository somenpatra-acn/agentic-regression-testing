"""
Approval Service - Business logic for managing approvals

This service handles:
- Retrieving pending approvals
- Approving/rejecting approvals
- Modifying approvals
- Statistics and reporting
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.approval import Approval, ApprovalStatus, ApprovalType
from utils.helpers import load_json, save_json
from utils.logger import get_logger

logger = get_logger(__name__)

# Approvals directory
APPROVALS_DIR = Path("approvals")
APPROVALS_DIR.mkdir(exist_ok=True)


class ApprovalService:
    """Service for managing approval operations"""

    @staticmethod
    def get_pending_approvals() -> List[Dict[str, Any]]:
        """
        Get all pending approvals

        Returns:
            List of pending approval summaries
        """
        pending = []

        for approval_file in APPROVALS_DIR.glob("*.json"):
            try:
                approval_data = load_json(str(approval_file))
                approval = Approval(**approval_data)

                if approval.status == ApprovalStatus.PENDING:
                    # Calculate time remaining
                    elapsed = (datetime.now() - approval.requested_at).total_seconds()
                    time_remaining = max(0, approval.timeout_seconds - elapsed)

                    pending.append({
                        'id': approval.id,
                        'type': approval.approval_type.value,
                        'item_id': approval.item_id,
                        'summary': approval.item_summary,
                        'status': approval.status.value,
                        'requested_at': approval.requested_at.isoformat(),
                        'timeout_seconds': approval.timeout_seconds,
                        'time_remaining': int(time_remaining),
                        'is_expired': time_remaining <= 0
                    })
            except Exception as e:
                logger.error(f"Error loading approval {approval_file}: {e}")

        # Sort by requested_at (newest first)
        pending.sort(key=lambda x: x['requested_at'], reverse=True)

        return pending

    @staticmethod
    def get_approval(approval_id: str) -> Optional[Dict[str, Any]]:
        """
        Get approval details by ID

        Args:
            approval_id: Approval ID

        Returns:
            Approval details or None if not found
        """
        approval_file = APPROVALS_DIR / f"{approval_id}.json"

        if not approval_file.exists():
            return None

        try:
            approval_data = load_json(str(approval_file))
            approval = Approval(**approval_data)

            # Calculate time remaining
            elapsed = (datetime.now() - approval.requested_at).total_seconds()
            time_remaining = max(0, approval.timeout_seconds - elapsed)

            return {
                'id': approval.id,
                'approval_type': approval.approval_type.value,
                'item_id': approval.item_id,
                'item_summary': approval.item_summary,
                'item_data': approval.item_data,
                'status': approval.status.value,
                'approved_by': approval.approved_by,
                'approved_at': approval.approved_at.isoformat() if approval.approved_at else None,
                'rejection_reason': approval.rejection_reason,
                'modifications': approval.modifications,
                'modified_item': approval.modified_item,
                'comments': approval.comments,
                'requested_at': approval.requested_at.isoformat(),
                'timeout_seconds': approval.timeout_seconds,
                'time_remaining': int(time_remaining),
                'is_expired': time_remaining <= 0,
                'context': approval.context
            }
        except Exception as e:
            logger.error(f"Error loading approval {approval_id}: {e}")
            return None

    @staticmethod
    def approve_approval(
        approval_id: str,
        approved_by: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve an approval request

        Args:
            approval_id: Approval ID
            approved_by: Name of approver
            comments: Optional comments

        Returns:
            Updated approval data or error
        """
        approval_file = APPROVALS_DIR / f"{approval_id}.json"

        if not approval_file.exists():
            return {'error': 'Approval not found', 'status': 404}

        try:
            approval_data = load_json(str(approval_file))
            approval = Approval(**approval_data)

            # Check if already processed
            if approval.status != ApprovalStatus.PENDING:
                return {
                    'error': f'Approval already {approval.status.value}',
                    'status': 400
                }

            # Check if expired
            elapsed = (datetime.now() - approval.requested_at).total_seconds()
            if elapsed > approval.timeout_seconds:
                approval.status = ApprovalStatus.TIMEOUT
                save_json(approval.dict(), str(approval_file))
                return {'error': 'Approval expired', 'status': 400}

            # Update approval
            approval.status = ApprovalStatus.APPROVED
            approval.approved_by = approved_by
            approval.approved_at = datetime.now()
            approval.comments = comments

            # Save updated approval
            save_json(approval.dict(), str(approval_file))

            logger.info(f"Approval {approval_id} approved by {approved_by}")

            return {
                'success': True,
                'approval': {
                    'id': approval.id,
                    'status': approval.status.value,
                    'approved_by': approval.approved_by,
                    'approved_at': approval.approved_at.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error approving {approval_id}: {e}")
            return {'error': str(e), 'status': 500}

    @staticmethod
    def reject_approval(
        approval_id: str,
        approved_by: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Reject an approval request

        Args:
            approval_id: Approval ID
            approved_by: Name of approver
            rejection_reason: Reason for rejection

        Returns:
            Updated approval data or error
        """
        approval_file = APPROVALS_DIR / f"{approval_id}.json"

        if not approval_file.exists():
            return {'error': 'Approval not found', 'status': 404}

        try:
            approval_data = load_json(str(approval_file))
            approval = Approval(**approval_data)

            # Check if already processed
            if approval.status != ApprovalStatus.PENDING:
                return {
                    'error': f'Approval already {approval.status.value}',
                    'status': 400
                }

            # Update approval
            approval.status = ApprovalStatus.REJECTED
            approval.approved_by = approved_by
            approval.approved_at = datetime.now()
            approval.rejection_reason = rejection_reason

            # Save updated approval
            save_json(approval.dict(), str(approval_file))

            logger.info(f"Approval {approval_id} rejected by {approved_by}: {rejection_reason}")

            return {
                'success': True,
                'approval': {
                    'id': approval.id,
                    'status': approval.status.value,
                    'approved_by': approval.approved_by,
                    'rejected_at': approval.approved_at.isoformat(),
                    'rejection_reason': approval.rejection_reason
                }
            }

        except Exception as e:
            logger.error(f"Error rejecting {approval_id}: {e}")
            return {'error': str(e), 'status': 500}

    @staticmethod
    def modify_approval(
        approval_id: str,
        approved_by: str,
        modifications: Dict[str, Any],
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve with modifications

        Args:
            approval_id: Approval ID
            approved_by: Name of approver
            modifications: Modifications to apply
            comments: Optional comments

        Returns:
            Updated approval data or error
        """
        approval_file = APPROVALS_DIR / f"{approval_id}.json"

        if not approval_file.exists():
            return {'error': 'Approval not found', 'status': 404}

        try:
            approval_data = load_json(str(approval_file))
            approval = Approval(**approval_data)

            # Check if already processed
            if approval.status != ApprovalStatus.PENDING:
                return {
                    'error': f'Approval already {approval.status.value}',
                    'status': 400
                }

            # Check if expired
            elapsed = (datetime.now() - approval.requested_at).total_seconds()
            if elapsed > approval.timeout_seconds:
                approval.status = ApprovalStatus.TIMEOUT
                save_json(approval.dict(), str(approval_file))
                return {'error': 'Approval expired', 'status': 400}

            # Update approval
            approval.status = ApprovalStatus.MODIFIED
            approval.approved_by = approved_by
            approval.approved_at = datetime.now()
            approval.modifications = modifications
            approval.comments = comments

            # Apply modifications to create modified_item
            approval.modified_item = approval.item_data.copy()
            approval.modified_item.update(modifications)

            # Save updated approval
            save_json(approval.dict(), str(approval_file))

            logger.info(f"Approval {approval_id} modified by {approved_by}")

            return {
                'success': True,
                'approval': {
                    'id': approval.id,
                    'status': approval.status.value,
                    'approved_by': approval.approved_by,
                    'approved_at': approval.approved_at.isoformat(),
                    'modifications': approval.modifications
                }
            }

        except Exception as e:
            logger.error(f"Error modifying {approval_id}: {e}")
            return {'error': str(e), 'status': 500}

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Get approval statistics

        Returns:
            Statistics dictionary
        """
        stats = {
            'total': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'modified': 0,
            'timeout': 0,
            'by_type': {},
            'average_approval_time': 0,
            'recent_approvals': []
        }

        approval_times = []
        recent = []

        for approval_file in APPROVALS_DIR.glob("*.json"):
            try:
                approval_data = load_json(str(approval_file))
                approval = Approval(**approval_data)

                stats['total'] += 1

                # Count by status
                if approval.status == ApprovalStatus.PENDING:
                    stats['pending'] += 1
                elif approval.status == ApprovalStatus.APPROVED:
                    stats['approved'] += 1
                elif approval.status == ApprovalStatus.REJECTED:
                    stats['rejected'] += 1
                elif approval.status == ApprovalStatus.MODIFIED:
                    stats['modified'] += 1
                elif approval.status == ApprovalStatus.TIMEOUT:
                    stats['timeout'] += 1

                # Count by type
                type_key = approval.approval_type.value
                stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1

                # Calculate approval time
                if approval.approved_at:
                    approval_time = (approval.approved_at - approval.requested_at).total_seconds()
                    approval_times.append(approval_time)

                # Add to recent approvals
                recent.append({
                    'id': approval.id,
                    'type': approval.approval_type.value,
                    'status': approval.status.value,
                    'requested_at': approval.requested_at.isoformat(),
                    'approved_at': approval.approved_at.isoformat() if approval.approved_at else None
                })

            except Exception as e:
                logger.error(f"Error processing approval {approval_file}: {e}")

        # Calculate average approval time
        if approval_times:
            stats['average_approval_time'] = sum(approval_times) / len(approval_times)

        # Sort recent approvals by date (newest first) and limit to 10
        recent.sort(key=lambda x: x['requested_at'], reverse=True)
        stats['recent_approvals'] = recent[:10]

        return stats
