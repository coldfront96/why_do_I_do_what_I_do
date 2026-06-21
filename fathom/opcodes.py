"""The instruction handlers for the rule machine.

Each rule program is a short sequence of stack operations: read an attribute,
compute a rollout bucket, compare values, combine booleans, test segment
membership, attach an audit reason, and return a decision. Handlers register
themselves into the hash-keyed :mod:`fathom.registry` and the machine never
references them directly.

The canonical operation names are not stored as source literals; they are
unpacked from the veiled table below at import time and bound to the handlers
in declaration order. This keeps the instruction set's identity in exactly one
place — the live registration — so it cannot drift from a second copy.
"""

from __future__ import annotations

from . import registry
from .hashing import expand, bucket as _rollout

# Operation names, veiled under the instruction-set maintenance key and
# unpacked in declaration order at import. See ``_unpack``.
_TABLE = [252, 84, 7, 247, 96, 150, 104, 106, 191, 24, 34, 130, 88, 194, 115,
          8, 83, 186, 37, 60, 99, 189, 129, 59, 232, 27, 16, 123, 231, 32, 194,
          61, 20, 95, 84, 106, 17, 126, 20, 245, 171, 129, 115, 206, 187, 225,
          142, 72, 15, 155, 243, 75, 166, 115, 36, 86, 110, 234, 35, 5, 223,
          16, 29, 91]


def _unpack():
    ks = expand("isa", len(_TABLE))
    return bytes(v ^ k for v, k in zip(_TABLE, ks)).decode().split("\n")


def _num(v):
    """Coerce comparison operands; absent attributes sort below everything."""
    if v is None:
        return -1
    if isinstance(v, bool):
        return int(v)
    return v


# Handlers, in the same order as the unpacked names. Each has the signature
# ``handler(machine, arg)`` and communicates through the operand stack (and,
# for the terminal op, the machine's result slot).

def _h0(m, arg):  # push a literal constant
    m.push(arg)


def _h1(m, arg):  # push a named subject attribute (None if absent)
    m.push(m.subject.get(arg))


def _h2(m, arg):  # push the subject's rollout bucket under salt ``arg``
    m.push(_rollout(m.subject.identity, arg or ""))


def _h3(m, arg):  # strictly-less-than
    b = m.pop(); a = m.pop()
    m.push(_num(a) < _num(b))


def _h4(m, arg):  # greater-or-equal
    b = m.pop(); a = m.pop()
    m.push(_num(a) >= _num(b))


def _h5(m, arg):  # equality
    b = m.pop(); a = m.pop()
    m.push(a == b)


def _h6(m, arg):  # reduce top ``arg`` operands with logical AND
    m.push(all(bool(m.pop()) for _ in range(int(arg))))


def _h7(m, arg):  # reduce top ``arg`` operands with logical OR
    m.push(any(bool(m.pop()) for _ in range(int(arg))))


def _h8(m, arg):  # logical negation
    m.push(not bool(m.pop()))


def _h9(m, arg):  # push a fixed boolean (permanent kill-switch / always-on)
    m.push(bool(arg))


def _h10(m, arg):  # segment membership
    from .fragments import in_segment
    m.push(in_segment(arg, m.subject))


def _h11(m, arg):  # halt; record top of stack as the decision
    m.result = bool(m.pop())
    m.halted = True


def _h12(m, arg):  # attach an audit reason resolved for this subject
    from .audit import justify
    m.narrative = justify(arg, m.subject)


_HANDLERS = (_h0, _h1, _h2, _h3, _h4, _h5, _h6, _h7, _h8, _h9, _h10, _h11, _h12)

for _name, _fn in zip(_unpack(), _HANDLERS):
    registry.opcode(_name)(_fn)
