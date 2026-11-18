"""Continuous layers bound to scene telemetry (composite gestures, tactile L->R felt slide, elastic brush, warm morph pad).

  velocity -> tactile felt slide (300->900 Hz pink noise) + speed-coupled brush, panned dynamically with composite vx(t)
  w-rate   -> single composite low-pass filtered brush/elastic sweep across stretching bars (no multi-bar FM clutter)
  amp-rate -> warm harmonic pad swell (< 900 Hz, <= 3 semitones) during star-to-circle morphs
"""

from __future__ import annotations

import numpy as np

from .score import note_hz, seed_of
from .telemetry import HZ, Tel, smooth, windows
from .voices import SR, TAU, _tri_saw, biquad_tv, pink_noise


def _slice(ts: np.ndarray, i0: int, i1: int):
    n = int((i1 - i0) / HZ * SR)
    tt = np.linspace(ts[i0], ts[i1], n, endpoint=False)
    return n, tt, lambda a: np.interp(tt, ts, a)


def _stereo(mono: np.ndarray, xn: np.ndarray, G, spread: float = 0.0) -> np.ndarray:
    p = np.clip((xn - 0.5) * 2 * G["pan_width"] + spread, -1, 1)
    th = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(th), mono * np.sin(th)], axis=1) * np.sqrt(2)


def _add(buf: np.ndarray, ts: np.ndarray, i0: int, st: np.ndarray) -> None:
    s = int(ts[i0] * SR)
    e = min(len(buf), s + len(st))
    buf[s:e] += st[: e - s]


def texture(buf: np.ndarray, tels: list[Tel], G: dict[str, float]) -> int:
    """Composite tactile mechanical/felt slide (300->900 Hz) + high-air brush tracked to speed-weighted on-screen x."""
    shaped = [T for T in tels if T.kind != "text"]
    if not shaped:
        return 0
    ts = shaped[0].ts
    w_tot = sum(T.speed * (T.op > 0.05) for T in shaped)
    vx = sum(T.speed * T.xn * (T.op > 0.05) for T in shaped) / np.maximum(w_tot, 1e-9)
    sm = smooth(w_tot, 0.03)
    rng = np.random.default_rng(seed_of("composite_texture", len(shaped)))
    count = 0
    for i0, i1 in windows(sm > 0.03):
        n, tt, f = _slice(ts, i0, i1)
        if n < 64:
            continue
        env = np.clip(f(sm) / 1.4, 0, 1.5)
        pn = pink_noise(n, rng)
        # Tactile mechanical/felt slide (300 Hz -> 900 Hz bandpass pink noise)
        felt = biquad_tv(pn, 300.0 + 600.0 * np.clip(env, 0, 1), 1.1, "bp") * 0.85
        # Speed-coupled brush (couples 2-8 kHz brightness to motion speed)
        brush = biquad_tv(rng.standard_normal(n), 2800.0 + 2600.0 * np.clip(env, 0, 1), 0.9, "bp") * (env ** 1.25) * 0.55
        g = 10 ** ((G["texture_db"] + 3.5) / 20)
        # Stronger stereo pan tracking so composite motion balances cleanly L->R
        xn_pan = np.clip(0.5 + (f(vx) - 0.5) * 1.45, 0.0, 1.0)
        _add(buf, ts, i0, _stereo((felt + brush) * (env ** 0.95) * g, xn_pan, G))
        count += 1
    return count


def stretch(buf: np.ndarray, tels: list[Tel], G: dict[str, float]) -> int:
    """One continuous low-pass filtered brush/elastic sweep tied to total bar width variance."""
    bars = [T for T in tels if T.kind == "rrect" and float(T.w.max() - T.w.min()) >= 200 and T.area.max() < 2.0]
    if not bars:
        return 0
    ts = bars[0].ts
    W = 1920.0
    rates = [np.abs(np.gradient(T.w)) * HZ / W * ((T.op > 0.02) & (T.scale > 0.05)) for T in bars]
    tot_rate = smooth(sum(rates), 0.05)
    mean_w = sum(T.w for T in bars) / (len(bars) * W)
    mean_xn = sum(T.xn * (r + 1e-6) for T, r in zip(bars, rates)) / (sum(rates) + 1e-6 * len(bars))
    rng = np.random.default_rng(seed_of("composite_stretch", len(bars)))
    count = 0
    for i0, i1 in windows(tot_rate > 0.25):
        n, tt, f = _slice(ts, i0, i1)
        if n < 64:
            continue
        gn = np.clip(f(tot_rate) / max(1.8, 0.7 * len(bars)), 0, 1) ** 0.75
        # Subtle <= 3 semitone low-mid elastic body + low-pass pink noise brush (300 -> 1400 Hz, Q=1.2)
        fr = 220.0 * (2 ** ((2.8 * (f(mean_w) - 0.4)) / 12))
        ph = np.cumsum(TAU * fr / SR)
        elastic = biquad_tv(_tri_saw(ph, 0.28), 280.0 + 950.0 * gn, 1.1, "lp") * 0.45
        brush = biquad_tv(pink_noise(n, rng), 260.0 + 1250.0 * gn, 1.2, "lp") * 0.75
        _add(buf, ts, i0, _stereo((elastic + brush) * gn * 10 ** ((G["stretch_db"] + 3.0) / 20), f(mean_xn), G))
        count += 1
    return count


def shimmer(buf: np.ndarray, tels: list[Tel], G: dict[str, float]) -> int:
    """Smooth warm harmonic pad swell (< 1.1 kHz, <= 3 semitones) during star-to-circle blob morphs."""
    blobs = [T for T in tels if T.kind == "blob" and "amp" in T.el.get("tracks", {})]
    if not blobs:
        return 0
    ts = blobs[0].ts
    rates = [np.abs(np.gradient(T.amp)) * HZ * ((T.op > 0.02) & (T.scale > 0.05)) for T in blobs]
    tot_amp = smooth(sum(rates), 0.06)
    mean_amp = sum(T.amp for T in blobs) / len(blobs)
    mean_xn = sum(T.xn * (r + 1e-6) for T, r in zip(blobs, rates)) / (sum(rates) + 1e-6 * len(blobs))
    count = 0
    for i0, i1 in windows(tot_amp > 0.03):
        n, tt, f = _slice(ts, i0, i1)
        if n < 64:
            continue
        gn = np.clip(f(tot_amp) / max(0.25, 0.08 * len(blobs)), 0, 1) ** 0.7
        f1 = note_hz(0, 0) * (2 ** ((2.0 * f(mean_amp)) / 12))
        f2 = note_hz(2, 0) * (2 ** ((2.0 * f(mean_amp)) / 12))
        ph1, ph2 = np.cumsum(TAU * f1 / SR), np.cumsum(TAU * f2 / SR)
        pad_sig = biquad_tv(0.65 * _tri_saw(ph1, 0.2) + 0.45 * _tri_saw(ph2, 0.2), 340.0 + 720.0 * gn, 1.0, "lp")
        _add(buf, ts, i0, _stereo(pad_sig * gn * 10 ** ((G["shimmer_db"] + 4.0) / 20), f(mean_xn), G))
        count += 1
    return count


def render_layers(buf: np.ndarray, tels: list[Tel], G: dict[str, float]) -> dict[str, int]:
    return {
        "texture": texture(buf, tels, G),
        "stretch": stretch(buf, tels, G),
        "shimmer": shimmer(buf, tels, G),
    }
