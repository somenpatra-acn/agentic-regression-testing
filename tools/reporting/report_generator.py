"""
Report Generator Tool

Generates test execution reports in multiple formats.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata


class ReportGeneratorTool(BaseTool):
    """
    Generates test execution reports

    This tool provides report generation for:
    - HTML reports with styling
    - JSON reports for programmatic access
    - Markdown reports for documentation
    - Statistics calculation

    Features:
    - Multiple format support
    - Customizable styling
    - Statistics aggregation
    - Pass/fail visualization
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="report_generator",
            description="Generates test execution reports in multiple formats",
            version="1.0.0",
            tags=["reporting", "html", "json", "markdown"],
            requires_auth=False,
            is_safe=True,  # Only generates reports
            input_schema={
                "test_results": "list - List of test result dictionaries",
                "app_name": "string - Application name",
                "format": "string - Report format (html, json, markdown)",
                "include_stats": "boolean - Include statistics (default: True)",
            },
            output_schema={
                "report_content": "string - Generated report content",
                "statistics": "dict - Test statistics",
                "format": "string - Report format",
            }
        )

    def execute(
        self,
        test_results: List[Dict[str, Any]],
        app_name: str,
        format: str = "html",
        include_stats: bool = True,
    ) -> ToolResult:
        """
        Generate a test report

        Args:
            test_results: List of test result dictionaries
            app_name: Application name
            format: Report format (html, json, markdown)
            include_stats: Include statistics in report

        Returns:
            ToolResult with generated report content
        """
        return self._wrap_execution(
            self._generate_report,
            test_results=test_results,
            app_name=app_name,
            format=format,
            include_stats=include_stats,
        )

    def _generate_report(
        self,
        test_results: List[Dict[str, Any]],
        app_name: str,
        format: str,
        include_stats: bool,
    ) -> ToolResult:
        """Internal report generation logic"""

        if not app_name or not app_name.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="app_name cannot be empty",
            )

        if format not in ["html", "json", "markdown"]:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Unsupported format: {format}. Must be html, json, or markdown",
            )

        try:
            # Calculate statistics
            statistics = self._calculate_statistics(test_results) if include_stats else {}

            # Generate report based on format
            if format == "html":
                report_content = self._generate_html(test_results, app_name, statistics)
            elif format == "json":
                report_content = self._generate_json(test_results, app_name, statistics)
            elif format == "markdown":
                report_content = self._generate_markdown(test_results, app_name, statistics)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "report_content": report_content,
                    "statistics": statistics,
                    "format": format,
                },
                metadata={
                    "app_name": app_name,
                    "test_count": len(test_results),
                    "content_length": len(report_content),
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Report generation failed: {str(e)}",
                metadata={
                    "app_name": app_name,
                    "format": format,
                    "exception_type": type(e).__name__,
                }
            )

    def _calculate_statistics(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate test statistics"""

        total = len(test_results)
        if total == 0:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "error": 0,
                "pass_rate": "0.0%",
                "total_duration": 0.0,
            }

        passed = sum(1 for r in test_results if r.get("status") == "passed")
        failed = sum(1 for r in test_results if r.get("status") == "failed")
        skipped = sum(1 for r in test_results if r.get("status") == "skipped")
        error = sum(1 for r in test_results if r.get("status") == "error")

        # Calculate total duration
        total_duration = 0.0
        for r in test_results:
            if "metrics" in r and isinstance(r["metrics"], dict):
                total_duration += r["metrics"].get("duration_seconds", 0.0)
            elif "duration_seconds" in r:
                total_duration += r.get("duration_seconds", 0.0)

        pass_rate = (passed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": error,
            "pass_rate": f"{pass_rate:.1f}%",
            "total_duration": total_duration,
        }

    def _generate_html(
        self,
        test_results: List[Dict[str, Any]],
        app_name: str,
        statistics: Dict[str, Any],
    ) -> str:
        """Generate HTML report"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {app_name}</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        .summary {{
            background-color: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            margin-top: 0;
            color: #333;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }}
        .stat-box:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .stat-box h3 {{
            margin: 0;
            font-size: 2em;
            color: #333;
        }}
        .stat-box p {{
            margin: 10px 0 0 0;
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}
        .stat-box.passed {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .stat-box.passed h3,
        .stat-box.passed p {{
            color: white;
        }}
        .stat-box.failed {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        .stat-box.failed h3,
        .stat-box.failed p {{
            color: white;
        }}
        .test-results {{
            background-color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .test-results h2 {{
            margin-top: 0;
            color: #333;
        }}
        .test-item {{
            padding: 15px;
            margin: 15px 0;
            border-left: 5px solid #ddd;
            border-radius: 5px;
            background-color: #fafafa;
            transition: all 0.2s;
        }}
        .test-item:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transform: translateX(5px);
        }}
        .test-item.passed {{
            border-left-color: #667eea;
            background-color: #f0f4ff;
        }}
        .test-item.failed {{
            border-left-color: #f5576c;
            background-color: #fff0f2;
        }}
        .test-item.skipped {{
            border-left-color: #ffa726;
            background-color: #fff8e1;
        }}
        .test-item.error {{
            border-left-color: #ef5350;
            background-color: #ffebee;
        }}
        .test-item h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 1.2em;
        }}
        .test-item p {{
            margin: 5px 0;
            color: #666;
        }}
        .test-item .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status.passed {{
            background-color: #667eea;
            color: white;
        }}
        .status.failed {{
            background-color: #f5576c;
            color: white;
        }}
        .status.skipped {{
            background-color: #ffa726;
            color: white;
        }}
        .status.error {{
            background-color: #ef5350;
            color: white;
        }}
        .error-message {{
            background-color: #fff5f5;
            border: 1px solid #fc8181;
            padding: 12px;
            border-radius: 5px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #c53030;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .duration {{
            color: #667eea;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Test Execution Report</h1>
        <p><strong>Application:</strong> {app_name}</p>
        <p><strong>Generated:</strong> {timestamp}</p>
    </div>

    <div class="summary">
        <h2>📊 Summary</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>{statistics.get('total', 0)}</h3>
                <p>Total Tests</p>
            </div>
            <div class="stat-box passed">
                <h3>{statistics.get('passed', 0)}</h3>
                <p>Passed</p>
            </div>
            <div class="stat-box failed">
                <h3>{statistics.get('failed', 0)}</h3>
                <p>Failed</p>
            </div>
            <div class="stat-box">
                <h3>{statistics.get('skipped', 0)}</h3>
                <p>Skipped</p>
            </div>
            <div class="stat-box">
                <h3>{statistics.get('pass_rate', '0%')}</h3>
                <p>Pass Rate</p>
            </div>
            <div class="stat-box">
                <h3 class="duration">{statistics.get('total_duration', 0):.2f}s</h3>
                <p>Duration</p>
            </div>
        </div>
    </div>

    <div class="test-results">
        <h2>📋 Test Results</h2>
"""

        for result in test_results:
            test_name = result.get("test_name", "Unknown Test")
            status = result.get("status", "unknown")
            error_message = result.get("error_message")

            # Get duration
            duration = 0.0
            if "metrics" in result and isinstance(result["metrics"], dict):
                duration = result["metrics"].get("duration_seconds", 0.0)
            elif "duration_seconds" in result:
                duration = result.get("duration_seconds", 0.0)

            html += f"""
        <div class="test-item {status}">
            <h3>{test_name}</h3>
            <p><span class="status {status}">{status}</span></p>
            <p><strong>Duration:</strong> <span class="duration">{duration:.2f}s</span></p>
"""

            if error_message:
                html += f"""
            <div class="error-message">{error_message}</div>
"""

            html += "        </div>\n"

        html += """
    </div>
</body>
</html>
"""

        return html

    def _generate_json(
        self,
        test_results: List[Dict[str, Any]],
        app_name: str,
        statistics: Dict[str, Any],
    ) -> str:
        """Generate JSON report"""

        import json

        report_data = {
            "application": app_name,
            "generated_at": datetime.now().isoformat(),
            "statistics": statistics,
            "results": test_results,
        }

        return json.dumps(report_data, indent=2, default=str)

    def _generate_markdown(
        self,
        test_results: List[Dict[str, Any]],
        app_name: str,
        statistics: Dict[str, Any],
    ) -> str:
        """Generate Markdown report"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = f"""# 🧪 Test Execution Report

**Application:** {app_name}
**Generated:** {timestamp}

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total Tests | {statistics.get('total', 0)} |
| Passed | {statistics.get('passed', 0)} |
| Failed | {statistics.get('failed', 0)} |
| Skipped | {statistics.get('skipped', 0)} |
| Error | {statistics.get('error', 0)} |
| Pass Rate | {statistics.get('pass_rate', '0%')} |
| Duration | {statistics.get('total_duration', 0):.2f}s |

## 📋 Test Results

"""

        for result in test_results:
            test_name = result.get("test_name", "Unknown Test")
            status = result.get("status", "unknown")
            error_message = result.get("error_message")

            # Status icon
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "error": "💥",
            }.get(status, "❓")

            # Get duration
            duration = 0.0
            if "metrics" in result and isinstance(result["metrics"], dict):
                duration = result["metrics"].get("duration_seconds", 0.0)
            elif "duration_seconds" in result:
                duration = result.get("duration_seconds", 0.0)

            md += f"""### {status_icon} {test_name}

- **Status:** `{status.upper()}`
- **Duration:** {duration:.2f}s

"""

            if error_message:
                md += f"""**Error:**
```
{error_message}
```

"""

        return md
