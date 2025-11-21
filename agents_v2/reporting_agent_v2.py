"""
Reporting Agent V2 - LangGraph Implementation

This agent generates test execution reports using reusable tools and LangGraph.

Key improvements over V1:
- Uses reusable tools instead of embedded logic
- LangGraph for state management and workflow
- Multiple format generation
- Better error handling
- HITL integration ready
- Fully testable with mocked tools
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents_v2.state import ReportingState
from tools import get_tool
from tools.base import ToolStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class ReportingAgentV2:
    """
    Reporting Agent using LangGraph and reusable tools

    Workflow:
    1. Initialize state
    2. Validate test results
    3. Generate reports (for each format)
    4. Write reports to disk
    5. Process and return results
    """

    def __init__(
        self,
        output_dir: str = "reports",
        enable_hitl: bool = False,
    ):
        """
        Initialize Reporting Agent

        Args:
            output_dir: Directory to write reports
            enable_hitl: Enable human-in-the-loop for approvals
        """
        self.output_dir = output_dir
        self.enable_hitl = enable_hitl
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow

        Graph structure:
            START
              ↓
           initialize
              ↓
           validate_results
              ↓
           generate_reports
              ↓
           write_reports
              ↓
           process_results
              ↓
            END
        """
        workflow = StateGraph(ReportingState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("validate_results", self._validate_results_node)
        workflow.add_node("generate_reports", self._generate_reports_node)
        workflow.add_node("write_reports", self._write_reports_node)
        workflow.add_node("process_results", self._process_results_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges
        workflow.add_edge("initialize", "validate_results")

        # Conditional edge after validation
        workflow.add_conditional_edges(
            "validate_results",
            self._check_validation,
            {
                "success": "generate_reports",
                "error": "handle_error",
            }
        )

        workflow.add_edge("generate_reports", "write_reports")
        workflow.add_edge("write_reports", "process_results")
        workflow.add_edge("process_results", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=MemorySaver())

    # ========== Graph Nodes ==========

    def _initialize_node(self, state: ReportingState) -> ReportingState:
        """Initialize workflow state"""
        logger.info(f"Initializing report generation for {state.get('app_name', 'Unknown')}")

        state["start_time"] = datetime.now()
        state["status"] = "in_progress"
        state["generated_reports"] = []

        # Set default formats if not provided
        if "report_formats" not in state or not state["report_formats"]:
            state["report_formats"] = ["html"]

        return state

    def _validate_results_node(self, state: ReportingState) -> ReportingState:
        """Validate test results"""
        logger.info("Validating test results")

        test_results = state.get("test_results", [])
        app_name = state.get("app_name", "")

        if not test_results:
            state["error"] = "No test results provided"
            state["status"] = "failed"
            return state

        if not app_name or not app_name.strip():
            state["error"] = "Application name is required"
            state["status"] = "failed"
            return state

        # Validate formats
        report_formats = state.get("report_formats", [])
        valid_formats = ["html", "json", "markdown"]

        invalid_formats = [f for f in report_formats if f not in valid_formats]
        if invalid_formats:
            state["error"] = f"Invalid report formats: {invalid_formats}"
            state["status"] = "failed"
            return state

        logger.info(f"Validated {len(test_results)} test results for {len(report_formats)} formats")

        return state

    def _generate_reports_node(self, state: ReportingState) -> ReportingState:
        """Generate reports using ReportGeneratorTool"""
        logger.info("Generating reports")

        try:
            # Get report generator tool
            generator = get_tool("report_generator")

            test_results = state["test_results"]
            app_name = state["app_name"]
            report_formats = state["report_formats"]
            generated_reports = []

            # Generate report for each format
            for format in report_formats:
                logger.debug(f"Generating {format} report")

                result = generator.execute(
                    test_results=test_results,
                    app_name=app_name,
                    format=format,
                    include_stats=True,
                )

                if result.is_success():
                    generated_reports.append({
                        "format": format,
                        "content": result.data["report_content"],
                        "statistics": result.data["statistics"],
                    })

                    # Store statistics in state (from last report)
                    state["statistics"] = result.data["statistics"]
                else:
                    logger.error(f"Report generation failed for {format}: {result.error}")
                    # Continue with other formats

            if not generated_reports:
                state["error"] = "Failed to generate any reports"
                state["status"] = "failed"
            else:
                state["generated_reports"] = generated_reports
                logger.info(f"Generated {len(generated_reports)} reports")

        except Exception as e:
            state["error"] = f"Report generation error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"Report generation exception: {e}")

        return state

    def _write_reports_node(self, state: ReportingState) -> ReportingState:
        """Write reports to disk using ReportWriterTool"""
        logger.info("Writing reports to disk")

        try:
            # Get report writer tool
            writer = get_tool("report_writer", config={
                "output_dir": self.output_dir
            })

            generated_reports = state["generated_reports"]
            written_count = 0

            for report in generated_reports:
                format = report["format"]
                content = report["content"]

                result = writer.execute(
                    report_content=content,
                    format=format,
                    overwrite=True,  # Allow overwriting for generated reports
                )

                if result.is_success():
                    # Update report with file path
                    report["file_path"] = result.data["file_path"]
                    report["filename"] = result.data["filename"]
                    written_count += 1
                    logger.debug(f"Wrote {format} report: {result.data['file_path']}")
                else:
                    logger.error(f"Failed to write {format} report: {result.error}")

            if written_count == 0:
                state["error"] = "Failed to write any reports"
                state["status"] = "failed"
            else:
                logger.info(f"Wrote {written_count} reports to disk")

        except Exception as e:
            state["error"] = f"File writing error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"File writing exception: {e}")

        return state

    def _process_results_node(self, state: ReportingState) -> ReportingState:
        """Process and finalize report generation results"""
        logger.info("Processing report generation results")

        state["end_time"] = datetime.now()
        state["status"] = "completed"

        # Calculate execution time
        if state.get("start_time") and state.get("end_time"):
            execution_time = (state["end_time"] - state["start_time"]).total_seconds()
            state["execution_time"] = execution_time
            logger.info(f"Report generation completed in {execution_time:.2f} seconds")

        # Log summary
        generated_count = len(state.get("generated_reports", []))
        written_count = sum(1 for r in state.get("generated_reports", []) if "file_path" in r)

        logger.info(f"Generated {generated_count} reports, wrote {written_count} to disk")

        return state

    def _handle_error_node(self, state: ReportingState) -> ReportingState:
        """Handle errors and cleanup"""
        logger.error(f"Report generation failed: {state.get('error', 'Unknown error')}")

        state["end_time"] = datetime.now()
        state["status"] = "failed"

        return state

    # ========== Routing Functions ==========

    def _check_validation(self, state: ReportingState) -> str:
        """Check if validation was successful"""
        if state.get("error"):
            return "error"
        if state.get("test_results") and state.get("app_name"):
            return "success"
        return "error"

    # ========== Public Methods ==========

    def generate_reports(
        self,
        test_results: List[Dict[str, Any]],
        app_name: str,
        report_formats: Optional[List[str]] = None,
    ) -> ReportingState:
        """
        Generate test execution reports

        Args:
            test_results: List of test result dictionaries
            app_name: Application name
            report_formats: List of formats to generate (default: ["html"])

        Returns:
            Final state with generated reports
        """
        # Prepare initial state
        initial_state: ReportingState = {
            "test_results": test_results,
            "app_name": app_name,
        }

        if report_formats:
            initial_state["report_formats"] = report_formats

        # Execute graph
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"Report generation workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now(),
                "generated_reports": [],
            }

    def get_reporting_result(self, state: ReportingState) -> Dict[str, Any]:
        """
        Extract formatted reporting result from state

        Args:
            state: Final workflow state

        Returns:
            Formatted reporting result
        """
        return {
            "status": state.get("status"),
            "generated_reports": state.get("generated_reports", []),
            "statistics": state.get("statistics", {}),
            "metadata": {
                "app_name": state.get("app_name", ""),
                "formats": state.get("report_formats", []),
                "execution_time": state.get("execution_time"),
            },
            "error": state.get("error"),
        }
