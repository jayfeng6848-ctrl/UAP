"""Infrastructure adapters.

This layer owns everything that talks to the outside world: database, cache,
queue, object storage, logging and metrics. Core logic depends on the
*interfaces* defined here, never on a concrete vendor SDK.
"""

__all__ = ["database", "cache", "queue", "storage", "logging", "monitoring"]
