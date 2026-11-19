"""Session 9 gates: mesh v3 prims, five new demos, text-fit rule, planner categories/aspects, forbidden palette."""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NEW = {"helio": (64, 1920, 1080), "summit": (70, 1920, 1080), "mosaic": (66, 1080, 1350), "tempo": (66, 1080, 1920), "quill": (68, 1920, 1080)}
V3 = {"wave", "blob", "knot", "helix", "ribbon"}


def _gen(name):
    subprocess.run(["python3", f"examples/demos/{name}.py"], cwd=ROOT, check=True, capture_output=True)
    return json.loads((ROOT / f"examples/demos/{name}.json").read_text())


@pytest.mark.parametrize("name", NEW)
def test_new_demo_contract(name):
    tl = _gen(name)
    dur, w, h = NEW[name]
    assert (tl["duration"], tl["width"], tl["height"], tl["fps"]) == (dur, w, h, 60)
    assert len(tl["cuts"]) >= 6 and len(tl["sfx"]) >= 25
    prims = {p["prim"] for e in tl["elements"] if e["kind"] == "mesh" for p in e["parts"]}
    assert prims & V3, "each new demo uses a v3 hero"


@pytest.mark.parametrize("name", NEW)
def test_text_fit_rule(name):
    tl = _gen(name)
    for e in tl["elements"]:
        if e["kind"] == "text" and e.get("text") and e.get("size"):
            wdt = len(e["text"]) * 0.5 * e["size"]
            assert wdt <= tl["width"] * 0.97, (name, e["id"], e["text"], wdt)


def test_heroes_are_not_repeated_across_new_demos():
    sets = {n: {p["prim"] for e in _gen(n)["elements"] if e["kind"] == "mesh" for p in e["parts"]} & V3 for n in NEW}
    firsts = [tuple(sorted(s)) for s in sets.values()]
    assert len(set(firsts)) >= 4


def test_mesh3_faces_node():
    code = """import {DYN} from './docs/engine/mesh3.js';
const c={wave:DYN.wave({w:900,d:700,amp:90},0).length,blob:DYN.blob({r:200,amp:.2},0).length,knot:DYN.knot({R:200,r:50}).length,helix:DYN.helix({R:100,r:20,h:300,turns:3}).length,ribbon:DYN.ribbon({w:200,len:600,R:100},0).length};
console.log(JSON.stringify(c));"""
    out = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert all(v > 50 for v in json.loads(out).values())


@pytest.mark.parametrize("prompt,cat", [("Tempo, a music app for podcasts", "music"), ("A design studio for creative portfolios", "creative"), ("AI writing assistant for blogs", "writing"), ("Summit outdoor hiking gear", "outdoor")])
def test_planner_new_categories(prompt, cat, tmp_path):
    out = tmp_path / "p.json"
    r = subprocess.run(["node", "tools/plan_json.mjs", prompt, str(out), "--long", "--aspect", "4:5"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tl = json.loads(out.read_text())
    assert cat in r and tl["duration"] == 38 and (tl["width"], tl["height"]) == (1080, 1350) and "Moment" in r


def test_no_forbidden_style_in_new_scripts():
    import re
    for n in list(NEW) + ["../launch5"]:
        src = (ROOT / f"examples/demos/{n}.py").read_text() if not n.startswith("..") else (ROOT / "examples/launch5.py").read_text()
        assert not re.search(r"shadow|emoji|LIVE|gradient\(", src, re.I)


def test_mcp_server_lists_and_plans():
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "plan_video", "arguments": {"prompt": "Tempo, a music app", "aspect": "9:16", "long": True}}}]
    out = subprocess.run(["node", "tools/mcp_server.mjs"], cwd=ROOT, input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True, timeout=20).stdout.strip().splitlines()
    names = {t["name"] for t in json.loads(out[0])["result"]["tools"]}
    assert {"skill", "plan_video", "audit_sound", "render_poster", "render_video", "list_demos"} <= names
    plan = json.loads(json.loads(out[1])["result"]["content"][0]["text"])
    assert plan["category"] == "music" and plan["duration"] == 38 and Path(plan["timeline"]).exists()
