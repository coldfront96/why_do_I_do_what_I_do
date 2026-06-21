import pytest

from fathom import Engine


@pytest.fixture(scope="module")
def engine():
    return Engine.load_default()


def test_decisions_are_deterministic(engine):
    ctx = {"user_id": "u-1024", "plan": "pro"}
    first = {f: engine.evaluate(f, ctx) for f in engine.keys()}
    second = {f: engine.evaluate(f, ctx) for f in engine.keys()}
    assert first == second


def test_attribute_targeting(engine):
    assert engine.evaluate("ui.dark_mode", {"user_id": "x", "plan": "pro"}) is True
    assert engine.evaluate("ui.dark_mode", {"user_id": "x", "plan": "free"}) is False


def test_kill_switch_is_off(engine):
    assert engine.evaluate("billing.legacy_dunning", {"user_id": "x"}) is False


def test_segment_roster_membership(engine):
    assert engine.evaluate("search.semantic_ranking", {"user_id": "u-7"}) is True


def test_rollout_bucketing_is_stable(engine):
    decisions = {
        engine.evaluate("checkout.new_flow", {"user_id": "u-1024"}) for _ in range(5)
    }
    assert len(decisions) == 1


def test_telemetry_flags_expose_a_reason(engine):
    # The telemetry.* flags surface engine metadata through the audit channel.
    for flag in ("telemetry.baseline", "telemetry.release", "telemetry.credits"):
        result = engine.explain(flag, {"user_id": "support"})
        assert result["value"] is True
        assert isinstance(result["reason"], str) and result["reason"]


def test_unknown_flag_raises(engine):
    with pytest.raises(KeyError):
        engine.evaluate("does.not.exist", {"user_id": "x"})
