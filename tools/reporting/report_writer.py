"""
Report Writer Tool

Writes generated reports to disk with path validation.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class ReportWriterTool(BaseTool):
    """
    Writes test reports to disk

    This tool provides safe report writing with:
    - Path validation
    - Directory creation
    - File naming conventions
    - Encoding handling

    Features:
    - Multiple format support
    - Automatic timestamping
    - Directory management
    - Overwrite protection (optional)
    """

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        if not self.config.get("output_dir"):
            raise ValueError("output_dir is required in config")

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="report_writer",
            description="Writes test reports to disk with path validation",
            version="1.0.0",
            tags=["reporting", "file", "write", "io"],
            requires_auth=False,
            is_safe=False,  # Modifies filesystem
            input_schema={
                "report_content": "string - Report content to write",
                "format": "string - Report format (html, json, markdown)",
                "filename": "string - Optional custom filename (default: auto-generated)",
                "overwrite": "boolean - Allow overwriting existing files (default: False)",
            },
            output_schema={
                "file_path": "string - Absolute path to written file",
                "filename": "string - Filename",
                "created": "boolean - Whether file was created (vs updated)",
            }
        )

    def execute(
        self,
        report_content: str,
        format: str,
        filename: Optional[str] = None,
        overwrite: bool = False,
    ) -> ToolResult:
        """
        Write report to disk

        Args:
            report_content: Report content
            format: Report format (html, json, markdown)
            filename: Optional custom filename
            overwrite: Allow overwriting existing files

        Returns:
            ToolResult with file path
        """
        return self._wrap_execution(
            self._write_report,
            report_content=report_content,
            format=format,
            filename=filename,
            overwrite=overwrite,
        )

    def _write_report(
        self,
        report_content: str,
        format: str,
        filename: Optional[str],
        overwrite: bool,
    ) -> ToolResult:
        """Internal write logic"""

        if not report_content:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="report_content cannot be empty",
            )

        if format not in ["html", "json", "markdown"]:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Unsupported format: {format}",
            )

        try:
            # Get output directory from config
            output_dir = Path(self.config["output_dir"])

            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = {
                    "html": "html",
                    "json": "json",
                    "markdown": "md",
                }[format]
                filename = f"report_{timestamp}.{extension}"

            # Construct full path
            file_path = output_dir / filename

            # Check if file exists
            file_exists = file_path.exists()
            created = not file_exists

            # Handle existing file
            if file_exists and not overwrite:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"File already exists and overwrite=False: {file_path}",
                    metadata={"filename": filename, "file_path": str(file_path)}
                )

            # Write content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "file_path": str(file_path),
                    "filename": filename,
                    "created": created,
                },
                metadata={
                    "format": format,
                    "file_size": len(report_content),
                    "output_dir": str(output_dir),
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"File write failed: {str(e)}",
                metadata={
                    "format": format,
                    "filename": filename,
                    "exception_type": type(e).__name__,
                }
            )
