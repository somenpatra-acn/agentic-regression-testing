"""
Path Validator Tool

Validates file paths to prevent path traversal and other file system attacks.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class PathValidatorTool(BaseTool):
    """
    Validates file paths to prevent security vulnerabilities

    Features:
    - Path traversal detection (../, ..\)
    - Absolute path validation
    - Allowed directory whitelist
    - Forbidden path patterns
    - Symlink detection
    - File extension validation
    """

    # Dangerous path patterns
    TRAVERSAL_PATTERNS = [
        r"\.\./",      # Unix path traversal
        r"\.\.",       # Path traversal
        r"\.\.\\",     # Windows path traversal
        r"%2e%2e",     # URL encoded ..
        r"%252e",      # Double URL encoded .
    ]

    FORBIDDEN_PATTERNS = [
        r"^/etc/",           # System config (Unix)
        r"^/root/",          # Root home (Unix)
        r"^/proc/",          # Process info (Unix)
        r"^/sys/",           # System info (Unix)
        r"^C:[/\\]Windows",  # Windows system (forward or back slash)
        r"^C:[/\\]Program Files",  # Windows programs (forward or back slash)
        r"[/\\]\.env$",      # Environment files (/.env or \.env at end)
        r"[/\\]\.ssh[/\\]",  # SSH keys directory
        r"[/\\]\.aws[/\\]",  # AWS credentials directory
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.allowed_dirs = self.config.get("allowed_dirs", [])
        self.allowed_extensions = self.config.get("allowed_extensions", [])
        self.base_dir = self.config.get("base_dir", None)
        self.allow_symlinks = self.config.get("allow_symlinks", False)
        self.strict_mode = self.config.get("strict_mode", True)

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="path_validator",
            description="Validates file paths to prevent path traversal and security issues",
            version="1.0.0",
            tags=["security", "validation", "filesystem"],
            is_safe=True,
            input_schema={
                "path": "string - Path to validate",
                "must_exist": "boolean - Whether path must exist",
                "check_traversal": "boolean - Check for path traversal attempts",
                "check_forbidden": "boolean - Check against forbidden patterns",
            }
        )

    def execute(
        self,
        path: str,
        must_exist: bool = False,
        check_traversal: bool = True,
        check_forbidden: bool = True,
        check_extension: bool = False,
    ) -> ToolResult:
        """
        Validate a file path

        Args:
            path: Path to validate
            must_exist: Whether the path must exist
            check_traversal: Check for path traversal attempts
            check_forbidden: Check against forbidden patterns
            check_extension: Check if extension is in allowed list

        Returns:
            ToolResult with validation status and normalized path
        """
        return self._wrap_execution(
            self._validate,
            path=path,
            must_exist=must_exist,
            check_traversal=check_traversal,
            check_forbidden=check_forbidden,
            check_extension=check_extension,
        )

    def _validate(
        self,
        path: str,
        must_exist: bool,
        check_traversal: bool,
        check_forbidden: bool,
        check_extension: bool,
    ) -> ToolResult:
        """Internal validation logic"""

        if not path:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="Path cannot be empty",
            )

        warnings = []
        original_path = path

        try:
            # Convert to Path object for safer manipulation
            path_obj = Path(path)

            # Check for path traversal (on original input)
            if check_traversal:
                for pattern in self.TRAVERSAL_PATTERNS:
                    if re.search(pattern, path, re.IGNORECASE):
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error=f"Path traversal detected: pattern '{pattern}' found in path",
                            metadata={"pattern": pattern, "original_path": original_path}
                        )

            # Check for symlinks BEFORE resolving (since resolve() follows symlinks)
            if self.base_dir:
                base = Path(self.base_dir)
                unresolved_path = base / path_obj
            else:
                unresolved_path = path_obj

            is_symlink = unresolved_path.exists() and unresolved_path.is_symlink()
            if is_symlink and not self.allow_symlinks:
                warnings.append("Path is a symlink")
                if self.strict_mode:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Symlinks are not allowed in strict mode",
                        metadata={"original_path": original_path}
                    )

            # Resolve to absolute path
            try:
                abs_path = unresolved_path.resolve()
            except (OSError, RuntimeError) as e:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"Failed to resolve path: {str(e)}",
                    metadata={"original_path": original_path}
                )

            # Check forbidden patterns (check both original and resolved paths)
            if check_forbidden:
                # Check original path (to catch Unix paths like /etc/passwd even on Windows)
                normalized_original = original_path.replace("\\", "/")
                for pattern in self.FORBIDDEN_PATTERNS:
                    if re.search(pattern, normalized_original, re.IGNORECASE):
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error=f"Forbidden path pattern detected: '{pattern}'",
                            metadata={"pattern": pattern, "original_path": original_path}
                        )

                # Check resolved path (to catch .env and relative paths after resolution)
                normalized_resolved = str(abs_path).replace("\\", "/")
                for pattern in self.FORBIDDEN_PATTERNS:
                    if re.search(pattern, normalized_resolved, re.IGNORECASE):
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error=f"Forbidden path pattern detected: '{pattern}'",
                            metadata={"pattern": pattern, "original_path": original_path, "resolved_path": str(abs_path)}
                        )

            # Check if path is within allowed directories
            if self.allowed_dirs:
                is_allowed = False
                for allowed_dir in self.allowed_dirs:
                    allowed_path = Path(allowed_dir).resolve()
                    try:
                        abs_path.relative_to(allowed_path)
                        is_allowed = True
                        break
                    except ValueError:
                        continue

                if not is_allowed:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"Path is outside allowed directories: {self.allowed_dirs}",
                        metadata={
                            "original_path": original_path,
                            "resolved_path": str(abs_path),
                            "allowed_dirs": self.allowed_dirs
                        }
                    )

            # Check if path must exist
            if must_exist and not abs_path.exists():
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"Path does not exist: {abs_path}",
                    metadata={"original_path": original_path, "resolved_path": str(abs_path)}
                )

            # Check file extension
            if check_extension and self.allowed_extensions:
                extension = abs_path.suffix.lower()
                if extension not in self.allowed_extensions:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"File extension '{extension}' not in allowed list: {self.allowed_extensions}",
                        metadata={
                            "original_path": original_path,
                            "resolved_path": str(abs_path),
                            "extension": extension
                        }
                    )

            # All checks passed
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=str(abs_path),
                metadata={
                    "original_path": original_path,
                    "resolved_path": str(abs_path),
                    "is_absolute": abs_path.is_absolute(),
                    "exists": abs_path.exists(),
                    "is_file": abs_path.is_file() if abs_path.exists() else None,
                    "is_dir": abs_path.is_dir() if abs_path.exists() else None,
                    "warnings": warnings,
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Unexpected error during path validation: {str(e)}",
                metadata={"original_path": original_path}
            )

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing dangerous characters

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path traversal patterns first
        filename = filename.replace("..", "_")

        # Remove path separators
        filename = filename.replace("/", "_").replace("\\", "_")

        # Remove other dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\x00"]
        for char in dangerous_chars:
            filename = filename.replace(char, "_")

        # Remove leading/trailing dots and spaces
        filename = filename.strip(". ")

        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext

        return filename
