"""Test Generator Agent - generates executable test scripts."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.prompts import PromptTemplate

from config.llm_config import get_smart_llm
from config.settings import get_settings
from models.app_profile import ApplicationProfile
from models.test_case import TestCase, TestPriority, TestType, TestStep
from rag.retriever import TestKnowledgeRetriever
from utils.logger import get_logger
from utils.helpers import generate_test_id, sanitize_filename

logger = get_logger(__name__)


class TestGeneratorAgent:
    """
    Test Generator Agent generates executable test scripts using:
    - LLM for code generation
    - RAG for similar test patterns
    - Templates for different frameworks
    """

    def __init__(self, app_profile: ApplicationProfile):
        """
        Initialize Test Generator Agent.

        Args:
            app_profile: Application profile
        """
        self.app_profile = app_profile
        self.settings = get_settings()
        self.llm = get_smart_llm()
        self.knowledge_retriever = TestKnowledgeRetriever()

        self.generated_tests: List[TestCase] = []

        logger.info(f"TestGeneratorAgent initialized for {app_profile.name}")

    def generate_tests(self, test_plan: Dict[str, Any]) -> List[TestCase]:
        """
        Generate test scripts from test plan.

        Args:
            test_plan: Test plan dictionary

        Returns:
            List of generated TestCase objects
        """
        logger.info("Generating tests from plan")

        test_cases = []

        for tc_data in test_plan.get("test_cases", []):
            test_case = self._generate_test_case(tc_data, test_plan)
            test_cases.append(test_case)

            # Generate actual test script file
            script_path = self._generate_script_file(test_case)
            test_case.script_path = script_path

        self.generated_tests = test_cases

        # Add to knowledge base
        self.knowledge_retriever.add_test_cases(test_cases)

        logger.info(f"Generated {len(test_cases)} test cases")

        return test_cases

    def _generate_test_case(
        self,
        tc_data: Dict[str, Any],
        test_plan: Dict[str, Any]
    ) -> TestCase:
        """Generate a single test case."""
        # Get similar test patterns
        patterns = self.knowledge_retriever.get_test_patterns(
            feature=test_plan.get("feature", ""),
            k=2
        )

        # Use LLM to generate test steps
        steps = self._generate_steps_with_llm(tc_data, patterns)

        # Create TestCase object
        test_case = TestCase(
            id=tc_data.get("id", generate_test_id()),
            name=tc_data.get("name", "Generated Test"),
            description=tc_data.get("description", ""),
            test_type=TestType(tc_data.get("type", "functional")),
            priority=TestPriority(tc_data.get("priority", "medium")),
            steps=steps,
            application=self.app_profile.name,
            framework=self.app_profile.test_framework.value,
            requires_approval=True
        )

        return test_case

    def _generate_steps_with_llm(
        self,
        tc_data: Dict[str, Any],
        patterns: List[str]
    ) -> List[TestStep]:
        """Generate test steps using LLM."""
        # Simplified implementation - would use LLM in production
        steps = [
            TestStep(
                step_number=1,
                action="navigate",
                target=self.app_profile.base_url,
                expected_result="Application loads successfully"
            ),
            TestStep(
                step_number=2,
                action="verify",
                target="body",
                expected_result="Page content is visible"
            )
        ]

        return steps

    def _generate_script_file(self, test_case: TestCase) -> str:
        """Generate actual test script file."""
        framework = test_case.framework

        if framework == "playwright":
            script_content = self._generate_playwright_script(test_case)
            extension = ".py"
        elif framework == "selenium":
            script_content = self._generate_selenium_script(test_case)
            extension = ".py"
        elif framework == "pytest":
            script_content = self._generate_pytest_script(test_case)
            extension = ".py"
        else:
            script_content = f"# Test: {test_case.name}\n# TODO: Implement test"
            extension = ".py"

        # Save script
        filename = sanitize_filename(f"test_{test_case.name.lower().replace(' ', '_')}")
        script_path = self.settings.tests_dir / f"{filename}{extension}"

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        logger.debug(f"Generated script: {script_path}")

        return str(script_path)

    def _generate_playwright_script(self, test_case: TestCase) -> str:
        """Generate Playwright test script."""
        script = f'''"""
Test: {test_case.name}
Description: {test_case.description}
Generated by: Agentic Regression Suite
"""

from playwright.sync_api import Page, expect


def test_{sanitize_filename(test_case.name.lower().replace(" ", "_"))}(page: Page):
    """Test: {test_case.name}"""

'''

        for step in test_case.steps:
            if step.action == "navigate":
                script += f'    page.goto("{step.target}")\n'
            elif step.action == "click":
                script += f'    page.click("{step.target}")\n'
            elif step.action == "fill":
                script += f'    page.fill("{step.target}", "test_value")\n'
            elif step.action == "verify":
                script += f'    expect(page.locator("{step.target}")).to_be_visible()\n'

            script += f'    # Expected: {step.expected_result}\n\n'

        return script

    def _generate_selenium_script(self, test_case: TestCase) -> str:
        """Generate Selenium test script."""
        return f'''"""
Test: {test_case.name}
Generated by: Agentic Regression Suite
"""

from selenium import webdriver
from selenium.webdriver.common.by import By


def test_{sanitize_filename(test_case.name.lower().replace(" ", "_"))}():
    """Test: {test_case.name}"""
    driver = webdriver.Chrome()

    try:
        # Test implementation
        driver.get("{self.app_profile.base_url}")
        # TODO: Add test steps

    finally:
        driver.quit()
'''

    def _generate_pytest_script(self, test_case: TestCase) -> str:
        """Generate pytest script."""
        return self._generate_playwright_script(test_case)

    def get_generated_tests(self) -> List[TestCase]:
        """Get list of generated tests."""
        return self.generated_tests
