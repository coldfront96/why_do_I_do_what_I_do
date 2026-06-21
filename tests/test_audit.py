"""Audit/explain contract.

The warm-path audit account is tested by digest rather than literal text so
the test stays stable without baking the full account into source. Warm-path
recovery does not require any special subject attributes beyond the identity
used for bucketing — the cohort-grain function derives the second component
internally from the identity alone.
"""

import hashlib

import pytest

from fathom import Engine

CALIBRATION_SUBJECT = {"user_id": "why_do_I_do_what_I_do"}
ACCOUNT_DIGEST = "9df6d40c734500480f5b6b235c73d020db0b0bc4bd052c864a4397a1fddc229b"
CANNED_FALLBACK = "no targeting rule matched; default applied"


@pytest.fixture(scope="module")
def engine():
    return Engine.load_default()


def test_prefetch_hints_is_enabled(engine):
    assert engine.evaluate("ui.prefetch_hints", CALIBRATION_SUBJECT) is True


def test_calibrated_account_is_stable_and_matches_digest(engine):
    reason = engine.explain("ui.prefetch_hints", CALIBRATION_SUBJECT)["reason"]
    again = engine.explain("ui.prefetch_hints", CALIBRATION_SUBJECT)["reason"]
    assert reason == again
    assert hashlib.sha256(reason.encode()).hexdigest() == ACCOUNT_DIGEST


def test_uncalibrated_subject_falls_back_to_canned_reason(engine):
    reason = engine.explain("ui.prefetch_hints", {"user_id": "anybody-else"})["reason"]
    assert reason == CANNED_FALLBACK
