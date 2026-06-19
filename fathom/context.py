"""The subject context evaluated against flag rules.

A :class:`Subject` is just a frozen bag of attributes (``user_id``, ``plan``,
``country``, …) plus the identity string used for bucketing. Rules read
attributes by name; missing attributes evaluate to ``None`` rather than
raising, so partially-populated contexts degrade gracefully.
"""

from __future__ import annotations

from typing import Any, Mapping


class Subject:
    __slots__ = ("_attrs", "_identity")

    def __init__(self, attrs: Mapping[str, Any] | None = None, *, identity: str | None = None):
        self._attrs = dict(attrs or {})
        # The identity used for bucketing defaults to ``user_id`` so that a
        # subject buckets consistently even if the caller forgets to set one.
        self._identity = identity or str(self._attrs.get("user_id", ""))

    @classmethod
    def coerce(cls, value: "Subject | Mapping[str, Any]") -> "Subject":
        return value if isinstance(value, cls) else cls(value)

    @property
    def identity(self) -> str:
        return self._identity

    def get(self, name: str) -> Any:
        if name == "@identity":
            return self._identity
        return self._attrs.get(name)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Subject({self._attrs!r}, identity={self._identity!r})"
