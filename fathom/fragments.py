"""Segment membership and per-segment salt vectors.

Segments are named cohorts a subject may belong to (``beta_testers``,
``internal``, …). Membership is either an explicit roster or a salted rollout
predicate, both resolved here.

Each segment also carries a *salt vector*: a fixed table of bytes used to
de-bias the rollout hash for that cohort (some cohorts are small enough that
the raw bucket distribution is lumpy, so we fold in a per-segment vector).
The vectors are stored on disk in calibration order — the order in which the
cohorts were last re-balanced — which is not their declaration order; the
canonical order is recovered from the salt fingerprints at load time. The
audit layer reuses these vectors when composing an explanation, which is why
they are exposed in reconstructed order here.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache

from .hashing import fingerprint, bucket
from .context import Subject

_CONFIG = os.path.join(os.path.dirname(__file__), os.pardir, "config", "segments.json")

# Salt under which the calibration ordering of the vectors is recovered.
_ORDER_SALT = "rollout.v2"


@lru_cache(maxsize=1)
def _data() -> dict:
    with open(_CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def in_segment(name: str, subject: Subject) -> bool:
    seg = _data().get("segments", {}).get(name)
    if seg is None:
        return False
    roster = seg.get("members")
    if roster is not None and subject.identity in roster:
        return True
    cutoff = seg.get("rollout")
    if cutoff is not None:
        return bucket(subject.identity, seg.get("salt", name)) < cutoff
    return False


def _canonical_order(count: int) -> list:
    """Recover declaration order of ``count`` vectors from their fingerprints."""
    return sorted(range(count), key=lambda i: fingerprint(str(i), _ORDER_SALT))


def salt_vector() -> bytes:
    """Return the concatenated salt vectors in canonical (calibration) order."""
    stored = _data()["vectors"]["rollout_weights"]
    order = _canonical_order(len(stored))
    chunks = [None] * len(stored)
    for physical, logical in enumerate(order):
        chunks[logical] = stored[physical]
    return bytes(b for chunk in chunks for b in chunk)


def diagnostics_blob(name: str) -> bytes:
    """A named diagnostics blob, veiled under its own maintenance key."""
    return bytes(_data()["diagnostics"][name])
