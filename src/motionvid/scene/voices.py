"""Hand-written agency-grade DSP voices for the scene engine. Every voice returns (mono float64, anchor sample).

Enforces the 5 Agency DSP constraints:
1. Filtered triangle/saw damped bodies (120 ms, 180-420 Hz, LP 1.8 kHz -> 300 Hz in 90 ms) + 6 ms woody click (800-2200 Hz).
2. Whooshes lock a pink-noise low-Q (Q=1.2) LP air layer (250 -> 1600 -> 200 Hz) with a 90 -> 42 Hz sub weight layer.
3. Pitch sweeps constrained to realistic physics (<= +4 st over 35-60 ms for pops; -5 to -12 st over 180-300 ms for impacts).
"""

from __future__ import annotations

import numpy as np
from scipy.signal import lfilter

SR = 48000
TAU = 2 * np.pi
PINK_B = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
PINK_A = [1.0, -2.494956002, 2.017265875, -0.522189400]


def _t(dur: float) -> np.ndarray:
    return np.arange(max(1, int(dur * SR))) / SR


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


def _tri_saw(ph: np.ndarray, saw_mix: float = 0.25) -> np.ndarray:
    """Band-limited triangle + warm sawtooth blend (odd + even harmonics for woody marimba warmth)."""
    tri = np.sin(ph) - (1 / 9) * np.sin(3 * ph) + (1 / 25) * np.sin(5 * ph)
    saw = np.sin(ph) + 0.5 * np.sin(2 * ph) + (1 / 3) * np.sin(3 * ph) + 0.25 * np.sin(4 * ph)
    return (1 - saw_mix) * tri + saw_mix * saw


def sub_thump(dur: float = 0.5, f0: float = 88.0, f1: float = 44.0, tau: float = 0.14):
    """Pitch-dropping sine (f0 -> f1, <= 12 semitones over ~220 ms): physical mass of a growing shape."""
    t = _t(dur)
    f0_c = min(f0, f1 * 2.0)  # constrain sweep to <= 12 semitones
    ph = TAU * np.cumsum(f1 + (f0_c - f1) * np.exp(-t / tau)) / SR
    env = (1 - np.exp(-t / 0.004)) * np.exp(-t / (dur * 0.34)) * np.clip((dur - t) / 0.05, 0, 1)
    return np.sin(ph) * env, 0


def impact(s: float, rng: np.random.Generator):
    """Layered physical impact: 90->42 Hz sub drop over 220 ms + damped low-mid wooden body + woody transient."""
    sub, _ = sub_thump(0.48 + 0.45 * s, 90 - 8 * (1 - s), 42 + 12 * (1 - s), tau=0.13)
    t = _t(0.32)
    f_body = 140 * (1 + (2 ** (3.0 / 12) - 1) * np.exp(-t / 0.045))
    body = biquad_tv(_tri_saw(TAU * np.cumsum(f_body) / SR, 0.3), 300 + 1400 * np.exp(-t / 0.06), 0.9, "lp") * np.exp(-t / 0.075) * 0.55
    wood = biquad_tv(pink_noise(len(t), rng), 1350, 1.1, "bp") * np.exp(-t / 0.005) * (0.4 + 0.35 * s)
    air = biquad_tv(rng.standard_normal(len(t)), 9500, 0.7, "hp") * np.exp(-t / 0.015) * (0.14 + 0.15 * s)
    y = np.zeros(len(sub))
    y[:len(body)] += body + wood + air
    return norm(y + sub * 1.15), 0


def whoosh(pre: float, post: float, s: float, rng: np.random.Generator):
    """Locked dual-layer transition whoosh: pink noise LP (250->1600->200 Hz, Q=1.2) + sub drop (90->42 Hz over 220 ms)."""
    t = _t(pre + post)
    u = np.where(t < pre, t / max(pre, 1e-4), 1.0)
    post_u = np.clip((t - pre) / max(post, 1e-4), 0, 1)
    fc = np.where(t < pre, 250 * (1600 / 250) ** (u ** 1.35), 200 + 1400 * np.exp(-post_u * 2.6))
    env = np.where(t < pre, u ** 3.2, np.exp(-(t - pre) / (post * 0.36)))
    air_lp = biquad_tv(pink_noise(len(t), rng), fc, 1.2, "lp") * env
    shimmer_air = biquad_tv(rng.standard_normal(len(t)), 3400, 0.8, "bp") * (env ** 1.4) * (0.22 + 0.16 * s)
    # Weight layer: sine sweeping 90 Hz -> 42 Hz over 220 ms peaking right on the cut frame
    tau_w = np.clip((t - (pre - 0.04)) / 0.22, 0, 1)
    f_sub = 90.0 - (90.0 - 42.0) * tau_w
    w_env = np.where(t < pre, u ** 4.2, np.exp(-(t - pre) / 0.14))
    weight = np.sin(TAU * np.cumsum(f_sub) / SR) * w_env * (0.85 + 0.35 * s)
    return taper(norm(air_lp + shimmer_air + weight)), int(pre * SR)


