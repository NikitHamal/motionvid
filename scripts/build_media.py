"""Build the evolution media in docs/media/<version>/. Old versions are frozen: v0.1, v0.2 and v0.3 are never rebuilt.

    python scripts/build_media.py              # builds v0.4 and v0.5, writes docs/media/flawbench.json
    python scripts/build_media.py v0.5         # one version
Needs: numpy, scipy, node + `npm install` (ffmpeg-static, @napi-rs/canvas).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs" / "media"
FFMPEG = ROOT / "node_modules" / "ffmpeg-static" / "ffmpeg"
# version -> (timeline, blur sub-frames, poster time)
BUILDS = {
    "v0.4": ("examples/reel2.json", 3, 15.6),
    "v0.5": ("examples/launch.json", 3, 14.8),
}


def sh(*a: str) -> None:
    subprocess.run(list(a), cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, check=True)


def build(v: str) -> None:
    tl, blur, poster = BUILDS[v]
    out, dst = ROOT / "out" / v, MEDIA / v
    dst.mkdir(parents=True, exist_ok=True)
    sh(sys.executable, "-m", "motionvid", "video", tl, str(out), "--xray", "--engine", "scene", "--blur", str(blur))
    for s, d in [("final.mp4", "reel.mp4"), ("xray.mp4", "reel-xray.mp4"), ("cues.json", "reel.cues.json")]:
        shutil.copy(out / s, dst / d)
    shutil.copy(ROOT / tl, dst / "reel.json")
    sh(str(FFMPEG), "-y", "-loglevel", "error", "-i", str(out / "audio.wav"), "-c:a", "aac", "-b:a", "128k", str(dst / "reel.m4a"))
    sh("node", "tools/render_video.mjs", tl, str(dst / "poster.png"), "--poster", str(poster), "--width", "1280")


def flawbench() -> None:
    sys.path.insert(0, str(ROOT))
    from bench.soundaudit import run

    old = json.loads((MEDIA / "flawbench.json").read_text()) if (MEDIA / "flawbench.json").exists() else {}
    # Preserve frozen v0.2 and v0.3 scene numbers if present; add v0.4 (reel2) and v0.5 (launch)
    v02_scene = old.get("v02_scene") or old.get("showreel", {}).get("scene")
    v03_scene = old.get("v03_scene") or old.get("reel2", {}).get("scene")
    res = {
        "showreel": run(ROOT / "examples" / "showreel.json"),
        "reel2": run(ROOT / "examples" / "reel2.json"),
        "launch": run(ROOT / "examples" / "launch.json"),
    }
    if v02_scene:
        res["v02_scene"] = v02_scene
    if v03_scene:
        res["v03_scene"] = v03_scene
    (MEDIA / "flawbench.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    for v in sys.argv[1:] or list(BUILDS):
        build(v)
    if not sys.argv[1:]:
        flawbench()
    print("media ready:", ", ".join(sorted(str(p.relative_to(MEDIA)) for p in MEDIA.rglob("*") if p.is_file())))
