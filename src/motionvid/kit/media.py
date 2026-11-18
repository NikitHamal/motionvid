"""Real photos and footage as layers. Photos live in docs/media/assets (scripts/get_assets.py), footage is a 15 fps jpg sequence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import item

_CRED = Path(__file__).resolve().parents[3] / "docs" / "media" / "assets" / "credits.json"


def credits() -> dict[str, Any]:
    return json.loads(_CRED.read_text()) if _CRED.exists() else {}


def photo(name: str, w: float, h: float, r: float = 0, zoom: Any = 1.0, px: Any = 0.0, py: Any = 0.0, **kw: Any) -> dict[str, Any]:
    """A photo item (cover fit). zoom/px/py may be tracks: Ken Burns, e.g. zoom=[(t, 1.0), (t + 6, 1.18, 'inOutSine')]."""
    return item("image", None, src=f"media/assets/{name}.jpg", w=w, h=h, r=r, zoom=zoom if isinstance(zoom, list) else [(0, zoom)],
                px=px if isinstance(px, list) else [(0, px)], py=py if isinstance(py, list) else [(0, py)], **kw)


def footage(name: str, w: float, h: float, t0: float = 0.0, r: float = 0, ss: float = 0.0, loop: str = "pp", zoom: Any = 1.0, **kw: Any) -> dict[str, Any]:
    """A footage item. t0 = timeline time at which the clip starts, ss = seconds to skip into the clip, loop 'pp' ping-pong | 'wrap' | 'clamp'."""
    c = credits()[name]
    return item("video", None, dir=c["dir"], n=c["n"], fps=c["fps"], t0=t0, ss=ss, loop=loop, w=w, h=h, r=r, zoom=zoom if isinstance(zoom, list) else [(0, zoom)], **kw)


def clip_seconds(name: str) -> float:
    c = credits()[name]
    return c["n"] / c["fps"]
