"""
Web Discovery Tool

Discovers web application elements using Playwright through the WebAdapter.
"""

from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata
from adapters import get_adapter
from adapters.base_adapter import DiscoveryResult
from models.app_profile import ApplicationProfile


class WebDiscoveryTool(BaseTool):
    """
    Discovers UI elements from web applications

    This tool wraps the WebAdapter to provide element discovery
    as a reusable tool for agents.

    Features:
    - Crawls web pages up to configured depth
    - Discovers buttons, inputs, links, and interactive elements
    - Respects URL filters and crawl limits
    - Captures page structure and navigation paths
    """

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        if not self.config.get("app_profile"):
            raise ValueError("app_profile is required in config")

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="web_discovery",
            description="Discovers UI elements from web applications using Playwright",
            version="1.0.0",
            tags=["discovery", "web", "ui", "playwright"],
            requires_auth=True,
            is_safe=True,
            input_schema={
                "url": "string (optional) - Starting URL for discovery, defaults to app base_url",
                "max_depth": "integer (optional) - Maximum crawl depth, overrides app config",
                "max_pages": "integer (optional) - Maximum pages to crawl, overrides app config",
            },
            output_schema={
                "elements": "list - Discovered UI elements with selectors and attributes",
                "pages": "list - URLs of discovered pages",
                "metadata": "dict - Discovery statistics and information",
            }
        )

    def execute(
        self,
        url: Optional[str] = None,
        max_depth: Optional[int] = None,
        max_pages: Optional[int] = None,
    ) -> ToolResult:
        """
        Discover elements from a web application

        Args:
            url: Starting URL (defaults to app_profile.base_url)
            max_depth: Maximum crawl depth (defaults to app config)
            max_pages: Maximum pages to crawl (defaults to app config)

        Returns:
            ToolResult containing discovered elements and pages
        """
        return self._wrap_execution(
            self._discover,
            url=url,
            max_depth=max_depth,
            max_pages=max_pages,
        )

    def _discover(
        self,
        url: Optional[str],
        max_depth: Optional[int],
        max_pages: Optional[int],
    ) -> ToolResult:
        """Internal discovery logic"""

        app_profile: ApplicationProfile = self.config["app_profile"]

        # Override discovery config if parameters provided
        if max_depth is not None:
            app_profile.discovery.max_depth = max_depth
        if max_pages is not None:
            app_profile.discovery.max_pages = max_pages
        if url is not None:
            app_profile.discovery.url = url

        # Get web adapter
        adapter = None
        try:
            adapter = get_adapter(app_profile.adapter, app_profile)

            # Ensure discovery is enabled
            if not app_profile.discovery.enabled:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Discovery is disabled in application profile",
                    metadata={"app_name": app_profile.name}
                )

            # Perform discovery
            discovery_result: DiscoveryResult = adapter.discover_elements()

            # Convert to dict for serialization
            result_dict = discovery_result.to_dict()

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result_dict,
                metadata={
                    "app_name": app_profile.name,
                    "total_elements": len(discovery_result.elements),
                    "total_pages": len(discovery_result.pages),
                    "element_types": self._count_element_types(discovery_result),
                    "crawl_depth": app_profile.discovery.max_depth,
                }
            )

        except ImportError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Missing dependency: {str(e)}",
                metadata={"suggestion": "Install Playwright: pip install playwright && playwright install"}
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Discovery failed: {str(e)}",
                metadata={
                    "app_name": app_profile.name,
                    "exception_type": type(e).__name__,
                }
            )

        finally:
            # Cleanup adapter resources
            if adapter:
                try:
                    adapter.cleanup()
                except Exception as e:
                    # Log but don't fail on cleanup errors
                    pass

    def _count_element_types(self, discovery_result: DiscoveryResult) -> Dict[str, int]:
        """Count elements by type for metadata"""
        type_counts = {}
        for element in discovery_result.elements:
            element_type = element.type
            type_counts[element_type] = type_counts.get(element_type, 0) + 1
        return type_counts
