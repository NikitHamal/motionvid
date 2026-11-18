"""Event decoder: parametric sound effects.

No learned weights. Each role is a small physical model with a handful of
knobs. The planner chooses the role and a sparse override; the defaults below
carry the rest.
"""

from __future__ import annotations

import numpy as np

from ..score import EVENT_ROLES, Event
from .dsp import (
    align_peak,
    bandlimit,
    bandpass_timevarying,
    db_to_gain,
    env_apex,
    fade,
    modal,
    pan,
    reverb,
    saturate,
    shaped_burst,
    sweep_sine,
)
from .foley import FOLEY_PARAMS, render_foley
from .foley import ROLES as _FOLEY_ROLES
from .natural import PARAMS as NATURAL_PARAMS
from .natural import ROLES as NATURAL_ROLES

# Every role with its own stereo physical model (rendered by `render_foley`).
FOLEY_ROLES = _FOLEY_ROLES + NATURAL_ROLES

# Upper limit for every noise attack. Raw white-noise bursts sprayed energy
# to 24 kHz; above ~12 kHz they only add fizz, not snap. Impact and glitch use
# an 8th-order slope here (~48 dB down at 24 kHz; 4th order left thin
# full-band streaks on their steps and onsets).
ATTACK_HI = 12000.0

CONTINUOUS_ROLES = ("whoosh", "riser", "swell", "noise_sweep")

ROLE_PARAMS: dict[str, dict[str, float]] = {
    "whoosh": dict(f_start=180, f_peak=2400, f_end=500, body_f=90, width=0.55, reverb=0.15),
    "impact": dict(f0=70, t60=0.35, width=0.0, reverb=0.2),
    "ui_pop": dict(f0=880, t60=0.07, width=0.0, reverb=0.08),
    "riser": dict(f_start=220, f_peak=6500, body_f=110, width=0.45, reverb=0.25),
    "swell": dict(f_start=350, f_peak=3200, width=0.6, reverb=0.35),
    "click": dict(f0=1900, t60=0.03, width=0.0, reverb=0.05),
    "bell": dict(f0=880, t60=1.2, width=0.3, reverb=0.3),
    "sub_drop": dict(f0=110, f_end=35, t60=0.8, width=0.0, reverb=0.1),
    "glitch": dict(f0=600, t60=0.2, width=0.5, reverb=0.05),
    "noise_sweep": dict(f_start=300, f_peak=4200, f_end=800, width=0.5, reverb=0.25),
    # natural and foley roles: rendered by `foley.py`
    **FOLEY_PARAMS,
    # everyday, nature and action roles (v0.3): rendered by `natural.py`
    **NATURAL_PARAMS,
}


