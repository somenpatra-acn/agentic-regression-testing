"""Application settings and configuration management."""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    openai_api_key: Optional[str] = Field(None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, validation_alias="ANTHROPIC_API_KEY")
    llm_provider: str = Field(default="openai", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4-turbo-preview", validation_alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.1, validation_alias="LLM_TEMPERATURE")

    # Vector Store
    vector_store: str = Field(default="faiss", validation_alias="VECTOR_STORE")
    embedding_model: str = Field(default="text-embedding-3-small", validation_alias="EMBEDDING_MODEL")

    # Oracle EBS
    oracle_connection_string: Optional[str] = Field(None, validation_alias="ORACLE_CONNECTION_STRING")
    oracle_modules: List[str] = Field(default_factory=list)

    # Application Under Test
    app_url: Optional[str] = Field(None, validation_alias="APP_URL")
    app_auth_type: str = Field(default="basic", validation_alias="APP_AUTH_TYPE")
    app_username: Optional[str] = Field(None, validation_alias="APP_USERNAME")
    app_password: Optional[str] = Field(None, validation_alias="APP_PASSWORD")

    # CI/CD Integration
    azure_devops_org: Optional[str] = Field(None, validation_alias="AZURE_DEVOPS_ORG")
    azure_devops_project: Optional[str] = Field(None, validation_alias="AZURE_DEVOPS_PROJECT")
    azure_devops_pat: Optional[str] = Field(None, validation_alias="AZURE_DEVOPS_PAT")
    github_token: Optional[str] = Field(None, validation_alias="GITHUB_TOKEN")
    github_repo: Optional[str] = Field(None, validation_alias="GITHUB_REPO")

    # HITL Configuration
    hitl_mode: str = Field(default="APPROVE_PLAN", validation_alias="HITL_MODE")
    approval_timeout: int = Field(default=3600, validation_alias="APPROVAL_TIMEOUT")
    enable_web_interface: bool = Field(default=False, validation_alias="ENABLE_WEB_INTERFACE")

    # Test Execution
    test_framework: str = Field(default="playwright", validation_alias="TEST_FRAMEWORK")
    parallel_execution: bool = Field(default=True, validation_alias="PARALLEL_EXECUTION")
    max_workers: int = Field(default=4, validation_alias="MAX_WORKERS")
    headless_mode: bool = Field(default=True, validation_alias="HEADLESS_MODE")
    screenshot_on_failure: bool = Field(default=True, validation_alias="SCREENSHOT_ON_FAILURE")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_file: str = Field(default="logs/regression_suite.log", validation_alias="LOG_FILE")

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path.cwd())
    knowledge_base_dir: Path = Field(default_factory=lambda: Path.cwd() / "knowledge_base")
    tests_dir: Path = Field(default_factory=lambda: Path.cwd() / "tests" / "generated")
    logs_dir: Path = Field(default_factory=lambda: Path.cwd() / "logs")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse oracle_modules if provided as string
        if isinstance(self.oracle_modules, str):
            self.oracle_modules = [m.strip() for m in self.oracle_modules.split(",") if m.strip()]

        # Ensure directories exist
        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.knowledge_base_dir / "test_data").mkdir(parents=True, exist_ok=True)
        (self.knowledge_base_dir / "vector_store").mkdir(parents=True, exist_ok=True)

    def get_llm_api_key(self) -> Optional[str]:
        """Get the appropriate API key based on LLM provider."""
        if self.llm_provider == "openai":
            return self.openai_api_key
        elif self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return None

    def is_hitl_enabled(self) -> bool:
        """Check if any HITL mode is enabled."""
        return self.hitl_mode != "FULL_AUTO"

    def requires_plan_approval(self) -> bool:
        """Check if test plan approval is required."""
        return self.hitl_mode in ["APPROVE_PLAN", "APPROVE_ALL", "INTERACTIVE"]

    def requires_test_approval(self) -> bool:
        """Check if test script approval is required."""
        return self.hitl_mode in ["APPROVE_TESTS", "APPROVE_ALL", "INTERACTIVE"]

    def requires_execution_approval(self) -> bool:
        """Check if execution approval is required."""
        return self.hitl_mode in ["APPROVE_ALL", "INTERACTIVE"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
