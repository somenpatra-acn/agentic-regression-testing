"""
Unit tests for Execution Tools

Tests for TestExecutorTool and ResultCollectorTool.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.execution import TestExecutorTool, ResultCollectorTool
from tools.base import ToolRegistry, ToolStatus


class TestTestExecutorTool:
    """Tests for TestExecutorTool"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        ToolRegistry.clear()
        yield
        ToolRegistry.clear()

    @pytest.fixture
    def executor(self):
        """Create TestExecutorTool instance"""
        return TestExecutorTool()

    def test_metadata(self, executor):
        """Test tool metadata"""
        metadata = executor.metadata

        assert metadata.name == "test_executor"
        assert "executes test scripts" in metadata.description.lower()
        assert "execution" in metadata.tags
        assert not metadata.is_safe  # Executes code
        assert "script_path" in metadata.input_schema
        assert "exit_code" in metadata.output_schema

    def test_execute_missing_script_path(self, executor):
        """Test execution with missing script path"""
        result = executor.execute(script_path="")

        assert result.is_failure()
        assert "cannot be empty" in result.error

    def test_execute_nonexistent_script(self, executor):
        """Test execution with non-existent script"""
        result = executor.execute(script_path="/nonexistent/script.py")

        assert result.is_failure()
        assert "not found" in result.error.lower()

    @patch('subprocess.run')
    def test_execute_successful_test(self, mock_run, executor, tmp_path):
        """Test successful test execution"""
        # Create test script
        script_file = tmp_path / "test_sample.py"
        script_file.write_text("def test_pass(): assert True")

        # Mock successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_sample.py::test_pass PASSED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = executor.execute(
            script_path=str(script_file),
            framework="pytest",
            timeout_seconds=60,
        )

        assert result.is_success()
        assert result.data["exit_code"] == 0
        assert "PASSED" in result.data["stdout"]
        assert result.data["duration_seconds"] > 0
        assert not result.data["timed_out"]

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "pytest" in call_args[0][0]
        assert str(script_file) in call_args[0][0]

    @patch('subprocess.run')
    def test_execute_failed_test(self, mock_run, executor, tmp_path):
        """Test failed test execution"""
        # Create test script
        script_file = tmp_path / "test_fail.py"
        script_file.write_text("def test_fail(): assert False")

        # Mock failed execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test_fail.py::test_fail FAILED"
        mock_result.stderr = "AssertionError"
        mock_run.return_value = mock_result

        result = executor.execute(
            script_path=str(script_file),
            framework="pytest",
        )

        assert result.is_failure()
        assert result.data["exit_code"] == 1
        assert "FAILED" in result.data["stdout"]

    @patch('subprocess.run')
    def test_execute_timeout(self, mock_run, executor, tmp_path):
        """Test execution timeout"""
        # Create test script
        script_file = tmp_path / "test_slow.py"
        script_file.write_text("import time; time.sleep(100)")

        # Mock timeout
        import subprocess
        timeout_exc = subprocess.TimeoutExpired(
            cmd=["python"],
            timeout=5,
        )
        timeout_exc.stdout = b""
        timeout_exc.stderr = b""
        mock_run.side_effect = timeout_exc

        result = executor.execute(
            script_path=str(script_file),
            timeout_seconds=5,
        )

        assert result.is_failure()
        assert result.data["timed_out"]
        assert "timed out" in result.data["stderr"].lower()

    @patch('subprocess.run')
    def test_execute_with_env_vars(self, mock_run, executor, tmp_path):
        """Test execution with environment variables"""
        # Create test script
        script_file = tmp_path / "test_env.py"
        script_file.write_text("import os; assert os.getenv('TEST_VAR') == 'test_value'")

        # Mock successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "PASSED"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = executor.execute(
            script_path=str(script_file),
            env_vars={"TEST_VAR": "test_value"},
        )

        assert result.is_success()

        # Verify env vars were passed
        call_kwargs = mock_run.call_args[1]
        assert "TEST_VAR" in call_kwargs["env"]
        assert call_kwargs["env"]["TEST_VAR"] == "test_value"

    def test_execute_unittest_framework(self, executor, tmp_path):
        """Test command building for unittest framework"""
        script_file = tmp_path / "test_unit.py"
        script_file.write_text("import unittest")

        command = executor._build_command(script_file, "unittest")

        assert "unittest" in command
        assert str(script_file) in command

    def test_execute_python_framework(self, executor, tmp_path):
        """Test command building for direct Python execution"""
        script_file = tmp_path / "script.py"
        script_file.write_text("print('hello')")

        command = executor._build_command(script_file, "python")

        assert command[0] == "python"
        assert str(script_file) in command

    def test_execute_without_capture(self, executor, tmp_path):
        """Test execution without output capture"""
        # This would require actual subprocess execution
        # Skipping for unit tests - covered in integration tests
        pass


