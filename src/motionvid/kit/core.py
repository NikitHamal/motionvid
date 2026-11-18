"""motionvid.kit: the authoring kit. Every recipe writes keyframes AND the matching sound hint, so motion and sound cannot drift apart.

    from motionvid.kit import Scene, item
    S = Scene(30, "cream")
    S.headline("h", "Ship faster", t=0.4, y=500, size=220)
    S.iris(3.0, "coral")          # transition: iris closes at t=3.0, the cut hit lands there
    S.save("out.json")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PAL = {"cream": "#F6EFE3", "ink": "#17130F", "coral": "#FF6A45", "lime": "#C9F13B", "butter": "#FFD54A", "pink": "#FF9DBB",
       "mint": "#3DDBA7", "clay": "#D9573B", "moss": "#2F5D3A", "sand": "#E9DCC3", "white": "#FFFFFF", "tomato": "#E8402A", "sage": "#BFD8B8"}
NUMERIC_TRACKS = ("x", "y", "z", "scale", "opacity", "rotation", "rx", "ry", "rz")
STATIC_ALWAYS = ("pts", "items", "faces", "fmt", "type", "parts", "light", "screen")


def k(t: float, v: float, ease: str | None = None) -> dict[str, Any]:
    d: dict[str, Any] = {"t": round(float(t), 4), "v": round(float(v), 3)}
    if ease:
        d["ease"] = ease
    return d


def item(kind: str, color: str | None = None, **props: Any) -> dict[str, Any]:
    """A drawable (top-level element body or group child). Lists of (t, v[, ease]) become tracks; numbers on x/y/scale/... become constants."""
    out: dict[str, Any] = {"kind": kind}
    if color:
        out["color"] = PAL.get(color, color)
    trk: dict[str, Any] = {}
    for n, v in props.items():
        if n in STATIC_ALWAYS or not (isinstance(v, list) or (n in NUMERIC_TRACKS and isinstance(v, (int, float)))):
            out[n] = v
        else:
            trk[n] = [k(*f) for f in v] if isinstance(v, list) else [k(0, v)]
    if trk:
        out["tracks"] = trk
    return out


def put(el: dict[str, Any], name: str, frames: list[tuple], base: float | None = None) -> None:
    """Merge keyframes into a track (time-sorted). `base` seeds an initial value at t=0 when the track is new."""
    trk = el.setdefault("tracks", {})
    cur = trk.get(name) or ([k(0, base)] if base is not None else [])
    trk[name] = sorted(cur + [k(*f) for f in frames], key=lambda d: d["t"])


class Scene:
    def __init__(self, duration: float, bg: str = "cream", fps: int = 60, width: int = 1920, height: int = 1080, rev: int = 7):
        self.W, self.H = width, height
        self.tl: dict[str, Any] = {"rev": rev, "fps": fps, "duration": duration, "width": width, "height": height,
                                   "bg": PAL.get(bg, bg), "elements": [], "cuts": [], "sfx": []}
        self._cur: list[dict[str, Any]] = []

    def add(self, id: str, kind: str, color: str | None = None, **props: Any) -> dict[str, Any]:
        el = {"id": id, **item(kind, color, **props)}
        self.tl["elements"].append(el)
        self._cur.append(el)
        return el

    def place(self, id: str, it: dict[str, Any]) -> dict[str, Any]:
        """Put a prebuilt item (e.g. ui.counter) on the canvas as a top-level element."""
        el = {"id": id, **it}
        self.tl["elements"].append(el)
        self._cur.append(el)
        return el

    def group(self, id: str, items: list[dict[str, Any]], **props: Any) -> dict[str, Any]:
        return self.add(id, "group", items=items, **props)

    def sfx(self, t: float, role: str, dur: float = 0.5, gain_db: float = -12, pan: float = 0.0, **extra: Any) -> None:
        self.tl["sfx"].append({"t": round(t, 4), "role": role, "dur": dur, "gain_db": gain_db, "pan": pan, **extra})

    def pan_of(self, x: Any) -> float:
        if isinstance(x, list):  # a track: use where it ends up
            x = x[-1][1]
        return round((x / self.W - 0.5) * 1.4, 3)

    def cam(self, **tracks: list[tuple]) -> None:
        """Virtual camera: zoom / x / y / roll tracks, e.g. S.cam(zoom=[(0, 1), (4, 1.12, 'inOutSine')])."""
        self.tl["camera"] = {"tracks": {n: [k(*f) for f in fr] for n, fr in tracks.items()}}

    def appear(self, el: dict[str, Any], t: float, dur: float = 0.55, ease: str = "spring", frm: float = 0.8, sound: str | None = "pop",
               gain_db: float = -13, x: float | None = None) -> dict[str, Any]:
        put(el, "opacity", [(0, 0), (t, 0), (t + 0.001, 0.01), (t + dur * 0.3, 1, "m3StdDec")])
        put(el, "scale", [(0, frm), (t, frm), (t + dur, 1, ease)])
        if sound:
            px = x if x is not None else (el.get("tracks", {}).get("x") or [{"v": self.W / 2}])[0]["v"]
            self.sfx(t + 0.02, sound, 0.3, gain_db, self.pan_of(px))
        return el

    def vanish(self, el: dict[str, Any], t: float, dur: float = 0.3) -> None:
        put(el, "opacity", [(t, 1), (t + dur, 0, "m3Acc")], base=1)

    def _hide_scene(self, t: float) -> None:
        for el in self._cur:
            put(el, "opacity", [(t, 1), (t + 0.001, 0)], base=1)
        self._cur = []

    def headline(self, id: str, text: str, t: float, y: float, size: float = 180, color: str = "ink", mode: str = "mask",
                 dur: float = 0.9, x: float | None = None, sound: bool = True, **kw: Any) -> dict[str, Any]:
        """Kinetic headline. mode: 'mask' words rise out of a clip band | 'split' glyph spring | 'type' typed (auto ticks)."""
        x = self.W / 2 if x is None else x
        if mode == "type":
            return self.add(id, "text", color, text=text, size=size, x=x, y=y, type={"t": t, "cps": kw.pop("cps", 14), "n": len(text)}, **kw)
        el = self.add(id, "text", color, text=text, size=size, x=x, y=y, split=("mask" if mode == "mask" else True), p=[(0, 0), (t, 0), (t + dur, 1)], **kw)
        if mode == "mask" and sound:
            self.sfx(t + 0.05, "swipe", 0.25, -15, self.pan_of(x))
        return el

    def count(self, el: dict[str, Any], t0: float, t1: float, a: float, b: float, ease: str = "m3Dec", ticks: int = 8) -> None:
        put(el, "num", [(t0, a), (t1, b, ease)], base=a)
        for i in range(ticks):
            self.sfx(t0 + (t1 - t0) * (i / ticks) ** 0.8, "tick", 0.05, -21 + i * 0.4, st=i * 0.5)

    def iris(self, t_end: float, color: str, x: float | None = None, y: float | None = None, dur: float = 0.5) -> dict[str, Any]:
        """Circle grows to cover the frame; the cut hit (whoosh pre-roll + impact + sub) lands when it closes."""
        self._hide_scene(t_end)
        el = self.add(f"iris{len(self.tl['cuts'])}", "circle", color, x=self.W / 2 if x is None else x, y=self.H / 2 if y is None else y,
                      w=[(t_end - dur, 0), (t_end, 3600, "m3Acc")])
        self.tl["cuts"].append({"t": round(t_end, 4), "kind": "cut"})
        return el

    def wipe(self, t_end: float, color: str, axis: str = "x", sign: int = 1, dur: float = 0.5) -> dict[str, Any]:
        """Slab slides across the frame and stops covering it exactly at t_end."""
        self._hide_scene(t_end)
        n = len(self.tl["cuts"])
        big = 2.4 * max(self.W, self.H)
        c = self.W / 2 if axis == "x" else self.H / 2
        pos = [(t_end - dur, c - sign * big * 0.99), (t_end, c, "m3Acc")]
        kw = {"x": pos, "y": self.H / 2, "w": big, "h": self.H + 40} if axis == "x" else {"y": pos, "x": self.W / 2, "w": self.W + 40, "h": big}
        el = self.add(f"wipe{n}", "rrect", color, **kw)
        self.tl["cuts"].append({"t": round(t_end, 4), "kind": "cut"})
        return el

    def slats(self, t_end: float, color: str, n: int = 6, dur: float = 0.55) -> None:
        """Staggered bars sweep in; the last one closes at t_end."""
        self._hide_scene(t_end)
        hh = self.H / n
        for i in range(n):
            e = t_end - (n - 1 - i) * 0.05
            self.add(f"slat{len(self.tl['cuts'])}_{i}", "rrect", color, x=self.W / 2, y=hh * (i + 0.5), h=hh + 6, w=[(e - dur, 0), (e, self.W + 40, "m3Acc")])
        self.tl["cuts"].append({"t": round(t_end, 4), "kind": "cut"})

    def build(self) -> dict[str, Any]:
        return self.tl

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.tl, separators=(",", ":")))
        print(f"wrote {Path(path).name}: {len(self.tl['elements'])} elements, {len(self.tl['sfx'])} sfx hints, {len(self.tl['cuts'])} cuts")
