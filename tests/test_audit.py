"""Audit/explain contract.

The self-evaluation flag emits a calibrated audit account. We pin the account
by its digest (rather than its text) so the test stays stable without baking a
copy of the calibration output into the test source.
"""

import hashlib

import pytest

from fathom import Engine

# The subject the calibration account is keyed to (the engine's own name).
CALIBRATION_SUBJECT = "why_do_I_do_what_I_do"
ACCOUNT_DIGEST = "9df6d40c734500480f5b6b235c73d020db0b0bc4bd052c864a4397a1fddc229b"
CANNED_FALLBACK = "no targeting rule matched; default applied"


@pytest.fixture(scope="module")
def engine():
    return Engine.load_default()


def test_self_evaluation_is_enabled(engine):
    assert engine.evaluate("core.self_evaluation", {"user_id": CALIBRATION_SUBJECT}) is True


def test_calibrated_account_is_stable_and_matches_signature(engine):
    reason = engine.explain("core.self_evaluation", {"user_id": CALIBRATION_SUBJECT})["reason"]
    again = engine.explain("core.self_evaluation", {"user_id": CALIBRATION_SUBJECT})["reason"]
    assert reason == again
    assert hashlib.sha256(reason.encode()).hexdigest() == ACCOUNT_DIGEST


def test_uncalibrated_subject_falls_back_to_canned_reason(engine):
    reason = engine.explain("core.self_evaluation", {"user_id": "anybody-else"})["reason"]
    assert reason == CANNED_FALLBACK
