"""Reporting Agent - generates test reports and integrates with CI/CD."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.app_profile import ApplicationProfile
from models.test_result import TestResult, TestStatus
from utils.logger import get_logger
from utils.helpers import format_duration

logger = get_logger(__name__)


class ReportingAgent:
    """
    Reporting Agent generates test reports and integrates with CI/CD tools.

    Supports:
    - HTML reports
    - JSON reports
    - CI/CD integration (Azure DevOps, GitHub Actions)
    - Trend analysis
    """

    def __init__(self, app_profile: ApplicationProfile):
        """
        Initialize Reporting Agent.

        Args:
            app_profile: Application profile
        """
        self.app_profile = app_profile

        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)

        logger.info(f"ReportingAgent initialized for {app_profile.name}")

    def generate_report(
        self,
        test_results: List[TestResult],
        format: str = "html"
    ) -> str:
        """
        Generate test execution report.

        Args:
            test_results: List of test results
            format: Report format (html, json, markdown)

        Returns:
            Path to generated report
        """
        logger.info(f"Generating {format} report for {len(test_results)} test results")

        if format == "html":
            report_path = self._generate_html_report(test_results)
        elif format == "json":
            report_path = self._generate_json_report(test_results)
        elif format == "markdown":
            report_path = self._generate_markdown_report(test_results)
        else:
            raise ValueError(f"Unsupported report format: {format}")

        logger.info(f"Report generated: {report_path}")

        return str(report_path)

    def _generate_html_report(self, test_results: List[TestResult]) -> Path:
        """Generate HTML report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"report_{timestamp}.html"

        # Calculate statistics
        stats = self._calculate_statistics(test_results)

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {self.app_profile.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ text-align: center; padding: 15px; background-color: #f0f0f0; border-radius: 5px; min-width: 120px; }}
        .stat-box.passed {{ background-color: #4CAF50; color: white; }}
        .stat-box.failed {{ background-color: #f44336; color: white; }}
        .test-results {{ background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .test-item {{ padding: 10px; margin: 10px 0; border-left: 4px solid #ddd; }}
        .test-item.passed {{ border-left-color: #4CAF50; background-color: #f1f8f4; }}
        .test-item.failed {{ border-left-color: #f44336; background-color: #fef1f0; }}
        .test-item h3 {{ margin: 0 0 10px 0; }}
        .test-item p {{ margin: 5px 0; color: #666; }}
        .error-message {{ background-color: #ffe6e6; padding: 10px; border-radius: 3px; margin-top: 10px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Execution Report</h1>
        <p>Application: {self.app_profile.name}</p>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>{stats['total']}</h3>
                <p>Total Tests</p>
            </div>
            <div class="stat-box passed">
                <h3>{stats['passed']}</h3>
                <p>Passed</p>
            </div>
            <div class="stat-box failed">
                <h3>{stats['failed']}</h3>
                <p>Failed</p>
            </div>
            <div class="stat-box">
                <h3>{stats['pass_rate']}</h3>
                <p>Pass Rate</p>
            </div>
            <div class="stat-box">
                <h3>{stats['duration']}</h3>
                <p>Duration</p>
            </div>
        </div>
    </div>

    <div class="test-results">
        <h2>Test Results</h2>
"""

        for result in test_results:
            status_class = result.status.value
            html_content += f"""
        <div class="test-item {status_class}">
            <h3>{result.test_name}</h3>
            <p><strong>Status:</strong> {result.status.value.upper()}</p>
            <p><strong>Duration:</strong> {format_duration(result.metrics.duration_seconds)}</p>
            <p><strong>Executed:</strong> {result.executed_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
"""

            if result.error_message:
                html_content += f"""
            <div class="error-message">
                <strong>Error:</strong> {result.error_message}
            </div>
"""

            html_content += "        </div>\n"

        html_content += """
    </div>
</body>
</html>
"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return report_path

    def _generate_json_report(self, test_results: List[TestResult]) -> Path:
        """Generate JSON report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"report_{timestamp}.json"

        stats = self._calculate_statistics(test_results)

        report_data = {
            "application": self.app_profile.name,
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "results": [result.to_dict() for result in test_results]
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        return report_path

    def _generate_markdown_report(self, test_results: List[TestResult]) -> Path:
        """Generate Markdown report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"report_{timestamp}.md"

        stats = self._calculate_statistics(test_results)

        md_content = f"""# Test Execution Report

**Application:** {self.app_profile.name}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {stats['total']} |
| Passed | {stats['passed']} |
| Failed | {stats['failed']} |
| Pass Rate | {stats['pass_rate']} |
| Duration | {stats['duration']} |

## Test Results

"""

        for result in test_results:
            status_icon = "✅" if result.status == TestStatus.PASSED else "❌"

            md_content += f"""### {status_icon} {result.test_name}

- **Status:** {result.status.value.upper()}
- **Duration:** {format_duration(result.metrics.duration_seconds)}
- **Executed:** {result.executed_at.strftime("%Y-%m-%d %H:%M:%S")}

"""

            if result.error_message:
                md_content += f"""**Error:**
```
{result.error_message}
```

"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return report_path

    def _calculate_statistics(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Calculate test statistics."""
        total = len(test_results)
        passed = sum(1 for r in test_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in test_results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in test_results if r.status == TestStatus.SKIPPED)
        error = sum(1 for r in test_results if r.status == TestStatus.ERROR)

        total_duration = sum(r.metrics.duration_seconds for r in test_results)

        pass_rate = (passed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": error,
            "pass_rate": f"{pass_rate:.1f}%",
            "duration": format_duration(total_duration)
        }

    def publish_to_cicd(
        self,
        test_results: List[TestResult],
        platform: str = "azure"
    ) -> bool:
        """
        Publish results to CI/CD platform.

        Args:
            test_results: Test results
            platform: CI/CD platform (azure, github)

        Returns:
            True if successful
        """
        logger.info(f"Publishing results to {platform}")

        # This would integrate with actual CI/CD APIs
        # For now, just log
        stats = self._calculate_statistics(test_results)

        logger.info(
            f"CI/CD publish summary: {stats['passed']}/{stats['total']} passed "
            f"({stats['pass_rate']} pass rate)"
        )

        return True
