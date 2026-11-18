"""Synthetic ground-truth timelines: designer-INTENT labels, not compiler output.

Each template says what a sound designer would want: fast arrivals whoosh (and thud if they stop
abruptly), slow drifts stay silent, pops pop. Speeds in the ambiguous band are generated but not
scored, so thresholds are not simply read off the labels. Proxy labels: a human-labelled set is a
roadmap item (docs/ROADMAP.md).
"""

from __future__ import annotations

import numpy as np

from ..timeline import track_value

W, H, FPS, DUR = 1920, 1080, 30, 4.0
DIAG = float(np.hypot(W, H))


def _case(rng: np.random.Generator):
    kind = rng.choice(["fly_stop", "fly_settle", "drift", "pop", "gentle", "fade_fast", "fade_slow"])
    t0 = float(rng.uniform(0.3, 1.8))
    x0 = float(rng.uniform(-200, 400))
    el = {"id": "e", "tracks": {"y": [{"t": 0, "v": 540}]}}
    truth: list[dict] = []
    if kind in ("fly_stop", "fly_settle", "drift"):
        speed = {"fly_stop": (0.9, 2.5), "fly_settle": (0.9, 2.5), "drift": (0.03, 0.2)}[kind]
        avg = float(rng.uniform(*speed))
        dist = float(rng.uniform(500, 1500))
        dur = dist / (avg * DIAG)
        ease = str(rng.choice(["inCubic", "inQuad", "linear", "inExpo"] if kind == "fly_stop" else
                              ["outCubic", "outExpo", "linear", "inOutCubic"]))
        el["tracks"]["x"] = [{"t": t0, "v": x0}, {"t": t0 + dur, "v": x0 + dist, "ease": ease}]
        if kind != "drift":
            truth.append(dict(role="whoosh", lo=t0, hi=t0 + dur))
        if kind == "fly_stop" and ease != "linear" or (kind == "fly_stop" and avg > 1.2):
            truth.append(dict(role="impact", lo=t0 + dur, hi=t0 + dur))
    elif kind in ("pop", "gentle"):
        a, dur = (float(rng.uniform(0.1, 0.5)), float(rng.uniform(0.12, 0.35))) if kind == "pop" else (0.9, 1.0)
        el["tracks"]["scale"] = [{"t": t0, "v": a}, {"t": t0 + dur, "v": 1.0, "ease": "outBack"}]
        if kind == "pop":
            ts = np.linspace(t0, t0 + dur, 200)
            k = float(ts[int(np.argmax([track_value(el["tracks"]["scale"], t) for t in ts]))])
            truth.append(dict(role="ui_pop", lo=k, hi=k))
    else:
        dur = float(rng.uniform(0.08, 0.2)) if kind == "fade_fast" else 1.5
        el["tracks"]["opacity"] = [{"t": t0, "v": 0}, {"t": t0 + dur, "v": 1}]
        if kind == "fade_fast":
            truth.append(dict(role="ui_pop", lo=t0 + dur / 2, hi=t0 + dur / 2))
    return {"fps": FPS, "width": W, "height": H, "duration": DUR, "elements": [el]}, truth, str(kind)


def make_set(seed0: int, n: int = 150):
    return [_case(np.random.default_rng(seed0 + i)) for i in range(n)]


def score(genome: dict, cases, compile_fn) -> dict:
    tol = 1.0 / FPS
    tp = fp = fn = 0
    errs: list[float] = []
    for tl, truth, _ in cases:
        cues = compile_fn(tl, genome)
        used: set[int] = set()
        for tr in truth:
            hit = next((i for i, c in enumerate(cues) if i not in used and c["role"] == tr["role"]
                        and tr["lo"] - tol <= c["t"] <= tr["hi"] + tol), None)
            if hit is None:
                fn += 1
            else:
                tp += 1; used.add(hit)
                errs.append(abs(cues[hit]["t"] - (tr["lo"] if tr["role"] != "whoosh" else cues[hit]["t"])))
        fp += len(cues) - len(used)
    p = tp / max(tp + fp, 1); r = tp / max(tp + fn, 1)
    return {"f1": 2 * p * r / max(p + r, 1e-9), "precision": p, "recall": r, "tp": tp, "fp": fp, "fn": fn,
            "mean_err_ms": 1000 * float(np.mean(errs)) if errs else 0.0}
