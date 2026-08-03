"""
Database manager - Factory for creating database adapters.

Automatically selects the correct adapter based on DATABASE_PROVIDER environment variable.
"""

import os
from typing import Optional
from dotenv import load_dotenv

from .base import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgresAdapter

# Load environment variables
load_dotenv()


# Global adapter instance (lazy-loaded)
_adapter_instance: Optional[DatabaseAdapter] = None


def _create_adapter(provider: Optional[str] = None) -> DatabaseAdapter:
    """Create and initialize a new database adapter instance."""
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


def get_database_adapter(provider: Optional[str] = None) -> DatabaseAdapter:
    """
    Get the database adapter (singleton for the default provider).

    Previously this created a NEW adapter (and a new connection pool, plus a
    full schema re-init) on every call — call sites invoke it per request and
    per scheduler tick, permanently leaking one Postgres connection each time.
    Now the default-provider adapter is created once and reused.

    Args:
        provider: Explicit provider override ('sqlite' or 'postgres').
                 When given, a fresh non-cached adapter is returned.

    Environment Variables:
        DATABASE_PROVIDER: 'sqlite' or 'postgres' (default: 'sqlite')
        DATABASE_URL: PostgreSQL connection string (required for postgres)
    """
    if provider is not None:
        return _create_adapter(provider)

    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = _create_adapter()
    return _adapter_instance


def get_adapter() -> DatabaseAdapter:
    """
    Get the global database adapter instance (singleton pattern).

    Creates the adapter on first call, then reuses it.
    Useful for ensuring consistent database connection throughout the app.

    Returns:
        DatabaseAdapter instance
    """
    return get_database_adapter()


def reset_adapter():
    """
    Reset the global adapter instance.

    Useful for testing or when switching database providers at runtime.
    """
    global _adapter_instance

    if _adapter_instance:
        _adapter_instance.close()
        _adapter_instance = None
