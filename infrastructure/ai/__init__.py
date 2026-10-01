"""AI transport adapters (P16-D03 / D07).

The only place where vendor/transport detail and credential unwrapping may live.
No module outside ``infrastructure`` may import a provider SDK or read an API key.
"""

from .adapters import (
    EchoAdapter,
    OpenAICompatibleAdapter,
    http_json_transport,
    register_default_adapters,
)

__all__ = [
    "EchoAdapter",
    "OpenAICompatibleAdapter",
    "http_json_transport",
    "register_default_adapters",
]
