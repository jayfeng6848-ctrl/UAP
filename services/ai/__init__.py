"""AI orchestration services (P16-D03 / D04 / D07).

Provider selection, routing and credential resolution orchestration. Transport
and vendor details live in ``infrastructure.ai``; contracts live in
``core.ai`` / ``intelligence``.
"""

from .credentials import EnvSecretResolver, SecretResolver, SecretValue
from .gateway import AIGatewayService
from .routing import resolve_route

__all__ = ["AIGatewayService", "EnvSecretResolver", "SecretResolver", "SecretValue", "resolve_route"]
