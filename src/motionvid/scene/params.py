"""Tunable parameters of the scene audio engine. The scene RSI loop mutates `scene_genome.json`."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT = {
    "preroll_s": 0.19,        # whoosh ramps up this long before a cut so its peak lands on the cut frame
    "sub_db": -6.0,           # sub-bass thump level at full shape mass
    "sub_f0": 95.0,           # Hz, start of the pitch drop
    "sub_f1": 42.0,           # Hz, end of the pitch drop
    "pluck_db": -15.0,
    "tick_db": -21.0,
    "crystal_db": -17.0,
    "suction_db": -14.0,
    "impact_db": -7.0,
    "whoosh_db": -10.0,
    "texture_db": -24.0,      # continuous velocity foley
    "stretch_db": -26.0,      # continuous spring/stretch tone
    "shimmer_db": -31.0,      # continuous morph shimmer
    "bed_db": -36.0,
    "jitter_cents": 45.0,
    "vel_jitter_db": 2.5,
    "semitone_every": 3.5,
    "pan_width": 0.65,
    "reverb_wet": 0.16,
    "reverb_t60": 0.45,
    "tilt_low_db": 3.0,
    "tilt_high_db": 2.5,
    "glue_ratio": 2.0,
    "target_lufs": -16.0,
    "tp_ceiling_db": -1.0,
    "room_dbfs": -54.0,
}

BOUNDS = {
    "preroll_s": (0.14, 0.22), "sub_db": (-12.0, -2.0), "pluck_db": (-20.0, -10.0), "tick_db": (-26.0, -16.0),
    "texture_db": (-30.0, -18.0), "stretch_db": (-32.0, -20.0), "shimmer_db": (-37.0, -25.0), "bed_db": (-42.0, -30.0),
    "reverb_wet": (0.08, 0.25), "crystal_db": (-22.0, -12.0), "impact_db": (-11.0, -3.0),
}

PATH = Path(__file__).resolve().parents[3] / "scene_genome.json"


def load(path: Path | None = None) -> dict[str, float]:
    p = path or PATH
    g = dict(DEFAULT)
    if p.exists():
        g.update(json.loads(p.read_text()))
    return g


def save(g: dict[str, float], path: Path | None = None) -> None:
    (path or PATH).write_text(json.dumps(g, indent=2, sort_keys=True) + "\n")
