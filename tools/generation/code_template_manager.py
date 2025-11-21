"""
Code Template Manager Tool

Manages code templates and patterns for test generation.
"""

from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class CodeTemplateManagerTool(BaseTool):
    """
    Manages code templates for test generation

    This tool provides:
    - Framework-specific templates
    - Code snippets for common actions
    - Import statement management
    - Boilerplate code generation

    Features:
    - Template caching
    - Multiple framework support
    - Customizable templates
    - Pattern library
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._templates = self._load_templates()

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="code_template_manager",
            description="Manages code templates and patterns for test generation",
            version="1.0.0",
            tags=["generation", "templates", "patterns"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "template_type": "string - Type of template (test_function, import, setup, teardown)",
                "framework": "string - Framework name (playwright, selenium, etc.)",
                "context": "dict - Context variables for template",
            },
            output_schema={
                "template": "string - Rendered template",
                "imports": "list - Required imports",
            }
        )

    def execute(
        self,
        template_type: str,
        framework: str = "playwright",
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Get a code template

        Args:
            template_type: Type of template to retrieve
            framework: Framework name
            context: Context variables for rendering

        Returns:
            ToolResult with template content
        """
        return self._wrap_execution(
            self._get_template,
            template_type=template_type,
            framework=framework,
            context=context or {},
        )

    def _get_template(
        self,
        template_type: str,
        framework: str,
        context: Dict[str, Any],
    ) -> ToolResult:
        """Internal template retrieval logic"""

        framework = framework.lower()
        template_type = template_type.lower()

        valid_types = ["test_function", "import", "setup", "teardown", "fixture", "action"]
        if template_type not in valid_types:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Invalid template_type: {template_type}. Valid types: {valid_types}",
            )

        valid_frameworks = ["playwright", "selenium", "pytest", "robot"]
        if framework not in valid_frameworks:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Invalid framework: {framework}. Valid frameworks: {valid_frameworks}",
            )

        try:
            # Get template
            template_key = f"{framework}_{template_type}"
            template = self._templates.get(template_key, "")

            if not template:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"Template not found: {template_key}",
                )

            # Render template with context
            rendered = self._render_template(template, context)

            # Get imports for this framework/type
            imports = self._get_imports_for_template(framework, template_type)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "template": rendered,
                    "imports": imports,
                },
                metadata={
                    "template_type": template_type,
                    "framework": framework,
                    "template_key": template_key,
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Template retrieval failed: {str(e)}",
                metadata={
                    "template_type": template_type,
                    "framework": framework,
                    "exception_type": type(e).__name__,
                }
            )

    def _load_templates(self) -> Dict[str, str]:
        """Load all templates"""
        templates = {}

        # Playwright templates
        templates["playwright_test_function"] = '''def test_{test_name}(page: Page):
    """
    Test: {description}
    """
    {test_body}'''

        templates["playwright_import"] = "from playwright.sync_api import Page, expect"

        templates["playwright_setup"] = '''@pytest.fixture
def setup_page(page: Page):
    page.goto("{base_url}")
    yield page'''

        templates["playwright_action"] = '''page.{action}("{selector}")'''

        # Selenium templates
        templates["selenium_test_function"] = '''def test_{test_name}():
    """
    Test: {description}
    """
    driver = webdriver.Chrome()
    try:
        {test_body}
    finally:
        driver.quit()'''

        templates["selenium_import"] = """from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC"""

        templates["selenium_setup"] = '''driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)'''

        templates["selenium_teardown"] = "driver.quit()"

        # pytest templates
        templates["pytest_fixture"] = '''@pytest.fixture
def {fixture_name}():
    {setup_code}
    yield
    {teardown_code}'''

        templates["pytest_import"] = "import pytest"

        # Robot Framework templates
        templates["robot_test_function"] = '''{test_name}
    [Documentation]    {description}
    {test_steps}'''

        templates["robot_import"] = "Library    SeleniumLibrary"

        return templates

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables"""
        try:
            return template.format(**context)
        except KeyError as e:
            # If a key is missing, return template with available substitutions
            for key, value in context.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template

    def _get_imports_for_template(self, framework: str, template_type: str) -> List[str]:
        """Get required imports for a template"""
        import_map = {
            "playwright": [
                "from playwright.sync_api import Page, expect",
            ],
            "selenium": [
                "from selenium import webdriver",
                "from selenium.webdriver.common.by import By",
                "from selenium.webdriver.support.ui import WebDriverWait",
                "from selenium.webdriver.support import expected_conditions as EC",
            ],
            "pytest": [
                "import pytest",
            ],
            "robot": [],
        }

        return import_map.get(framework, [])
