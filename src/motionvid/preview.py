"""Self-contained HTML preview synced to audio.wav. Frames come from the shared engine (docs/engine/*.js),
inlined here, so the preview, the site, Studio and the video renderer can never drift apart."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parents[2] / "docs" / "engine"

PAGE = """<!doctype html><meta charset=utf-8><title>motionvid preview</title>
<body style="margin:0;background:#17130F;color:#F6EFE3;font:700 16px system-ui;text-align:center">
<canvas id=c width=%(w)d height=%(h)d style="width:min(96vw,1100px);margin-top:12px;border-radius:28px"></canvas><br>
<button id=b style="margin:12px;height:48px;padding:0 28px;border:0;border-radius:999px;background:#FF6A45;font:inherit">Play</button>
<label><input id=x type=checkbox> X-ray</label> <span id=s></span><audio id=a src="audio.wav"></audio>
<script>
%(engine)s
const TL=%(tl)s,CUES=%(cues)s,c=document.getElementById('c'),ctx=c.getContext('2d'),a=document.getElementById('a'),K=c.width/TL.width;
function draw(){const t=a.currentTime;drawFrame(ctx,TL,t,K);if(document.getElementById('x').checked)drawXray(ctx,TL,CUES,t,K);
document.getElementById('s').textContent=t.toFixed(2)+'s'}
(function loop(){draw();requestAnimationFrame(loop)})();
document.getElementById('b').onclick=()=>{a.paused?a.play():a.pause()};
</script>
"""


def engine_js() -> str:
    try:
        src = [(ENGINE_DIR / n).read_text() for n in ("render.js", "xray.js")]
    except FileNotFoundError as e:  # pip install without the repo checkout
        raise FileNotFoundError(f"engine sources not found at {ENGINE_DIR}; use an editable install from the repo") from e
    return "\n".join(s.replace("export ", "") for s in src)


def html(tl: dict[str, Any], cues: list[dict[str, Any]]) -> str:
    slim = [{"role": c["role"], "t": c["t"], "gain_db": c["gain_db"]} for c in cues]
    return PAGE % {"w": min(tl["width"], 1280), "h": round(min(tl["width"], 1280) * tl["height"] / tl["width"]),
                   "tl": json.dumps(tl), "cues": json.dumps(slim), "engine": engine_js()}
