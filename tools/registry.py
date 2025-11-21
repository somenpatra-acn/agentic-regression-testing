"""
Tool Registry Helper Functions

Convenience functions for tool management.
"""

from typing import List, Optional, Dict, Any
from tools.base import BaseTool, ToolRegistry, ToolMetadata


def register_tool(tool_class: type) -> None:
    """
    Register a tool class

    Args:
        tool_class: Tool class to register

    Example:
        @register_tool
        class MyTool(BaseTool):
            ...
    """
    ToolRegistry.register(tool_class)


def get_tool(tool_name: str, config: Optional[Dict[str, Any]] = None) -> BaseTool:
    """
    Get a tool instance by name

    Args:
        tool_name: Name of the tool
        config: Optional configuration

    Returns:
        BaseTool instance

    Example:
        tool = get_tool("web_discovery", config={"timeout": 30})
        result = tool.execute(url="https://example.com")
    """
    return ToolRegistry.get(tool_name, config=config)


def list_tools(tags: Optional[List[str]] = None) -> List[ToolMetadata]:
    """
    List all registered tools

    Args:
        tags: Optional list of tags to filter by

    Returns:
        List of tool metadata

    Example:
        # List all tools
        all_tools = list_tools()

        # List only discovery tools
        discovery_tools = list_tools(tags=["discovery"])
    """
    return ToolRegistry.list_tools(tags=tags)


def get_tool_metadata(tool_name: str) -> ToolMetadata:
    """
    Get tool metadata without instantiating

    Args:
        tool_name: Name of the tool

    Returns:
        ToolMetadata

    Example:
        metadata = get_tool_metadata("web_discovery")
        print(f"Description: {metadata.description}")
    """
    return ToolRegistry.get_metadata(tool_name)
