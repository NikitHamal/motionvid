"""Hand-written agency-grade DSP voices for the scene engine. Every voice returns (mono float64, anchor sample).

Enforces exact synthesis presets:
1. `whoosh` / `suction`: pink noise -> 24dB/oct resonant Low-Pass Filter (Q = 2.2) sweeping exponentially
   `140 Hz -> 3.4 kHz` (`suction`, hard-gated at end) or `2.6 kHz -> 120 Hz` (`whoosh`).
2. `impact` + `sub`: sine sub-drop (`92 Hz -> 36 Hz` over `190 ms`) + triangle mid-punch (`165 Hz -> 62 Hz`
   over `55 ms`) + `5 ms` high-passed click (`> 2.2 kHz`) through a soft-clipper (`tanh`).
3. `text_tick` (`tick`): `18 ms` of bandpass-filtered noise (`1.4 kHz - 2.8 kHz`) with `3 ms` attack,
   `15 ms` exponential decay, andstationary damped `1.6 kHz` body — zero sine pitch drop.
4. `crystal`: two detuned high-frequency sine/triangle partials (`2093 Hz` + `3136 Hz`, `+7 cents` detune)
   with a `120 ms` glassy decay and stereo shimmer.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import lfilter

SR = 48000
TAU = 2 * np.pi
PINK_B = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
PINK_A = [1.0, -2.494956002, 2.017265875, -0.522189400]


def _t(dur: float) -> np.ndarray:
    return np.arange(max(1, int(round(dur * SR)))) / SR


def pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return lfilter(PINK_B, PINK_A, rng.standard_normal(n))


def norm(x: np.ndarray, peak: float = 1.0) -> np.ndarray:
    m = float(np.abs(x).max())
    return x * (peak / m) if m > 1e-12 else x


def taper(x: np.ndarray, ms: float = 4.0) -> np.ndarray:
    n = min(len(x) // 2, max(1, int(ms * SR / 1000)))
    x = x.copy()
    x[-n:] *= np.linspace(1, 0, n)
    return x


def biquad_tv(x: np.ndarray, f, q: float = 0.8, kind: str = "lp", block: int = 128) -> np.ndarray:
    """Time-varying RBJ biquad. `f` is a scalar or per-sample cutoff/centre array in Hz."""
    f = np.broadcast_to(np.asarray(f, dtype=float), x.shape)
    out, zi = np.empty_like(x), np.zeros(2)
    for s in range(0, len(x), block):
        w = TAU * float(np.clip(f[s], 20, SR * 0.45)) / SR
        c, al = np.cos(w), np.sin(w) / (2 * q)
        b = {"lp": [(1 - c) / 2, 1 - c, (1 - c) / 2], "hp": [(1 + c) / 2, -(1 + c), (1 + c) / 2], "bp": [al, 0, -al]}[kind]
        a = [1 + al, -2 * c, 1 - al]
        out[s:s + block], zi = lfilter(np.array(b) / a[0], np.array(a) / a[0], x[s:s + block], zi=zi)
    return out


def lpf24_tv(x: np.ndarray, fc, q: float = 2.2, block: int = 128) -> np.ndarray:
    """24 dB/oct (4-pole) resonant Low-Pass Filter with overall resonance Q."""
    stage1 = biquad_tv(x, fc, 0.707, "lp", block=block)
    return biquad_tv(stage1, fc, q, "lp", block=block)


def _tri(ph: np.ndarray) -> np.ndarray:
    """Band-limited triangle wave."""
    return np.sin(ph) - (1 / 9) * np.sin(3 * ph) + (1 / 25) * np.sin(5 * ph)


def _tri_saw(ph: np.ndarray, saw_mix: float = 0.25) -> np.ndarray:
    """Band-limited triangle + warm sawtooth blend (odd + even harmonics for woody marimba warmth)."""
    tri = _tri(ph)
    saw = np.sin(ph) + 0.5 * np.sin(2 * ph) + (1 / 3) * np.sin(3 * ph) + 0.25 * np.sin(4 * ph)
    return (1 - saw_mix) * tri + saw_mix * saw


def sub_thump(dur: float = 0.42, f0: float = 92.0, f1: float = 36.0, tau: float = 0.065):
    """Sine sub-drop (92 Hz -> 36 Hz over 190 ms) through a soft-clipper (tanh)."""
    t = _t(dur)
    u = np.clip(t / 0.19, 0.0, 1.0)
    f_inst = f1 + (f0 - f1) * ((1.0 - u) ** 1.8)
    ph = TAU * np.cumsum(f_inst) / SR
    env = (1.0 - np.exp(-t / 0.0025)) * np.exp(-t / 0.135) * np.clip((dur - t) / 0.04, 0.0, 1.0)
    return norm(np.tanh(1.35 * np.sin(ph) * env)), 0


def impact(s: float, rng: np.random.Generator):
    """Sum sine sub-drop (92->36 Hz over 190 ms) + triangle mid-punch (165->62 Hz over 55 ms) + 5 ms HP click (>2.2 kHz) through tanh."""
    dur = 0.34 + 0.18 * s
    t = _t(dur)
    # 1. Sine sub-drop: 92 Hz -> 36 Hz over 190 ms
    u_sub = np.clip(t / 0.19, 0.0, 1.0)
    f_sub = 36.0 + (92.0 - 36.0) * ((1.0 - u_sub) ** 1.8)
    sub = np.sin(TAU * np.cumsum(f_sub) / SR) * (1.0 - np.exp(-t / 0.002)) * np.exp(-t / (0.11 + 0.04 * s))
    # 2. Triangle mid-punch: 165 Hz -> 62 Hz over 55 ms
    u_mid = np.clip(t / 0.055, 0.0, 1.0)
    f_mid = 62.0 + (165.0 - 62.0) * ((1.0 - u_mid) ** 1.6)
    mid_punch = _tri(TAU * np.cumsum(f_mid) / SR) * (1.0 - np.exp(-t / 0.0015)) * np.exp(-t / 0.038) * 0.72
    # 3. 5 ms high-passed click (> 2.2 kHz)
    hp_noise = biquad_tv(rng.standard_normal(len(t)), 2200.0, 0.85, "hp")
    click = hp_noise * np.exp(-t / 0.0024) * (0.34 + 0.18 * s)
    # Soft-clipper (tanh)
    y = np.tanh(1.65 * (sub * 1.15 + mid_punch + click))
    return taper(norm(y), 4.0), 0


def whoosh(pre: float, post: float, s: float, rng: np.random.Generator):
    """Pink noise -> 24dB/oct resonant LPF (Q=2.2) peaking at event.time then sweeping exponentially 2.6 kHz -> 120 Hz, + sub weight."""
    tail_len = max(post, 0.38)
    t = _t(pre + tail_len)
    u_pre = np.clip(t / max(pre, 1e-4), 0.0, 1.0)
    u_post = np.clip((t - pre) / max(post, 1e-4), 0.0, 1.0)
    # Asymmetric exponential filter sweep peaking at 2.6 kHz at t=pre, then sweeping exponentially 2.6 kHz -> 120 Hz over post
    fc_pre = 180.0 * ((2600.0 / 180.0) ** (u_pre ** 2.2))
    fc_post = 2600.0 * ((120.0 / 2600.0) ** (u_post ** 0.85))
    fc = np.where(t <= pre, fc_pre, fc_post)
    env_pre = u_pre ** 3.4
    env_post = np.exp(-(t - pre) / max(0.065, post * 0.45)) + 0.78 * np.exp(-(t - pre) / 0.58)
    env = np.where(t <= pre, env_pre, env_post)
    air_lp = lpf24_tv(pink_noise(len(t), rng), fc, q=2.2) * env * 0.88
    tail_air = biquad_tv(pink_noise(len(t), rng), 2600.0, 0.9, "bp") * np.where(t > pre, np.exp(-(t - pre) / 0.58), u_pre ** 3.8) * (1.05 + 0.25 * s)
    # Sub-bass weight layer (92 Hz -> 36 Hz over 190 ms) peaking at the cut frame
    u_w = np.clip((t - (pre - 0.05)) / 0.19, 0.0, 1.0)
    f_sub = 36.0 + (92.0 - 36.0) * ((1.0 - u_w) ** 1.5)
    w_env = np.where(t <= pre, u_pre ** 3.8, np.exp(-(t - pre) / 0.095))
    weight = np.sin(TAU * np.cumsum(f_sub) / SR) * w_env * (1.20 + 0.35 * s)
    return taper(norm(air_lp + tail_air + weight), 4.0), int(round(pre * SR))


def riser(dur: float, rng: np.random.Generator):
    """Anticipation riser building over `dur` (e.g. 12.85s -> 13.40s) and hard-cutting at `dur` into the cut impact; anchor = 0."""
    t = _t(dur)
    u = np.clip(t / max(dur, 1e-4), 0.0, 1.0)
    f_sw = 220.0 * (2 ** ((3.5 * (u ** 1.6)) / 12))
    tone = biquad_tv(_tri_saw(TAU * np.cumsum(f_sw) / SR, 0.35), 240.0 + 1800.0 * (u ** 1.8), 1.2, "lp") * 0.45
    fc = 160.0 * ((3200.0 / 160.0) ** (u ** 1.7))
    swell = lpf24_tv(pink_noise(len(t), rng), fc, q=2.2) * 0.75
    env = (u ** 2.4) * (1.0 - np.exp(-t / 0.005))
    return taper(norm((tone + swell) * env), 2.0), 0


def suction(dur: float, rng: np.random.Generator):
    """Reverse-suction anticipation sweep: pink noise -> 24dB/oct resonant LPF (Q=2.2) sweeping exponentially 140 Hz -> 3.4 kHz, hard-gated at end."""
    t = _t(dur)
    u = np.clip(t / max(dur, 1e-4), 0.0, 1.0)
    fc = 140.0 * ((3400.0 / 140.0) ** (u ** 1.65))
    env = (u ** 2.6) * (1.0 - np.exp(-t / 0.003))
    y = lpf24_tv(pink_noise(len(t), rng), fc, q=2.2) * env
    sub = np.sin(TAU * np.cumsum(46.0 + 44.0 * (u ** 1.5)) / SR) * (u ** 2.4) * 0.35
    # Hard gate at end of suction (1.5 ms de-click only) so it cuts to silence right when crystal hits
    return taper(norm(y + sub), 1.5), 0


def pluck(freq: float, dur: float, rng: np.random.Generator, bell: bool = False, bright: float = 1.0):
    """Stationary damped woody/marimba body (180-420 Hz, ZERO pitch drop) + 6 ms woody click for hero scene arrivals."""
    t = _t(min(max(dur, 0.14), 0.22))
    f0 = float(np.clip(freq if freq <= 440 else freq * 0.5, 180.0, 420.0))
    # Zero pitch envelope (no downward water-drop sweep)
    raw = _tri_saw(TAU * f0 * t, saw_mix=0.28 if not bell else 0.16)
    fc = 280.0 + 1450.0 * np.exp(-t / 0.038)
    body = biquad_tv(raw, fc, 0.85, "lp") * np.exp(-t / 0.055)
    click = biquad_tv(rng.standard_normal(len(t)), 1600.0, 1.15, "bp") * np.exp(-t / 0.0025) * 0.52 * bright
    air = biquad_tv(rng.standard_normal(len(t)), 9600.0, 0.7, "hp") * np.exp(-t / 0.0025) * 0.14
    return taper(norm((body + click + air) * (1.0 - np.exp(-t / 0.001))), 3.0), 0


def text_tick(freq: float, rng: np.random.Generator):
    """Ultra-short (18-30 ms) non-pitched tactile micro-click: 1.4-2.8 kHz bandpass noise + stationary damped body, zero pitch drop."""
    t = _t(0.030)
    # Map glyph frequency hint into [1400 Hz, 2800 Hz] bandpass/resonator center with ZERO pitch envelope over time
    fc = float(np.clip(1400.0 + (freq - 420.0) * 2.4, 1400.0, 2800.0))
    # 3 ms attack, 15 ms exponential decay
    att = np.clip(t / 0.003, 0.0, 1.0)
    dec = np.exp(-np.maximum(0.0, t - 0.003) / 0.011)
    env = att * dec
    bp_noise = biquad_tv(rng.standard_normal(len(t)), fc, 2.4, "bp") * env * 0.42
    hp_imp = biquad_tv(rng.standard_normal(len(t)), 2400.0, 0.8, "hp") * np.exp(-t / 0.0022) * 0.25
    # Damped stationary resonator at `fc` (zero pitch sweep over time)
    body = np.sin(TAU * fc * t) * env * 1.45
    air = biquad_tv(rng.standard_normal(len(t)), 9800.0, 0.7, "hp") * np.exp(-t / 0.002) * 0.22
    return taper(norm(bp_noise + hp_imp + body + air), 2.0), 0


tick = text_tick


def crystal(rng: np.random.Generator):
    """Two detuned high-frequency sine/triangle partials (2093 Hz + 3136 Hz, +7 cents detune) with 120 ms glassy decay."""
    t = _t(0.12)
    det = 2.0 ** (7.0 / 1200.0)  # +7 cents detune
    f1a, f1b = 2093.0, 2093.0 * det
    f2a, f2b = 3136.0, 3136.0 * det
    p1 = 0.65 * (np.sin(TAU * f1a * t) + np.sin(TAU * f1b * t)) + 0.35 * (_tri(TAU * f1a * t) + _tri(TAU * f1b * t))
    p2 = 0.65 * (np.sin(TAU * f2a * t) + np.sin(TAU * f2b * t)) + 0.35 * (_tri(TAU * f2a * t) + _tri(TAU * f2b * t))
    env = (1.0 - np.exp(-t / 0.001)) * np.exp(-t / 0.032)  # 120 ms glassy decay window
    shimmer = biquad_tv(rng.standard_normal(len(t)), 9600.0, 0.75, "hp") * np.exp(-t / 0.010) * 0.22
    return taper(norm((0.58 * p1 + 0.42 * p2) * env + shimmer), 4.0), 0


def pad(freqs, dur: float, rng: np.random.Generator):
    """Warm low-passed harmonic pad bed (< 900 Hz): keeps the soundscape cohesive without high-mid clutter."""
    t = _t(dur)
    y = np.zeros(len(t))
    for i, f in enumerate(freqs):
        for d in (-0.45, 0.45):
            ph = TAU * (f + d * (1 + i * 0.25)) * t + rng.uniform(0, TAU)
            y += (np.sin(ph) + 0.25 * np.sin(2 * ph)) / (1 + 0.55 * i)
    y = biquad_tv(y, 620.0 + 180.0 * np.sin(TAU * 0.14 * t), 0.75, "lp")
    y *= 0.78 + 0.22 * np.sin(TAU * 0.17 * t + rng.uniform(0, TAU))
    return norm(y), 0


def place(buf: np.ndarray, sig: np.ndarray, start: int, gain: float, pan: float, stereo_shimmer: bool = False) -> None:
    """Add a mono signal into a stereo buffer with constant-power pan in [-1, 1] and optional stereo shimmer."""
    th = (float(np.clip(pan, -1, 1)) + 1) * np.pi / 4
    a, b = max(0, -start), max(0, start)
    seg = sig[a:a + max(0, len(buf) - b)]
    if len(seg) == 0:
        return
    buf[b:b + len(seg), 0] += seg * gain * np.cos(th) * np.sqrt(2)
    buf[b:b + len(seg), 1] += seg * gain * np.sin(th) * np.sqrt(2)
    if stereo_shimmer and len(seg) > 36:
        # 0.75 ms Haas/quadrature stereo shimmer offset across L/R
        d = 36
        buf[b + d:b + len(seg), 0] += seg[:-d] * gain * 0.28
        buf[b + d:b + len(seg), 1] -= seg[:-d] * gain * 0.28
