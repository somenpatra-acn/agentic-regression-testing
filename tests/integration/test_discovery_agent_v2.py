"""
Integration Tests for Discovery Agent V2

Tests the complete Discovery Agent workflow with LangGraph and tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from tools.base import ToolRegistry
from tools.validation.input_sanitizer import InputSanitizerTool
from tools.validation.path_validator import PathValidatorTool
from tools.discovery.web_discovery import WebDiscoveryTool
from tools.discovery.api_discovery import APIDiscoveryTool
from adapters.base_adapter import DiscoveryResult, Element


@pytest.mark.integration
class TestDiscoveryAgentV2Integration:
    """Integration tests for Discovery Agent V2"""

    @pytest.fixture(autouse=True)
    def setup_tools(self):
        """Register all required tools before each test"""
        ToolRegistry.clear()
        ToolRegistry.register(InputSanitizerTool)
        ToolRegistry.register(PathValidatorTool)
        ToolRegistry.register(WebDiscoveryTool)
        ToolRegistry.register(APIDiscoveryTool)
        yield
        ToolRegistry.clear()

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_complete_web_discovery_workflow(
        self, mock_get_adapter, sample_web_app_profile
    ):
        """Test complete web discovery workflow"""
        # Setup mock adapter
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            elements=[
                Element(
                    id="login_button",
                    type="button",
                    name="Login",
                    selector="#login-btn",
                    page_url="/login"
                ),
                Element(
                    id="username_input",
                    type="input",
                    name="Username",
                    selector="#username",
                    page_url="/login"
                ),
            ],
            pages=["/", "/login", "/dashboard"],
            metadata={"crawl_time": 5.2}
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        # Create agent
        agent = DiscoveryAgentV2(
            app_profile=sample_web_app_profile,
            enable_hitl=False
        )

        # Execute discovery
        final_state = agent.discover()

        # Assertions on state
        assert final_state["status"] == "completed"
        assert len(final_state["elements"]) == 2
        assert len(final_state["pages"]) == 3
        assert final_state["total_elements"] == 2
        assert final_state["total_pages"] == 3
        assert "button" in final_state["element_types"]
        assert "input" in final_state["element_types"]
        assert final_state["error"] is None

        # Get formatted result
        result = agent.get_discovery_result(final_state)

        assert result["status"] == "completed"
        assert len(result["elements"]) == 2
        assert result["statistics"]["total_elements"] == 2
        assert result["metadata"]["app_name"] == "test_web_app"
        assert result["metadata"]["execution_time"] is not None

    @patch('tools.discovery.api_discovery.get_adapter')
    def test_complete_api_discovery_workflow(
        self, mock_get_adapter, sample_api_app_profile
    ):
        """Test complete API discovery workflow"""
        # Setup mock adapter
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            apis=[
                {"path": "/users", "method": "GET", "description": "List users"},
                {"path": "/users/{id}", "method": "GET", "description": "Get user"},
                {"path": "/users", "method": "POST", "description": "Create user"},
            ],
            metadata={"openapi_version": "3.0.0"}
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        # Create agent
        agent = DiscoveryAgentV2(
            app_profile=sample_api_app_profile,
            enable_hitl=False
        )

        # Execute discovery
        final_state = agent.discover()

        # Assertions
        assert final_state["status"] == "completed"
        assert len(final_state["apis"]) == 3
        assert final_state["total_elements"] == 3
        assert final_state["error"] is None

        # Get formatted result
        result = agent.get_discovery_result(final_state)

        assert result["status"] == "completed"
        assert len(result["apis"]) == 3
        assert result["metadata"]["app_type"] == "api"

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_discovery_with_parameters(
        self, mock_get_adapter, sample_web_app_profile
    ):
        """Test discovery with custom parameters"""
        mock_adapter = Mock()
        mock_adapter.discover_elements.return_value = DiscoveryResult()
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        # Execute with custom parameters
        final_state = agent.discover(
            url="https://custom.example.com",
            max_depth=5,
            max_pages=20
        )

        # Verify parameters were used
        assert final_state["discovery_params"]["url"] == "https://custom.example.com"
        assert final_state["discovery_params"]["max_depth"] == 5
        assert final_state["discovery_params"]["max_pages"] == 20

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_input_validation_in_workflow(
        self, mock_get_adapter, sample_web_app_profile
    ):
        """Test that input validation occurs in the workflow"""
        mock_adapter = Mock()
        mock_adapter.discover_elements.return_value = DiscoveryResult()
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        # Execute with potentially malicious input
        final_state = agent.discover(
            feature_description="Test <script>alert('xss')</script> feature"
        )

        # Should have validation warnings
        assert len(final_state.get("validation_warnings", [])) > 0
        assert "HTML tags" in str(final_state.get("validation_warnings", []))

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_error_handling(self, mock_get_adapter, sample_web_app_profile):
        """Test error handling in discovery workflow"""
        # Make adapter raise an exception
        mock_get_adapter.side_effect = Exception("Connection failed")

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        # Execute discovery
        final_state = agent.discover()

        # Should handle error gracefully
        assert final_state["status"] == "failed"
        assert final_state["error"] is not None
        assert "Connection failed" in final_state["error"] or "error" in final_state["error"]

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_discovery_disabled(self, mock_get_adapter, sample_web_app_profile):
        """Test behavior when discovery is disabled"""
        sample_web_app_profile.discovery.enabled = False

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.discover()

        # Should fail when discovery is disabled
        assert final_state["status"] == "failed"
        assert "disabled" in final_state["error"].lower()

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_execution_timing(self, mock_get_adapter, sample_web_app_profile):
        """Test that execution time is tracked"""
        mock_adapter = Mock()
        mock_adapter.discover_elements.return_value = DiscoveryResult()
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.discover()

        # Should have timing information
        assert "start_time" in final_state
        assert "end_time" in final_state
        assert final_state["start_time"] < final_state["end_time"]

        # Formatted result should include execution time
        result = agent.get_discovery_result(final_state)
        assert result["metadata"]["execution_time"] is not None
        assert result["metadata"]["execution_time"] > 0

    def test_unsupported_app_type(self, sample_web_app_profile):
        """Test handling unsupported application type"""
        # Set unsupported type
        sample_web_app_profile.type = "database"  # Not implemented yet

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.discover()

        # Should fail with unsupported type error
        assert final_state["status"] == "failed"
        assert "unsupported" in final_state["error"].lower()

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_state_tracking_through_workflow(
        self, mock_get_adapter, sample_web_app_profile
    ):
        """Test that state is properly tracked through the workflow"""
        mock_adapter = Mock()
        mock_discovery_result = DiscoveryResult(
            elements=[
                Element(id="el1", type="button", name="Button", selector="#btn")
            ],
            pages=["/page1"],
        )
        mock_adapter.discover_elements.return_value = mock_discovery_result
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.discover()

        # Verify all state fields are populated correctly
        assert final_state["app_profile"] == sample_web_app_profile
        assert final_state["status"] == "completed"
        assert isinstance(final_state["elements"], list)
        assert isinstance(final_state["pages"], list)
        assert isinstance(final_state["validation_warnings"], list)
        assert isinstance(final_state["total_elements"], int)
        assert isinstance(final_state["element_types"], dict)


@pytest.mark.integration
@pytest.mark.slow
class TestDiscoveryAgentV2Performance:
    """Performance tests for Discovery Agent V2"""

    @pytest.fixture(autouse=True)
    def setup_tools(self):
        """Register all required tools"""
        ToolRegistry.clear()
        ToolRegistry.register(InputSanitizerTool)
        ToolRegistry.register(WebDiscoveryTool)
        yield
        ToolRegistry.clear()

    @patch('tools.discovery.web_discovery.get_adapter')
    def test_discovery_completes_in_reasonable_time(
        self, mock_get_adapter, sample_web_app_profile
    ):
        """Test that discovery completes in reasonable time"""
        import time

        mock_adapter = Mock()
        mock_adapter.discover_elements.return_value = DiscoveryResult(
            elements=[Element(id=f"el{i}", type="button", name=f"Button {i}", selector=f"#btn{i}")
                     for i in range(100)],  # Large dataset
            pages=[f"/page{i}" for i in range(50)],
        )
        mock_adapter.cleanup = Mock()
        mock_get_adapter.return_value = mock_adapter

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        start = time.time()
        final_state = agent.discover()
        elapsed = time.time() - start

        # Should complete quickly even with large dataset
        assert elapsed < 5.0  # 5 seconds max
        assert final_state["status"] == "completed"
        assert len(final_state["elements"]) == 100


@pytest.mark.integration
class TestDiscoveryAgentV2Comparison:
    """Comparison tests between V1 and V2 agents"""

    def test_v2_uses_reusable_tools(self, sample_web_app_profile):
        """Test that V2 uses reusable tools instead of embedded logic"""
        # Register tools
        ToolRegistry.register(InputSanitizerTool)
        ToolRegistry.register(WebDiscoveryTool)

        # Create agent
        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        # Verify tools can be accessed independently
        sanitizer = ToolRegistry.get("input_sanitizer")
        web_tool = ToolRegistry.get("web_discovery", config={
            "app_profile": sample_web_app_profile
        })

        assert sanitizer is not None
        assert web_tool is not None

        # Tools should be reusable outside the agent
        result = sanitizer.execute(text="test input")
        assert result.is_success()

    def test_v2_has_better_error_handling(self, sample_web_app_profile):
        """Test that V2 has improved error handling"""
        # Don't register tools to cause an error
        ToolRegistry.clear()

        agent = DiscoveryAgentV2(app_profile=sample_web_app_profile)

        # Should handle missing tools gracefully
        final_state = agent.discover()

        assert final_state["status"] == "failed"
        assert final_state["error"] is not None
