"""Tunable parameters of the motion->cue compiler. The RSI loop mutates these; humans can too."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT = {
    "seg_on_speed": 0.06,       # diag/s: motion above this is a segment
    "whoosh_min_speed": 0.55,   # diag/s peak speed to earn a whoosh
    "whoosh_min_dur": 0.12,     # s
    "impact_min_pre_speed": 0.40,  # diag/s just before an abrupt stop
    "impact_stop_window": 0.06,    # s over which speed must collapse
    "pop_min_scale_delta": 0.35,
    "pop_max_dur": 0.55,        # s
    "fade_max_dur": 0.30,       # s: faster fade-ins get a soft pop
    "min_gap": 0.045,           # s: same-role cues closer than this merge
    "gain_floor_db": -20.0,
    "gain_ceiling_db": -4.0,
    "intensity_gamma": 0.7,
    "pan_width": 0.8,
}

BOUNDS = {
    "seg_on_speed": (0.02, 0.2), "whoosh_min_speed": (0.2, 1.2), "whoosh_min_dur": (0.05, 0.4),
    "impact_min_pre_speed": (0.1, 1.0), "impact_stop_window": (0.02, 0.15),
    "pop_min_scale_delta": (0.1, 0.8), "pop_max_dur": (0.2, 1.0), "fade_max_dur": (0.1, 0.6),
    "min_gap": (0.02, 0.12), "intensity_gamma": (0.4, 1.2),
}

PATH = Path(__file__).resolve().parents[2] / "genome.json"


def load(path: Path | None = None) -> dict[str, float]:
    p = path or PATH
    g = dict(DEFAULT)
    if p.exists():
        g.update(json.loads(p.read_text()))
    return g


def save(g: dict[str, float], path: Path | None = None) -> None:
    (path or PATH).write_text(json.dumps(g, indent=2, sort_keys=True) + "\n")
