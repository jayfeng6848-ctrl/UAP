"""Company Domain manifest.

Placeholder only. Declares what this domain will need; implements nothing.
"""

from __future__ import annotations

DOMAIN_MANIFEST: dict[str, object] = {
    "domain_id": "company",
    "domain_name": "Company Domain",
    "version": "0.0.0-placeholder",
    "status": "placeholder",
    "core_dependencies": list(('core.tenant', 'core.space', 'core.membership')),
    "permissions": list(('space:read', 'member:manage')),
    "tables": [],
    "entrypoints": [],
}


def get_manifest() -> dict[str, object]:
    """Return the manifest. Nothing else exists in this domain yet."""
    return dict(DOMAIN_MANIFEST)


__all__ = ["DOMAIN_MANIFEST", "get_manifest"]
