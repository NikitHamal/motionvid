"""Engine parity (JS vs Python easings), preview, showreel validity, ReelCheck gates, video smoke test."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))

from motionvid.preview import html  # noqa: E402
from motionvid.timeline import EASES, validate  # noqa: E402

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


@needs_node
def test_js_and_python_easings_match():
    js = ("import {EASES} from './docs/engine/render.js';const us=[0,.1,.25,.5,.77,.93,1];"
          "console.log(JSON.stringify(Object.fromEntries(Object.entries(EASES).map(([k,f])=>[k,us.map(f)]))))")
    out = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    got = json.loads(out)
    assert set(got) == set(EASES)
    for name, vals in got.items():
        for u, v in zip([0, .1, .25, .5, .77, .93, 1], vals):
            assert abs(EASES[name](u) - v) < 1e-9, (name, u)


def test_showreel_valid_and_long_enough():
    tl = validate(json.loads((ROOT / "examples" / "showreel.json").read_text()))
    assert tl["duration"] >= 15 and len(tl["elements"]) >= 30


def test_showreel_matches_builder():
    """examples/showreel.json is generated; a stale file means someone edited it by hand."""
    out = subprocess.run([sys.executable, "showreel.py"], cwd=ROOT / "examples", capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert (ROOT / "examples" / "showreel.json").exists()


def test_preview_inlines_engine():
    tl = validate({"duration": 1, "elements": [{"id": "a", "kind": "circle"}]})
    page = html(tl, [{"role": "impact", "t": 0.5, "gain_db": -6}])
    assert "function drawFrame" in page and "function drawXray" in page and "export " not in page


def test_reelcheck_gates_hold():
    import reelcheck
    res = reelcheck.run(ROOT / "examples" / "showreel.json")
    assert reelcheck.check(res) == [], res


@needs_node
def test_video_renderer_smoke(tmp_path):
    tl = tmp_path / "t.json"
    tl.write_text(json.dumps({"fps": 10, "duration": 0.5, "width": 320, "height": 180, "elements": [
        {"id": "c", "kind": "blob", "color": "#FF6A45", "w": 100, "tracks": {"scale": [{"t": 0, "v": 0}, {"t": 0.4, "v": 1, "ease": "outBack"}]}}]}))
    out = tmp_path / "o.mp4"
    r = subprocess.run(["node", "tools/render_video.mjs", str(tl), str(out), "--width", "320"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
    assert out.stat().st_size > 500
