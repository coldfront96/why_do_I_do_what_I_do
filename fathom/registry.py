"""A hash-keyed handler registry.

Opcode handlers do not look each other up by name at runtime; they are keyed
by the fingerprint of their canonical name. This lets the bytecode reference
operations by a compact integer code (see :mod:`fathom.compiler`) without the
machine carrying a human-readable opcode table, and it keeps the dispatch
table stable even if a handler is renamed in source (only its registered
canonical name matters).
"""

from __future__ import annotations

from typing import Callable, Dict

from .hashing import fingerprint

# Salt namespace for opcode identity. Distinct from rollout salts so opcode
# fingerprints never collide with bucketing fingerprints.
_OPSALT = "isa.v2"

_HANDLERS: Dict[int, Callable] = {}
_CANON: Dict[int, str] = {}


def opcode(name: str):
    """Register a handler under the fingerprint of its canonical ``name``."""
    key = fingerprint(name, _OPSALT)

    def _register(fn: Callable) -> Callable:
        _HANDLERS[key] = fn
        _CANON[key] = name
        return fn

    return _register


def key_for(name: str) -> int:
    return fingerprint(name, _OPSALT)


def names() -> list:
    """The canonical names of every registered operation, unordered."""
    return list(_CANON.values())


def resolve(key: int) -> Callable:
    try:
        return _HANDLERS[key]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"no handler registered for opcode key {key}") from exc


def canonical(key: int) -> str:
    return _CANON.get(key, f"op#{key}")
