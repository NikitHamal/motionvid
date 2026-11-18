"""Hand-written DSP voices for the scene engine. Every voice returns (mono float64, anchor sample).

The anchor is the sample where the HIT is heard (peak of a riser, cut frame of a whoosh), so the
scheduler can land it exactly on the motion event. No samples, no weights.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import lfilter

SR = 48000
TAU = 2 * np.pi


def _t(dur: float) -> np.ndarray:
    return np.arange(max(1, int(dur * SR))) / SR


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


def sub_thump(dur: float = 0.6, f0: float = 95.0, f1: float = 42.0, tau: float = 0.12):
    """Pitch-dropping sine (f0 -> f1): mass of a growing shape."""
    t = _t(dur)
    ph = TAU * np.cumsum(f1 + (f0 - f1) * np.exp(-t / tau)) / SR
    env = (1 - np.exp(-t / 0.003)) * np.exp(-t / (dur * 0.3)) * np.clip((dur - t) / 0.05, 0, 1)
    return np.sin(ph) * env, 0


def impact(s: float, rng: np.random.Generator):
    """Layered hit: sub drop + body + high crack. `s` in [0,1] is shape mass."""
    sub, _ = sub_thump(0.5 + 0.6 * s, 95 - 15 * (1 - s), 42 + 26 * (1 - s))
    t = _t(0.45)
    body = np.sin(TAU * np.cumsum(75 + 135 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.09) * 0.55
    crack = biquad_tv(rng.standard_normal(len(t)), 2500, 0.7, "hp") * np.exp(-t / 0.022) * (0.25 + 0.4 * s)
    y = np.zeros(len(sub))
    y[:len(body)] += body + crack
    return norm(y + sub * 1.1), 0


def whoosh(pre: float, post: float, s: float, rng: np.random.Generator):
    """Transition sweep that RAMPS UP for `pre` seconds and peaks on the cut frame (anchor), then rings out."""
    t = _t(pre + post)
    u = np.where(t < pre, t / pre, 1.0)
    fc = np.where(t < pre, 250 * (6500 / 250) ** (u ** 1.5), 6500 * np.exp(-(t - pre) / (post * 0.45)) + 900)
    env = np.where(t < pre, u ** 2.4, np.exp(-(t - pre) / (post * 0.32)))
    y = biquad_tv(rng.standard_normal(len(t)), fc, 0.7, "bp") * env
    y += biquad_tv(rng.standard_normal(len(t)), 6500, 0.7, "hp") * env ** 1.5 * (0.25 + 0.2 * s)
    return taper(norm(y)), int(pre * SR)


def riser(dur: float, rng: np.random.Generator):
    t = _t(dur + 0.15)
    u = np.clip(t / dur, 0, 1)
    tone = np.sin(TAU * np.cumsum(180 * (1200 / 180) ** (u ** 2)) / SR) * 0.5
    hiss = biquad_tv(rng.standard_normal(len(t)), 300 + 5000 * u ** 2, 1.0, "bp")
    env = u ** 2.2 * np.where(t > dur, np.exp(-(t - dur) / 0.04), 1.0)
    return taper(norm((tone + hiss) * env)), int(dur * SR)


def suction(dur: float, rng: np.random.Generator):
    """Reverse suction: band sweeps down into the point of collapse; hit = last sample."""
    t = _t(dur)
    u = t / dur
    y = biquad_tv(rng.standard_normal(len(t)), 5500 * (500 / 5500) ** u, 1.4, "bp") * u ** 2.2
    return taper(norm(y), 3), len(t) - 1


def _partials(f: float, t: np.ndarray, ratios, taus, amps) -> np.ndarray:
    y = np.zeros(len(t))
    for r, tau, a in zip(ratios, taus, amps):
        if f * r < SR * 0.45:
            y += a * np.sin(TAU * f * r * t) * np.exp(-t / tau)
    return y


def pluck(freq: float, dur: float, rng: np.random.Generator, bell: bool = False, bright: float = 1.0):
    t = _t(dur)
    k = dur / 0.35
    ratios = (1, 2.76, 5.4, 8.93) if bell else (1, 2.0, 3.0, 4.2)
    y = _partials(freq, t, ratios, (0.2 * k, 0.1 * k, 0.05 * k, 0.025 * k), (1, 0.5, 0.25 * bright, 0.12 * bright))
    snap = biquad_tv(rng.standard_normal(len(t)), 5000, 0.7, "hp") * np.exp(-t / 0.003) * 0.35 * bright
    return taper(norm((y + snap) * (1 - np.exp(-t / 0.0015)))), 0


def tick(freq: float, rng: np.random.Generator):
    """Glyph tick: pitched body + inharmonic click + 9 kHz+ air transient."""
    t = _t(0.07)
    y = np.sin(TAU * freq * t) * np.exp(-t / 0.012) + 0.45 * np.sin(TAU * freq * 2.76 * t) * np.exp(-t / 0.006)
    y += biquad_tv(rng.standard_normal(len(t)), 9000, 0.7, "hp") * np.exp(-t / 0.0015) * 0.6
    return taper(norm(y * (1 - np.exp(-t / 0.0005)))), 0


def crystal(rng: np.random.Generator):
    """3-6 kHz crystalline pop with an upward chirp and air."""
    t = _t(0.3)
    y = _partials(3100.0, t, (1, 1.39, 1.68, 1.97), (0.06, 0.05, 0.04, 0.03), (1, 0.7, 0.6, 0.5))
    y += 0.5 * np.sin(TAU * np.cumsum(2400 + 3000 * np.minimum(t / 0.04, 1)) / SR) * np.exp(-t / 0.02)
    y += biquad_tv(rng.standard_normal(len(t)), 9500, 0.7, "hp") * np.exp(-t / 0.012) * 0.5
    return taper(norm(y * (1 - np.exp(-t / 0.0004)))), 0


def pad(freqs, dur: float, rng: np.random.Generator):
    """Quiet scene bed: detuned sines under a slow swell; keeps the soundscape continuous across edits."""
    t = _t(dur)
    y = np.zeros(len(t))
    for i, f in enumerate(freqs):
        for d in (-0.6, 0.6):
            y += np.sin(TAU * (f + d * (1 + i * 0.3)) * t + rng.uniform(0, TAU)) / (1 + 0.4 * i)
    y *= 0.75 + 0.25 * np.sin(TAU * 0.17 * t + rng.uniform(0, TAU))
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
