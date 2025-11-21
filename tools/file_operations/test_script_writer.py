"""
Test Script Writer Tool

Safely writes generated test scripts to disk with path validation and security checks.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class TestScriptWriterTool(BaseTool):
    """
    Safely writes test scripts to disk

    This tool provides secure file writing with:
    - Path validation (uses PathValidatorTool internally)
    - Directory creation
    - File overwrite protection (optional)
    - Encoding handling
    - Atomic writes (write to temp then rename)

    Features:
    - Security checks
    - Backup creation (optional)
    - File permissions setting
    - Content validation
    """

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # output_dir is required
        if not self.config.get("output_dir"):
            raise ValueError("output_dir is required in config")

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="test_script_writer",
            description="Safely writes generated test scripts to disk with validation",
            version="1.0.0",
            tags=["file", "write", "scripts", "io"],
            requires_auth=False,
            is_safe=False,  # Modifies filesystem
            input_schema={
                "filename": "string - Name of the file to write",
                "content": "string - Script content to write",
                "overwrite": "boolean - Allow overwriting existing files (default: False)",
                "create_backup": "boolean - Create backup of existing file (default: True)",
            },
            output_schema={
                "file_path": "string - Absolute path to written file",
                "created": "boolean - Whether file was created (vs updated)",
                "backup_path": "string - Path to backup file (if created)",
            }
        )

    def execute(
        self,
        filename: str,
        content: str,
        overwrite: bool = False,
        create_backup: bool = True,
    ) -> ToolResult:
        """
        Write test script to disk

        Args:
            filename: Name of the file to write
            content: Script content
            overwrite: Allow overwriting existing files
            create_backup: Create backup of existing file

        Returns:
            ToolResult with file path and status
        """
        return self._wrap_execution(
            self._write,
            filename=filename,
            content=content,
            overwrite=overwrite,
            create_backup=create_backup,
        )

    def _write(
        self,
        filename: str,
        content: str,
        overwrite: bool,
        create_backup: bool,
    ) -> ToolResult:
        """Internal write logic"""

        if not filename or not filename.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="filename cannot be empty",
            )

        if not content:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="content cannot be empty",
            )

        try:
            # Get output directory from config
            output_dir = Path(self.config["output_dir"])

            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)

            # Validate path using PathValidatorTool
            from tools import get_tool

            path_validator = get_tool("path_validator", config={
                "allowed_dirs": [str(output_dir)],
                "strict_mode": True,
                "allow_symlinks": False,
            })

            # Construct full path
            file_path = output_dir / filename

            # Validate the path
            validation_result = path_validator.execute(
                path=str(file_path),
                must_exist=False,
                check_traversal=True,
                check_forbidden=True,
            )

            if validation_result.is_failure():
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"Path validation failed: {validation_result.error}",
                    metadata={"filename": filename}
                )

            # Check if file exists
            file_exists = file_path.exists()
            created = not file_exists
            backup_path = None

            # Handle existing file
            if file_exists:
                if not overwrite:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"File already exists and overwrite=False: {file_path}",
                        metadata={"filename": filename, "file_path": str(file_path)}
                    )

                # Create backup if requested
                if create_backup:
                    backup_path = self._create_backup(file_path)

            # Write content to file
            # Use atomic write (write to temp file then rename)
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')

            try:
                # Write to temp file
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Atomic rename
                temp_path.replace(file_path)

            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise e

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "file_path": str(file_path),
                    "created": created,
                    "backup_path": backup_path,
                },
                metadata={
                    "filename": filename,
                    "file_size": len(content),
                    "output_dir": str(output_dir),
                    "overwrite": overwrite,
                    "had_backup": backup_path is not None,
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"File write failed: {str(e)}",
                metadata={
                    "filename": filename,
                    "exception_type": type(e).__name__,
                }
            )

    def _create_backup(self, file_path: Path) -> str:
        """Create a backup of an existing file"""
        import shutil
        from datetime import datetime

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".{timestamp}{file_path.suffix}.bak")

        # Copy file to backup
        shutil.copy2(file_path, backup_path)

        return str(backup_path)
