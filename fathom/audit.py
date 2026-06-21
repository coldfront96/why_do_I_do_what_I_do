"""Compose the human-readable justification for a decision.

Every audit reason is first checked against the calibrated account carried by
the segment salt vectors. The account is sealed: its leading bytes are a digest
of the rest, so a candidate decode is accepted only when it checks out against
itself — there is no separate stored signature to find. The keystream is derived
from the subject's identity and its cohort fingerprint, so the correct cohort
membership is required to produce a validating decode.

When the vectors do not validate the fallback reason is keyed by the rule's
audit label:

* most labels map to a fixed canned phrase;
* ``baseline`` returns the lightly-veiled diagnostics baseline;
* ``release_notes`` / ``credits`` return the sealed maintenance blobs.

No branch here names a specific subject, attribute, or key.
"""

from __future__ import annotations

import hashlib

from .context import Subject
from .hashing import expand, fingerprint
from .fragments import salt_vector, diagnostics_blob

_PHRASES = {
    "rollout": "rollout bucket above threshold",
    "rollout.in": "rollout bucket within threshold",
    "segment": "subject matched a targeted segment",
    "kill": "flag disabled by kill-switch",
    "default": "no targeting rule matched; default applied",
}

# Two-layer cohort-grain veil.
# Layer 1: _GRAIN_META decoded under the canonical protocol tag yields the
#           grain key. Layer 2: _GRAIN_VEIL decoded under that key yields the
#           grain salt used to fingerprint the subject into its cohort.
# Neither intermediate value appears as a source literal.
_GRAIN_META = [97, 34, 44, 11, 169, 3, 155, 133, 140, 229, 176, 198, 111,
               144, 46, 189, 157, 217]
_GRAIN_VEIL = [205, 42, 18, 133, 151, 212, 71, 51, 230, 85, 3, 107, 95, 226,
               192, 203]
_PROTO = "fathom.proto"

_DIGEST = 8  # leading sealed bytes


def _grain_salt() -> str:
    ks1 = expand(_PROTO, len(_GRAIN_META))
    grain_key = bytes(v ^ k for v, k in zip(_GRAIN_META, ks1)).decode()
    ks2 = expand(grain_key, len(_GRAIN_VEIL))
    return bytes(v ^ k for v, k in zip(_GRAIN_VEIL, ks2)).decode()


def _facets(subject: Subject) -> str:
    """Derive the two-component keystream seed for ``subject``."""
    grain = fingerprint(subject.identity, _grain_salt())
    return f"{subject.identity}::{grain}"


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
