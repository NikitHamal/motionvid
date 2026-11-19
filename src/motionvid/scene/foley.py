"""Continuous layers bound to scene telemetry:
1. Continuous motion bed: `pink noise + root fifth drone` through a low-pass filter where
   `cutoff = 180 Hz + motion_energy * 1400 Hz` and `gain = -34 dB + motion_energy * 16 dB`, panned by `pan_x`.
2. Tactile L->R felt/brush slide, elastic bar stretch, warm morph shimmer, and continuous sub-mass coupling.
"""

from __future__ import annotations

import numpy as np

from .score import note_hz, seed_of
from .telemetry import HZ, Tel, motion_curves, smooth, windows
from .voices import SR, TAU, _tri_saw, biquad_tv, pink_noise


def _slice(ts: np.ndarray, i0: int, i1: int):
    n = int((i1 - i0) / HZ * SR)
    tt = np.linspace(ts[i0], ts[i1], n, endpoint=False)
    return n, tt, lambda a: np.interp(tt, ts, a)


def _stereo(mono: np.ndarray, xn: np.ndarray, G, spread: float = 0.0) -> np.ndarray:
    p = np.clip((xn - 0.5) * 2 * G["pan_width"] + spread, -1, 1)
    th = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(th), mono * np.sin(th)], axis=1) * np.sqrt(2)


def _stereo_pan(mono: np.ndarray, pan_x: np.ndarray, width: float = 0.78) -> np.ndarray:
    p = np.clip(pan_x * width, -1.0, 1.0)
    th = (p + 1.0) * np.pi / 4.0
    return np.stack([mono * np.cos(th), mono * np.sin(th)], axis=1) * np.sqrt(2)


def _add(buf: np.ndarray, ts: np.ndarray, i0: int, st: np.ndarray) -> None:
    s = int(ts[i0] * SR)
    e = min(len(buf), s + len(st))
    buf[s:e] += st[: e - s]


def motion_bed(buf: np.ndarray, tels: list[Tel], G: dict[str, float]) -> int:
    """Continuous warm filtered noise + root-fifth drone bed driven by motion_energy (0..1) and pan_x (-1..1).
    cutoff = 180 Hz + motion_energy * 1400 Hz, gain = -34 dB + motion_energy * 16 dB, panned by pan_x.
    Also couples sub-bass weight (52 Hz) to positive area growth so every visual expansion has physical mass.
    """
    if not tels:
        return 0
    ts = tels[0].ts
    energy_240, pan_240 = motion_curves(tels)
    n = min(len(buf), int(round(float(ts[-1]) * SR)))
    if n < 64:
        return 0
    tt = np.linspace(0.0, float(ts[-1]), n, endpoint=False)
    me = np.interp(tt, ts, energy_240)
    px = np.interp(tt, ts, pan_240)
    rng = np.random.default_rng(seed_of("continuous_motion_bed", len(tels)))
    # Root (110 Hz A2) + Fifth (165 Hz E3) + Octave (220 Hz A3) warm harmonic drone + pink noise
    drone = (
        0.55 * _tri_saw(TAU * 110.0 * tt, 0.22)
        + 0.38 * _tri_saw(TAU * 165.0 * tt + 0.7, 0.20)
        + 0.22 * np.sin(TAU * 220.0 * tt + 1.4)
    )
    pn = pink_noise(n, rng) * 1.15
    cutoff = 180.0 + me * 1400.0
    filtered = biquad_tv(drone + pn, cutoff, 1.25, "lp", block=256) * 1.45
    gain_db = -34.0 + me * 16.0
    gain = 10.0 ** (gain_db / 20.0)
    sig = filtered * gain
    buf[:n] += _stereo_pan(sig, px, width=max(0.72, float(G.get("pan_width", 0.65))))
    # Continuous sub-bass mass coupling for non-text shape expansions (50 Hz sine burst on positive d(area)/dt)
    shaped = [T for T in tels if T.kind != "text"]
    if shaped:
        tot_a = sum(T.area for T in shaped)
        step = int(0.25 * HZ)
        rise = np.zeros_like(tot_a)
        rise[:-step] = np.maximum(0.0, tot_a[step:] - tot_a[:-step])
        sub_env_240 = np.clip(smooth(rise, 0.04) / 0.06, 0.0, 1.0)
        sub_env = np.interp(tt, ts, sub_env_240)
        sub_wave = np.sin(TAU * 52.0 * tt) * (sub_env ** 1.3) * (10.0 ** ((G["sub_db"] - 4.5) / 20.0))
        buf[:n] += _stereo_pan(sub_wave, px, width=0.35)
    return 1


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
        s_ref = max(1.2, float(np.percentile(sm[sm > 0.03], 92)) if (sm > 0.03).any() else 1.2)
        sp_norm = np.clip(f(sm) / s_ref, 0.0, 1.35)
        pn = pink_noise(n, rng)
        felt = biquad_tv(pn, 300.0 + 600.0 * np.clip(sp_norm, 0, 1), 1.1, "bp") * (sp_norm ** 0.85) * 0.85
        # dB-linear 2-8 kHz brightness scaling with speed so log-band energy tracks speed linearly
        studio = G.get("rev", 5) >= 6  # rev 6: the brush moves down from 3.2-5.4 kHz to 0.9-1.7 kHz with a gentler speed slope (no static hiss)
        brush_db = G["texture_db"] - 7.0 + (12.0 * sp_norm - 4.0 if studio else 20.0 * sp_norm)
        sp_c = np.clip(sp_norm, 0, 1)
        brush_fc = (900.0 + 800.0 * sp_c) if studio else (3200.0 + 2200.0 * sp_c)
        brush = biquad_tv(rng.standard_normal(n), brush_fc, 0.85, "bp") * (10.0 ** (brush_db / 20.0))
        g_felt = 10.0 ** ((G["texture_db"] + 4.0) / 20.0)
        vx_w = f(vx)
        if (vx_w.min() < -0.1 or vx_w.max() > 1.1) and np.ptp(vx_w) > 0.25:
            vx_w = (vx_w - vx_w.min()) / (np.ptp(vx_w) + 1e-9)
        xn_pan = np.clip(0.5 + (vx_w - 0.5) * 1.55, 0.0, 1.0)
        _add(buf, ts, i0, _stereo(felt * g_felt + brush, xn_pan, G))
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
    for i0, i1 in windows(tot_rate > 0.18):
        n, tt, f = _slice(ts, i0, i1)
        if n < 64:
            continue
        gn = np.clip(f(tot_rate) / max(1.4, 0.55 * len(bars)), 0, 1) ** 0.68
        fr = 220.0 * (2 ** ((2.6 * (f(mean_w) - 0.4)) / 12))
        ph = np.cumsum(TAU * fr / SR)
        elastic = biquad_tv(_tri_saw(ph, 0.28), 280.0 + 1100.0 * gn, 1.15, "lp") * 0.52
        brush = biquad_tv(pink_noise(n, rng), 260.0 + 1350.0 * gn, 1.25, "lp") * 0.85
        _add(buf, ts, i0, _stereo((elastic + brush) * gn * 10 ** ((G["stretch_db"] + 5.5) / 20), f(mean_xn), G))
        count += 1
    return count


