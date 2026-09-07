"""Domain placeholders.

STEP 0: manifests and documentation only. No business logic, no business tables.
Domains depend on core; core must never depend on a domain.
"""

from domains.business.manifest import DOMAIN_MANIFEST as BUSINESS_MANIFEST
from domains.company.manifest import DOMAIN_MANIFEST as COMPANY_MANIFEST
from domains.entertainment.manifest import DOMAIN_MANIFEST as ENTERTAINMENT_MANIFEST
from domains.family.manifest import DOMAIN_MANIFEST as FAMILY_MANIFEST

ALL_DOMAINS = (
    FAMILY_MANIFEST,
    COMPANY_MANIFEST,
    BUSINESS_MANIFEST,
    ENTERTAINMENT_MANIFEST,
)


def list_domains() -> tuple[dict[str, object], ...]:
    return ALL_DOMAINS


__all__ = ["ALL_DOMAINS", "list_domains"]
