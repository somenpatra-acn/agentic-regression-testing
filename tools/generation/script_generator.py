"""
Script Generator Tool

Generates executable test script code from test cases using templates and LLM.
"""

from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata
from utils.helpers import sanitize_filename


class ScriptGeneratorTool(BaseTool):
    """
    Generates executable test scripts

    This tool generates test script code for various frameworks:
    - Playwright (Python)
    - Selenium (Python)
    - pytest
    - Robot Framework

    Features:
    - Template-based generation
    - Framework-specific syntax
    - Step-by-step code generation
    - Import statement generation
    - Proper test structure
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="script_generator",
            description="Generates executable test script code from test cases",
            version="1.0.0",
            tags=["generation", "scripts", "code"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "test_case": "dict - Test case with name, description, steps",
                "framework": "string - Test framework (playwright, selenium, pytest, robot)",
                "app_profile": "dict - Application profile with base_url, etc.",
            },
            output_schema={
                "script_content": "string - Generated test script code",
                "filename": "string - Suggested filename",
                "imports": "list - Required imports",
            }
        )

    def execute(
        self,
        test_case: Dict[str, Any],
        framework: str = "playwright",
        app_profile: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Generate test script code

        Args:
            test_case: Test case dictionary with name, description, steps
            framework: Test framework to use
            app_profile: Application profile with base_url, etc.

        Returns:
            ToolResult with generated script content
        """
        return self._wrap_execution(
            self._generate,
            test_case=test_case,
            framework=framework,
            app_profile=app_profile,
        )

    def _generate(
        self,
        test_case: Dict[str, Any],
        framework: str,
        app_profile: Optional[Dict[str, Any]],
    ) -> ToolResult:
        """Internal generation logic"""

        # Validate inputs
        if not test_case:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="test_case cannot be empty",
            )

        test_name = test_case.get("name", "Unnamed Test")
        test_description = test_case.get("description", "")
        steps = test_case.get("steps", [])

        if not test_name:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="test_case must have a name",
            )

        framework = framework.lower()
        supported_frameworks = ["playwright", "selenium", "pytest", "robot"]

        if framework not in supported_frameworks:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Unsupported framework: {framework}. Supported: {supported_frameworks}",
            )

        try:
            # Generate script based on framework
            if framework == "playwright":
                script_content, imports = self._generate_playwright_script(
                    test_case, app_profile
                )
            elif framework == "selenium":
                script_content, imports = self._generate_selenium_script(
                    test_case, app_profile
                )
            elif framework == "pytest":
                script_content, imports = self._generate_pytest_script(
                    test_case, app_profile
                )
            elif framework == "robot":
                script_content, imports = self._generate_robot_script(
                    test_case, app_profile
                )
            else:
                script_content = f"# Test: {test_name}\n# TODO: Implement for {framework}"
                imports = []

            # Generate filename
            safe_name = sanitize_filename(test_name.lower().replace(" ", "_"))
            if framework == "robot":
                filename = f"test_{safe_name}.robot"
            else:
                filename = f"test_{safe_name}.py"

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "script_content": script_content,
                    "filename": filename,
                    "imports": imports,
                },
                metadata={
                    "test_name": test_name,
                    "framework": framework,
                    "step_count": len(steps),
                    "has_app_profile": app_profile is not None,
                    "script_length": len(script_content),
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Script generation failed: {str(e)}",
                metadata={
                    "test_name": test_name,
                    "framework": framework,
                    "exception_type": type(e).__name__,
                }
            )

    def _generate_playwright_script(
        self,
        test_case: Dict[str, Any],
        app_profile: Optional[Dict[str, Any]],
    ) -> tuple[str, List[str]]:
        """Generate Playwright test script"""

        test_name = test_case.get("name", "Test")
        test_description = test_case.get("description", "")
        steps = test_case.get("steps", [])
        safe_name = sanitize_filename(test_name.lower().replace(" ", "_"))

        base_url = ""
        if app_profile:
            base_url = app_profile.get("base_url", "")

        imports = [
            "from playwright.sync_api import Page, expect",
        ]

        script = f'''"""
Test: {test_name}
Description: {test_description}
Framework: Playwright
Generated by: Agentic AI Regression Suite
"""

from playwright.sync_api import Page, expect


def test_{safe_name}(page: Page):
    """
    Test: {test_name}

    Description: {test_description}
    """
'''

        # Generate step code
        if steps:
            for step in steps:
                step_num = step.get("step_number", 0)
                action = step.get("action", "")
                target = step.get("target", "")
                expected = step.get("expected_result", "")

                script += f"\n    # Step {step_num}: {action}\n"

                if action == "navigate" or action == "goto":
                    url = target if target else base_url
                    script += f'    page.goto("{url}")\n'

                elif action == "click":
                    script += f'    page.click("{target}")\n'

                elif action == "fill" or action == "type":
                    script += f'    page.fill("{target}", "test_value")\n'

                elif action == "verify" or action == "assert":
                    script += f'    expect(page.locator("{target}")).to_be_visible()\n'

                elif action == "wait":
                    script += f'    page.wait_for_selector("{target}")\n'

                else:
                    script += f'    # TODO: Implement action "{action}" on "{target}"\n'

                if expected:
                    script += f'    # Expected: {expected}\n'
        else:
            # No steps provided, add placeholder
            script += f'\n    page.goto("{base_url}")\n'
            script += '    # TODO: Add test steps\n'

        return script, imports

    def _generate_selenium_script(
        self,
        test_case: Dict[str, Any],
        app_profile: Optional[Dict[str, Any]],
    ) -> tuple[str, List[str]]:
        """Generate Selenium test script"""

        test_name = test_case.get("name", "Test")
        test_description = test_case.get("description", "")
        steps = test_case.get("steps", [])
        safe_name = sanitize_filename(test_name.lower().replace(" ", "_"))

        base_url = ""
        if app_profile:
            base_url = app_profile.get("base_url", "")

        imports = [
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
        ]

        script = f'''"""
Test: {test_name}
Description: {test_description}
Framework: Selenium
Generated by: Agentic AI Regression Suite
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_{safe_name}():
    """
    Test: {test_name}

    Description: {test_description}
    """
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
'''

        # Generate step code
        if steps:
            for step in steps:
                step_num = step.get("step_number", 0)
                action = step.get("action", "")
                target = step.get("target", "")
                expected = step.get("expected_result", "")

                script += f"\n        # Step {step_num}: {action}\n"

                if action == "navigate" or action == "goto":
                    url = target if target else base_url
                    script += f'        driver.get("{url}")\n'

                elif action == "click":
                    script += f'        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "{target}")))\n'
                    script += '        element.click()\n'

                elif action == "fill" or action == "type":
                    script += f'        element = driver.find_element(By.CSS_SELECTOR, "{target}")\n'
                    script += '        element.send_keys("test_value")\n'

                elif action == "verify" or action == "assert":
                    script += f'        element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "{target}")))\n'
                    script += '        assert element.is_displayed()\n'

                else:
                    script += f'        # TODO: Implement action "{action}" on "{target}"\n'

                if expected:
                    script += f'        # Expected: {expected}\n'
        else:
            script += f'\n        driver.get("{base_url}")\n'
            script += '        # TODO: Add test steps\n'

        script += '''
    finally:
        driver.quit()
'''

        return script, imports

    def _generate_pytest_script(
        self,
        test_case: Dict[str, Any],
        app_profile: Optional[Dict[str, Any]],
    ) -> tuple[str, List[str]]:
        """Generate pytest script (uses Playwright by default)"""
        return self._generate_playwright_script(test_case, app_profile)

    def _generate_robot_script(
        self,
        test_case: Dict[str, Any],
        app_profile: Optional[Dict[str, Any]],
    ) -> tuple[str, List[str]]:
        """Generate Robot Framework test script"""

        test_name = test_case.get("name", "Test")
        test_description = test_case.get("description", "")
        steps = test_case.get("steps", [])

        base_url = ""
        if app_profile:
            base_url = app_profile.get("base_url", "")

        script = f'''*** Settings ***
Library    SeleniumLibrary
Suite Setup    Open Browser    {base_url}    chrome
Suite Teardown    Close Browser

*** Test Cases ***
{test_name}
    [Documentation]    {test_description}
'''

        if steps:
            for step in steps:
                action = step.get("action", "")
                target = step.get("target", "")

                if action == "navigate":
                    script += f'    Go To    {target}\n'
                elif action == "click":
                    script += f'    Click Element    {target}\n'
                elif action == "fill":
                    script += f'    Input Text    {target}    test_value\n'
                elif action == "verify":
                    script += f'    Element Should Be Visible    {target}\n'
                else:
                    script += f'    # TODO: {action} on {target}\n'
        else:
            script += '    # TODO: Add test steps\n'

        return script, []
