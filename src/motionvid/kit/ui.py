"""UI components as groups (local px around the group centre). Each recipe adds its sound hint: card pop, button click, toggle, notification."""

from __future__ import annotations

from typing import Any

from .core import Scene, item, put

NUDGE = [[0, 0], [0, 38], [10, 29], [17, 44], [24, 41], [17, 26], [30, 26]]


def text(s: str, color: str = "ink", size: float = 48, x: float = 0, y: float = 0, weight: int = 700, **kw: Any) -> dict[str, Any]:
    return item("text", color, text=s, size=size, weight=weight, x=x, y=y, **kw)


def pill(w: float, h: float, color: str, x: Any = 0, y: Any = 0, **kw: Any) -> dict[str, Any]:
    return item("rrect", color, w=w, h=h, r="pill", x=x, y=y, **kw)


def lift(items: list | tuple, z: float) -> list[dict[str, Any]]:
    """Give items without an explicit z a layer above the card body (painter order inside tilted groups)."""
    return [i if ("z" in i or "z" in (i.get("tracks") or {})) else {**i, "z": z} for i in items]


def card(S: Scene, id: str, t: float | None, x: float, y: float, w: float, h: float, color: str = "white", r: float = 56,
         items: list | tuple = (), sound: str | None = "pop", **kw: Any) -> dict[str, Any]:
    el = S.group(id, [item("rrect", color, w=w, h=h, r=r), *lift(items, 1)], x=x, y=y, w=w, h=h, **kw)
    return S.appear(el, t, sound=sound, x=x) if t is not None else el


def button(S: Scene, id: str, t: float, x: float, y: float, w: float, h: float, label: str, color: str = "coral", ink: str = "ink",
           press: float | None = None, size: float | None = None) -> dict[str, Any]:
    el = S.group(id, [pill(w, h, color), text(label, ink, size or h * 0.42, weight=800)], x=x, y=y, w=w, h=h)
    S.appear(el, t, x=x)
    if press is not None:
        put(el, "scale", [(press - 0.06, 1), (press, 0.92, "m3Std"), (press + 0.3, 1, "springWild")])
        S.sfx(press, "click", 0.1, -9, S.pan_of(x))
    return el


def toggle(S: Scene, x: float, y: float, on_at: float, color: str = "mint", w: float = 150) -> list[dict[str, Any]]:
    h = w * 0.56
    S.sfx(on_at, "toggle", 0.15, -12, S.pan_of(x))
    return [pill(w, h, "sand", x=x, y=y), pill(w, h, color, x=x, y=y, opacity=[(on_at - 0.001, 0), (on_at + 0.05, 1)]),
            item("circle", "white", w=h * 0.78, y=y, x=[(on_at - 0.05, x - w * 0.22), (on_at + 0.25, x + w * 0.22, "spring")])]


def phone(S: Scene, id: str, t: float | None, x: float, y: float, h: float = 980, color: str = "ink", screen: str = "cream",
          items: list | tuple = (), **kw: Any) -> dict[str, Any]:
    w = h * 0.48
    body = [item("rrect", color, w=w, h=h, r=h * 0.085, ext=h * 0.035), item("rrect", screen, w=w * 0.93, h=h * 0.955, r=h * 0.07, z=1),
            item("rrect", color, w=w * 0.3, h=h * 0.026, r="pill", y=-h * 0.44, z=2), *[{**i, **({} if "z" in (i.get("tracks") or {}) else {"z": 3})} for i in items]]
    el = S.group(id, body, x=x, y=y, w=w, h=h, persp=kw.pop("persp", 1900), **kw)
    return S.appear(el, t, x=x) if t is not None else el


def window(S: Scene, id: str, t: float | None, x: float, y: float, w: float, h: float, color: str = "white", bar: str = "sand",
           items: list | tuple = (), **kw: Any) -> dict[str, Any]:
    top = -h / 2 + 44
    chrome = [item("rrect", bar, w=w, h=88, r=36, y=top), item("rrect", bar, w=w, h=40, r=0, y=top + 22),
              *[item("circle", c, w=22, x=-w / 2 + 48 + i * 40, y=top) for i, c in enumerate(("coral", "butter", "mint"))],
              pill(w * 0.34, 40, "white", y=top)]
    return card(S, id, t, x, y, w, h, color, 36, [*lift(chrome, 1), *lift(items, 2)], **kw)


