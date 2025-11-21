"""
Test Generator Agent V2 - LangGraph Implementation

This agent generates executable test scripts from test cases using reusable tools and LangGraph.

Key improvements over V1:
- Uses reusable tools instead of embedded logic
- LangGraph for state management and workflow
- Script validation before writing
- Better error handling
- HITL integration ready
- Fully testable with mocked tools
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents_v2.state import TestGenerationState
from tools import get_tool
from tools.base import ToolStatus
from models.app_profile import ApplicationProfile
from utils.logger import get_logger

logger = get_logger(__name__)


class TestGeneratorAgentV2:
    """
    Test Generator Agent using LangGraph and reusable tools

    Workflow:
    1. Initialize state
    2. Validate and sanitize test cases
    3. Generate script code for each test case
    4. Validate generated scripts
    5. Write scripts to disk
    6. Process and return results
    """

    def __init__(
        self,
        app_profile: ApplicationProfile,
        output_dir: str,
        enable_hitl: bool = False,
    ):
        """
        Initialize Test Generator Agent

        Args:
            app_profile: Application profile configuration
            output_dir: Directory to write generated scripts
            enable_hitl: Enable human-in-the-loop for approvals
        """
        self.app_profile = app_profile
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
           validate_test_cases
              ↓
           generate_scripts (for each test case)
              ↓
           validate_scripts
              ↓
           write_scripts
              ↓
           process_results
              ↓
            END
        """
        workflow = StateGraph(TestGenerationState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("validate_test_cases", self._validate_test_cases_node)
        workflow.add_node("generate_scripts", self._generate_scripts_node)
        workflow.add_node("validate_scripts", self._validate_scripts_node)
        workflow.add_node("write_scripts", self._write_scripts_node)
        workflow.add_node("process_results", self._process_results_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges
        workflow.add_edge("initialize", "validate_test_cases")
        workflow.add_edge("validate_test_cases", "generate_scripts")

        # Conditional edge after generation
        workflow.add_conditional_edges(
            "generate_scripts",
            self._check_generation,
            {
                "success": "validate_scripts",
                "error": "handle_error",
            }
        )

        workflow.add_edge("validate_scripts", "write_scripts")
        workflow.add_edge("write_scripts", "process_results")
        workflow.add_edge("process_results", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=MemorySaver())

    # ========== Graph Nodes ==========

    def _initialize_node(self, state: TestGenerationState) -> TestGenerationState:
        """Initialize workflow state"""
        logger.info(f"Initializing test generation for {self.app_profile.name}")

        state["start_time"] = datetime.now()
        state["status"] = "in_progress"
        state["framework"] = self.app_profile.test_framework.value
        state["generated_scripts"] = []
        state["validation_results"] = []
        state["requires_approval"] = self.enable_hitl

        return state

    def _validate_test_cases_node(self, state: TestGenerationState) -> TestGenerationState:
        """Validate test cases"""
        logger.info("Validating test cases")

        test_cases = state.get("test_cases", [])

        if not test_cases:
            state["error"] = "No test cases provided"
            state["status"] = "failed"
            return state

        # Basic validation
        validated_cases = []
        for tc in test_cases:
            if not tc.get("name"):
                logger.warning(f"Test case missing name: {tc}")
                continue

            validated_cases.append(tc)

        state["test_cases"] = validated_cases

        if not validated_cases:
            state["error"] = "No valid test cases after validation"
            state["status"] = "failed"

        return state

    def _generate_scripts_node(self, state: TestGenerationState) -> TestGenerationState:
        """Generate script code for each test case using ScriptGeneratorTool"""
        logger.info("Generating test scripts")

        try:
            # Get script generator tool
            generator = get_tool("script_generator")

            test_cases = state["test_cases"]
            framework = state["framework"]
            generated_scripts = []

            # Prepare app profile data
            app_profile_data = {
                "base_url": self.app_profile.base_url,
                "name": self.app_profile.name,
            }

            # Generate script for each test case
            for tc in test_cases:
                logger.debug(f"Generating script for: {tc.get('name')}")

                result = generator.execute(
                    test_case=tc,
                    framework=framework,
                    app_profile=app_profile_data,
                )

                if result.is_success():
                    generated_scripts.append({
                        "test_case_id": tc.get("id"),
                        "test_case_name": tc.get("name"),
                        "filename": result.data["filename"],
                        "content": result.data["script_content"],
                        "imports": result.data["imports"],
                    })
                else:
                    logger.error(f"Script generation failed for {tc.get('name')}: {result.error}")
                    # Continue with other test cases

            if not generated_scripts:
                state["error"] = "Failed to generate any scripts"
                state["status"] = "failed"
            else:
                state["generated_scripts"] = generated_scripts
                logger.info(f"Generated {len(generated_scripts)} scripts")

        except Exception as e:
            state["error"] = f"Script generation error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"Script generation exception: {e}")

        return state

    def _validate_scripts_node(self, state: TestGenerationState) -> TestGenerationState:
        """Validate generated scripts using ScriptValidatorTool"""
        logger.info("Validating generated scripts")

        try:
            # Get script validator tool
            validator = get_tool("script_validator")

            generated_scripts = state["generated_scripts"]
            framework = state["framework"]
            validation_results = []

            for script in generated_scripts:
                result = validator.execute(
                    script_content=script["content"],
                    framework=framework,
                    strict=False,  # Non-strict by default
                )

                validation_result = {
                    "filename": script["filename"],
                    "is_valid": result.data.get("is_valid", False) if result.is_success() else False,
                    "errors": result.data.get("errors", []) if result.is_success() else [result.error],
                    "warnings": result.data.get("warnings", []) if result.is_success() else [],
                    "suggestions": result.data.get("suggestions", []) if result.is_success() else [],
                }

                validation_results.append(validation_result)

                if not validation_result["is_valid"]:
                    logger.warning(f"Validation failed for {script['filename']}: {validation_result['errors']}")

            state["validation_results"] = validation_results

            # Check if all scripts are valid
            all_valid = all(vr["is_valid"] for vr in validation_results)

            if not all_valid:
                invalid_count = sum(1 for vr in validation_results if not vr["is_valid"])
                logger.warning(f"{invalid_count} scripts have validation errors")
                # Don't fail the workflow, but log warnings

        except Exception as e:
            logger.error(f"Script validation error: {e}")
            # Don't fail workflow on validation errors

        return state

    def _write_scripts_node(self, state: TestGenerationState) -> TestGenerationState:
        """Write scripts to disk using TestScriptWriterTool"""
        logger.info("Writing scripts to disk")

        try:
            # Get script writer tool
            writer = get_tool("test_script_writer", config={
                "output_dir": self.output_dir
            })

            generated_scripts = state["generated_scripts"]
            written_files = []

            for script in generated_scripts:
                result = writer.execute(
                    filename=script["filename"],
                    content=script["content"],
                    overwrite=True,  # Allow overwriting for generated tests
                    create_backup=True,
                )

                if result.is_success():
                    written_files.append({
                        "filename": script["filename"],
                        "file_path": result.data["file_path"],
                        "created": result.data["created"],
                    })
                    logger.debug(f"Wrote script: {result.data['file_path']}")
                else:
                    logger.error(f"Failed to write {script['filename']}: {result.error}")

            if not written_files:
                state["error"] = "Failed to write any scripts"
                state["status"] = "failed"
            else:
                # Update generated_scripts with file paths
                for i, script in enumerate(state["generated_scripts"]):
                    for written in written_files:
                        if script["filename"] == written["filename"]:
                            state["generated_scripts"][i]["file_path"] = written["file_path"]
                            break

                logger.info(f"Wrote {len(written_files)} scripts to disk")

        except Exception as e:
            state["error"] = f"File writing error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"File writing exception: {e}")

        return state

    def _process_results_node(self, state: TestGenerationState) -> TestGenerationState:
        """Process and finalize test generation results"""
        logger.info("Processing test generation results")

        state["end_time"] = datetime.now()
        state["status"] = "completed"

        # Calculate statistics
        passed_count = sum(1 for vr in state.get("validation_results", []) if vr.get("is_valid", False))
        failed_count = len(state.get("validation_results", [])) - passed_count
        skipped_count = len(state.get("test_cases", [])) - len(state.get("generated_scripts", []))

        state["passed_count"] = passed_count
        state["failed_count"] = failed_count
        state["skipped_count"] = skipped_count

        # Calculate execution time
        if state.get("start_time") and state.get("end_time"):
            execution_time = (state["end_time"] - state["start_time"]).total_seconds()
            state["execution_time"] = execution_time
            logger.info(f"Test generation completed in {execution_time:.2f} seconds")

        return state

    def _handle_error_node(self, state: TestGenerationState) -> TestGenerationState:
        """Handle errors and cleanup"""
        logger.error(f"Test generation failed: {state.get('error', 'Unknown error')}")

        state["end_time"] = datetime.now()
        state["status"] = "failed"

        return state

    # ========== Routing Functions ==========

    def _check_generation(self, state: TestGenerationState) -> str:
        """Check if generation was successful"""
        if state.get("error"):
            return "error"
        if state.get("generated_scripts"):
            return "success"
        return "error"

    # ========== Public Methods ==========

    def generate_tests(
        self,
        test_cases: List[Dict[str, Any]],
    ) -> TestGenerationState:
        """
        Generate test scripts from test cases

        Args:
            test_cases: List of test case dictionaries

        Returns:
            Final state with generated scripts
        """
        # Prepare initial state
        initial_state: TestGenerationState = {
            "test_cases": test_cases,
        }

        # Execute graph
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"Test generation workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now(),
            }

    def get_generation_result(self, state: TestGenerationState) -> Dict[str, Any]:
        """
        Extract formatted generation result from state

        Args:
            state: Final workflow state

        Returns:
            Formatted generation result
        """
        return {
            "status": state.get("status"),
            "generated_scripts": state.get("generated_scripts", []),
            "validation_results": state.get("validation_results", []),
            "statistics": {
                "passed_count": state.get("passed_count", 0),
                "failed_count": state.get("failed_count", 0),
                "skipped_count": state.get("skipped_count", 0),
                "total_cases": len(state.get("test_cases", [])),
                "total_generated": len(state.get("generated_scripts", [])),
            },
            "metadata": {
                "framework": state.get("framework", ""),
                "execution_time": state.get("execution_time"),
            },
            "error": state.get("error"),
        }
