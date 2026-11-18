"""Session 8 gates: mesh kit, real media, screens, demo contracts, headless planner."""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMOS = ["atlas", "pulse", "ledgerly", "noir", "terra", "kernel"]


def _gen(name):
    subprocess.run(["python3", f"examples/demos/{name}.py"], cwd=ROOT, check=True, capture_output=True)
    return json.loads((ROOT / f"examples/demos/{name}.json").read_text())


def test_part_and_mesh_keep_parts_static():
    from motionvid.kit import Scene, mesh
    S = Scene(5)
    el = mesh.mesh(S, "m", 1.0, 960, 540, [mesh.part("rbox", "coral", w=100, h=[(0, 4), (1, 80)], rx=20, pos=[1, 2, 3])], 300, ry=[(0, 0), (4, 90)])
    assert isinstance(el["parts"], list) and el["parts"][0]["rot"][0] == 20 and el["parts"][0]["tracks"]["h"][1]["v"] == 80
    assert el["tracks"]["ry"][1]["v"] == 90


def test_screens_and_media_build():
    from motionvid.kit import Scene, screens, media
    S = Scene(10)
    for fn, args in ((screens.travel_feed, (400, 820, 1, ["beach", "palms", "shore"])), (screens.dashboard, (900, 560, 1)), (screens.activity, (400, 820, 1)), (screens.wallet, (400, 820, 1, ["fash1", "fash2"]))):
        assert len(fn(S, *args)) > 8
    assert media.footage("jog", 400, 300)["n"] > 50 and (ROOT / "docs/media/assets/beach.jpg").exists()


@pytest.mark.parametrize("name", DEMOS)
def test_demo_contract(name):
    tl = _gen(name)
    assert tl["duration"] >= 45 and tl["fps"] == 60
    raw = json.dumps(tl).lower()
    assert "shadow" not in raw and "gradient" not in raw
    kinds = {e["kind"] for e in tl["elements"]}
    assert "mesh" in kinds and ({"image", "video"} & kinds or "mesh" in kinds)
    assert any(c for c in tl["cuts"]) and tl["elements"][-1]["id"] == "outro"
    srcs = {e["src"] for e in tl["elements"] if e["kind"] == "image"} | {p for e in tl["elements"] if e["kind"] == "mesh" for pt in e["parts"] for sc in ([pt["screen"]] if isinstance(pt.get("screen"), dict) else pt.get("screen", [])) for it in sc["items"] if it["kind"] == "image" for p in [it["src"]]}
    assert all((ROOT / "docs" / s).exists() for s in srcs)
    for e in tl["elements"]:
        if e["kind"] == "text" and e.get("split") and "fmt" not in e:
            assert len(e["text"]) * 0.56 * e["size"] <= 1.0 * tl["width"], (name, e["text"])


def test_demos_differ():
    sig = {n: sorted({p["prim"] for e in _gen(n)["elements"] if e["kind"] == "mesh" for p in e["parts"]}) for n in DEMOS}
    assert len({json.dumps(v) for v in sig.values()}) >= 5


def test_headless_planner_varies_by_seed(tmp_path):
    outs = []
    for seed in (0, 1):
        o = tmp_path / f"p{seed}.json"
        subprocess.run(["node", "tools/plan_json.mjs", "Atlas, a travel app with real photos", str(o), "--seed", str(seed)], cwd=ROOT, check=True, capture_output=True)
        tl = json.loads(o.read_text())
        outs.append(sorted({p["prim"] for e in tl["elements"] if e["kind"] == "mesh" for p in e["parts"]}))
        assert tl["duration"] == 30 and any(e["kind"] == "mesh" for e in tl["elements"])
    assert outs[0] != outs[1]


def test_mesh_poster_renders(tmp_path):
    out = tmp_path / "p.png"
    subprocess.run(["node", "tools/render_video.mjs", "examples/demos/atlas.json", str(out), "--poster", "3.5", "--width", "480"], cwd=ROOT, check=True, capture_output=True)
    assert out.stat().st_size > 20000
