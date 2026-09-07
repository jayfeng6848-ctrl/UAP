"""Cache package.

Only the interface exists in STEP 0. See :mod:`infrastructure.cache.interfaces`.
"""

from .interfaces import CacheClient, CacheNotConfiguredError, NullCache

__all__ = ["CacheClient", "CacheNotConfiguredError", "NullCache"]
