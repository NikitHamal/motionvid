"""Build the demo reels (docs/media/demos/<id>/) and write docs/demos.json. Demos are separate from the v0.x evolution.

    python scripts/build_demos.py lumen orbit      # build some
    python scripts/build_demos.py                  # all
    python scripts/build_demos.py sheet lumen      # contact sheet out/<id>_sheet.png (QA: 8 frames, no audio)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = ROOT / "node_modules" / "ffmpeg-static" / "ffmpeg"
MEDIA = ROOT / "docs" / "media" / "demos"
# id: (title, brief, width, poster time, blur)
DEMOS = {
    "lumen": ("Lumen", "Fintech app launch", 1280, 24.0, 3),
    "orbit": ("Orbit", "SaaS analytics dashboard", 1280, 10.0, 3),
    "forge": ("Forge", "Developer tool", 1280, 9.5, 3),
    "bloom": ("Bloom", "Wellness app, vertical 9:16", 720, 17.0, 3),
    "cadence": ("Cadence", "3D hardware reveal", 1280, 11.0, 3),
    "parcel": ("Parcel", "Delivery service", 1280, 9.0, 3),
    "atlas": ("Atlas", "Travel app, real photos, photo cube and globe", 1280, 3.6, 3),
    "pulse": ("Pulse", "Fitness wearable, real footage, vertical 9:16", 720, 12.0, 3),
    "ledgerly": ("Ledgerly", "Finance SaaS, 3D laptop and coin stack", 1280, 12.0, 2),
    "noir": ("Noir", "Fashion drop, photo carousel, square 1:1", 1080, 20.0, 2),
    "terra": ("Terra", "Urban climate, city footage, extruded 3D", 1280, 12.0, 2),
    "kernel": ("Kernel", "Developer infrastructure, code editor and racks", 1280, 12.0, 2),
    "helio": ("Helio", "Solar energy, morphing sun, wave field, city footage", 1280, 13.0, 2),
    "summit": ("Summit", "Outdoor gear, terrain flyover, real footage", 1280, 6.0, 2),
    "mosaic": ("Mosaic", "Design suite, morphing blob, ribbon, portrait 4:5", 1080, 15.0, 2),
    "tempo": ("Tempo", "Music app, torus knot, equalizer, vertical 9:16", 720, 14.0, 2),
    "quill": ("Quill", "AI writing SaaS, dark theme, helix, typed editor", 1280, 35.0, 2),
}


def sh(*a: str) -> None:
    subprocess.run(list(a), cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, check=True)


def gen(i: str) -> str:
    sh(sys.executable, f"examples/demos/{i}.py")
    return f"examples/demos/{i}.json"


def sheet(i: str) -> None:
    tl = gen(i)
    d = json.loads((ROOT / tl).read_text())["duration"]
    ts = [d * (j + 0.5) / 8 for j in range(8)]
    for j, t in enumerate(ts):
        sh("node", "tools/render_video.mjs", tl, f"out/{i}_s{j}.png", "--poster", f"{t:.2f}", "--width", "640")
    sh(str(FFMPEG), "-y", "-loglevel", "error", "-framerate", "1", "-i", f"out/{i}_s%d.png", "-vf", "tile=4x2:padding=6:color=gray", "-frames:v", "1", f"out/{i}_sheet.png")


def build(i: str) -> None:
    title, brief, width, poster, blur = DEMOS[i]
    tl, out, dst = gen(i), ROOT / "out" / i, MEDIA / i
    dst.mkdir(parents=True, exist_ok=True)
    sh(sys.executable, "-m", "motionvid", "video", tl, str(out), "--width", str(width), "--blur", str(blur))
    shutil.copy(out / "final.mp4", dst / "reel.mp4")
    shutil.copy(out / "cues.json", dst / "reel.cues.json")
    shutil.copy(ROOT / tl, dst / "reel.json")
    sh(str(FFMPEG), "-y", "-loglevel", "error", "-i", str(out / "audio.wav"), "-c:a", "aac", "-b:a", "128k", str(dst / "reel.m4a"))
    sh("node", "tools/render_video.mjs", tl, str(dst / "poster.png"), "--poster", str(poster), "--width", str(width))


def registry() -> None:
    rows = []
    for i, (title, brief, *_rest) in DEMOS.items():
        p = MEDIA / i
        if not (p / "reel.mp4").exists():
            continue
        tl = json.loads((p / "reel.json").read_text())
        rows.append({"id": i, "title": title, "brief": brief, "duration": tl["duration"], "fps": tl["fps"], "aspect": [tl["width"], tl["height"]],
                     "sfx": len(tl["sfx"]), "elements": len(tl["elements"]), "video": f"media/demos/{i}/reel.mp4", "poster": f"media/demos/{i}/poster.png",
                     "player": {"timeline": f"media/demos/{i}/reel.json", "cues": f"media/demos/{i}/reel.cues.json", "audio": f"media/demos/{i}/reel.m4a"}})
    (ROOT / "docs" / "demos.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "sheet":
        for i in args[1:]:
            sheet(i)
    else:
        for i in args or list(DEMOS):
            build(i)
        registry()
