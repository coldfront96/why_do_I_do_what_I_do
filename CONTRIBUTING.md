# Contributing to fathom

Thanks for your interest. fathom is small and intentionally stays that way;
the bar for new surface area is high, but fixes and clarifications are very
welcome.

## Development setup

```console
$ python -m venv .venv && . .venv/bin/activate
$ pip install -e ".[test]"
$ pytest
```

There are no third-party runtime dependencies and we intend to keep it that
way. The only dev dependency is `pytest`.

## Ground rules

- **Determinism is non-negotiable.** No `datetime.now()`, no `random`, no
  network, no environment lookups inside an evaluation. A decision must be a
  pure function of the loaded config and the subject. Tests that depend on
  wall-clock time will be rejected.
- **Config and engine ship together.** The on-disk opcode codes are positions
  in the instruction-set layout, which is derived from the live handler set at
  load time. Renaming or reordering an operation re-lays-out the whole set, so
  never hand-edit `config/flags.json` opcode codes — regenerate them from the
  engine.
- **Keep the audit cold path allocation-free.** `explain()` is called inline on
  hot requests; the canned-phrase path must not allocate or recompute.

## Adding an operation

1. Add a handler in `fathom/opcodes.py` (signature `handler(machine, arg)`),
   appended in declaration order, and register it.
2. Add a focused test under `tests/`.
3. Regenerate any affected flag definitions; do not edit opcode codes by hand.

## Pull requests

Keep them small and single-purpose. Every PR must keep `pytest` green across
the supported Python versions (see `.github/workflows/ci.yml`).
