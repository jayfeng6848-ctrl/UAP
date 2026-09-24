"""Action resolution.

The canonical vocabulary is platform owned. An action outside it is rejected
outright rather than coerced, so a misspelling or a look-alike character can
never slip past as a different action. Module extensions are not enabled yet
(the registry is still a proposal), so this resolver accepts the canonical set
only.
"""

from __future__ import annotations

from core.permission import Action
from core.permission.vocabulary import ACTIONS, normalize_action

from .errors import ActionResolutionError


class ActionResolver:
    """Validate and normalise an action into its canonical form."""

    def __init__(self, extra_actions: tuple[str, ...] = ()) -> None:
        self._allowed = frozenset(ACTIONS) | frozenset(
            normalize_action(a) for a in extra_actions
        )

    @property
    def allowed(self) -> frozenset[str]:
        return self._allowed

    def resolve(self, action: Action | str, resource_type: str = "") -> Action:
        try:
            name = normalize_action(action.name if isinstance(action, Action) else action)
        except TypeError as exc:
            raise ActionResolutionError("action must be a string") from exc

        if name not in self._allowed:
            raise ActionResolutionError(f"non-canonical action {name!r}")

        resource = action.resource_type if isinstance(action, Action) else resource_type
        return Action(name=name, resource_type=resource)

    def is_canonical(self, action: Action | str) -> bool:
        try:
            return self.resolve(action).name in ACTIONS
        except ActionResolutionError:
            return False


__all__ = ["ActionResolver"]
