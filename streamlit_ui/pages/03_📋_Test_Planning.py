"""
Test Planning Page - AI-Powered Test Plan Creation

Create comprehensive test plans with AI assistance.
Supports both autonomous and interactive modes.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_ui.auth import require_auth
from memory.schemas import UserRole
from agents_v2.conversational_orchestrator_agent import ConversationalOrchestratorAgent
from agents_v2.test_planner_agent_v2 import TestPlannerAgentV2
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Test Planning - AI Regression Testing",
    page_icon="📋",
    layout="wide",
)


def init_page_state():
    """Initialize page-specific state"""
    if "test_plan" not in st.session_state:
        st.session_state.test_plan = None

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []


def show_autonomous_mode():
    """Show autonomous test planning mode"""
    st.subheader("🤖 Autonomous Test Planning")

    st.markdown("""
    Generate test plans automatically based on feature descriptions and discovered elements.
    """)

    # Check for discovery results
    cached_discovery = st.session_state.state_manager.get_cached_discovery(
        st.session_state.session_id
    )

    if cached_discovery:
        st.success(f"✅ Using cached discovery: {len(cached_discovery.get('elements', []))} elements found")

    # Configuration form
    with st.form("planning_config"):
        feature_description = st.text_area(
            "Feature Description",
            placeholder="Describe the feature or functionality to test...\n\nExample: User login functionality with email and password validation",
            height=150,
            help="Detailed description of what needs to be tested"
        )

        col1, col2 = st.columns(2)

        with col1:
            coverage_level = st.selectbox(
                "Coverage Level",
                options=["basic", "standard", "comprehensive"],
                index=1,
                help="Level of test coverage to generate"
            )

        with col2:
            priority = st.selectbox(
                "Priority",
                options=["high", "medium", "low"],
                index=1,
                help="Priority level for test execution"
            )

        include_edge_cases = st.checkbox("Include edge cases", value=True)
        include_negative_tests = st.checkbox("Include negative tests", value=True)
        include_security_tests = st.checkbox("Include security tests", value=False)

        submitted = st.form_submit_button("🚀 Generate Test Plan", use_container_width=True)

        if submitted:
            if not feature_description.strip():
                st.error("Please provide a feature description")
            else:
                run_autonomous_planning(
                    feature_description,
                    coverage_level,
                    priority,
                    include_edge_cases,
                    include_negative_tests,
                    include_security_tests,
                    cached_discovery
                )


def run_autonomous_planning(
    feature_description: str,
    coverage_level: str,
    priority: str,
    include_edge_cases: bool,
    include_negative_tests: bool,
    include_security_tests: bool,
    discovery_result: Optional[Dict] = None
):
    """
    Run autonomous test planning

    Args:
        feature_description: Feature to test
        coverage_level: Coverage level (basic/standard/comprehensive)
        priority: Priority level
        include_edge_cases: Include edge case tests
        include_negative_tests: Include negative tests
        include_security_tests: Include security tests
        discovery_result: Optional discovery results
    """
    try:
        with st.spinner("📋 Generating test plan..."):
            # Create test planner agent
            planner = TestPlannerAgentV2()

            # Prepare discovered elements
            discovered_elements = []
            if discovery_result:
                discovered_elements = discovery_result.get("elements", [])

            # Generate test plan
            result = planner.create_plan(
                feature_description=feature_description,
                discovered_elements=discovered_elements,
                coverage_level=coverage_level
            )

            # Store result
            st.session_state.test_plan = result
            st.session_state.state_manager.cache_planning_result(
                st.session_state.session_id,
                result,
                ttl=1800  # 30 minutes
            )

        test_cases = result.get("test_cases", [])
        st.success(f"✅ Test plan generated! Created {len(test_cases)} test cases.")

    except Exception as e:
        logger.error(f"Test planning failed: {e}")
        st.error(f"❌ Test planning failed: {str(e)}")


def show_interactive_mode():
    """Show interactive test planning mode with conversational AI"""
    st.subheader("🗣️ Interactive Test Planning")

    st.markdown("""
    Chat with AI to create test plans. The AI will ask clarifying questions
    and help you design comprehensive test coverage.
    """)

    # Initialize conversational orchestrator if needed
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = ConversationalOrchestratorAgent(
            session_id=st.session_state.session_id,
            user_id=st.session_state.username,
            execution_mode="interactive"
        )

    # Chat interface
    st.markdown("---")

    # Display chat messages
    for message in st.session_state.chat_messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        with st.chat_message(role):
            st.markdown(content)

            # Show reasoning if available
            if role == "assistant" and "reasoning" in message:
                with st.expander("💭 AI Reasoning"):
                    st.markdown(message["reasoning"])

    # Chat input
    if prompt := st.chat_input("What would you like to test?"):
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt
        })

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                orchestrator = st.session_state.orchestrator
                response = orchestrator.process_user_message(prompt)

            # Display response
            st.markdown(response.get("message", ""))

            # Show reasoning
            if "reasoning" in response:
                with st.expander("💭 AI Reasoning"):
                    st.markdown(response["reasoning"])

        # Add assistant message
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response.get("message", ""),
            "reasoning": response.get("reasoning")
        })

    # Suggested prompts
    if not st.session_state.chat_messages:
        st.markdown("### 💡 Try asking:")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Create test plan for login", use_container_width=True):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": "I need to create a test plan for user login functionality"
                })
                st.rerun()

        with col2:
            if st.button("What coverage levels exist?", use_container_width=True):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": "What test coverage levels can you provide?"
                })
                st.rerun()


def show_test_plan():
    """Display generated test plan"""
    if st.session_state.test_plan:
        st.markdown("---")
        st.subheader("📋 Generated Test Plan")

        plan = st.session_state.test_plan
        test_cases = plan.get("test_cases", [])

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Test Cases", len(test_cases))

        with col2:
            positive_tests = len([tc for tc in test_cases if tc.get("test_type") == "positive"])
            st.metric("Positive Tests", positive_tests)

        with col3:
            negative_tests = len([tc for tc in test_cases if tc.get("test_type") == "negative"])
            st.metric("Negative Tests", negative_tests)

        with col4:
            edge_cases = len([tc for tc in test_cases if "edge" in tc.get("test_type", "").lower()])
            st.metric("Edge Cases", edge_cases)

        # Test cases display
        st.markdown("### Test Cases")

        for idx, test_case in enumerate(test_cases, 1):
            with st.expander(f"Test Case {idx}: {test_case.get('title', 'Untitled')}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Description:** {test_case.get('description', 'N/A')}")
                    st.markdown(f"**Type:** `{test_case.get('test_type', 'functional')}`")
                    st.markdown(f"**Priority:** `{test_case.get('priority', 'medium')}`")

                with col2:
                    st.markdown(f"**Expected Result:**")
                    st.info(test_case.get('expected_result', 'N/A'))

                # Steps
                steps = test_case.get('steps', [])
                if steps:
                    st.markdown("**Steps:**")
                    for step_idx, step in enumerate(steps, 1):
                        st.markdown(f"{step_idx}. {step}")

                # Test data
                test_data = test_case.get('test_data', {})
                if test_data:
                    st.markdown("**Test Data:**")
                    st.json(test_data)

        # Actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 Generate Test Scripts", use_container_width=True):
                st.switch_page("pages/04_⚙️_Test_Generation.py")

        with col2:
            if st.button("🔄 Create New Plan", use_container_width=True):
                st.session_state.test_plan = None
                st.rerun()

        with col3:
            if st.download_button(
                "💾 Download JSON",
                data=json.dumps(plan, indent=2),
                file_name="test_plan.json",
                mime="application/json",
                use_container_width=True
            ):
                st.success("Downloaded!")


def main():
    """Main test planning page"""
    # Check authentication
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Please login to continue")
        st.stop()

    # Initialize page state
    init_page_state()

    # Page header
    st.title("📋 Test Planning")
    st.markdown("Create comprehensive test plans with AI assistance.")
    st.markdown("---")

    # Execution mode tabs
    execution_mode = st.session_state.execution_mode

    if execution_mode == "interactive":
        show_interactive_mode()
    else:
        show_autonomous_mode()

    # Show test plan if available
    show_test_plan()


if __name__ == "__main__":
    main()
