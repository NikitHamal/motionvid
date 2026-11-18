"""Tunable parameters of the scene audio engine. The scene RSI loop mutates `scene_genome.json`."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT = {
    "rev": 6,                 # engine revision: 5 = frozen v0.4/v0.5 sound, 6 = Studio sound (v0.6+)
    "reverb6_wet": 0.10,      # rev 6: 10% wet, 0.38 s decay, HP 280 Hz, only on text_tick / hero_pluck / crystal
    "reverb6_t60": 0.38,
    "reverb6_hp": 280.0,
    "riser6_boost_db": 4.5,
    "preroll_s": 0.16,        # whoosh ramps up 160 ms before a cut so its peak lands on the cut frame
    "sub_db": -5.5,           # sub-bass thump level at full shape mass
    "sub_f0": 92.0,           # Hz, start of the pitch drop (sine sub-drop 92 Hz -> 36 Hz over 190 ms)
    "sub_f1": 36.0,           # Hz, end of the pitch drop
    "pluck_db": -14.0,        # damped low-mid wooden/marimba body (180-420 Hz)
    "tick_db": -22.0,         # damped felt/wood key-tick
    "crystal_db": -16.5,      # crisp 4 kHz micro-click + damped pop
    "suction_db": -13.5,      # tight reverse-suction sweep
    "impact_db": -6.5,
    "whoosh_db": -9.5,
    "texture_db": -22.0,      # tactile mechanical/felt slide (300->900 Hz bandpass pink noise, panned L->R)
    "stretch_db": -24.0,      # single composite low-pass brush/elastic sweep
    "shimmer_db": -28.0,      # warm harmonic pad swell during star-to-circle morph
    "bed_db": -36.0,
    "jitter_cents": 35.0,
    "vel_jitter_db": 3.0,
    "semitone_every": 3.5,
    "pan_width": 0.65,
    "reverb_wet": 0.12,       # Rule 5: 12% wet short room reverb
    "reverb_t60": 0.35,       # Rule 5: 0.35s decay, high-passed at 300 Hz
    "bell_2500_db": -4.0,     # Rule 5: -4 dB bell cut at 2.5 kHz (Q=1.0)
    "tilt_low_db": 3.0,       # Rule 5: +3 dB low shelf at 75 Hz
    "tilt_high_db": 1.5,
    "glue_ratio": 2.0,
    "target_lufs": -16.0,
    "tp_ceiling_db": -1.0,
    "room_dbfs": -54.0,
    "max_polyphony": 3,       # Rule 2: strict 3-voice polyphony cap
    "cooldown_s": 0.11,       # Rule 2: 110 ms minimum retrigger cooldown per event class
}

BOUNDS = {
    "preroll_s": (0.14, 0.22), "sub_db": (-12.0, -2.0), "pluck_db": (-20.0, -10.0), "tick_db": (-26.0, -16.0),
    "texture_db": (-30.0, -18.0), "stretch_db": (-32.0, -20.0), "shimmer_db": (-37.0, -25.0), "bed_db": (-42.0, -30.0),
    "reverb_wet": (0.08, 0.20), "crystal_db": (-22.0, -12.0), "impact_db": (-11.0, -3.0),
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
