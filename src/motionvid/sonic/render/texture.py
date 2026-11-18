"""Texture decoder: spectral trajectory + grains.

The preset is a target spectral tilt, a slow modulation, and a grain density.
A 4M head will later predict the 32-band trajectory; the renderer stays DSP.
"""

from __future__ import annotations

import numpy as np

from ..score import AMBIENCE_TEXTURES, Texture
from .dsp import TAU, db_to_gain

FADE_IN = 0.03  # s
FADE_OUT = 0.08  # s
GRAIN_ATTACK = 0.0015  # s

PRESETS: dict[str, dict] = {
    "room_cold": dict(
        points=[(20, -16), (60, -12), (200, -18), (800, -24), (3000, -32), (10000, -42)],
        lfo=(0.07, 0.18),
        grain=(0.4, 0.04),
    ),
    "wind": dict(
        points=[(20, -8), (100, -10), (500, -16), (2000, -26), (8000, -38)],
        lfo=(0.13, 0.35),
        grain=(0.2, 0.08),
    ),
    "city_hum": dict(
        points=[(20, -6), (50, -8), (120, -14), (400, -22), (1500, -30), (5000, -40)],
        lfo=(0.05, 0.12),
        grain=(0.6, 0.03),
    ),
    "vinyl": dict(
        points=[(20, -24), (100, -20), (1000, -18), (4000, -24), (12000, -36)],
        lfo=(0.9, 0.08),
        grain=(8.0, 0.006),
    ),
    "drone": dict(
        points=[(20, -6), (80, -8), (200, -10), (600, -16), (2000, -26), (6000, -36)],
        lfo=(0.03, 0.25),
        grain=(0.1, 0.1),
    ),
    "rain": dict(
        points=[(20, -18), (200, -14), (1000, -10), (4000, -14), (12000, -24)],
        lfo=(0.4, 0.1),
        grain=(30.0, 0.01),
    ),
    "fire": dict(
        points=[(20, -14), (100, -12), (500, -14), (2000, -20), (8000, -32)],
        lfo=(0.6, 0.2),
        grain=(12.0, 0.02),
    ),
    "sci_fi": dict(
        points=[(20, -10), (60, -6), (150, -12), (500, -18), (2000, -24), (8000, -38)],
        lfo=(0.2, 0.3),
        grain=(1.5, 0.05),
    ),
}


def _spectral_curve(n: int, sr: int, preset: dict, bands: list[float] | None) -> np.ndarray:
    f = np.fft.rfftfreq(n, 1.0 / sr)
    log_f = np.log10(np.maximum(f, 20.0))
    if bands is not None:
        centers = np.logspace(np.log10(20.0), np.log10(min(16000.0, sr / 2)), 32)
        curve = np.interp(log_f, np.log10(centers), np.asarray(bands, dtype=float))
    else:
        pts = np.asarray(preset["points"], dtype=float)
        curve = np.interp(log_f, np.log10(pts[:, 0]), pts[:, 1])
    return _shape_curve(curve, f)


def _shape_curve(curve_db: np.ndarray, f: np.ndarray) -> np.ndarray:
    """Roll off the ends that `np.interp` leaves flat.

    `np.interp` clamps past the last control point, so a preset whose last
    point is (12000, -36) keeps a flat -36 dB/Hz noise tail all the way to
    Nyquist. That tail is the audible hiss: real beds lose energy quickly
    above ~8 kHz. The same applies below the first point, where a slow LFO
    leaves sub energy that reads as rumble.
    """
    out = np.asarray(curve_db, dtype=float).copy()
    # -24 dB per octave above 8 kHz.
    octaves = np.log2(np.maximum(f, 1.0) / 8000.0)
    out -= 24.0 * np.clip(octaves, 0.0, None)
    # High-pass below 30 Hz.
    out -= 60.0 * np.clip((30.0 - f) / 30.0, 0.0, 1.0)
    return np.maximum(out, -140.0)


def _band_grain(rng: np.random.Generator, n: int, sr: int, center: float, q: float) -> np.ndarray:
    """A short band-passed burst, normalised to unit RMS.

    A grain built from raw white noise puts most of its energy above 12 kHz
    and reads as a click or a hiss. Band-passing it gives it a pitch.
    """
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    bw = max(center / max(q, 0.5), 120.0)
    X *= np.exp(-0.5 * ((f - center) / bw) ** 2)
    g = np.fft.irfft(X, n)
    return g / max(float(np.sqrt(np.mean(g**2) + 1e-12)), 1e-9)