class TestResultCollectorTool:
    """Tests for ResultCollectorTool"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        ToolRegistry.clear()
        yield
        ToolRegistry.clear()

    @pytest.fixture
    def collector(self):
        """Create ResultCollectorTool instance"""
        return ResultCollectorTool()

    def test_metadata(self, collector):
        """Test tool metadata"""
        metadata = collector.metadata

        assert metadata.name == "result_collector"
        assert "parses test execution" in metadata.description.lower()
        assert "execution" in metadata.tags
        assert metadata.is_safe  # Only parses output
        assert "test_name" in metadata.input_schema
        assert "status" in metadata.output_schema

    def test_collect_missing_test_name(self, collector):
        """Test collection with missing test name"""
        result = collector.execute(
            test_name="",
            test_case_id="test-1",
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=1.0,
        )

        assert result.is_failure()
        assert "cannot be empty" in result.error

    def test_collect_successful_pytest_output(self, collector):
        """Test parsing successful pytest output"""
        stdout = """
test_sample.py::test_login PASSED
test_sample.py::test_logout PASSED

====== 2 passed in 1.23s ======
"""

        result = collector.execute(
            test_name="test_sample",
            test_case_id="test-1",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=1.23,
            framework="pytest",
        )

        assert result.is_success()
        assert result.data["status"] == "passed"
        assert result.data["passed_count"] == 2
        assert result.data["failed_count"] == 0

    def test_collect_failed_pytest_output(self, collector):
        """Test parsing failed pytest output"""
        stdout = """
test_sample.py::test_fail FAILED

FAILED test_sample.py::test_fail - AssertionError: Expected True but got False

AssertionError: Expected True but got False

====== 1 failed in 0.5s ======
"""

        result = collector.execute(
            test_name="test_fail",
            test_case_id="test-2",
            exit_code=1,
            stdout=stdout,
            stderr="",
            duration_seconds=0.5,
            framework="pytest",
        )

        assert result.is_success()
        assert result.data["status"] == "failed"
        assert result.data["failed_count"] == 1
        assert "AssertionError" in result.data["error_message"]

    def test_collect_pytest_with_traceback(self, collector):
        """Test parsing pytest output with traceback"""
        stdout = """
test_sample.py::test_error ERROR

Traceback (most recent call last):
  File "test_sample.py", line 5, in test_error
    raise ValueError("Something went wrong")
ValueError: Something went wrong

====== 1 error in 0.1s ======
"""

        result = collector.execute(
            test_name="test_error",
            test_case_id="test-3",
            exit_code=1,
            stdout=stdout,
            stderr="",
            duration_seconds=0.1,
            framework="pytest",
        )

        assert result.is_success()
        assert result.data["status"] == "error"
        assert result.data["stack_trace"] is not None
        assert "Traceback" in result.data["stack_trace"]
        assert "ValueError" in result.data["stack_trace"]

    def test_collect_unittest_output(self, collector):
        """Test parsing unittest output"""
        stdout = """
test_login (test_sample.TestCase) ... ok
test_logout (test_sample.TestCase) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.500s

OK
"""

        result = collector.execute(
            test_name="TestCase",
            test_case_id="test-4",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.5,
            framework="unittest",
        )

        assert result.is_success()
        assert result.data["status"] == "passed"

    def test_collect_unittest_failure(self, collector):
        """Test parsing unittest failure"""
        stdout = """
test_fail (test_sample.TestCase) ... FAIL

