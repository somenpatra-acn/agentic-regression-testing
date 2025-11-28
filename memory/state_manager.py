"""
State Manager for Session and Workflow State

Manages session metadata, user preferences, and workflow state caching.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from memory.redis_manager import RedisManager, get_redis_manager
from memory.schemas import (
    SessionMetadata,
    UserPreferences,
    WorkflowStateCache,
    AgentDecision
)


class StateManager:
    """
    Manages session state and workflow caching with Redis
    """

    def __init__(self, redis_manager: Optional[RedisManager] = None):
        """Initialize state manager"""
        self.redis = redis_manager or get_redis_manager()

    # ========== Session Management ==========

    def create_session(
        self,
        session_id: str,
        user_id: str,
        execution_mode: str = "interactive"
    ) -> SessionMetadata:
        """Create new session"""
        metadata = SessionMetadata(
            session_id=session_id,
            user_id=user_id,
            execution_mode=execution_mode
        )

        key = f"session:{session_id}:metadata"
        self.redis.set_json(key, metadata.model_dump(), ttl=24*3600)  # 24h TTL

        return metadata

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session metadata"""
        key = f"session:{session_id}:metadata"
        data = self.redis.get_json(key)

        if data:
            return SessionMetadata(**data)
        return None

    def update_session_activity(self, session_id: str):
        """Update last active timestamp"""
        session = self.get_session(session_id)
        if session:
            session.last_active = datetime.now()
            key = f"session:{session_id}:metadata"
            self.redis.set_json(key, session.model_dump(), ttl=24*3600)

    def delete_session(self, session_id: str):
        """Delete session and all associated data"""
        patterns = [
            f"session:{session_id}:*"
        ]
        for pattern in patterns:
            keys = self.redis.keys(pattern)
            for key in keys:
                self.redis.delete(key)

    def list_user_sessions(self, user_id: str) -> List[SessionMetadata]:
        """List all sessions for a user"""
        pattern = "session:*:metadata"
        keys = self.redis.keys(pattern)

        sessions = []
        for key in keys:
            data = self.redis.get_json(key)
            if data and data.get("user_id") == user_id:
                sessions.append(SessionMetadata(**data))

        # Sort by last active
        sessions.sort(key=lambda x: x.last_active, reverse=True)
        return sessions

    # ========== User Preferences ==========

    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences"""
        key = f"user:{user_id}:preferences"
        data = self.redis.get_json(key)

        if data:
            return UserPreferences(**data)
        else:
            # Return defaults
            return UserPreferences(user_id=user_id)

    def update_user_preferences(self, preferences: UserPreferences):
        """Update user preferences"""
        key = f"user:{preferences.user_id}:preferences"
        self.redis.set_json(key, preferences.model_dump())  # No TTL

    # ========== Workflow State Caching ==========

    def cache_workflow_state(
        self,
        session_id: str,
        workflow_state: Dict[str, Any],
        ttl: int = 3600  # 1 hour
    ):
        """Cache workflow state"""
        state = WorkflowStateCache(
            session_id=session_id,
            **workflow_state
        )

        key = f"session:{session_id}:workflow_state"
        self.redis.set_json(key, state.model_dump(), ttl=ttl)

    def get_workflow_state(self, session_id: str) -> Optional[WorkflowStateCache]:
        """Get cached workflow state"""
        key = f"session:{session_id}:workflow_state"
        data = self.redis.get_json(key)

        if data:
            return WorkflowStateCache(**data)
        return None

    def update_workflow_stage(
        self,
        session_id: str,
        stage: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """Update workflow stage"""
        state = self.get_workflow_state(session_id)

        if state:
            state.current_stage = stage
            if stage not in state.completed_stages:
                state.completed_stages.append(stage)

            # Store stage-specific result
            if result:
                setattr(state, f"{stage}_result", result)

            state.last_updated = datetime.now()

            key = f"session:{session_id}:workflow_state"
            self.redis.set_json(key, state.model_dump(), ttl=3600)

    # ========== Agent Decision History ==========

    def add_agent_decision(
        self,
        session_id: str,
        decision: AgentDecision
    ):
        """Record agent decision"""
        key = f"session:{session_id}:agent_decisions"
        self.redis.rpush(key, decision.model_dump_json())
        self.redis.expire(key, 7*24*3600)  # 7 days

    def get_agent_decisions(self, session_id: str) -> List[AgentDecision]:
        """Get agent decision history"""
        key = f"session:{session_id}:agent_decisions"
        decisions_json = self.redis.lrange(key)

        decisions = []
        for dec_json in decisions_json:
            try:
                import json
                dec_dict = json.loads(dec_json)
                decisions.append(AgentDecision(**dec_dict))
            except Exception:
                continue

        return decisions

    # ========== Cache Management ==========

    def cache_discovery_result(
        self,
        session_id: str,
        result: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ):
        """Cache discovery result"""
        key = f"session:{session_id}:discovery_cache"
        self.redis.set_json(key, result, ttl=ttl)

    def get_cached_discovery(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached discovery result"""
        key = f"session:{session_id}:discovery_cache"
        return self.redis.get_json(key)

    def cache_test_plan(
        self,
        session_id: str,
        plan: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ):
        """Cache test plan"""
        key = f"session:{session_id}:plan_cache"
        self.redis.set_json(key, plan, ttl=ttl)

    def get_cached_test_plan(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached test plan"""
        key = f"session:{session_id}:plan_cache"
        return self.redis.get_json(key)

    def cache_test_generation(
        self,
        session_id: str,
        generation: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ):
        """Cache test generation result"""
        key = f"session:{session_id}:generation_cache"
        self.redis.set_json(key, generation, ttl=ttl)

    def get_cached_generation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached test generation result"""
        key = f"session:{session_id}:generation_cache"
        return self.redis.get_json(key)

    def cache_test_execution(
        self,
        session_id: str,
        execution: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ):
        """Cache test execution result"""
        key = f"session:{session_id}:execution_cache"
        self.redis.set_json(key, execution, ttl=ttl)

    def get_cached_execution(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached test execution result"""
        key = f"session:{session_id}:execution_cache"
        return self.redis.get_json(key)

    # Alias methods for backward compatibility
    def get_cached_planning(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_cached_test_plan"""
        return self.get_cached_test_plan(session_id)

    # ========== Statistics ==========

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        session = self.get_session(session_id)
        workflow = self.get_workflow_state(session_id)
        decisions = self.get_agent_decisions(session_id)

        return {
            "session_id": session_id,
            "user_id": session.user_id if session else None,
            "created_at": session.created_at if session else None,
            "last_active": session.last_active if session else None,
            "execution_mode": session.execution_mode if session else None,
            "current_stage": workflow.current_stage if workflow else None,
            "completed_stages": workflow.completed_stages if workflow else [],
            "total_decisions": len(decisions),
            "has_cached_discovery": self.get_cached_discovery(session_id) is not None,
            "has_cached_plan": self.get_cached_test_plan(session_id) is not None,
            "has_cached_generation": self.get_cached_generation(session_id) is not None,
            "has_cached_execution": self.get_cached_execution(session_id) is not None,
        }
