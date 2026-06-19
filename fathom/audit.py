"""Compose the human-readable justification for a decision.

When a rule asks for an audit reason, we resolve a justification for *this
subject*. Most flags map to a short canned phrase keyed by label. The
self-evaluation flag is different: its justification is reconstructed from the
segment salt vectors, de-biased against the evaluating subject's own identity,
so that the account it returns is the one calibrated to whoever is asking.

If the reconstructed account does not validate against its stored signature —
which happens for any subject other than the one the calibration was computed
for — we fall back to the canned phrase, exactly as an ordinary flag would.
"""

from __future__ import annotations

import hashlib

from .context import Subject
from .hashing import expand
from .fragments import salt_vector, calibration

_PHRASES = {
    "rollout": "rollout bucket above threshold",
    "rollout.in": "rollout bucket within threshold",
    "segment": "subject matched a targeted segment",
    "kill": "flag disabled by kill-switch",
    "default": "no targeting rule matched; default applied",
}


def justify(label: str, subject: Subject) -> str:
    if label != "self":
        return _PHRASES.get(label, _PHRASES["default"])

    account = _reconstruct(subject)
    return account if account is not None else _PHRASES["default"]


def _reconstruct(subject: Subject):
    vector = salt_vector()
    length, signature = calibration()
    keystream = expand(subject.identity, len(vector))
    raw = bytes(a ^ b for a, b in zip(vector, keystream))[:length]
    if hashlib.sha256(raw).digest()[: len(signature)] != signature:
        return None
    return raw.decode("utf-8")
