"""UAP service layer.

Services orchestrate domain rules over core contracts and infrastructure
adapters, and they are the only layer allowed to own business persistence.

Dependency direction (enforced by tests/architecture):
    apps -> agent -> services -> intelligence -> core -> infrastructure
    domains  attach sideways and may only depend on core.
"""

__all__: list[str] = []
