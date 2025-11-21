"""
Test Planner Agent V2 - LangGraph Implementation

This agent creates comprehensive test plans using reusable tools and LangGraph for workflow orchestration.

Key improvements over V1:
- Uses reusable tools instead of embedded logic
- LangGraph for state management and workflow
- RAG tools for knowledge retrieval
- Better error handling and validation
- HITL integration ready
- Fully testable with mocked tools
"""

from datetime import datetime
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents_v2.state import TestPlanningState
from tools import get_tool
from tools.base import ToolStatus
from models.app_profile import ApplicationProfile
from models.approval import ApprovalType
from hitl.approval_manager import ApprovalManager
from utils.logger import get_logger

logger = get_logger(__name__)


class TestPlannerAgentV2:
    """
    Test Planner Agent using LangGraph and reusable tools

    Workflow:
    1. Initialize state
    2. Validate and sanitize inputs
    3. Retrieve similar tests from RAG
    4. Get test patterns
    5. Generate test plan with LLM
    6. Extract test cases from plan
    7. Process and return results
    """

    def __init__(
        self,
        app_profile: ApplicationProfile,
        enable_hitl: bool = False,
    ):
        """
        Initialize Test Planner Agent

        Args:
            app_profile: Application profile configuration
            enable_hitl: Enable human-in-the-loop for approvals
        """
        self.app_profile = app_profile
        self.enable_hitl = enable_hitl

        # Initialize approval manager if HITL is enabled
        self.approval_manager = None
        if enable_hitl:
            from config.settings import get_settings
            settings = get_settings()
            self.approval_manager = ApprovalManager(
                hitl_mode=settings.hitl_mode,
                timeout=settings.approval_timeout
            )

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow

        Graph structure:
            START
              ↓
           initialize
              ↓
           validate_input
              ↓
           retrieve_similar_tests
              ↓
           retrieve_patterns
              ↓
           generate_plan
              ↓
           extract_test_cases
              ↓
           request_approval (if HITL enabled)
              ↓
           process_results
              ↓
            END
        """
        workflow = StateGraph(TestPlanningState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("retrieve_similar_tests", self._retrieve_similar_tests_node)
        workflow.add_node("retrieve_patterns", self._retrieve_patterns_node)
        workflow.add_node("generate_plan", self._generate_plan_node)
        workflow.add_node("extract_test_cases", self._extract_test_cases_node)
        workflow.add_node("request_approval", self._request_approval_node)
        workflow.add_node("process_results", self._process_results_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges
        workflow.add_edge("initialize", "validate_input")
        workflow.add_edge("validate_input", "retrieve_similar_tests")
        workflow.add_edge("retrieve_similar_tests", "retrieve_patterns")
        workflow.add_edge("retrieve_patterns", "generate_plan")

        # Conditional edge after plan generation
        workflow.add_conditional_edges(
            "generate_plan",
            self._check_plan_generation,
            {
                "success": "extract_test_cases",
                "error": "handle_error",
            }
        )

        workflow.add_edge("extract_test_cases", "request_approval")
        workflow.add_edge("request_approval", "process_results")
        workflow.add_edge("process_results", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=MemorySaver())

    # ========== Graph Nodes ==========

    def _initialize_node(self, state: TestPlanningState) -> TestPlanningState:
        """Initialize workflow state"""
        logger.info(f"Initializing test planning for {self.app_profile.name}")

        state["start_time"] = datetime.now()
        state["status"] = "in_progress"
        state["app_profile"] = self.app_profile
        state["similar_tests"] = []
        state["test_patterns"] = []
        state["test_cases"] = []
        state["requires_approval"] = self.enable_hitl

        return state

    def _validate_input_node(self, state: TestPlanningState) -> TestPlanningState:
        """Validate and sanitize inputs using InputSanitizerTool"""
        logger.info("Validating inputs")

        try:
            # Get input sanitizer tool
            sanitizer = get_tool("input_sanitizer", config={
                "strict_mode": False,
                "max_length": 10000,
            })

            # Sanitize feature description
            feature_description = state.get("feature_description", "")

            if feature_description:
                result = sanitizer.execute(
                    text=feature_description,
                    check_prompt_injection=True,
                    check_sql_injection=False,  # Not needed for test planning
                    check_command_injection=False,
                )

                if result.is_success():
                    # Update state with sanitized input
                    state["feature_description"] = result.data
                    if result.metadata.get("warnings"):
                        logger.warning(f"Input validation warnings: {result.metadata['warnings']}")
                else:
                    state["error"] = f"Input validation failed: {result.error}"
                    state["status"] = "failed"
                    return state

        except Exception as e:
            logger.error(f"Validation error: {e}")
            state["error"] = f"Validation error: {str(e)}"

        return state

    def _retrieve_similar_tests_node(self, state: TestPlanningState) -> TestPlanningState:
        """Retrieve similar tests from knowledge base using VectorSearchTool"""
        logger.info("Retrieving similar tests from knowledge base")

        try:
            # Get vector search tool
            search_tool = get_tool("vector_search", config={
                "collection_name": "test_knowledge"
            })

            # Search for similar tests
            feature_description = state["feature_description"]
            app_name = self.app_profile.name

            result = search_tool.execute(
                query=feature_description,
                k=5,
                doc_type="test_case",
                application=app_name,
            )

            if result.is_success():
                state["similar_tests"] = result.data.get("results", [])
                logger.info(f"Retrieved {result.data.get('count', 0)} similar tests")
            else:
                logger.warning(f"Failed to retrieve similar tests: {result.error}")
                state["similar_tests"] = []

        except Exception as e:
            logger.error(f"Error retrieving similar tests: {e}")
            state["similar_tests"] = []

        return state

    def _retrieve_patterns_node(self, state: TestPlanningState) -> TestPlanningState:
        """Retrieve test patterns using TestPatternRetrieverTool"""
        logger.info("Retrieving test patterns")

        try:
            # Get pattern retriever tool
            pattern_tool = get_tool("test_pattern_retriever", config={
                "collection_name": "test_knowledge"
            })

            # Get test patterns for the feature
            feature = state["feature_description"]

            result = pattern_tool.execute(
                pattern_type="feature",
                feature=feature,
                k=3,
            )

            if result.is_success():
                state["test_patterns"] = result.data.get("patterns", [])
                logger.info(f"Retrieved {result.data.get('count', 0)} test patterns")
            else:
                logger.warning(f"Failed to retrieve patterns: {result.error}")
                state["test_patterns"] = []

        except Exception as e:
            logger.error(f"Error retrieving patterns: {e}")
            state["test_patterns"] = []

        return state

    def _generate_plan_node(self, state: TestPlanningState) -> TestPlanningState:
        """Generate test plan using TestPlanGeneratorTool"""
        logger.info("Generating test plan with LLM")

        try:
            # Get plan generator tool
            generator_tool = get_tool("test_plan_generator")

            # Prepare discovery info if available
            discovery_info = None
            if state.get("discovery_result"):
                discovery_result = state["discovery_result"]
                discovery_info = {
                    "total_elements": len(discovery_result.get("elements", [])),
                    "total_pages": len(discovery_result.get("pages", [])),
                    "element_types": discovery_result.get("metadata", {}).get("element_types", {}),
                }

            # Generate plan
            result = generator_tool.execute(
                feature_description=state["feature_description"],
                app_name=self.app_profile.name,
                app_type=self.app_profile.app_type.value,
                discovery_info=discovery_info,
                similar_tests=state.get("similar_tests", []),
            )

            if result.is_success():
                state["test_plan"] = result.data
                logger.info("Test plan generated successfully")
            else:
                state["error"] = f"Plan generation failed: {result.error}"
                state["status"] = "failed"
                logger.error(f"Plan generation failed: {result.error}")

        except Exception as e:
            state["error"] = f"Plan generation error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"Plan generation exception: {e}")

        return state

    def _extract_test_cases_node(self, state: TestPlanningState) -> TestPlanningState:
        """Extract test cases using TestCaseExtractorTool"""
        logger.info("Extracting test cases from plan")

        try:
            # Get extractor tool
            extractor_tool = get_tool("test_case_extractor")

            # Extract test cases from LLM response
            test_plan = state["test_plan"]
            llm_response = test_plan.get("llm_response", "")

            result = extractor_tool.execute(
                llm_response=llm_response,
                app_name=self.app_profile.name,
                feature=state["feature_description"],
            )

            if result.is_success():
                state["test_cases"] = result.data.get("test_cases", [])
                state["coverage_analysis"] = {
                    "coverage": result.data.get("raw_sections", {}).get("coverage", ""),
                    "gaps": result.data.get("raw_sections", {}).get("gaps", ""),
                    "recommendations": result.data.get("raw_sections", {}).get("recommendations", ""),
                }
                logger.info(f"Extracted {result.data.get('count', 0)} test cases")
            else:
                logger.warning(f"Test case extraction failed: {result.error}")
                state["test_cases"] = []

        except Exception as e:
            logger.error(f"Test case extraction error: {e}")
            state["test_cases"] = []

        return state

    def _request_approval_node(self, state: TestPlanningState) -> TestPlanningState:
        """Request approval for test plan if HITL is enabled"""
        if not self.enable_hitl or not self.approval_manager:
            logger.info("HITL not enabled, skipping approval request")
            return state

        logger.info("Requesting approval for test plan")

        try:
            from models.approval import Approval, ApprovalStatus
            from utils.helpers import generate_approval_id, save_json
            from pathlib import Path

            # Prepare test plan summary
            test_cases = state.get("test_cases", [])
            test_plan = state.get("test_plan", {})

            summary = (
                f"Test plan for {self.app_profile.name}: "
                f"{state.get('feature_description', 'N/A')}\n"
                f"Generated {len(test_cases)} test cases"
            )

            # Prepare approval data
            approval_data = {
                "feature_description": state.get("feature_description"),
                "app_name": self.app_profile.name,
                "test_cases_count": len(test_cases),
                "test_cases": [
                    {
                        "id": tc.get("id"),
                        "name": tc.get("name"),
                        "description": tc.get("description", ""),
                        "priority": tc.get("priority", "medium")
                    }
                    for tc in test_cases
                ],
                "test_plan": test_plan
            }

            # Create approval object
            approval_id = generate_approval_id()
            approval = Approval(
                id=approval_id,
                approval_type=ApprovalType.TEST_PLAN,
                item_id=f"plan-{self.app_profile.name}",
                item_data=approval_data,
                item_summary=summary,
                status=ApprovalStatus.PENDING,
                requested_at=datetime.now(),
                timeout_seconds=self.approval_manager.default_timeout,
                context={"agent": "test_planner", "app": self.app_profile.name}
            )

            # Save approval to file
            approvals_dir = Path("approvals")
            approvals_dir.mkdir(exist_ok=True)
            approval_file = approvals_dir / f"{approval_id}.json"
            save_json(approval.model_dump(), str(approval_file))

            logger.info(f"Approval request created: {approval_id}")
            logger.info(f"Waiting for approval via web interface...")

            # Store approval ID in state so orchestrator can check it later
            state["approval_id"] = approval_id
            state["approval_status"] = "pending"

            # For now, we'll just create the approval and continue
            # In a production system, you'd poll or use webhooks for approval status

        except Exception as e:
            logger.error(f"Error requesting approval: {e}")
            # Continue without approval in case of error
            state["approval_status"] = "error"

        return state

    def _process_results_node(self, state: TestPlanningState) -> TestPlanningState:
        """Process and finalize test planning results"""
        logger.info("Processing test planning results")

        state["end_time"] = datetime.now()
        state["status"] = "completed"

        # Calculate execution time
        if state.get("start_time") and state.get("end_time"):
            execution_time = (state["end_time"] - state["start_time"]).total_seconds()
            logger.info(f"Test planning completed in {execution_time:.2f} seconds")

        return state

    def _handle_error_node(self, state: TestPlanningState) -> TestPlanningState:
        """Handle errors and cleanup"""
        logger.error(f"Test planning failed: {state.get('error', 'Unknown error')}")

        state["end_time"] = datetime.now()
        state["status"] = "failed"

        return state

    # ========== Routing Functions ==========

    def _check_plan_generation(self, state: TestPlanningState) -> str:
        """Check if plan generation was successful"""
        if state.get("error"):
            return "error"
        if state.get("test_plan"):
            return "success"
        return "error"

    # ========== Public Methods ==========

    def create_plan(
        self,
        feature_description: str,
        discovery_result: Optional[Dict[str, Any]] = None,
    ) -> TestPlanningState:
        """
        Create a test plan

        Args:
            feature_description: Description of feature to test
            discovery_result: Optional discovery results

        Returns:
            Final state with test plan
        """
        # Prepare initial state
        initial_state: TestPlanningState = {
            "app_profile": self.app_profile,
            "feature_description": feature_description,
            "discovery_result": discovery_result,
        }

        # Execute graph
        try:
            final_state = self.graph.invoke(
                initial_state,
                config={"configurable": {"thread_id": "planning_session"}}
            )
            return final_state
        except Exception as e:
            logger.error(f"Test planning workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now(),
            }

    def get_test_plan(self, state: TestPlanningState) -> Dict[str, Any]:
        """
        Extract formatted test plan from state

        Args:
            state: Final workflow state

        Returns:
            Formatted test plan
        """
        return {
            "status": state.get("status"),
            "test_plan": state.get("test_plan"),
            "test_cases": state.get("test_cases", []),
            "coverage_analysis": state.get("coverage_analysis", {}),
            "statistics": {
                "similar_tests_found": len(state.get("similar_tests", [])),
                "patterns_retrieved": len(state.get("test_patterns", [])),
                "test_cases_extracted": len(state.get("test_cases", [])),
            },
            "metadata": {
                "app_name": self.app_profile.name,
                "feature": state.get("feature_description", ""),
                "execution_time": (
                    (state["end_time"] - state["start_time"]).total_seconds()
                    if state.get("end_time") and state.get("start_time")
                    else None
                ),
            },
            "error": state.get("error"),
        }