FAILED (failures=1)
"""

        result = collector.execute(
            test_name="TestCase",
            test_case_id="test-5",
            exit_code=1,
            stdout=stdout,
            stderr="",
            duration_seconds=0.2,
            framework="unittest",
        )

        assert result.is_success()
        assert result.data["status"] == "failed"  # Non-zero exit with failures
        assert result.data["failed_count"] == 1

    def test_collect_generic_python_output(self, collector):
        """Test parsing generic Python output"""
        result = collector.execute(
            test_name="script",
            test_case_id="test-6",
            exit_code=0,
            stdout="Test completed successfully",
            stderr="",
            duration_seconds=0.1,
            framework="python",
        )

        assert result.is_success()
        assert result.data["status"] == "passed"
        assert result.data["passed_count"] == 1

    def test_collect_generic_python_error(self, collector):
        """Test parsing generic Python error"""
        stderr = """
Traceback (most recent call last):
  File "script.py", line 10, in main
    divide_by_zero()
ZeroDivisionError: division by zero
"""

        result = collector.execute(
            test_name="script",
            test_case_id="test-7",
            exit_code=1,
            stdout="",
            stderr=stderr,
            duration_seconds=0.05,
            framework="python",
        )

        assert result.is_success()
        assert result.data["status"] in ["failed", "error"]  # Either is acceptable
        assert result.data["error_message"] is not None
        assert "division by zero" in result.data["error_message"]
        assert result.data["stack_trace"] is not None

    def test_collect_mixed_results(self, collector):
        """Test parsing mixed pass/fail results"""
        stdout = """
test_sample.py::test_pass PASSED
test_sample.py::test_fail FAILED
test_sample.py::test_skip SKIPPED

====== 1 passed, 1 failed, 1 skipped in 1.0s ======
"""

        result = collector.execute(
            test_name="test_sample",
            test_case_id="test-8",
            exit_code=1,
            stdout=stdout,
            stderr="",
            duration_seconds=1.0,
            framework="pytest",
        )

        assert result.is_success()
        assert result.data["status"] == "failed"  # Non-zero exit
        assert result.data["passed_count"] == 1
        assert result.data["failed_count"] == 1
        assert result.data["skipped_count"] == 1

    def test_collect_long_output_truncation(self, collector):
        """Test that long output is truncated"""
        # Create very long error message
        long_error = "A" * 1000
        stdout = f"ERROR: {long_error}"

        result = collector.execute(
            test_name="test_long",
            test_case_id="test-9",
            exit_code=1,
            stdout=stdout,
            stderr="",
            duration_seconds=0.1,
            framework="pytest",
        )

        assert result.is_success()
        # Error message should be truncated to 500 chars
        if result.data["error_message"]:
            assert len(result.data["error_message"]) <= 500


class TestExecutionToolsIntegration:
    """Integration tests for execution tools"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        ToolRegistry.clear()
        yield
        ToolRegistry.clear()

    def test_register_test_executor_tool(self):
        """Test registering TestExecutorTool"""
        ToolRegistry.register(TestExecutorTool)

        metadata = ToolRegistry.get_metadata("test_executor")
        assert metadata.name == "test_executor"

    def test_register_result_collector_tool(self):
        """Test registering ResultCollectorTool"""
        ToolRegistry.register(ResultCollectorTool)

        metadata = ToolRegistry.get_metadata("result_collector")
        assert metadata.name == "result_collector"

    def test_list_execution_tools(self):
        """Test listing execution tools by tag"""
        ToolRegistry.register(TestExecutorTool)
        ToolRegistry.register(ResultCollectorTool)

        execution_tools = ToolRegistry.list_tools(tags=["execution"])
        assert len(execution_tools) == 2

        tool_names = [t.name for t in execution_tools]
        assert "test_executor" in tool_names
        assert "result_collector" in tool_names

    def test_get_execution_tools_via_registry(self):
        """Test getting execution tools from registry"""
        ToolRegistry.register(TestExecutorTool)
        ToolRegistry.register(ResultCollectorTool)

        executor = ToolRegistry.get("test_executor")
        collector = ToolRegistry.get("result_collector")

        assert isinstance(executor, TestExecutorTool)
        assert isinstance(collector, ResultCollectorTool)
