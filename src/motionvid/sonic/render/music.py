"""Music decoder: a tiny symbolic instrument synth.

Six voices, additive/FM/noise, no samples, no model. The score carries the
notes; this file carries the timbre.
"""

from __future__ import annotations

import numpy as np

from ..score import MusicTrack
from .dsp import TAU, db_to_gain, lowpass, pan, shaped_burst


def _additive(f: float, t: np.ndarray, harmonics: int, tilt: float, sr: int) -> np.ndarray:
    k = np.arange(1, harmonics + 1, dtype=float)
    freqs = f * k
    keep = freqs < sr * 0.45
    if not np.any(keep):
        return np.zeros_like(t)
    k, freqs = k[keep], freqs[keep]
    return (np.sin(TAU * freqs[:, None] * t[None, :]) / k[:, None] ** tilt).sum(axis=0)


def _note(instrument: str, midi: int, dur: float, vel: float, sr: int, seed: int) -> np.ndarray:
    f = 440.0 * 2.0 ** ((midi - 69) / 12.0)
    n = max(1, int(dur * sr))
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)

    if instrument == "pluck":
        k = np.arange(1, 13, dtype=float)
        freqs = f * k
        keep = freqs < sr * 0.45
        k, freqs = k[keep], freqs[keep]
        amps = np.exp(-t[None, :] * (4.0 + 0.9 * k[:, None]) / max(dur, 0.1)) / k[:, None]
        out = (np.sin(TAU * freqs[:, None] * t[None, :]) * amps).sum(axis=0)
        out *= np.exp(-2.0 * t / max(dur, 0.1))

    elif instrument == "pad":
        out = np.zeros(n)
        for det in (-0.004, 0.0, 0.004):
            out += _additive(f * (1.0 + det), t, 12, 1.0, sr)
        out *= np.minimum(t / 0.35, 1.0) * np.exp(-0.3 * t / max(dur, 0.1))
        out = lowpass(out, sr, 1800.0)

    elif instrument == "bass":
        out = np.sin(TAU * f * t) + 0.25 * _additive(f, t, 6, 1.0, sr)
        out *= np.exp(-2.0 * t / max(dur, 0.1))

    elif instrument == "bell":
        mod = np.sin(TAU * f * 3.5 * t) * 2.2 * np.exp(-3.0 * t / max(dur, 0.1))
        out = np.sin(TAU * f * t + mod) * np.exp(-2.5 * t / max(dur, 0.1))

    elif instrument == "perc":
        out = shaped_burst(rng, n, int(0.12 * sr), 12.0, sr, lo=200.0, hi=10000.0)
        out += np.sin(TAU * 70.0 * t) * np.exp(-8.0 * t / max(dur, 0.1)) * 0.5

    elif instrument == "strings":
        out = _additive(f, t, 16, 1.0, sr) * (1.0 + 0.02 * np.sin(TAU * 5.0 * t))
        out *= np.minimum(t / 0.25, 1.0) * np.exp(-0.2 * t / max(dur, 0.1))
        out = lowpass(out, sr, 3000.0)

    else:
        raise ValueError(f"unknown instrument {instrument!r}")

    return out * vel


def render_track(track: MusicTrack, sr: int, n_total: int, seed: int = 0) -> np.ndarray:
    """Render one music track to stereo, shape (n_total, 2)."""
    out = np.zeros((n_total, 2))
    rng = np.random.default_rng(seed)

    for note in track.notes:
        if track.humanize > 0:
            jitter_t = float(rng.normal(0.0, track.humanize))
            jitter_v = float(1.0 + rng.normal(0.0, track.humanize * 2.0))
        else:
            jitter_t, jitter_v = 0.0, 1.0

        vel = float(np.clip(note.vel * jitter_v, 0.0, 1.0))
        sig = _note(track.instrument, note.midi, note.dur, vel, sr, int(rng.integers(1 << 31)))
        start = int(max(0.0, note.t + jitter_t) * sr)
        end = min(n_total, start + len(sig))
        if end <= start:
            continue
        left, right = pan(sig[: end - start], track.pan)
        out[start:end, 0] += left
        out[start:end, 1] += right

    return out * db_to_gain(track.gain_db)
