"""ReelCheck: gates for a rendered video timeline (audio/visual hit alignment, level safety, coverage).

Unlike MotionSync-Bench (role x duration grid), this measures a real production timeline end to end:
for every non-click cue, find the first 70 % envelope crossing of the RENDERED audio in a +-80 ms window
around the cue time and report the error. Run: python bench/reelcheck.py [timeline.json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from motionvid.compose import SR, render_cues  # noqa: E402
from motionvid.cues import compile_cues  # noqa: E402
from motionvid.timeline import validate  # noqa: E402

FRAME_MS = 1000 / 30


def run(path: Path) -> dict:
    tl = validate(json.loads(path.read_text()))
    cues = compile_cues(tl)
    audio, _ = render_cues(cues, tl["duration"])
    mono = np.abs(audio).max(axis=1)
    w = int(0.005 * SR)
    c = np.cumsum(np.concatenate([[0.0], mono.astype(np.float64) ** 2]))
    env = np.sqrt((c[w:] - c[:-w]) / w)
    errs = []
    for q in cues:
        if q["role"] == "click":
            continue
        a, b = max(0, int((q["t"] - 0.08) * SR)), min(len(env), int((q["t"] + 0.08) * SR))
        seg = env[a:b]
        if seg.size == 0 or seg.max() < 1e-4:
            continue
        i = int(np.argmax(seg >= 0.7 * seg.max()))
        errs.append(abs((a + i) / SR - q["t"]) * 1000)
    e = np.array(errs)
    return {
        "timeline": path.name, "duration_s": tl["duration"], "cues": len(cues), "scored": int(e.size),
        "median_err_ms": round(float(np.median(e)), 1), "p95_err_ms": round(float(np.percentile(e, 95)), 1),
        "within_1_frame": round(float((e <= FRAME_MS).mean()), 3),
        "peak": round(float(np.abs(audio).max()), 3), "cue_density_per_s": round(len(cues) / tl["duration"], 2),
    }


GATES = {"median_err_ms": ("<=", 12.0), "within_1_frame": (">=", 0.75), "peak": ("<=", 0.98)}


def check(r: dict) -> list[str]:
    return [f"{k} {r[k]} violates {op} {v}" for k, (op, v) in GATES.items()
            if not (r[k] <= v if op == "<=" else r[k] >= v)]


if __name__ == "__main__":
    res = run(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "examples" / "showreel.json")
    print(json.dumps(res, indent=2))
    bad = check(res)
    print("GATES OK" if not bad else "GATES FAILED: " + "; ".join(bad))
    sys.exit(1 if bad else 0)
