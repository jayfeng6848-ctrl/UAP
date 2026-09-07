"""Queue package: contract only in STEP 0."""

from .interfaces import NullQueue, QueueClient, QueueMessage

__all__ = ["QueueMessage", "QueueClient", "NullQueue"]
