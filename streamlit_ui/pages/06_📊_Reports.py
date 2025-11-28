"""
Reports Page - Test Analytics and Visualizations

View comprehensive test reports with analytics and visualizations.
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v2.reporting_agent_v2 import ReportingAgentV2
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Reports - AI Regression Testing",
    page_icon="📊",
    layout="wide",
)


def init_page_state():
    """Initialize page-specific state"""
    if "report_data" not in st.session_state:
        st.session_state.report_data = None


def show_report_generator():
    """Show report generation options"""
    st.subheader("📊 Generate Report")

    # Check for execution results
    cached_execution = st.session_state.state_manager.get_cached_execution(
        st.session_state.session_id
    )

    if cached_execution:
        total_tests = cached_execution.get("total_tests", 0)
        st.success(f"✅ Found execution results: {total_tests} tests")
    else:
        st.warning("⚠️ No execution results found. Please run tests first.")
        if st.button("▶️ Go to Test Execution"):
            # Check permissions first
            from memory.schemas import UserRole
            auth_manager = st.session_state.auth_manager
            if auth_manager.has_permission(st.session_state.username, UserRole.TESTER):
                st.switch_page("pages/05_▶️_Test_Execution.py")
            else:
                st.error("❌ Requires Tester role or higher")
        st.stop()

    # Report generation form
    with st.form("report_config"):
        col1, col2 = st.columns(2)

        with col1:
            report_format = st.selectbox(
                "Report Format",
                options=["HTML", "JSON", "MARKDOWN"],
                index=0,
                help="Output format for the report"
            )

        with col2:
            include_screenshots = st.checkbox("Include screenshots", value=True)
            include_logs = st.checkbox("Include execution logs", value=True)

        report_title = st.text_input(
            "Report Title",
            value=f"Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            help="Title for the report"
        )

        submitted = st.form_submit_button("🚀 Generate Report", use_container_width=True)

        if submitted:
            generate_report(
                report_format,
                report_title,
                include_screenshots,
                include_logs,
                cached_execution
            )


def generate_report(
    report_format: str,
    report_title: str,
    include_screenshots: bool,
    include_logs: bool,
    execution_result: dict
):
    """
    Generate test report

    Args:
        report_format: Report format (HTML/JSON/MARKDOWN)
        report_title: Report title
        include_screenshots: Include screenshots
        include_logs: Include logs
        execution_result: Test execution results
    """
    try:
        with st.spinner("📊 Generating report..."):
            # Create reporting agent
            reporter = ReportingAgentV2()

            # Generate report
            result = reporter.generate_report(
                execution_result=execution_result,
                report_format=report_format.lower(),
                output_dir="reports"
            )

            # Store report data
            st.session_state.report_data = result

        st.success("✅ Report generated successfully!")

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        st.error(f"❌ Report generation failed: {str(e)}")


def show_test_summary(execution_result: dict):
    """Display test execution summary"""
    st.subheader("📋 Test Summary")

    total_tests = execution_result.get("total_tests", 0)
    passed = execution_result.get("passed", 0)
    failed = execution_result.get("failed", 0)
    skipped = execution_result.get("skipped", 0)

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Tests", total_tests)

    with col2:
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        st.metric("✅ Passed", passed, delta=f"{pass_rate:.1f}%")

    with col3:
        fail_rate = (failed / total_tests * 100) if total_tests > 0 else 0
        st.metric("❌ Failed", failed, delta=f"{fail_rate:.1f}%")

    with col4:
        st.metric("⏭️ Skipped", skipped)

    with col5:
        execution_time = execution_result.get("execution_time", 0)
        st.metric("⏱️ Duration", f"{execution_time:.1f}s")


def show_test_charts(execution_result: dict):
    """Display test analytics charts"""
    st.subheader("📈 Analytics")

    total_tests = execution_result.get("total_tests", 0)
    passed = execution_result.get("passed", 0)
    failed = execution_result.get("failed", 0)
    skipped = execution_result.get("skipped", 0)

    col1, col2 = st.columns(2)

    with col1:
        # Pass/Fail pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Passed', 'Failed', 'Skipped'],
            values=[passed, failed, skipped],
            marker=dict(colors=['#28a745', '#dc3545', '#ffc107'])
        )])
        fig_pie.update_layout(title="Test Results Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Pass rate gauge
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pass_rate,
            title={'text': "Pass Rate"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#28a745"},
                'steps': [
                    {'range': [0, 50], 'color': "#dc3545"},
                    {'range': [50, 80], 'color': "#ffc107"},
                    {'range': [80, 100], 'color': "#28a745"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Test duration chart
    test_results = execution_result.get("test_results", [])
    if test_results:
        st.markdown("### ⏱️ Test Duration")

        # Extract test names and durations
        test_names = [t.get("name", "Unknown")[:30] for t in test_results[:10]]  # Top 10
        durations = [t.get("duration", 0) for t in test_results[:10]]

        fig_bar = go.Figure(data=[go.Bar(
            x=test_names,
            y=durations,
            marker_color='lightblue'
        )])
        fig_bar.update_layout(
            title="Test Execution Time (Top 10)",
            xaxis_title="Test Name",
            yaxis_title="Duration (seconds)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def show_test_details(execution_result: dict):
    """Display detailed test results"""
    st.subheader("📝 Test Details")

    test_results = execution_result.get("test_results", [])

    if test_results:
        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All", "Passed", "Failed", "Skipped"],
                index=0
            )

        with col2:
            sort_by = st.selectbox(
                "Sort by",
                options=["Name", "Duration", "Status"],
                index=0
            )

        with col3:
            sort_order = st.radio(
                "Order",
                options=["Ascending", "Descending"],
                index=0,
                horizontal=True
            )

        # Apply filters
        filtered_results = test_results

        if status_filter != "All":
            filtered_results = [
                t for t in filtered_results
                if t.get("status", "").lower() == status_filter.lower()
            ]

        # Sort results
        if sort_by == "Duration":
            filtered_results = sorted(
                filtered_results,
                key=lambda x: x.get("duration", 0),
                reverse=(sort_order == "Descending")
            )
        elif sort_by == "Status":
            filtered_results = sorted(
                filtered_results,
                key=lambda x: x.get("status", ""),
                reverse=(sort_order == "Descending")
            )
        else:  # Name
            filtered_results = sorted(
                filtered_results,
                key=lambda x: x.get("name", ""),
                reverse=(sort_order == "Descending")
            )

        # Display results
        st.markdown(f"**Showing {len(filtered_results)} of {len(test_results)} tests**")

        for test in filtered_results:
            status = test.get("status", "unknown")
            name = test.get("name", "Unknown")
            duration = test.get("duration", 0)

            # Status emoji
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(status.lower(), "❓")

            with st.expander(f"{status_emoji} {name} ({duration:.2f}s)"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Status:** `{status}`")
                    st.markdown(f"**Duration:** {duration:.2f} seconds")

                    error_msg = test.get("error_message")
                    if error_msg:
                        st.markdown("**Error:**")
                        st.code(error_msg, language="text")

                with col2:
                    # Screenshot if available
                    screenshot_path = test.get("screenshot_path")
                    if screenshot_path and Path(screenshot_path).exists():
                        st.image(screenshot_path, caption="Failure Screenshot")
    else:
        st.info("No test results available")


def show_generated_report():
    """Display generated report"""
    if st.session_state.report_data:
        st.markdown("---")
        st.subheader("📄 Generated Report")

        report_data = st.session_state.report_data
        report_path = report_data.get("report_path")

        if report_path and Path(report_path).exists():
            st.success(f"✅ Report saved to: `{report_path}`")

            # Download button
            try:
                with open(report_path, 'r') as f:
                    content = f.read()

                file_ext = Path(report_path).suffix
                mime_types = {
                    ".html": "text/html",
                    ".json": "application/json",
                    ".md": "text/markdown"
                }

                st.download_button(
                    "💾 Download Report",
                    data=content,
                    file_name=Path(report_path).name,
                    mime=mime_types.get(file_ext, "text/plain"),
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Error reading report: {e}")
        else:
            st.warning("Report file not found")


def main():
    """Main reports page"""
    # Check authentication
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Please login to continue")
        st.stop()

    # Initialize page state
    init_page_state()

    # Page header
    st.title("📊 Test Reports & Analytics")
    st.markdown("View comprehensive test reports with visualizations and analytics.")
    st.markdown("---")

    # Check for execution results
    cached_execution = st.session_state.state_manager.get_cached_execution(
        st.session_state.session_id
    )

    if cached_execution:
        # Show summary
        show_test_summary(cached_execution)

        st.markdown("---")

        # Show charts
        show_test_charts(cached_execution)

        st.markdown("---")

        # Show detailed results
        show_test_details(cached_execution)

        st.markdown("---")

    # Report generator
    show_report_generator()

    # Show generated report
    show_generated_report()


if __name__ == "__main__":
    main()
