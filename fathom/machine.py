"""The rule evaluation machine.

A tiny, deterministic stack machine. It executes a compiled rule program
against a subject and yields a boolean decision plus an optional narrative
(the audit reason). There is no control flow beyond linear execution and an
explicit ``return``; rules are intentionally restricted to keep evaluation
total and side-effect free.
"""

from __future__ import annotations

from typing import List, Optional

from .registry import resolve
from .context import Subject


class Machine:
    def __init__(self, subject: Subject):
        self.subject = subject
        self._stack: List[object] = []
        self.result: Optional[bool] = None
        self.narrative: Optional[str] = None
        self.halted = False

    def push(self, value) -> None:
        self._stack.append(value)

    def pop(self):
        return self._stack.pop()

    def run(self, program) -> bool:
        for key, arg in program:
            if self.halted:
                break
            resolve(key)(self, arg)
        # A program with no explicit ``return`` falls through to its top value.
        if self.result is None and self._stack:
            self.result = bool(self._stack[-1])
        return bool(self.result)
