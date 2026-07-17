"""
In-memory session storage adapter.

Used for local development. All data is lost when the application restarts.
Not suitable for production with multiple API instances.
"""

from typing import List, Dict
from threading import Lock
from .base import SessionAdapter


class MemorySessionAdapter(SessionAdapter):
    """
    In-memory conversation history storage.

    Thread-safe for single-process applications.
    Data persists only during application runtime.
    """

    def __init__(self):
        """Initialize with empty storage."""
        self._storage: Dict[str, List[Dict[str, str]]] = {}
        self._lock = Lock()

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history from in-memory storage."""
        with self._lock:
            return self._storage.get(session_id, []).copy()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add message to in-memory storage."""
        with self._lock:
            if session_id not in self._storage:
                self._storage[session_id] = []

            self._storage[session_id].append({
                "role": role,
                "content": content
            })

    def clear_history(self, session_id: str) -> None:
        """Clear conversation history from memory."""
        with self._lock:
            if session_id in self._storage:
                del self._storage[session_id]

    def set_ttl(self, session_id: str, ttl_seconds: int) -> None:
        """
        TTL is not implemented for in-memory storage.

        Data expires when the application restarts.
        In production, use RedisSessionAdapter for TTL support.
        """
        pass  # No-op for memory adapter

    def session_exists(self, session_id: str) -> bool:
        """Check if session has any messages."""
        with self._lock:
            return session_id in self._storage and len(self._storage[session_id]) > 0

    def get_all_session_ids(self) -> List[str]:
        """Get list of all session IDs in memory."""
        with self._lock:
            return list(self._storage.keys())
