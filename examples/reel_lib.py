"""Tiny authoring helpers an agent can reuse to write dense timelines without hand-typing keyframes."""

from __future__ import annotations

import math
from typing import Any

PAL = {"cream": "#F6EFE3", "ink": "#17130F", "coral": "#FF6A45", "lime": "#C9F13B",
       "butter": "#FFD54A", "pink": "#FF9DBB", "mint": "#3DDBA7"}
W, H = 1920, 1080


def k(t: float, v: float, ease: str | None = None) -> dict[str, Any]:
    d: dict[str, Any] = {"t": round(t, 4), "v": round(v, 3)}
    if ease:
        d["ease"] = ease
    return d


def track(*frames: tuple) -> list[dict[str, Any]]:
    return [k(*f) for f in frames]


class Reel:
    def __init__(self, duration: float, bg: str):
        self.tl: dict[str, Any] = {"fps": 30, "duration": duration, "width": W, "height": H, "bg": PAL.get(bg, bg),
                                   "elements": [], "cuts": [], "sfx": []}

    def add(self, id: str, kind: str, color: str, **tracks_and_props: Any) -> dict[str, Any]:
        static = ("w", "h", "r", "n", "amp", "stroke", "text", "size", "weight", "split", "stagger", "type")
        props = {p: tracks_and_props.pop(p) for p in list(tracks_and_props)
                 if p in static and not isinstance(tracks_and_props[p], list)}
        el = {"id": id, "kind": kind, "color": PAL.get(color, color), **props,
              "tracks": {n: track(*f) for n, f in tracks_and_props.items()}}
        self.tl["elements"].append(el)
        return el

    def sfx(self, t: float, role: str, dur: float = 0.5, gain_db: float = -10, pan: float = 0.0) -> None:
        self.tl["sfx"].append({"t": round(t, 4), "role": role, "dur": dur, "gain_db": gain_db, "pan": pan})

    def flood(self, id: str, color: str, end: float, cx: float = W / 2, cy: float = H / 2, dur: float = 0.5) -> None:
        """Color flood: a circle that grows to cover the frame; the hit lands exactly when it closes."""
        self.add(id, "circle", color, x=[(0, cx)], y=[(0, cy)], w=[(end - dur, 0), (end, 2900, "inExpo")])
        self.sfx(end - dur * 0.55, "whoosh", 0.5, -11)
        self.tl["cuts"].append({"t": round(end, 4), "kind": "cut"})

    def split_clicks(self, t0: float, n: int, p_dur: float, stagger: float, gain_db: float = -15) -> None:
        """One tick per character of a split text revealed over p_dur starting at t0 (matches render.js)."""
        for i in range(n):
            ti = t0 + p_dur * (i * stagger) / (1 + stagger * n)
            self.sfx(ti + 0.12, "click", 0.08, gain_db + (i % 3), pan=((i / max(1, n - 1)) - 0.5) * 0.8)

    def build(self) -> dict[str, Any]:
        return self.tl


def orbit(cx: float, cy: float, r: float, a0: float, a1: float, t0: float, t1: float, steps: int = 24):
    xs, ys = [], []
    for i in range(steps + 1):
        u = i / steps
        a = math.radians(a0 + (a1 - a0) * u)
        xs.append((t0 + (t1 - t0) * u, cx + r * math.cos(a)))
        ys.append((t0 + (t1 - t0) * u, cy + r * math.sin(a)))
    return xs, ys
