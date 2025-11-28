"""
Discovery Tools

Tools for discovering application elements, APIs, and testable components.
"""

from tools.discovery.web_discovery import WebDiscoveryTool
from tools.discovery.api_discovery import APIDiscoveryTool
from tools.registry import register_tool

# Register tools
register_tool(WebDiscoveryTool)
register_tool(APIDiscoveryTool)

__all__ = [
    "WebDiscoveryTool",
    "APIDiscoveryTool",
]
