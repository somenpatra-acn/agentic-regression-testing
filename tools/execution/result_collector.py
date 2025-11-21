"""
Result Collector Tool

Parses test execution output and creates structured test results.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class ResultCollectorTool(BaseTool):
    """
    Collects and processes test execution results

    This tool provides result parsing for:
    - Pytest output parsing
    - Unittest output parsing
    - Exit code interpretation
    - Artifact collection
    - Result structuring

    Features:
    - Multiple framework support
    - Failure extraction
    - Duration parsing
    - Step result extraction
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="result_collector",
            description="Parses test execution output and creates structured results",
            version="1.0.0",
            tags=["execution", "testing", "parsing", "results"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "test_name": "string - Name of the test",
                "test_case_id": "string - Test case ID",
                "exit_code": "int - Process exit code",
                "stdout": "string - Standard output",
                "stderr": "string - Standard error",
                "duration_seconds": "float - Execution duration",
                "framework": "string - Test framework used",
            },
            output_schema={
                "status": "string - Test status (passed, failed, error, skipped)",
                "error_message": "string - Error message if failed",
                "stack_trace": "string - Stack trace if error",
                "step_results": "list - Individual step results",
                "assertions": "dict - Assertion results",
            }
        )

    def execute(
        self,
        test_name: str,
        test_case_id: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        framework: str = "pytest",
    ) -> ToolResult:
        """
        Collect and parse test execution results

        Args:
            test_name: Name of the test
            test_case_id: Test case ID
            exit_code: Process exit code
            stdout: Standard output
            stderr: Standard error
            duration_seconds: Execution duration
            framework: Test framework used

        Returns:
            ToolResult with parsed results
        """
        return self._wrap_execution(
            self._collect_results,
            test_name=test_name,
            test_case_id=test_case_id,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            framework=framework,
        )

    def _collect_results(
        self,
        test_name: str,
        test_case_id: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        framework: str,
    ) -> ToolResult:
        """Internal collection logic"""

        if not test_name or not test_name.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="test_name cannot be empty",
            )

        try:
            framework_lower = framework.lower()

            # Parse based on framework
            if framework_lower == "pytest":
                parsed = self._parse_pytest_output(stdout, stderr, exit_code)
            elif framework_lower == "unittest":
                parsed = self._parse_unittest_output(stdout, stderr, exit_code)
            else:
                parsed = self._parse_generic_output(stdout, stderr, exit_code)

            # Determine overall status
            status = self._determine_status(exit_code, parsed)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "test_name": test_name,
                    "test_case_id": test_case_id,
                    "status": status,
                    "error_message": parsed.get("error_message"),
                    "stack_trace": parsed.get("stack_trace"),
                    "step_results": parsed.get("step_results", []),
                    "assertions": parsed.get("assertions", {}),
                    "passed_count": parsed.get("passed_count", 0),
                    "failed_count": parsed.get("failed_count", 0),
                    "skipped_count": parsed.get("skipped_count", 0),
                },
                metadata={
                    "framework": framework,
                    "exit_code": exit_code,
                    "duration_seconds": duration_seconds,
                    "stdout_length": len(stdout),
                    "stderr_length": len(stderr),
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Result collection failed: {str(e)}",
                metadata={
                    "test_name": test_name,
                    "framework": framework,
                    "exception_type": type(e).__name__,
                }
            )

    def _parse_pytest_output(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
    ) -> Dict[str, Any]:
        """Parse pytest output"""

        result = {
            "error_message": None,
            "stack_trace": None,
            "step_results": [],
            "assertions": {},
            "passed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
        }

        # Parse summary line (e.g., "1 passed, 2 failed in 1.23s")
        summary_pattern = r"(\d+)\s+(passed|failed|skipped|error)"
        for match in re.finditer(summary_pattern, stdout, re.IGNORECASE):
            count = int(match.group(1))
            status = match.group(2).lower()

            if status == "passed":
                result["passed_count"] = count
            elif status == "failed":
                result["failed_count"] = count
            elif status == "skipped":
                result["skipped_count"] = count

        # Extract failure message
        if exit_code != 0:
            # Look for FAILED section
            failed_pattern = r"FAILED.*?\n(.*?)(?=FAILED|\Z)"
            failed_match = re.search(failed_pattern, stdout, re.DOTALL)
            if failed_match:
                result["error_message"] = failed_match.group(1).strip()[:500]

            # Look for assertion errors
            assert_pattern = r"AssertionError:(.*?)(?=\n\n|\Z)"
            assert_match = re.search(assert_pattern, stdout, re.DOTALL)
            if assert_match:
                result["error_message"] = f"AssertionError: {assert_match.group(1).strip()}"

            # Extract stack trace
            if "Traceback" in stdout or "Traceback" in stderr:
                traceback_pattern = r"(Traceback.*?)(?=\n\n|\Z)"
                traceback_match = re.search(traceback_pattern, stdout + "\n" + stderr, re.DOTALL)
                if traceback_match:
                    result["stack_trace"] = traceback_match.group(1).strip()[:2000]

        # Parse individual test results
        test_pattern = r"(test_\w+)\s+(PASSED|FAILED|SKIPPED|ERROR)"
        for match in re.finditer(test_pattern, stdout):
            test_func = match.group(1)
            status = match.group(2).lower()

            result["step_results"].append({
                "name": test_func,
                "status": status,
            })

        return result

    def _parse_unittest_output(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
    ) -> Dict[str, Any]:
        """Parse unittest output"""

        result = {
            "error_message": None,
            "stack_trace": None,
            "step_results": [],
            "assertions": {},
            "passed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
        }

        # Parse summary line (e.g., "Ran 3 tests in 1.234s")
        ran_pattern = r"Ran (\d+) tests?"
        ran_match = re.search(ran_pattern, stdout)
        if ran_match:
            total = int(ran_match.group(1))

        # Check for failures/errors
        if "FAILED" in stdout or "failures=" in stdout:
            fail_pattern = r"failures=(\d+)"
            fail_match = re.search(fail_pattern, stdout)
            if fail_match:
                result["failed_count"] = int(fail_match.group(1))

        if "OK" in stdout and exit_code == 0:
            result["passed_count"] = total if 'total' in locals() else 1

        # Extract error message
        if exit_code != 0:
            error_pattern = r"ERROR:.*?\n(.*?)(?=\n\n|\Z)"
            error_match = re.search(error_pattern, stdout, re.DOTALL)
            if error_match:
                result["error_message"] = error_match.group(1).strip()[:500]

            # Extract stack trace
            if "Traceback" in stdout:
                result["stack_trace"] = stdout[stdout.find("Traceback"):].strip()[:2000]

        return result

    def _parse_generic_output(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
    ) -> Dict[str, Any]:
        """Parse generic Python output"""

        result = {
            "error_message": None,
            "stack_trace": None,
            "step_results": [],
            "assertions": {},
            "passed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
        }

        # If exit code is 0, assume success
        if exit_code == 0:
            result["passed_count"] = 1
        else:
            result["failed_count"] = 1

            # Extract error from stderr
            if stderr:
                result["error_message"] = stderr.strip()[:500]

            # Extract traceback
            if "Traceback" in stdout or "Traceback" in stderr:
                combined = stdout + "\n" + stderr
                traceback_start = combined.find("Traceback")
                if traceback_start != -1:
                    result["stack_trace"] = combined[traceback_start:].strip()[:2000]

        return result

    def _determine_status(self, exit_code: int, parsed: Dict[str, Any]) -> str:
        """Determine overall test status"""

        if exit_code == 0:
            return "passed"

        # Check for specific failure indicators
        if parsed.get("failed_count", 0) > 0:
            return "failed"

        if parsed.get("error_message"):
            return "error"

        # Default to error for non-zero exit
        return "error"
