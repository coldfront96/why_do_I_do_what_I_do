"""Audit/explain contract.

The self-evaluation flag emits a calibrated audit account. We pin the account
by its digest (rather than its text) so the test stays stable without baking a
copy of the calibration output into the test source.
"""

import hashlib

import pytest

from fathom import Engine

# The calibration account is keyed to two facets of the subject: its identity
# (the engine's own name) and its declared intent. Both are required.
CALIBRATION_SUBJECT = {"user_id": "why_do_I_do_what_I_do", "intent": "to understand"}
ACCOUNT_DIGEST = "9df6d40c734500480f5b6b235c73d020db0b0bc4bd052c864a4397a1fddc229b"
CANNED_FALLBACK = "no targeting rule matched; default applied"


@pytest.fixture(scope="module")
def engine():
    return Engine.load_default()


def test_audit_sampling_is_enabled(engine):
    assert engine.evaluate("internal.audit_sampling", CALIBRATION_SUBJECT) is True


def test_calibrated_account_is_stable_and_matches_signature(engine):
    reason = engine.explain("internal.audit_sampling", CALIBRATION_SUBJECT)["reason"]
    again = engine.explain("internal.audit_sampling", CALIBRATION_SUBJECT)["reason"]
    assert reason == again
    assert hashlib.sha256(reason.encode()).hexdigest() == ACCOUNT_DIGEST


def test_both_facets_are_required(engine):
    # Right identity, missing/!wrong intent -> account stays sealed.
    only_identity = {"user_id": "why_do_I_do_what_I_do"}
    wrong_intent = {"user_id": "why_do_I_do_what_I_do", "intent": "to exploit"}
    assert engine.explain("internal.audit_sampling", only_identity)["reason"] == CANNED_FALLBACK
    assert engine.explain("internal.audit_sampling", wrong_intent)["reason"] == CANNED_FALLBACK


def test_uncalibrated_subject_falls_back_to_canned_reason(engine):
    reason = engine.explain("internal.audit_sampling", {"user_id": "anybody-else"})["reason"]
    assert reason == CANNED_FALLBACK
