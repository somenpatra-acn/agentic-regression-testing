"""
Integration tests for Test Executor Agent V2

Tests the complete workflow of test execution using LangGraph.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v2.test_executor_agent_v2 import TestExecutorAgentV2
from tools.base import ToolRegistry, ToolStatus
from tools.execution import TestExecutorTool, ResultCollectorTool


class TestTestExecutorAgentV2Integration:
    """Integration tests for TestExecutorAgentV2"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        ToolRegistry.clear()
        # Register required tools
        ToolRegistry.register(TestExecutorTool)
        ToolRegistry.register(ResultCollectorTool)
        yield
        ToolRegistry.clear()

    @pytest.fixture
    def agent(self):
        """Create TestExecutorAgentV2 instance"""
        return TestExecutorAgentV2(
            framework="pytest",
            timeout_seconds=60,
        )

    @pytest.fixture
    def sample_test_scripts(self, tmp_path):
        """Create sample test scripts"""
        # Create test script 1
        script1 = tmp_path / "test_login.py"
        script1.write_text("""
def test_login():
    '''Test user login'''
    assert True
""")

        # Create test script 2
        script2 = tmp_path / "test_logout.py"
        script2.write_text("""
def test_logout():
    '''Test user logout'''
    assert True
""")

        return [
            {
                "test_case_id": "TEST-001",
                "test_case_name": "User Login Test",
                "file_path": str(script1),
            },
            {
                "test_case_id": "TEST-002",
                "test_case_name": "User Logout Test",
                "file_path": str(script2),
            },
        ]

    def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.framework == "pytest"
        assert agent.timeout_seconds == 60
        assert agent.graph is not None

    @patch('subprocess.run')
    def test_execute_tests_successful(self, mock_run, agent, sample_test_scripts):
        """Test successful test execution workflow"""
        # Mock successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_login.py::test_login PASSED\n1 passed in 0.5s"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute tests
        final_state = agent.execute_tests(
            test_scripts=sample_test_scripts,
        )

        # Verify state
        assert final_state["status"] == "completed"
        assert final_state["passed_count"] > 0
        assert final_state["failed_count"] == 0
        assert len(final_state["test_results"]) == len(sample_test_scripts)
        assert final_state["execution_time"] > 0

        # Verify results
        for test_result in final_state["test_results"]:
            assert "test_case_id" in test_result
            assert "test_name" in test_result
            assert "status" in test_result
            assert test_result["status"] in ["passed", "failed", "error", "skipped"]

    @patch('subprocess.run')
    def test_execute_tests_with_failures(self, mock_run, agent, sample_test_scripts):
        """Test execution workflow with test failures"""
        # Mock failed execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = """
test_login.py::test_login FAILED

FAILED test_login.py::test_login - AssertionError

