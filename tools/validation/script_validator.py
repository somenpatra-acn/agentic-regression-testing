"""
Script Validator Tool

Validates generated test scripts for syntax errors, security issues, and best practices.
"""

import ast
import re
from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class ScriptValidatorTool(BaseTool):
    """
    Validates generated test scripts

    This tool performs:
    - Python syntax validation (AST parsing)
    - Security checks (dangerous imports, code injection)
    - Best practices validation
    - Framework-specific checks
    - Style checks (basic)

    Features:
    - Syntax error detection
    - Security vulnerability scanning
    - Import validation
    - Function structure validation
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="script_validator",
            description="Validates generated test scripts for syntax, security, and best practices",
            version="1.0.0",
            tags=["validation", "security", "scripts", "quality"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "script_content": "string - Script content to validate",
                "framework": "string - Test framework (playwright, selenium, etc.)",
                "strict": "boolean - Enable strict validation (default: False)",
            },
            output_schema={
                "is_valid": "boolean - Whether script is valid",
                "errors": "list - Validation errors",
                "warnings": "list - Validation warnings",
                "suggestions": "list - Improvement suggestions",
            }
        )

    def execute(
        self,
        script_content: str,
        framework: str = "playwright",
        strict: bool = False,
    ) -> ToolResult:
        """
        Validate a test script

        Args:
            script_content: Script content to validate
            framework: Test framework name
            strict: Enable strict validation

        Returns:
            ToolResult with validation results
        """
        return self._wrap_execution(
            self._validate,
            script_content=script_content,
            framework=framework,
            strict=strict,
        )

    def _validate(
        self,
        script_content: str,
        framework: str,
        strict: bool,
    ) -> ToolResult:
        """Internal validation logic"""

        if not script_content or not script_content.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="script_content cannot be empty",
            )

        errors = []
        warnings = []
        suggestions = []

        try:
            # 1. Syntax validation (Python AST parsing)
            syntax_errors = self._validate_syntax(script_content)
            errors.extend(syntax_errors)

            # 2. Security validation
            security_issues = self._validate_security(script_content)
            if security_issues:
                if strict:
                    errors.extend(security_issues)
                else:
                    warnings.extend(security_issues)

            # 3. Import validation
            import_issues = self._validate_imports(script_content, framework)
            warnings.extend(import_issues)

            # 4. Framework-specific validation
            framework_issues = self._validate_framework_specific(script_content, framework)
            suggestions.extend(framework_issues)

            # 5. Best practices
            practice_issues = self._check_best_practices(script_content)
            suggestions.extend(practice_issues)

            # Determine overall validity
            is_valid = len(errors) == 0

            result_status = ToolStatus.SUCCESS if is_valid else ToolStatus.FAILURE

            return ToolResult(
                status=result_status,
                data={
                    "is_valid": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "suggestions": suggestions,
                },
                metadata={
                    "framework": framework,
                    "strict_mode": strict,
                    "error_count": len(errors),
                    "warning_count": len(warnings),
                    "suggestion_count": len(suggestions),
                    "script_length": len(script_content),
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Validation failed: {str(e)}",
                metadata={
                    "framework": framework,
                    "exception_type": type(e).__name__,
                }
            )

    def _validate_syntax(self, script_content: str) -> List[str]:
        """Validate Python syntax using AST"""
        errors = []

        try:
            ast.parse(script_content)
        except SyntaxError as e:
            errors.append(f"Syntax error on line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")

        return errors

    def _validate_security(self, script_content: str) -> List[str]:
        """Check for security issues"""
        issues = []

        # Check for dangerous imports
        dangerous_imports = [
            "os.system",
            "subprocess.call",
            "exec(",
            "eval(",
            "__import__",
        ]

        for dangerous in dangerous_imports:
            if dangerous in script_content:
                issues.append(f"Security risk: Found dangerous code '{dangerous}'")

        # Check for potential code injection
        if "exec(" in script_content or "eval(" in script_content:
            issues.append("Security risk: Dynamic code execution detected")

        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*=\s*["\'].*["\']',
            r'api_key\s*=\s*["\'].*["\']',
            r'secret\s*=\s*["\'].*["\']',
        ]

        for pattern in credential_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                issues.append("Security risk: Possible hardcoded credentials detected")
                break

        return issues

    def _validate_imports(self, script_content: str, framework: str) -> List[str]:
        """Validate imports"""
        warnings = []

        # Expected imports for each framework
        expected_imports = {
            "playwright": ["playwright.sync_api"],
            "selenium": ["selenium"],
            "pytest": ["pytest"],
            "robot": [],
        }

        framework_lower = framework.lower()
        if framework_lower in expected_imports:
            expected = expected_imports[framework_lower]

            for exp_import in expected:
                if exp_import and exp_import not in script_content:
                    warnings.append(f"Missing expected import: {exp_import}")

        # Check for unused imports (basic check)
        import_lines = [line for line in script_content.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]

        for imp_line in import_lines:
            # Extract imported name
            if ' as ' in imp_line:
                parts = imp_line.split(' as ')
                imported_name = parts[1].strip()
            elif 'import ' in imp_line:
                imported_name = imp_line.split('import')[-1].strip().split(',')[0].strip()
            else:
                continue

            # Check if used in script (basic check)
            if imported_name and script_content.count(imported_name) == 1:
                # Only appears in import line
                warnings.append(f"Possibly unused import: {imported_name}")

        return warnings

    def _validate_framework_specific(self, script_content: str, framework: str) -> List[str]:
        """Framework-specific validation"""
        suggestions = []

        framework_lower = framework.lower()

        if framework_lower == "playwright":
            # Check for expect statements
            if "expect(" not in script_content:
                suggestions.append("Consider using 'expect()' for assertions in Playwright")

            # Check for proper page fixture
            if "def test_" in script_content and "page: Page" not in script_content:
                suggestions.append("Test functions should accept 'page: Page' parameter")

        elif framework_lower == "selenium":
            # Check for explicit waits
            if "WebDriverWait" not in script_content and "find_element" in script_content:
                suggestions.append("Consider using WebDriverWait for element interactions")

            # Check for driver.quit()
            if "webdriver" in script_content and "driver.quit()" not in script_content:
                suggestions.append("Ensure driver.quit() is called in finally block")

        elif framework_lower == "pytest":
            # Check for test function naming
            functions = re.findall(r'def\s+(\w+)\s*\(', script_content)
            for func in functions:
                if not func.startswith('test_'):
                    suggestions.append(f"Function '{func}' should start with 'test_' for pytest")

        return suggestions

    def _check_best_practices(self, script_content: str) -> List[str]:
        """Check for best practices"""
        suggestions = []

        # Check for docstrings
        if 'def test_' in script_content:
            # Extract function definitions
            functions = re.findall(r'def\s+test_\w+\s*\([^)]*\):\s*\n\s*("""[^"]*"""|\'\'\'[^\']*\'\'\')?', script_content, re.MULTILINE)

            if not any(functions):
                suggestions.append("Add docstrings to test functions for better documentation")

        # Check for magic numbers
        numbers = re.findall(r'\b(\d{3,})\b', script_content)
        if numbers:
            suggestions.append("Consider extracting magic numbers into named constants")

        # Check line length (basic check)
        lines = script_content.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            suggestions.append(f"Lines exceed 120 characters: {long_lines[:3]}")

        # Check for empty except blocks
        if re.search(r'except.*:\s*pass\s*\n', script_content):
            suggestions.append("Avoid empty except blocks; handle exceptions explicitly")

        return suggestions
