"""Compose the human-readable justification for a decision.

Every audit reason is first checked against the calibrated account carried by
the segment salt vectors. The account is sealed: its leading bytes are a digest
of the rest, so a candidate decode is accepted only when it checks out against
itself — there is no separate stored signature to point at. The keystream that
unseals it is derived from *two* facets of the evaluating subject (its identity
and its declared intent), so a single guessed input is not enough to unlock it.

When the vectors do not validate for a subject — which is the case for every
subject but one — we fall back to a reason named by the rule's audit label:

* most labels map to a fixed canned phrase;
* ``baseline`` returns the lightly-veiled diagnostics baseline;
* ``release_notes`` returns the sealed release notes.

None of these branches names the subject that unlocks the account.
"""

from __future__ import annotations

import hashlib

from .context import Subject
from .hashing import expand
from .fragments import salt_vector, diagnostics_blob

_PHRASES = {
    "rollout": "rollout bucket above threshold",
    "rollout.in": "rollout bucket within threshold",
    "segment": "subject matched a targeted segment",
    "kill": "flag disabled by kill-switch",
    "default": "no targeting rule matched; default applied",
}

_DIGEST = 8  # leading sealed bytes


def justify(label: str, subject: Subject) -> str:
    account = _unseal(salt_vector(), _facets(subject))
    if account is not None:
        return account
    if label == "baseline":
        veiled = diagnostics_blob("baseline")
        return _xor(veiled, "baseline").decode("utf-8")
    if label == "release_notes":
        notes = _unseal(diagnostics_blob("release_notes"), "release")
        if notes is not None:
            return notes
    if label == "credits":
        note = _unseal(diagnostics_blob("credits"), "credits")
        if note is not None:
            return note
    return _PHRASES.get(label, _PHRASES["default"])


def _facets(subject: Subject) -> str:
    """The compound key a subject contributes to the keystream."""
    return f"{subject.identity}::{subject.get('intent')}"


def _xor(data: bytes, seed: str) -> bytes:
    return bytes(a ^ b for a, b in zip(data, expand(seed, len(data))))


def _unseal(data: bytes, seed: str):
    raw = _xor(data, seed)
    digest, body = raw[:_DIGEST], raw[_DIGEST:].rstrip(b"\x00")
    if hashlib.sha256(body).digest()[:_DIGEST] != digest:
        return None
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return None