def riser(dur: float, rng: np.random.Generator):
    """Warm harmonic pad swell (<= +4 semitones) + pink-noise LP filter sweep (250 -> 1550 Hz, Q=1.2)."""
    t = _t(dur + 0.15)
    u = np.clip(t / dur, 0, 1)
    f_sw = 220.0 * (2 ** ((3.5 * (u ** 1.4)) / 12))  # +3.5 semitones max (no slide whistle)
    tone = biquad_tv(_tri_saw(TAU * np.cumsum(f_sw) / SR, 0.35), 280 + 1300 * (u ** 1.6), 1.1, "lp") * 0.45
    swell = biquad_tv(pink_noise(len(t), rng), 250 + 1350 * (u ** 1.7), 1.2, "lp") * 0.7
    env = (u ** 2.1) * np.where(t > dur, np.exp(-(t - dur) / 0.045), 1.0)
    return taper(norm((tone + swell) * env)), int(dur * SR)


def suction(dur: float, rng: np.random.Generator):
    """Tight reverse-suction sweep closing into the collapse frame; hit = last sample."""
    t = _t(dur)
    u = t / dur
    y = biquad_tv(pink_noise(len(t), rng), 1800 * (260 / 1800) ** u, 1.2, "lp") * (u ** 2.3)
    sub = np.sin(TAU * np.cumsum(48 + 38 * (u ** 1.5)) / SR) * (u ** 2.5) * 0.55
    return taper(norm(y + sub), 3), len(t) - 1


def pluck(freq: float, dur: float, rng: np.random.Generator, bell: bool = False, bright: float = 1.0):
    """120 ms damped woody/marimba body (180-420 Hz triangle/saw, LP 1.8 kHz->300 Hz over 90 ms) + 6 ms woody click."""
    t = _t(min(max(dur, 0.16), 0.24))
    f0 = float(np.clip(freq if freq <= 440 else freq * 0.5, 180.0, 420.0))
    # Subtle +2.8 semitone pitch envelope over 42 ms (Rule 4: +2 to +4 st over 35-60 ms)
    f_env = f0 * (2 ** ((2.8 * np.exp(-t / 0.022)) / 12))
    raw = _tri_saw(TAU * np.cumsum(f_env) / SR, saw_mix=0.32 if not bell else 0.18)
    fc = 300.0 + 1500.0 * np.exp(-t / 0.042)  # closes 1.8 kHz -> 300 Hz over ~90 ms
    body = biquad_tv(raw, fc, 0.85, "lp") * np.exp(-t / 0.065)
    # 6 ms woody click transient (800 Hz - 2.2 kHz bandpass impulse)
    click = biquad_tv(rng.standard_normal(len(t)), 1380.0, 1.05, "bp") * np.exp(-t / 0.0028) * 0.55 * bright
    air = biquad_tv(rng.standard_normal(len(t)), 9600.0, 0.7, "hp") * np.exp(-t / 0.003) * 0.12
    return taper(norm((body + click + air) * (1 - np.exp(-t / 0.0012)))), 0


def tick(freq: float, rng: np.random.Generator):
    """Short damped organic felt/wood key-tick: low-mid marimba resonance + 6 ms woody transient + soft 9.5 kHz air."""
    t = _t(0.065)
    f0 = float(np.clip(freq, 410.0, 820.0))
    f_env = f0 * (2 ** ((2.2 * np.exp(-t / 0.018)) / 12))
    body = biquad_tv(_tri_saw(TAU * np.cumsum(f_env) / SR, 0.2), 340 + 1350 * np.exp(-t / 0.025), 0.85, "lp") * np.exp(-t / 0.014)
    wood = biquad_tv(rng.standard_normal(len(t)), 1450.0, 1.2, "bp") * np.exp(-t / 0.0025) * 0.42
    air = biquad_tv(rng.standard_normal(len(t)), 9500.0, 0.7, "hp") * np.exp(-t / 0.0018) * 0.25
    return taper(norm((body + wood + air) * (1 - np.exp(-t / 0.0005)))), 0


def crystal(rng: np.random.Generator):
    """Crisp 4 kHz micro-click + tight damped wooden pop (+2.5 st over 40 ms), zero ringing bells or laser chirps."""
    t = _t(0.14)
    f_env = 340.0 * (2 ** ((2.6 * np.exp(-t / 0.02)) / 12))
    pop = biquad_tv(_tri_saw(TAU * np.cumsum(f_env) / SR, 0.25), 320 + 1400 * np.exp(-t / 0.035), 0.9, "lp") * np.exp(-t / 0.038)
    micro_click = biquad_tv(rng.standard_normal(len(t)), 4000.0, 1.8, "bp") * np.exp(-t / 0.0028) * 0.75
    air = biquad_tv(rng.standard_normal(len(t)), 9800.0, 0.7, "hp") * np.exp(-t / 0.006) * 0.28
    return taper(norm((pop + micro_click + air) * (1 - np.exp(-t / 0.0004)))), 0


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


def place(buf: np.ndarray, sig: np.ndarray, start: int, gain: float, pan: float) -> None:
    """Add a mono signal into a stereo buffer with constant-power pan in [-1, 1]."""
    th = (float(np.clip(pan, -1, 1)) + 1) * np.pi / 4
    a, b = max(0, -start), max(0, start)
    seg = sig[a:a + max(0, len(buf) - b)]
    if len(seg) == 0:
        return
    buf[b:b + len(seg), 0] += seg * gain * np.cos(th) * np.sqrt(2)
    buf[b:b + len(seg), 1] += seg * gain * np.sin(th) * np.sqrt(2)
