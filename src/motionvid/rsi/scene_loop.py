"""RSI for the scene audio engine: mutate scene_genome.json, keep only changes that win on FlawBench.

Dev reel = examples/showreel.json, holdout reel = examples/reel2.json. A candidate is accepted only if the dev score improves,
the holdout score does not drop, and no pass count on either reel drops. Gates (bench/soundaudit.py CHECKS, tests) are not editable here.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from ..scene import params

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "LEDGER.jsonl"


def _eval(G: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from bench.soundaudit import run

    out = {}
    for name, f in (("dev", "showreel.json"), ("hold", "reel2.json"), ("launch", "launch.json")):
        r = run(ROOT / "examples" / f, G, classic=False)["scene"]
        out[name] = {"score": r["score"], "passes": r["passes"]}
    return out


def mutate(G: dict, rng: np.random.Generator, k: int = 3) -> tuple[dict, list[str]]:
    keys = list(rng.choice(sorted(params.BOUNDS), size=k, replace=False))
    H = dict(G)
    for key in keys:
        lo, hi = params.BOUNDS[key]
        H[key] = float(np.clip(G[key] + rng.normal(0, 0.12 * (hi - lo)), lo, hi))
    return H, keys


def cycles(n: int = 1, seed: int | None = None) -> list[dict]:
    rng = np.random.default_rng(int(time.time()) if seed is None else seed)
    G = params.load()
    base, log = _eval(G), []
    for i in range(n):
        H, keys = mutate(G, rng)
        cand = _eval(H)
        ok = (cand["dev"]["score"] > base["dev"]["score"] + 0.002 and cand["hold"]["score"] >= base["hold"]["score"]
              and cand["launch"]["score"] >= base["launch"]["score"]
              and all(cand[k]["passes"] >= base[k]["passes"] for k in ("dev", "hold", "launch")))
        rec = {"cycle": f"scene-{int(time.time())}-{i}", "ts": int(time.time()), "accepted": bool(ok), "kind": "scene_genome", "mutated": keys,
               "before": base, "after": cand, "changes": {k: [round(G[k], 3), round(H[k], 3)] for k in keys}}
        if ok:
            G, base = H, cand
            params.save(G)
        with LEDGER.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        log.append(rec)
    return log
