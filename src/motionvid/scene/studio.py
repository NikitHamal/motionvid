"""Studio voices (engine rev 6). Every voice returns (mono float64, anchor sample) like `voices.py`.

Fixes from the v0.4 Launch audit:
- `whoosh6`: centred asymmetric envelope, 160 ms exponential ramp-in -> peak at the cut -> 220 ms exponential decay.
  Pink noise through a 24 dB/oct LPF (Q = 1.6) sweeping 150 Hz -> 1.35 kHz -> 110 Hz. Nothing above 2.2 kHz.
- `text_tick6`: 14 ms total = 3 ms high-passed transient (> 2.4 kHz) + 11 ms damped woody impulse (1.15 kHz), zero pitch drop.
- `hero_pluck6`: tonal marimba/kalimba pluck, fixed pitch, 5 ms wooden mallet transient.
- `riser6`: rising LPF noise sweep 200 Hz -> 2.4 kHz + octave glide 110 Hz -> 220 Hz.
- `settle`: bounce impact low-pass that opens slightly on smaller bounces.
"""

from __future__ import annotations

import numpy as np

from .voices import SR, TAU, _t, _tri_saw, biquad_tv, lpf24_tv, norm, pink_noise, taper


def whoosh6(pre: float, post: float, s: float, rng: np.random.Generator):
    t = _t(pre + post + 0.02)
    u_in = np.clip(t / pre, 0.0, 1.0)
    u_out = np.clip((t - pre) / post, 0.0, 1.0)
    fc = np.where(t <= pre, 150.0 * (1350.0 / 150.0) ** u_in, 1350.0 * (110.0 / 1350.0) ** u_out)
    k = 5.0
    env_in = (np.exp(k * u_in) - 1.0) / (np.exp(k) - 1.0)
    env_out = np.exp(-(t - pre) / (post / 4.6))  # -40 dB at +post
    env = np.where(t <= pre, env_in, env_out)
    y = lpf24_tv(pink_noise(len(t), rng), fc, q=1.6)
    y = biquad_tv(biquad_tv(y, 2200.0, 0.707, "lp"), 2200.0, 0.707, "lp")  # guard: 24 dB/oct above 2.2 kHz
    return taper(norm(y * env), 3.0), int(round(pre * SR))


def text_tick6(st: float, rng: np.random.Generator):
    t = _t(0.014)
    n = len(t)
    a = int(0.003 * SR)
    hp = biquad_tv(rng.standard_normal(n), 2400.0, 0.9, "hp") * np.exp(-t / 0.0009)
    hp[a:] = 0.0
    fb = 1100.0 * 2.0 ** (st / 12.0)  # stationary inside a tick; climbs 0.5 semitone per glyph (max +7) for phrasing
    tb = np.maximum(t - 0.003, 0.0)
    body = (np.sin(TAU * fb * tb) + 0.12 * biquad_tv(rng.standard_normal(n), fb, 3.0, "bp")) * np.exp(-tb / 0.0032)
    body[:a] = 0.0
    body[a:a + 24] *= np.linspace(0.0, 1.0, 24)
    return taper(norm(0.3 * hp + body), 2.0), 0


def hero_pluck6(freq: float, rng: np.random.Generator):
    t = _t(0.32)
    f0 = float(np.clip(freq * 2.0, 360.0, 840.0))
    body = sum(a * np.sin(TAU * f0 * r * t + 0.4 * i) * np.exp(-t / d)
               for i, (r, a, d) in enumerate([(1.0, 1.0, 0.06), (4.0, 0.34, 0.03), (9.2, 0.10, 0.012)]))
    mallet = biquad_tv(rng.standard_normal(len(t)), 1900.0, 1.2, "bp") * np.exp(-t / 0.0013)
    mallet[int(0.005 * SR):] *= np.exp(-np.arange(len(t) - int(0.005 * SR)) / (0.0015 * SR))
    thock = np.sin(TAU * 310.0 * t) * np.exp(-t / 0.006)
    return taper(norm((body + 0.7 * mallet + 0.35 * thock) * (1.0 - np.exp(-t / 0.0006))), 4.0), 0


def riser6(dur: float, rng: np.random.Generator):
    t = _t(dur)
    u = np.clip(t / max(dur, 1e-4), 0.0, 1.0)
    fc = 200.0 * (2400.0 / 200.0) ** (u ** 1.5)
    swell = lpf24_tv(pink_noise(len(t), rng), fc, q=1.6)
    f_g = 110.0 * 2.0 ** (u ** 1.4)  # one-octave glide 110 -> 220 Hz
    tone = biquad_tv(_tri_saw(TAU * np.cumsum(f_g) / SR, 0.3), 380.0 + 1700.0 * u ** 1.6, 1.0, "lp") * 0.9
    env = (u ** 2.1) * (1.0 - np.exp(-t / 0.005))
    return taper(norm((0.8 * swell / max(1e-9, np.abs(swell).max()) + 0.55 * tone / max(1e-9, np.abs(tone).max())) * env), 2.0), 0


def air6(rng: np.random.Generator):
    """Room-air tail after a cut (2.4-6 kHz, 0.16 s decay) so the hit lands inside a space; never part of the whoosh."""
    t = _t(0.7)
    y = biquad_tv(biquad_tv(rng.standard_normal(len(t)), 3600.0, 0.8, "bp"), 2600.0, 0.7, "hp")
    return taper(norm(y * (1.0 - np.exp(-t / 0.02)) * np.exp(-t / 0.16)), 8.0), 0


def settle(x: np.ndarray, idx: int) -> np.ndarray:
    """Bounce `idx` (0 = first): the low-pass opens 900 Hz -> ~1.75 kHz so smaller bounces sound lighter."""
    fc = 900.0 * 1.25 ** idx
    return norm(biquad_tv(biquad_tv(x, fc, 0.707, "lp"), fc, 0.707, "lp"), float(np.abs(x).max()))


STUDIO_ROLES = {"tick": "text_tick", "pluck": "hero_pluck"}
