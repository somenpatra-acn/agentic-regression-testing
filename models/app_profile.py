"""Application profile data models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class AuthType(str, Enum):
    """Authentication types."""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    CUSTOM = "custom"


class ApplicationType(str, Enum):
    """Application types."""
    WEB = "web"
    API = "api"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    DATABASE = "database"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class TestFramework(str, Enum):
    """Supported test frameworks."""
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    PYTEST = "pytest"
    ROBOT = "robot"
    CUSTOM = "custom"


class AuthConfig(BaseModel):
    """Authentication configuration."""
    auth_type: AuthType = Field(default=AuthType.NONE, description="Authentication type")
    credentials_env: Optional[str] = Field(None, description="Environment variable for credentials")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")
    token: Optional[str] = Field(None, description="API token")
    api_key: Optional[str] = Field(None, description="API key")
    oauth_config: Optional[Dict[str, str]] = Field(None, description="OAuth configuration")
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")

    class Config:
        json_schema_extra = {
            "example": {
                "auth_type": "oauth2",
                "credentials_env": "APP_OAUTH_CREDS",
                "oauth_config": {
                    "client_id": "client123",
                    "auth_url": "https://auth.example.com/oauth/token"
                }
            }
        }


class DiscoveryConfig(BaseModel):
    """Discovery configuration."""
    enabled: bool = Field(default=True, description="Enable discovery")
    url: Optional[str] = Field(None, description="Application URL")
    openapi_spec: Optional[str] = Field(None, description="OpenAPI spec URL")
    connection_string: Optional[str] = Field(None, description="Database connection string")

    # Discovery scope
    discover_elements: List[str] = Field(
        default_factory=lambda: ["buttons", "forms", "links", "inputs"],
        description="UI elements to discover"
    )
    discover_apis: bool = Field(default=True, description="Discover API endpoints")
    discover_schema: bool = Field(default=False, description="Discover database schema")

    # Discovery limits
    max_depth: int = Field(default=3, description="Maximum crawl depth")
    max_pages: int = Field(default=50, description="Maximum pages to crawl")
    timeout_seconds: int = Field(default=300, description="Discovery timeout")

    # Filters
    include_patterns: List[str] = Field(default_factory=list, description="URL patterns to include")
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["/logout", "/admin"],
        description="URL patterns to exclude"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "url": "https://app.example.com",
                "discover_elements": ["buttons", "forms"],
                "max_depth": 3
            }
        }


class ApplicationProfile(BaseModel):
    """Complete application profile."""
    name: str = Field(..., description="Application name")
    app_type: ApplicationType = Field(..., description="Application type")
    adapter: str = Field(..., description="Adapter to use")

    # Connection
    base_url: Optional[str] = Field(None, description="Base URL")
    auth: AuthConfig = Field(default_factory=AuthConfig, description="Authentication config")

    # Discovery
    discovery: DiscoveryConfig = Field(
        default_factory=DiscoveryConfig,
        description="Discovery configuration"
    )

    # Testing
    test_framework: TestFramework = Field(
        default=TestFramework.PLAYWRIGHT,
        description="Test framework"
    )
    parallel_execution: bool = Field(default=True, description="Enable parallel execution")
    max_workers: int = Field(default=4, description="Maximum parallel workers")
    headless: bool = Field(default=True, description="Headless browser mode")

    # Application-specific settings
    modules: List[str] = Field(default_factory=list, description="Application modules")
    features: List[str] = Field(default_factory=list, description="Features to test")
    custom_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom configuration"
    )

    # Metadata
    description: Optional[str] = Field(None, description="Application description")
    version: Optional[str] = Field(None, description="Application version")
    tags: List[str] = Field(default_factory=list, description="Tags")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "web_portal",
                "app_type": "web",
                "adapter": "web_adapter",
                "base_url": "https://portal.example.com",
                "auth": {
                    "auth_type": "basic",
                    "username": "test_user",
                    "password": "test_pass"
                },
                "test_framework": "playwright",
                "modules": ["authentication", "dashboard"]
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = dict(self.auth.custom_headers)

        if self.auth.auth_type == AuthType.BEARER and self.auth.token:
            headers["Authorization"] = f"Bearer {self.auth.token}"
        elif self.auth.auth_type == AuthType.API_KEY and self.auth.api_key:
            headers["X-API-Key"] = self.auth.api_key

        return headers

    def is_web_app(self) -> bool:
        """Check if this is a web application."""
        return self.app_type in [ApplicationType.WEB, ApplicationType.ENTERPRISE]

    def is_api(self) -> bool:
        """Check if this is an API."""
        return self.app_type == ApplicationType.API

    def supports_ui_testing(self) -> bool:
        """Check if UI testing is supported."""
        return self.app_type in [
            ApplicationType.WEB,
            ApplicationType.DESKTOP,
            ApplicationType.MOBILE,
            ApplicationType.ENTERPRISE
        ]
