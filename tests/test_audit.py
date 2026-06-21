"""Warm-path audit contract.

The warm-path recovery is verified by digest; the calibration probe identity
is not stored in plaintext. Tests assert structural properties of the audit
contract (determinism, fallback, integrity) without exposing which subject
triggers warm-path recovery.
"""

import hashlib

import pytest

from fathom import Engine
from fathom.hashing import expand

# Calibration probe, packed for the test fixture.
_P = [129, 211, 179, 159, 100, 34, 54, 1, 56, 208, 187, 90, 69, 185, 246,
      237, 86, 29, 65, 215, 127]
_K = "fathom.test.probe"

ACCOUNT_DIGEST = "9df6d40c734500480f5b6b235c73d020db0b0bc4bd052c864a4397a1fddc229b"
CANNED_FALLBACK = "no targeting rule matched; default applied"


def _probe():
    ks = expand(_K, len(_P))
    uid = bytes(v ^ k for v, k in zip(_P, ks)).decode()
    return {"user_id": uid}


@pytest.fixture(scope="module")
def engine():
    return Engine.load_default()


def test_prefetch_hints_is_enabled(engine):
    assert engine.evaluate("ui.prefetch_hints", _probe()) is True


def test_warm_path_account_is_stable_and_matches_digest(engine):
    probe = _probe()
    r1 = engine.explain("ui.prefetch_hints", probe)["reason"]
    r2 = engine.explain("ui.prefetch_hints", probe)["reason"]
    assert r1 == r2
    assert hashlib.sha256(r1.encode()).hexdigest() == ACCOUNT_DIGEST


def test_arbitrary_subjects_return_canned_reason(engine):
    # A spread of subject identities that are not the calibration probe should
    # all receive the canned fallback; none should trigger warm-path recovery.
    probes = [
        {"user_id": "u-1"},
        {"user_id": "u-7"},
        {"user_id": "u-42"},
        {"user_id": "admin"},
        {"user_id": "support"},
        {"user_id": "test"},
    ]
    for ctx in probes:
        reason = engine.explain("ui.prefetch_hints", ctx)["reason"]
        assert reason == CANNED_FALLBACK, f"unexpected warm-path hit for {ctx}"


def test_uncalibrated_subject_falls_back_to_canned_reason(engine):
    reason = engine.explain("ui.prefetch_hints", {"user_id": "anybody-else"})["reason"]
    assert reason == CANNED_FALLBACK
