"""Fetch the real photos and footage used by the demos (Pexels licence, free for commercial use, no attribution required; credited anyway).

    python scripts/get_assets.py          # download what is missing into docs/media/assets and docs/media/footage
Photos -> docs/media/assets/<id>.jpg (<= 1200 px). Footage -> docs/media/footage/<id>/f001.jpg ... at 15 fps + meta in docs/media/assets/credits.json.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FF = str(ROOT / "node_modules" / "ffmpeg-static" / "ffmpeg")
A, F = ROOT / "docs/media/assets", ROOT / "docs/media/footage"
PX = "https://images.pexels.com/photos/{0}/pexels-photo-{0}.jpeg?auto=compress&cs=tinysrgb&w=1200"
PHOTOS = {  # id: (pexels id, credit)
    "laptop": (577210, "Lukas Blazek"), "analytics": (34069, "Negative Space"), "desk": (139387, "Negative Space"),
    "beach": (22480990, "Asad Photo Maldives"), "palms": (4389548, "Mathias Reding"), "shore": (33737360, "Patel Poojan"), "sunrise": (39014750, "Uday Veeru"),
    "sneaker": (11292946, "Broxx Asia"), "studio1": (27008321, "Jose Martin Segura Benites"), "studio2": (27008322, "Jose Martin Segura Benites"),
    "studio3": (27008318, "Jose Martin Segura Benites"), "jogger": (19783892, "Rendi iD"), "park": (10615656, "Quang Nguyen Vinh"),
}
PHOTOS.update(json.loads((A / "extra_photos.json").read_text()) if (A / "extra_photos.json").exists() else {})
VIDEOS = {  # id: (url, credit, seconds, width px)
    "citynight": ("https://videos.pexels.com/video-files/19467260/19467260-uhd_3840_2160_30fps.mp4", "Dimitar Germanov", 8, 960),
    "jog": ("https://videos.pexels.com/video-files/39443622/16797989_2160_3840_30fps.mp4", "Yuliya Duzhaya", 7, 540),
}
extra = ROOT / "docs/media/assets/extra_videos.json"
VIDEOS.update({k: tuple(v) for k, v in json.loads(extra.read_text()).items()} if extra.exists() else {})


def run(*a: str) -> None:
    subprocess.run(list(a), check=True, stderr=subprocess.DEVNULL)


def main() -> None:
    A.mkdir(parents=True, exist_ok=True)
    cred = json.loads((A / "credits.json").read_text()) if (A / "credits.json").exists() else {}
    for i, (pid, who) in PHOTOS.items():
        dst = A / f"{i}.jpg"
        if not dst.exists():
            src = A / f"{i}_src.jpg"
            urls = [pid] if isinstance(pid, str) else [PX.format(pid), PX.replace(f"pexels-photo-{{0}}.jpeg", "pexels-photo.jpg").format(pid)]
            for url in urls:  # Pexels file names differ per photo: try both patterns
                if subprocess.run(["curl", "-sfL", "-m", "90", "-o", str(src), url]).returncode == 0:
                    break
            run(FF, "-y", "-loglevel", "error", "-i", str(src), "-vf", "scale='min(1200,iw)':-2", "-q:v", "4", str(dst))
            src.unlink()
        cred[i] = {"kind": "photo", "by": who, "src": "pexels.com"}
    for i, (url, who, sec, w) in VIDEOS.items():
        d = F / i
        if not d.exists():
            d.mkdir(parents=True)
            run("curl", "-sL", "-m", "300", "-o", f"/tmp/{i}.mp4", url)
            run(FF, "-y", "-loglevel", "error", "-t", str(sec), "-i", f"/tmp/{i}.mp4", "-vf", f"fps=15,scale={w}:-2", "-q:v", "5", str(d / "f%03d.jpg"))
            Path(f"/tmp/{i}.mp4").unlink()
        n = len(list(d.glob("f*.jpg")))
        cred[i] = {"kind": "footage", "by": who, "src": "pexels.com", "fps": 15, "n": n, "dir": f"media/footage/{i}"}
    (A / "credits.json").write_text(json.dumps(cred, indent=1))
    print(len(PHOTOS), "photos,", len(VIDEOS), "clips")


if __name__ == "__main__":
    sys.exit(main())
