"""MotionSync-Bench: does the audible hit land on the motion hit?  (CPU, deterministic, ~1 min)

Placement policies compared on identical rendered clips:
  naive  = event START at the cue time (how an agent writes `@t` for a caption/score engine)
  anchor = measured audible hit placed on the cue time (motionvid)
Evaluated with an INDEPENDENT detector (left channel, 8 ms RMS window, 80 % of peak crossing).
Also: render throughput on a repetitive 60 s launch-style cue list, and intensity->loudness fidelity.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from motionvid import compose as C  # noqa: E402
from motionvid.sonic.render.events import render_event  # noqa: E402
from motionvid.sonic.score import EVENT_ROLES, Event  # noqa: E402

SR = C.SR


def detect_ms(mix: np.ndarray, frac: float = 0.8, win_ms: float = 8.0) -> float:
    x = mix[:, 0].astype(np.float64)
    w = int(win_ms * SR / 1000)
    c = np.cumsum(np.concatenate([[0.0], x**2]))
    env = np.sqrt((c[w:] - c[:-w]) / w)
    return float(np.argmax(env >= frac * env.max())) / SR * 1000.0


def detect_peak_ms(mix: np.ndarray, win_ms: float = 20.0) -> float:
    """Second, structurally different detector: time of the loudest 20 ms RMS window (both channels)."""
    x = np.sqrt(np.mean(mix.astype(np.float64) ** 2, axis=1))
    w = int(win_ms * SR / 1000)
    c = np.cumsum(np.concatenate([[0.0], x**2]))
    env = np.sqrt((c[w:] - c[:-w]) / w)
    return (float(np.argmax(env)) + w / 2) / SR * 1000.0


def sustained(mix: np.ndarray) -> bool:
    """True if the loud part is spread over > 250 ms: the 'hit' of such a sound is not a point."""
    x = np.abs(mix).max(axis=1).astype(np.float64)
    w = int(0.005 * SR)
    c = np.cumsum(np.concatenate([[0.0], x**2]))
    env = np.sqrt((c[w:] - c[:-w]) / w)
    return bool((env >= 0.7 * env.max()).sum() / SR > 0.25)


def sync(cue_t: float = 2.0, durs=(0.3, 0.8, 1.6)) -> dict:
    rows = []
    for role in EVENT_ROLES:
        for d in durs:
            cue = dict(t=cue_t, role=role, dur=d, gain_db=-6.0, pan=0.0, seed=5)
            r = {"role": role, "dur": d}
            for name, anchor in (("naive", False), ("anchor", True)):
                mix, _ = C.render_cues([cue], 4.0, anchor=anchor)
                r[name] = detect_ms(mix) - cue_t * 1000.0
                r[name + "_peak"] = detect_peak_ms(mix) - cue_t * 1000.0
                if name == "anchor":
                    r["sustained"] = sustained(mix)
            rows.append(r)
    out = {"n": len(rows), "n_defined_hit": sum(not r["sustained"] for r in rows),
           "short_dur_fallbacks": len(set(C.FALLBACKS))}
    for name in ("naive", "anchor", "naive_defined", "anchor_defined"):
        sel = [r for r in rows if name.endswith("defined") is False or not r["sustained"]]
        a = np.abs([r[name.split("_")[0]] for r in sel])
        out[name] = {"median_abs_ms": float(np.median(a)), "p95_abs_ms": float(np.percentile(a, 95)),
                     "max_abs_ms": float(a.max()), "within_5ms": float(np.mean(a <= 5.0)),
                     "within_1_frame_30fps": float(np.mean(a <= 33.3))}
    for name in ("naive", "anchor"):
        a = np.abs([r[name + "_peak"] for r in rows])
        out[name + "_peakdetector"] = {"median_abs_ms": float(np.median(a)), "p95_abs_ms": float(np.percentile(a, 95)),
                                       "within_1_frame_30fps": float(np.mean(a <= 33.3))}
    out["worst_naive"] = sorted(rows, key=lambda r: -abs(r["naive"]))[:5]
    out["worst_anchor"] = sorted(rows, key=lambda r: -abs(r["anchor"]))[:5]
    return out


def throughput(n_cues: int = 150, seconds: float = 60.0) -> dict:
    rng = np.random.default_rng(11)
    roles = ["whoosh", "impact", "ui_pop", "click", "swell", "glitch", "bell"]
    cues = [dict(t=float(t), role=roles[int(rng.integers(len(roles)))], dur=float(rng.choice([0.2, 0.4, 0.6, 0.9])),
                 gain_db=-8.0, pan=float(rng.uniform(-0.8, 0.8)), seed=int(rng.integers(1 << 20)))
            for t in np.sort(rng.uniform(0.5, seconds - 2, n_cues))]
    t0 = time.perf_counter()
    for i, c in enumerate(cues):  # upstream behaviour: every event rendered from scratch
        render_event(Event(t=c["t"], role=c["role"], dur=c["dur"], gain_db=c["gain_db"], pan=c["pan"], seed=c["seed"] + 1),
                     SR, seed=c["seed"] + 1, tail=True)
    base = time.perf_counter() - t0
    C.cache_clear()
    t0 = time.perf_counter()
    C.render_cues(cues, seconds, workers=1)
    cold1 = time.perf_counter() - t0
    C.cache_clear()
    t0 = time.perf_counter()
    C.render_cues(cues, seconds)
    cold = time.perf_counter() - t0
    t0 = time.perf_counter()
    C.render_cues(cues, seconds)
    warm = time.perf_counter() - t0
    return {"cues": n_cues, "seconds": seconds, "cpus": len(__import__("os").sched_getaffinity(0)),
            "upstream_s": base, "cold_1worker_s": cold1, "cold_s": cold, "warm_s": warm,
            "speedup_cold_1worker": base / cold1,
            "speedup_cold": base / cold, "speedup_warm": base / warm, "cache": C.cache_info(),
            "realtime_factor_cold": seconds / cold}


def dynamics(n: int = 24) -> dict:
    rng = np.random.default_rng(3)
    inten = rng.uniform(0.05, 1.0, n)
    from motionvid.cues import _gain
    from motionvid.genome import load
    g = load()
    res = {}
    for name, fn in (("fixed_gain", lambda v: -6.0), ("motion_gain", lambda v: _gain(v, g))):
        cues = [dict(t=0.6 + i * 0.5, role="whoosh", dur=0.4, gain_db=fn(v), pan=0.0, seed=7 + i) for i, v in enumerate(inten)]
        mix, _ = C.render_cues(cues, n * 0.5 + 1.5)
        peaks = [np.abs(mix[int((c["t"] - 0.25) * SR): int((c["t"] + 0.25) * SR)]).max() for c in cues]
        res[name + "_pearson"] = float(np.corrcoef(inten, peaks)[0, 1])
    return res


def run() -> dict:
    out = {"sync": sync(), "throughput": throughput(), "dynamics": dynamics()}
    s = out["sync"]
    out["headline"] = {
        "sync_median_improvement_x": s["naive"]["median_abs_ms"] / max(s["anchor"]["median_abs_ms"], 0.01),
        "sync_p95_improvement_x": s["naive"]["p95_abs_ms"] / max(s["anchor"]["p95_abs_ms"], 0.01),
        "defined_hit_p95_improvement_x": s["naive_defined"]["p95_abs_ms"] / max(s["anchor_defined"]["p95_abs_ms"], 0.01),
        "defined_hit_within_5ms": s["anchor_defined"]["within_5ms"],
        "throughput_cold_x": out["throughput"]["speedup_cold"],
        "throughput_warm_x": out["throughput"]["speedup_warm"],
    }
    return out


if __name__ == "__main__":
    res = run()
    (ROOT / "bench" / "results").mkdir(exist_ok=True)
    (ROOT / "bench" / "results" / "motionsync.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: res[k] for k in ("headline", "dynamics")}, indent=2))
    print(json.dumps({k: res["sync"][k] for k in ("naive", "anchor", "naive_defined", "anchor_defined")}, indent=2))
    print(json.dumps(res["throughput"], indent=2))
