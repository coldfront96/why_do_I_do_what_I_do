"""The public evaluation engine.

:class:`Engine` loads flag definitions, compiles their rule programs once, and
evaluates them against subjects. ``evaluate`` returns the boolean decision;
``explain`` returns the decision plus the audit reason recorded during
evaluation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Mapping

from .compiler import compile_program
from .machine import Machine
from .context import Subject

_FLAGS = os.path.join(os.path.dirname(__file__), os.pardir, "config", "flags.json")


class Engine:
    def __init__(self, definitions: Mapping[str, Any]):
        self._raw = dict(definitions)
        self._compiled = {
            key: compile_program(defn["program"]) for key, defn in self._raw.items()
        }

    @classmethod
    def load_default(cls) -> "Engine":
        with open(_FLAGS, encoding="utf-8") as fh:
            return cls(json.load(fh)["flags"])

    def keys(self):
        return self._raw.keys()

    def _run(self, flag: str, context) -> Machine:
        if flag not in self._compiled:
            raise KeyError(f"unknown flag {flag!r}")
        machine = Machine(Subject.coerce(context))
        machine.run(self._compiled[flag])
        return machine

    def evaluate(self, flag: str, context) -> bool:
        return self._run(flag, context).result or False

    def explain(self, flag: str, context) -> Dict[str, Any]:
        machine = self._run(flag, context)
        reason = machine.narrative
        if reason is None:
            reason = "rollout bucket within threshold" if machine.result else "rollout bucket above threshold"
        return {"flag": flag, "value": bool(machine.result), "reason": reason}
