"""The score: the typed intermediate representation between intent and audio.

Everything the planner emits, and everything the renderers consume, is a Score.
It is deliberately small, human-writable, and validatable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

EVENT_ROLES = (
    "whoosh",
    "impact",
    "ui_pop",
    "riser",
    "swell",
    "click",
    "bell",
    "sub_drop",
    "glitch",
    "noise_sweep",
    # Natural and foley roles (v0.2). Appended, never inserted: a role's index
    # seeds its noise, so the original ten keep rendering bit-identically.
    "thunder",
    "door_slam",
    "knock",
    "footsteps",
    "water_drop",
    "explosion",
    # Everyday, nature and action roles (v0.3), appended for the same reason.
    "bird_chirp",
    "crickets",
    "wave_crash",
    "wind_gust",
    "splash",
    "frog",
    "owl",
    "glass_break",
    "clock_tick",
    "phone_ring",
    "keyboard_typing",
    "mouse_click",
    "camera_shutter",
    "paper_rustle",
    "cork_pop",
    "coin_drop",
    "metal_clang",
    "wood_creak",
    "heartbeat",
    "applause",
    "pouring_water",
    "can_opening",
    "clock_alarm",
    "punch",
    "sword_clash",
    "gunshot",
    "car_horn",
    "siren",
    "engine",
    "church_bell",
    "fireworks",
)
INSTRUMENTS = ("pad", "pluck", "bass", "bell", "perc", "strings")
TEXTURES = (
    "room_cold",
    "wind",
    "city_hum",
    "vinyl",
    "drone",
    "rain",
    "fire",
    "sci_fi",
    # Scenes built from event models (v0.3, `render/ambience.py`), appended.
    "ocean",
    "stream",
    "forest",
    "night",
    "traffic",
)
AMBIENCE_TEXTURES = ("ocean", "stream", "forest", "night", "traffic")
SECTION_ROLES = ("intro", "build", "peak", "break", "outro")
SAMPLE_RATES = (16000, 22050, 24000, 32000, 44100, 48000)


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


@dataclass
class Section:
    t: float
    dur: float
    role: str = "build"
    energy: float = 0.5
    density: float = 0.5

    def __post_init__(self) -> None:
        _check(self.role in SECTION_ROLES, f"unknown section role {self.role!r}")
        _check(self.t >= 0, "section t must be >= 0")
        _check(self.dur > 0, "section dur must be > 0")
        _check(0.0 <= self.energy <= 1.0, "energy must be in [0, 1]")
        _check(0.0 <= self.density <= 1.0, "density must be in [0, 1]")


@dataclass
class Note:
    t: float
    dur: float
    midi: int
    vel: float = 0.7

    def __post_init__(self) -> None:
        _check(self.t >= 0, "note t must be >= 0")
        _check(self.dur > 0, "note dur must be > 0")
        _check(0 <= self.midi <= 127, "midi out of range")
        _check(0.0 <= self.vel <= 1.0, "vel must be in [0, 1]")


@dataclass
class MusicTrack:
    instrument: str
    notes: list[Note] = field(default_factory=list)
    gain_db: float = -12.0
    pan: float = 0.0
    articulation: str = "sustain"
    humanize: float = 0.0

    def __post_init__(self) -> None:
        _check(self.instrument in INSTRUMENTS, f"unknown instrument {self.instrument!r}")
        _check(-1.0 <= self.pan <= 1.0, "pan must be in [-1, 1]")
        _check(self.humanize >= 0, "humanize must be >= 0")


@dataclass
class Texture:
    t: float
    dur: float
    character: str = "room_cold"
    gain_db: float = -30.0
    width: float = 0.6
    bands: list[float] | None = None

    def __post_init__(self) -> None:
        _check(self.character in TEXTURES, f"unknown texture {self.character!r}")
        _check(self.t >= 0, "texture t must be >= 0")
        _check(self.dur > 0, "texture dur must be > 0")
        _check(0.0 <= self.width <= 1.0, "width must be in [0, 1]")
        if self.bands is not None:
            _check(len(self.bands) == 32, "bands must have exactly 32 values")


@dataclass
class Event:
    t: float
    role: str
    dur: float
    character: str = ""
    apex: float | None = None
    params: dict[str, float] = field(default_factory=dict)
    gain_db: float = -6.0
    pan: float = 0.0
    seed: int = 0

    def __post_init__(self) -> None:
        _check(self.role in EVENT_ROLES, f"unknown event role {self.role!r}")
        _check(self.t >= 0, "event t must be >= 0")
        _check(self.dur > 0, "event dur must be > 0")
        if self.apex is None:
            self.apex = self.t + 0.55 * self.dur
        _check(
            self.t - 1e-9 <= self.apex <= self.t + self.dur + 1e-9,
            "apex must lie inside [t, t + dur]",
        )
        _check(-1.0 <= self.pan <= 1.0, "pan must be in [-1, 1]")


@dataclass
class Score:
    duration: float
    sample_rate: int = 24000
    seed: int = 0
    tempo: float = 90.0
    meter: tuple[int, int] = (4, 4)
    key: str = "D"
    mode: str = "minor"
    mood: str = "neutral"
    target_lufs: float = -20.0
    sections: list[Section] = field(default_factory=list)
    music: list[MusicTrack] = field(default_factory=list)
    textures: list[Texture] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    def __post_init__(self) -> None:
        _check(self.duration > 0, "duration must be > 0")
        _check(self.sample_rate in SAMPLE_RATES, f"unsupported sample rate {self.sample_rate}")
        _check(self.tempo > 0, "tempo must be > 0")
        _check(self.key in tuple("ABCDEFG"), f"unknown key {self.key!r}")
        _check(self.mode in ("major", "minor"), f"unknown mode {self.mode!r}")

    # -- serialization -------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["meter"] = list(self.meter)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Score":
        d = dict(d)
        d["meter"] = tuple(d.get("meter", (4, 4)))
        d["sections"] = [Section(**s) for s in d.get("sections", [])]
        d["music"] = [
            MusicTrack(
                instrument=t["instrument"],
                notes=[Note(**n) for n in t.get("notes", [])],
                gain_db=t.get("gain_db", -12.0),
                pan=t.get("pan", 0.0),
                articulation=t.get("articulation", "sustain"),
                humanize=t.get("humanize", 0.0),
            )
            for t in d.get("music", [])
        ]
        d["textures"] = [Texture(**x) for x in d.get("textures", [])]
        d["events"] = [Event(**e) for e in d.get("events", [])]
        return cls(**d)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "Score":
        return cls.from_dict(json.loads(Path(path).read_text()))

    # -- validation ----------------------------------------------------

    def validate(self) -> None:
        end = self.duration + 1e-6
        for i, s in enumerate(self.sections):
            _check(s.t + s.dur <= end, f"section {i} out of range")
        for i, ev in enumerate(self.events):
            _check(ev.t + ev.dur <= end, f"event {i} out of range")
        for i, tx in enumerate(self.textures):
            _check(tx.t + tx.dur <= end, f"texture {i} out of range")
        for i, tr in enumerate(self.music):
            for j, n in enumerate(tr.notes):
                _check(n.t + n.dur <= end, f"note {i}.{j} out of range")

    # -- demo ----------------------------------------------------------

    @classmethod
    def demo(cls) -> "Score":
        """A 12 s cue that exercises every decoder.

        D minor, 92 BPM, pad + bass + pluck + perc, one cold room texture,
        a whoosh into an impact at 4.237 s, a pop, a riser, and a bell.
        """
        chords = [
            (0.0, (50, 53, 57)),  # Dm
            (3.0, (46, 50, 53)),  # Bb
            (6.0, (41, 45, 48)),  # F
            (9.0, (48, 52, 55)),  # C
        ]
        pad = MusicTrack(
            "pad",
            [Note(t, 3.0, m, 0.45) for t, ch in chords for m in ch],
            gain_db=-17,
        )
        bass = MusicTrack(
            "bass",
            [Note(t, 2.7, root, 0.6) for t, root in ((0.0, 38), (3.0, 34), (6.0, 41), (9.0, 36))],
            gain_db=-15,
        )
        arp: list[Note] = []
        for t, ch in chords:
            for i in range(6):
                arp.append(Note(t + i * 0.5, 0.42, ch[i % 3] + 12, 0.32))
        pluck = MusicTrack("pluck", arp, gain_db=-21, pan=0.25)
        perc = MusicTrack(
            "perc",
            [Note(t + 1.304, 0.15, 36, 0.28) for t in (0.0, 3.0, 6.0, 9.0)]
            + [Note(t + 0.652, 0.12, 42, 0.18) for t in (0.0, 3.0, 6.0, 9.0)],
            gain_db=-23,
        )

        return cls(
            duration=12.0,
            sample_rate=48000,
            seed=7,
            tempo=92.0,
            key="D",
            mode="minor",
            target_lufs=-20.0,
            sections=[
                Section(0.0, 3.0, "intro", 0.25, 0.2),
                Section(3.0, 3.0, "build", 0.55, 0.45),
                Section(6.0, 3.0, "peak", 0.9, 0.7),
                Section(9.0, 3.0, "outro", 0.35, 0.3),
            ],
            music=[pad, bass, pluck, perc],
            textures=[Texture(0.0, 12.0, "room_cold", gain_db=-30, width=0.7)],
            events=[
                Event(4.2, "whoosh", 0.8, "fast, airy", apex=4.237, gain_db=-8),
                Event(4.237, "impact", 0.7, "short, deep", gain_db=-6),
                Event(6.0, "ui_pop", 0.16, "soft, rounded", gain_db=-14),
                Event(8.0, "riser", 2.0, "dark, tense", apex=9.85, gain_db=-20),
                Event(10.5, "bell", 1.4, "glockenspiel", gain_db=-14, pan=0.2),
            ],
        )
