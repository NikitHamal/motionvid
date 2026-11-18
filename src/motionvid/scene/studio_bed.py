"""Absolute-level continuous layers (engine rev 6), added after loudness normalisation so dBFS targets are literal.

- motion bed: pink noise, low-pass 110 Hz (idle) -> 780 Hz (peak motion), level -46 dBFS idle -> -22 dBFS at peak.
- sub hum: 55 Hz + 110 Hz soft triangle at -32 dBFS RMS, scaled by motion_energy.
- fifth pad: 240 Hz + 360 Hz, low-passed, -28 dBFS RMS, tied to the 5-bar width-morph curve (tension = sharpened fifth).
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter1d

from .score import seed_of
from .telemetry import HZ, Tel, smooth
from .voices import SR, TAU, _tri, biquad_tv, lpf24_tv, pink_noise

BED_IDLE_DB, BED_PEAK_DB, HUM_DB, PAD_DB = -46.0, -22.0, -32.0, -28.0
LP_IDLE, LP_PEAK = 110.0, 780.0


def _rms_flat(x: np.ndarray, win: float = 0.12) -> np.ndarray:
    return x / np.sqrt(uniform_filter1d(x * x, int(win * SR), mode="nearest") + 1e-12)


def _pan(mono: np.ndarray, p: np.ndarray) -> np.ndarray:
    th = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([mono * np.cos(th), mono * np.sin(th)], axis=1) * np.sqrt(2)


def _bars(tels: list[Tel]) -> list[Tel]:
    return [T for T in tels if T.kind == "rrect" and float(T.w.max() - T.w.min()) >= 200 and T.area.max() < 2.0]


def _pad_env(tels: list[Tel], tt: np.ndarray, ts: np.ndarray):
    bars = _bars(tels)
    if not bars:
        return None, None
    act = sum(((T.op > 0.02) & (T.scale > 0.05)).astype(float) for T in bars) / len(bars)
    mean_w = sum(T.w * ((T.op > 0.02) & (T.scale > 0.05)) for T in bars) / np.maximum(act * len(bars), 1e-9)
    rate = smooth(sum(np.abs(np.gradient(T.w)) * HZ / 1920.0 for T in bars), 0.12)
    tension = np.clip(rate / max(1e-6, float(np.percentile(rate[rate > 0.05], 90)) if (rate > 0.05).any() else 1.0), 0, 1)
    env = smooth(act, 0.3) * (0.4 + 0.6 * smooth(tension, 0.2))
    morph = np.clip((mean_w - mean_w[act > 0.5].min()) / max(1e-6, np.ptp(mean_w[act > 0.5])), 0, 1) if (act > 0.5).any() else 0 * mean_w
    return np.interp(tt, ts, env), np.interp(tt, ts, smooth(morph, 0.1))


def bed_curves(tels: list[Tel], W: float = 1920.0) -> tuple[np.ndarray, np.ndarray]:
    """motion_energy for the bed: physical shapes only (decorative rings excluded), normalised to the 96th percentile
    of the smoothed activity so mid motion sits mid-way and stillness really is idle."""
    shaped = [T for T in tels if T.kind in ("blob", "circle", "rrect") and T.area.max() < 2.0]
    ts = tels[0].ts
    act, wx = np.zeros_like(ts), np.zeros_like(ts)
    for T in shaped:
        vis = ((T.op > 0.02) & (T.scale > 0.03)).astype(float)
        a = (T.speed + 0.4 * (np.abs(np.gradient(T.w * T.scale)) + np.abs(np.gradient(T.h * T.scale))) * HZ / W
             + 0.8 * np.abs(np.gradient(T.amp)) * HZ * 4.0) * vis
        act += a
        wx += a * ((T.xn - 0.5) * 2.0)
    sm = smooth(act, 0.09)
    ref = max(1e-6, float(np.percentile(sm[sm > 0.02], 80))) if (sm > 0.02).any() else 1.0
    me = np.clip(sm / ref, 0.0, 1.0) ** 0.6
    dur = float(ts[-1])
    if dur > 1.2:
        me = me * np.clip((dur - ts) / 1.0, 0.0, 1.0)
    return me, np.clip(smooth(wx / np.maximum(act, 1e-6), 0.05), -1.0, 1.0)


def duck_curve(times: list[float], n: int, depth_db: float = 12.0) -> np.ndarray:
    """Side-chain gain (1 ms grid): bed/pad dip `depth_db` for 50 ms from each text_tick, then release over ~120 ms."""
    m = n // (SR // 1000) + 1
    hit = np.zeros(m)
    for t in times:
        hit[max(0, int((t - 0.005) * 1000)):int((t + 0.045) * 1000) + 1] = 1.0
    env, r = np.zeros(m), np.exp(-1.0 / 120.0)
    for i in range(m):
        env[i] = max(hit[i], (env[i - 1] * r) if i else 0.0)
    g = 1.0 - (1.0 - 10 ** (-depth_db / 20)) * env
    return np.interp(np.arange(n) / SR * 1000.0, np.arange(m), g)


def abs_layers(tels: list[Tel], n: int, G: dict[str, float], duck: list[float] | None = None) -> tuple[np.ndarray, dict[str, float]]:
    """Returns (n, 2) stereo layer at absolute dBFS plus measured stats."""
    out = np.zeros((n, 2))
    if not tels or n < 256:
        return out, {}
    ts = tels[0].ts
    me240, px240 = bed_curves(tels)
    tt = np.linspace(0.0, float(ts[-1]), n, endpoint=False)
    me, px = np.interp(tt, ts, me240), np.interp(tt, ts, px240)
    rng = np.random.default_rng(seed_of("studio_bed", len(tels)))
    # 1. motion bed: darker, quieter, idle floor -46 dBFS
    fc = LP_IDLE + (LP_PEAK - LP_IDLE) * me ** 0.9
    bed = _rms_flat(lpf24_tv(pink_noise(n, rng), fc, q=0.9))
    bed_db = BED_IDLE_DB + (BED_PEAK_DB - BED_IDLE_DB) * me ** 1.1 + float(G.get("bed6_trim_db", 0.0))
    bed *= 10 ** (bed_db / 20)
    # 2. tuned sub hum (55 + 110 Hz soft triangle), modulated by motion_energy
    hum = _tri(TAU * 55.0 * tt) + 0.6 * _tri(TAU * 110.0 * tt + 0.9)
    hum = biquad_tv(hum, 240.0, 0.8, "lp", block=512)
    hum *= 10 ** (HUM_DB / 20) / np.sqrt((hum ** 2).mean() + 1e-12) * (0.15 + 0.85 * me) ** 1.3 * me.clip(0, 1) ** 0.25
    out += _pan(bed + hum, px * 0.65)
    stats = {"bed_idle_db": 0.0, "bed_peak_db": 0.0}
    # 3. warm fifth pad bound to the bar morph
    env, morph = _pad_env(tels, tt, ts)
    if env is not None:
        cents = 14.0 * morph  # tension: the fifth sharpens as the bars narrow toward the funnel
        f1, f2 = 240.0 * (1 + 0.012 * (1 - morph)), 360.0 * 2 ** (cents / 1200.0)
        pad = np.sin(TAU * np.cumsum(f1) / SR) + 0.8 * _tri(TAU * np.cumsum(f2) / SR)
        pad = lpf24_tv(pad, 520.0 + 700.0 * morph, q=0.8)
        pad *= 10 ** ((PAD_DB + float(G.get("pad6_trim_db", 0.0))) / 20) / np.sqrt((pad ** 2).mean() + 1e-12) * env
        out += np.stack([pad, pad], axis=1) * 1.0
    if duck:
        out *= duck_curve(duck, n)[:, None]
    blk = int(0.1 * SR)
    m = n // blk * blk
    db = 10 * np.log10((bed[:m].reshape(-1, blk) ** 2).mean(axis=1) + 1e-20)
    stats = {"bed_idle_db": round(float(np.percentile(db, 8)), 1), "bed_peak_db": round(float(db.max()), 1),
             "bed_lp_max_hz": LP_PEAK, "has_pad": float(env is not None)}
    return out, stats
