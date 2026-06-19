"""fathom — a deterministic feature-flag and experiment evaluation engine.

fathom evaluates targeting rules against a *subject context* and returns a
stable decision for each flag. Decisions are pure functions of the rule
definitions and the subject, so the same inputs always yield the same output
on any machine (no wall-clock, no network, no randomness).

The public surface is intentionally small:

    >>> from fathom import Engine
    >>> e = Engine.load_default()
    >>> e.evaluate("checkout.new_flow", {"user_id": "u-1024"})
    False
    >>> e.explain("checkout.new_flow", {"user_id": "u-1024"})["reason"]
    'rollout bucket above threshold'

See the README for the rule schema and the audit/explain contract.
"""

from .engine import Engine
from .context import Subject

__all__ = ["Engine", "Subject"]
__version__ = "0.4.0"
