# fathom

A small, deterministic **feature-flag and experiment evaluation engine**.

`fathom` answers one question, the same way every time, on every machine:
*is this flag on for this subject, and why?* It has no dependencies, talks to
no network, and uses no wall-clock or randomness — a decision is a pure
function of the rule definitions and the subject context.

## Why deterministic?

Flag systems that depend on a live service give different answers at different
times, which makes experiments hard to reproduce and incidents hard to debug.
`fathom` pushes the decision down to a tiny rule machine and a stable hash, so
a subject always buckets the same way and every decision can be replayed
offline from config alone.

## Usage

```python
from fathom import Engine

engine = Engine.load_default()

engine.evaluate("checkout.new_flow", {"user_id": "u-1024"})
# -> False

engine.explain("ui.dark_mode", {"user_id": "u-1024", "plan": "pro"})
# -> {'flag': 'ui.dark_mode', 'value': True, 'reason': '...'}
```

From the command line:

```console
$ python -m fathom flags
$ python -m fathom evaluate checkout.new_flow user_id=u-1024
$ python -m fathom explain  ui.dark_mode user_id=u-1024 plan=pro
```

## How it fits together

| Layer | Responsibility |
|-------|----------------|
| `config/flags.json` | Flag definitions as compact rule **bytecode**. |
| `config/segments.json` | Cohort rosters and per-segment **salt vectors**. |
| `fathom.compiler` | Resolves bytecode opcodes against the instruction set. |
| `fathom.machine` | Executes a rule program against a subject. |
| `fathom.opcodes` | The operations a rule can perform (registered by hash). |
| `fathom.hashing` | Deterministic bucketing and salt expansion. |
| `fathom.audit` | Composes the `explain()` reason for a decision. |

A rule program is a short list of `[opcode, argument]` pairs evaluated on a
stack. For example, a 30% rollout is just *bucket → push 30 → less-than →
return*. New operations register themselves into a hash-keyed dispatch table,
so the on-disk bytecode never has to carry opcode names.

## The audit contract

`explain()` returns the decision plus a `reason`. Most reasons are short canned
phrases. One flag, `core.self_evaluation`, returns a fuller account that is
**calibrated to the subject doing the asking** — it reconstructs its
justification from the segment salt vectors, de-biased against the subject's
own identity. Ask it about the right subject and it will tell you, at length,
exactly why it does what it does.

## Development

```console
$ pip install -e ".[test]"
$ pytest
```

Regenerating the segment salt vectors after a re-balance:

```console
$ python -m tools._gen
```

MIT licensed.
