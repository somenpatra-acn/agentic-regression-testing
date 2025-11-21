"""Test case data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestPriority(str, Enum):
    """Test priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestType(str, Enum):
    """Test types."""
    UI = "ui"
    API = "api"
    DATABASE = "database"
    INTEGRATION = "integration"
    E2E = "e2e"
    SMOKE = "smoke"
    REGRESSION = "regression"


class TestStep(BaseModel):
    """Individual test step."""
    step_number: int = Field(..., description="Step sequence number")
    action: str = Field(..., description="Action to perform")
    target: Optional[str] = Field(None, description="Target element or endpoint")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data for step")
    expected_result: str = Field(..., description="Expected outcome")
    screenshot: bool = Field(default=False, description="Capture screenshot after step")

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "action": "click",
                "target": "#login-button",
                "expected_result": "Login page loads"
            }
        }


class TestCase(BaseModel):
    """Complete test case specification."""
    id: str = Field(..., description="Unique test case identifier")
    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Test case description")
    test_type: TestType = Field(..., description="Type of test")
    priority: TestPriority = Field(default=TestPriority.MEDIUM, description="Test priority")

    # Test definition
    steps: List[TestStep] = Field(default_factory=list, description="Test steps")
    preconditions: List[str] = Field(default_factory=list, description="Prerequisites")
    postconditions: List[str] = Field(default_factory=list, description="Cleanup actions")

    # Test data
    test_data: Dict[str, Any] = Field(default_factory=dict, description="Test data")

    # Application context
    application: str = Field(..., description="Target application")
    module: Optional[str] = Field(None, description="Application module")
    feature: Optional[str] = Field(None, description="Feature being tested")

    # Test script
    script_path: Optional[str] = Field(None, description="Path to generated test script")
    framework: str = Field(default="playwright", description="Test framework")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Test tags")
    author: Optional[str] = Field(None, description="Test author")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Human-in-the-loop
    requires_approval: bool = Field(default=True, description="Requires human approval")
    approved_by: Optional[str] = Field(None, description="Approver name")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    human_feedback: Optional[str] = Field(None, description="Human feedback/notes")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "TEST-001",
                "name": "User Login Test",
                "description": "Verify user can login with valid credentials",
                "test_type": "ui",
                "priority": "critical",
                "application": "web_portal",
                "steps": [
                    {
                        "step_number": 1,
                        "action": "navigate",
                        "target": "/login",
                        "expected_result": "Login page displayed"
                    }
                ]
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def add_step(self, action: str, target: Optional[str], expected_result: str, **kwargs) -> None:
        """Add a test step."""
        step_number = len(self.steps) + 1
        step = TestStep(
            step_number=step_number,
            action=action,
            target=target,
            expected_result=expected_result,
            **kwargs
        )
        self.steps.append(step)

    def approve(self, approver: str) -> None:
        """Mark test as approved."""
        self.approved_by = approver
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
