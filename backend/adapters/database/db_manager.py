"""
Database manager - Factory for creating database adapters.

Automatically selects the correct adapter based on DATABASE_PROVIDER environment variable.
"""

import os
from typing import Optional

from .base import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgresAdapter


def get_database_adapter(provider: Optional[str] = None) -> DatabaseAdapter:
    """
    Get the appropriate database adapter based on configuration.

    Args:
        provider: Database provider ('sqlite' or 'postgres').
                 If None, reads from DATABASE_PROVIDER environment variable.
                 Defaults to 'sqlite' if not specified.

    Returns:
        DatabaseAdapter instance (SQLiteAdapter or PostgresAdapter)

    Raises:
        ValueError: If provider is invalid or required configuration is missing

    Environment Variables:
        DATABASE_PROVIDER: 'sqlite' or 'postgres' (default: 'sqlite')
        DATABASE_URL: PostgreSQL connection string (required for postgres)

    Examples:
        # Use environment variable (recommended)
        db = get_database_adapter()

        # Override provider
        db = get_database_adapter('postgres')
    """
    if provider is None:
        provider = os.environ.get('DATABASE_PROVIDER', 'sqlite').lower()

    print(f"📊 Initializing {provider.upper()} database adapter...")

    if provider == 'sqlite':
        db_path = os.environ.get('SQLITE_DB_PATH')
        adapter = SQLiteAdapter(db_path=db_path)

    elif provider == 'postgres' or provider == 'postgresql':
        connection_url = os.environ.get('DATABASE_URL')
        if not connection_url:
            raise ValueError(
                "DATABASE_URL environment variable is required for PostgreSQL.\n"
                "Example: postgresql://user:password@host:port/database"
            )
        adapter = PostgresAdapter(connection_url=connection_url)

    else:
        raise ValueError(
            f"Invalid DATABASE_PROVIDER: '{provider}'. "
            f"Must be 'sqlite' or 'postgres'."
        )

    # Initialize database schema
    adapter.initialize()

    return adapter


# Global adapter instance (lazy-loaded)
_adapter_instance: Optional[DatabaseAdapter] = None


def get_adapter() -> DatabaseAdapter:
    """
    Get the global database adapter instance (singleton pattern).

    Creates the adapter on first call, then reuses it.
    Useful for ensuring consistent database connection throughout the app.

    Returns:
        DatabaseAdapter instance
    """
    global _adapter_instance

    if _adapter_instance is None:
        _adapter_instance = get_database_adapter()

    return _adapter_instance


def reset_adapter():
    """
    Reset the global adapter instance.

    Useful for testing or when switching database providers at runtime.
    """
    global _adapter_instance

    if _adapter_instance:
        _adapter_instance.close()
        _adapter_instance = None
