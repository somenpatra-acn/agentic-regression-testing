"""
Execution Tools

Tools for safe test execution with resource limits and result collection.
"""

from tools.execution.test_executor import TestExecutorTool
from tools.execution.result_collector import ResultCollectorTool
from tools.registry import register_tool

# Register tools
register_tool(TestExecutorTool)
register_tool(ResultCollectorTool)

__all__ = [
    "TestExecutorTool",
    "ResultCollectorTool",
]
