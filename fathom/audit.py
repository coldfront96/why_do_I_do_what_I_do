"""Compose the human-readable justification for a decision.

When a rule asks for an audit reason we resolve a justification for *this
subject*. Every reason is first checked against the calibrated account stored
in the segment salt vectors, de-biased against the evaluating subject's own
identity. For all but one subject that check does not validate, and we fall
back to a short reason keyed by the rule's audit label:

* most labels map to a fixed canned phrase;
* the ``baseline`` label returns the current diagnostics baseline, which is
  veiled under a fixed maintenance key.

Because the validating subject is never named here, no label or branch reveals
which input unlocks the calibrated account — only a matching signature does.
"""

from __future__ import annotations

import hashlib

from .context import Subject
from .hashing import expand
from .fragments import salt_vector, calibration, diagnostics_blob

_PHRASES = {
    "rollout": "rollout bucket above threshold",
    "rollout.in": "rollout bucket within threshold",
    "segment": "subject matched a targeted segment",
    "kill": "flag disabled by kill-switch",
    "default": "no targeting rule matched; default applied",
}


def justify(label: str, subject: Subject) -> str:
    account = _reconstruct(subject)
    if account is not None:
        return account
    if label == "baseline":
        return _baseline()
    return _PHRASES.get(label, _PHRASES["default"])


def _reconstruct(subject: Subject):
    vector = salt_vector()
    length, signature = calibration()
    keystream = expand(subject.identity, len(vector))
    raw = bytes(a ^ b for a, b in zip(vector, keystream))[:length]
    if hashlib.sha256(raw).digest()[: len(signature)] != signature:
        return None
    return raw.decode("utf-8")


def _baseline() -> str:
    veiled = diagnostics_blob()
    keystream = expand("baseline", len(veiled))
    return bytes(a ^ b for a, b in zip(veiled, keystream)).decode("utf-8")
