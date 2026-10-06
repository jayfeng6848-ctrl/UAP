"""Company Domain manifest.

Activated by ``P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION`` (PDL Appendix AF):
the domain is no longer a placeholder — its contract surface exists under this
package and its two business tables are owned by migration ``0019_p20_company``.

The manifest declares metadata only. It carries no logic, no persistence and no
authorization; ``core_dependencies`` names the core contracts this domain is
allowed to rely on (``assignment`` is a business assignment, **not** a membership,
so ``core.membership`` is deliberately not declared).
"""

from __future__ import annotations

DOMAIN_MANIFEST: dict[str, object] = {
    "domain_id": "company",
    "domain_name": "Company Domain",
    "version": "0.1.0",
    "status": "active",
    "core_dependencies": ["core.tenant", "core.space"],
    # The 11 Company permission keys frozen by migration 0019 (canonical 12
    # actions; no new action, no new ACL subject type).
    "permissions": [
        "company_employee.read",
        "company_employee.list",
        "company_employee.create",
        "company_employee.update",
        "company_employee.delete",
        "company_employee.admin",
        "company_assignment.read",
        "company_assignment.list",
        "company_assignment.create",
        "company_assignment.update",
        "company_assignment.delete",
    ],
    "tables": ["company_employees", "company_assignments"],
    # Orchestration lives in the service layer (domains may not import it).
    "entrypoints": ["services.company.use_cases"],
}


def get_manifest() -> dict[str, object]:
    """Return the manifest. Nothing else exists in this domain yet."""
    return dict(DOMAIN_MANIFEST)


__all__ = ["DOMAIN_MANIFEST", "get_manifest"]
