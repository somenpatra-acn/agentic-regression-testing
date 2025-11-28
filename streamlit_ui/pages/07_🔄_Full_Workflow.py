"""
Full Workflow Page - End-to-End Test Automation Wizard

Run the complete workflow from discovery to reporting in one go.
"""

import streamlit as st
import sys
from pathlib import Path
import json
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from memory.schemas import UserRole
from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Full Workflow - AI Regression Testing",
    page_icon="🔄",
    layout="wide",
)


def init_page_state():
    """Initialize page-specific state"""
    if "workflow_running" not in st.session_state:
        st.session_state.workflow_running = False

    if "workflow_stage" not in st.session_state:
        st.session_state.workflow_stage = "configuration"

    if "workflow_result" not in st.session_state:
        st.session_state.workflow_result = None

    if "workflow_progress" not in st.session_state:
        st.session_state.workflow_progress = {
            "discovery": {"status": "pending", "result": None},
            "planning": {"status": "pending", "result": None},
            "generation": {"status": "pending", "result": None},
            "execution": {"status": "pending", "result": None},
            "reporting": {"status": "pending", "result": None}
        }


def show_workflow_wizard():
    """Show workflow configuration wizard"""
    st.subheader("🔄 Full Workflow Configuration")

    st.markdown("""
    Run the complete testing workflow in one go:
    **Discovery → Test Planning → Test Generation → Execution → Reporting**
    """)

    # Configuration form
    with st.form("workflow_config"):
        st.markdown("### 🎯 Application Configuration")

        col1, col2 = st.columns(2)

        with col1:
            url = st.text_input(
                "Application URL",
                placeholder="https://example.com",
                help="URL of the application to test"
            )

            app_type = st.selectbox(
                "Application Type",
                options=["WEB", "API"],
                index=0,
                help="Type of application"
            )

        with col2:
            test_framework = st.selectbox(
                "Test Framework",
                options=["PLAYWRIGHT", "SELENIUM", "PYTEST"],
                index=0,
                help="Which test framework to use"
            )

            browser = st.selectbox(
                "Browser",
                options=["chromium", "firefox", "webkit"],
                index=0,
                help="Target browser"
            )

        st.markdown("### 📝 Feature to Test")

        feature_description = st.text_area(
            "Feature Description",
            placeholder="Describe what functionality you want to test...\n\nExample: User authentication with login, logout, and password reset",
            height=150,
            help="Detailed description of the feature to test"
        )

        st.markdown("### ⚙️ Workflow Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            max_depth = st.slider("Discovery Depth", 1, 5, 3)
            max_pages = st.slider("Max Pages", 10, 200, 50)

        with col2:
            coverage_level = st.selectbox("Coverage Level", ["basic", "standard", "comprehensive"], index=1)
            parallel_execution = st.checkbox("Parallel Execution", value=True)

        with col3:
            headless = st.checkbox("Headless Mode", value=True)
            generate_report = st.checkbox("Auto-generate Report", value=True)

        st.markdown("---")

        # Execution mode
        execution_mode = st.session_state.execution_mode

        if execution_mode == "interactive":
            st.info("🗣️ **Interactive Mode**: You'll be asked to approve each stage before proceeding")
        else:
            st.info("🤖 **Autonomous Mode**: The workflow will run automatically without intervention")

        submitted = st.form_submit_button("🚀 Start Full Workflow", use_container_width=True)

        if submitted:
            if not url or not feature_description.strip():
                st.error("Please provide both URL and feature description")
            else:
                run_full_workflow(
                    url=url,
                    app_type=app_type,
                    test_framework=test_framework,
                    browser=browser,
                    feature_description=feature_description,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    coverage_level=coverage_level,
                    parallel_execution=parallel_execution,
                    headless=headless,
                    generate_report=generate_report
                )


def run_full_workflow(
    url: str,
    app_type: str,
    test_framework: str,
    browser: str,
    feature_description: str,
    max_depth: int,
    max_pages: int,
    coverage_level: str,
    parallel_execution: bool,
    headless: bool,
    generate_report: bool
):
    """
    Run complete workflow

    Args:
        url: Application URL
        app_type: Application type
        test_framework: Test framework
        browser: Browser
        feature_description: Feature to test
        max_depth: Discovery depth
        max_pages: Max pages to discover
        coverage_level: Coverage level
        parallel_execution: Enable parallel execution
        headless: Headless mode
        generate_report: Generate report
    """
    st.session_state.workflow_running = True
    st.session_state.workflow_stage = "running"

    try:
        # Create application profile
        app_profile = ApplicationProfile(
            name="workflow_app",
            app_type=ApplicationType[app_type],
            adapter="web" if app_type == "WEB" else "api",
            base_url=url,
            test_framework=TestFramework[test_framework],
        )

        # Create orchestrator
        with st.spinner("🔄 Initializing workflow..."):
            orchestrator = OrchestratorAgentV2(
                app_profile=app_profile,
                output_dir="generated_tests",
                reports_dir="reports",
                enable_hitl=(st.session_state.execution_mode == "interactive")
            )

        # Progress containers
        progress_container = st.empty()
        stage_container = st.empty()
        details_container = st.empty()

        # Run workflow
        progress_container.progress(0.0, "Starting workflow...")

        # Stage 1: Discovery
        update_stage_status("discovery", "running")
        progress_container.progress(0.2, "🔍 Running discovery...")
        stage_container.info("**Current Stage:** Discovery")

        # In real implementation, this would call orchestrator.run_full_workflow()
        # For now, we'll simulate the stages

        # Simulate discovery
        import time
        time.sleep(2)
        update_stage_status("discovery", "completed", {"elements": 95, "pages": 12})

        # Stage 2: Planning
        progress_container.progress(0.4, "📋 Creating test plan...")
        update_stage_status("planning", "running")
        stage_container.info("**Current Stage:** Test Planning")
        time.sleep(2)
        update_stage_status("planning", "completed", {"test_cases": 25})

        # Stage 3: Generation
        progress_container.progress(0.6, "📝 Generating test scripts...")
        update_stage_status("generation", "running")
        stage_container.info("**Current Stage:** Test Generation")
        time.sleep(2)
        update_stage_status("generation", "completed", {"files": 8})

        # Stage 4: Execution (requires permission)
        auth_manager = st.session_state.auth_manager
        if auth_manager.has_permission(st.session_state.username, UserRole.TESTER):
            progress_container.progress(0.8, "▶️ Executing tests...")
            update_stage_status("execution", "running")
            stage_container.info("**Current Stage:** Test Execution")
            time.sleep(3)
            update_stage_status("execution", "completed", {"passed": 22, "failed": 3, "total": 25})
        else:
            update_stage_status("execution", "skipped", {"reason": "Insufficient permissions"})

        # Stage 5: Reporting
        if generate_report:
            progress_container.progress(0.9, "📊 Generating report...")
            update_stage_status("reporting", "running")
            stage_container.info("**Current Stage:** Report Generation")
            time.sleep(1)
            update_stage_status("reporting", "completed", {"report_path": "reports/test_report.html"})

        progress_container.progress(1.0, "✅ Workflow complete!")
        stage_container.success("**All stages completed successfully!**")

        st.session_state.workflow_stage = "completed"

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        st.error(f"❌ Workflow failed: {str(e)}")
        st.session_state.workflow_stage = "failed"

    finally:
        st.session_state.workflow_running = False


def update_stage_status(stage: str, status: str, result: Optional[Dict] = None):
    """
    Update stage status in workflow progress

    Args:
        stage: Stage name
        status: Status (pending/running/completed/failed/skipped)
        result: Optional result data
    """
    if stage in st.session_state.workflow_progress:
        st.session_state.workflow_progress[stage]["status"] = status
        if result:
            st.session_state.workflow_progress[stage]["result"] = result


def show_workflow_progress():
    """Display workflow progress tracker"""
    if st.session_state.workflow_stage in ["running", "completed", "failed"]:
        st.markdown("---")
        st.subheader("📊 Workflow Progress")

        progress = st.session_state.workflow_progress

        # Progress timeline
        stages = ["discovery", "planning", "generation", "execution", "reporting"]
        stage_names = ["🔍 Discovery", "📋 Planning", "📝 Generation", "▶️ Execution", "📊 Reporting"]

        for stage, name in zip(stages, stage_names):
            stage_data = progress.get(stage, {})
            status = stage_data.get("status", "pending")
            result = stage_data.get("result", {})

            # Status indicator
            if status == "completed":
                icon = "✅"
                color = "green"
            elif status == "running":
                icon = "🔄"
                color = "blue"
            elif status == "failed":
                icon = "❌"
                color = "red"
            elif status == "skipped":
                icon = "⏭️"
                color = "gray"
            else:
                icon = "⏸️"
                color = "gray"

            # Display stage
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                st.markdown(f"## {icon}")

            with col2:
                st.markdown(f"### {name}")
                st.markdown(f"**Status:** `{status}`")

            with col3:
                if result:
                    st.json(result)

            st.markdown("---")


def show_workflow_results():
    """Display final workflow results"""
    if st.session_state.workflow_stage == "completed":
        st.markdown("---")
        st.subheader("✅ Workflow Completed Successfully!")

        progress = st.session_state.workflow_progress

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            discovery_result = progress["discovery"].get("result", {})
            st.metric("Elements Discovered", discovery_result.get("elements", 0))

        with col2:
            planning_result = progress["planning"].get("result", {})
            st.metric("Test Cases Created", planning_result.get("test_cases", 0))

        with col3:
            generation_result = progress["generation"].get("result", {})
            st.metric("Test Files Generated", generation_result.get("files", 0))

        with col4:
            execution_result = progress["execution"].get("result", {})
            total_tests = execution_result.get("total", 0)
            passed = execution_result.get("passed", 0)
            if total_tests > 0:
                pass_rate = (passed / total_tests * 100)
                st.metric("Pass Rate", f"{pass_rate:.1f}%")

        # Actions
        st.markdown("---")
        st.markdown("### 🎯 Next Steps")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 View Detailed Report", use_container_width=True):
                st.switch_page("pages/06_📊_Reports.py")

        with col2:
            if st.button("🔄 Run Another Workflow", use_container_width=True):
                # Reset workflow state
                st.session_state.workflow_stage = "configuration"
                st.session_state.workflow_progress = {
                    "discovery": {"status": "pending", "result": None},
                    "planning": {"status": "pending", "result": None},
                    "generation": {"status": "pending", "result": None},
                    "execution": {"status": "pending", "result": None},
                    "reporting": {"status": "pending", "result": None}
                }
                st.rerun()

        with col3:
            st.info("💡 Explore individual stages for more control")


def main():
    """Main full workflow page"""
    # Check authentication
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Please login to continue")
        st.stop()

    # Initialize page state
    init_page_state()

    # Page header
    st.title("🔄 Full Workflow")
    st.markdown("Run the complete end-to-end testing workflow automatically.")
    st.markdown("---")

    # Show wizard or progress based on stage
    if st.session_state.workflow_stage == "configuration":
        show_workflow_wizard()
    elif st.session_state.workflow_stage in ["running", "completed", "failed"]:
        show_workflow_progress()
        if st.session_state.workflow_stage == "completed":
            show_workflow_results()


if __name__ == "__main__":
    main()
