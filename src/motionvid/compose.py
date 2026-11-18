"""Anchor-aligned, cached, unlimited-event mixer.

Why this exists: the upstream mixer places an event by its START time. A whoosh's loud moment is
~0.55*dur later, a riser's is at its end, an impact's is at its start, so an agent that writes
`@cue_time` lands every sound late by an amount that depends on the role. Here every cue's *anchor*
(first -3 dB crossing of the smoothed envelope, measured on the rendered audio) is placed on the
cue time with sample precision. Clips are rendered once and cached, so repeated motion is cheap.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np

from .sonic.render.dsp import db_to_gain, rms
from .sonic.render.events import render_event
from .sonic.render.mix import END_FADE, _active_ref
from .sonic.render.texture import render_texture
from .sonic.score import Event, Texture

SR = 48000
VARIANTS = 3
FALLBACKS: list[tuple[str, float]] = []  # (role, requested dur) that needed a longer render


def anchor_sample(clip: np.ndarray, sr: int = SR, frac: float = 0.7, win_ms: float = 5.0) -> int:
    """Index where the smoothed envelope first reaches `frac` of its peak (the audible hit)."""
    mono = np.abs(clip).max(axis=1) if clip.ndim > 1 else np.abs(clip)
    w = max(1, int(win_ms * sr / 1000))
    c = np.cumsum(np.concatenate([[0.0], mono.astype(np.float64) ** 2]))
    env = np.sqrt((c[w:] - c[:-w]) / w)
    if env.size == 0 or env.max() <= 1e-9:
        return 0
    return int(np.argmax(env >= frac * env.max()))


_CACHE: dict[tuple, tuple[np.ndarray, int]] = {}
DUR_BUCKETS = (0.15, 0.3, 0.6, 1.2, 2.4)


def _bucket(dur: float) -> float:
    return min(DUR_BUCKETS, key=lambda b: abs(np.log(b / max(dur, 0.05))))


def _render_key(key: tuple) -> tuple[np.ndarray, int]:
    role, dur, variant, sr = key
    d = dur
    for _ in range(8):
        try:
            ev = Event(t=0.0, role=role, dur=d, gain_db=0.0, pan=0.0, seed=1 + variant)
            clip = render_event(ev, sr, seed=1 + variant, tail=True).astype(np.float32)
            if float(np.abs(clip).max()) > 1e-5:  # some upstream roles are silent at short durations
                return clip, anchor_sample(clip, sr)
        except ValueError:  # ...and others reject them
            pass
        FALLBACKS.append((role, dur))
        d *= 1.5
    raise ValueError(f"role {role!r} cannot render at dur>={dur}")


def cache_info() -> dict[str, int]:
    return {"entries": len(_CACHE)}


def cache_clear() -> None:
    _CACHE.clear()


def _key(cue: dict[str, Any], sr: int) -> tuple:
    return (cue["role"], _bucket(cue["dur"]), cue["seed"] % VARIANTS, sr)


def prerender(cues: list[dict[str, Any]], sr: int = SR, workers: int | None = None) -> int:
    """Render every distinct (role, duration bucket, variant) once, in parallel. Returns #rendered."""
    todo = sorted({_key(c, sr) for c in cues} - set(_CACHE))
    w = workers if workers is not None else min(len(os.sched_getaffinity(0)), 8)
    if w > 1 and len(todo) > 1:
        with ProcessPoolExecutor(max_workers=w) as ex:
            for k, v in zip(todo, ex.map(_render_key, todo, chunksize=1)):
                _CACHE[k] = v
    else:
        for k in todo:
            _CACHE[k] = _render_key(k)
    return len(todo)


def clip_for(cue: dict[str, Any], sr: int = SR) -> tuple[np.ndarray, int]:
    k = _key(cue, sr)
    if k not in _CACHE:
        _CACHE[k] = _render_key(k)
    clip, a = _CACHE[k]
    p = float(np.clip(cue["pan"], -1, 1))
    if abs(p) > 1e-6:  # equal-power balance on the centred clip
        th = (p + 1) * np.pi / 4
        clip = clip * (np.array([np.cos(th), np.sin(th)], dtype=np.float32) * np.sqrt(2))
    return clip, a


def render_cues(cues: list[dict[str, Any]], duration: float, sr: int = SR, bed: str | None = None,
                bed_db: float = -24.0, anchor: bool = True, workers: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
    prerender(cues, sr, workers)
    n = int(round(duration * sr))
    ev = np.zeros((n, 2), dtype=np.float64)
    cropped = 0
    for c in cues:
        clip, a = clip_for(c, sr)
        start = int(round(c["t"] * sr)) - (a if anchor else 0)
        sig = clip.astype(np.float64) * db_to_gain(c["gain_db"])
        if start < 0:
            cropped += 1
            sig, start = sig[-start:], 0
        end = min(n, start + len(sig))
        if end > start:
            ev[start:end] += sig[: end - start]
    b = min(n, int(END_FADE * sr))
    if b > 1:
        ev[n - b:] *= np.linspace(1.0, 0.0, b)[:, None]
    peak = float(np.abs(ev).max())
    g_fg = 0.89 / peak if peak > 1e-6 else 0.0
    mix = ev * g_fg
    if bed:
        tex = render_texture(Texture(0.0, duration, bed, gain_db=bed_db, width=0.7), sr, seed=7)[:n]
        tex = np.pad(tex, ((0, n - len(tex)), (0, 0)))
        ref = _active_ref(ev, sr) * g_fg if peak > 1e-6 else 0.1
        t_rms = max(rms(tex), 1e-9)
        mix = mix + tex * min(ref * db_to_gain(bed_db) / t_rms, ref / t_rms)
    p = float(np.abs(mix).max())
    if p > 0.98:
        mix *= 0.98 / p
    return mix.astype(np.float32), {"cues": len(cues), "cropped_lead": cropped, "fg_gain": g_fg}
