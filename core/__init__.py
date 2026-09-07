"""UAP Platform Core.

Business-agnostic foundation.

Dependency rule (enforced by tests/architecture):
    domains -> core        OK
    core    -> domains     FORBIDDEN
"""

__version__ = "0.1.0"

CORE_MODULES = (
    "identity",
    "auth",
    "tenant",
    "space",
    "membership",
    "permission",
    "device",
    "session",
    "policy",
    "event",
    "audit",
    "resource",
)
