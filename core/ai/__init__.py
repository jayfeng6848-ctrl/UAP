"""AI routing contracts (P16-D03 / D04).

Pure decision shapes only: the routing *result* has a frozen shape, while the
transport, credentials and vendor details stay outside ``core``.
"""

from .routing import RouteDecision, RouteRequest

__all__ = ["RouteDecision", "RouteRequest"]
