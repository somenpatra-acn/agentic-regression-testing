"""
Test Generation Page - Executable Test Script Generation

Generate test scripts in Playwright, Selenium, or Pytest.
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from memory.schemas import UserRole
from agents_v2.test_generator_agent_v2 import TestGeneratorAgentV2
from models.app_profile import TestFramework
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Test Generation - AI Regression Testing",
    page_icon="📝",
    layout="wide",
)


def init_page_state():
    """Initialize page-specific state"""
    if "generated_tests" not in st.session_state:
        st.session_state.generated_tests = None


def show_generation_config():
    """Show test generation configuration"""
    st.subheader("⚙️ Test Generation Configuration")

    # Check for test plan
    cached_plan = st.session_state.state_manager.get_cached_planning(
        st.session_state.session_id
    )

    if cached_plan:
        test_cases = cached_plan.get("test_cases", [])
        st.success(f"✅ Using cached test plan: {len(test_cases)} test cases")
    else:
        st.warning("⚠️ No test plan found. Please create a test plan first.")
        if st.button("📋 Go to Test Planning"):
            st.switch_page("pages/03_📋_Test_Planning.py")
        st.stop()

    # Configuration form
    with st.form("generation_config"):
        col1, col2 = st.columns(2)

        with col1:
            framework = st.selectbox(
                "Test Framework",
                options=["PLAYWRIGHT", "SELENIUM", "PYTEST"],
                index=0,
                help="Which test framework to use"
            )

            language = st.selectbox(
                "Programming Language",
                options=["python", "typescript", "javascript"],
                index=0,
                help="Programming language for tests"
            )

        with col2:
            browser = st.selectbox(
                "Browser",
                options=["chromium", "firefox", "webkit"],
                index=0,
                help="Target browser for tests"
            )

            use_page_object = st.checkbox(
                "Use Page Object Model",
                value=True,
                help="Generate tests using Page Object Model pattern"
            )

        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col1, col2 = st.columns(2)

            with col1:
                include_screenshots = st.checkbox("Include screenshot capture", value=True)
                include_videos = st.checkbox("Include video recording", value=False)

            with col2:
                parallel_execution = st.checkbox("Enable parallel execution", value=True)
                retry_failed = st.checkbox("Retry failed tests", value=True)

        submitted = st.form_submit_button("🚀 Generate Tests", use_container_width=True)

        if submitted:
            run_test_generation(
                framework,
                language,
                browser,
                use_page_object,
                include_screenshots,
                include_videos,
                parallel_execution,
                retry_failed,
                cached_plan
            )


def run_test_generation(
    framework: str,
    language: str,
    browser: str,
    use_page_object: bool,
    include_screenshots: bool,
    include_videos: bool,
    parallel_execution: bool,
    retry_failed: bool,
    test_plan: dict
):
    """
    Generate test scripts

    Args:
        framework: Test framework
        language: Programming language
        browser: Target browser
        use_page_object: Use Page Object Model
        include_screenshots: Include screenshots
        include_videos: Include video recording
        parallel_execution: Enable parallel execution
        retry_failed: Retry failed tests
        test_plan: Test plan data
    """
    try:
        with st.spinner("📝 Generating test scripts..."):
            # Create test generator agent
            generator = TestGeneratorAgentV2()

            # Prepare test cases
            test_cases = test_plan.get("test_cases", [])

            # Generate tests
            result = generator.generate_tests(
                test_cases=test_cases,
                framework=TestFramework[framework],
                output_dir="generated_tests"
            )

            # Store result
            st.session_state.generated_tests = result
            st.session_state.state_manager.cache_generation_result(
                st.session_state.session_id,
                result,
                ttl=1800  # 30 minutes
            )

        generated_files = result.get("files_generated", [])
        st.success(f"✅ Test generation complete! Generated {len(generated_files)} test files.")

    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        st.error(f"❌ Test generation failed: {str(e)}")


def show_generated_tests():
    """Display generated test scripts"""
    if st.session_state.generated_tests:
        st.markdown("---")
        st.subheader("📝 Generated Test Scripts")

        result = st.session_state.generated_tests
        files = result.get("files_generated", [])

        # Summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Files", len(files))

        with col2:
            test_files = len([f for f in files if "test_" in f])
            st.metric("Test Files", test_files)

        with col3:
            page_objects = len([f for f in files if "page" in f.lower()])
            st.metric("Page Objects", page_objects)

        # File browser
        st.markdown("### 📁 Generated Files")

        for file_path in files:
            file_name = Path(file_path).name

            with st.expander(f"📄 {file_name}"):
                try:
                    # Try to read and display file content
                    if Path(file_path).exists():
                        with open(file_path, 'r') as f:
                            content = f.read()

                        st.code(content, language="python")

                        # Download button
                        st.download_button(
                            "💾 Download",
                            data=content,
                            file_name=file_name,
                            mime="text/plain"
                        )
                    else:
                        st.warning(f"File not found: {file_path}")

                except Exception as e:
                    st.error(f"Error reading file: {e}")

        # Actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("▶️ Execute Tests", use_container_width=True):
                # Check permissions
                auth_manager = st.session_state.auth_manager
                if auth_manager.has_permission(st.session_state.username, UserRole.TESTER):
                    st.switch_page("pages/05_▶️_Test_Execution.py")
                else:
                    st.error("❌ Requires Tester role or higher")

        with col2:
            if st.button("🔄 Generate Again", use_container_width=True):
                st.session_state.generated_tests = None
                st.rerun()

        with col3:
            # Download all as ZIP
            st.info("💡 Use the file browser above to download individual files")


def main():
    """Main test generation page"""
    # Check authentication
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Please login to continue")
        st.stop()

    # Initialize page state
    init_page_state()

    # Page header
    st.title("📝 Test Generation")
    st.markdown("Generate executable test scripts in Playwright, Selenium, or Pytest.")
    st.markdown("---")

    # Show configuration
    show_generation_config()

    # Show generated tests if available
    show_generated_tests()


if __name__ == "__main__":
    main()
