"""Kit, rev 7 UI foley, 3D engine kinds, demos registry and the design rules on the new files."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from motionvid.kit import Scene, item, ui, three  # noqa: E402
from motionvid.scene.engine import render  # noqa: E402
from motionvid.timeline import validate  # noqa: E402


def _scene():
    S = Scene(8, "cream", fps=30)
    S.headline("h", "Hello", 0.3, 300, 200)
    ui.phone(S, "p", 0.5, 500, 540, 700, items=[ui.text("x"), *ui.bars([.5, .8], 1.0, 200, 200, ["coral"])])
    three.box(S, "b", 1.0, 1300, 540, 240)
    ui.button(S, "btn", 1.5, 1300, 900, 400, 120, "Go", press=3.0)
    ui.cursor(S, "c", [(2.0, 1500, 950), (3.0, 1320, 910)], [3.0])
    S.iris(7, "ink")
    return S


def test_kit_scene_validates_and_has_sound_for_every_ui_action():
    tl = validate(_scene().build())
    roles = {s["role"] for s in tl["sfx"]}
    assert {"pop", "click", "swipe"} <= roles and tl["rev"] == 7 and tl["cuts"]


def test_rev7_ui_roles_render_and_rev6_stays_default():
    tl = {"rev": 7, "fps": 30, "duration": 4, "width": 1920, "height": 1080, "elements": [], "cuts": [],
          "sfx": [{"t": 0.3 + i * 0.5, "role": r} for i, r in enumerate(["click", "pop", "chime", "toggle", "notify", "swipe"])]}
    audio, info = render(tl)
    assert info["by_role"] == {r: 1 for r in ["click", "pop", "chime", "toggle", "notify", "swipe"]} and abs(audio).max() > 0.05


def test_scene_hides_previous_scene_at_the_cut():
    S = Scene(6, "cream", fps=30)
    el = S.add("a", "circle", "coral", w=100)
    S.iris(3, "ink")
    ops = el["tracks"]["opacity"]
    assert ops[-1]["v"] == 0 and ops[-1]["t"] > 3


@pytest.mark.skipif(subprocess.run(["which", "node"], capture_output=True).returncode != 0, reason="node missing")
def test_engine_draws_every_kind_without_throwing():
    js = ("import {createCanvas} from '@napi-rs/canvas';import {drawFrame} from './docs/engine/render.js';"
          "const tl=JSON.parse(process.argv[1]);const c=createCanvas(480,270);for(const t of [0.1,1,2.5,4,6.9])drawFrame(c.getContext('2d'),tl,t,0.25);console.log('ok')")
    out = subprocess.run(["node", "--input-type=module", "-e", js, json.dumps(_scene().build())], cwd=ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "ok", out.stderr[-400:]


def test_demos_registry_matches_files_and_are_long():
    rows = json.loads((ROOT / "docs" / "demos.json").read_text())
    assert len(rows) >= 5
    for r in rows:
        assert r["duration"] >= 30 and (ROOT / "docs" / r["video"]).exists() and (ROOT / "docs" / r["poster"]).exists()


def test_new_files_follow_design_rules():
    files = [*ROOT.glob("src/motionvid/kit/*.py"), *ROOT.glob("examples/demos/*.py"), *ROOT.glob("docs/create/*"), *ROOT.glob("docs/engine/*.js")]
    emoji = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    for f in files:
        s = f.read_text()
        assert not emoji.search(s), f
        assert "box-shadow:" not in s.replace("box-shadow: none", "") and "text-shadow:" not in s.replace("text-shadow: none", ""), f
        assert not re.search(r"(?i)\blive\b\s*(badge|pill)", s), f
