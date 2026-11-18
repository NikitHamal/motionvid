"""Real UI screens: complete, believable app and site layouts as flat items centred on (0,0), sized (w, h).
Use them as a phone/laptop `screen`, inside `ui.window`, or flat on the canvas. Every screen animates in from t0 and adds its own sound hints.
    items = screens.travel_feed(S, 400, 820, t0, ["beach", "palms", "shore"])
"""

from __future__ import annotations

from typing import Any

from .core import Scene, item, put
from .media import photo
from .ui import counter, pill, text


def rise(it: dict[str, Any], t: float, dy: float = 36, dur: float = 0.65) -> dict[str, Any]:
    """Slide up + fade in at t (reads the item's current y)."""
    y = ((it.get("tracks") or {}).get("y") or [{"v": 0}])[0]["v"]
    it.setdefault("tracks", {})["y"] = [{"t": 0, "v": y + dy}, {"t": round(t, 4), "v": y + dy}, {"t": round(t + dur, 4), "v": y, "ease": "m3Dec"}]
    put(it, "opacity", [(0, 0), (t, 0), (t + 0.25, 1)])
    return it


def tap(S: Scene, t: float, x: float = 0, pan: float = 0.0) -> None:
    S.sfx(t, "click", 0.1, -10, pan)


def nav(w: float, h: float, t0: float, n: int = 4, active: int = 0, a: str = "ink", b: str = "sand") -> list:
    y = h / 2 - 62
    out = [item("rrect", "white", w=w * 0.9, h=96, r=48, y=y, z=2)]
    for i in range(n):
        x = (i - (n - 1) / 2) * w * 0.2
        out.append(item("circle", a if i == active else b, w=34 if i == active else 26, x=x, y=y, z=3))
    return [rise(o, t0 + 0.6, 50) for o in out]


def travel_feed(S: Scene, w: float, h: float, t0: float, photos: list[str], title: str = "Explore", price: tuple[float, float] = (240, 1290)) -> list:
    top = -h / 2
    out = [text(title, "ink", h * 0.058, x=-w * 0.36, y=top + h * 0.075, weight=800, align="left", z=2),
           item("circle", "coral", w=h * 0.05, x=w * 0.36, y=top + h * 0.075, z=2), pill(w * 0.86, h * 0.062, "sand", y=top + h * 0.165, z=1),
           item("circle", "ink", w=h * 0.022, x=-w * 0.36, y=top + h * 0.165, z=2),
           photo(photos[0], w * 0.86, h * 0.34, w * 0.1, zoom=[(t0, 1.0), (t0 + 8, 1.2, "inOutSine")], y=top + h * 0.40, z=1),
           pill(w * 0.34, h * 0.05, "white", x=-w * 0.22, y=top + h * 0.26, z=3),
           text("Maldives", "ink", h * 0.026, x=-w * 0.22, y=top + h * 0.26, weight=800, z=4)]
    for i, name in enumerate(photos[1:3]):
        out.append(photo(name, w * 0.415, h * 0.22, w * 0.08, zoom=[(t0, 1.0), (t0 + 9, 1.16, "inOutSine")], x=(-0.22 if i == 0 else 0.22) * w, y=top + h * 0.72, z=1))
    out.append(text("from", "ink", h * 0.022, x=-w * 0.36, y=top + h * 0.605, weight=600, align="left", z=2))
    c = counter("ink", h * 0.04, -w * 0.4 + h * 0.08, top + h * 0.605, price[0], price[1], t0 + 1.0, 2.0, pre="$")
    c["z"], c["align"] = 2, "left"
    out.append(c)
    S.count(c, t0 + 1.0, t0 + 3.0, price[0], price[1], ticks=6)
    return [rise(o, t0 + 0.2 + i * 0.06, 40) for i, o in enumerate(out)] + nav(w, h, t0, 4)