def _layer(n: int, sr: int, preset: dict, bands: list[float] | None, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal(n)
    X = np.fft.rfft(noise)
    curve_db = _spectral_curve(n, sr, preset, bands)
    X *= 10.0 ** (curve_db / 20.0)
    sig = np.fft.irfft(X, n)

    t = np.arange(n) / sr
    rate, depth = preset["lfo"]
    # Three incommensurate sines instead of one: a single periodic tremolo is
    # a large part of what makes a noise bed read as "filtered white noise".
    for _ in range(3):
        r = rate * rng.uniform(0.55, 1.7)
        sig *= 1.0 + depth * 0.5 * np.sin(TAU * r * t + rng.uniform(0.0, TAU))

    bed_rms = float(np.sqrt(np.mean(sig**2) + 1e-12))
    grain_rate, grain_len = preset["grain"]
    count = int(grain_rate * n / sr)
    gl = max(8, int(grain_len * sr))
    for _ in range(count):
        # Draw pos before dur so the RNG sequence (and therefore every
        # already-rendered cue) is unchanged by the clamp below.
        pos = int(rng.integers(0, max(1, n - gl)))
        dur = max(8, int(gl * rng.uniform(0.6, 1.6)))
        dur = min(dur, n - pos)
        center = float(np.exp(rng.uniform(np.log(600.0), np.log(6000.0))))
        grain = _band_grain(rng, dur, sr, center, q=float(rng.uniform(2.0, 6.0)))
        env = np.exp(-np.linspace(0.0, 6.0, dur))
        # A grain that starts at full amplitude is a step: a broadband tick
        # up to Nyquist. A ~1.5 ms raised-cosine attack keeps it in band.
        a = min(dur // 4, max(1, int(GRAIN_ATTACK * sr)))
        env[:a] *= 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, a))
        amp = bed_rms * float(rng.uniform(1.5, 3.5))
        sig[pos : pos + dur] += grain * env * amp

    return sig


def render_texture(tx: Texture, sr: int, seed: int = 0) -> np.ndarray:
    """Render one texture to stereo, shape (n, 2), with a seamless loop point."""
    n = max(1, int(tx.dur * sr))
    if tx.character in AMBIENCE_TEXTURES:
        # Scenes built from event models (v0.3); no loop tiling, the whole
        # bed is rendered.
        from .ambience import render_ambience

        raw = render_ambience(tx, sr, seed)
        mid = 0.5 * (raw[:, 0] + raw[:, 1])
        side = 0.5 * (raw[:, 0] - raw[:, 1]) * min(1.0, tx.width / 0.7)
        out = np.stack([mid + side, mid - side], axis=1)
        out -= out.mean(axis=0, keepdims=True)
        r = float(np.sqrt(np.mean(out**2) + 1e-12))
        out *= 0.08 / max(r, 1e-9)
        out = _edge_fades(out, sr)
        return out * db_to_gain(tx.gain_db)
    preset = PRESETS[tx.character]
    rng = np.random.default_rng(seed)

    left = _layer(n, sr, preset, tx.bands, rng)
    right = _layer(n, sr, preset, tx.bands, rng)

    mid = 0.5 * (left + right)
    side = 0.5 * (left - right) * tx.width
    left, right = mid + side, mid - side

    # Seamless loop: blend the tail into the head, drop the tail, then tile
    # the loop back to the requested length.
    k = int(0.4 * sr)
    if n > 2 * k:
        f = np.linspace(0.0, 1.0, k)[:, None]
        head = np.stack([left[:k], right[:k]], axis=1)
        tail = np.stack([left[n - k :], right[n - k :]], axis=1)
        blended = tail * (1.0 - f) + head * f
        loop = np.concatenate(
            [blended, np.stack([left[k : n - k], right[k : n - k]], axis=1)], axis=0
        )
        reps = int(np.ceil(n / len(loop)))
        left = np.tile(loop[:, 0], reps)[:n]
        right = np.tile(loop[:, 1], reps)[:n]

    out = np.stack([left, right], axis=1)
    # Remove DC here, before the fades, so the bed starts and ends at exactly
    # zero. (Doing it on the summed stem would re-open a step at sample 0.)
    out -= out.mean(axis=0, keepdims=True)
    r = float(np.sqrt(np.mean(out**2) + 1e-12))
    out *= 0.08 / max(r, 1e-9)
    out = _edge_fades(out, sr)
    return out * db_to_gain(tx.gain_db)


def _edge_fades(x: np.ndarray, sr: int) -> np.ndarray:
    """Raised-cosine fade-in and fade-out, so the bed never starts or stops on a step."""
    n = len(x)
    a = min(n // 4, int(FADE_IN * sr))
    b = min(n // 4, int(FADE_OUT * sr))
    if a > 1:
        x[:a] *= (0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, a)))[:, None]
    if b > 1:
        x[n - b :] *= (0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, b)))[:, None]
    return x
