"""Nature and city ambiences (v0.3): beds made of real events, not shaped noise.

The original eight textures are filtered noise with grains (`texture.py`).
These five are scenes: an ocean is waves breaking at irregular intervals over
a surf wash, a forest is leaves moving and birds calling from different
places, a night is a cricket chorus with the odd frog or owl, a stream is
thousands of small bubbles, traffic is cars passing over a low city rumble.
Each one is assembled from the physical models in `natural.py` (through
`render_foley`, so every component is band-limited to 12 kHz and fades to
zero), at random times, places and takes chosen by the seed.
"""

from __future__ import annotations

import numpy as np

from ..score import Event, Texture
from .dsp import bandlimit
from .foley import _norm, _smooth, _smooth_lowpass, render_foley
from .events import ROLE_PARAMS
from .natural import _bubble_into

AMBIENCES = ("ocean", "stream", "forest", "night", "traffic")


def _wash(rng: np.random.Generator, n: int, sr: int, lo: float, hi: float) -> np.ndarray:
    return _norm(bandlimit(rng.standard_normal(n), sr, lo, hi, order=2))


def _place(out: np.ndarray, role: str, t: float, dur: float, seed: int, gain_db: float, pan: float,
           sr: int, rng: np.random.Generator) -> None:
    """Render one event of `role` and add it to `out` at time `t` (s)."""
    n = len(out)
    at = int(t * sr)
    if at >= n:
        return
    dur = max(0.1, min(dur, (n - at) / sr))
    ev = Event(0.0, role, dur, gain_db=gain_db, pan=float(np.clip(pan, -1.0, 1.0)), seed=seed)
    p = dict(ROLE_PARAMS[role])
    clip = render_foley(ev, sr, rng, p, seed, tail=False)
    k = min(len(clip), n - at)
    out[at : at + k] += clip[:k]


def _ocean(n, sr, rng, crng):
    dur = n / sr
    out = np.zeros((n, 2))
    # the surf between breakers: a low, slowly heaving wash
    heave = 0.55 + 0.45 * _smooth(crng, n, sr, 0.15)
    for c in range(2):
        out[:, c] += 0.35 * (_wash(rng, n, sr, 50.0, 700.0) + 0.4 * _wash(rng, n, sr, 600.0, 3500.0)) * heave
    t = -crng.uniform(0.5, 3.0)
    while t < dur:
        L = crng.uniform(5.0, 8.0)
        _place(out, "wave_crash", max(0.0, t), L, int(crng.integers(1, 1 << 16)), crng.uniform(-6.0, 0.0),
               crng.uniform(-0.5, 0.5), sr, rng)
        t += crng.uniform(4.5, 8.0)
    return out


def _stream(n, sr, rng, crng):
    """A brook: water running over stones. Bubbles at many sizes in clusters
    (where the water drops over a stone), over a soft wash."""
    dur = n / sr
    out = np.zeros((n, 2))
    for c in range(2):
        dens = 0.4 + 0.6 * _smooth(crng, n, sr, 1.5)
        cnt = int(110 * dur)
        times = crng.uniform(0.0, dur, cnt)
        keep = crng.random(cnt) < np.interp(times, np.arange(n) / sr, dens)
        mono = np.zeros(n)
        for tm in times[keep]:
            _bubble_into(mono, sr, int(tm * sr), crng.uniform(350.0, 2600.0), 1.0, 0.25, crng.uniform(0.2, 1.0))
        out[:, c] = _norm(mono) + 0.35 * _wash(rng, n, sr, 250.0, 3500.0) * (0.8 + 0.2 * _smooth(crng, n, sr, 0.5))
    return out


