"""Command-line access to the evaluation engine.

    python -m fathom flags
    python -m fathom evaluate checkout.new_flow user_id=u-1024
    python -m fathom explain  checkout.new_flow user_id=u-1024

Attributes are passed as ``key=value`` pairs. The subject's bucketing identity
defaults to ``user_id``.
"""

from __future__ import annotations

import sys

from .engine import Engine


def _parse(pairs):
    attrs = {}
    for p in pairs:
        if "=" not in p:
            raise SystemExit(f"expected key=value, got {p!r}")
        k, v = p.split("=", 1)
        attrs[k] = v
    return attrs


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 0

    cmd, rest = argv[0], argv[1:]
    engine = Engine.load_default()

    if cmd == "flags":
        for key in sorted(engine.keys()):
            print(key)
        return 0

    if cmd in ("evaluate", "explain"):
        if not rest:
            raise SystemExit(f"{cmd} requires a flag name")
        flag, attrs = rest[0], _parse(rest[1:])
        if cmd == "evaluate":
            print(str(engine.evaluate(flag, attrs)).lower())
        else:
            result = engine.explain(flag, attrs)
            print(f"{result['flag']} = {str(result['value']).lower()}")
            print(f"  reason: {result['reason']}")
        return 0

    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    raise SystemExit(main())
