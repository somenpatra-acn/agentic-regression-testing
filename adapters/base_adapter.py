"""Base adapter interface for application testing."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from models.test_case import TestCase
from models.test_result import TestResult


class Element(BaseModel):
    """Discovered UI element or API endpoint."""
    id: str = Field(..., description="Element identifier")
    type: str = Field(..., description="Element type (button, input, api, etc.)")
    name: str = Field(..., description="Element name")
    selector: Optional[str] = Field(None, description="CSS selector or XPath")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Element attributes")
    parent: Optional[str] = Field(None, description="Parent element ID")
    page_url: Optional[str] = Field(None, description="Page URL where element found")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "login_button",
                "type": "button",
                "name": "Login",
                "selector": "#login-btn",
                "page_url": "/login"
            }
        }


class DiscoveryResult(BaseModel):
    """Result of application discovery."""
    elements: List[Element] = Field(default_factory=list, description="Discovered elements")
    pages: List[str] = Field(default_factory=list, description="Discovered pages")
    apis: List[Dict[str, Any]] = Field(default_factory=list, description="Discovered APIs")
    schema: Optional[Dict[str, Any]] = Field(None, description="Database schema")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class BaseApplicationAdapter(ABC):
    """Base adapter interface for application testing."""

    def __init__(self, app_profile):
        """
        Initialize adapter.

        Args:
            app_profile: Application profile configuration
        """
        self.app_profile = app_profile
        self.name = app_profile.name

    @abstractmethod
    def discover_elements(self) -> DiscoveryResult:
        """
        Discover UI elements, APIs, or database schema.

        Returns:
            Discovery results
        """
        pass

    @abstractmethod
    def execute_test(self, test_case: TestCase) -> TestResult:
        """
        Execute a test case on the target application.

        Args:
            test_case: Test case to execute

        Returns:
            Test execution result
        """
        pass

    @abstractmethod
    def validate_state(self) -> bool:
        """
        Validate application is in a testable state.

        Returns:
            True if application is ready for testing
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources (close browsers, connections, etc.)."""
        pass

    def authenticate(self) -> bool:
        """
        Authenticate with the application.

        Returns:
            True if authentication successful
        """
        # Default implementation - can be overridden
        return True

    def take_screenshot(self, filename: str) -> Optional[str]:
        """
        Take screenshot (for UI testing).

        Args:
            filename: Screenshot filename

        Returns:
            Path to screenshot file
        """
        # Default implementation - can be overridden
        return None

    def get_logs(self) -> List[str]:
        """
        Get application logs.

        Returns:
            List of log entries
        """
        # Default implementation - can be overridden
        return []

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get adapter capabilities.

        Returns:
            Dictionary of capabilities
        """
        return {
            "ui_testing": False,
            "api_testing": False,
            "database_testing": False,
            "screenshot_capture": False,
            "video_recording": False,
            "log_capture": False,
        }
