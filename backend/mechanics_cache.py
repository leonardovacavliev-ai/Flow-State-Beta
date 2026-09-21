"""
Store behind the Query B (platform-mechanics) memoization.

This lives outside app.py so the admin route modules and the crawl worker can
invalidate the cache after they change what is in the vector database. They
cannot import app.py to do it: app.py imports and registers them at startup,
so the dependency only runs one way.

The retrieval logic itself stays in app.py. This module owns three things and
nothing else: the dict, the lock that guards it, and the TTL.

Scope: one process. Each gunicorn worker keeps its own copy, so a mutation
served by one worker leaves the other workers to expire on the TTL.
"""

import os
import threading
import time

# TTL exists so a re-crawl propagates without a restart; negative results are
# cached too, since the ESPs with no mechanics documentation are exactly the
# ones that were paying the full cost for nothing.
MECHANICS_CACHE_TTL_SECONDS = int(os.environ.get('MECHANICS_CACHE_TTL_SECONDS', '900'))

_mechanics_cache = {}
_mechanics_cache_lock = threading.Lock()


def get_cached_mechanics(cache_key):
    """Return the memoized results for this key, or None if absent or stale.

    None means "miss": a cached-but-empty result set is a dict, not None, so
    negative results still count as hits.
    """
    now = time.time()
    with _mechanics_cache_lock:
        cached = _mechanics_cache.get(cache_key)
        if cached and now - cached[0] < MECHANICS_CACHE_TTL_SECONDS:
            return cached[1]
    return None


def cache_mechanics_results(cache_key, results, fetched_at):
    """Memoize results under this key.

    fetched_at is the caller's timestamp from before the search ran, so the
    TTL is measured from when the miss started rather than when it finished.
    """
    with _mechanics_cache_lock:
        _mechanics_cache[cache_key] = (fetched_at, results)


def clear_mechanics_cache():
    """Drop memoized Query B results. Call after changing an ESP's vectors."""
    with _mechanics_cache_lock:
        _mechanics_cache.clear()
    print("[MECHANICS CACHE] cleared")