def shimmer(buf: np.ndarray, tels: list[Tel], G: dict[str, float]) -> int:
    """Smooth warm harmonic pad swell (< 1.2 kHz, <= 3 semitones) during star-to-circle blob morphs."""
    blobs = [T for T in tels if T.kind == "blob" and "amp" in T.el.get("tracks", {})]
    if not blobs:
        return 0
    ts = blobs[0].ts
    rates = [np.abs(np.gradient(T.amp)) * HZ * ((T.op > 0.02) & (T.scale > 0.05)) for T in blobs]
    tot_amp = smooth(sum(rates), 0.06)
    mean_amp = sum(T.amp for T in blobs) / len(blobs)
    mean_xn = sum(T.xn * (r + 1e-6) for T, r in zip(blobs, rates)) / (sum(rates) + 1e-6 * len(blobs))
    count = 0
    for i0, i1 in windows(tot_amp > 0.025):
        n, tt, f = _slice(ts, i0, i1)
        if n < 64:
            continue
        gn = np.clip(f(tot_amp) / max(0.22, 0.065 * len(blobs)), 0, 1) ** 0.65
        f1 = note_hz(0, 0) * (2 ** ((2.0 * f(mean_amp)) / 12))
        f2 = note_hz(2, 0) * (2 ** ((2.0 * f(mean_amp)) / 12))
        ph1, ph2 = np.cumsum(TAU * f1 / SR), np.cumsum(TAU * f2 / SR)
        pad_sig = biquad_tv(0.65 * _tri_saw(ph1, 0.2) + 0.45 * _tri_saw(ph2, 0.2), 340.0 + 820.0 * gn, 1.0, "lp")
        _add(buf, ts, i0, _stereo(pad_sig * gn * 10 ** ((G["shimmer_db"] + 6.5) / 20), f(mean_xn), G))
        count += 1
    return count


def render_layers(buf: np.ndarray, tels: list[Tel], G: dict[str, float], rev: int = 5) -> dict[str, int]:
    """rev 6: the continuous bed moves to `studio_bed.abs_layers` (absolute dBFS); texture/stretch/shimmer stay."""
    return {
        "motion_bed": motion_bed(buf, tels, G) if rev < 6 else 1,
        "texture": texture(buf, tels, G),
        "stretch": stretch(buf, tels, G),
        "shimmer": shimmer(buf, tels, G),
    }
