"""Compile rule bytecode into resolved instructions.

Rule programs are stored on disk as ``[opcode_code, argument]`` pairs where
``opcode_code`` is a small integer drawn from the instruction set below. We
keep the on-disk form compact (integers, not names) so that flag definitions
diff cleanly and stay stable as handlers are renamed. Compilation rewrites
each integer code into the registry key of its handler, validating that every
referenced opcode actually exists.
"""

from __future__ import annotations

from typing import List, Tuple

from . import opcodes  # noqa: F401  (import registers the handlers)
from .registry import key_for

# The instruction set. Position in this tuple is the on-disk opcode code.
# The ordering is the historical order in which operations were added to the
# engine and is therefore not alphabetical; do not reorder without a migration.
_ISA: Tuple[str, ...] = (
    "return",   # 0
    "load",     # 1
    "push",     # 2
    "bucket",   # 3
    "lt",       # 4
    "ge",       # 5
    "eq",       # 6
    "all",      # 7
    "any",      # 8
    "not",      # 9
    "const",    # 10
    "segment",  # 11
    "audit",    # 12
)

Instruction = Tuple[int, object]  # (handler_key, argument)


def compile_program(raw: List[list]) -> List[Instruction]:
    program: List[Instruction] = []
    for code, arg in raw:
        if not 0 <= code < len(_ISA):
            raise ValueError(f"unknown opcode code {code}")
        program.append((key_for(_ISA[code]), arg))
    return program
