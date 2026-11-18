"""3D recipes: box3d solids, flat-shaded spheres, exploded layer stacks, orbiting spheres. Flat shading only (no shadows, no gradients)."""

from __future__ import annotations

import math
from typing import Any

from .core import Scene, item, put


def box(S: Scene, id: str, t: float, x: float, y: float, w: float, color: str = "coral", h: float | None = None, d: float | None = None,
        rx: float = -20, ry: tuple = (24, 24), t1: float | None = None, items: list | tuple = (), sound: str | None = "pop", **kw: Any) -> dict[str, Any]:
    t1 = t1 if t1 is not None else t + 3.0
    extra: dict[str, Any] = {"items": list(items)} if items else {}
    el = S.add(id, "box3d", color, x=x, y=y, w=w, h=h or w, d=d or w, rx=rx, ry=[(t, ry[0]), (t1, ry[1], "inOutSine")], persp=1600, **extra, **kw)
    return S.appear(el, t, frm=0.6, sound=sound, x=x)


def orb(S: Scene, id: str, t: float, x: float, y: float, d: float, color: str = "lime", sound: str | None = "pop") -> dict[str, Any]:
    return S.appear(S.add(id, "sphere", color, x=x, y=y, w=d), t, frm=0.4, sound=sound, x=x)


def stack(S: Scene, id: str, t: float, x: float, y: float, w: float, h: float, colors: list[str], open_at: float, gap: float = 96,
          r: float = 52, rx: tuple = (-16, -54), ry: tuple = (0, 26), t1: float | None = None, items_per_layer: list | None = None) -> dict[str, Any]:
    """Exploded layers: collapsed at t, spread along z at open_at. Layer 0 is the back."""
    n = len(colors)
    its = []
    for i, c in enumerate(colors):
        z1 = (i - (n - 1) / 2) * gap
        its.append(item("rrect", c, w=w, h=h, r=r, z=[(open_at, 0), (open_at + 1.0, z1, "spring")]))
        for sub in (items_per_layer[i] if items_per_layer else []):
            its.append({**sub, "tracks": {**sub.get("tracks", {}), "z": [{"t": open_at, "v": 1}, {"t": open_at + 1.0, "v": z1 + 2, "ease": "spring"}]}})
    t1 = t1 if t1 is not None else open_at + 5
    el = S.group(id, its, x=x, y=y, w=w, h=h, persp=1500, rx=[(t, rx[0]), (open_at, rx[0]), (open_at + 1.2, rx[1], "m3Dec")], ry=[(t, ry[0]), (t1, ry[1], "inOutSine")])
    S.sfx(open_at, "swipe", 0.3, -12, S.pan_of(x))
    return S.appear(el, t, frm=0.85, sound="pop", x=x)


def orbit_spheres(S: Scene, id: str, t0: float, t1: float, cx: float, cy: float, rx: float, ry: float, colors: list[str], d: float = 130, turns: float = 1.0) -> list:
    out = []
    n = len(colors)
    for i, c in enumerate(colors):
        xs, ys, ss = [], [], []
        for j in range(33):
            u = j / 32
            a = 2 * math.pi * (i / n + turns * u)
            tt = t0 + (t1 - t0) * u
            xs.append((tt, cx + rx * math.cos(a)))
            ys.append((tt, cy + ry * math.sin(a) * 0.45))
            ss.append((tt, 0.72 + 0.38 * (math.sin(a) * 0.5 + 0.5)))
        out.append(S.appear(S.add(f"{id}{i}", "sphere", c, w=d, x=xs, y=ys, scale=ss), t0 + i * 0.08, sound=None, frm=0.3))
    return out
