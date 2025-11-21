"""
Test Executor Agent V2 - LangGraph Implementation

This agent executes generated test scripts and collects results using reusable tools and LangGraph.

Key improvements over V1:
- Uses reusable tools instead of adapter calls
- LangGraph for state management and workflow
- Safe execution with resource limits
- Better error handling
- HITL integration ready
- Fully testable with mocked tools
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents_v2.state import TestExecutionState
from tools import get_tool
from tools.base import ToolStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class TestExecutorAgentV2:
    """
    Test Executor Agent using LangGraph and reusable tools

    Workflow:
    1. Initialize state
    2. Validate test scripts
    3. Execute tests (sequential or parallel)
    4. Collect results
    5. Process and return results
    """

    def __init__(
        self,
        framework: str = "pytest",
        timeout_seconds: int = 300,
        enable_hitl: bool = False,
    ):
        """
        Initialize Test Executor Agent

        Args:
            framework: Test framework (pytest, unittest, etc.)
            timeout_seconds: Default timeout for test execution
            enable_hitl: Enable human-in-the-loop for failures
        """
        self.framework = framework
        self.timeout_seconds = timeout_seconds
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
           validate_scripts
              ↓
           execute_tests
              ↓
           collect_results
              ↓
           process_results
              ↓
            END
        """
        workflow = StateGraph(TestExecutionState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("validate_scripts", self._validate_scripts_node)
        workflow.add_node("execute_tests", self._execute_tests_node)
        workflow.add_node("collect_results", self._collect_results_node)
        workflow.add_node("process_results", self._process_results_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges
        workflow.add_edge("initialize", "validate_scripts")

        # Conditional edge after validation
        workflow.add_conditional_edges(
            "validate_scripts",
            self._check_validation,
            {
                "success": "execute_tests",
                "error": "handle_error",
            }
        )

        workflow.add_edge("execute_tests", "collect_results")
        workflow.add_edge("collect_results", "process_results")
        workflow.add_edge("process_results", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=MemorySaver())

    # ========== Graph Nodes ==========

    def _initialize_node(self, state: TestExecutionState) -> TestExecutionState:
        """Initialize workflow state"""
        logger.info(f"Initializing test execution for {len(state.get('test_scripts', []))} scripts")

        state["start_time"] = datetime.now()
        state["status"] = "in_progress"
        state["test_results"] = []
        state["passed_count"] = 0
        state["failed_count"] = 0
        state["skipped_count"] = 0

        # Set default execution config if not provided
        if "execution_config" not in state:
            state["execution_config"] = {
                "framework": self.framework,
                "timeout_seconds": self.timeout_seconds,
                "parallel": False,
                "capture_output": True,
            }

        return state

    def _validate_scripts_node(self, state: TestExecutionState) -> TestExecutionState:
        """Validate test scripts before execution"""
        logger.info("Validating test scripts")

        test_scripts = state.get("test_scripts", [])

        if not test_scripts:
            state["error"] = "No test scripts provided"
            state["status"] = "failed"
            return state

        # Validate each script exists
        from pathlib import Path
        validated_scripts = []

        for script in test_scripts:
            script_path = script.get("file_path") or script.get("script_path")

            if not script_path:
                logger.warning(f"Script missing file_path: {script}")
                continue

            # Check if file exists
            if not Path(script_path).exists():
                logger.warning(f"Script file not found: {script_path}")
                continue

            validated_scripts.append(script)

        state["test_scripts"] = validated_scripts

        if not validated_scripts:
            state["error"] = "No valid test scripts after validation"
            state["status"] = "failed"

        logger.info(f"Validated {len(validated_scripts)} scripts")

        return state

    def _execute_tests_node(self, state: TestExecutionState) -> TestExecutionState:
        """Execute test scripts using TestExecutorTool"""
        logger.info("Executing test scripts")

        try:
            # Get test executor tool
            executor = get_tool("test_executor")

            test_scripts = state["test_scripts"]
            execution_config = state["execution_config"]
            execution_results = []

            framework = execution_config.get("framework", self.framework)
            timeout_seconds = execution_config.get("timeout_seconds", self.timeout_seconds)
            parallel = execution_config.get("parallel", False)

            if parallel:
                # TODO: Implement parallel execution in future iteration
                logger.warning("Parallel execution not yet implemented, using sequential")
                parallel = False

            # Execute each script sequentially
            for idx, script in enumerate(test_scripts, 1):
                script_path = script.get("file_path") or script.get("script_path")
                test_case_id = script.get("test_case_id", f"test-{idx}")
                test_name = script.get("test_case_name") or script.get("name", f"Test {idx}")

                logger.debug(f"Executing {idx}/{len(test_scripts)}: {test_name}")

                result = executor.execute(
                    script_path=script_path,
                    framework=framework,
                    timeout_seconds=timeout_seconds,
                    capture_output=True,
                )

                if result.is_success() or result.is_failure():
                    # Store execution result with script metadata
                    execution_results.append({
                        "test_case_id": test_case_id,
                        "test_name": test_name,
                        "script_path": script_path,
                        "execution_data": result.data,
                        "execution_metadata": result.metadata,
                    })
                else:
                    logger.error(f"Script execution error for {test_name}: {result.error}")
                    # Store error result
                    execution_results.append({
                        "test_case_id": test_case_id,
                        "test_name": test_name,
                        "script_path": script_path,
                        "execution_data": {
                            "exit_code": -1,
                            "stdout": "",
                            "stderr": result.error or "Unknown error",
                            "duration_seconds": 0,
                            "timed_out": False,
                        },
                        "execution_metadata": result.metadata or {},
                    })

            if not execution_results:
                state["error"] = "Failed to execute any scripts"
                state["status"] = "failed"
            else:
                # Store raw execution results for collection phase
                state["execution_results"] = execution_results
                logger.info(f"Executed {len(execution_results)} scripts")

        except Exception as e:
            state["error"] = f"Script execution error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"Script execution exception: {e}")

        return state

    def _collect_results_node(self, state: TestExecutionState) -> TestExecutionState:
        """Collect and parse test results using ResultCollectorTool"""
        logger.info("Collecting test results")

        try:
            # Get result collector tool
            collector = get_tool("result_collector")

            execution_results = state.get("execution_results", [])
            test_results = []
            execution_config = state["execution_config"]
            framework = execution_config.get("framework", self.framework)

            for exec_result in execution_results:
                test_name = exec_result["test_name"]
                test_case_id = exec_result["test_case_id"]
                exec_data = exec_result["execution_data"]

                # Parse execution output
                result = collector.execute(
                    test_name=test_name,
                    test_case_id=test_case_id,
                    exit_code=exec_data["exit_code"],
                    stdout=exec_data["stdout"],
                    stderr=exec_data["stderr"],
                    duration_seconds=exec_data["duration_seconds"],
                    framework=framework,
                )

                if result.is_success():
                    # Create structured test result
                    test_result = {
                        "id": f"result-{test_case_id}",
                        "test_case_id": test_case_id,
                        "test_name": test_name,
                        "status": result.data["status"],
                        "error_message": result.data.get("error_message"),
                        "stack_trace": result.data.get("stack_trace"),
                        "step_results": result.data.get("step_results", []),
                        "metrics": {
                            "duration_seconds": exec_data["duration_seconds"],
                            "start_time": state["start_time"],
                            "end_time": datetime.now(),
                        },
                        "script_path": exec_result["script_path"],
                        "timed_out": exec_data.get("timed_out", False),
                    }

                    test_results.append(test_result)

                    # Update counts
                    if result.data["status"] == "passed":
                        state["passed_count"] = state.get("passed_count", 0) + 1
                    elif result.data["status"] == "failed":
                        state["failed_count"] = state.get("failed_count", 0) + 1
                    elif result.data["status"] == "skipped":
                        state["skipped_count"] = state.get("skipped_count", 0) + 1
                    else:
                        # Error status
                        state["failed_count"] = state.get("failed_count", 0) + 1

                else:
                    logger.error(f"Result collection failed for {test_name}: {result.error}")

            state["test_results"] = test_results
            logger.info(f"Collected {len(test_results)} test results")

        except Exception as e:
            logger.error(f"Result collection error: {e}")
            # Don't fail workflow on collection errors
            state["test_results"] = []

        return state

    def _process_results_node(self, state: TestExecutionState) -> TestExecutionState:
        """Process and finalize test execution results"""
        logger.info("Processing test execution results")

        state["end_time"] = datetime.now()
        state["status"] = "completed"

        # Calculate execution time
        if state.get("start_time") and state.get("end_time"):
            execution_time = (state["end_time"] - state["start_time"]).total_seconds()
            state["execution_time"] = execution_time
            logger.info(f"Test execution completed in {execution_time:.2f} seconds")

        # Log summary
        passed = state.get("passed_count", 0)
        failed = state.get("failed_count", 0)
        skipped = state.get("skipped_count", 0)
        total = len(state.get("test_results", []))

        logger.info(
            f"Execution summary: {passed} passed, {failed} failed, "
            f"{skipped} skipped out of {total} total"
        )

        return state

    def _handle_error_node(self, state: TestExecutionState) -> TestExecutionState:
        """Handle errors and cleanup"""
        logger.error(f"Test execution failed: {state.get('error', 'Unknown error')}")

        state["end_time"] = datetime.now()
        state["status"] = "failed"

        return state

    # ========== Routing Functions ==========

    def _check_validation(self, state: TestExecutionState) -> str:
        """Check if validation was successful"""
        if state.get("error"):
            return "error"
        if state.get("test_scripts"):
            return "success"
        return "error"

    # ========== Public Methods ==========

    def execute_tests(
        self,
        test_scripts: List[Dict[str, Any]],
        execution_config: Optional[Dict[str, Any]] = None,
    ) -> TestExecutionState:
        """
        Execute test scripts

        Args:
            test_scripts: List of test script dictionaries with file_path
            execution_config: Execution configuration (framework, timeout, etc.)

        Returns:
            Final state with test results
        """
        # Prepare initial state
        initial_state: TestExecutionState = {
            "test_scripts": test_scripts,
        }

        if execution_config:
            initial_state["execution_config"] = execution_config

        # Execute graph
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"Test execution workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now(),
                "test_results": [],
                "passed_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
            }

    def get_execution_result(self, state: TestExecutionState) -> Dict[str, Any]:
        """
        Extract formatted execution result from state

        Args:
            state: Final workflow state

        Returns:
            Formatted execution result
        """
        return {
            "status": state.get("status"),
            "test_results": state.get("test_results", []),
            "statistics": {
                "passed_count": state.get("passed_count", 0),
                "failed_count": state.get("failed_count", 0),
                "skipped_count": state.get("skipped_count", 0),
                "total_tests": len(state.get("test_results", [])),
                "execution_time": state.get("execution_time"),
            },
            "metadata": {
                "framework": state.get("execution_config", {}).get("framework", self.framework),
                "timeout_seconds": state.get("execution_config", {}).get("timeout_seconds", self.timeout_seconds),
            },
            "error": state.get("error"),
        }
