"""
Unit Tests for Discovery Tools

Tests WebDiscoveryTool and APIDiscoveryTool with mocked adapters.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.discovery.web_discovery import WebDiscoveryTool
from tools.discovery.api_discovery import APIDiscoveryTool
from tools.base import ToolStatus, ToolRegistry
from adapters.base_adapter import DiscoveryResult, Element


@pytest.mark.unit
class TestWebDiscoveryTool:
    """Test WebDiscoveryTool"""

    @pytest.fixture
    def web_tool(self, sample_web_app_profile):
        """Create web discovery tool"""
        return WebDiscoveryTool(config={"app_profile": sample_web_app_profile})

    def test_tool_metadata(self, web_tool):
        """Test tool metadata"""
        metadata = web_tool.metadata

        assert metadata.name == "web_discovery"
        assert metadata.version == "1.0.0"
        assert "discovery" in metadata.tags
        assert "web" in metadata.tags
        assert metadata.requires_auth is True

    def test_config_validation(self, sample_web_app_profile):
        """Test config validation"""
        # Missing app_profile should raise error
        with pytest.raises(ValueError, match="app_profile is required"):
            WebDiscoveryTool(config={})

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_successful_discovery(self, mock_get_adapter, web_tool, sample_discovery_result):
        """Test successful web discovery"""
        # Setup mock adapter
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            elements=[
                Element(
                    id="test_button",
                    type="button",
                    name="Test Button",
                    selector="#test-btn"
                )
            ],
            pages=["/", "/test"],
            metadata={}
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        # Execute discovery
        result = web_tool.execute()

        # Assertions
        assert result.is_success()
        assert "elements" in result.data
        assert "pages" in result.data
        assert result.metadata["total_elements"] == 1
        assert result.metadata["total_pages"] == 2
        assert mock_adapter.cleanup.called

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_discovery_disabled(self, mock_get_adapter, sample_web_app_profile):
        """Test discovery when disabled in config"""
        # Disable discovery
        sample_web_app_profile.discovery.enabled = False

        tool = WebDiscoveryTool(config={"app_profile": sample_web_app_profile})
        result = tool.execute()

        # Should fail when discovery is disabled
        assert result.is_failure()
        assert "disabled" in result.error.lower()

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_discovery_with_parameters(self, mock_get_adapter, web_tool):
        """Test discovery with override parameters"""
        mock_adapter = Mock()
        mock_adapter.discover_elements.return_value = DiscoveryResult()
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        # Execute with parameters
        result = web_tool.execute(
            url="https://custom.example.com",
            max_depth=5,
            max_pages=20
        )

        # Check that parameters were applied
        app_profile = web_tool.config["app_profile"]
        assert app_profile.discovery.url == "https://custom.example.com"
        assert app_profile.discovery.max_depth == 5
        assert app_profile.discovery.max_pages == 20

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_missing_playwright_dependency(self, mock_get_adapter, web_tool):
        """Test handling missing Playwright dependency"""
        mock_get_adapter.side_effect = ImportError("Playwright not installed")

        result = web_tool.execute()

        assert result.is_failure()
        assert result.status == ToolStatus.ERROR
        assert "Missing dependency" in result.error
        assert "Playwright" in result.metadata.get("suggestion", "")

    @patch('tools.discovery.web_adapter.get_adapter')
    def test_discovery_exception(self, mock_get_adapter, web_tool):
        """Test handling discovery exceptions"""
        mock_get_adapter.side_effect = Exception("Connection timeout")

        result = web_tool.execute()

        assert result.is_failure()
        assert result.status == ToolStatus.ERROR
        assert "Discovery failed" in result.error
        assert result.metadata["exception_type"] == "Exception"

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_adapter_cleanup_on_error(self, mock_get_adapter, web_tool):
        """Test that adapter cleanup is called even on error"""
        mock_adapter = Mock()
        mock_adapter.discover_elements.side_effect = Exception("Test error")
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        result = web_tool.execute()

        # Cleanup should be called even on error
        assert mock_adapter.cleanup.called
        assert result.is_failure()

    def test_element_type_counting(self, web_tool):
        """Test element type counting in metadata"""
        discovery_result = DiscoveryResult(
            elements=[
                Element(id="btn1", type="button", name="Button 1", selector="#btn1"),
                Element(id="btn2", type="button", name="Button 2", selector="#btn2"),
                Element(id="input1", type="input", name="Input 1", selector="#input1"),
                Element(id="link1", type="link", name="Link 1", selector="#link1"),
            ]
        )

        type_counts = web_tool._count_element_types(discovery_result)

        assert type_counts["button"] == 2
        assert type_counts["input"] == 1
        assert type_counts["link"] == 1


@pytest.mark.unit
class TestAPIDiscoveryTool:
    """Test APIDiscoveryTool"""

    @pytest.fixture
    def api_tool(self, sample_api_app_profile):
        """Create API discovery tool"""
        return APIDiscoveryTool(config={"app_profile": sample_api_app_profile})

    def test_tool_metadata(self, api_tool):
        """Test tool metadata"""
        metadata = api_tool.metadata

        assert metadata.name == "api_discovery"
        assert metadata.version == "1.0.0"
        assert "api" in metadata.tags
        assert "openapi" in metadata.tags
        assert metadata.requires_auth is False

    def test_config_validation(self):
        """Test config validation"""
        with pytest.raises(ValueError, match="app_profile is required"):
            APIDiscoveryTool(config={})

    @patch('tools.discovery.api_discovery.get_adapter')
    def test_successful_api_discovery(self, mock_get_adapter, api_tool):
        """Test successful API discovery"""
        # Setup mock adapter
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            apis=[
                {"path": "/users", "method": "GET", "description": "Get users"},
                {"path": "/users", "method": "POST", "description": "Create user"},
                {"path": "/users/{id}", "method": "GET", "description": "Get user by ID"},
            ],
            metadata={"openapi_version": "3.0.0"}
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        # Execute discovery
        result = api_tool.execute()

        # Assertions
        assert result.is_success()
        assert "apis" in result.data
        assert len(result.data["apis"]) == 3
        assert result.metadata["total_endpoints"] == 3
        assert result.metadata["spec_version"] == "3.0.0"
        assert mock_adapter.cleanup.called

    @patch('tools.discovery.api_discovery.get_adapter')
    def test_filter_deprecated_endpoints(self, mock_get_adapter, api_tool):
        """Test filtering deprecated endpoints"""
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            apis=[
                {"path": "/users", "method": "GET", "deprecated": False},
                {"path": "/old-api", "method": "GET", "deprecated": True},
                {"path": "/posts", "method": "GET", "deprecated": False},
            ],
            metadata={}
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        # Execute without including deprecated
        result = api_tool.execute(include_deprecated=False)

        assert result.is_success()
        assert len(result.data["apis"]) == 2  # Should exclude deprecated
        assert all(not api.get("deprecated", False) for api in result.data["apis"])

    @patch('tools.discovery.api_discovery.get_adapter')
    def test_filter_by_methods(self, mock_get_adapter, api_tool):
        """Test filtering by HTTP methods"""
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            apis=[
                {"path": "/users", "method": "GET"},
                {"path": "/users", "method": "POST"},
                {"path": "/users/{id}", "method": "DELETE"},
                {"path": "/posts", "method": "GET"},
            ],
            metadata={}
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        # Execute filtering only GET methods
        result = api_tool.execute(methods=["GET"])

        assert result.is_success()
        assert len(result.data["apis"]) == 2
        assert all(api["method"] == "GET" for api in result.data["apis"])

    @patch('tools.discovery.api_discovery.get_adapter')
    def test_method_counting(self, mock_get_adapter, api_tool):
        """Test method counting in metadata"""
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            apis=[
                {"method": "GET"}, {"method": "GET"}, {"method": "GET"},
                {"method": "POST"}, {"method": "POST"},
                {"method": "DELETE"},
            ],
            metadata={}
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        result = api_tool.execute()

        assert result.is_success()
        method_counts = result.metadata["method_counts"]
        assert method_counts["GET"] == 3
        assert method_counts["POST"] == 2
        assert method_counts["DELETE"] == 1

    @patch('tools.discovery.api_discovery.get_adapter')
    def test_spec_url_override(self, mock_get_adapter, api_tool, sample_api_app_profile):
        """Test overriding spec URL"""
        mock_adapter = Mock()
        mock_adapter.discover_elements.return_value = DiscoveryResult()
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        original_url = sample_api_app_profile.discovery.url
        custom_url = "https://custom.api.com/spec.json"

        result = api_tool.execute(spec_url=custom_url)

        # URL should be restored after execution
        assert sample_api_app_profile.discovery.url == original_url

    @patch('tools.discovery.api_discovery.get_adapter')
    def test_missing_dependency(self, mock_get_adapter, api_tool):
        """Test handling missing dependencies"""
        mock_get_adapter.side_effect = ImportError("openapi-spec-validator not found")

        result = api_tool.execute()

        assert result.is_failure()
        assert "Missing dependency" in result.error
        assert "suggestion" in result.metadata


@pytest.mark.unit
class TestDiscoveryToolsIntegration:
    """Integration tests for discovery tools"""

    def test_web_tool_registration(self):
        """Test registering WebDiscoveryTool"""
        ToolRegistry.register(WebDiscoveryTool)

        metadata = ToolRegistry.get_metadata("web_discovery")
        assert metadata.name == "web_discovery"
        assert "discovery" in metadata.tags

    def test_api_tool_registration(self):
        """Test registering APIDiscoveryTool"""
        ToolRegistry.register(APIDiscoveryTool)

        metadata = ToolRegistry.get_metadata("api_discovery")
        assert metadata.name == "api_discovery"
        assert "api" in metadata.tags

    def test_list_discovery_tools(self):
        """Test listing discovery tools by tag"""
        ToolRegistry.register(WebDiscoveryTool)
        ToolRegistry.register(APIDiscoveryTool)

        discovery_tools = ToolRegistry.list_tools(tags=["discovery"])

        assert len(discovery_tools) == 2
        tool_names = [t.name for t in discovery_tools]
        assert "web_discovery" in tool_names
        assert "api_discovery" in tool_names
