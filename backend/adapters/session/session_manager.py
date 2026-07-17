"""
Factory function for session adapters.

Instantiates the correct adapter based on SESSION_PROVIDER environment variable.
"""

import os
from typing import Optional
from .base import SessionAdapter
from .memory_adapter import MemorySessionAdapter
from .redis_adapter import RedisSessionAdapter


_session_adapter_instance: Optional[SessionAdapter] = None


def get_session_adapter() -> SessionAdapter:
    """
    Get or create session adapter instance (singleton pattern).

    Returns:
        SessionAdapter: Configured session storage adapter

    Environment Variables:
        SESSION_PROVIDER: 'memory' or 'redis' (default: 'memory')
        REDIS_URL: Redis connection string (required if SESSION_PROVIDER=redis)
        SESSION_TTL_SECONDS: Session expiration time (default: 1800 = 30 minutes)

    Raises:
        ValueError: If SESSION_PROVIDER is invalid or required config is missing
        ConnectionError: If Redis connection fails
    """
    global _session_adapter_instance

    # Return existing instance (singleton)
    if _session_adapter_instance is not None:
        return _session_adapter_instance

    # Get configuration
    provider = os.getenv('SESSION_PROVIDER', 'memory').lower()
    ttl = int(os.getenv('SESSION_TTL_SECONDS', '1800'))

    print(f"[SessionManager] Initializing session adapter: {provider}")

    # Create adapter based on provider
    if provider == 'memory':
        _session_adapter_instance = MemorySessionAdapter()
        print("[SessionManager] ✓ In-memory session storage initialized")

    elif provider == 'redis':
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            raise ValueError(
                "REDIS_URL environment variable is required when SESSION_PROVIDER=redis"
            )

        try:
            _session_adapter_instance = RedisSessionAdapter(
                redis_url=redis_url,
                default_ttl=ttl
            )
            print(f"[SessionManager] ✓ Redis session storage initialized (TTL: {ttl}s)")
        except Exception as e:
            print(f"[SessionManager] ✗ Redis connection failed: {e}")
            raise

    else:
        raise ValueError(
            f"Invalid SESSION_PROVIDER: {provider}. Must be 'memory' or 'redis'"
        )

    return _session_adapter_instance


def reset_session_adapter():
    """
    Reset singleton instance.

    Used for testing purposes to force re-initialization.
    """
    global _session_adapter_instance
    _session_adapter_instance = None
