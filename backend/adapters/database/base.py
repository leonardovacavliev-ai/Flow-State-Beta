"""
Base interface for database adapters.

All database implementations must inherit from DatabaseAdapter.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class DatabaseAdapter(ABC):
    """Abstract base class for analytics database operations."""

    @abstractmethod
    def initialize(self):
        """Initialize database schema (create tables if needed)."""
        pass

    @abstractmethod
    def close(self):
        """Close database connection."""
        pass

    # Session operations
    @abstractmethod
    def create_session(self, session_id: str, ip_address: str, country: str) -> int:
        """Create a new session record."""
        pass

    @abstractmethod
    def end_session(self, session_id: str, duration_seconds: int):
        """Mark a session as ended."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        pass

    # Message operations
    @abstractmethod
    def log_message(self, session_id: str, role: str, message: str,
                   esp_name: Optional[str] = None, response_time: Optional[float] = None):
        """Log a chat message."""
        pass

    # ESP selection operations
    @abstractmethod
    def log_esp_selection(self, session_id: str, esp_name: str):
        """Log ESP selection."""
        pass

    # Feedback operations
    @abstractmethod
    def log_feedback(self, session_id: str, rating: int, comment: Optional[str] = None):
        """Log user feedback."""
        pass

    # Analytics queries
    @abstractmethod
    def get_analytics_summary(self, time_range: str) -> Dict[str, Any]:
        """
        Get analytics summary for dashboard.

        Args:
            time_range: '24h', '7d', '30d', or 'all'

        Returns:
            Dictionary with metrics:
            - total_sessions
            - total_messages
            - unique_users (by IP)
            - avg_session_duration
            - avg_messages_per_session
            - esp_breakdown
            - country_breakdown
            - feedback_stats
            - daily_sparklines
        """
        pass

    @abstractmethod
    def get_sessions_list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of recent sessions."""
        pass

    @abstractmethod
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        pass

    # Data management
    @abstractmethod
    def delete_old_data(self, days: int):
        """Delete data older than specified days."""
        pass

    @abstractmethod
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics (size, row counts, etc)."""
        pass
