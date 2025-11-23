"""
Orchestrator Agent V2 - LangGraph Implementation

This agent coordinates all sub-agents into a complete end-to-end testing workflow.

Key improvements over V1:
- LangGraph for structured workflow management
- Direct coordination of V2 agents (no LangChain dependency)
- Type-safe state management
- Better error handling and recovery
- HITL integration at each stage
- Fully testable
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents_v2.state import OrchestratorState
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from agents_v2.test_planner_agent_v2 import TestPlannerAgentV2
from agents_v2.test_generator_agent_v2 import TestGeneratorAgentV2
from agents_v2.test_executor_agent_v2 import TestExecutorAgentV2
from agents_v2.reporting_agent_v2 import ReportingAgentV2
from models.app_profile import ApplicationProfile
from utils.logger import get_logger

logger = get_logger(__name__)


class OrchestratorAgentV2:
    """
    Orchestrator Agent using LangGraph to coordinate all sub-agents

    Workflow:
    1. Initialize - Setup state and validate inputs
    2. Discovery - Discover application elements
    3. Planning - Create test plan
    4. Generation - Generate test scripts
    5. Execution - Execute tests
    6. Reporting - Generate reports
    7. Finalize - Compile final results
    """

    def __init__(
        self,
        app_profile: ApplicationProfile,
        output_dir: str = "generated_tests",
        reports_dir: str = "reports",
        enable_hitl: bool = False,
    ):
        """
        Initialize Orchestrator Agent

        Args:
            app_profile: Application profile configuration
            output_dir: Directory for generated test scripts
            reports_dir: Directory for test reports
            enable_hitl: Enable human-in-the-loop approvals
        """
        self.app_profile = app_profile
        self.output_dir = output_dir
        self.reports_dir = reports_dir
        self.enable_hitl = enable_hitl

        # Initialize sub-agents
        self.discovery_agent = DiscoveryAgentV2(
            app_profile=app_profile,
            enable_hitl=enable_hitl,
        )

        self.test_planner = TestPlannerAgentV2(
            app_profile=app_profile,
            enable_hitl=enable_hitl,
        )

        self.test_generator = TestGeneratorAgentV2(
            app_profile=app_profile,
            output_dir=output_dir,
            enable_hitl=enable_hitl,
        )

        self.test_executor = TestExecutorAgentV2(
            framework=app_profile.test_framework.value,
            enable_hitl=enable_hitl,
        )

        self.reporting_agent = ReportingAgentV2(
            output_dir=reports_dir,
            enable_hitl=enable_hitl,
        )

        self.graph = self._build_graph()

        logger.info(
            f"OrchestratorAgentV2 initialized for {app_profile.name} "
            f"(HITL: {enable_hitl})"
        )

    def _build_graph(self) -> StateGraph:
        """
        Build the master workflow graph

        Graph structure:
            START
              ↓
           initialize
              ↓
           run_discovery
              ↓
           run_planning
              ↓
           run_generation
              ↓
           run_execution
              ↓
           run_reporting
              ↓
           finalize
              ↓
            END
        """
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("run_discovery", self._run_discovery_node)
        workflow.add_node("run_planning", self._run_planning_node)
        workflow.add_node("run_generation", self._run_generation_node)
        workflow.add_node("run_execution", self._run_execution_node)
        workflow.add_node("run_reporting", self._run_reporting_node)
        workflow.add_node("finalize", self._finalize_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges - sequential workflow
        workflow.add_edge("initialize", "run_discovery")

        # Conditional routing after each stage
        workflow.add_conditional_edges(
            "run_discovery",
            self._check_stage_success,
            {
                "continue": "run_planning",
                "error": "handle_error",
            }
        )

        workflow.add_conditional_edges(
            "run_planning",
            self._check_stage_success,
            {
                "continue": "run_generation",
                "error": "handle_error",
            }
        )

        workflow.add_conditional_edges(
            "run_generation",
            self._check_stage_success,
            {
                "continue": "run_execution",
                "error": "handle_error",
            }
        )

        workflow.add_conditional_edges(
            "run_execution",
            self._check_stage_success,
            {
                "continue": "run_reporting",
                "error": "handle_error",
            }
        )

        workflow.add_edge("run_reporting", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=MemorySaver())

    # ========== Graph Nodes ==========

    def _initialize_node(self, state: OrchestratorState) -> OrchestratorState:
        """Initialize orchestrator state"""
        logger.info(f"Initializing orchestrator workflow for {state.get('app_profile').name}")

        state["start_time"] = datetime.now()
        state["workflow_status"] = "in_progress"
        state["current_stage"] = "initialization"
        state["completed_stages"] = []
        state["pending_approvals"] = []
        state["approval_responses"] = {}

        return state

    def _run_discovery_node(self, state: OrchestratorState) -> OrchestratorState:
        """Run discovery sub-workflow"""
        logger.info("Running Discovery Agent")

        state["current_stage"] = "discovery"

        try:
            # Run discovery agent
            # Get discovery parameters and unpack them
            discovery_params = state.get("discovery_params", {})

            # Extract URL from app profile if not in params
            url = discovery_params.get("url") or state["app_profile"].base_url

            discovery_state = self.discovery_agent.discover(
                url=url,
                max_depth=discovery_params.get("max_depth"),
                max_pages=discovery_params.get("max_pages"),
                **{k: v for k, v in discovery_params.items() if k not in ["url", "max_depth", "max_pages"]}
            )

            # Store discovery state
            state["discovery_state"] = discovery_state

            # Check if successful
            if discovery_state.get("status") == "completed":
                state["completed_stages"].append("discovery")
                logger.info(
                    f"Discovery completed: {len(discovery_state.get('elements', []))} elements found"
                )
            else:
                state["error"] = f"Discovery failed: {discovery_state.get('error')}"
                state["workflow_status"] = "failed"

        except Exception as e:
            state["error"] = f"Discovery exception: {str(e)}"
            state["workflow_status"] = "failed"
            logger.error(f"Discovery stage failed: {e}")

        return state

    def _run_planning_node(self, state: OrchestratorState) -> OrchestratorState:
        """Run test planning sub-workflow"""
        logger.info("Running Test Planner Agent")

        state["current_stage"] = "planning"

        try:
            # Get discovery results
            discovery_state = state.get("discovery_state", {})
            discovery_result = discovery_state.get("discovery_result", {})

            # Run test planner
            planning_state = self.test_planner.create_plan(
                feature_description=state.get("feature_description", "Complete regression test suite"),
                discovery_result=discovery_result,
            )

            # Store planning state
            state["planning_state"] = planning_state

            # Check if successful
            if planning_state.get("status") == "completed":
                state["completed_stages"].append("planning")
                test_cases_count = len(planning_state.get("test_cases", []))
                logger.info(f"Planning completed: {test_cases_count} test cases created")
            else:
                state["error"] = f"Planning failed: {planning_state.get('error')}"
                state["workflow_status"] = "failed"

        except Exception as e:
            state["error"] = f"Planning exception: {str(e)}"
            state["workflow_status"] = "failed"
            logger.error(f"Planning stage failed: {e}")

        return state

    def _run_generation_node(self, state: OrchestratorState) -> OrchestratorState:
        """Run test generation sub-workflow"""
        logger.info("Running Test Generator Agent")

        state["current_stage"] = "generation"

        try:
            # Get test cases from planning
            planning_state = state.get("planning_state", {})
            test_cases = planning_state.get("test_cases", [])

            if not test_cases:
                state["error"] = "No test cases available from planning stage"
                state["workflow_status"] = "failed"
                return state

            # Run test generator
            generation_state = self.test_generator.generate_tests(
                test_cases=test_cases,
            )

            # Store generation state
            state["generation_state"] = generation_state

            # Check if successful
            if generation_state.get("status") == "completed":
                state["completed_stages"].append("generation")
                scripts_count = len(generation_state.get("generated_scripts", []))
                logger.info(f"Generation completed: {scripts_count} scripts generated")
            else:
                state["error"] = f"Generation failed: {generation_state.get('error')}"
                state["workflow_status"] = "failed"

        except Exception as e:
            state["error"] = f"Generation exception: {str(e)}"
            state["workflow_status"] = "failed"
            logger.error(f"Generation stage failed: {e}")

        return state

    def _run_execution_node(self, state: OrchestratorState) -> OrchestratorState:
        """Run test execution sub-workflow"""
        logger.info("Running Test Executor Agent")

        state["current_stage"] = "execution"

        try:
            # Get generated scripts
            generation_state = state.get("generation_state", {})
            generated_scripts = generation_state.get("generated_scripts", [])

            if not generated_scripts:
                state["error"] = "No test scripts available from generation stage"
                state["workflow_status"] = "failed"
                return state

            # Run test executor
            execution_state = self.test_executor.execute_tests(
                test_scripts=generated_scripts,
            )

            # Store execution state
            state["execution_state"] = execution_state

            # Check if successful
            if execution_state.get("status") == "completed":
                state["completed_stages"].append("execution")
                passed = execution_state.get("passed_count", 0)
                failed = execution_state.get("failed_count", 0)
                logger.info(f"Execution completed: {passed} passed, {failed} failed")
            else:
                state["error"] = f"Execution failed: {execution_state.get('error')}"
                state["workflow_status"] = "failed"

        except Exception as e:
            state["error"] = f"Execution exception: {str(e)}"
            state["workflow_status"] = "failed"
            logger.error(f"Execution stage failed: {e}")

        return state

    def _run_reporting_node(self, state: OrchestratorState) -> OrchestratorState:
        """Run reporting sub-workflow"""
        logger.info("Running Reporting Agent")

        state["current_stage"] = "reporting"

        try:
            # Get test results from execution
            execution_state = state.get("execution_state", {})
            test_results = execution_state.get("test_results", [])

            if not test_results:
                logger.warning("No test results available, generating empty report")

            # Run reporting agent
            reporting_state = self.reporting_agent.generate_reports(
                test_results=test_results,
                app_name=state["app_profile"].name,
                report_formats=["html", "json", "markdown"],
            )

            # Store final report in orchestrator state
            state["final_report"] = self.reporting_agent.get_reporting_result(reporting_state)

            # Check if successful
            if reporting_state.get("status") == "completed":
                state["completed_stages"].append("reporting")
                reports_count = len(reporting_state.get("generated_reports", []))
                logger.info(f"Reporting completed: {reports_count} reports generated")
            else:
                # Don't fail workflow on reporting errors
                logger.warning(f"Reporting had issues: {reporting_state.get('error')}")
                state["completed_stages"].append("reporting")

        except Exception as e:
            # Don't fail workflow on reporting errors
            logger.warning(f"Reporting stage had issues: {e}")
            state["completed_stages"].append("reporting")

        return state

    def _finalize_node(self, state: OrchestratorState) -> OrchestratorState:
        """Finalize orchestrator workflow"""
        logger.info("Finalizing orchestrator workflow")

        state["end_time"] = datetime.now()
        state["workflow_status"] = "completed"
        state["current_stage"] = "finalized"

        # Calculate total execution time
        if state.get("start_time") and state.get("end_time"):
            total_time = (state["end_time"] - state["start_time"]).total_seconds()
            state["total_execution_time"] = total_time
            logger.info(f"Workflow completed in {total_time:.2f} seconds")

        # Log summary
        completed_stages = state.get("completed_stages", [])
        logger.info(f"Completed stages: {', '.join(completed_stages)}")

        return state

    def _handle_error_node(self, state: OrchestratorState) -> OrchestratorState:
        """Handle workflow errors"""
        logger.error(f"Workflow failed at stage '{state.get('current_stage')}': {state.get('error')}")

        state["end_time"] = datetime.now()
        state["workflow_status"] = "failed"

        # Calculate partial execution time
        if state.get("start_time") and state.get("end_time"):
            total_time = (state["end_time"] - state["start_time"]).total_seconds()
            state["total_execution_time"] = total_time

        return state

    # ========== Routing Functions ==========

    def _check_stage_success(self, state: OrchestratorState) -> str:
        """Check if current stage succeeded"""
        if state.get("workflow_status") == "failed":
            return "error"
        return "continue"

    # ========== Public Methods ==========

    def run_full_workflow(
        self,
        feature_description: Optional[str] = None,
        discovery_params: Optional[Dict[str, Any]] = None,
    ) -> OrchestratorState:
        """
        Run complete end-to-end testing workflow

        Args:
            feature_description: Description of feature to test
            discovery_params: Optional discovery parameters

        Returns:
            Final orchestrator state
        """
        logger.info("Starting full orchestrator workflow")

        # Prepare initial state
        initial_state: OrchestratorState = {
            "app_profile": self.app_profile,
            "feature_description": feature_description or "Complete regression test suite",
            "user_request": "Run full automated testing workflow",
        }

        if discovery_params:
            initial_state["discovery_params"] = discovery_params

        # Execute workflow
        try:
            # Config with thread_id is required by LangGraph checkpointer
            config = {"configurable": {"thread_id": "orchestrator_main"}}
            final_state = self.graph.invoke(initial_state, config=config)
            return final_state
        except Exception as e:
            logger.error(f"Orchestrator workflow failed: {e}")
            return {
                "workflow_status": "failed",
                "error": str(e),
                "end_time": datetime.now(),
                "completed_stages": [],
            }

    def get_workflow_summary(self, state: OrchestratorState) -> Dict[str, Any]:
        """
        Extract formatted workflow summary from state

        Args:
            state: Final workflow state

        Returns:
            Formatted summary
        """
        summary = {
            "status": state.get("workflow_status", "unknown"),
            "completed_stages": state.get("completed_stages", []),
            "total_execution_time": state.get("total_execution_time"),
            "error": state.get("error"),
        }

        # Add stage summaries
        if "discovery_state" in state:
            discovery_state = state["discovery_state"]
            summary["discovery"] = {
                "elements_found": len(discovery_state.get("elements", [])),
                "pages_found": len(discovery_state.get("pages", [])),
            }

        if "planning_state" in state:
            planning_state = state["planning_state"]
            summary["planning"] = {
                "test_cases_created": len(planning_state.get("test_cases", [])),
            }

        if "generation_state" in state:
            generation_state = state["generation_state"]
            summary["generation"] = {
                "scripts_generated": len(generation_state.get("generated_scripts", [])),
                "passed_validation": generation_state.get("passed_count", 0),
            }

        if "execution_state" in state:
            execution_state = state["execution_state"]
            summary["execution"] = {
                "total_tests": len(execution_state.get("test_results", [])),
                "passed": execution_state.get("passed_count", 0),
                "failed": execution_state.get("failed_count", 0),
            }

        if "final_report" in state:
            final_report = state["final_report"]
            summary["reporting"] = {
                "reports_generated": len(final_report.get("generated_reports", [])),
                "formats": [r.get("format") for r in final_report.get("generated_reports", [])],
            }

        return summary
