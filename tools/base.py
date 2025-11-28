"""
Base Tool Interface

All tools must inherit from BaseTool and implement the execute() method.
This ensures consistency and enables tool composition.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import time
from datetime import datetime


class ToolStatus(str, Enum):
    """Tool execution status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"  # Some operations succeeded, some failed
    ERROR = "error"  # Unexpected error


class ToolResult(BaseModel):
    """
    Standardized tool execution result

    All tools return this consistent format for easy parsing and error handling.
    """
    status: ToolStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True

    def is_success(self) -> bool:
        """Check if tool execution was successful"""
        return self.status == ToolStatus.SUCCESS

    def is_failure(self) -> bool:
        """Check if tool execution failed"""
        return self.status in [ToolStatus.FAILURE, ToolStatus.ERROR]


class ToolMetadata(BaseModel):
    """Tool metadata for registration and documentation"""
    name: str
    description: str
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    requires_auth: bool = False
    is_safe: bool = True  # False if tool can modify state or execute code
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    """
    Abstract base class for all tools

    All tools must:
    1. Inherit from this class
    2. Implement execute() method
    3. Define metadata property
    4. Handle errors gracefully

    Tools should be:
    - Stateless (or manage state explicitly)
    - Idempotent when possible
    - Fast and efficient
    - Well-documented
    - Thoroughly tested
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize tool with optional configuration

        Args:
            config: Tool-specific configuration dictionary
        """
        self.config = config or {}
        self._validate_config()

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return tool metadata for registration"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool's main functionality

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Standardized result object
        """
        pass

    def _validate_config(self) -> None:
        """
        Validate tool configuration

        Override this method to add custom validation logic.
        Raise ValueError if configuration is invalid.
        """
        pass

    def _wrap_execution(self, func, **kwargs) -> ToolResult:
        """
        Wrapper to measure execution time and handle errors

        Args:
            func: Function to execute
            **kwargs: Function arguments

        Returns:
            ToolResult with timing and error handling
        """
        start_time = time.time()

        try:
            result = func(**kwargs)
            execution_time = time.time() - start_time

            # If function returns ToolResult, update execution time and merge metadata
            if isinstance(result, ToolResult):
                result.execution_time = execution_time
                # Merge tool name into metadata if not already present
                if "tool" not in result.metadata:
                    result.metadata["tool"] = self.metadata.name
                return result

            # If function returns data directly, wrap in ToolResult
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                execution_time=execution_time,
                metadata={"tool": self.metadata.name}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "tool": self.metadata.name,
                    "exception_type": type(e).__name__
                }
            )

    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters

        Override this method to add custom input validation.

        Args:
            **kwargs: Input parameters to validate

        Returns:
            bool: True if valid, raises ValueError if invalid
        """
        return True

    def __str__(self) -> str:
        return f"{self.metadata.name} v{self.metadata.version}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.metadata.name}', version='{self.metadata.version}')>"


class ToolRegistry:
    """
    Central registry for all tools

    Provides:
    - Tool registration and discovery
    - Version management
    - Tool metadata access
    - Tool instantiation
    """

    _tools: Dict[str, type] = {}
    _instances: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool_class: type) -> None:
        """
        Register a tool class

        Args:
            tool_class: Tool class to register (must inherit from BaseTool)
        """
        if not issubclass(tool_class, BaseTool):
            raise ValueError(f"{tool_class.__name__} must inherit from BaseTool")

        # Create temporary instance to get metadata
        # Try without config first, then with minimal dummy config if needed
        try:
            temp_instance = tool_class()
        except (ValueError, TypeError):
            # Tool requires config, use minimal dummy config for registration
            # Import ApplicationProfile here to avoid circular imports
            from models.app_profile import ApplicationProfile, ApplicationType, TestFramework

            dummy_app_profile = ApplicationProfile(
                name="dummy",
                app_type=ApplicationType.WEB,
                adapter="web",
                test_framework=TestFramework.PLAYWRIGHT,
            )

            dummy_config = {
                "output_dir": ".",  # For tools that need output_dir
                "knowledge_base_dir": ".",  # For tools that need knowledge_base_dir
                "app_profile": dummy_app_profile,  # For tools that need app_profile
                "required_param": "dummy_value",  # For tools with custom required params
            }
            try:
                temp_instance = tool_class(config=dummy_config)
            except Exception as e:
                raise ValueError(
                    f"Could not register {tool_class.__name__}: {e}. "
                    "Tool may require specific configuration."
                )

        tool_name = temp_instance.metadata.name

        if tool_name in cls._tools:
            try:
                existing_instance = cls._tools[tool_name]()
            except:
                existing_instance = cls._tools[tool_name](config=dummy_config)
            existing_version = existing_instance.metadata.version
            new_version = temp_instance.metadata.version
            print(f"Warning: Overwriting tool '{tool_name}' (v{existing_version} -> v{new_version})")

        cls._tools[tool_name] = tool_class

    @classmethod
    def get(cls, tool_name: str, config: Optional[Dict[str, Any]] = None) -> BaseTool:
        """
        Get tool instance by name

        Args:
            tool_name: Name of the tool
            config: Optional configuration for tool instantiation

        Returns:
            BaseTool: Tool instance
        """
        if tool_name not in cls._tools:
            available_tools = ", ".join(cls._tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )

        # Create new instance with config
        tool_class = cls._tools[tool_name]
        return tool_class(config=config)

    @classmethod
    def get_metadata(cls, tool_name: str) -> ToolMetadata:
        """Get tool metadata without instantiating"""
        if tool_name not in cls._tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        temp_instance = cls._tools[tool_name]()
        return temp_instance.metadata

    @classmethod
    def list_tools(cls, tags: Optional[List[str]] = None) -> List[ToolMetadata]:
        """
        List all registered tools

        Args:
            tags: Optional filter by tags

        Returns:
            List of tool metadata
        """
        tools = []

        # Import ApplicationProfile here to avoid circular imports
        from models.app_profile import ApplicationProfile, ApplicationType, TestFramework

        dummy_app_profile = ApplicationProfile(
            name="dummy",
            app_type=ApplicationType.WEB,
            adapter="web",
            test_framework=TestFramework.PLAYWRIGHT,
        )

        dummy_config = {
            "output_dir": ".",
            "knowledge_base_dir": ".",
            "app_profile": dummy_app_profile,
            "required_param": "dummy_value",  # For tools with custom required params
        }

        for tool_class in cls._tools.values():
            # Try to instantiate with and without config
            try:
                temp_instance = tool_class()
            except (ValueError, TypeError):
                try:
                    temp_instance = tool_class(config=dummy_config)
                except:
                    continue  # Skip tools that can't be instantiated

            metadata = temp_instance.metadata

            # Filter by tags if provided
            if tags:
                if any(tag in metadata.tags for tag in tags):
                    tools.append(metadata)
            else:
                tools.append(metadata)

        return tools

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (mainly for testing)"""
        cls._tools.clear()
        cls._instances.clear()