def bars(vals: list[float], t0: float, w_total: float, h_max: float, colors: list[str], x0: float = 0, y0: float = 0,
         gap: float = 0.24, stagger: float = 0.07) -> list[dict[str, Any]]:
    n = len(vals)
    bw = w_total / (n + (n - 1) * gap)
    out = []
    for i, v in enumerate(vals):
        hh, ti = h_max * v, t0 + i * stagger
        out.append(item("rrect", colors[i % len(colors)], r=bw * 0.32, w=bw, x=x0 - w_total / 2 + bw / 2 + i * bw * (1 + gap),
                        h=[(ti, 0), (ti + 0.8, hh, "spring")], y=[(ti, y0), (ti + 0.8, y0 - hh / 2, "spring")]))
    return out


def line(pts: list[list[float]], t0: float, dur: float, color: str = "coral", stroke: float = 12, ease: str = "m3Dec") -> list[dict[str, Any]]:
    return [item("path", color, pts=pts, stroke=stroke, p=[(t0, 0), (t0 + dur, 1, ease)]),
            item("circle", color, w=stroke * 3, x=pts[-1][0], y=pts[-1][1], scale=[(t0 + dur - 0.05, 0), (t0 + dur + 0.35, 1, "spring")])]


def progress_ring(color: str, d: float, t0: float, dur: float, to: float = 0.78, stroke: float = 28, x: float = 0, y: float = 0,
                  track: str = "sand") -> list[dict[str, Any]]:
    return [item("ring", track, w=d, stroke=stroke, x=x, y=y), item("ring", color, w=d, stroke=stroke, x=x, y=y, sweep=[(t0, 0.001), (t0 + dur, to, "m3Dec")], opacity=[(t0 - 0.001, 0), (t0, 1)])]


def counter(color: str, size: float, x: float, y: float, a: float, b: float, t0: float, dur: float, pre: str = "", suf: str = "", dec: int = 0) -> dict[str, Any]:
    return item("text", color, size=size, weight=800, x=x, y=y, fmt={"pre": pre, "suf": suf, "dec": dec}, num=[(t0, a), (t0 + dur, b, "m3Dec")])


def cursor(S: Scene, id: str, moves: list[tuple], clicks: list[float] = (), color: str = "ink") -> None:
    """Pointer with a click ripple. moves: (t, x, y[, ease]); clicks: times (the tip position is read from the path)."""
    from .core import k as _k
    xs = [_k(m[0], m[1], m[3] if len(m) > 3 else "m3Std") for m in moves]
    ys = [_k(m[0], m[2], m[3] if len(m) > 3 else "m3Std") for m in moves]
    for nm, col, sc in ((f"{id}_o", "white", 1.55), (id, color, 1.25)):
        el = S.add(nm, "poly", col, pts=[[a * sc, b * sc] for a, b in NUDGE])
        el["tracks"] = {"x": xs, "y": ys}
        put(el, "opacity", [(0, 0), (moves[0][0], 0), (moves[0][0] + 0.2, 1)])
    for i, tc in enumerate(clicks):
        from motionvid.timeline import track_value
        px, py = track_value(xs, tc), track_value(ys, tc)
        S.add(f"{id}_c{i}", "ring", "coral", stroke=8, x=px, y=py, w=[(tc, 20), (tc + 0.45, 150, "m3Dec")], opacity=[(tc - 0.001, 0), (tc, 1), (tc + 0.45, 0)])
        S.sfx(tc, "click", 0.1, -9, S.pan_of(px))


def notification(S: Scene, id: str, t: float, x: float, y: float, w: float, h: float, title: str, color: str = "white", dot: str = "coral", ink: str = "ink") -> dict[str, Any]:
    its = [item("circle", dot, w=h * 0.5, x=-w / 2 + h * 0.5), text(title, ink, h * 0.3, x=h * 0.22, weight=800)]
    el = card(S, id, None, x, [(t, -h), (t + 0.7, y, "spring")], w, h, color, h / 2, its)
    put(el, "opacity", [(0, 0), (t, 0), (t + 0.01, 1)])
    S.sfx(t + 0.1, "notify", 0.6, -12, S.pan_of(x))
    return el


def typed(S: Scene, s: str, t: float, cps: float, x: float, y: float, size: float = 44, color: str = "cream", weight: int = 600, pan: float = 0.0) -> dict[str, Any]:
    """Left-aligned typed line (a group child) with a tick every 2nd glyph. x is the left edge."""
    for i in range(0, len(s), 2):
        S.sfx(t + i / cps, "tick", 0.05, -22, pan, st=(i // 2) % 8 * 0.5)
    return item("text", color, text=s, size=size, weight=weight, align="left", x=x, y=y, type={"t": t, "cps": cps, "n": len(s)})