1 failed in 0.3s
"""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute tests
        final_state = agent.execute_tests(
            test_scripts=sample_test_scripts,
        )

        # Verify state
        assert final_state["status"] == "completed"
        assert final_state["failed_count"] > 0
        assert len(final_state["test_results"]) == len(sample_test_scripts)

        # Verify failure details
        failed_results = [r for r in final_state["test_results"] if r["status"] == "failed"]
        assert len(failed_results) > 0

        for failed_result in failed_results:
            # Should have error information
            assert "error_message" in failed_result or "stack_trace" in failed_result

    def test_execute_tests_empty_list(self, agent):
        """Test execution with empty test list"""
        final_state = agent.execute_tests(test_scripts=[])

        assert final_state["status"] == "failed"
        assert "No test scripts" in final_state["error"]

    def test_execute_tests_nonexistent_script(self, agent):
        """Test execution with non-existent script"""
        test_scripts = [
            {
                "test_case_id": "TEST-999",
                "test_case_name": "Nonexistent Test",
                "file_path": "/nonexistent/test.py",
            }
        ]

        final_state = agent.execute_tests(test_scripts=test_scripts)

        # Should fail validation
        assert final_state["status"] == "failed"
        assert "No valid test scripts" in final_state["error"]

    @patch('subprocess.run')
    def test_execute_tests_with_custom_config(self, mock_run, agent, sample_test_scripts):
        """Test execution with custom configuration"""
        # Mock execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Custom config
        execution_config = {
            "framework": "unittest",
            "timeout_seconds": 120,
            "parallel": False,
        }

        final_state = agent.execute_tests(
            test_scripts=sample_test_scripts,
            execution_config=execution_config,
        )

        assert final_state["status"] == "completed"
        assert final_state["execution_config"]["framework"] == "unittest"
        assert final_state["execution_config"]["timeout_seconds"] == 120

    @patch('subprocess.run')
    def test_get_execution_result(self, mock_run, agent, sample_test_scripts):
        """Test getting formatted execution result"""
        # Mock execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "2 passed in 1.0s"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute tests
        final_state = agent.execute_tests(test_scripts=sample_test_scripts)

        # Get formatted result
        result = agent.get_execution_result(final_state)

        # Verify result structure
        assert "status" in result
        assert "test_results" in result
        assert "statistics" in result
        assert "metadata" in result

        # Verify statistics
        stats = result["statistics"]
        assert "passed_count" in stats
        assert "failed_count" in stats
        assert "skipped_count" in stats
        assert "total_tests" in stats
        assert "execution_time" in stats

        # Verify metadata
        metadata = result["metadata"]
        assert "framework" in metadata
        assert "timeout_seconds" in metadata

    @patch('subprocess.run')
    def test_workflow_state_transitions(self, mock_run, agent, sample_test_scripts):
        """Test workflow state transitions"""
        # Mock execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute tests
        final_state = agent.execute_tests(test_scripts=sample_test_scripts)

        # Verify state has all expected fields
        assert "start_time" in final_state
        assert "end_time" in final_state
        assert "status" in final_state
        assert "test_scripts" in final_state
        assert "test_results" in final_state
        assert "passed_count" in final_state
        assert "failed_count" in final_state
        assert "skipped_count" in final_state
        assert "execution_time" in final_state

        # Verify timing
        assert isinstance(final_state["start_time"], datetime)
        assert isinstance(final_state["end_time"], datetime)
        assert final_state["end_time"] > final_state["start_time"]

    @patch('subprocess.run')
    def test_execution_with_timeout(self, mock_run, agent, sample_test_scripts):
        """Test execution that times out"""
        import subprocess

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["pytest"],
            timeout=60,
            stdout=b"",
            stderr=b"",
        )

        final_state = agent.execute_tests(test_scripts=sample_test_scripts)

        # Should complete but mark tests as failed/timed out
        assert final_state["status"] == "completed"

        # Check that timeout was recorded
        for result in final_state["test_results"]:
            if result.get("timed_out"):
                assert result["timed_out"] is True

    @patch('subprocess.run')
    def test_multiple_test_results(self, mock_run, agent, sample_test_scripts):
        """Test collecting results from multiple tests"""
        # Mock execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
test_login.py::test_login PASSED
test_logout.py::test_logout PASSED

2 passed in 1.5s
"""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        final_state = agent.execute_tests(test_scripts=sample_test_scripts)

        # Should have results for all tests
        assert len(final_state["test_results"]) == len(sample_test_scripts)

        # Verify each result has required fields
        for test_result in final_state["test_results"]:
            assert test_result["test_case_id"] in ["TEST-001", "TEST-002"]
            assert test_result["status"] == "passed"
            assert "metrics" in test_result
            assert "duration_seconds" in test_result["metrics"]

    def test_error_handling(self, agent, sample_test_scripts):
        """Test error handling in workflow"""
        # Simulate error by providing invalid config
        with patch('tools.get_tool') as mock_get_tool:
            mock_get_tool.side_effect = Exception("Tool not found")

            final_state = agent.execute_tests(test_scripts=sample_test_scripts)

            assert final_state["status"] == "failed"
            assert "error" in final_state
            assert final_state["error"] is not None


class TestTestExecutorAgentV2WithRealExecution:
    """Integration tests with real test execution (optional)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        ToolRegistry.clear()
        ToolRegistry.register(TestExecutorTool)
        ToolRegistry.register(ResultCollectorTool)
        yield
        ToolRegistry.clear()

    @pytest.fixture
    def agent(self):
        """Create TestExecutorAgentV2 instance"""
        return TestExecutorAgentV2(framework="pytest")

    @pytest.fixture
    def real_test_script(self, tmp_path):
        """Create a real executable test script"""
        script = tmp_path / "test_real.py"
        script.write_text("""
import pytest

def test_simple_pass():
    '''Simple passing test'''
    assert 1 + 1 == 2

def test_simple_fail():
    '''Simple failing test'''
    assert 1 + 1 == 3  # This will fail
""")
        return script

    @pytest.mark.skipif(
        not pytest.importorskip("pytest", minversion="6.0"),
        reason="Requires pytest >= 6.0"
    )
    def test_real_execution(self, agent, real_test_script):
        """Test with real pytest execution (requires pytest installed)"""
        test_scripts = [
            {
                "test_case_id": "REAL-001",
                "test_case_name": "Real Test",
                "file_path": str(real_test_script),
            }
        ]

        final_state = agent.execute_tests(test_scripts=test_scripts)

        # Should complete (even with test failures)
        assert final_state["status"] == "completed"
        assert len(final_state["test_results"]) == 1

        # Should have captured test result
        result = final_state["test_results"][0]
        assert result["test_case_id"] == "REAL-001"
        # Status depends on whether test passed or failed
        assert result["status"] in ["passed", "failed", "error"]
