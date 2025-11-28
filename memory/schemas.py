"""
Pydantic schemas for Redis data structures
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles for multi-user support"""
    ADMIN = "admin"
    TESTER = "tester"
    VIEWER = "viewer"


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message"""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionMetadata(BaseModel):
    """Session metadata"""
    session_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    execution_mode: str = "interactive"  # "interactive" or "autonomous"
    app_profile_name: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPreferences(BaseModel):
    """User preferences"""
    user_id: str
    default_mode: str = "interactive"
    default_framework: str = "playwright"
    default_headless: bool = True
    notification_enabled: bool = True
    favorite_frameworks: List[str] = Field(default_factory=lambda: ["playwright"])
    theme: str = "light"


class AgentDecision(BaseModel):
    """Agent decision record"""
    user_request: str
    agent_reasoning: str
    agents_invoked: List[str]
    outcome: str  # "success", "failed", "partial"
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowStateCache(BaseModel):
    """Cached workflow state"""
    session_id: str
    current_stage: str
    completed_stages: List[str] = Field(default_factory=list)
    discovery_result: Optional[Dict[str, Any]] = None
    planning_result: Optional[Dict[str, Any]] = None
    generation_result: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    app_profile: Optional[Dict[str, Any]] = None
    feature_description: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
