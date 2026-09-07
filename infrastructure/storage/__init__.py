"""Storage package: contract only in STEP 0."""

from .interfaces import StorageClient, StorageNotConfiguredError, StoredObject

__all__ = ["StoredObject", "StorageClient", "StorageNotConfiguredError"]
