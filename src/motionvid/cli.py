"""motionvid CLI:  cues | render | bench | rsi."""

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
    sub.add_parser("bench")
    r = sub.add_parser("rsi")
    r.add_argument("--cycles", type=int, default=1)
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
        audio, info = render_cues(cues, tl["duration"], bed=a.bed)
        write_wav(out / "audio.wav", audio, SR)
        (out / "cues.json").write_text(json.dumps(cues, indent=2))
        (out / "preview.html").write_text(html(tl, cues))
        print(json.dumps({"out": str(out), **info}))
        if shutil.which("ffmpeg") and (out / "video.mp4").exists():
            subprocess.run(["ffmpeg", "-y", "-i", str(out / "video.mp4"), "-i", str(out / "audio.wav"), "-c:v", "copy",
                            "-c:a", "aac", "-shortest", str(out / "final.mp4")], check=False)
        return 0
    if a.cmd == "bench":
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from bench.motionsync import run

        print(json.dumps(run()["headline"], indent=2))
        return 0
    from .rsi.loop import cycle

    for _ in range(a.cycles):
        print(json.dumps(cycle(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
