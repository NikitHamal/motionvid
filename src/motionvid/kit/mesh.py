"""Real 3D: mesh parts (rounded solids, lathe solids, torus, extrusions) and ready objects (phone, laptop, tower of bars, globe, rack, coin).
Parts are lit per face (flat colors, bevels catch the light). No shadows, no gradients. Screens are flat UI items texture-mapped onto a face."""

from __future__ import annotations

import math
from typing import Any

from .core import PAL, Scene, k

TRACKABLE = ("x", "y", "z", "rx", "ry", "rz", "s", "opacity", "w", "h", "d", "r", "b", "len", "R")


def part(prim: str, color: str | None = None, **kw: Any) -> dict[str, Any]:
    """prim: rbox | cyl | sphere | cone | capsule | torus | gem | extrude. Lists on x y z rx ry rz s opacity w h d r b len R become tracks."""
    out: dict[str, Any] = {"prim": prim}
    if color:
        out["color"] = PAL.get(color, color)
    tr: dict[str, Any] = {}
    pos, rot = list(kw.pop("pos", [0, 0, 0])), list(kw.pop("rot", [0, 0, 0]))
    for i, n in enumerate(("x", "y", "z")):
        if isinstance(kw.get(n), (int, float)):
            pos[i] = kw.pop(n)
    for i, n in enumerate(("rx", "ry", "rz")):
        if isinstance(kw.get(n), (int, float)):
            rot[i] = kw.pop(n)
    out["pos"], out["rot"] = pos, rot
    for n, v in kw.items():
        if isinstance(v, list) and n in TRACKABLE:
            tr[n] = [k(*f) for f in v]
        elif n == "faces":
            out[n] = {a: PAL.get(b, b) for a, b in v.items()}
        else:
            out[n] = v
    if tr:
        out["tracks"] = tr
    return out


def mesh(S: Scene, id: str, t: float | None, x: float, y: float, parts: list, size: float = 400, rx: Any = -12, ry: Any = 0, rz: Any = 0,
         persp: float = 1700, sound: str | None = "pop", frm: float = 0.7, **kw: Any) -> dict[str, Any]:
    """Place a mesh element. rx/ry/rz: number or keyframes [(t, deg[, ease])]. t=None adds it without an appear."""
    el = S.add(id, "mesh", None, x=x, y=y, w=size, h=size, rx=rx, ry=ry, rz=rz, persp=persp, parts=parts, **kw)
    return S.appear(el, t, frm=frm, sound=sound, x=x) if t is not None else el


def spin(t0: float, t1: float, a0: float, a1: float, ease: str = "inOutSine") -> list:
    return [(t0, a0), (t1, a1, ease)]


def phone3d(items: list, w: float = 420, h: float = 860, body: str = "ink", bg: str = "cream", d: float = 46, **kw: Any) -> list:
    return [part("rbox", body, w=w, h=h, d=d, r=w * 0.14, seg=4, gloss=16, screen={"items": items, "w": w * 0.93, "h": h * 0.955, "r": w * 0.115, "bg": PAL.get(bg, bg)}, **kw)]


def laptop3d(items: list, w: float = 1000, body: str = "sand", bg: str = "cream", open_deg: float = 14, **kw: Any) -> list:
    lh, bd, bh = w * 0.62, w * 0.66, 26
    c, sn = math.cos(math.radians(open_deg)), math.sin(math.radians(open_deg))
    hy, hz = bh / 2 * -1 + 0, -bd / 2
    lid = part("rbox", body, w=w, h=lh, d=20, r=14, seg=3, gloss=12, rx=open_deg, pos=[0, hy - lh / 2 * c, hz - lh / 2 * sn],
               screen={"items": items, "w": w * 0.94, "h": lh * 0.92, "r": 12, "bg": PAL.get(bg, bg)}, **kw)
    base = part("rbox", body, w=w * 1.04, h=bh, d=bd, r=12, seg=3, gloss=10, faces={"top": PAL.get("sand")}, pos=[0, 0, 0])
    keys = part("rbox", "ink", w=w * 0.84, h=3, d=bd * 0.46, r=1.4, pos=[0, -bh / 2 - 1, bd * 0.08])
    pad = part("rbox", PAL["sand"], w=w * 0.3, h=3, d=bd * 0.2, r=1.4, pos=[0, -bh / 2 - 1, bd * 0.38])
    out = [base, keys, pad, lid]
    for p_ in out:  # centre the open laptop vertically on the element
        p_["pos"][1] += lh * 0.36
    return out


