import json
from pathlib import Path

import numpy as np
import pytest

from motionvid import compose as C
from motionvid.cues import compile_cues
from motionvid.timeline import TimelineError, track_value, validate

EX = json.loads((Path(__file__).resolve().parents[1] / "examples" / "launch.json").read_text())


def test_easing_endpoints():
    kfs = [{"t": 0, "v": 0}, {"t": 1, "v": 10, "ease": "outBack"}]
    assert track_value(kfs, 0) == 0 and abs(track_value(kfs, 1) - 10) < 1e-9 and track_value(kfs, 2) == 10


def test_validate_errors_are_actionable():
    with pytest.raises(TimelineError, match="duration"):
        validate({})
    with pytest.raises(TimelineError, match="ease"):
        validate({"duration": 1, "elements": [{"id": "a", "tracks": {"x": [{"t": 0, "v": 0, "ease": "bogus"}]}}]})


def test_cues_deterministic_and_sorted():
    a, b = compile_cues(EX), compile_cues(EX)
    assert a == b and [c["t"] for c in a] == sorted(c["t"] for c in a)
    assert any(c["why"] == "agent hint" and c["role"] == "riser" for c in a)


def test_abrupt_arrival_gets_whoosh_and_impact_at_stop():
    tl = {"duration": 3, "elements": [{"id": "a", "tracks": {"x": [{"t": 0.5, "v": 0}, {"t": 1.0, "v": 1500, "ease": "inCubic"}]}}]}
    roles = {c["role"]: c["t"] for c in compile_cues(tl)}
    assert abs(roles["impact"] - 1.0) < 0.02 and "whoosh" in roles


def test_slow_drift_is_silent():
    tl = {"duration": 5, "elements": [{"id": "a", "tracks": {"x": [{"t": 0, "v": 0}, {"t": 5, "v": 300}]}}]}
    assert compile_cues(tl) == []


@pytest.mark.parametrize("role", ["impact", "whoosh", "ui_pop", "riser", "click", "glitch"])
def test_anchor_lands_on_cue_within_frame(role):
    cue = dict(t=1.0, role=role, dur=0.6, gain_db=-6, pan=0.0, seed=2)
    mix, _ = C.render_cues([cue], 2.5, workers=1)
    x = np.abs(mix).max(axis=1).astype(float)
    w = 240
    env = np.sqrt(np.convolve(x**2, np.ones(w) / w, "valid"))
    t = np.argmax(env >= 0.7 * env.max()) / C.SR
    assert abs(t - 1.0) < 1 / 30


def test_every_role_renders_at_short_duration():
    from motionvid.sonic.score import EVENT_ROLES

    for role in EVENT_ROLES:
        clip, _ = C.clip_for(dict(role=role, dur=0.15, pan=0.0, seed=1))
        assert np.isfinite(clip).all() and np.abs(clip).max() > 1e-5


def test_mix_never_clips_and_is_deterministic():
    cues = compile_cues(EX)
    a, _ = C.render_cues(cues, EX["duration"], workers=1)
    b, _ = C.render_cues(cues, EX["duration"], workers=1)
    assert np.array_equal(a, b) and np.abs(a).max() <= 0.98 + 1e-6 and abs(a.mean()) < 1e-3


def test_rsi_dev_f1_not_below_ledger_floor():
    from motionvid import genome as G
    from motionvid.rsi import gt

    s = gt.score(G.load(), gt.make_set(10_000), compile_cues)
    assert s["f1"] >= 0.89 and s["recall"] >= 0.95
