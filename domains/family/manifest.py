"""Family Domain manifest.

Placeholder only. Declares what this domain will need; implements nothing.
"""

from __future__ import annotations

DOMAIN_MANIFEST: dict[str, object] = {
    "domain_id": "family",
    "domain_name": "Family Domain",
    "version": "0.0.0-placeholder",
    "status": "placeholder",
    "core_dependencies": list(('core.space', 'core.membership')),
    "permissions": list(('space:read', 'membership:read')),
    "tables": [],
    "entrypoints": [],
}


def get_manifest() -> dict[str, object]:
    """Return the manifest. Nothing else exists in this domain yet."""
    return dict(DOMAIN_MANIFEST)


__all__ = ["DOMAIN_MANIFEST", "get_manifest"]
