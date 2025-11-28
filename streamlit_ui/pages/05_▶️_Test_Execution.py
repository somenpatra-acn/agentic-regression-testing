"""
Test Execution Page - Run Tests and Monitor Results

Execute generated tests and monitor results in real-time.
Requires Tester role or higher.
"""

import streamlit as st
import sys
from pathlib import Path
import json
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from memory.schemas import UserRole
from agents_v2.test_executor_agent_v2 import TestExecutorAgentV2
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Test Execution - AI Regression Testing",
    page_icon="▶️",
    layout="wide",
)


def init_page_state():
    """Initialize page-specific state"""
    if "execution_running" not in st.session_state:
        st.session_state.execution_running = False

    if "execution_results" not in st.session_state:
        st.session_state.execution_results = None

    if "live_results" not in st.session_state:
        st.session_state.live_results = []


def check_permissions():
    """Check if user has permission to execute tests"""
    auth_manager = st.session_state.auth_manager
    if not auth_manager.has_permission(st.session_state.username, UserRole.TESTER):
        st.error("❌ Access Denied: Requires Tester role or higher")
        st.info("Please contact an administrator to upgrade your account.")
        st.stop()


def show_execution_config():
    """Show test execution configuration"""
    st.subheader("▶️ Test Execution Configuration")

    # Check for generated tests
    cached_generation = st.session_state.state_manager.get_cached_generation(
        st.session_state.session_id
    )

    if cached_generation:
        files = cached_generation.get("files_generated", [])
        st.success(f"✅ Found {len(files)} generated test files")
    else:
        st.warning("⚠️ No generated tests found. Please generate tests first.")
        if st.button("📝 Go to Test Generation"):
            st.switch_page("pages/04_⚙️_Test_Generation.py")
        st.stop()

    # Configuration form
    with st.form("execution_config"):
        col1, col2 = st.columns(2)

        with col1:
            browser = st.selectbox(
                "Browser",
                options=["chromium", "firefox", "webkit"],
                index=0,
                help="Browser to use for test execution"
            )

            headless = st.checkbox("Run in headless mode", value=True)

        with col2:
            parallel_workers = st.slider(
                "Parallel Workers",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of parallel test workers"
            )

            timeout = st.number_input(
                "Timeout (seconds)",
                min_value=10,
                max_value=300,
                value=60,
                help="Test timeout in seconds"
            )

        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col1, col2 = st.columns(2)

            with col1:
                capture_screenshots = st.checkbox("Capture screenshots on failure", value=True)
                capture_video = st.checkbox("Record test execution video", value=False)

            with col2:
                retry_failed = st.checkbox("Retry failed tests", value=True)
                max_retries = st.number_input("Max retries", min_value=1, max_value=5, value=2)

        submitted = st.form_submit_button("🚀 Run Tests", use_container_width=True)

        if submitted:
            run_test_execution(
                browser,
                headless,
                parallel_workers,
                timeout,
                capture_screenshots,
                capture_video,
                retry_failed,
                max_retries,
                cached_generation
            )


def run_test_execution(
    browser: str,
    headless: bool,
    parallel_workers: int,
    timeout: int,
    capture_screenshots: bool,
    capture_video: bool,
    retry_failed: bool,
    max_retries: int,
    generation_result: dict
):
    """
    Execute tests

    Args:
        browser: Browser to use
        headless: Run in headless mode
        parallel_workers: Number of parallel workers
        timeout: Test timeout
        capture_screenshots: Capture screenshots on failure
        capture_video: Record video
        retry_failed: Retry failed tests
        max_retries: Max retry attempts
        generation_result: Generated test files
    """
    st.session_state.execution_running = True
    st.session_state.live_results = []

    try:
        # Create progress containers
        progress_container = st.empty()
        status_container = st.empty()
        results_container = st.empty()

        with st.spinner("▶️ Executing tests..."):
            # Create test executor agent
            executor = TestExecutorAgentV2()

            # Get test files
            test_files = generation_result.get("files_generated", [])
            test_files = [f for f in test_files if "test_" in Path(f).name]

            # Execute tests
            progress_container.progress(0.1, "Initializing test execution...")

            result = executor.execute_tests(
                test_files=test_files,
                parallel=True,
                max_workers=parallel_workers
            )

            progress_container.progress(1.0, "Test execution complete!")

            # Store results
            st.session_state.execution_results = result
            st.session_state.state_manager.cache_execution_result(
                st.session_state.session_id,
                result,
                ttl=3600  # 1 hour
            )

        # Show summary
        total_tests = result.get("total_tests", 0)
        passed = result.get("passed", 0)
        failed = result.get("failed", 0)

        status_container.success(f"✅ Execution complete! {passed}/{total_tests} tests passed.")

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        st.error(f"❌ Test execution failed: {str(e)}")

    finally:
        st.session_state.execution_running = False


