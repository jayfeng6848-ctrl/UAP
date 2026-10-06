"""Domain-facing Intelligence Facade (OQ-CUI-03 / OQ-CUI-09 · PDL Appendix AP).

This package owns **orchestration only**: it derives the authorized context from
the authenticated session, reads Company data through the existing Company service
use cases (never SQL, never the repository), and hands the request to the existing
AI runtime / gateway. It is not a second AI engine, gateway or authorization engine.
"""

from .facade import ErrorCode, IntelligenceError, confirm_proposal, run_copilot
from .proposal import PROPOSAL_TTL_SECONDS, EphemeralProposal, proposal_store

__all__ = [
    "EphemeralProposal",
    "ErrorCode",
    "IntelligenceError",
    "PROPOSAL_TTL_SECONDS",
    "confirm_proposal",
    "proposal_store",
    "run_copilot",
]
