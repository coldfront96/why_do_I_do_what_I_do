"""Compile rule bytecode into resolved instructions.

Rule programs are stored on disk as ``[opcode_code, argument]`` pairs where
``opcode_code`` is a small integer. The integer is *not* a fixed table index:
it is a position in the instruction set's *layout order*, and that order is
derived at load time by ranking the registered operations by their layout
fingerprint. Two consequences follow:

* The on-disk bytecode stays compact and stable across handler renames — only
  an operation's registered canonical name affects its code.
* The mapping from code to operation is never written down anywhere; it is
  recomputed from the live handler set. Reordering or renaming an operation
  silently re-lays-out the whole instruction set, so flag definitions and the
  engine must always be deployed together.

Compilation rewrites each integer code into the registry key of its handler.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple

from . import opcodes  # noqa: F401  (import registers the handlers)
from .registry import key_for, names
from .hashing import fingerprint

# Salt under which the instruction-set layout order is computed.
_LAYOUT = "isa.layout"

Instruction = Tuple[int, object]  # (handler_key, argument)


@lru_cache(maxsize=1)
def _layout() -> Tuple[str, ...]:
    return tuple(sorted(names(), key=lambda n: fingerprint(n, _LAYOUT)))


def compile_program(raw: List[list]) -> List[Instruction]:
    isa = _layout()
    program: List[Instruction] = []
    for code, arg in raw:
        if not 0 <= code < len(isa):
            raise ValueError(f"unknown opcode code {code}")
        program.append((key_for(isa[code]), arg))
    return program