def show_live_execution():
    """Show live test execution progress"""
    if st.session_state.execution_running:
        st.markdown("---")
        st.subheader("🔴 Live Execution")

        # Live status
        with st.container():
            st.markdown("**Running tests...**")

            # Progress bar
            progress = st.progress(0)
            status = st.empty()

            # Simulate live updates (in real implementation, this would come from executor)
            for i in range(100):
                if not st.session_state.execution_running:
                    break

                progress.progress(i / 100)
                status.text(f"Running test {i + 1}/100...")
                time.sleep(0.1)


def show_execution_results():
    """Display test execution results"""
    if st.session_state.execution_results:
        st.markdown("---")
        st.subheader("📊 Test Results")

        result = st.session_state.execution_results

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        total_tests = result.get("total_tests", 0)
        passed = result.get("passed", 0)
        failed = result.get("failed", 0)
        skipped = result.get("skipped", 0)

        with col1:
            st.metric("Total Tests", total_tests)

        with col2:
            st.metric("✅ Passed", passed, delta=f"{(passed/total_tests*100):.1f}%" if total_tests > 0 else "0%")

        with col3:
            st.metric("❌ Failed", failed, delta=f"{(failed/total_tests*100):.1f}%" if total_tests > 0 else "0%")

        with col4:
            st.metric("⏭️ Skipped", skipped)

        # Execution details
        execution_time = result.get("execution_time", 0)
        st.info(f"⏱️ Execution time: {execution_time:.2f} seconds")

        # Test results table
        st.markdown("### Test Case Results")

        test_results = result.get("test_results", [])

        if test_results:
            # Create results table
            results_data = []
            for test in test_results:
                results_data.append({
                    "Test Name": test.get("name", "Unknown"),
                    "Status": test.get("status", "unknown"),
                    "Duration": f"{test.get('duration', 0):.2f}s",
                    "Error": test.get("error_message", "")[:50] if test.get("error_message") else "N/A"
                })

            st.dataframe(
                results_data,
                use_container_width=True,
                height=400
            )

            # Failed tests details
            failed_tests = [t for t in test_results if t.get("status") == "failed"]
            if failed_tests:
                st.markdown("### ❌ Failed Tests Details")

                for test in failed_tests:
                    with st.expander(f"🔴 {test.get('name', 'Unknown')}"):
                        st.markdown(f"**Error Message:**")
                        st.code(test.get("error_message", "No error message"), language="text")

                        # Screenshot if available
                        screenshot_path = test.get("screenshot_path")
                        if screenshot_path and Path(screenshot_path).exists():
                            st.markdown("**Screenshot:**")
                            st.image(screenshot_path)

                        # Stack trace
                        stack_trace = test.get("stack_trace")
                        if stack_trace:
                            st.markdown("**Stack Trace:**")
                            st.code(stack_trace, language="text")

        # Actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 View Report", use_container_width=True):
                st.switch_page("pages/06_📊_Reports.py")

        with col2:
            if st.button("🔄 Run Again", use_container_width=True):
                st.session_state.execution_results = None
                st.rerun()

        with col3:
            if st.download_button(
                "💾 Download Results",
                data=json.dumps(result, indent=2),
                file_name=f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            ):
                st.success("Downloaded!")


def main():
    """Main test execution page"""
    # Check authentication
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Please login to continue")
        st.stop()

    # Check permissions
    check_permissions()

    # Initialize page state
    init_page_state()

    # Page header
    st.title("▶️ Test Execution")
    st.markdown("Execute generated tests and monitor results in real-time.")
    st.markdown("---")

    # Show configuration
    show_execution_config()

    # Show live execution if running
    if st.session_state.execution_running:
        show_live_execution()

    # Show results if available
    show_execution_results()


if __name__ == "__main__":
    main()
