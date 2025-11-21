"""
API Discovery Tool

Discovers REST API endpoints from OpenAPI/Swagger specifications.
"""

from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata
from adapters import get_adapter
from adapters.base_adapter import DiscoveryResult
from models.app_profile import ApplicationProfile


class APIDiscoveryTool(BaseTool):
    """
    Discovers API endpoints from OpenAPI/Swagger specs

    This tool wraps the APIAdapter to provide API discovery
    as a reusable tool for agents.

    Features:
    - Parses OpenAPI 2.0 and 3.0 specifications
    - Discovers endpoints, methods, parameters, and schemas
    - Extracts authentication requirements
    - Identifies request/response models
    """

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        if not self.config.get("app_profile"):
            raise ValueError("app_profile is required in config")

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="api_discovery",
            description="Discovers REST API endpoints from OpenAPI/Swagger specifications",
            version="1.0.0",
            tags=["discovery", "api", "rest", "openapi", "swagger"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "spec_url": "string (optional) - OpenAPI spec URL, overrides app config",
                "include_deprecated": "boolean - Include deprecated endpoints",
                "methods": "list (optional) - Filter by HTTP methods (GET, POST, etc)",
            },
            output_schema={
                "apis": "list - Discovered API endpoints with methods and schemas",
                "schemas": "dict - Data models and schemas",
                "metadata": "dict - API specification metadata",
            }
        )

    def execute(
        self,
        spec_url: Optional[str] = None,
        include_deprecated: bool = False,
        methods: Optional[List[str]] = None,
    ) -> ToolResult:
        """
        Discover API endpoints from OpenAPI specification

        Args:
            spec_url: OpenAPI spec URL (defaults to app config)
            include_deprecated: Include deprecated endpoints
            methods: Filter by HTTP methods (e.g., ["GET", "POST"])

        Returns:
            ToolResult containing discovered APIs and schemas
        """
        return self._wrap_execution(
            self._discover,
            spec_url=spec_url,
            include_deprecated=include_deprecated,
            methods=methods,
        )

    def _discover(
        self,
        spec_url: Optional[str],
        include_deprecated: bool,
        methods: Optional[List[str]],
    ) -> ToolResult:
        """Internal discovery logic"""

        app_profile: ApplicationProfile = self.config["app_profile"]

        # Override spec URL if provided
        if spec_url is not None:
            # Store original and temporarily override
            original_url = app_profile.discovery.url
            app_profile.discovery.url = spec_url

        adapter = None
        try:
            adapter = get_adapter(app_profile)

            # Perform discovery
            discovery_result: DiscoveryResult = adapter.discover_elements()

            # Filter results based on parameters
            filtered_apis = discovery_result.apis
            if not include_deprecated:
                filtered_apis = [
                    api for api in filtered_apis
                    if not api.get("deprecated", False)
                ]

            if methods:
                methods_upper = [m.upper() for m in methods]
                filtered_apis = [
                    api for api in filtered_apis
                    if api.get("method", "").upper() in methods_upper
                ]

            # Count endpoints by method
            method_counts = {}
            for api in filtered_apis:
                method = api.get("method", "UNKNOWN").upper()
                method_counts[method] = method_counts.get(method, 0) + 1

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "apis": filtered_apis,
                    "schema": discovery_result.schema,
                    "metadata": discovery_result.metadata,
                },
                metadata={
                    "app_name": app_profile.name,
                    "total_endpoints": len(filtered_apis),
                    "method_counts": method_counts,
                    "has_authentication": bool(app_profile.auth.auth_type != "none"),
                    "spec_version": discovery_result.metadata.get("openapi_version", "unknown"),
                }
            )

        except ImportError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Missing dependency: {str(e)}",
                metadata={
                    "suggestion": "Install required packages: pip install requests openapi-spec-validator"
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"API discovery failed: {str(e)}",
                metadata={
                    "app_name": app_profile.name,
                    "exception_type": type(e).__name__,
                }
            )

        finally:
            # Restore original URL if it was overridden
            if spec_url is not None:
                app_profile.discovery.url = original_url

            # Cleanup adapter resources
            if adapter:
                try:
                    adapter.cleanup()
                except Exception:
                    pass
