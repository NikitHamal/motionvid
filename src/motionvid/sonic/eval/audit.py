"""Model-free audit: the hard gate that a reward model cannot game."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..io import read_wav


def audit_waveform(audio: np.ndarray, sr: int) -> dict[str, float]:
    if audio.ndim > 1:
        mono = audio.mean(axis=1)
    else:
        mono = audio
    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    rms = float(np.sqrt(np.mean(mono**2) + 1e-12))
    rms_db = float(20.0 * np.log10(rms + 1e-12))
    dc = float(np.mean(mono)) if len(mono) else 0.0
    diff = np.abs(np.diff(mono))
    max_jump = float(np.max(diff)) if len(diff) else 0.0
    click_score = max_jump / max(peak, 1e-9)

    threshold = 0.02 * max(peak, 1e-9)
    above = np.where(np.abs(mono) > threshold)[0]
    onset = float(above[0] / sr) if len(above) else 0.0

    spec = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), 1.0 / sr)
    centroid = float(np.sum(freqs * spec) / (np.sum(spec) + 1e-9))

    return {
        "peak": peak,
        "rms_dbfs": rms_db,
        "dc": dc,
        "max_jump": max_jump,
        "click_score": click_score,
        "onset": onset,
        "spectral_centroid": centroid,
        "clipped_fraction": float(np.mean(np.abs(mono) >= 0.999)),
    }


def audit_file(path: str | Path) -> dict[str, float]:
    audio, sr = read_wav(path)
    return audit_waveform(audio, sr)


def passes(audit: dict[str, float]) -> bool:
    # `click_score` is reported but not gated: a click, glitch or impact is an
    # intentional transient, not a rendering bug. The texture stem is checked
    # separately for discontinuities.
    return (
        audit["peak"] <= 0.99
        and abs(audit["dc"]) < 0.001
        and audit["clipped_fraction"] == 0.0
    )
