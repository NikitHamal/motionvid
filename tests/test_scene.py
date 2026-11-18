"""Scene audio engine: determinism, master bus limits, pre-roll, humanization, pan range, FlawBench gates."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))
sys.path.insert(0, str(ROOT))

from motionvid.scene import params, voices as V  # noqa: E402
from motionvid.scene.engine import render  # noqa: E402

TL = json.loads((ROOT / "examples" / "showreel.json").read_text())


@pytest.fixture(scope="module")
def out():
    return render(TL)


def test_deterministic_and_exact_length(out):
    a, info = out
    b, _ = render(TL)
    assert a.shape == (int(TL["duration"] * 48000), 2) and np.array_equal(a, b)


def test_master_bus_limits(out):
    a, info = out
    assert info["true_peak_dbtp"] <= -0.95 and abs(info["lufs"] - (-16.0)) <= 0.6
    assert 0.0 < info["glue_max_gr_db"] <= 3.2


def test_whoosh_preroll_lands_on_each_cut(out):
    ev = [e for e in out[1]["events"] if e["role"] == "whoosh" and "cut" in e["why"]]
    assert len(ev) == len(TL["cuts"])
    for e, c in zip(ev, TL["cuts"]):
        assert abs(e["t"] - c["t"]) < 1e-6 and 0.14 <= e["p"]["pre"] <= 0.25


def test_glyphs_are_humanized_and_skip_whitespace(out):
    ticks = [e for e in out[1]["events"] if e["role"] == "tick"]
    assert ticks and all(e["why"].split("'")[1].strip() for e in ticks)
    reel = [e for e in ticks if e["why"].startswith("reel")]
    f = np.array([e["p"]["freq"] for e in reel])
    assert f[-1] > f[0] and len(set(np.round(f, 1))) == len(f)
    g = np.array([e["gain_db"] for e in reel])
    assert g.std() > 0.3


def test_pans_stay_inside_the_stereo_window(out):
    assert all(abs(e["pan"]) <= params.DEFAULT["pan_width"] + 0.36 for e in out[1]["events"])
    assert any(abs(e["pan"]) > 0.3 for e in out[1]["events"])


@pytest.mark.parametrize("role,mk", [
    ("sub", lambda r: V.sub_thump(0.5)), ("impact", lambda r: V.impact(0.8, r)), ("pluck", lambda r: V.pluck(440, 0.4, r)),
    ("tick", lambda r: V.tick(900, r)), ("crystal", lambda r: V.crystal(r)), ("whoosh", lambda r: V.whoosh(0.19, 0.5, 0.8, r))])
def test_voice_hit_lands_within_one_frame_of_anchor(role, mk):
    sig, anchor = mk(np.random.default_rng(1))
    w = 240
    c = np.cumsum(np.concatenate([[0.0], sig ** 2]))
    env = np.sqrt((c[w:] - c[:-w]) / w)
    hit = int(np.argmax(env >= 0.7 * env.max()))
    assert abs(hit - anchor) / 48000 * 1000 <= 33.4, (role, hit, anchor)


def test_flawbench_scene_beats_classic_without_regressing():
    import soundaudit

    r = soundaudit.run(ROOT / "examples" / "showreel.json")
    assert r["scene"]["passes"] >= 8 and r["scene"]["passes"] >= r["classic"]["passes"] + 4
    assert r["scene"]["score"] >= 2.0 * r["classic"]["score"]
