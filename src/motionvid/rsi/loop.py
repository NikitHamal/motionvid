"""Recursive self-improvement, honest edition.

One cycle: (1) measure the current genome on DEV and HOLDOUT synthetic ground truth,
(2) propose N seeded mutations, keep the best on DEV, (3) accept it ONLY if DEV improves by a margin
AND HOLDOUT does not regress AND the regression gate passes, (4) write genome.json + append LEDGER.jsonl.
The loop improves the compiler's parameters; it never edits the gates or the labels.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from .. import genome as G
from ..cues import compile_cues
from . import gt

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "LEDGER.jsonl"
DEV = gt.make_set(0)
HOLD = gt.make_set(10_000)
MARGIN = 0.002


def _gate(genome: dict) -> bool:
    """Regression gate: explicit agent hints always survive; example launch timeline keeps >= 20 cues."""
    ex = json.loads((ROOT / "examples" / "launch.json").read_text())
    cues = compile_cues(ex, genome)
    hints = [c for c in cues if c["why"] == "agent hint"]
    return len(hints) == len(ex["sfx"]) and len(cues) >= 20


def _history() -> list[dict]:
    return [json.loads(x) for x in LEDGER.read_text().splitlines()] if LEDGER.exists() else []


def mutate(g: dict, rng: np.random.Generator) -> dict:
    out = dict(g)
    for k in rng.choice(list(G.BOUNDS), size=int(rng.integers(1, 3)), replace=False):
        lo, hi = G.BOUNDS[k]
        out[k] = float(np.clip(out[k] * (1 + rng.uniform(-0.3, 0.3)), lo, hi))
    return out


def cycle(n_mut: int = 60) -> dict:
    hist = _history()
    n = len(hist) + 1
    rng = np.random.default_rng(1234 + n)
    cur = G.load()
    t0 = time.time()
    base_dev = gt.score(cur, DEV, compile_cues)
    base_hold = gt.score(cur, HOLD, compile_cues)
    best, best_dev = cur, base_dev
    for _ in range(n_mut):
        cand = mutate(best, rng)
        s = gt.score(cand, DEV, compile_cues)
        if s["f1"] > best_dev["f1"]:
            best, best_dev = cand, s
    hold = gt.score(best, HOLD, compile_cues)
    accepted = (best is not cur and best_dev["f1"] >= base_dev["f1"] + MARGIN
                and hold["f1"] >= base_hold["f1"] - 0.0 and _gate(best))
    if accepted:
        G.save(best)
    entry = {"cycle": n, "ts": int(t0), "accepted": bool(accepted), "dev_before": base_dev["f1"],
             "dev_after": best_dev["f1"], "hold_before": base_hold["f1"], "hold_candidate": hold["f1"],
             "hold_detail": hold, "changed": {k: [cur[k], best[k]] for k in best if best[k] != cur[k]} if accepted else {},
             "seconds": round(time.time() - t0, 1)}
    with LEDGER.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
