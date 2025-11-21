"""
Unit Tests for Tool Framework

Tests the base tool classes, ToolRegistry, and tool execution.
"""

import pytest
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata, ToolRegistry
from tools import register_tool, get_tool, list_tools


class DummyTool(BaseTool):
    """A simple tool for testing"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="dummy_tool",
            description="A dummy tool for testing",
            version="1.0.0",
            tags=["test", "dummy"],
            is_safe=True,
        )

    def execute(self, value: int = 0) -> ToolResult:
        """Execute dummy operation"""
        return self._wrap_execution(self._do_work, value=value)

    def _do_work(self, value: int) -> ToolResult:
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=value * 2,
            metadata={"operation": "multiply by 2"}
        )


class FailingTool(BaseTool):
    """A tool that always fails for testing error handling"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="failing_tool",
            description="A tool that fails",
            version="1.0.0",
            tags=["test"],
            is_safe=True,
        )

    def execute(self) -> ToolResult:
        """Always raises an exception"""
        return self._wrap_execution(self._fail)

    def _fail(self):
        raise ValueError("This tool always fails")


class ConfigurableTool(BaseTool):
    """A tool with configuration for testing"""

    def _validate_config(self) -> None:
        if "required_param" not in self.config:
            raise ValueError("required_param is missing from config")

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="configurable_tool",
            description="A tool with configuration",
            version="1.0.0",
            tags=["test", "config"],
            is_safe=True,
        )

    def execute(self, input_value: str) -> ToolResult:
        """Execute with config"""
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=f"{input_value}_{self.config['required_param']}",
            metadata={"config": self.config}
        )


# ========== Test Classes ==========

