"""Orchestrator Agent - coordinates all other agents."""

from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool

from config.llm_config import get_smart_llm
from config.settings import get_settings
from models.app_profile import ApplicationProfile
from adapters import get_adapter
from agents.discovery import DiscoveryAgent
from agents.test_planner import TestPlannerAgent
from agents.test_generator import TestGeneratorAgent
from agents.test_executor import TestExecutorAgent
from agents.reporting import ReportingAgent
from hitl.approval_manager import ApprovalManager
from utils.logger import get_logger

logger = get_logger(__name__)


class OrchestratorAgent:
    """
    Orchestrator Agent coordinates all sub-agents and manages the testing workflow.

    Workflow:
    1. Interpret user input or CI/CD triggers
    2. Coordinate Discovery Agent to explore application
    3. Coordinate Test Planner to create test plan
    4. Coordinate Test Generator to create test scripts
    5. Coordinate Test Executor to run tests
    6. Coordinate Reporting Agent to generate reports
    """

    def __init__(
        self,
        app_profile: ApplicationProfile,
        hitl_mode: Optional[str] = None
    ):
        """
        Initialize Orchestrator Agent.

        Args:
            app_profile: Application profile configuration
            hitl_mode: Human-in-the-loop mode (overrides settings)
        """
        self.app_profile = app_profile
        self.settings = get_settings()

        # Initialize HITL
        self.hitl_mode = hitl_mode or self.settings.hitl_mode
        self.approval_manager = ApprovalManager(
            hitl_mode=self.hitl_mode,
            timeout=self.settings.approval_timeout
        )

        # Initialize application adapter
        self.adapter = get_adapter(app_profile.adapter, app_profile)

        # Initialize sub-agents
        self.discovery_agent = DiscoveryAgent(self.adapter, self.app_profile)
        self.test_planner = TestPlannerAgent(self.app_profile)
        self.test_generator = TestGeneratorAgent(self.app_profile)
        self.test_executor = TestExecutorAgent(self.adapter, self.app_profile)
        self.reporting_agent = ReportingAgent(self.app_profile)

        # Initialize LangChain agent
        self.llm = get_smart_llm()
        self.agent_executor = self._create_agent()

        logger.info(
            f"OrchestratorAgent initialized for {app_profile.name} "
            f"(HITL mode: {self.hitl_mode})"
        )

    def _create_agent(self) -> AgentExecutor:
        """Create LangChain agent with tools."""
        tools = self._create_tools()

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an orchestrator agent for an AI-powered regression testing framework.

Your role is to:
1. Understand the user's testing requirements
2. Coordinate sub-agents to discover, plan, generate, execute, and report on tests
3. Manage human approval workflows when required
4. Provide clear status updates and recommendations

Available sub-agents:
- Discovery Agent: Explores the application to find UI elements, APIs, or schemas
- Test Planner: Creates comprehensive test plans with gap analysis
- Test Generator: Generates executable test scripts
- Test Executor: Runs tests and captures results
- Reporting Agent: Generates test reports and integrates with CI/CD

