"""
Pytest Configuration and Fixtures

Shared fixtures and configuration for all tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
from typing import Dict, Any

from models.app_profile import ApplicationProfile, ApplicationType, TestFramework, AuthConfig, DiscoveryConfig
from tools.base import ToolRegistry


@pytest.fixture(autouse=True)
def reset_tool_registry():
    """Reset tool registry before each test"""
    ToolRegistry.clear()
    yield
    ToolRegistry.clear()


@pytest.fixture
def sample_web_app_profile() -> ApplicationProfile:
    """Create a sample web application profile for testing"""
    return ApplicationProfile(
        name="test_web_app",
        app_type=ApplicationType.WEB,
        adapter="web_adapter",
        base_url="https://example.com",
        description="Test web application",
        test_framework=TestFramework.PLAYWRIGHT,
        headless=True,
        auth=AuthConfig(
            auth_type="basic",
            username="testuser",
            password="testpass",
        ),
        discovery=DiscoveryConfig(
            enabled=True,
            max_depth=2,
            max_pages=10,
        ),
    )


@pytest.fixture
def sample_api_app_profile() -> ApplicationProfile:
    """Create a sample API application profile for testing"""
    return ApplicationProfile(
        name="test_api",
        app_type=ApplicationType.API,
        adapter="api_adapter",
        base_url="https://api.example.com",
        description="Test REST API",
        test_framework=TestFramework.PYTEST,
        auth=AuthConfig(
            auth_type="bearer",
            token="test_bearer_token",
        ),
        discovery=DiscoveryConfig(
            enabled=True,
            url="https://api.example.com/openapi.json",
        ),
    )


@pytest.fixture
def mock_playwright_page():
    """Create a mock Playwright page object"""
    page = MagicMock()
    page.goto = Mock()
    page.query_selector = Mock(return_value=None)
    page.query_selector_all = Mock(return_value=[])
    page.wait_for_load_state = Mock()
    page.set_default_timeout = Mock()
    page.url = "https://example.com"
    page.title = Mock(return_value="Test Page")
    return page


@pytest.fixture
def mock_playwright_browser():
    """Create a mock Playwright browser object"""
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    context.new_page = Mock(return_value=page)
    browser.new_context = Mock(return_value=context)

    return browser


@pytest.fixture
def mock_web_adapter(sample_web_app_profile, mock_playwright_page):
    """Create a mock web adapter"""
    adapter = Mock()
    adapter.app_profile = sample_web_app_profile
    adapter.page = mock_playwright_page
    adapter.discover_elements = Mock()
    adapter.cleanup = Mock()
    return adapter


@pytest.fixture
def mock_api_adapter(sample_api_app_profile):
    """Create a mock API adapter"""
    adapter = Mock()
    adapter.app_profile = sample_api_app_profile
    adapter.discover_elements = Mock()
    adapter.cleanup = Mock()
    return adapter


@pytest.fixture
def sample_discovery_result() -> Dict[str, Any]:
    """Create a sample discovery result"""
    return {
        "elements": [
            {
                "id": "login_button",
                "type": "button",
                "name": "Login",
                "selector": "#login-btn",
                "page_url": "/login",
                "attributes": {"class": "btn btn-primary"}
            },
            {
                "id": "username_input",
                "type": "input",
                "name": "Username",
                "selector": "#username",
                "page_url": "/login",
                "attributes": {"type": "text", "required": True}
            },
        ],
        "pages": [
            "/",
            "/login",
            "/dashboard",
        ],
        "apis": [],
        "metadata": {
            "crawl_time": 5.2,
            "pages_crawled": 3,
        }
    }


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for test files"""
    test_dir = tmp_path / "test_output"
    test_dir.mkdir()
    return test_dir


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration hook"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )
