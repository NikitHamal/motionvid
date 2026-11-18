"""Regenerate every media artifact used by the site (docs/) and Studio (src/) from the one source of truth.

    python scripts/build_media.py        # showreel.py -> audio, cues, mp4, x-ray mp4, m4a, launch mp4, poster
Needs: numpy, node + `npm install` (ffmpeg-static, @napi-rs/canvas).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT, MEDIA = ROOT / "out", ROOT / "docs" / "media"
FFMPEG = ROOT / "node_modules" / "ffmpeg-static" / "ffmpeg"


def sh(*a: str, cwd: Path = ROOT) -> None:
    subprocess.run(list(a), cwd=cwd, check=True)


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    sh(sys.executable, "showreel.py", cwd=ROOT / "examples")
    sh(sys.executable, "-m", "motionvid", "video", "examples/showreel.json", "out/showreel", "--xray")
    sh(sys.executable, "-m", "motionvid", "video", "examples/launch.json", "out/launch")
    for src, dst in [("showreel/final.mp4", "showreel.mp4"), ("showreel/xray.mp4", "showreel-xray.mp4"),
                     ("launch/final.mp4", "launch.mp4"), ("showreel/cues.json", "showreel.cues.json")]:
        shutil.copy(OUT / src, MEDIA / dst)
    shutil.copy(ROOT / "examples" / "showreel.json", MEDIA / "showreel.json")
    sh(str(FFMPEG), "-y", "-loglevel", "error", "-i", str(OUT / "showreel/audio.wav"), "-c:a", "aac", "-b:a", "96k", str(MEDIA / "showreel.m4a"))
    sh("node", "tools/render_video.mjs", "examples/showreel.json", str(MEDIA / "poster.png"), "--poster", "15.2", "--width", "1280")
    print("media ready:", ", ".join(sorted(p.name for p in MEDIA.iterdir())))


if __name__ == "__main__":
    main()
