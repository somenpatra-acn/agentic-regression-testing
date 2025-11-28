"""
Orchestrator & Agent Activity Monitor

Real-time dashboard for monitoring:
- Orchestrator activities
- Agent invocations
- Tool usage
- Workflow state
- Performance metrics
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any

from memory import StateManager


def init_page_state():
    """Initialize page-specific state"""
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 5


def show_orchestrator_status():
    """Show current orchestrator status"""
    st.subheader("🎯 Orchestrator Status")

    col1, col2, col3, col4 = st.columns(4)

    # Get workflow state
    state_manager = st.session_state.state_manager
    workflow_state = state_manager.get_workflow_state(st.session_state.session_id)

    with col1:
        status = "🟢 Active" if st.session_state.get("orchestrator") else "🔴 Inactive"
        st.metric("Status", status)

    with col2:
        current_stage = workflow_state.current_stage if workflow_state else "None"
        st.metric("Current Stage", current_stage)

    with col3:
        completed = len(workflow_state.completed_stages) if workflow_state else 0
        st.metric("Completed Stages", completed)

    with col4:
        mode = st.session_state.execution_mode
        st.metric("Mode", mode.title())


def show_session_info():
    """Show session information"""
    st.subheader("📝 Session Information")

    state_manager = st.session_state.state_manager
    session_stats = state_manager.get_session_stats(st.session_state.session_id)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Session Details:**")
        st.text(f"Session ID: {st.session_state.session_id[:16]}...")
        st.text(f"User: {st.session_state.username}")
        st.text(f"Started: {session_stats.get('created_at', 'Unknown')}")

    with col2:
        st.markdown("**Cached Data:**")
        st.text(f"✓ Discovery: {session_stats.get('has_cached_discovery', False)}")
        st.text(f"✓ Plan: {session_stats.get('has_cached_plan', False)}")
        st.text(f"✓ Generation: {session_stats.get('has_cached_generation', False)}")
        st.text(f"✓ Execution: {session_stats.get('has_cached_execution', False)}")


def show_agent_activity():
    """Show agent invocation history"""
    st.subheader("🤖 Agent Activity")

    state_manager = st.session_state.state_manager
    decisions = state_manager.get_agent_decisions(st.session_state.session_id)

    if decisions:
        # Create dataframe
        data = []
        for decision in decisions:
            data.append({
                "Timestamp": decision.timestamp,
                "Agent": decision.agent_name,
                "Action": decision.action,
                "Status": decision.status,
                "Duration": f"{decision.execution_time:.2f}s" if decision.execution_time else "N/A"
            })

        df = pd.DataFrame(data)

        # Show table
        st.dataframe(df, use_container_width=True, height=300)

        # Show timeline chart
        fig = px.timeline(
            df,
            x_start="Timestamp",
            x_end="Timestamp",
            y="Agent",
            color="Status",
            title="Agent Execution Timeline"
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No agent activity recorded for this session yet.")


def show_workflow_progress():
    """Show workflow progress visualization"""
    st.subheader("📊 Workflow Progress")

    state_manager = st.session_state.state_manager
    workflow_state = state_manager.get_workflow_state(st.session_state.session_id)

    if workflow_state:
        stages = ["Discovery", "Planning", "Generation", "Execution", "Reporting"]
        completed = workflow_state.completed_stages

        # Create progress data
        progress_data = []
        for stage in stages:
            status = "✅ Complete" if stage.lower() in [s.lower() for s in completed] else "⏳ Pending"
            progress_data.append({
                "Stage": stage,
                "Status": status,
                "Progress": 100 if "Complete" in status else 0
            })

        df = pd.DataFrame(progress_data)

        # Show progress bars
        for _, row in df.iterrows():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"{row['Status']} {row['Stage']}")
            with col2:
                st.progress(row['Progress'] / 100)

    else:
        st.info("No workflow started yet.")


def show_cache_status():
    """Show cache status and contents"""
    st.subheader("💾 Cache Status")

    state_manager = st.session_state.state_manager

    # Discovery cache
    with st.expander("🔍 Discovery Cache"):
        discovery_cache = state_manager.get_cached_discovery(st.session_state.session_id)
        if discovery_cache:
            st.json(discovery_cache)
        else:
            st.info("No discovery data cached")

    # Planning cache
    with st.expander("📋 Planning Cache"):
        plan_cache = state_manager.get_cached_test_plan(st.session_state.session_id)
        if plan_cache:
            st.json(plan_cache)
        else:
            st.info("No planning data cached")

    # Generation cache
    with st.expander("📝 Generation Cache"):
        gen_cache = state_manager.get_cached_generation(st.session_state.session_id)
        if gen_cache:
            st.json(gen_cache)
        else:
            st.info("No generation data cached")

    # Execution cache
    with st.expander("🧪 Execution Cache"):
        exec_cache = state_manager.get_cached_execution(st.session_state.session_id)
        if exec_cache:
            st.json(exec_cache)
        else:
            st.info("No execution data cached")


def show_conversation_log():
    """Show conversation history"""
    st.subheader("💬 Conversation Log")

    if "orchestrator" in st.session_state and st.session_state.orchestrator:
        try:
            summary = st.session_state.orchestrator.get_conversation_summary()

            if summary and "messages" in summary:
                for msg in summary["messages"]:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    timestamp = msg.get("timestamp", "")

                    with st.chat_message(role):
                        st.markdown(f"**{timestamp}**")
                        st.markdown(content)
            else:
                st.info("No conversation history available")
        except Exception as e:
            st.error(f"Error loading conversation: {e}")
    else:
        st.info("Orchestrator not initialized for this session")


def show_performance_metrics():
    """Show performance metrics"""
    st.subheader("⚡ Performance Metrics")

    state_manager = st.session_state.state_manager
    decisions = state_manager.get_agent_decisions(st.session_state.session_id)

    if decisions:
        # Calculate metrics
        total_decisions = len(decisions)
        successful = len([d for d in decisions if d.status == "success"])
        failed = len([d for d in decisions if d.status == "failed"])
        avg_time = sum([d.execution_time for d in decisions if d.execution_time]) / total_decisions if total_decisions > 0 else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Actions", total_decisions)
        with col2:
            st.metric("Successful", successful, delta=f"{(successful/total_decisions*100):.0f}%")
        with col3:
            st.metric("Failed", failed, delta=f"-{(failed/total_decisions*100):.0f}%")
        with col4:
            st.metric("Avg Time", f"{avg_time:.2f}s")

        # Show distribution chart
        status_counts = pd.DataFrame({
            "Status": ["Success", "Failed"],
            "Count": [successful, failed]
        })

        fig = px.pie(status_counts, values="Count", names="Status", title="Action Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No performance data available yet")


def main():
    """Main monitor page"""
    # Check authentication
    if not st.session_state.get("authentication_status"):
        st.warning("⚠️ Please login to continue")
        st.stop()

    # Initialize
    init_page_state()

    # Page header
    st.title("📊 Orchestrator & Agent Monitor")
    st.markdown("Real-time monitoring of orchestrator activities, agent invocations, and workflow state.")
    st.markdown("---")

    # Auto-refresh controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
    with col2:
        interval = st.selectbox("Interval", [5, 10, 30, 60], index=0)
        st.session_state.refresh_interval = interval
    with col3:
        if st.button("🔃 Refresh Now"):
            st.rerun()

    st.markdown("---")

    # Main content
    show_orchestrator_status()
    st.markdown("---")

    show_session_info()
    st.markdown("---")

    show_workflow_progress()
    st.markdown("---")

    show_agent_activity()
    st.markdown("---")

    show_performance_metrics()
    st.markdown("---")

    show_cache_status()
    st.markdown("---")

    show_conversation_log()

    # Auto-refresh logic
    if st.session_state.auto_refresh:
        import time
        time.sleep(st.session_state.refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
