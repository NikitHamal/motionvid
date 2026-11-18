"""UI foley (engine rev 7): voices for interface motion. A timeline opts in with `"rev": 7`; rev 6 output is untouched.

Roles (sfx hints): click, pop, chime, toggle, notify, swipe. All fixed-pitch inside a hit, no laser chirps (pitch moves <= 2.5 semitones).
"""

from __future__ import annotations

import numpy as np

from .voices import SR, TAU, _t, biquad_tv, norm, pink_noise, taper

UI_ROLES = ("click", "pop", "chime", "toggle", "notify", "swipe")


def _hit(f: float, dur: float, decay: float, rng: np.random.Generator, bright: float = 1.0):
    t = _t(dur)
    body = sum(a * np.sin(TAU * f * r * t + 0.3 * i) * np.exp(-t / (decay * d))
               for i, (r, a, d) in enumerate([(1.0, 1.0, 1.0), (4.0, 0.3 * bright, 0.5), (9.2, 0.08 * bright, 0.2)]))
    mallet = biquad_tv(rng.standard_normal(len(t)), 2000.0, 1.2, "bp") * np.exp(-t / 0.0012)
    return (body + 0.5 * mallet) * (1.0 - np.exp(-t / 0.0007))


def click7(st: float, rng: np.random.Generator):
    t = _t(0.03)
    hp = biquad_tv(rng.standard_normal(len(t)), 2200.0, 0.9, "hp") * np.exp(-t / 0.0007)
    body = np.sin(TAU * 520.0 * 2.0 ** (st / 12.0) * t) * np.exp(-t / 0.006)
    thock = np.sin(TAU * 170.0 * t) * np.exp(-t / 0.009)
    return taper(norm(0.28 * hp + body + 0.6 * thock), 2.0), 0


def pop7(rng: np.random.Generator):
    t = _t(0.12)
    f = 330.0 * 2.0 ** (2.5 / 12.0 * np.minimum(1.0, t / 0.035))
    y = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.032) * (1.0 - np.exp(-t / 0.0018))
    return taper(norm(y + 0.08 * biquad_tv(rng.standard_normal(len(t)), 3000.0, 1.5, "bp") * np.exp(-t / 0.002)), 3.0), 0


def chime7(freq: float, rng: np.random.Generator):
    f0 = float(np.clip(freq, 392.0, 988.0))
    n = int(0.62 * SR)
    out = np.zeros(n)
    for i, (r, dly, g) in enumerate([(1.0, 0.0, 1.0), (1.5, 0.075, 0.8), (2.0, 0.15, 0.7)]):
        h = _hit(f0 * r, 0.45, 0.07, rng, 0.8) * g
        a = int(dly * SR)
        out[a:a + len(h)] += h[: n - a]
    return taper(norm(out), 5.0), 0


def toggle7(rng: np.random.Generator):
    a, b = click7(-3.0, rng)[0], click7(+4.0, rng)[0]
    out = np.zeros(int(0.14 * SR))
    out[:len(a)] += 0.7 * a
    k = int(0.06 * SR)
    out[k:k + len(b)] += b
    return taper(norm(out), 2.0), int(0.06 * SR)


def notify7(freq: float, rng: np.random.Generator):
    f0 = float(np.clip(freq, 440.0, 880.0))
    out = np.zeros(int(0.7 * SR))
    for dly, r in [(0.0, 1.0), (0.12, 4 / 3)]:
        h = _hit(f0 * r, 0.5, 0.09, rng, 0.5)
        a = int(dly * SR)
        out[a:a + len(h)] += h
    return taper(norm(out), 5.0), 0


def swipe7(s: float, rng: np.random.Generator):
    dur = 0.24
    t = _t(dur)
    u = t / dur
    fc = 380.0 * (1700.0 / 380.0) ** np.sin(np.pi * np.clip(u, 0, 1) ** 0.8)
    y = biquad_tv(biquad_tv(pink_noise(len(t), rng), fc, 1.4, "bp"), 2200.0, 0.707, "lp")
    env = np.where(u < 0.4, (u / 0.4) ** 2.0, np.exp(-(u - 0.4) / 0.2)) * (1.0 - np.exp(-t / 0.004))
    return taper(norm(y * env), 3.0), int(0.4 * dur * SR)


def voice(role: str, p: dict, rng: np.random.Generator):
    if role == "click":
        return click7(float(p.get("st", 0.0)), rng)
    if role == "pop":
        return pop7(rng)
    if role == "chime":
        return chime7(float(p.get("freq", 523.25)), rng)
    if role == "toggle":
        return toggle7(rng)
    if role == "notify":
        return notify7(float(p.get("freq", 587.33)), rng)
    return swipe7(float(p.get("s", 0.5)), rng)
