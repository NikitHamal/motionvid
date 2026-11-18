"""Build the evolution media in docs/media/<version>/. Old versions are frozen: v0.1 and v0.2 are never rebuilt.

    python scripts/build_media.py              # builds v0.3 and v0.4, writes docs/media/flawbench.json
    python scripts/build_media.py v0.4         # one version
Needs: numpy, scipy, node + `npm install` (ffmpeg-static, @napi-rs/canvas).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs" / "media"
FFMPEG = ROOT / "node_modules" / "ffmpeg-static" / "ffmpeg"
# version -> (timeline, blur sub-frames, poster time)
BUILDS = {"v0.3": ("examples/showreel.json", 1, 15.2), "v0.4": ("examples/reel2.json", 3, 16.0)}


def sh(*a: str) -> None:
    subprocess.run(list(a), cwd=ROOT, check=True)


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

    res = {"showreel": run(ROOT / "examples" / "showreel.json"), "reel2": run(ROOT / "examples" / "reel2.json")}
    (MEDIA / "flawbench.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    for v in sys.argv[1:] or list(BUILDS):
        build(v)
    if not sys.argv[1:]:
        flawbench()
    print("media ready:", ", ".join(sorted(str(p.relative_to(MEDIA)) for p in MEDIA.rglob("*") if p.is_file())))