Always explain your reasoning and keep the user informed of progress.
"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    def _create_tools(self) -> List[Tool]:
        """Create tools for the orchestrator agent."""
        return [
            Tool(
                name="discover_application",
                description="Discover UI elements, APIs, or database schema of the application",
                func=self._tool_discover
            ),
            Tool(
                name="create_test_plan",
                description="Create a comprehensive test plan for the application or feature",
                func=self._tool_create_plan
            ),
            Tool(
                name="generate_tests",
                description="Generate executable test scripts from a test plan",
                func=self._tool_generate_tests
            ),
            Tool(
                name="execute_tests",
                description="Execute test scripts and collect results",
                func=self._tool_execute_tests
            ),
            Tool(
                name="generate_report",
                description="Generate a test execution report",
                func=self._tool_generate_report
            ),
        ]

    def _tool_discover(self, input_str: str) -> str:
        """Tool: Discover application."""
        try:
            logger.info("Orchestrator invoking Discovery Agent")
            discovery_result = self.discovery_agent.discover()

            summary = (
                f"Discovery complete:\n"
                f"- Found {len(discovery_result.elements)} elements\n"
                f"- Crawled {len(discovery_result.pages)} pages\n"
                f"- Discovered {len(discovery_result.apis)} APIs"
            )

            logger.info(summary)
            return summary

        except Exception as e:
            error_msg = f"Discovery failed: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _tool_create_plan(self, input_str: str) -> str:
        """Tool: Create test plan."""
        try:
            logger.info(f"Orchestrator invoking Test Planner: {input_str}")

            # Get discovery results
            discovery_result = self.discovery_agent.get_last_discovery()

            # Create test plan
            test_plan = self.test_planner.create_plan(
                feature_description=input_str,
                discovery_result=discovery_result
            )

            summary = (
                f"Test plan created:\n"
                f"- Test cases: {len(test_plan.get('test_cases', []))}\n"
                f"- Coverage areas: {', '.join(test_plan.get('coverage', []))}\n"
                f"- Gaps identified: {len(test_plan.get('gaps', []))}"
            )

            # Human approval if required
            if self.approval_manager.is_approval_required("test_plan"):
                try:
                    test_plan = self.approval_manager.approve_test_plan(
                        test_plan,
                        summary
                    )
                    summary += "\n✓ Test plan approved by human"
                except Exception as e:
                    summary += f"\n✗ Test plan rejected: {str(e)}"

            logger.info(summary)
            return summary

        except Exception as e:
            error_msg = f"Test planning failed: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _tool_generate_tests(self, input_str: str) -> str:
        """Tool: Generate test scripts."""
        try:
            logger.info("Orchestrator invoking Test Generator")

            # Get test plan
            test_plan = self.test_planner.get_last_plan()

            if not test_plan:
                return "Error: No test plan available. Create a test plan first."

            # Generate tests
            generated_tests = self.test_generator.generate_tests(test_plan)

            summary = f"Generated {len(generated_tests)} test scripts"

            logger.info(summary)
            return summary

        except Exception as e:
            error_msg = f"Test generation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _tool_execute_tests(self, input_str: str) -> str:
        """Tool: Execute tests."""
        try:
            logger.info("Orchestrator invoking Test Executor")

            # Get generated tests
            test_cases = self.test_generator.get_generated_tests()

            if not test_cases:
                return "Error: No tests available. Generate tests first."

            # Execute tests
            results = self.test_executor.execute_tests(test_cases)

            passed = sum(1 for r in results if r.status.value == "passed")
            failed = sum(1 for r in results if r.status.value == "failed")

            summary = (
                f"Test execution complete:\n"
                f"- Total: {len(results)}\n"
                f"- Passed: {passed}\n"
                f"- Failed: {failed}"
            )

            logger.info(summary)
            return summary

        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _tool_generate_report(self, input_str: str) -> str:
        """Tool: Generate test report."""
        try:
            logger.info("Orchestrator invoking Reporting Agent")

            # Get test results
            results = self.test_executor.get_test_results()

            if not results:
                return "Error: No test results available. Execute tests first."

            # Generate report
            report_path = self.reporting_agent.generate_report(results)

            summary = f"Test report generated: {report_path}"

            logger.info(summary)
            return summary

        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Run the orchestrator with user input.

        Args:
            user_input: User's testing request

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Orchestrator processing: {user_input}")

        try:
            result = self.agent_executor.invoke({"input": user_input})

            return {
                "success": True,
                "output": result.get("output", ""),
                "steps": result.get("intermediate_steps", [])
            }

        except Exception as e:
            logger.error(f"Orchestrator execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def run_full_workflow(self, feature_description: str) -> Dict[str, Any]:
        """
        Run complete testing workflow: discover -> plan -> generate -> execute -> report.

        Args:
            feature_description: Description of feature to test

        Returns:
            Dictionary with workflow results
        """
        logger.info(f"Running full workflow for: {feature_description}")

        workflow_input = f"""
        Run a complete regression testing workflow for: {feature_description}

        Steps:
        1. Discover the application
        2. Create a test plan
        3. Generate test scripts
        4. Execute the tests
        5. Generate a report

        Please execute all steps in order.
        """

        return self.run(workflow_input)

    def cleanup(self) -> None:
        """Clean up resources."""
        self.adapter.cleanup()
        logger.info("Orchestrator cleanup complete")
