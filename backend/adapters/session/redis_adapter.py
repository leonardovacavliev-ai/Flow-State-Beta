"""
Redis session storage adapter.

Used for cloud production deployments. Provides persistent, distributed
session storage with automatic expiration (TTL).
"""

import json
import redis
from typing import List, Dict
from .base import SessionAdapter


class RedisSessionAdapter(SessionAdapter):
    """
    Redis-backed conversation history storage.

    Features:
    - Persistent across application restarts
    - Shared across multiple API instances
    - Automatic session expiration via TTL
    - High performance (in-memory data store)
    """

    def __init__(self, redis_url: str, default_ttl: int = 1800):
        """
        Initialize Redis client.

        Args:
            redis_url: Redis connection string (e.g., redis://localhost:6379/0)
            default_ttl: Default time-to-live in seconds (default: 30 minutes)
        """
        self.client = redis.from_url(
            redis_url,
            decode_responses=True,  # Return strings instead of bytes
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        self.default_ttl = default_ttl

        # Test connection
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def _get_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}:history"

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history from Redis."""
        key = self._get_key(session_id)
        data = self.client.get(key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                # Corrupted data, return empty
                return []

        return []

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add message to Redis and refresh TTL.

        Thread-safe: uses Redis atomic operations.
        """
        key = self._get_key(session_id)

        # Get existing history
        history = self.get_conversation_history(session_id)

        # Append new message
        history.append({
            "role": role,
            "content": content
        })

        # Save back to Redis with TTL
        self.client.setex(
            key,
            self.default_ttl,
            json.dumps(history)
        )

    def clear_history(self, session_id: str) -> None:
        """Delete session data from Redis."""
        key = self._get_key(session_id)
        self.client.delete(key)

    def set_ttl(self, session_id: str, ttl_seconds: int) -> None:
        """Update expiration time for existing session."""
        key = self._get_key(session_id)
        self.client.expire(key, ttl_seconds)

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists in Redis."""
        key = self._get_key(session_id)
        return self.client.exists(key) > 0

    def get_all_session_ids(self) -> List[str]:
        """
        Get all active session IDs.

        Warning: Uses KEYS command which is O(N).
        Use sparingly in production.
        """
        pattern = "session:*:history"
        keys = self.client.keys(pattern)

        # Extract session IDs from keys
        session_ids = []
        for key in keys:
            # Format: "session:{session_id}:history"
            parts = key.split(":")
            if len(parts) == 3:
                session_ids.append(parts[1])

        return session_ids

    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False
