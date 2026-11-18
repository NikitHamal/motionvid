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

    for name in ("showreel.json", "reel2.json"):
        r = soundaudit.run(ROOT / "examples" / name)
        assert r["scene"]["passes"] == 9 and r["scene"]["passes"] >= r["classic"]["passes"] + 6
        assert r["scene"]["score"] >= 2.2 * r["classic"]["score"]


def test_agency_dsp_rules_polyphony_and_timbre(out):
    _, info = out
    plucks = [e for e in info["events"] if e["role"] == "pluck"]
    assert plucks and all(180.0 <= e["p"]["freq"] <= 420.0 and not e["p"]["bell"] for e in plucks)
    # Check 3-voice burst polyphony cap on non-tick discrete shape pops
    pt = sorted(e["t"] for e in plucks if "hero" not in e["why"] and "motif" not in e["why"])
    for i in range(len(pt) - 3):
        assert pt[i + 3] - pt[i] >= 0.3, f"More than 3 shape pops in 300ms at {pt[i]}"
    # Verify whoosh contains locked sub-bass weight layer (< 100 Hz)
    w_sig, _ = V.whoosh(0.16, 0.18, 0.8, np.random.default_rng(7))
    sp = np.abs(np.fft.rfft(w_sig))
    freqs = np.fft.rfftfreq(len(w_sig), 1 / 48000)
    sub_e = float((sp[(freqs >= 35) & (freqs <= 100)] ** 2).mean())
    mid_e = float((sp[(freqs >= 1500) & (freqs <= 3500)] ** 2).mean())
    assert sub_e > mid_e, "Whoosh must have locked sub-bass weight layer stronger than high-mid hiss"


def test_launch_v05_five_root_bugs_fixed():
    from motionvid.scene.telemetry import build, motion_curves

    from motionvid.scene import params

    l_tl = json.loads((ROOT / "examples" / "launch.json").read_text())
    audio, info = render(l_tl, {**params.load(), "rev": 5})  # the v0.4/v0.5 sound spec stays reproducible as rev 5
    evs = info["events"]
    # 1. Suction anticipation sweep: starts 0.25s before crystal (5.75s -> 6.00s and 12.47s -> 12.72s)
    suctions = [e for e in evs if e["role"] == "suction"]
    crystals = [e for e in evs if e["role"] == "crystal"]
    assert [e["t"] for e in suctions] == [5.75, 12.47]
    assert [e["t"] for e in crystals] == [6.0, 12.72]
    for s_ev, c_ev in zip(suctions, crystals):
        assert round(s_ev["t"] + s_ev["p"]["dur"], 2) == c_ev["t"]
    # 2. Sub + impact locked on every cut with 0 ms offset; whoosh pre=0.16s, post=0.18s
    cuts = [c["t"] for c in l_tl["cuts"]]
    assert cuts == [3.2, 6.6, 10.2, 13.4]
    for tc in cuts:
        at_cut = {e["role"]: e for e in evs if abs(e["t"] - tc) < 1e-4}
        assert {"sub", "impact", "whoosh"} <= set(at_cut)
        assert at_cut["whoosh"]["p"]["pre"] == 0.16 and at_cut["whoosh"]["p"]["post"] == 0.18
    # No early sub pre-bloom 130 ms before cuts
    subs = [e["t"] for e in evs if e["role"] == "sub"]
    assert all(all(abs(st - (tc - 0.13)) > 0.05 for tc in cuts) for st in subs)
    # 3. Pitched pluck strictly <= 1 hero arrival per scene (4 hero shape arrivals across 5 scenes), zero text plucks
    plucks = [e for e in evs if e["role"] == "pluck"]
    assert len(plucks) == 4 and all(not any(k in e["why"] for k in ("hook", "tel_title", "stat", "brand", "cta")) for e in plucks)
    # 4. Continuous motion bed active across 3.5-5.8s, 8.1-9.4s, and 10.6-12.6s
    tels = build(l_tl)
    me, px = motion_curves(tels)
    assert me.min() >= 0.0 and me.max() <= 1.0 and px.min() >= -1.0 and px.max() <= 1.0
    for a, b in ((3.5, 5.8), (8.1, 9.4), (10.6, 12.6)):
        seg = audio[int(a * 48000):int(b * 48000)]
        rms_db = 10 * np.log10((seg ** 2).mean() + 1e-20)
        assert rms_db > -32.0, f"Dead air in {a}..{b}s: {rms_db:.1f} dBFS"
    # 5. Climax riser at 12.85s -> 13.40s, zero discrete triggers after 15.40s
    risers = [e for e in evs if e["role"] == "riser"]
    assert len(risers) == 1 and risers[0]["t"] == 12.85 and risers[0]["p"]["dur"] == 0.55
    assert max(e["t"] for e in evs) <= 15.40