def product_page(S: Scene, w: float, h: float, t0: float, name: str, label: str = "Add to bag", press: float | None = None, accent: str = "coral") -> list:
    top = -h / 2
    out = [photo(name, w * 0.92, h * 0.5, w * 0.1, zoom=[(t0, 1.0), (t0 + 8, 1.15, "inOutSine")], y=top + h * 0.29, z=1),
           text("Drop 04", "ink", h * 0.05, x=-w * 0.4, y=top + h * 0.62, weight=800, align="left", z=2)]
    for i, c in enumerate(("ink", accent, "butter", "mint")):
        out.append(item("circle", c, w=h * 0.045, x=-w * 0.4 + h * 0.025 + i * h * 0.06, y=top + h * 0.7, z=2))
    out.append(item("ring", "ink", w=h * 0.06, stroke=4, x=-w * 0.4 + h * 0.025 + h * 0.06, y=top + h * 0.7, z=3, scale=[(t0 + 2.2, 0), (t0 + 2.7, 1, "spring")]))
    out += [pill(w * 0.82, h * 0.085, accent, y=top + h * 0.85, z=2), text(label, "ink", h * 0.036, y=top + h * 0.85, weight=800, z=3)]
    if press is not None:
        tap(S, press)
    return [rise(o, t0 + 0.15 + i * 0.07, 34) for i, o in enumerate(out)]


def activity(S: Scene, w: float, h: float, t0: float, accent: str = "lime", ink: str = "ink") -> list:
    top, d = -h / 2, w * 0.7
    out = [text("Today", ink, h * 0.05, x=-w * 0.38, y=top + h * 0.08, weight=800, align="left", z=2)]
    for i, (c, f, to) in enumerate(((accent, 1.0, 0.82), ("coral", 0.74, 0.64), ("butter", 0.48, 0.9))):
        d_i = d * f
        out += [item("ring", "sand", w=d_i, stroke=h * 0.03, y=top + h * 0.36, z=1),
                item("ring", c, w=d_i, stroke=h * 0.03, y=top + h * 0.36, z=2, sweep=[(t0 + 0.6 + i * 0.25, 0.001), (t0 + 2.4 + i * 0.25, to, "m3Dec")], opacity=[(t0 + 0.55, 0), (t0 + 0.6, 1)])]
    c = counter(ink, h * 0.075, 0, top + h * 0.36, 0, 12480, t0 + 0.8, 2.2)
    c["z"] = 3
    out.append(c)
    S.count(c, t0 + 0.8, t0 + 3.0, 0, 12480, ticks=8)
    vals = [0.4, 0.62, 0.5, 0.85, 0.7, 0.95, 0.58]
    for i, v in enumerate(vals):
        bh, ti = h * 0.16 * v, t0 + 1.6 + i * 0.1
        out.append(item("rrect", accent if i == 5 else "sand", w=w * 0.085, r=w * 0.03, x=(i - 3) * w * 0.125, h=[(ti, 0), (ti + 0.7, bh, "spring")], y=[(ti, top + h * 0.82), (ti + 0.7, top + h * 0.82 - bh / 2, "spring")], z=2))
    return [rise(o, t0 + 0.15, 30) if "tracks" in o and "sweep" not in o.get("tracks", {}) and "h" not in o.get("tracks", {}) else o for o in out]


