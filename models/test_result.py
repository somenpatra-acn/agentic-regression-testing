"""Test result data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    ERROR = "error"
    RUNNING = "running"
    PENDING = "pending"


class TestMetrics(BaseModel):
    """Test execution metrics."""
    duration_seconds: float = Field(..., description="Test execution duration")
    start_time: datetime = Field(..., description="Test start timestamp")
    end_time: datetime = Field(..., description="Test end timestamp")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage")

    class Config:
        json_schema_extra = {
            "example": {
                "duration_seconds": 12.5,
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T10:00:12"
            }
        }


class StepResult(BaseModel):
    """Individual test step result."""
    step_number: int = Field(..., description="Step sequence number")
    status: TestStatus = Field(..., description="Step execution status")
    actual_result: str = Field(..., description="Actual outcome")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    screenshot_path: Optional[str] = Field(None, description="Screenshot path")
    duration_seconds: float = Field(..., description="Step duration")

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "status": "passed",
                "actual_result": "Login page loaded successfully",
                "duration_seconds": 2.3
            }
        }


class TestResult(BaseModel):
    """Complete test execution result."""
    id: str = Field(..., description="Unique result identifier")
    test_case_id: str = Field(..., description="Associated test case ID")
    test_name: str = Field(..., description="Test case name")

    # Execution details
    status: TestStatus = Field(..., description="Overall test status")
    step_results: List[StepResult] = Field(default_factory=list, description="Step results")

    # Error information
    error_message: Optional[str] = Field(None, description="Error message if failed")
    stack_trace: Optional[str] = Field(None, description="Stack trace if error")

    # Artifacts
    log_file: Optional[str] = Field(None, description="Log file path")
    screenshots: List[str] = Field(default_factory=list, description="Screenshot paths")
    video_path: Optional[str] = Field(None, description="Video recording path")

    # Metrics
    metrics: TestMetrics = Field(..., description="Execution metrics")

    # Environment
    environment: str = Field(default="test", description="Execution environment")
    browser: Optional[str] = Field(None, description="Browser used (if UI test)")
    os_platform: Optional[str] = Field(None, description="OS platform")

    # CI/CD
    build_number: Optional[str] = Field(None, description="CI/CD build number")
    commit_hash: Optional[str] = Field(None, description="Git commit hash")
    branch: Optional[str] = Field(None, description="Git branch")

    # Human validation
    validated_by_human: bool = Field(default=False, description="Human validated result")
    human_comment: Optional[str] = Field(None, description="Human validation comment")
    is_false_positive: bool = Field(default=False, description="Marked as false positive")
    is_false_negative: bool = Field(default=False, description="Marked as false negative")

    # Metadata
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    executed_by: str = Field(default="agent", description="Executor (agent or human)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "RESULT-001",
                "test_case_id": "TEST-001",
                "test_name": "User Login Test",
                "status": "passed",
                "metrics": {
                    "duration_seconds": 12.5,
                    "start_time": "2024-01-01T10:00:00",
                    "end_time": "2024-01-01T10:00:12"
                }
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def add_step_result(
        self,
        step_number: int,
        status: TestStatus,
        actual_result: str,
        duration_seconds: float,
        **kwargs
    ) -> None:
        """Add a step result."""
        step_result = StepResult(
            step_number=step_number,
            status=status,
            actual_result=actual_result,
            duration_seconds=duration_seconds,
            **kwargs
        )
        self.step_results.append(step_result)

    def mark_false_positive(self, comment: str, validator: str) -> None:
        """Mark result as false positive."""
        self.is_false_positive = True
        self.validated_by_human = True
        self.human_comment = comment
        self.executed_by = validator

    def is_success(self) -> bool:
        """Check if test passed."""
        return self.status == TestStatus.PASSED

    def get_failure_summary(self) -> Optional[str]:
        """Get failure summary."""
        if self.status != TestStatus.FAILED:
            return None

        failed_steps = [sr for sr in self.step_results if sr.status == TestStatus.FAILED]
        if failed_steps:
            return f"Failed at step {failed_steps[0].step_number}: {failed_steps[0].error_message}"
        return self.error_message
