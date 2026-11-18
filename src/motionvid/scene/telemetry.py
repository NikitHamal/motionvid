"""Continuous scene telemetry: per-element position, size, speed and morph signals at 240 Hz.

This is what the scene engine listens to. Sound is bound to these signals (area -> sub-bass,
x -> pan, speed -> texture, w/amp rate -> tone), not only to discrete trigger times.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ..timeline import diag, sample, validate

HZ = 240
SHAPES = ("blob", "circle", "rrect", "ring")


@dataclass
class Tel:
    id: str
    kind: str
    el: dict[str, Any]
    ts: np.ndarray
    x: np.ndarray       # pixels
    y: np.ndarray
    xn: np.ndarray      # 0..1 across the frame
    speed: np.ndarray   # frame diagonals per second
    scale: np.ndarray
    op: np.ndarray
    w: np.ndarray
    h: np.ndarray
    amp: np.ndarray
    area: np.ndarray    # fraction of frame area, capped at 3


def smooth(a: np.ndarray, sec: float) -> np.ndarray:
    n = max(1, int(sec * HZ))
    return np.convolve(np.pad(a, (n, n), mode="edge"), np.ones(2 * n + 1) / (2 * n + 1), mode="valid")


def build(tl: dict[str, Any]) -> list[Tel]:
    tl = validate(tl)
    W, H = tl["width"], tl["height"]
    ts = np.arange(int(tl["duration"] * HZ) + 1) / HZ
    tsl = list(ts)
    out: list[Tel] = []
    for el in tl["elements"]:
        g = lambda n, d: np.array(sample(el, n, tsl, d))  # noqa: E731
        x, y = g("x", W / 2), g("y", H / 2)
        w = g("w", float(el.get("w") or 160))
        h = g("h", float(el["h"])) if ("h" in el or "h" in el.get("tracks", {})) else w.copy()
        sc = g("scale", 1.0)
        op = np.clip(g("opacity", 1.0), 0, 1)
        shaped = el.get("kind") in SHAPES and el.get("kind") != "ring"
        area = np.minimum(3.0, w * h * sc ** 2 / (W * H)) if shaped else np.zeros_like(ts)
        speed = np.hypot(np.gradient(x), np.gradient(y)) * HZ / diag(tl)
        out.append(Tel(el["id"], el.get("kind", "rrect"), el, ts, x, y, x / W, speed, sc, op, w, h,
                       g("amp", float(el.get("amp", 0.08))), area))
    return out


def first_cross(a: np.ndarray, level: float, i0: int, i1: int, rising: bool = True) -> int:
    seg = a[i0:i1 + 1] >= level if rising else a[i0:i1 + 1] <= level
    return i0 + int(np.argmax(seg)) if seg.any() else i1


def windows(mask: np.ndarray, pad: int = 12, join: int = 24) -> list[tuple[int, int]]:
    """Index windows where `mask` is true, padded and merged when closer than `join` samples."""
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    out, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p > join:
            out.append((max(0, s - pad), min(len(mask) - 1, p + pad)))
            s = i
        p = i
    out.append((max(0, s - pad), min(len(mask) - 1, p + pad)))
    return out
