"""Motion -> sound cues, from the physics of the motion alone (0 parameters, no model, no language).

Cue = {t, role, dur, gain_db, pan, seed, why}. ``t`` is the moment the HIT must be heard
(peak speed, abrupt stop, pop apex, cut); the renderer anchors the sound's own hit to it.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np

from . import genome as G
from .timeline import diag, sample, validate

HZ = 240.0
CUT_ROLE = {"cut": ("impact", -14.0), "flash": ("impact", -8.0), "wipe": ("whoosh", -9.0),
            "glitch": ("glitch", -10.0), "dissolve": ("swell", -14.0)}


def _seed(*parts: Any) -> int:
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:7], 16)


def _gain(intensity: float, g: dict[str, float]) -> float:
    x = min(1.0, max(0.0, intensity)) ** g["intensity_gamma"]
    return g["gain_floor_db"] + (g["gain_ceiling_db"] - g["gain_floor_db"]) * x


def _pan(x_px: float, tl: dict[str, Any], g: dict[str, float]) -> float:
    return float(np.clip((x_px / tl["width"] - 0.5) * 2 * g["pan_width"], -1, 1))


def _segments(speed: np.ndarray, on: float) -> list[tuple[int, int]]:
    segs, start = [], None
    for i, s in enumerate(speed):
        if s > on and start is None:
            start = i
        elif s <= on and start is not None:
            segs.append((start, i)); start = None
    if start is not None:
        segs.append((start, len(speed) - 1))
    return segs


def _element_cues(tl: dict[str, Any], el: dict[str, Any], g: dict[str, float]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    n = int(tl["duration"] * HZ) + 1
    ts = [i / HZ for i in range(n)]
    x = np.array(sample(el, "x", ts, 0.0)); y = np.array(sample(el, "y", ts, 0.0))
    d = diag(tl)
    speed = np.hypot(np.gradient(x), np.gradient(y)) * HZ / d
    for a, b in _segments(speed, g["seg_on_speed"]):
        dur = (b - a) / HZ
        pk = a + int(np.argmax(speed[a:b + 1]))
        w = max(1, int(g["impact_stop_window"] * HZ))
        pre = float(speed[max(a, b - w)])
        px = float(x[pk])
        if pre >= g["impact_min_pre_speed"] and b < n - 1:
            out.append(dict(t=b / HZ, role="impact", dur=0.6, gain_db=_gain(pre, g), pan=_pan(float(x[b]), tl, g),
                            seed=_seed(el["id"], "i", b), why=f"{el['id']}: abrupt stop from {pre:.2f} diag/s"))
        if speed[pk] >= g["whoosh_min_speed"] and dur >= g["whoosh_min_dur"]:
            out.append(dict(t=pk / HZ, role="whoosh", dur=float(np.clip(dur * 1.2, 0.3, 1.6)),
                            gain_db=_gain(float(speed[pk]) / 1.6, g), pan=_pan(px, tl, g),
                            seed=_seed(el["id"], "w", pk), why=f"{el['id']}: peak speed {speed[pk]:.2f} diag/s"))
    sc = np.array(sample(el, "scale", ts, 1.0))
    win = max(1, int(g["pop_max_dur"] * HZ))
    i = 0
    while i < n - 1:
        j = min(n - 1, i + win)
        if sc[i:j + 1].max() - sc[i] >= g["pop_min_scale_delta"] and sc[min(n - 1, i + 1)] - sc[i] > 1e-6:
            k = i + int(np.argmax(sc[i:j + 1]))
            out.append(dict(t=k / HZ, role="ui_pop", dur=0.25, gain_db=_gain(0.55, g),
                            pan=_pan(float(x[k]) if "x" in el.get("tracks", {}) else tl["width"] / 2, tl, g),
                            seed=_seed(el["id"], "p", k), why=f"{el['id']}: scale pop to {sc[k]:.2f}"))
            i = k + int(0.25 * HZ)
        else:
            i += 1
    op = np.array(sample(el, "opacity", ts, 1.0))
    fw = max(1, int(g["fade_max_dur"] * HZ))
    for i in range(0, n - fw):
        if op[i] <= 0.05 and op[i + fw] >= 0.9:
            k = i + int(np.argmax(op[i:i + fw + 1] >= 0.5))
            out.append(dict(t=k / HZ, role="ui_pop", dur=0.2, gain_db=_gain(0.3, g),
                            pan=_pan(float(x[k]), tl, g) if "x" in el.get("tracks", {}) else 0.0,
                            seed=_seed(el["id"], "f", k), why=f"{el['id']}: fast fade-in"))
            break
    ty = el.get("type")
    if ty:
        for c in range(int(ty["n"])):
            out.append(dict(t=ty["t"] + c / ty["cps"], role="click", dur=0.08, gain_db=-17.0 + (c % 3),
                            pan=0.0, seed=_seed(el["id"], "c", c), why=f"{el['id']}: typed char {c}"))
    return out


def compile_cues(tl: dict[str, Any], genome: dict[str, float] | None = None) -> list[dict[str, Any]]:
    """Timeline -> sorted, de-duplicated cue list."""
    tl = validate(tl)
    g = genome or G.load()
    cues: list[dict[str, Any]] = []
    for el in tl["elements"]:
        cues += _element_cues(tl, el, g)
    for c in tl["cuts"]:
        role, db = CUT_ROLE.get(c.get("kind", "cut"), ("impact", -14.0))
        cues.append(dict(t=float(c["t"]), role=role, dur=0.7 if role != "glitch" else 0.3, gain_db=db, pan=0.0,
                         seed=_seed("cut", c["t"]), why=f"cut:{c.get('kind', 'cut')}"))
    for s in tl["sfx"]:
        cues.append(dict(t=float(s["t"]), role=s["role"], dur=float(s.get("dur", 0.6)), gain_db=float(s.get("gain_db", -8.0)),
                         pan=float(s.get("pan", 0.0)), seed=_seed("sfx", s["role"], s["t"]), why="agent hint"))
    cues.sort(key=lambda c: (c["t"], c["role"]))
    kept: list[dict[str, Any]] = []
    for c in cues:
        dup = next((k for k in reversed(kept) if k["role"] == c["role"] and c["t"] - k["t"] < g["min_gap"]), None)
        if dup is None:
            kept.append(c)
        elif c["gain_db"] > dup["gain_db"]:
            kept[kept.index(dup)] = c
    return kept