def _forest(n, sr, rng, crng):
    """A forest in the morning: leaves moving in a light breeze, and birds
    singing from different places, near and far."""
    dur = n / sr
    out = np.zeros((n, 2))
    breeze = 0.5 + 0.5 * _smooth(crng, n, sr, 0.2)
    for c in range(2):
        leaves = _wash(rng, n, sr, 700.0, 4500.0) * (0.4 + 0.6 * _smooth(crng, n, sr, 3.0))
        low = _wash(rng, n, sr, 60.0, 400.0)
        out[:, c] += 0.035 * (leaves * breeze + 0.8 * low * breeze)
    birds = int(crng.integers(2, 5))
    for b in range(birds):
        seed = int(crng.integers(1, 1 << 16))
        pan = crng.uniform(-0.8, 0.8)
        g = crng.uniform(-14.0, -4.0)
        t = crng.uniform(0.0, 2.5)
        while t < dur - 0.5:
            L = crng.uniform(1.5, 3.5)
            _place(out, "bird_chirp", t, L, seed, g, pan, sr, rng)
            t += L + crng.uniform(1.5, 6.0)
    return out


def _night(n, sr, rng, crng):
    """A summer night: a cricket chorus all the way through, a frog or two,
    once in a while an owl far off."""
    dur = n / sr
    out = np.zeros((n, 2))
    _place(out, "crickets", 0.0, dur, 2 + 3 * int(crng.integers(0, 1000)), -4.0, 0.0, sr, rng)
    _place(out, "crickets", 0.0, dur, 3 * int(crng.integers(0, 1000)), -10.0, crng.uniform(-0.6, 0.6), sr, rng)
    t = crng.uniform(1.0, 4.0)
    while t < dur - 1.0:
        L = crng.uniform(1.5, 3.0)
        role = "owl" if crng.random() < 0.3 else "frog"
        _place(out, role, t, L, int(crng.integers(1, 1 << 16)), crng.uniform(-14.0, -8.0), crng.uniform(-0.7, 0.7), sr, rng)
        t += L + crng.uniform(3.0, 8.0)
    for c in range(2):
        out[:, c] += 0.03 * _wash(rng, n, sr, 40.0, 300.0)
    return out


def _traffic(n, sr, rng, crng):
    """A street: a low city rumble, cars passing both ways at different
    distances, rarely a horn further off."""
    dur = n / sr
    out = np.zeros((n, 2))
    for c in range(2):
        out[:, c] += 0.3 * (_wash(rng, n, sr, 30.0, 250.0) + 0.3 * _wash(rng, n, sr, 250.0, 1500.0)) * (0.8 + 0.2 * _smooth(crng, n, sr, 0.2))
    t = -crng.uniform(0.0, 2.0)
    while t < dur:
        L = crng.uniform(3.0, 5.0)
        seed = 2 + 3 * int(crng.integers(0, 1000))  # engine variant 2: passing
        _place(out, "engine", max(0.0, t), L, seed, crng.uniform(-12.0, -2.0), crng.choice((-0.5, 0.5)), sr, rng)
        t += crng.uniform(1.2, 4.0)
    if dur > 6 and crng.random() < 0.6:
        _place(out, "car_horn", crng.uniform(1.0, dur - 2.0), 0.8, int(crng.integers(1, 1 << 16)), -18.0, crng.uniform(-0.8, 0.8), sr, rng)
    return out


_FNS = {"ocean": _ocean, "stream": _stream, "forest": _forest, "night": _night, "traffic": _traffic}


def render_ambience(tx: Texture, sr: int, seed: int) -> np.ndarray:
    """The raw stereo scene, shape (n, 2), band-limited to 12 kHz. Level,
    DC, width and edges are applied by `render_texture`."""
    n = max(1, int(tx.dur * sr))
    rng = np.random.default_rng((seed * 7_777_777 + AMBIENCES.index(tx.character) * 131) & 0xFFFFFFFF)
    crng = np.random.default_rng((seed * 2_654_435_761 + 0xA4B1E) & 0xFFFFFFFF)
    out = _FNS[tx.character](n, sr, rng, crng)
    return np.stack([_smooth_lowpass(out[:, 0], sr), _smooth_lowpass(out[:, 1], sr)], axis=1)
