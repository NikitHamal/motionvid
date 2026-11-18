"""FlawBench: nine audio flaws an expert reviewer found in the v0.2 showreel, each turned into a number.

Run: python bench/soundaudit.py            # classic engine vs scene engine on the same timeline(s)
Thresholds come from the review text, not from our results. Labels and thresholds are gate-protected (RSI may not edit them).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from motionvid.scene.master import lufs, true_peak_db  # noqa: E402
from motionvid.scene.telemetry import build  # noqa: E402
from motionvid.timeline import validate  # noqa: E402

SR = 48000
# name: (direction, pass threshold, score floor, score ceiling)
CHECKS = {
    "sub_coupling": (">=", 0.7, 0.0, 1.0),
    "air_vs_mid_db": (">=", -30.0, -70.0, -24.0),
    "dead_air_s": ("<=", 0.25, 4.0, 0.0),
    "pan_corr": (">=", 0.5, 0.0, 0.8),
    "motion_bright_corr": (">=", 0.3, 0.0, 0.6),
    "preroll_rise_db": (">=", 6.0, 0.0, 12.0),
    "glyph_ramp_rho": (">=", 0.4, 0.0, 0.8),
    "tail_300ms_db": (">=", -30.0, -60.0, -18.0),
    "master_lufs_err": ("<=", 1.5, 6.0, 0.0),
}


def _band_db(x: np.ndarray, lo: float, hi: float) -> float:
    s = sosfilt(butter(4, [lo, hi], "bp", fs=SR, output="sos"), x, axis=0)
    return float(10 * np.log10((s ** 2).mean() + 1e-20))


def _rms_db(x: np.ndarray, win: float) -> np.ndarray:
    n = int(win * SR)
    m = x[: len(x) // n * n].reshape(-1, n, x.shape[1])
    return 10 * np.log10((m ** 2).mean(axis=(1, 2)) + 1e-20)


def _rank(a: np.ndarray) -> np.ndarray:
    return np.argsort(np.argsort(a)).astype(float)


def audit(audio: np.ndarray, tl: dict, glyph_times: list[float], other_times: list[float]) -> dict:
    tl = validate(tl)
    mono = audio.mean(axis=1)
    mid = _band_db(audio, 200, 2000)
    out = {"sub_vs_mid_db": _band_db(audio, 20, 80) - mid, "air_vs_mid_db": _band_db(audio, 9000, 15000) - mid}
    r100 = _rms_db(audio, 0.1)[: int(tl["duration"] * 10) - 10]  # the last second is an intentional fade-out
    out["dead_air_s"] = float((r100 < -60).sum() * 0.1)
    out["longest_gap_s"] = float(max((len(g) for g in np.split(r100 < -60, np.flatnonzero(np.diff(r100 < -60)) + 1) if g[0]), default=0) * 0.1)
    # pan tracking: audio balance vs speed-weighted on-screen x
    tels = [t for t in build(tl) if t.kind != "text"]
    hop = int(0.05 * SR)
    nw = len(audio) // hop
    L = (audio[: nw * hop, 0].reshape(nw, hop) ** 2).mean(axis=1)
    R = (audio[: nw * hop, 1].reshape(nw, hop) ** 2).mean(axis=1)
    bal = (R - L) / (R + L + 1e-12)
    tc = (np.arange(nw) + 0.5) * 0.05
    w = sum(np.interp(tc, t.ts, t.speed) * (np.interp(tc, t.ts, t.op) > 0.05) for t in tels)
    vx = sum(np.interp(tc, t.ts, t.speed * t.xn) * (np.interp(tc, t.ts, t.op) > 0.05) for t in tels) / np.maximum(w, 1e-9)
    ok = (w > 0.15) & (10 * np.log10(L + R + 1e-20) > -50)
    out["pan_corr"] = float(np.corrcoef(bal[ok], vx[ok])[0, 1]) if ok.sum() > 8 and bal[ok].std() > 0 else 0.0
    out["pan_samples"] = int(ok.sum())
    # continuous motion: on-screen speed vs 2-8 kHz brightness, only while something moves
    k = sum(np.interp(tc, t.ts, t.speed) for t in tels)
    hf0 = sosfilt(butter(4, [2000, 8000], "bp", fs=SR, output="sos"), audio, axis=0)
    hfl = 10 * np.log10((hf0[: nw * hop] ** 2).mean(axis=1).reshape(nw, hop).mean(axis=1) + 1e-20)
    mv = k > 0.03
    out["motion_bright_corr"] = float(np.corrcoef(k[mv], hfl[mv])[0, 1]) if mv.sum() > 8 else 0.0
    # mass coupling: every growth of an on-screen shape should arrive with sub-bass (20-80 Hz) in the next 250 ms
    area = sum(np.interp(tc, t.ts, t.area) for t in tels)
    sub = np.abs(sosfilt(butter(4, [20, 80], "bp", fs=SR, output="sos"), mono))
    sub_env = 20 * np.log10(np.sqrt(np.convolve(sub ** 2, np.ones(int(0.02 * SR)) / int(0.02 * SR), "same")) + 1e-9)
    rise = area[5:] - area[:-5]
    grow, cl = [], []
    for i in list(np.flatnonzero(rise >= 0.02)) + [10 ** 9]:
        if cl and (i == 10 ** 9 or tc[i] - tc[cl[-1]] > 0.3):
            grow.append(tc[cl[int(np.argmax(rise[cl]))]])
            cl = []
        if i != 10 ** 9:
            cl.append(i)
    hit = 0
    for t0 in grow:
        a = sub_env[int(max(0, t0 - 0.5) * SR):int(max(0.01, t0 - 0.15) * SR)]
        b = sub_env[int(max(0, t0 - 0.1) * SR):int(min(tl["duration"], t0 + 0.3) * SR)]
        hit += int(a.size > 0 and b.size > 0 and b.max() - np.median(a) >= 6.0)
    out["sub_coupling"] = hit / len(grow) if grow else 1.0
    out["growth_events"] = len(grow)
    # pre-roll: 2-8 kHz envelope must be building into each cut and peaking on it
    hf = np.abs(sosfilt(butter(4, [2000, 8000], "bp", fs=SR, output="sos"), mono))
    env = np.sqrt(np.convolve(hf ** 2, np.ones(int(0.01 * SR)) / int(0.01 * SR), "same"))
    rises, offs, tails = [], [], []
    for c in tl["cuts"]:
        t0 = float(c["t"])
        e = lambda t: 20 * np.log10(env[int(np.clip(t, 0, tl["duration"] - 0.01) * SR)] + 1e-9)  # noqa: E731
        rises.append(max(e(t0 - 0.02), e(t0)) - e(t0 - 0.19))
        a, b = int((t0 - 0.1) * SR), int(min(tl["duration"], t0 + 0.3) * SR)
        offs.append(abs(a + int(np.argmax(env[a:b])) - t0 * SR) / SR * 1000)
        pk = env[int((t0 - 0.05) * SR):int((t0 + 0.05) * SR)].max()
        tails.append(20 * np.log10(env[int(min(tl["duration"] - 0.01, t0 + 0.3) * SR) - 1:][:int(0.02 * SR)].mean() / (pk + 1e-9) + 1e-9)) if t0 + 0.3 < tl["duration"] else None
    out["preroll_rise_db"] = float(np.median(rises)) if rises else 0.0
    out["cut_peak_offset_ms"] = float(np.median(offs)) if offs else 0.0
    t_ok = [x for x in tails if x is not None]
    out["tail_300ms_db"] = float(np.median(t_ok)) if t_ok else -60.0
    # glyph phrasing: pitch should climb within a word (isolated glyphs only; contaminated windows are skipped)
    iso = [t for t in glyph_times if not any(-0.03 <= o - t <= 0.08 for o in other_times)]
    rhos, grp = [], []
    for t in iso + [1e9]:
        if grp and t - grp[-1] > 0.4:
            pts = []
            for g in grp:
                seg = mono[int(g * SR):int(g * SR) + int(0.04 * SR)]
                sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 8192))
                f = np.fft.rfftfreq(8192, 1 / SR)
                m = (f > 400) & (f < 6000)
                pts.append(1200 * np.log2(f[m][np.argmax(sp[m])]))
            if len(pts) >= 4:
                rhos.append(float(np.corrcoef(_rank(np.arange(len(pts))), _rank(np.array(pts)))[0, 1]))
            grp = []
        grp.append(t)
    out["glyph_ramp_rho"] = float(np.median(rhos)) if rhos else 0.0
    out["glyph_groups"] = len(rhos)
    out["glyphs"] = len(glyph_times)
    out["lufs"] = lufs(audio)
    out["true_peak_dbtp"] = true_peak_db(audio)
    out["master_lufs_err"] = abs(out["lufs"] - (-16.0))
    return out


def judge(m: dict) -> dict:
    res, sc = {}, []
    for k, (op, thr, lo, hi) in CHECKS.items():
        res[k] = bool(m[k] >= thr if op == ">=" else m[k] <= thr)
        sc.append(float(np.clip((m[k] - lo) / (hi - lo), 0, 1)))
    if m["true_peak_dbtp"] > -0.95:
        res["master_lufs_err"] = False
    return {"passes": sum(res.values()), "of": len(res), "score": round(float(np.mean(sc)), 3), "detail": res}


def run(tl_path: Path, G: dict | None = None, classic: bool = True) -> dict:
    from motionvid.compose import render_cues
    from motionvid.cues import compile_cues
    from motionvid.scene.engine import render

    tl = validate(json.loads(tl_path.read_text()))
    cues = compile_cues(tl)
    a1, _ = render_cues(cues, tl["duration"]) if classic else (None, None)
    a2, info = render(tl, G)
    g1 = [c["t"] for c in cues if c["role"] == "click"]
    g2 = [e["t"] for e in info["events"] if e["role"] == "tick"]
    o1 = [c["t"] for c in cues if c["role"] != "click"]
    o2 = [e["t"] for e in info["events"] if e["role"] != "tick"]
    r = {}
    for name, a, g, o in (("classic", a1, g1, o1), ("scene", a2, g2, o2)):
        if a is None:
            continue
        m = audit(a, tl, g, o)
        r[name] = {**{k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()}, **judge(m)}
    return {"timeline": tl_path.name, **r}


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]] or [ROOT / "examples" / "showreel.json"]
    res = [run(p) for p in paths]
    print(json.dumps(res, indent=1))
