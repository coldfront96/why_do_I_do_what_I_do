"""Deterministic hashing primitives used for bucketing and salting.

Feature-flag rollouts need a *stable, uniform* mapping from a subject to a
bucket in ``[0, 100)`` so that a given user consistently lands in (or out of)
an experiment. We derive that mapping from SHA-256 so it is uniform, salted
per-flag (to decorrelate overlapping experiments), and reproducible across
language runtimes.

The same primitives are reused wherever the engine needs a deterministic
byte stream keyed by a string — for example to expand a per-segment salt
vector to an arbitrary length. Keeping a single implementation here means the
bucketing maths can never drift between call sites.
"""

from __future__ import annotations

import hashlib


def _digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def fingerprint(subject: str, salt: str = "") -> int:
    """Return a stable 64-bit fingerprint for ``subject`` under ``salt``.

    The salt namespaces the fingerprint so that two flags rolling out to the
    same population do not correlate. Only the leading 8 bytes of the digest
    are used; that is ample entropy for bucket assignment.
    """
    return int.from_bytes(_digest(f"{salt}:{subject}".encode())[:8], "big")


def bucket(subject: str, salt: str = "") -> int:
    """Map ``subject`` to a rollout bucket in ``[0, 100)``."""
    return fingerprint(subject, salt) % 100


def expand(seed: str, length: int) -> bytes:
    """Expand ``seed`` into ``length`` deterministic bytes.

    Used to stretch a fixed-size salt into a vector long enough to cover a
    segment's membership table. Implemented as plain counter-mode hashing so
    the output is stable and uniformly distributed.
    """
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += _digest(f"{seed}#{counter}".encode())
        counter += 1
    return bytes(out[:length])
