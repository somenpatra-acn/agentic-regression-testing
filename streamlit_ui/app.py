"""
Main Streamlit Application Entry Point

Multi-page application with authentication, session management, and routing.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from streamlit_ui.config import STREAMLIT_CONFIG, REDIS_CONFIG, MESSAGES, PAGES
from streamlit_ui.auth import AuthManager
from memory import RedisManager, StateManager, get_redis_manager
from memory.schemas import UserRole
from utils.logger import get_logger

logger = get_logger(__name__)


def init_page_config():
    """Initialize Streamlit page configuration"""
    st.set_page_config(
        page_title=STREAMLIT_CONFIG["page_title"],
        page_icon=STREAMLIT_CONFIG["page_icon"],
        layout=STREAMLIT_CONFIG["layout"],
        initial_sidebar_state=STREAMLIT_CONFIG["initial_sidebar_state"],
    )


def init_session_state():
    """Initialize session state variables"""
    # Authentication state
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "name" not in st.session_state:
        st.session_state.name = None

    # Session management
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())

    # Execution mode
    if "execution_mode" not in st.session_state:
        st.session_state.execution_mode = "interactive"

    # Redis and state manager
    if "redis_manager" not in st.session_state:
        st.session_state.redis_manager = get_redis_manager()

    if "state_manager" not in st.session_state:
        st.session_state.state_manager = StateManager()

    # Auth manager
    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = AuthManager()


def init_user_session(username: str):
    """
    Initialize user session in Redis

    Args:
        username: Authenticated username
    """
    try:
        state_manager = st.session_state.state_manager
        session_id = st.session_state.session_id
        execution_mode = st.session_state.execution_mode

        # Create session metadata
        state_manager.create_session(
            session_id=session_id,
            user_id=username,
            execution_mode=execution_mode
        )

        logger.info(f"Initialized session {session_id} for user {username}")

    except Exception as e:
        logger.error(f"Failed to initialize user session: {e}")
        st.warning(f"Session initialization failed: {str(e)}")


def show_redis_status():
    """Display Redis connection status"""
    redis_manager = st.session_state.redis_manager

    if redis_manager.is_fake:
        st.sidebar.warning(MESSAGES["no_redis"])
    else:
        st.sidebar.success("✅ Connected to Redis")


def show_login_page():
    """Display login page"""
    st.title("🤖 AI Regression Testing Framework")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(MESSAGES["welcome"])
        st.markdown("---")
        st.subheader("🔐 Login")

        # Login form
        auth_manager = st.session_state.auth_manager
        name, username, authentication_status = auth_manager.login()

        # Update session state
        st.session_state.authentication_status = authentication_status
        st.session_state.username = username
        st.session_state.name = name

        # Handle authentication result
        if authentication_status:
            st.success(f"Welcome, {name}!")
            init_user_session(username)
            st.rerun()
        elif authentication_status is False:
            st.error("❌ Username or password is incorrect")
        elif authentication_status is None:
            st.info("👉 Please enter your credentials")

        # Show default credentials hint
        with st.expander("ℹ️ Default Credentials"):
            st.markdown("""
            **For testing purposes:**

            | Role | Username | Password |
            |------|----------|----------|
            | Admin | `admin` | `admin123` |
            | Tester | `tester` | `tester123` |
            | Viewer | `viewer` | `viewer123` |

            ⚠️ **Change these passwords in production!**
            """)


def show_main_app():
    """Display main application interface"""
    # Sidebar navigation
    show_sidebar()

    # Main content area
    st.title("🏠 Home")
    st.markdown("---")

    # Welcome message
    username = st.session_state.username
    name = st.session_state.name
    auth_manager = st.session_state.auth_manager
    user_role = auth_manager.get_user_role(username)

    st.markdown(f"### Welcome back, **{name}**! 👋")
    st.markdown(f"**Role:** `{user_role.value}`")
    st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")

    st.markdown("---")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Sessions", "1", delta="Current")

    with col2:
        st.metric("Test Plans", "0", delta="Created")

    with col3:
        st.metric("Tests Generated", "0", delta="Ready")

    with col4:
        st.metric("Tests Executed", "0", delta="Passed")

    st.markdown("---")

    # Execution mode selector
    st.subheader("⚙️ Execution Mode")

    execution_mode = st.radio(
        "Select how you want to work:",
        options=["interactive", "autonomous"],
        index=0 if st.session_state.execution_mode == "interactive" else 1,
        format_func=lambda x: "🗣️ Interactive (Conversational AI)" if x == "interactive" else "🤖 Autonomous (Batch Processing)",
        horizontal=True
    )

    if execution_mode != st.session_state.execution_mode:
        st.session_state.execution_mode = execution_mode
        st.rerun()

    if execution_mode == "interactive":
        st.info("""
        **Interactive Mode:**
        - Chat with AI to plan and execute tests
        - Get explanations and reasoning at each step
        - AI automatically selects the best tools and agents
        - Context is maintained across conversation
        """)
    else:
        st.info("""
        **Autonomous Mode:**
        - Batch processing of test workflows
        - Minimal human intervention
        - Pre-configured workflows
        - Faster execution for known scenarios
        """)

    st.markdown("---")

    # Quick actions
    st.subheader("🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Start Discovery", use_container_width=True):
            st.switch_page("pages/02_🔍_Discovery.py")

    with col2:
        if st.button("📋 Create Test Plan", use_container_width=True):
            st.switch_page("pages/03_📋_Test_Planning.py")

    with col3:
        if st.button("🔄 Run Full Workflow", use_container_width=True):
            st.switch_page("pages/07_🔄_Full_Workflow.py")

    st.markdown("---")

    # Recent activity
    st.subheader("📊 Recent Activity")
    st.info("No recent activity. Start by running a discovery or creating a test plan.")

    # System status
    with st.expander("🔧 System Status"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Redis Connection:**")
            if st.session_state.redis_manager.is_fake:
                st.warning("Using in-memory storage (fakeredis)")
            else:
                st.success("Connected to Redis")

        with col2:
            st.markdown("**LLM Configuration:**")
            from config.llm_config import get_llm_provider
            provider = get_llm_provider()
            st.info(f"Provider: {provider}")


def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        # User info
        st.markdown(f"### 👤 {st.session_state.name}")
        st.markdown(f"**@{st.session_state.username}**")

        # User role
        auth_manager = st.session_state.auth_manager
        user_role = auth_manager.get_user_role(st.session_state.username)
        st.markdown(f"**Role:** `{user_role.value}`")

        st.markdown("---")

        # Navigation
        st.markdown("### 📂 Navigation")

        # Home
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

        # Discovery
        if st.button("🔍 Discovery", use_container_width=True):
            st.switch_page("pages/02_🔍_Discovery.py")

        # Test Planning
        if st.button("📋 Test Planning", use_container_width=True):
            st.switch_page("pages/03_📋_Test_Planning.py")

        # Test Generation
        if st.button("📝 Test Generation", use_container_width=True):
            st.switch_page("pages/04_⚙️_Test_Generation.py")

        # Test Execution (requires tester role or higher)
        if auth_manager.has_permission(st.session_state.username, UserRole.TESTER):
            if st.button("▶️ Test Execution", use_container_width=True):
                st.switch_page("pages/05_▶️_Test_Execution.py")

        # Reports
        if st.button("📊 Reports", use_container_width=True):
            st.switch_page("pages/06_📊_Reports.py")

        # Full Workflow
        if st.button("🔄 Full Workflow", use_container_width=True):
            st.switch_page("pages/07_🔄_Full_Workflow.py")

        # Monitor (admin only)
        if auth_manager.has_permission(st.session_state.username, UserRole.ADMIN):
            if st.button("📊 Monitor", use_container_width=True):
                st.switch_page("pages/08_📊_Monitor.py")

        st.markdown("---")

        # Execution mode indicator
        mode = st.session_state.execution_mode
        mode_emoji = "🗣️" if mode == "interactive" else "🤖"
        st.markdown(f"**Mode:** {mode_emoji} {mode.title()}")

        st.markdown("---")

        # Redis status
        show_redis_status()

        st.markdown("---")

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            auth_manager = st.session_state.auth_manager
            auth_manager.logout()
            st.session_state.authentication_status = None
            st.session_state.username = None
            st.session_state.name = None
            st.rerun()


def main():
    """Main application entry point"""
    # Initialize page config
    init_page_config()

    # Initialize session state
    init_session_state()

    # Check authentication
    if st.session_state.authentication_status:
        # User is authenticated - show main app
        show_main_app()
    else:
        # User is not authenticated - show login
        show_login_page()


if __name__ == "__main__":
    main()