@pytest.mark.unit
class TestToolResult:
    """Test ToolResult class"""

    def test_tool_result_creation(self):
        """Test creating a ToolResult"""
        result = ToolResult(
            status=ToolStatus.SUCCESS,
            data={"key": "value"},
            metadata={"tool": "test"}
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.data == {"key": "value"}
        assert result.metadata["tool"] == "test"
        assert result.is_success()
        assert not result.is_failure()

    def test_tool_result_failure(self):
        """Test failure ToolResult"""
        result = ToolResult(
            status=ToolStatus.FAILURE,
            error="Something went wrong"
        )

        assert result.status == ToolStatus.FAILURE
        assert result.error == "Something went wrong"
        assert result.is_failure()
        assert not result.is_success()

    def test_tool_result_error(self):
        """Test error ToolResult"""
        result = ToolResult(
            status=ToolStatus.ERROR,
            error="Exception occurred"
        )

        assert result.status == ToolStatus.ERROR
        assert result.is_failure()


@pytest.mark.unit
class TestBaseTool:
    """Test BaseTool abstract class"""

    def test_tool_instantiation(self):
        """Test creating a tool instance"""
        tool = DummyTool()

        assert tool.metadata.name == "dummy_tool"
        assert tool.metadata.version == "1.0.0"
        assert "test" in tool.metadata.tags

    def test_tool_with_config(self):
        """Test tool with configuration"""
        config = {"required_param": "test_value"}
        tool = ConfigurableTool(config=config)

        assert tool.config == config
        assert tool.config["required_param"] == "test_value"

    def test_tool_config_validation_failure(self):
        """Test tool config validation"""
        with pytest.raises(ValueError, match="required_param is missing"):
            ConfigurableTool(config={})

    def test_tool_execution(self):
        """Test tool execution"""
        tool = DummyTool()
        result = tool.execute(value=5)

        assert result.is_success()
        assert result.data == 10
        assert result.execution_time > 0

    def test_tool_execution_with_error(self):
        """Test tool execution with error"""
        tool = FailingTool()
        result = tool.execute()

        assert result.is_failure()
        assert result.status == ToolStatus.ERROR
        assert "This tool always fails" in result.error
        assert result.metadata["exception_type"] == "ValueError"

    def test_tool_str_repr(self):
        """Test tool string representation"""
        tool = DummyTool()

        assert str(tool) == "dummy_tool v1.0.0"
        assert "DummyTool" in repr(tool)
        assert "dummy_tool" in repr(tool)


@pytest.mark.unit
class TestToolRegistry:
    """Test ToolRegistry"""

    def test_register_tool(self):
        """Test registering a tool"""
        ToolRegistry.register(DummyTool)

        tools = ToolRegistry.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "dummy_tool"

    def test_register_multiple_tools(self):
        """Test registering multiple tools"""
        ToolRegistry.register(DummyTool)
        ToolRegistry.register(FailingTool)
        ToolRegistry.register(ConfigurableTool)

        tools = ToolRegistry.list_tools()
        assert len(tools) == 3

        tool_names = [t.name for t in tools]
        assert "dummy_tool" in tool_names
        assert "failing_tool" in tool_names
        assert "configurable_tool" in tool_names

    def test_register_non_tool_class(self):
        """Test registering a non-tool class fails"""
        class NotATool:
            pass

        with pytest.raises(ValueError, match="must inherit from BaseTool"):
            ToolRegistry.register(NotATool)

    def test_get_tool(self):
        """Test getting a tool by name"""
        ToolRegistry.register(DummyTool)

        tool = ToolRegistry.get("dummy_tool")

        assert isinstance(tool, DummyTool)
        assert tool.metadata.name == "dummy_tool"

    def test_get_tool_with_config(self):
        """Test getting a tool with configuration"""
        ToolRegistry.register(ConfigurableTool)

        config = {"required_param": "test123"}
        tool = ToolRegistry.get("configurable_tool", config=config)

        assert isinstance(tool, ConfigurableTool)
        assert tool.config["required_param"] == "test123"

    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist"""
        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            ToolRegistry.get("nonexistent")

    def test_get_metadata(self):
        """Test getting tool metadata without instantiation"""
        ToolRegistry.register(DummyTool)

        metadata = ToolRegistry.get_metadata("dummy_tool")

        assert metadata.name == "dummy_tool"
        assert metadata.description == "A dummy tool for testing"
        assert metadata.version == "1.0.0"

    def test_list_tools_with_tags(self):
        """Test listing tools filtered by tags"""
        ToolRegistry.register(DummyTool)
        ToolRegistry.register(ConfigurableTool)

        # Filter by 'config' tag
        tools = ToolRegistry.list_tools(tags=["config"])

        assert len(tools) == 1
        assert tools[0].name == "configurable_tool"

    def test_overwrite_warning(self, caplog):
        """Test warning when overwriting a tool"""
        ToolRegistry.register(DummyTool)

        # Register again - should warn
        ToolRegistry.register(DummyTool)

        assert "Overwriting tool 'dummy_tool'" in caplog.text

    def test_clear_registry(self):
        """Test clearing the registry"""
        ToolRegistry.register(DummyTool)
        ToolRegistry.register(FailingTool)

        assert len(ToolRegistry.list_tools()) == 2

        ToolRegistry.clear()

        assert len(ToolRegistry.list_tools()) == 0


@pytest.mark.unit
class TestToolHelpers:
    """Test helper functions"""

    def test_register_tool_decorator(self):
        """Test register_tool helper function"""
        register_tool(DummyTool)

        tools = list_tools()
        assert len(tools) == 1
        assert tools[0].name == "dummy_tool"

    def test_get_tool_helper(self):
        """Test get_tool helper function"""
        register_tool(DummyTool)

        tool = get_tool("dummy_tool")

        assert isinstance(tool, DummyTool)

    def test_list_tools_helper(self):
        """Test list_tools helper function"""
        register_tool(DummyTool)
        register_tool(FailingTool)

        tools = list_tools()

        assert len(tools) == 2

    def test_list_tools_with_tags_helper(self):
        """Test list_tools with tag filtering"""
        register_tool(DummyTool)
        register_tool(ConfigurableTool)

        tools = list_tools(tags=["config"])

        assert len(tools) == 1
        assert tools[0].name == "configurable_tool"


@pytest.mark.unit
class TestToolExecution:
    """Test tool execution patterns"""

    def test_execution_timing(self):
        """Test that execution time is measured"""
        tool = DummyTool()
        result = tool.execute(value=10)

        assert result.execution_time > 0
        assert result.execution_time < 1.0  # Should be very fast

    def test_execution_metadata(self):
        """Test that metadata is preserved"""
        tool = DummyTool()
        result = tool.execute(value=5)

        assert "tool" in result.metadata
        assert result.metadata["tool"] == "dummy_tool"

    def test_execution_timestamp(self):
        """Test that timestamp is recorded"""
        tool = DummyTool()
        result = tool.execute(value=5)

        assert result.timestamp is not None
        assert isinstance(result.timestamp, type(result.timestamp))
