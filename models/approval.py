"""Approval and feedback data models for HITL workflows."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"


class ApprovalType(str, Enum):
    """Type of approval request."""
    TEST_PLAN = "test_plan"
    TEST_CASE = "test_case"
    TEST_EXECUTION = "test_execution"
    DISCOVERY_RESULTS = "discovery_results"
    GENERATED_CODE = "generated_code"


class Feedback(BaseModel):
    """Human feedback on test execution or generation."""
    id: str = Field(..., description="Unique feedback identifier")
    item_id: str = Field(..., description="ID of item being reviewed")
    item_type: str = Field(..., description="Type of item (test_case, result, etc.)")

    # Feedback content
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5")
    comment: str = Field(..., description="Feedback comment")
    corrections: Optional[Dict[str, Any]] = Field(None, description="Suggested corrections")

    # Classification
    is_false_positive: bool = Field(default=False, description="Marked as false positive")
    is_false_negative: bool = Field(default=False, description="Marked as false negative")
    is_known_issue: bool = Field(default=False, description="Marked as known issue")
    needs_investigation: bool = Field(default=False, description="Needs further investigation")

    # Metadata
    provided_by: str = Field(..., description="Person providing feedback")
    provided_at: datetime = Field(default_factory=datetime.utcnow, description="Feedback timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "FB-001",
                "item_id": "TEST-001",
                "item_type": "test_case",
                "rating": 4,
                "comment": "Test looks good, but add verification of error message",
                "provided_by": "john.doe"
            }
        }

    def to_document(self) -> str:
        """Convert feedback to document for RAG storage."""
        doc = f"""
        Feedback for {self.item_type} {self.item_id}:
        Rating: {self.rating}/5
        Comment: {self.comment}
        Provided by: {self.provided_by}
        Date: {self.provided_at}
        """
        if self.corrections:
            doc += f"\nSuggested corrections: {self.corrections}"
        if self.is_false_positive:
            doc += "\nMarked as: FALSE POSITIVE"
        if self.is_known_issue:
            doc += "\nMarked as: KNOWN ISSUE"
        return doc.strip()


class Approval(BaseModel):
    """Approval request and response for HITL workflows."""
    id: str = Field(..., description="Unique approval identifier")
    approval_type: ApprovalType = Field(..., description="Type of approval")

    # Item being approved
    item_id: str = Field(..., description="ID of item requiring approval")
    item_data: Dict[str, Any] = Field(..., description="Item data for review")
    item_summary: str = Field(..., description="Human-readable summary")

    # Approval status
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING,
        description="Current approval status"
    )

    # Response
    approved_by: Optional[str] = Field(None, description="Approver name")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    modifications: Optional[Dict[str, Any]] = Field(
        None,
        description="Modifications made by approver"
    )
    modified_item: Optional[Dict[str, Any]] = Field(
        None,
        description="Modified version of item"
    )

    # Feedback
    feedback: Optional[Feedback] = Field(None, description="Associated feedback")
    comments: Optional[str] = Field(None, description="Approver comments")

    # Timing
    requested_at: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    timeout_seconds: int = Field(default=3600, description="Approval timeout")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    # Context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for approval"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "APPROVAL-001",
                "approval_type": "test_plan",
                "item_id": "PLAN-001",
                "item_data": {"tests": []},
                "item_summary": "Test plan for login feature with 5 test cases",
                "status": "pending",
                "timeout_seconds": 3600
            }
        }

    def approve(self, approver: str, comments: Optional[str] = None) -> None:
        """Approve the item."""
        self.status = ApprovalStatus.APPROVED
        self.approved_by = approver
        self.approved_at = datetime.utcnow()
        self.comments = comments

    def reject(self, approver: str, reason: str) -> None:
        """Reject the item."""
        self.status = ApprovalStatus.REJECTED
        self.approved_by = approver
        self.approved_at = datetime.utcnow()
        self.rejection_reason = reason

    def modify(self, approver: str, modifications: Dict[str, Any], modified_item: Dict[str, Any]) -> None:
        """Approve with modifications."""
        self.status = ApprovalStatus.MODIFIED
        self.approved_by = approver
        self.approved_at = datetime.utcnow()
        self.modifications = modifications
        self.modified_item = modified_item

    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        if self.expires_at is None:
            self.expires_at = datetime.fromtimestamp(
                self.requested_at.timestamp() + self.timeout_seconds
            )
        return datetime.utcnow() > self.expires_at

    def time_remaining(self) -> int:
        """Get remaining time in seconds."""
        if self.expires_at is None:
            self.expires_at = datetime.fromtimestamp(
                self.requested_at.timestamp() + self.timeout_seconds
            )
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
