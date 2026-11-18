"""StudioBench: the four synthesis bottlenecks and the polish checklist from the v0.4 Launch audit, as numbers (rev 5 vs rev 6).

Run: python bench/studio_audit.py [examples/launch.json]   -> docs/media/studio_audit.json
Thresholds come from the audit text. Labels and thresholds are gate-protected (RSI may not edit them).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from motionvid.scene import params, studio as S, voices as V  # noqa: E402
from motionvid.scene.engine import render  # noqa: E402
from motionvid.scene.studio_bed import bed_curves  # noqa: E402
from motionvid.scene.telemetry import HZ, build  # noqa: E402

SR = 48000


def _db(x) -> float:
    return float(10 * np.log10(np.mean(np.square(x)) + 1e-20))


def _band(x, lo, hi):
    return sosfilt(butter(4, [lo, hi], "bp", fs=SR, output="sos"), x)


def _hf_share_db(x, f0=2200.0) -> float:
    hi = sosfilt(butter(4, f0, "hp", fs=SR, output="sos"), x)
    return _db(hi) - _db(x)


def _freq(x) -> float:
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x)), 16384))
    f = np.fft.rfftfreq(16384, 1 / SR)
    return float(f[(f > 150) & (f < 6000)][np.argmax(sp[(f > 150) & (f < 6000)])])


def _centroid(x) -> float:
    sp = np.abs(np.fft.rfft(x * np.hanning(len(x)), 8192))
    f = np.fft.rfftfreq(8192, 1 / SR)
    return float((sp * f).sum() / (sp.sum() + 1e-12))


def quiet_floor(audio, events, tels, tl):
    """Final-mix level and 2-8 kHz level in windows with no motion and no event for 0.7 s (the 'idle bed')."""
    me, _ = bed_curves(tels)
    ev = np.array([e["t"] for e in events])
    rms, hf, blk = [], [], int(0.1 * SR)
    mono = audio.mean(axis=1)
    h = _band(mono, 2000, 8000)
    for i in range(int(tl["duration"] * 10) - 10):
        t = i / 10
        if me[int(t * HZ):int((t + 0.1) * HZ) + 1].max() < 0.12 and not ((ev > t - 0.4) & (ev < t + 0.1)).any():
            rms.append(_db(mono[i * blk:(i + 1) * blk]))
            hf.append(_db(h[i * blk:(i + 1) * blk]))
    return (float(np.median(rms)), float(np.median(hf)), len(rms)) if rms else (-90.0, -90.0, 0)


def whoosh_stats(sig, anchor):
    env = np.sqrt(np.convolve(sig ** 2, np.ones(int(0.01 * SR)) / int(0.01 * SR), "same"))
    pk = int(np.argmax(env))
    below = lambda lvl, a, b: next((i for i in range(a, b) if env[i] < env[pk] * lvl), b)  # noqa: E731
    ramp_ms = (pk - next(i for i in range(pk) if env[i] > env[pk] * 0.01)) / SR * 1000
    dec40_ms = (below(0.01, pk, len(env) - 1) - pk) / SR * 1000
    return {"hf_above_2k2_db": round(_hf_share_db(sig), 1), "peak_offset_ms": round((pk - anchor) / SR * 1000, 1),
            "ramp_in_ms": round(ramp_ms, 0), "decay_40db_ms": round(dec40_ms, 0)}


def voices(rev):
    rng = np.random.default_rng(3)
    if rev >= 6:
        tick, _ = S.text_tick6(2.0, rng)
        pluck, _ = S.hero_pluck6(392.0, rng)
        who = S.whoosh6(0.16, 0.22, 0.8, rng)
        ris, _ = S.riser6(0.55, rng)
    else:
        tick, _ = V.text_tick(520.0, rng)
        pluck, _ = V.pluck(392.0, 0.16, rng)
        who = V.whoosh(0.16, 0.18, 0.8, rng)
        ris, _ = V.riser(0.55, rng)
    n = len(pluck)
    w = lambda a, b: pluck[int(a * SR):int(b * SR)]  # noqa: E731
    return {
        "tick_ms": round(len(tick) / SR * 1000, 1),
        "tick_pitch_ratio": round(_freq(np.pad(tick[int(0.007 * SR):], (0, 2048))) / max(1.0, _freq(np.pad(tick[:int(0.007 * SR)], (0, 2048)))), 2),
        "pluck_drift_cents": round(1200 * np.log2(_freq(w(0.012, 0.05)) / _freq(w(0.0, 0.03))), 0),
        "pluck_mallet_5ms_db": round(_db(pluck[: int(0.005 * SR)]) - _db(pluck[int(0.02 * SR):int(0.06 * SR)]), 1),
        "riser_centroid_rise": round(_centroid(ris[-int(0.1 * SR):]) / _centroid(ris[int(0.05 * SR):int(0.15 * SR)]), 1),
        "whoosh": whoosh_stats(*who),
    }


def run(path: Path) -> dict:
    tl = json.loads(path.read_text())
    out = {"timeline": path.name}
    for rev in (5, 6):
        G = {**params.load(), "rev": rev}
        audio, info = render(tl, G)
        ev, tels = info["events"], build(tl)
        floor, hf, nwin = quiet_floor(audio, ev, tels, tl)
        ticks = np.array([e["t"] for e in ev if e["role"] == "tick"])
        bounce = [e for e in ev if e["role"] == "impact" and "bounce" in e["why"]]
        pans = [e["pan"] for e in ev if e["role"] == "tick"]
        r = voices(rev)
        r.update({"idle_floor_dbfs": round(floor, 1), "idle_hf_2k_8k_dbfs": round(hf, 1), "continuous_hf_2k_8k_dbfs": info["continuous_hf_2k_8k_dbfs"],
                  "continuous_rms_dbfs": info["continuous_rms_dbfs"], "idle_windows": nwin,
                  "bed_peak_db": info["bed"].get("bed_peak_db"), "bed_idle_db": info["bed"].get("bed_idle_db"),
                  "min_tick_gap_ms": round(float(np.diff(ticks).min() * 1000), 0) if len(ticks) > 1 else None,
                  "tick_pan_range": [round(min(pans), 2), round(max(pans), 2)] if pans else None,
                  "bounce_gains_db": [round(e["gain_db"] - bounce[0]["gain_db"], 1) for e in bounce],
                  "riser_gain_db": [e["gain_db"] for e in ev if e["role"] == "riser"],
                  "roles_with_reverb": ["tick", "pluck", "crystal", "air"] if rev >= 6 else ["all"], "lufs": info["lufs"]})
        out[f"rev{rev}"] = r
    a, b = out["rev5"], out["rev6"]
    gates = {
        "bed_idle_floor_le_-44": (b["bed_idle_db"] or 0) <= -44 and b["idle_floor_dbfs"] <= a["idle_floor_dbfs"] - 6,
        "bed_peak_le_-20": (b["bed_peak_db"] or 0) <= -20,
        "bed_hiss_2k_8k_down_10db": b["continuous_hf_2k_8k_dbfs"] <= a["continuous_hf_2k_8k_dbfs"] - 10,
        "whoosh_hf_le_-30db": b["whoosh"]["hf_above_2k2_db"] <= -30,
        "whoosh_peak_on_cut_5ms": abs(b["whoosh"]["peak_offset_ms"]) <= 5,
        "whoosh_ramp_in_120_190ms": 120 <= b["whoosh"]["ramp_in_ms"] <= 190,
        "whoosh_decay_160_260ms": 160 <= b["whoosh"]["decay_40db_ms"] <= 260,
        "tick_14ms": b["tick_ms"] <= 14.5,
        "tick_zero_pitch_drop": b["tick_pitch_ratio"] >= 0.95,
        "tick_rate_cap_90ms": (b["min_tick_gap_ms"] or 999) >= 89,
        "tick_pan_within_0.35": all(abs(p) <= 0.351 for p in (b["tick_pan_range"] or [0])),
        "pluck_no_bend_25c": abs(b["pluck_drift_cents"]) <= 25,
        "pluck_mallet_transient": b["pluck_mallet_5ms_db"] >= 0,
        "bounce_steps_-4.5": all(abs(g + 4.5 * i) <= 0.2 for i, g in enumerate(b["bounce_gains_db"])) and len(b["bounce_gains_db"]) >= 3,
        "riser_boost_4.5db": abs((b["riser_gain_db"][0] - a["riser_gain_db"][0]) - 4.5) <= 0.1,
        "riser_sweep_rises": b["riser_centroid_rise"] >= 3,
        "lufs_within_0.6": abs(b["lufs"] + 16) <= 0.6,
    }
    gates = {k: bool(v) for k, v in gates.items()}
    out["gates"], out["passed"] = gates, f"{sum(gates.values())}/{len(gates)}"
    return out


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "examples" / "launch.json"
    res = run(p)
    (ROOT / "docs" / "media" / "studio_audit.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "gates"}, indent=1))
    print({k: v for k, v in res["gates"].items() if not v} or "all gates pass", res["passed"])
