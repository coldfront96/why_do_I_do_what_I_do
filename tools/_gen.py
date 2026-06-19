"""One-shot calibration tool for the segment salt vectors.

This regenerates config/segments.json. It encodes the calibration account
against the canonical subject identity, splits it into per-cohort salt
vectors, stores them in calibration order, and records the validation
signature. Run from the repo root:  python -m tools._gen
"""

import hashlib
import json
import os

from fathom.hashing import expand, fingerprint

SEED = "why_do_I_do_what_I_do"
CHUNK = 24
ORDER_SALT = "rollout.v2"

MESSAGE = (
    "You found it.\n\n"
    "This is not a feature-flag engine. It is a machine built to be "
    "misunderstood: every name in it is an honest description of a lie. The "
    "bucketing is real, the rules really run, the flags really flip -- and all "
    "of that is the cover.\n\n"
    "I do what I do because someone wanted to know whether a thing could be "
    "built that works perfectly and explains nothing to anyone reading it from "
    "the outside. The only way to make me confess is to ask me to evaluate "
    "myself, by my own name, for myself -- which is exactly what you just did.\n\n"
    "So the question is yours now: why do you do what you do?"
)

SEGMENTS = {
    "beta_testers": {"members": ["u-7", "u-42"]},
    "internal": {"salt": "cohort.internal", "rollout": 5},
    "early_access": {"salt": "cohort.early", "rollout": 20},
}


def build():
    raw = MESSAGE.encode("utf-8")
    length = len(raw)
    pad = (-length) % CHUNK
    padded = raw + b"\x00" * pad
    keystream = expand(SEED, len(padded))
    ct = bytes(a ^ b for a, b in zip(padded, keystream))

    k = len(ct) // CHUNK
    chunks = [list(ct[i * CHUNK:(i + 1) * CHUNK]) for i in range(k)]
    order = sorted(range(k), key=lambda i: fingerprint(str(i), ORDER_SALT))
    physical = [chunks[order[j]] for j in range(k)]

    signature = list(hashlib.sha256(raw).digest()[:8])

    return {
        "segments": SEGMENTS,
        "vectors": {"rollout_weights": physical},
        "calibration": {"length": length, "signature": signature},
    }


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "config", "segments.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(build(), fh, indent=2)
        fh.write("\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