def bars3d(vals: list[float], t0: float, w_total: float, h_max: float, colors: list[str], depth: float = 120, stagger: float = 0.12, gap: float = 0.5, r: float = 18) -> list:
    n = len(vals)
    bw = w_total / (n + (n - 1) * gap)
    out = []
    for i, v in enumerate(vals):
        hh, ti = h_max * v, t0 + i * stagger
        out.append(part("rbox", colors[i % len(colors)], w=bw, d=depth, r=r, seg=3, gloss=10, pos=[-w_total / 2 + bw / 2 + i * bw * (1 + gap), 0, 0],
                        h=[(ti, 4), (ti + 0.9, hh, "spring")], y=[(ti, h_max / 2 - 2), (ti + 0.9, h_max / 2 - hh / 2, "spring")]))
    return out


def globe(r: float, core: str = "moss", ring: str = "butter", n: int = 5) -> list:
    out = [part("sphere", core, r=r, gloss=14)]
    for i in range(n):
        out.append(part("torus", ring, R=r * 1.02, r=3.2, seg=64, rz=90, ry=i * 180 / n))
    out.append(part("torus", ring, R=r * 1.02, r=3.2, seg=64, rx=0))
    return out


def rack(w: float = 360, units: int = 5, body: str = "ink", accent: str = "lime", gap: float = 8, unit_h: float = 62) -> list:
    out, total = [part("rbox", "sand", w=w + 40, h=units * (unit_h + gap) + 30, d=w * 0.8, r=18, seg=3)], units * (unit_h + gap)
    for i in range(units):
        y = -total / 2 + gap / 2 + unit_h / 2 + i * (unit_h + gap) + 4
        out.append(part("rbox", body, w=w, h=unit_h, d=w * 0.86, r=10, pos=[0, y, w * 0.06], gloss=10))
        out.append(part("cyl", accent, r=6, h=4, b=1.5, rx=90, pos=[-w * 0.4, y, w * 0.06 + w * 0.43 + 2]))
        out.append(part("rbox", "sand", w=w * 0.36, h=8, d=4, r=2, pos=[w * 0.1, y, w * 0.06 + w * 0.43 + 2]))
    return out


def coin(r: float, color: str = "butter", rim: str = "clay", h: float = 34) -> list:
    return [part("cyl", color, r=r, h=h, b=h * 0.45, rx=90, gloss=26, faces={"side": PAL.get(rim, rim)}), part("torus", rim, R=r * 0.72, r=h * 0.13, seg=48, rx=90, pos=[0, 0, h / 2 + 1])]


def cube_photos(size: float, photos: dict[str, str], body: str = "ink", r: float = 26) -> list:
    """Rounded cube with a photo on each named face (front, back, left, right, top): photos={'front': 'beach', ...}."""
    from .media import photo
    scr = [{"face": f, "items": [photo(n, size * 0.9, size * 0.9, r * 0.6) if f not in ("top",) else photo(n, size * 0.9, size * 0.9, r * 0.6)], "w": size * 0.9, "h": size * 0.9, "r": r * 0.6, "bg": PAL["sand"]} for f, n in photos.items()]
    return [part("rbox", body, w=size, h=size, d=size, r=r, seg=4, gloss=10, screen=scr)]


def orbit_parts(parts_fn, n: int, radius: float, t0: float, t1: float, turns: float = 1.0, face_out: bool = False) -> list:
    """Place n copies on a ring in the xz plane and orbit them: parts_fn(i) -> part dict (without pos)."""
    out = []
    for i in range(n):
        p = parts_fn(i)
        xs, zs = [], []
        for j in range(25):
            u = j / 24
            a = 2 * math.pi * (i / n + turns * u)
            xs.append((t0 + (t1 - t0) * u, radius * math.cos(a)))
            zs.append((t0 + (t1 - t0) * u, radius * math.sin(a)))
        p.setdefault("tracks", {})["x"] = [k(*f) for f in xs]
        p["tracks"]["z"] = [k(*f) for f in zs]
        if face_out:  # card fronts look away from the centre
            p["tracks"]["ry"] = [k(t0 + (t1 - t0) * j / 24, 90 - math.degrees(2 * math.pi * (i / n + turns * j / 24))) for j in range(25)]
        out.append(p)
    return out
