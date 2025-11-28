"""
Conversation Memory with Redis Backend

Integrates with LangChain for persistent conversation history.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from memory.redis_manager import RedisManager, get_redis_manager
from memory.schemas import ChatMessage, MessageRole

try:
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class ConversationMemory:
    """
    Persistent conversation memory using Redis

    Stores conversation history and integrates with LangChain memory.
    """

    def __init__(
        self,
        session_id: str,
        redis_manager: Optional[RedisManager] = None,
        max_history: int = 100,
        ttl: int = 7 * 24 * 3600  # 7 days
    ):
        """
        Initialize conversation memory

        Args:
            session_id: Unique session identifier
            redis_manager: Redis manager instance
            max_history: Maximum messages to keep
            ttl: Time to live in seconds
        """
        self.session_id = session_id
        self.redis = redis_manager or get_redis_manager()
        self.max_history = max_history
        self.ttl = ttl
        self._key = f"session:{session_id}:conversations"

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Add message to conversation history

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Created message object
        """
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        # Serialize and push to Redis list
        message_json = message.model_dump_json()
        self.redis.rpush(self._key, message_json)

        # Trim to max history
        if self.redis.llen(self._key) > self.max_history:
            self.redis.ltrim(self._key, -self.max_history, -1)

        # Set TTL
        self.redis.expire(self._key, self.ttl)

        return message

    def add_user_message(self, content: str, **metadata) -> ChatMessage:
        """Add user message"""
        return self.add_message(MessageRole.USER, content, metadata)

    def add_assistant_message(self, content: str, **metadata) -> ChatMessage:
        """Add assistant message"""
        return self.add_message(MessageRole.ASSISTANT, content, metadata)

    def add_system_message(self, content: str, **metadata) -> ChatMessage:
        """Add system message"""
        return self.add_message(MessageRole.SYSTEM, content, metadata)

    def get_messages(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Get conversation messages

        Args:
            limit: Maximum messages to return (None = all)
            offset: Number of messages to skip from start

        Returns:
            List of chat messages
        """
        # Get from Redis
        end = -1 if limit is None else offset + limit - 1
        messages_json = self.redis.lrange(self._key, offset, end)

        # Deserialize
        messages = []
        for msg_json in messages_json:
            try:
                msg_dict = json.loads(msg_json)
                messages.append(ChatMessage(**msg_dict))
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error deserializing message: {e}")
                continue

        return messages

    def get_last_n_messages(self, n: int) -> List[ChatMessage]:
        """Get last N messages"""
        total = self.redis.llen(self._key)
        start = max(0, total - n)
        return self.get_messages(offset=start)

    def clear(self):
        """Clear conversation history"""
        self.redis.delete(self._key)

    def get_langchain_messages(self) -> List:
        """
        Convert to LangChain message format

        Returns:
            List of LangChain messages
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain not available")

        messages = self.get_messages()
        lc_messages = []

        for msg in messages:
            if msg.role == MessageRole.USER:
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                lc_messages.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM:
                lc_messages.append(SystemMessage(content=msg.content))

        return lc_messages

    def to_langchain_memory(self) -> Any:
        """
        Create LangChain ConversationBufferMemory from history

        Returns:
            LangChain memory object
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain not available")

        memory = ConversationBufferMemory(return_messages=True)

        # Load history into memory
        messages = self.get_messages()
        for msg in messages:
            if msg.role == MessageRole.USER:
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == MessageRole.ASSISTANT:
                memory.chat_memory.add_ai_message(msg.content)

        return memory

    def get_context_window(
        self,
        max_messages: int = 10,
        max_tokens: Optional[int] = None
    ) -> List[ChatMessage]:
        """
        Get recent messages for context window

        Args:
            max_messages: Maximum number of messages
            max_tokens: Maximum tokens (approximate by chars)

        Returns:
            Recent messages that fit in context
        """
        messages = self.get_last_n_messages(max_messages)

        if max_tokens:
            # Approximate token count (1 token ≈ 4 chars)
            total_chars = 0
            filtered = []

            for msg in reversed(messages):
                msg_chars = len(msg.content)
                if total_chars + msg_chars > max_tokens * 4:
                    break
                filtered.insert(0, msg)
                total_chars += msg_chars

            return filtered

        return messages

    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary"""
        messages = self.get_messages()

        return {
            "session_id": self.session_id,
            "total_messages": len(messages),
            "user_messages": sum(1 for m in messages if m.role == MessageRole.USER),
            "assistant_messages": sum(1 for m in messages if m.role == MessageRole.ASSISTANT),
            "first_message_time": messages[0].timestamp if messages else None,
            "last_message_time": messages[-1].timestamp if messages else None,
        }
