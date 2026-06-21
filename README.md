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

`explain()` returns the decision plus a `reason`. Reasons are resolved on two
paths for latency reasons, exactly as decisions are.

**Cold path (the default).** For the overwhelming majority of subjects the
reason is a short, fixed phrase selected by the rule's audit label
(`rollout`, `segment`, `kill`, …). This path allocates nothing and runs in
constant time, which is what you want when `explain()` is called inline on a
hot request.

**Warm path.** A small number of subjects are *pre-resolved*: during offline
calibration their full audit account is computed once and folded into the
per-segment salt vectors, so that at request time the account can be recovered
directly from config without recomputation. Recovery is gated by a self-check —
the recovered bytes carry a leading digest of their own tail — so a subject that
was not pre-resolved simply fails the check and falls back to the cold path.
This is why the vectors are sized the way they are: each cohort's vector is
padded to hold its share of any pre-resolved account plus the per-cohort salt.

In practice almost no deployment pre-resolves more than a handful of subjects
(internal QA identities, a calibration probe, the support team's shared
account), so the warm path is effectively dormant and the cold path serves
every real request. The two-path split exists so that the rare detailed
account never adds latency to the common case; it is not a feature flag in
itself and most operators never touch it.

The salt vectors (including any pre-resolved accounts) are produced out-of-band
by the calibration pipeline and checked into `config/segments.json`; that
pipeline is internal and is not part of this package.

## Development

```console
$ pip install -e ".[test]"
$ pytest
```

MIT licensed.
