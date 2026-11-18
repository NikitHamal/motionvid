"""Scene telemetry -> discrete sound events with exact offset rules, 1 hero pluck per scene, and non-pitched text ticks."""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np

from ..timeline import sample
from .telemetry import HZ, SHAPES, Tel, first_cross

PENT = (0, 3, 5, 7, 10)  # A minor pentatonic, semitones above A
WOODY_HZ = (220.0, 261.6, 280.0, 329.6, 340.0, 392.0, 420.0)


def seed_of(*parts: Any) -> int:
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:7], 16)


def note_hz(deg: int, octave: int = 0) -> float:
    o, d = divmod(int(deg), 5)
    f = 220.0 * 2 ** ((PENT[d] + 12 * (o + octave)) / 12)
    while f > 420.0:
        f *= 0.5
    return max(180.0, f)


def snap_pent(f: float) -> float:
    m = 12 * math.log2(f / 220.0)
    o = math.floor(m / 12)
    best = min([*PENT, 12], key=lambda s: abs(s - (m - 12 * o)))
    return 220.0 * 2 ** ((12 * o + best) / 12)


def pan_of(xn: float, G: dict[str, float]) -> float:
    return float(np.clip((xn - 0.5) * 2 * G["pan_width"], -G["pan_width"], G["pan_width"]))


def _ev(t, role, gain_db, pan, why, **p) -> dict[str, Any]:
    return dict(t=round(float(t), 4), role=role, gain_db=round(float(gain_db), 2), pan=round(float(pan), 3),
                seed=seed_of(role, round(t, 3), why), why=why, p=p)


def _transitions(tl, tels, G):
    """Enforce offset rules on scene cuts:
    - whoosh: start = cut.time - 0.16s, peak filter cutoff at cut.time, tail out +0.18s
    - sub + impact: locked at sub.time === impact.time === cut.time (0 ms offset)
    """
    out = []
    for c in tl["cuts"]:
        tc = round(float(c["t"]), 4)
        i = min(int(tc * HZ), len(tels[0].ts) - 1) if tels else 0
        s = 0.75
        for T in tels:
            if T.kind in SHAPES and T.kind != "ring":
                lo, hi = max(0, i - int(0.6 * HZ)), min(len(T.area) - 1, i + int(0.08 * HZ))
                s = max(s, min(1.0, float(T.area[hi] - T.area[lo])))
        kind = c.get("kind", "cut")
        pre, post = 0.16, 0.18
        out.append(_ev(tc, "whoosh", G["whoosh_db"] + 3 * s, 0.0, f"cut:{kind} pre-roll 160 ms", pre=pre, post=post, s=s))
        out.append(_ev(tc, "impact", G["impact_db"] + 2 * s, 0.0, f"cut:{kind} mass {s:.2f}", s=s))
        out.append(_ev(tc, "sub", G["sub_db"], 0.0, f"cut:{kind} locked sub-drop", s=s, f0=92.0, f1=36.0))
    return out


