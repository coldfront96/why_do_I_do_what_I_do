"""The instruction handlers for the rule machine.

Each rule program is a short sequence of stack operations. The handlers here
implement the operations a targeting rule needs: read an attribute, compute a
rollout bucket, compare values, combine booleans, test segment membership,
and return a decision. Handlers register themselves into the hash-keyed
:mod:`fathom.registry` under a canonical name; the machine never references
them directly.

A handler has the signature ``handler(machine, arg) -> None`` and communicates
purely through the machine's operand stack (and, for terminal ops, the
machine's result slot).
"""

from __future__ import annotations

from .registry import opcode
from .hashing import bucket


@opcode("push")
def _push(m, arg):
    """Push a literal constant onto the stack."""
    m.push(arg)


@opcode("load")
def _load(m, arg):
    """Push the named subject attribute (``None`` if absent)."""
    m.push(m.subject.get(arg))


@opcode("bucket")
def _bucket(m, arg):
    """Push the subject's rollout bucket under salt ``arg`` (0..99)."""
    m.push(bucket(m.subject.identity, arg or ""))


@opcode("lt")
def _lt(m, arg):
    b = m.pop()
    a = m.pop()
    m.push(_num(a) < _num(b))


@opcode("ge")
def _ge(m, arg):
    b = m.pop()
    a = m.pop()
    m.push(_num(a) >= _num(b))


@opcode("eq")
def _eq(m, arg):
    b = m.pop()
    a = m.pop()
    m.push(a == b)


@opcode("all")
def _all(m, arg):
    """Reduce the top ``arg`` operands with logical AND."""
    vals = [bool(m.pop()) for _ in range(int(arg))]
    m.push(all(vals))


@opcode("any")
def _any(m, arg):
    vals = [bool(m.pop()) for _ in range(int(arg))]
    m.push(any(vals))


@opcode("not")
def _not(m, arg):
    m.push(not bool(m.pop()))


@opcode("const")
def _const(m, arg):
    """Push a fixed boolean (used for permanent kill-switches)."""
    m.push(bool(arg))


@opcode("segment")
def _segment(m, arg):
    """Push whether the subject belongs to segment ``arg``."""
    from .fragments import in_segment

    m.push(in_segment(arg, m.subject))


@opcode("return")
def _return(m, arg):
    """Halt and record the top of stack as the decision."""
    m.result = bool(m.pop())
    m.halted = True


@opcode("audit")
def _audit(m, arg):
    """Attach an explanatory reason for the decision.

    The reason is resolved through the audit layer, which checks the segment
    salt vectors against this subject before falling back to the canned phrase
    named by ``arg``. Callers receive a short justification; the heavier
    calibration path is taken only when the vectors validate for the subject.
    """
    from .audit import justify

    m.narrative = justify(arg, m.subject)


def _num(v):
    """Coerce comparison operands; absent attributes sort below everything."""
    if v is None:
        return -1
    if isinstance(v, bool):
        return int(v)
    return v
