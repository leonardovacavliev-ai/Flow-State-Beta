"""
Database adapters for analytics storage.

Supports both SQLite (local development) and PostgreSQL (cloud deployment).
"""

from .base import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgresAdapter
from .db_manager import get_database_adapter

__all__ = [
    'DatabaseAdapter',
    'SQLiteAdapter',
    'PostgresAdapter',
    'get_database_adapter'
]