def _whoosh(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    apex_frac = float(np.clip((ev.apex - ev.t) / ev.dur, 0.05, 0.95))
    env = env_apex(n, sr, apex_frac * ev.dur, rise_power=1.5, fall_power=3.0)
    noise = rng.standard_normal(n)
    ctrl = np.array([0.0, apex_frac, 1.0])
    centers = np.interp(
        np.linspace(0.0, 1.0, 64),
        ctrl,
        np.array([p["f_start"], p["f_peak"], p["f_end"]], dtype=float),
    )
    widths = np.maximum(centers * 0.55, 120.0)
    air = bandpass_timevarying(noise, centers, widths, sr) * env
    body = sweep_sine(p["body_f"], p["body_f"] * 0.55, ev.dur, sr) * env * 0.3
    return air + body


def _impact(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    t60 = float(p["t60"])
    body = modal(
        p["f0"],
        ev.dur,
        sr,
        ratios=(1.0, 2.32, 3.71, 5.13),
        t60=(t60, t60 * 0.6, t60 * 0.35, t60 * 0.2),
        gains=(1.0, 0.7, 0.4, 0.25),
    )
    click = shaped_burst(rng, n, int(0.005 * sr), 10.0, sr, lo=1000.0, hi=9000.0)
    sub = sweep_sine(p["f0"] * 0.7, p["f0"] * 0.35, ev.dur, sr) * np.exp(-5.0 * np.arange(n) / n)
    # tanh regenerates harmonics of the snap, so band-limit after it as well.
    return bandlimit(saturate(body + 0.6 * click + 0.7 * sub, 1.8), sr, None, ATTACK_HI, order=8)


def _ui_pop(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    t60 = float(p["t60"])
    body = modal(p["f0"], ev.dur, sr, ratios=(1.0, 2.7), t60=(t60, t60 * 0.4), gains=(1.0, 0.3))
    click = shaped_burst(rng, n, int(0.002 * sr), 8.0, sr, lo=1500.0, hi=10000.0)
    return body + 0.25 * click


def _riser(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    apex_s = float(np.clip(ev.apex - ev.t, 0.05 * ev.dur, 0.99 * ev.dur))
    env = env_apex(n, sr, apex_s, rise_power=2.0, fall_power=8.0)
    noise = rng.standard_normal(n)
    centers = np.interp(
        np.linspace(0.0, 1.0, 64),
        np.array([0.0, 1.0]),
        np.array([p["f_start"], p["f_peak"]], dtype=float),
    )
    widths = np.maximum(centers * 0.45, 150.0)
    air = bandpass_timevarying(noise, centers, widths, sr)
    tone = sweep_sine(p["body_f"], p["body_f"] * 8.0, ev.dur, sr, curve=2.0) * 0.15
    return (air + tone) * env


def _swell(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    apex_s = float(np.clip(ev.apex - ev.t, 0.05 * ev.dur, 0.99 * ev.dur))
    env = env_apex(n, sr, apex_s, rise_power=3.0, fall_power=6.0)
    noise = rng.standard_normal(n)
    centers = np.full(64, float(p["f_peak"]))
    widths = np.full(64, max(float(p["f_peak"]) * 0.8, 200.0))
    air = bandpass_timevarying(noise, centers, widths, sr)
    shimmer = modal(p["f_peak"] * 0.5, ev.dur, sr, ratios=(1.0, 2.01, 3.0), t60=(0.6, 0.4, 0.25))
    return (air * 0.8 + shimmer * 0.15) * env


def _click(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    out = shaped_burst(rng, n, int(0.02 * sr), 14.0, sr, lo=2000.0, hi=ATTACK_HI)
    out += modal(p["f0"], ev.dur, sr, ratios=(1.0, 1.9), t60=(p["t60"], p["t60"] * 0.5)) * 0.4
    return out


def _bell(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    t60 = float(p["t60"])
    return modal(
        p["f0"],
        ev.dur,
        sr,
        ratios=(1.0, 2.76, 5.40, 8.93),
        t60=(t60, t60 * 0.6, t60 * 0.4, t60 * 0.25),
        gains=(1.0, 0.6, 0.35, 0.2),
    )


def _sub_drop(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    env = np.exp(-3.0 * np.arange(n) / n)
    return sweep_sine(p["f0"], p["f_end"], ev.dur, sr, curve=0.6) * env


def _glitch(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    steps = int(rng.integers(3, 9))
    hold = max(1, n // steps)
    idx = np.minimum(np.arange(n) // hold, steps)
    vals = rng.standard_normal(steps + 1)[idx]
    sig = vals * np.exp(-3.0 * np.arange(n) / n)
    sig = np.round(sig * 8.0) / 8.0
    # The steps are the character; their edges should not reach Nyquist.
    return bandlimit(saturate(sig, 1.2), sr, None, ATTACK_HI, order=8)


def _noise_sweep(ev: Event, sr: int, rng: np.random.Generator, p: dict) -> np.ndarray:
    n = max(1, int(ev.dur * sr))
    env = env_apex(n, sr, 0.5 * ev.dur, rise_power=1.2, fall_power=2.0)
    noise = rng.standard_normal(n)
    centers = np.interp(
        np.linspace(0.0, 1.0, 64),
        np.array([0.0, 0.5, 1.0]),
        np.array([p["f_start"], p["f_peak"], p["f_end"]], dtype=float),
    )
    widths = np.maximum(centers * 0.6, 150.0)
    return bandpass_timevarying(noise, centers, widths, sr) * env


def _edges(mono: np.ndarray, sr: int, role: str) -> np.ndarray:
    """Fade the clip's edges so it starts and ends at zero without a step.

    Transient roles keep the short linear 2 ms / 10 ms fades: their attack is
    the sound. Continuous roles are noise under a slow envelope, so they get
    raised-cosine fades: 5 ms in, and out over 6% of the clip (20-80 ms).
    A noise_sweep ends at ~13% of its peak, and a 10 ms linear ramp from
    there was a small high-frequency tick at the dry end.
    """
    if role not in CONTINUOUS_ROLES:
        return fade(mono, sr, 0.002, 0.01)
    x = mono.copy()
    n = len(x)
    a = min(n, max(2, int(0.005 * sr)))
    b = min(n, max(2, int(float(np.clip(0.06 * n / sr, 0.02, 0.08)) * sr)))
    x[:a] *= 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, a))
    x[-b:] *= 0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, b))
    return x


def _wet(mono: np.ndarray, sr: int, p: dict, wet: float, seed: int, tail: bool) -> np.ndarray:
    out = reverb(mono, sr, decay=float(p.get("reverb_decay", 0.5)), wet=wet, seed=seed, tail=tail)
    if not tail:
        # The wet signal is still ringing where the dry clip ends; without a
        # fade the cut is a small step, an audible tick on quiet cues.
        b = min(len(out), max(1, int(0.01 * sr)))
        out[-b:] *= np.linspace(1.0, 0.0, b)
    return out


_RENDERERS = {
    "whoosh": _whoosh,
    "impact": _impact,
    "ui_pop": _ui_pop,
    "riser": _riser,
    "swell": _swell,
    "click": _click,
    "bell": _bell,
    "sub_drop": _sub_drop,
    "glitch": _glitch,
    "noise_sweep": _noise_sweep,
}


def render_event(ev: Event, sr: int, seed: int = 0, tail: bool = False) -> np.ndarray:
    """Render one event to stereo, shape (n, 2).

    By default the clip is exactly `ev.dur` long and the reverb is faded out
    with it. With `tail=True` the reverb rings out past `ev.dur` (the mixer
    uses this), so an event never ends on a cut-off tail.
    """
    idx = EVENT_ROLES.index(ev.role)
    rng = np.random.default_rng((seed * 1_000_003 + idx * 7_919 + int(ev.t * 1000)) & 0xFFFFFFFF)
    p = {**ROLE_PARAMS[ev.role], **ev.params}
    if ev.role in FOLEY_ROLES:
        # Stereo physical models with their own edges, reverb and panning.
        return render_foley(ev, sr, rng, p, seed, tail)
    fn = _RENDERERS[ev.role]

    # A one-sided transient (glitch steps, modal impact) carries DC. Remove it
    # before the fade, so the fade windows the offset to zero at the edges.
    # Continuous roles are aligned to their apex first and faded after: the
    # alignment can shift the clip up to 50 ms left, which used to discard the
    # fade-in and start the clip mid-waveform (a broadband click on whoosh).
    mono = fn(ev, sr, rng, p)
    mono = mono - mono.mean()
    if ev.role in CONTINUOUS_ROLES:
        mono = align_peak(mono, sr, ev.apex - ev.t)
    mono = _edges(mono, sr, ev.role)
    wet = float(p.get("reverb", 0.0))
    if wet > 0:
        mono = _wet(mono, sr, p, wet, int(rng.integers(1 << 31)), tail)

    width = float(np.clip(p.get("width", 0.0), 0.0, 1.0))
    if width > 0:
        rng2 = np.random.default_rng(int(rng.integers(1 << 31)))
        mono2 = fn(ev, sr, rng2, p)
        mono2 = mono2 - mono2.mean()
        mono2 = _edges(mono2, sr, ev.role)
        if wet > 0:
            mono2 = _wet(mono2, sr, p, wet, int(rng2.integers(1 << 31)), tail)
        mid = 0.5 * (mono + mono2)
        side = 0.5 * (mono - mono2) * width
        left, right = mid + side, mid - side
    else:
        left, right = pan(mono, ev.pan)

    return np.stack([left, right], axis=1) * db_to_gain(ev.gain_db)