def dashboard(S: Scene, w: float, h: float, t0: float, accent: str = "moss", hi: str = "butter") -> list:
    L, T = -w / 2, -h / 2
    out = [item("rrect", accent, w=w * 0.17, h=h, r=0, x=L + w * 0.085, z=1)]
    for i in range(5):
        out.append(pill(w * 0.11, h * 0.042, hi if i == 0 else "cream", x=L + w * 0.085, y=T + h * 0.18 + i * h * 0.085, z=2, opacity=[(t0, 0), (t0 + 0.2 + i * 0.1, 1)]))
    out.append(text("Revenue", "ink", h * 0.055, x=L + w * 0.22, y=T + h * 0.09, weight=800, align="left", z=2))
    for i, (lab, val, suf) in enumerate((("MRR", 84.2, "k"), ("Users", 12.4, "k"), ("Churn", 1.8, "%"))):
        cx = L + w * 0.31 + i * w * 0.245
        out.append(item("rrect", "white", w=w * 0.225, h=h * 0.2, r=h * 0.04, x=cx, y=T + h * 0.27, z=1))
        out.append(text(lab, "ink", h * 0.032, x=cx - w * 0.09, y=T + h * 0.22, weight=600, align="left", z=2))
        c = counter("ink", h * 0.07, cx, T + h * 0.31, 0, val, t0 + 0.6 + i * 0.2, 1.8, pre="$" if i == 0 else "", suf=suf, dec=1)
        c["z"] = 2
        out.append(c)
        S.count(c, t0 + 0.6 + i * 0.2, t0 + 2.4 + i * 0.2, 0, val, ticks=5)
    out.append(item("rrect", "white", w=w * 0.725, h=h * 0.4, r=h * 0.04, x=L + w * 0.5375, y=T + h * 0.68, z=1))
    vals = [0.3, 0.45, 0.4, 0.62, 0.55, 0.78, 0.7, 0.92]
    bw = w * 0.05
    for i, v in enumerate(vals):
        bh, ti = h * 0.3 * v, t0 + 1.4 + i * 0.09
        out.append(item("rrect", hi if i == 7 else accent, w=bw, r=bw * 0.3, x=L + w * 0.24 + i * w * 0.083, h=[(ti, 0), (ti + 0.7, bh, "spring")],
                        y=[(ti, T + h * 0.84), (ti + 0.7, T + h * 0.84 - bh / 2, "spring")], z=2))
    return [rise(o, t0 + 0.1 + (i % 6) * 0.05, 26) if "h" not in (o.get("tracks") or {}) and o["kind"] != "text" or o["kind"] == "text" and "num" not in (o.get("tracks") or {}) else o for i, o in enumerate(out)]


def site_home(S: Scene, w: float, h: float, t0: float, hero: str, title: str = "Move faster", accent: str = "coral", ink: str = "ink", bg: str = "cream", brand: str = "brand") -> list:
    L, T = -w / 2, -h / 2
    out = [text(brand, ink, h * 0.05, x=L + w * 0.06, y=T + h * 0.075, weight=800, align="left", z=2)]
    for i, lab in enumerate(("Product", "Pricing", "Docs")):
        out.append(text(lab, ink, h * 0.032, x=L + w * (0.46 + i * 0.1), y=T + h * 0.075, weight=600, align="left", z=2))
    out += [pill(w * 0.12, h * 0.07, accent, x=w * 0.4, y=T + h * 0.075, z=2), text("Start", ink, h * 0.032, x=w * 0.4, y=T + h * 0.075, weight=800, z=3)]
    out += [text(title, ink, h * 0.15, x=L + w * 0.06, y=T + h * 0.3, weight=800, align="left", z=2),
            pill(w * 0.17, h * 0.085, ink, x=L + w * 0.145, y=T + h * 0.47, z=2), text("Try it", bg if bg != "white" else "cream", h * 0.038, x=L + w * 0.145, y=T + h * 0.47, weight=800, z=3),
            photo(hero, w * 0.88, h * 0.33, h * 0.04, zoom=[(t0, 1.0), (t0 + 9, 1.14, "inOutSine")], y=T + h * 0.76, z=1)]
    return [rise(o, t0 + 0.1 + i * 0.05, 30) for i, o in enumerate(out)]


SYN = {"kw": "#FF6A45", "fn": "#C9F13B", "str": "#FFD54A", "mut": "#8C8374", "txt": "#F6EFE3"}


def shift(items: list, dy: float) -> list:
    """Move flat items down by dy (e.g. below a window bar)."""
    for it in items:
        for f in (it.get("tracks") or {}).get("y", []):
            f["v"] = round(f["v"] + dy, 3)
    return items


