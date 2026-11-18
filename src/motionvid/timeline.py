"""Motion timeline schema: what an LLM agent writes, and what the video is rendered from.

A timeline is plain JSON::

    {"fps": 30, "duration": 6, "width": 1920, "height": 1080,
     "elements": [{"id": "logo", "kind": "shape",
                   "tracks": {"x": [{"t": 0, "v": -300}, {"t": 0.6, "v": 960, "ease": "inCubic"}],
                              "scale": [{"t": 0.6, "v": 0.4}, {"t": 0.8, "v": 1.0, "ease": "outBack"}]}}],
     "cuts": [{"t": 3.0, "kind": "wipe"}],
     "sfx": [{"t": 5.0, "role": "riser", "dur": 1.0}]}

A keyframe's ``ease`` shapes the segment that ENDS at that keyframe.
"""

from __future__ import annotations

import math
from typing import Any

EASES = {
    "linear": lambda u: u,
    "inQuad": lambda u: u * u,
    "outQuad": lambda u: 1 - (1 - u) ** 2,
    "inOutQuad": lambda u: 2 * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 2 / 2,
    "inCubic": lambda u: u**3,
    "outCubic": lambda u: 1 - (1 - u) ** 3,
    "inOutCubic": lambda u: 4 * u**3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
    "inExpo": lambda u: 0.0 if u <= 0 else 2 ** (10 * u - 10),
    "outExpo": lambda u: 1.0 if u >= 1 else 1 - 2 ** (-10 * u),
    "outBack": lambda u: 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,
    "inBack": lambda u: 2.70158 * u**3 - 1.70158 * u**2,
    "outElastic": lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else 2 ** (-10 * u) * math.sin((u * 10 - 0.75) * 2 * math.pi / 3) + 1,
    "outBounce": lambda u: _bounce(u),
}


def _bounce(u: float) -> float:
    n, d = 7.5625, 2.75
    if u < 1 / d:
        return n * u * u
    if u < 2 / d:
        u -= 1.5 / d
        return n * u * u + 0.75
    if u < 2.5 / d:
        u -= 2.25 / d
        return n * u * u + 0.9375
    u -= 2.625 / d
    return n * u * u + 0.984375


class TimelineError(ValueError):
    pass


def track_value(kfs: list[dict[str, Any]], t: float) -> float:
    if t <= kfs[0]["t"]:
        return float(kfs[0]["v"])
    if t >= kfs[-1]["t"]:
        return float(kfs[-1]["v"])
    for a, b in zip(kfs, kfs[1:]):
        if a["t"] <= t <= b["t"]:
            span = b["t"] - a["t"]
            u = 1.0 if span <= 0 else (t - a["t"]) / span
            f = EASES[b.get("ease", "linear")](min(1.0, max(0.0, u)))
            return float(a["v"]) + (float(b["v"]) - float(a["v"])) * f
    return float(kfs[-1]["v"])


def validate(tl: dict[str, Any]) -> dict[str, Any]:
    """Return the timeline with defaults filled; raise TimelineError with an actionable message."""
    if not isinstance(tl, dict):
        raise TimelineError("timeline must be a JSON object")
    tl = dict(tl)
    tl.setdefault("fps", 30)
    tl.setdefault("width", 1920)
    tl.setdefault("height", 1080)
    tl.setdefault("elements", [])
    tl.setdefault("cuts", [])
    tl.setdefault("sfx", [])
    dur = tl.get("duration")
    if not isinstance(dur, (int, float)) or dur <= 0:
        raise TimelineError("'duration' (seconds) is required and must be > 0")
    for el in tl["elements"]:
        if "id" not in el:
            raise TimelineError("every element needs an 'id'")
        for name, kfs in el.get("tracks", {}).items():
            if not kfs:
                raise TimelineError(f"element {el['id']!r} track {name!r} is empty")
            ts = [k["t"] for k in kfs]
            if ts != sorted(ts):
                raise TimelineError(f"element {el['id']!r} track {name!r}: keyframes must be time-sorted")
            for k in kfs:
                if k.get("ease", "linear") not in EASES:
                    raise TimelineError(f"unknown ease {k['ease']!r}; use one of {sorted(EASES)}")
    for c in tl["cuts"]:
        if not 0 <= c["t"] <= dur:
            raise TimelineError(f"cut at t={c['t']} is outside the duration")
    return tl


def sample(el: dict[str, Any], name: str, times: list[float], default: float) -> list[float]:
    kfs = el.get("tracks", {}).get(name)
    if not kfs:
        return [default] * len(times)
    return [track_value(kfs, t) for t in times]


def diag(tl: dict[str, Any]) -> float:
    return math.hypot(tl["width"], tl["height"])
