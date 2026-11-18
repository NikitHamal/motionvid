"""Scene audio engine: timeline -> telemetry -> events + continuous layers + bed -> mastering bus -> stereo 48 kHz."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
from scipy.signal import butter, sosfilt

from ..timeline import validate
from . import foley, master, params, studio as S, studio_bed, ui_foley, voices as V
from .score import build_events
from .telemetry import build

SR = V.SR
CHORDS = [(110.0, 164.8, 220.0), (87.3, 130.8, 174.6), (65.4, 98.0, 130.8), (98.0, 146.8, 196.0)]  # Am F C G


SEND_ROLES = ("tick", "pluck", "crystal", "air", "chime", "notify", "pop")  # rev 6: the only roles that feed the room reverb


def _voice(e: dict[str, Any], rev: int = 5):
    rng, p, r = np.random.default_rng(e["seed"]), e["p"], e["role"]
    if r in ui_foley.UI_ROLES:
        return ui_foley.voice(r, p, rng)
    if rev >= 6:
        if r == "whoosh":
            return S.whoosh6(p["pre"], p["post"], p["s"], rng)
        if r == "tick":
            return S.text_tick6(float(p.get("st", 0.0)), rng)
        if r == "pluck":
            return S.hero_pluck6(p["freq"], rng)
        if r == "air":
            return S.air6(rng)
        if r == "riser":
            return S.riser6(p["dur"], rng)
        if r == "impact" and "settle" in p:
            sig, a = V.impact(p["s"], rng)
            return S.settle(sig, int(p["settle"])), a
    if r == "impact":
        return V.impact(p["s"], rng)
    if r == "whoosh":
        return V.whoosh(p["pre"], p["post"], p["s"], rng)
    if r == "sub":
        return V.sub_thump(0.35 + 0.5 * p["s"], p["f0"], p["f1"], 0.11)
    if r == "pluck":
        return V.pluck(p["freq"], p["dur"], rng, bell=p["bell"])
    if r == "tick":
        return V.tick(p["freq"], rng)
    if r == "crystal":
        return V.crystal(rng)
    if r == "suction":
        return V.suction(p["dur"], rng)
    if r == "riser":
        return V.riser(p["dur"], rng)
    raise ValueError(f"unknown role {r!r}")


def _bed(buf: np.ndarray, tl: dict[str, Any], G) -> None:
    dur = tl["duration"]
    edges = [0.0] + sorted(float(c["t"]) for c in tl["cuts"]) + [dur]
    for i, (a, b) in enumerate(zip(edges, edges[1:])):
        s, e = max(0.0, a - G["preroll_s"]), min(dur, b - G["preroll_s"] + 0.35) if b < dur else dur
        if e - s < 0.3:
            continue
        sig, _ = V.pad(CHORDS[i % 4], e - s, np.random.default_rng(100 + i))
        f = min(len(sig) // 2, int(0.3 * SR))
        sig[:f] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, f))
        sig[-f:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f))
        k = int(s * SR)
        m = min(len(buf) - k, len(sig))
        buf[k:k + m] += (sig[:m] * 10 ** (G["bed_db"] / 20))[:, None]


def render(tl: dict[str, Any], G: dict[str, float] | None = None) -> tuple[np.ndarray, dict[str, Any]]:
    """Returns (audio float32 (n, 2), info). `info['events']` is the x-ray cue list."""
    tl, G = validate(tl), G or params.load()
    if tl.get("rev"):  # a timeline can opt into a newer engine revision (7 = UI foley); older timelines are untouched
        G = {**G, "rev": max(int(G.get("rev", 5)), int(tl["rev"]))}
    rev = int(G.get("rev", 5))
    tels = build(tl)
    events = build_events(tl, tels, G)
    n = int(round(tl["duration"] * SR)) + SR  # one extra second so tails ring past the last event; cropped below
    buf = np.zeros((n, 2))
    send = np.zeros((n, 2)) if rev >= 6 else None
    cache: dict[tuple, tuple[np.ndarray, int]] = {}
    for e in events:
        key = (e["role"], e["seed"])
        if key not in cache:
            cache[key] = _voice(e, rev)
        sig, anchor = cache[key]
        V.place(buf, sig, int(round(e["t"] * SR)) - anchor, 10 ** (e["gain_db"] / 20), e["pan"],
                stereo_shimmer=(e["role"] == "crystal"))
        if send is not None and e["role"] in SEND_ROLES:
            V.place(send, sig, int(round(e["t"] * SR)) - anchor, 10 ** (e["gain_db"] / 20), e["pan"],
                    stereo_shimmer=(e["role"] == "crystal"))
    n_out = int(round(tl["duration"] * SR))
    cont = np.zeros_like(buf)  # every continuous layer, kept apart so its level and brightness can be audited
    abs_layer, bed_stats = None, {}
    if rev >= 6:
        layers = foley.render_layers(cont, tels, G, rev=6)
        abs_layer, bed_stats = studio_bed.abs_layers(tels, n_out, G, [e["t"] for e in events if e["role"] == "tick"])
        buf += cont
        out, stats = master.master(buf[:n_out], G, send[:n_out], abs_layer)
    else:
        layers = foley.render_layers(cont, tels, G)
        _bed(cont, tl, G)
        buf += cont
        out, stats = master.master(buf[:n_out], G)
    gain = 10 ** (stats.pop("gain_db") / 20)
    c = cont[:n_out] * gain + (abs_layer if abs_layer is not None else 0.0)
    sos = butter(4, [2000, 8000], "bp", fs=SR, output="sos")
    hf = sosfilt(sos, c.mean(axis=1))
    info = {"events": events, "by_role": dict(Counter(e["role"] for e in events)), "layers": layers, "rev": rev,
            "bed": bed_stats, "continuous_hf_2k_8k_dbfs": round(float(10 * np.log10((hf ** 2).mean() + 1e-20)), 1),
            "continuous_rms_dbfs": round(float(10 * np.log10((c ** 2).mean() + 1e-20)), 1), **stats}
    return out.astype(np.float32), info