def code_editor(S: Scene, w: float, h: float, t0: float, lines: list[list[tuple[str, str]]], cps: float = 26, size: float | None = None, r: float = 0) -> list:
    """Dark editor. lines: list of token lists [(text, 'kw'|'fn'|'str'|'mut'|'txt')]. Typed with ticks; a block cursor follows the type head."""
    size = size or h * 0.05
    lh, L, T = size * 1.55, -w / 2, -h / 2
    out = [item("rrect", "#262019", w=w, h=h, r=r, z=0), item("rrect", "#3A3229", w=w, h=h * 0.1, r=0, y=T + h * 0.05, z=1),
           text("main.ts", "cream", h * 0.036, x=L + w * 0.16, y=T + h * 0.05, weight=700, z=2),
           item("circle", "coral", w=h * 0.026, x=L + w * 0.04, y=T + h * 0.05, z=2), item("circle", "butter", w=h * 0.026, x=L + w * 0.08, y=T + h * 0.05, z=2)]
    tt = t0 + 0.5
    for i, toks in enumerate(lines):
        y, x, cnt = T + h * 0.16 + i * lh, L + w * 0.1, 0
        out.append(text(str(i + 1), "#8C8374", size * 0.8, x=L + w * 0.045, y=y, weight=600, align="left", z=2))
        for s, kind in toks:
            col = SYN[kind]
            out.append(item("text", col, text=s, size=size, weight=600, align="left", x=x, y=y, z=2, type={"t": tt + cnt / cps, "cps": cps, "n": len(s)}))
            for j in range(0, len(s), 3):
                S.sfx(tt + (cnt + j) / cps, "tick", 0.05, -23, 0.0, st=(j // 3) % 8 * 0.5)
            x += len(s) * size * 0.56
            cnt += len(s)
        tt += cnt / cps + 0.25
    return out


def wallet(S: Scene, w: float, h: float, t0: float, faces: list[str], card: str = "moss", ink: str = "ink") -> list:
    """Banking app: balance counter, a card with a chip, and transactions with real photo avatars."""
    top = -h / 2
    out = [text("Balance", ink, h * 0.034, x=-w * 0.38, y=top + h * 0.07, weight=600, align="left", z=2)]
    c = counter(ink, h * 0.065, -w * 0.38 + h * 0.19, top + h * 0.135, 18200, 24861, t0 + 0.8, 2.0, pre="$")
    c["z"] = 2
    c["align"] = "center"
    out += [c, item("rrect", card, w=w * 0.86, h=h * 0.24, r=h * 0.04, y=top + h * 0.36, z=1), item("rrect", "butter", w=h * 0.07, h=h * 0.05, r=h * 0.012, x=-w * 0.3, y=top + h * 0.31, z=2),
            text("4821", "cream", h * 0.036, x=-w * 0.38, y=top + h * 0.43, weight=700, align="left", z=2), item("circle", "coral", w=h * 0.06, x=w * 0.26, y=top + h * 0.43, z=2), item("circle", "butter", w=h * 0.06, x=w * 0.33, y=top + h * 0.43, z=2)]
    S.count(c, t0 + 0.8, t0 + 2.8, 18200, 24861, ticks=6)
    for i, f in enumerate(faces[:4]):
        y = top + h * (0.58 + i * 0.1)
        out += [photo(f, h * 0.07, h * 0.07, "pill", x=-w * 0.34, y=y, z=2), pill(w * 0.34, h * 0.022, "sand", x=-w * 0.06, y=y - h * 0.012, z=2), pill(w * 0.2, h * 0.016, "sand", x=-w * 0.13, y=y + h * 0.02, z=2),
                text(["+840", "-62", "+1.2k", "-18"][i], ink, h * 0.032, x=w * 0.36, y=y, weight=800, align="right", z=2)]
    return [rise(o, t0 + 0.15 + i * 0.05, 28) if "num" not in (o.get("tracks") or {}) else o for i, o in enumerate(out)]
