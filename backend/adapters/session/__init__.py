"""
Session storage adapters for conversation history.

Supports both in-memory (local dev) and Redis (cloud production) backends.
"""

from .base import SessionAdapter
from .memory_adapter import MemorySessionAdapter
from .redis_adapter import RedisSessionAdapter
from .session_manager import get_session_adapter

__all__ = [
    'SessionAdapter',
    'MemorySessionAdapter',
    'RedisSessionAdapter',
    'get_session_adapter',
]
