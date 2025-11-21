"""
LangGraph State Schemas

Type-safe state definitions for LangGraph workflows.
"""

from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime


class DiscoveryState(TypedDict, total=False):
    """
    State schema for Discovery workflow

    This defines all state variables that flow through the
    discovery graph nodes.
    """
    # Input
    app_profile: Any  # ApplicationProfile object
    discovery_params: Dict[str, Any]  # Optional override parameters

    # Discovery results
    discovery_result: Optional[Dict[str, Any]]  # Raw discovery result
    elements: List[Dict[str, Any]]  # Discovered elements
    pages: List[str]  # Discovered pages
    apis: List[Dict[str, Any]]  # Discovered APIs

    # Validation and sanitization
    sanitized_input: Optional[str]  # Sanitized user input
    validation_warnings: List[str]  # Validation warnings

    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    error: Optional[str]  # Error message if workflow failed
    status: str  # "pending", "in_progress", "completed", "failed"

    # Statistics
    total_elements: int
    total_pages: int
    element_types: Dict[str, int]

    # HITL
    requires_approval: bool
    approval_status: Optional[str]  # "pending", "approved", "rejected"
    human_feedback: Optional[str]


class TestPlanningState(TypedDict, total=False):
    """State schema for Test Planning workflow"""
    # Input
    app_profile: Any
    feature_description: str
    discovery_result: Dict[str, Any]

    # Planning results
    test_plan: Optional[Dict[str, Any]]
    test_cases: List[Dict[str, Any]]
    coverage_analysis: Optional[Dict[str, Any]]

    # RAG context
    similar_tests: List[Dict[str, Any]]
    test_patterns: List[Dict[str, Any]]

    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    error: Optional[str]
    status: str

    # HITL
    requires_approval: bool
    approval_status: Optional[str]
    human_feedback: Optional[str]


class TestGenerationState(TypedDict, total=False):
    """State schema for Test Generation workflow"""
    # Input
    test_plan: Dict[str, Any]
    test_cases: List[Dict[str, Any]]
    framework: str  # "playwright", "selenium", "pytest"

    # Generation results
    generated_scripts: List[Dict[str, Any]]  # {filename, content, test_case_id, file_path}
    validation_results: List[Dict[str, Any]]  # Script validation results

    # Statistics
    passed_count: int
    failed_count: int
    skipped_count: int
    execution_time: float

    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    error: Optional[str]
    status: str

    # HITL
    requires_approval: bool
    approval_status: Optional[str]
    human_feedback: Optional[str]


class TestExecutionState(TypedDict, total=False):
    """State schema for Test Execution workflow"""
    # Input
    test_scripts: List[Dict[str, Any]]
    execution_config: Dict[str, Any]

    # Execution results
    test_results: List[Dict[str, Any]]
    passed_count: int
    failed_count: int
    skipped_count: int

    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    error: Optional[str]
    status: str
    execution_time: float


class ReportingState(TypedDict, total=False):
    """State schema for Reporting workflow"""
    # Input
    test_results: List[Dict[str, Any]]
    app_name: str
    report_formats: List[str]  # ["html", "json", "markdown"]

    # Generated reports
    generated_reports: List[Dict[str, Any]]  # {format, content, file_path}
    statistics: Optional[Dict[str, Any]]

    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    error: Optional[str]
    status: str
    execution_time: float


class OrchestratorState(TypedDict, total=False):
    """
    State schema for Orchestrator workflow

    Combines all sub-workflows into a unified state.
    """
    # User input
    app_profile: Any
    feature_description: str
    user_request: str

    # Sub-workflow states
    discovery_state: Optional[DiscoveryState]
    planning_state: Optional[TestPlanningState]
    generation_state: Optional[TestGenerationState]
    execution_state: Optional[TestExecutionState]

    # Overall workflow
    current_stage: str  # "discovery", "planning", "generation", "execution", "reporting"
    completed_stages: List[str]
    workflow_status: str  # "pending", "in_progress", "completed", "failed"

    # HITL
    pending_approvals: List[str]  # List of stages pending approval
    approval_responses: Dict[str, str]  # {stage: "approved"/"rejected"}

    # Results
    final_report: Optional[Dict[str, Any]]

    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    total_execution_time: Optional[float]
    error: Optional[str]