def _expansions(tl, tels, G):
    """Emit sub-drop only for major non-cut hero shape arrivals (never pre-bloom before cuts or on oscillating bars)."""
    out = []
    cuts = [float(c["t"]) for c in tl["cuts"]]
    shaped = [
        T for T in tels
        if T.kind not in ("text", "ring")
        and T.area.max() < 2.0
        and not (T.kind == "rrect" and len(T.el.get("tracks", {}).get("w", [])) > 2)
    ]
    if not shaped:
        return out
    n = len(shaped[0].ts)
    tot_a = sum(T.area for T in shaped)
    step = int(0.25 * HZ)
    rise = tot_a[step:] - tot_a[:-step]
    cl: list[int] = []
    for idx in list(np.flatnonzero(rise >= 0.12)) + [10 ** 9]:
        if cl and (idx == 10 ** 9 or (idx - cl[-1]) / HZ > 0.35):
            best = cl[int(np.argmax(rise[cl]))]
            t = (best + 0.5 * step) / HZ
            dA = float(rise[best])
            if all(abs(t - tc) > 0.55 for tc in cuts):
                s = min(1.0, math.sqrt(max(0.05, dA)) / 0.65)
                k = min(n - 1, best + step // 2)
                w_a = sum(float(T.area[k]) for T in shaped) + 1e-9
                xn = sum(float(T.area[k] * T.xn[k]) for T in shaped) / w_a
                out.append(_ev(t, "sub", G["sub_db"] - 6 * (1 - s), pan_of(xn, G),
                               f"scene: area +{dA * 100:.1f}% sub-boom", s=s, f0=92.0, f1=36.0))
            cl = []
        if idx != 10 ** 9:
            cl.append(idx)
    return out


def _spread(T: Tel, G) -> float:
    xn = float(T.xn[len(T.xn) // 2])
    base = pan_of(xn, G)
    return base + (((seed_of(T.id) % 1000) / 1000) - 0.5) * 0.5 if abs(xn - 0.5) < 0.02 and T.x.std() < 1e-3 else base


def _notes(tels, G):
    """Detect shape arrivals (excluding text, decorative rings, full-screen floods, and oscillating width bars)."""
    notes = []
    for T in tels:
        if T.kind in ("text", "ring") or T.area.max() >= 2.0 or T.id == "outro":
            continue
        if T.kind == "rrect" and len(T.el.get("tracks", {}).get("w", [])) > 2:
            continue
        mass = lambda k: math.sqrt(float(T.area[k]))  # noqa: E731
        sc, n, i, popped = T.scale, len(T.scale), 0, False
        while i < n - 1:
            j = min(n - 1, i + int(0.55 * HZ))
            if sc[i:j + 1].max() - sc[i] >= 0.25 and sc[min(n - 1, i + 1)] - sc[i] > 1e-6:
                k = i + int(np.argmax(sc[i:j + 1]))
                notes.append((first_cross(sc, sc[i] + 0.85 * (sc[k] - sc[i]), i, k) / HZ, T, mass(k)))
                popped = True
                i = k + int(0.45 * HZ)
            else:
                i += 1
        if popped:
            continue
        op, fw = T.op, int(0.3 * HZ)
        for i in range(len(op) - fw):
            if op[i] <= 0.05 and op[i + fw] >= 0.9:
                notes.append((first_cross(op, 0.5, i, i + fw) / HZ, T, mass(i + fw)))
                break
    return notes


def _phrases(tl, notes, G):
    """Keep pitched marimba/pluck notes strictly for ONE hero arrival per scene."""
    out = []
    edges = [0.0] + sorted(float(c["t"]) for c in tl["cuts"]) + [float(tl["duration"])]
    for s_idx, (a, b) in enumerate(zip(edges, edges[1:])):
        scene_notes = [r for r in notes if a <= r[0] < b - 0.12]
        if not scene_notes:
            continue
        # Pick the single largest-mass hero shape arrival in the scene
        hero = max(scene_notes, key=lambda r: (round(r[2], 2), -r[0]))
        t, T, _ = hero
        f = WOODY_HZ[s_idx % len(WOODY_HZ)]
        out.append(_ev(t, "pluck", G["pluck_db"], _spread(T, G),
                       f"{T.id}: damped woody pop #1/{len(scene_notes)}", freq=f, bell=False, dur=0.16))
    return out


def _typography(tl, tels, G):
    """Replace all text plucks with ultra-short non-pitched tactile micro-clicks (`tick`) with +-3 dB jitter."""
    out, W = [], tl["width"]
    for T in tels:
        el = T.el
        if T.kind != "text":
            continue
        text, size = el.get("text") or el["id"], float(el.get("size", 96))
        times: list[tuple[int, str, float]] = []
        if el.get("split"):
            chars, st = list(text), float(el.get("stagger", 0.12))
            p = np.array(sample(el, "p", list(T.ts), 1.0))
            for i, c in enumerate(chars):
                cp = np.clip(p * (1 + st * len(chars)) - i * st, 0, 1)
                if not c.isspace() and cp.max() >= 0.35:
                    times.append((i, c, float(np.argmax(cp >= 0.35)) / HZ))
        elif el.get("type"):
            ty = el["type"]
            times = [(i, c, ty["t"] + i / ty["cps"]) for i, c in enumerate(text[:int(ty["n"])]) if not c.isspace()]
        else:
            # Whole-card text reveal (e.g. 48 KHZ, 0 BYTES, 25.8X SYNC): single tactile micro-click
            op, fw = T.op, int(0.25 * HZ)
            for i in range(len(op) - fw):
                if op[i] <= 0.05 and op[i + fw] >= 0.9:
                    t_card = first_cross(op, 0.5, i, i + fw) / HZ
                    out.append(_ev(t_card, "tick", G["tick_db"] + 1.5, pan_of(float(np.interp(t_card, T.ts, T.xn)), G),
                                   f"{T.id}: card micro-click", freq=520.0))
                    break
            continue
        if not times:
            continue
        base = snap_pent(float(np.clip(520 * (120 / size) ** 0.2, 430, 680)))
        tot = len(text) * 0.58 * size
        is_split = bool(el.get("split"))
        vj = max(3.0, float(G.get("vel_jitter_db", 3.0)))
        for k, (i, c, t) in enumerate(times):
            rng = np.random.default_rng(seed_of(T.id, i))
            f = base * 2 ** ((k / G["semitone_every"]) / 12) * 2 ** (rng.uniform(-G["jitter_cents"] * 0.35, G["jitter_cents"] * 0.35) / 1200)
            xc = float(np.interp(t, T.ts, T.x)) - tot / 2 + (i + 0.5) * 0.58 * size
            g = G["tick_db"] - (3.5 if is_split else 0.0) + rng.uniform(-vj, vj) - 0.1 * min(k, 15)
            out.append(_ev(t, "tick", g, pan_of(xc / W, G), f"{T.id}: glyph {c!r} #{k}", freq=f))
    return out


def _contractions(tels, G):
    """Enforce offset rules for collapse:
    - suction: start = collapse.time - 0.25s, end = collapse.time (hard gate at 0.0s offset)
    - crystal: fires at collapse.time
    """
    raw = []
    for T in tels:
        if T.kind not in ("rrect", "blob", "circle"):
            continue
        n, win = len(T.w), int(0.7 * HZ)
        i = 0
        while i < n - win:
            j = i + win
            if T.w[i] >= 500 and T.w[j] <= 0.45 * T.w[i] and T.w[j] <= 420 and T.area.max() < 2.0:
                raw.append((first_cross(T.w, T.w[j] * 1.1, i, j, rising=False) / HZ, float(T.xn[j])))
                i = j + HZ
            else:
                i += 1
        a = np.flatnonzero((T.scale[:-int(0.12 * HZ)] >= 0.8) & (T.scale[int(0.12 * HZ):] <= 0.05))
        if a.size:
            raw.append((first_cross(T.scale, 0.05, int(a[0]), int(a[0]) + int(0.12 * HZ), rising=False) / HZ, float(T.xn[int(a[0])])))
    out, raw = [], sorted(raw)
    while raw:
        t0 = raw[0][0]
        grp = [r for r in raw if r[0] - t0 < 0.15]
        raw = raw[len(grp):]
        t = round(float(np.mean([r[0] for r in grp])), 2)
        m, xn = min(4, len(grp)), float(np.mean([r[1] for r in grp]))
        t_suc = max(0.0, round(t - 0.25, 4))
        dur_suc = max(0.05, round(t - t_suc, 4))
        out.append(_ev(t_suc, "suction", G["suction_db"] + 1.5 * m, pan_of(xn, G),
                       f"{len(grp)} shape(s) anticipation sweep -> {t:.2f}s", dur=dur_suc, end=t))
        out.append(_ev(t, "crystal", G["crystal_db"] + 1.0 * m, pan_of(xn, G), "collapse detuned crystal"))
    return out


def _hints(tl, G):
    cuts = [c["t"] for c in tl["cuts"]]
    out = []
    for s in tl["sfx"]:
        role, t, d = s["role"], float(s["t"]), float(s.get("dur", 0.55))
        if role == "riser":
            out.append(_ev(t, "riser", float(s.get("gain_db", -8)) - 2, float(s.get("pan", 0)), "agent hint", dur=d))
        elif role == "impact":
            out.append(_ev(t, "impact", float(s.get("gain_db", -8)), float(s.get("pan", 0)), "agent hint",
                           s=float(np.clip((s.get("gain_db", -8) + 24) / 22, 0.2, 1))))
        elif role == "whoosh" and all(abs(t - c) > 0.35 for c in cuts):
            out.append(_ev(t, "whoosh", float(s.get("gain_db", -10)), float(s.get("pan", 0)), "agent hint",
                           pre=0.16, post=0.18, s=0.4))
    return out


def build_events(tl: dict[str, Any], tels: list[Tel], G: dict[str, float]) -> list[dict[str, Any]]:
    evs = [*_transitions(tl, tels, G), *_expansions(tl, tels, G), *_phrases(tl, _notes(tels, G), G),
           *_typography(tl, tels, G), *_contractions(tels, G), *_hints(tl, G)]
    # Remove all new triggers during the final fade-out window (after 15.40s on 16.8s launch reel)
    has_outro = any(el.get("id") == "outro" for el in tl.get("elements", []))
    max_t = tl["duration"] - 1.40 if has_outro else tl["duration"]
    return sorted([e for e in evs if 0 <= e["t"] <= max_t + 1e-6], key=lambda e: (e["t"], e["role"]))
