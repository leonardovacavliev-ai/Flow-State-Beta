"""
Base interface for session storage adapters.

All session adapters must implement this interface to provide
conversation history management with consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class SessionAdapter(ABC):
    """Abstract base class for session storage backends."""

    @abstractmethod
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries with 'role' and 'content' keys.
            Returns empty list if session not found.

        Example:
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        """
        pass

    @abstractmethod
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            session_id: Unique session identifier
            role: Message role ('user' or 'assistant')
            content: Message content text
        """
        pass

    @abstractmethod
    def clear_history(self, session_id: str) -> None:
        """
        Clear all conversation history for a session.

        Args:
            session_id: Unique session identifier
        """
        pass

    @abstractmethod
    def set_ttl(self, session_id: str, ttl_seconds: int) -> None:
        """
        Set expiration time for session data.

        Args:
            session_id: Unique session identifier
            ttl_seconds: Time-to-live in seconds

        Note:
            In-memory adapter may ignore this (no persistence).
            Redis adapter uses this to auto-expire sessions.
        """
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Unique session identifier

        Returns:
            True if session has data, False otherwise
        """
        pass

    @abstractmethod
    def get_all_session_ids(self) -> List[str]:
        """
        Get list of all active session IDs.

        Returns:
            List of session ID strings

        Note:
            Used for debugging/admin purposes.
            May be slow for large-scale production systems.
        """
        pass
