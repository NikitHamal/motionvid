"""Engine rev 6 (Studio sound): StudioBench gates, rev 5 stays reproducible, version registry is consistent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from bench.studio_audit import run as studio_run  # noqa: E402
from motionvid.scene import params, studio as S  # noqa: E402
from motionvid.scene.engine import render  # noqa: E402


def test_studiobench_all_gates_pass():
    res = studio_run(ROOT / "examples" / "launch.json")
    assert all(res["gates"].values()), {k: v for k, v in res["gates"].items() if not v}


def test_bed_floor_and_ceiling_are_literal_dbfs():
    _, info = render(json.loads((ROOT / "examples" / "showreel2.json").read_text()))
    assert info["bed"]["bed_idle_db"] <= -44 and info["bed"]["bed_peak_db"] <= -20 and info["bed"]["bed_lp_max_hz"] <= 780


def test_rev5_still_reproduces_and_rev6_is_default():
    tl = json.loads((ROOT / "examples" / "launch.json").read_text())
    assert params.load()["rev"] == 6
    _, i5 = render(tl, {**params.load(), "rev": 5})
    _, i6 = render(tl)
    assert i5["rev"] == 5 and i6["rev"] == 6 and i5["bed"] == {} and i6["bed"]


def test_sub_and_impact_stay_dry_and_whoosh_is_dark():
    from motionvid.scene.engine import SEND_ROLES

    assert not {"sub", "impact", "whoosh", "riser"} & set(SEND_ROLES)
    sig, anchor = S.whoosh6(0.16, 0.22, 0.8, np.random.default_rng(1))
    assert anchor == int(0.16 * 48000) and len(sig) / 48000 < 0.41


def test_versions_registry_has_no_missing_media_and_no_old_launch():
    reg = json.loads((ROOT / "docs" / "versions.json").read_text())
    ids = [v["id"] for v in reg]
    assert ids == sorted(ids, key=lambda s: [int(x) for x in s[1:].split(".")]) and ids[0] == "v0.1" and len(ids) == len(set(ids))
    for v in reg:
        for key in ("video", "xray", "poster"):
            assert (ROOT / "docs" / v[key]).exists(), (v["id"], key)
