"""Approval manager for human approval workflows."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from models.approval import Approval, ApprovalStatus, ApprovalType
from models.test_case import TestCase
from utils.logger import get_logger
from utils.helpers import generate_approval_id, save_json, load_json

logger = get_logger(__name__)


class ApprovalDeniedException(Exception):
    """Exception raised when approval is denied."""
    pass


class ApprovalManager:
    """
    Manage human approval workflows for test planning and execution.

    Supports different approval modes:
    - FULL_AUTO: No approvals required
    - APPROVE_PLAN: Approve test plans only
    - APPROVE_TESTS: Approve generated tests only
    - APPROVE_ALL: Approve plans, tests, and execution
    - INTERACTIVE: Step-by-step approval
    """

    def __init__(self, hitl_mode: str = "APPROVE_PLAN", timeout: int = 3600):
        """
        Initialize approval manager.

        Args:
            hitl_mode: HITL mode (FULL_AUTO, APPROVE_PLAN, etc.)
            timeout: Default approval timeout in seconds
        """
        self.hitl_mode = hitl_mode
        self.default_timeout = timeout
        self.approvals_dir = Path("approvals")
        self.approvals_dir.mkdir(exist_ok=True)

        logger.info(f"ApprovalManager initialized - Mode: {hitl_mode}")

    def is_approval_required(self, approval_type: ApprovalType) -> bool:
        """
        Check if approval is required for given type.

        Args:
            approval_type: Type of approval

        Returns:
            bool: True if approval required
        """
        if self.hitl_mode == "FULL_AUTO":
            return False

        if self.hitl_mode == "APPROVE_PLAN":
            return approval_type == ApprovalType.TEST_PLAN

        if self.hitl_mode == "APPROVE_TESTS":
            return approval_type == ApprovalType.TEST_CASE

        if self.hitl_mode == "APPROVE_ALL":
            return approval_type in [
                ApprovalType.TEST_PLAN,
                ApprovalType.TEST_CASE,
                ApprovalType.TEST_EXECUTION
            ]

        if self.hitl_mode == "INTERACTIVE":
            return True

        return False

    async def request_approval(
        self,
        approval_type: ApprovalType,
        item_id: str,
        item_data: Dict[str, Any],
        item_summary: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Approval:
        """
        Request human approval for an item.

        Args:
            approval_type: Type of approval needed
            item_id: ID of item requiring approval
            item_data: Complete item data
            item_summary: Human-readable summary
            context: Additional context
            timeout: Approval timeout (uses default if not provided)

        Returns:
            Approval: Approval object with decision

        Raises:
            ApprovalDeniedException: If approval is denied or times out
        """
        if not self.is_approval_required(approval_type):
            # Auto-approve
            approval = self._create_approval(
                approval_type, item_id, item_data, item_summary, context, timeout
            )
            approval.approve("system", "Auto-approved")
            return approval

        # Create approval request
        approval = self._create_approval(
            approval_type, item_id, item_data, item_summary, context, timeout
        )

        # Save approval request
        self._save_approval(approval)

        logger.info(
            f"Approval requested: {approval_type.value} for {item_id} "
            f"(timeout: {approval.timeout_seconds}s)"
        )

        # Wait for human approval
        approval = await self._wait_for_approval(approval)

        # Handle approval decision
        if approval.status == ApprovalStatus.APPROVED:
            logger.info(f"Approval granted by {approval.approved_by}")
            return approval

        elif approval.status == ApprovalStatus.MODIFIED:
            logger.info(f"Approval granted with modifications by {approval.approved_by}")
            return approval

        elif approval.status == ApprovalStatus.REJECTED:
            logger.warning(f"Approval rejected by {approval.approved_by}: {approval.rejection_reason}")
            raise ApprovalDeniedException(
                f"Approval rejected: {approval.rejection_reason}"
            )

        elif approval.status == ApprovalStatus.TIMEOUT:
            logger.error(f"Approval timed out for {item_id}")
            raise ApprovalDeniedException(
                f"Approval timed out after {approval.timeout_seconds} seconds"
            )

        return approval

    def _create_approval(
        self,
        approval_type: ApprovalType,
        item_id: str,
        item_data: Dict[str, Any],
        item_summary: str,
        context: Optional[Dict[str, Any]],
        timeout: Optional[int]
    ) -> Approval:
        """Create approval object."""
        return Approval(
            id=generate_approval_id(),
            approval_type=approval_type,
            item_id=item_id,
            item_data=item_data,
            item_summary=item_summary,
            context=context or {},
            timeout_seconds=timeout or self.default_timeout,
            requested_at=datetime.utcnow()
        )

    async def _wait_for_approval(self, approval: Approval) -> Approval:
        """
        Wait for human to provide approval decision.

        In a production system, this would:
        1. Notify human reviewer (email, Slack, web UI, etc.)
        2. Poll for approval decision
        3. Handle timeout

        For this implementation, we provide a CLI-based review.
        """
        from hitl.review_interface import CLIReviewer

        reviewer = CLIReviewer()

        # Run reviewer in background
        try:
            # Provide approval decision
            decision = await asyncio.get_event_loop().run_in_executor(
                None,
                reviewer.review_approval,
                approval
            )

            if decision["action"] == "approve":
                approval.approve(
                    approver=decision.get("approver", "human"),
                    comments=decision.get("comments")
                )
            elif decision["action"] == "reject":
                approval.reject(
                    approver=decision.get("approver", "human"),
                    reason=decision.get("reason", "Rejected by human")
                )
            elif decision["action"] == "modify":
                approval.modify(
                    approver=decision.get("approver", "human"),
                    modifications=decision.get("modifications", {}),
                    modified_item=decision.get("modified_item", approval.item_data)
                )

            # Save updated approval
            self._save_approval(approval)

            return approval

        except asyncio.TimeoutError:
            approval.status = ApprovalStatus.TIMEOUT
            self._save_approval(approval)
            return approval

    def _save_approval(self, approval: Approval) -> None:
        """Save approval to file."""
        filepath = self.approvals_dir / f"{approval.id}.json"
        save_json(approval.model_dump(), str(filepath))

    def get_approval(self, approval_id: str) -> Optional[Approval]:
        """
        Load approval from file.

        Args:
            approval_id: Approval ID

        Returns:
            Approval object or None
        """
        filepath = self.approvals_dir / f"{approval_id}.json"
        if filepath.exists():
            data = load_json(str(filepath))
            return Approval(**data)
        return None

    def get_pending_approvals(self) -> list:
        """
        Get all pending approvals.

        Returns:
            List of pending Approval objects
        """
        pending = []
        for filepath in self.approvals_dir.glob("*.json"):
            try:
                approval = Approval(**load_json(str(filepath)))
                if approval.status == ApprovalStatus.PENDING:
                    pending.append(approval)
            except Exception as e:
                logger.error(f"Error loading approval {filepath}: {e}")

        return pending

    def approve_test_plan(self, plan: Dict[str, Any], summary: str) -> Dict[str, Any]:
        """
        Request approval for test plan (synchronous wrapper).

        Args:
            plan: Test plan data
            summary: Human-readable summary

        Returns:
            Approved (possibly modified) test plan
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            approval = loop.run_until_complete(
                self.request_approval(
                    approval_type=ApprovalType.TEST_PLAN,
                    item_id=plan.get("id", "unknown"),
                    item_data=plan,
                    item_summary=summary
                )
            )

            # Return modified item if available, otherwise original
            return approval.modified_item or approval.item_data

        finally:
            loop.close()

    def approve_test_case(self, test_case: TestCase) -> TestCase:
        """
        Request approval for test case (synchronous wrapper).

        Args:
            test_case: Test case to approve

        Returns:
            Approved (possibly modified) test case
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            approval = loop.run_until_complete(
                self.request_approval(
                    approval_type=ApprovalType.TEST_CASE,
                    item_id=test_case.id,
                    item_data=test_case.to_dict(),
                    item_summary=f"Test: {test_case.name} - {test_case.description}"
                )
            )

            # Return modified test case if available
            if approval.modified_item:
                return TestCase(**approval.modified_item)

            return test_case

        finally:
            loop.close()
