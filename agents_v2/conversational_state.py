"""
Extended State Schemas for Conversational Orchestrator

Adds conversation context and reasoning tracking to existing states.
"""

from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime

from agents_v2.state import OrchestratorState


class ConversationalState(OrchestratorState, total=False):
    """
    Extended orchestrator state with conversation context

    Adds conversation-specific fields to track user intent,
    reasoning steps, and multi-turn interactions.
    """
    # Conversation context
    conversation_id: str
    user_intent: Optional[str]  # Parsed user intent
    original_request: str  # Original user message

    # Reasoning and decision making
    reasoning_steps: List[str]  # Step-by-step reasoning
    agent_selection_rationale: Optional[str]  # Why specific agents chosen
    clarification_needed: bool  # Whether to ask user questions
    clarification_questions: List[str]  # Questions to ask user

    # Multi-turn conversation
    conversation_history: List[Dict[str, Any]]  # Recent messages
    context_summary: Optional[str]  # Summarized context from history

    # User preferences and learning
    user_preferences: Dict[str, Any]  # Learned preferences
    similar_past_requests: List[Dict[str, Any]]  # Similar previous requests

    # Interactive mode specific
    awaiting_approval: bool  # Waiting for user approval
    approval_stage: Optional[str]  # Which stage needs approval
    suggested_action: Optional[Dict[str, Any]]  # Suggested next action

    # Execution mode
    execution_mode: str  # "interactive" or "autonomous"

    # Session tracking
    session_id: str
    user_id: Optional[str]


class IntentClassification(TypedDict, total=False):
    """
    Parsed user intent classification
    """
    intent_type: str  # "discovery", "planning", "generation", "execution", "report", "question"
    confidence: float  # 0.0 to 1.0
    entities: Dict[str, Any]  # Extracted entities (URL, feature name, etc.)
    requires_clarification: bool
    missing_information: List[str]


class ReasoningStep(TypedDict, total=False):
    """
    Single reasoning step
    """
    step_number: int
    thought: str  # What the agent is thinking
    action: Optional[str]  # What action to take
    observation: Optional[str]  # What was observed
    timestamp: datetime
