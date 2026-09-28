"""Runtime infrastructure for the P14 Runtime Slice (Wave 1).

This package holds process-level runtime concerns that are **not** database
internals:

* :mod:`infrastructure.runtime.errors`   -- error taxonomy (security failures
  must never be confused with transient failures, and secrets must never reach
  the message text)
* :mod:`infrastructure.runtime.retry`    -- bounded retry for idempotent
  infrastructure operations only
* :mod:`infrastructure.runtime.lifecycle`-- explicit startup/shutdown lifecycle

Deliberately, this ``__init__`` re-exports nothing: ``infrastructure.database``
imports the error taxonomy, and re-exporting here would create an import cycle.
Import the submodules explicitly.
"""

__all__: list[str] = []
