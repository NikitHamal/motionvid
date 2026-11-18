"""motionvid CLI:  cues | render | video | bench | rsi."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="motionvid")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("cues", "render"):
        p = sub.add_parser(name)
        p.add_argument("timeline")
        if name == "render":
            p.add_argument("out")
            p.add_argument("--bed", default=None, help="optional ambience bed, e.g. wind, rain")
            p.add_argument("--engine", choices=("scene", "scene5", "classic"), default="scene")
    v = sub.add_parser("video", help="timeline -> audio.wav + final.mp4 (+ xray.mp4 with --xray)")
    v.add_argument("timeline")
    v.add_argument("out")
    v.add_argument("--width", type=int, default=1280)
    v.add_argument("--xray", action="store_true", help="also render a cue x-ray version")
    v.add_argument("--engine", choices=("scene", "scene5", "classic"), default="scene")
    v.add_argument("--blur", type=int, default=1, help="motion-blur sub-frames per frame (1 = off)")
    sub.add_parser("bench")
    r = sub.add_parser("rsi")
    r.add_argument("--cycles", type=int, default=1)
    r.add_argument("--scene", action="store_true", help="tune the scene audio genome against FlawBench (dev + holdout reels)")
    a = ap.parse_args(argv)

    if a.cmd in ("cues", "render"):
        from .cues import compile_cues
        from .timeline import validate

        tl = validate(json.loads(Path(a.timeline).read_text()))
        cues = compile_cues(tl)
        if a.cmd == "cues":
            print(json.dumps(cues, indent=2))
            return 0
        from .compose import SR, render_cues
        from .preview import html
        from .sonic.io import write_wav

        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        if a.engine in ("scene", "scene5"):
            from .scene import params
            from .scene.engine import render as scene_render

            audio, info = scene_render(tl, {**params.load(), "rev": 5} if a.engine == "scene5" else None)  # scene5 = frozen v0.4/v0.5 sound
            cues = info.pop("events")
            info = {k: v for k, v in info.items()}
        else:
            audio, info = render_cues(cues, tl["duration"], bed=a.bed)
        write_wav(out / "audio.wav", audio, SR)
        (out / "cues.json").write_text(json.dumps(cues, indent=2))
        (out / "preview.html").write_text(html(tl, cues))
        print(json.dumps({"out": str(out), **info}))
        if shutil.which("ffmpeg") and (out / "video.mp4").exists():
            subprocess.run(["ffmpeg", "-y", "-i", str(out / "video.mp4"), "-i", str(out / "audio.wav"), "-c:v", "copy",
                            "-c:a", "aac", "-shortest", str(out / "final.mp4")], check=False)
        return 0
    if a.cmd == "video":
        return _video(a)
    if a.cmd == "bench":
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bench.motionsync import run

        print(json.dumps(run()["headline"], indent=2))
        return 0
    if a.scene:
        from .rsi.scene_loop import cycles

        print(json.dumps(cycles(a.cycles), indent=2))
        return 0
    from .rsi.loop import cycle

    for _ in range(a.cycles):
        print(json.dumps(cycle(), indent=2))
    return 0



def _video(a: argparse.Namespace) -> int:
    """Audio via the Python compiler, frames via tools/render_video.mjs (same engine as the site)."""
    root = Path(__file__).resolve().parents[2]
    out = Path(a.out)
    rc = main(["render", a.timeline, str(out), "--engine", a.engine])
    if rc or not shutil.which("node"):
        return rc or 1
    base = ["node", str(root / "tools/render_video.mjs"), a.timeline]
    common = ["--audio", str(out / "audio.wav"), "--width", str(a.width), "--blur", str(a.blur)]
    rc = subprocess.run(base[:2] + [base[2], str(out / "final.mp4")] + common).returncode
    if a.xray and not rc:
        rc = subprocess.run(base[:2] + [base[2], str(out / "xray.mp4")] + common + ["--cues", str(out / "cues.json")]).returncode
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
