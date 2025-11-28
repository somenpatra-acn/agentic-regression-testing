"""
Discovery Page - Application Element Discovery

Discover UI elements, APIs, or database schemas from applications.
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
from memory import ConversationMemory
from memory.schemas import UserRole
from agents_v2.conversational_orchestrator_agent import ConversationalOrchestratorAgent
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Discovery - AI Regression Testing",
    page_icon="🔍",
    layout="wide",
)


def init_page_state():
    """Initialize page-specific state"""
    if "discovery_running" not in st.session_state:
        st.session_state.discovery_running = False

    if "discovery_result" not in st.session_state:
        st.session_state.discovery_result = None

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []


def show_autonomous_mode():
    """Show autonomous discovery mode"""
    st.subheader("🤖 Autonomous Discovery")

    st.markdown("""
    Configure and run automated element discovery without interactive guidance.
    """)

    # Configuration form
    with st.form("discovery_config"):
        col1, col2 = st.columns(2)

        with col1:
            url = st.text_input(
                "Application URL",
                placeholder="https://example.com",
                help="URL of the application to discover"
            )

            app_type = st.selectbox(
                "Application Type",
                options=["WEB", "API"],
                help="Type of application"
            )

        with col2:
            max_depth = st.slider(
                "Max Crawl Depth",
                min_value=1,
                max_value=5,
                value=3,
                help="Maximum depth for page crawling"
            )

            max_pages = st.slider(
                "Max Pages",
                min_value=10,
                max_value=200,
                value=50,
                help="Maximum number of pages to discover"
            )

        headless = st.checkbox("Run in headless mode", value=True)
        use_cache = st.checkbox("Use cached results (if available)", value=True)

        submitted = st.form_submit_button("🚀 Start Discovery", use_container_width=True)

        if submitted:
            if not url:
                st.error("Please provide a URL")
            else:
                run_autonomous_discovery(url, app_type, max_depth, max_pages, headless, use_cache)


def run_autonomous_discovery(
    url: str,
    app_type: str,
    max_depth: int,
    max_pages: int,
    headless: bool,
    use_cache: bool
):
    """
    Run autonomous discovery

    Args:
        url: Application URL
        app_type: Application type (WEB/API)
        max_depth: Max crawl depth
        max_pages: Max pages to discover
        headless: Run browser in headless mode
        use_cache: Use cached results
    """
    st.session_state.discovery_running = True

    try:
        # Create application profile
        app_profile = ApplicationProfile(
            name="discovery_app",
            app_type=ApplicationType[app_type],
            adapter="web" if app_type == "WEB" else "api",
            base_url=url,
            test_framework=TestFramework.PLAYWRIGHT,
        )

        # Create discovery agent
        with st.spinner("🔍 Discovering elements..."):
            discovery_agent = DiscoveryAgentV2(app_profile=app_profile)

            # Run discovery
            result = discovery_agent.discover(
                url=url,
                max_depth=max_depth,
                max_pages=max_pages,
                headless=headless
            )

        # Store result
        st.session_state.discovery_result = result
        st.session_state.state_manager.cache_discovery_result(
            st.session_state.session_id,
            result,
            ttl=1800  # 30 minutes
        )

        st.success(f"✅ Discovery complete! Found {len(result.get('elements', []))} elements from {len(result.get('pages', []))} pages.")

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        st.error(f"❌ Discovery failed: {str(e)}")

    finally:
        st.session_state.discovery_running = False


def show_interactive_mode():
    """Show interactive discovery mode with conversational AI"""
    st.subheader("🗣️ Interactive Discovery")

    st.markdown("""
    Chat with AI to discover application elements. The AI will guide you through the process
    and explain its reasoning at each step.
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
    if prompt := st.chat_input("What would you like to discover?"):
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

            # Handle approval needed - show hint to user
            if response.get("awaiting_approval"):
                st.info("👉 Type 'yes' to proceed or 'no' to cancel in the chat below.")

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
            if st.button("Discover elements from a URL", use_container_width=True):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": "I want to discover elements from https://example.com"
                })
                st.rerun()

        with col2:
            if st.button("What can you discover?", use_container_width=True):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": "What types of applications can you discover?"
                })
                st.rerun()


def show_discovery_results():
    """Display discovery results"""
    if st.session_state.discovery_result:
        st.markdown("---")
        st.subheader("📊 Discovery Results")

        result = st.session_state.discovery_result

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Elements", len(result.get("elements", [])))

        with col2:
            st.metric("Pages Discovered", len(result.get("pages", [])))

        with col3:
            st.metric("Forms Found", len([e for e in result.get("elements", []) if e.get("type") == "form"]))

        with col4:
            st.metric("Buttons Found", len([e for e in result.get("elements", []) if e.get("type") == "button"]))

        # Detailed results
        tab1, tab2, tab3 = st.tabs(["📝 Elements", "📄 Pages", "📊 Raw Data"])

        with tab1:
            elements = result.get("elements", [])
            if elements:
                st.dataframe(
                    elements,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No elements discovered")

        with tab2:
            pages = result.get("pages", [])
            if pages:
                for page in pages:
                    with st.expander(f"🔗 {page.get('url', 'Unknown')}"):
                        st.json(page)
            else:
                st.info("No pages discovered")

        with tab3:
            st.json(result)

        # Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Create Test Plan", use_container_width=True):
                st.switch_page("pages/03_📋_Test_Planning.py")

        with col2:
            if st.button("🔄 Run Again", use_container_width=True):
                st.session_state.discovery_result = None
                st.rerun()

        with col3:
            if st.download_button(
                "💾 Download JSON",
                data=json.dumps(result, indent=2),
                file_name="discovery_result.json",
                mime="application/json",
                use_container_width=True
            ):
                st.success("Downloaded!")


def main():
    """Main discovery page"""
    # Check authentication
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Please login to continue")
        st.stop()

    # Initialize page state
    init_page_state()

    # Page header
    st.title("🔍 Application Discovery")
    st.markdown("Discover UI elements, APIs, or database schemas from applications.")
    st.markdown("---")

    # Execution mode tabs
    execution_mode = st.session_state.execution_mode

    if execution_mode == "interactive":
        show_interactive_mode()
    else:
        show_autonomous_mode()

    # Show results if available
    show_discovery_results()


if __name__ == "__main__":
    main()
