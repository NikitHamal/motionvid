"""Scene telemetry -> discrete sound events, with musical phrasing, burst grouping, and strict 3-voice polyphony budget."""

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
    out = []
    for c in tl["cuts"]:
        tc = float(c["t"])
        i = min(int(tc * HZ), len(tels[0].ts) - 1) if tels else 0
        s = 0.55
        for T in tels:
            if T.kind in SHAPES and T.kind != "ring":
                lo, hi = max(0, i - int(0.6 * HZ)), min(len(T.area) - 1, i + int(0.08 * HZ))
                s = max(s, min(1.0, float(T.area[hi] - T.area[lo])))
        kind = c.get("kind", "cut")
        pre = G["preroll_s"] * (1.12 if s > 0.8 else 1.0)
        out.append(_ev(tc, "whoosh", G["whoosh_db"] + 3 * s, 0.0, f"cut:{kind} pre-roll {pre * 1000:.0f} ms", pre=pre, post=0.55, s=s))
        out.append(_ev(tc, "impact", G["impact_db"] + 2 * s, 0.0, f"cut:{kind} mass {s:.2f}", s=s))
    return out


def _expansions(tels, G):
    out = []
    shaped = [T for T in tels if T.kind != "text"]
    if not shaped:
        return out
    # Composite scene area growth (captures both single hero blobs and multi-element bursts as one sub-boom 85->45 Hz)
    n = len(shaped[0].ts)
    tot_a = sum(T.area for T in shaped)
    step = int(0.25 * HZ)
    rise = tot_a[step:] - tot_a[:-step]
    cl: list[int] = []
    for idx in list(np.flatnonzero(rise >= 0.02)) + [10 ** 9]:
        if cl and (idx == 10 ** 9 or (idx - cl[-1]) / HZ > 0.3):
            best = cl[int(np.argmax(rise[cl]))]
            t = (best + 0.5 * step) / HZ
            dA = float(rise[best])
            s = min(1.0, math.sqrt(max(0.02, dA)) / 0.65)
            k = min(n - 1, best + step // 2)
            w_a = sum(float(T.area[k]) for T in shaped) + 1e-9
            xn = sum(float(T.area[k] * T.xn[k]) for T in shaped) / w_a
            out.append(_ev(t, "sub", G["sub_db"] - 8 * (1 - s), pan_of(xn, G),
                           f"scene: area +{dA * 100:.1f}% sub-boom", s=s, f0=G["sub_f0"], f1=G["sub_f1"]))
            cl = []
        if idx != 10 ** 9:
            cl.append(idx)
    return out


def _spread(T: Tel, G) -> float:
    xn = float(T.xn[len(T.xn) // 2])
    base = pan_of(xn, G)
    return base + (((seed_of(T.id) % 1000) / 1000) - 0.5) * 0.5 if abs(xn - 0.5) < 0.02 and T.x.std() < 1e-3 else base


def _notes(tels, G):
    notes = []
    for T in tels:
        if (T.kind == "text" and (T.el.get("split") or T.el.get("type"))) or (T.kind == "circle" and T.area.max() >= 2.0):
            continue
        # Mute individual oscillating spring bars (handled by composite continuous brush sweep + collapse click)
        if T.kind == "rrect" and len(T.el.get("tracks", {}).get("w", [])) > 2:
            continue
        mass = (lambda k: math.sqrt(float(T.area[k]))) if T.kind != "text" else (lambda k: min(1.0, float(T.el.get("size", 96)) / 600))
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


def _phrases(notes, G):
    """Rule 2: Group multi-element bursts within 400 ms into <= 3 staggered low-mid voices (0 dB, -5 dB, -10 dB)."""
    out = []
    raw = sorted(notes, key=lambda n: n[0])
    cd = G.get("cooldown_s", 0.11)
    idx = 0
    while raw:
        t0 = raw[0][0]
        grp = [r for r in raw if r[0] - t0 <= 0.42]
        raw = raw[len(grp):]
        # Sort burst so hero shapes come first, capped at 3 voices max
        grp_sorted = sorted(grp, key=lambda r: (-round(r[2], 2), r[0]))[:3]
        grp_sorted.sort(key=lambda r: r[0])
        last_t = -9.0
        for v_i, (t, T, s) in enumerate(grp_sorted):
            t_emit = max(t, last_t + cd) if v_i > 0 else t
            last_t = t_emit
            f = WOODY_HZ[(idx + v_i) % len(WOODY_HZ)]
            # Rule 2 & Timestamp Audit: mini-blob bursts (s < 0.18) tucked -14 to -18 dB behind hero transients; 3 staggered voices (0, -5, -10 dB)
            atten = -5.0 * v_i - (15.0 if s < 0.18 else 0.0)
            g = G["pluck_db"] + atten
            out.append(_ev(t_emit, "pluck", g, _spread(T, G), f"{T.id}: damped woody pop #{v_i + 1}/{len(grp)}",
                           freq=f, bell=False, dur=0.16))
        idx += 1
    return out


def _typography(tl, tels, G):
    out, W = [], tl["width"]
    hero_idx = 0
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
            if times:
                # Hero low-mid wooden thud (280 Hz & 340 Hz) or 2-note motif for brand reveal
                f_hero = 280.0 if hero_idx % 2 == 0 else 340.0
                hero_idx += 1
                out.append(_ev(max(0.0, times[0][2] - 0.02), "pluck", G["pluck_db"] + 1.0, 0.0, f"{T.id}: hero wooden thud",
                               freq=f_hero, bell=False, dur=0.14))
                if text.lower() == "motionvid" and len(times) >= 4:
                    out.append(_ev(times[-1][2] + 0.06, "pluck", G["pluck_db"] + 0.5, 0.12,
                                   f"{T.id}: signature motif", freq=340.0, bell=False, dur=0.16))
        elif el.get("type"):
            ty = el["type"]
            times = [(i, c, ty["t"] + i / ty["cps"]) for i, c in enumerate(text[:int(ty["n"])]) if not c.isspace()]
        if not times:
            continue
        base = snap_pent(float(np.clip(520 * (120 / size) ** 0.2, 430, 680)))
        tot = len(text) * 0.58 * size
        is_split = bool(el.get("split"))
        for k, (i, c, t) in enumerate(times):
            rng = np.random.default_rng(seed_of(T.id, i))
            f = base * 2 ** ((k / G["semitone_every"]) / 12) * 2 ** (rng.uniform(-G["jitter_cents"] * 0.35, G["jitter_cents"] * 0.35) / 1200)
            xc = float(np.interp(t, T.ts, T.x)) - tot / 2 + (i + 0.5) * 0.58 * size
            g = G["tick_db"] - (5.0 if is_split else 0.0) + rng.uniform(-G["vel_jitter_db"], G["vel_jitter_db"]) - 0.12 * min(k, 15)
            out.append(_ev(t, "tick", g, pan_of(xc / W, G), f"{T.id}: glyph {c!r} #{k}", freq=f))
    return out


def _contractions(tels, G):
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
        t, m, xn = float(np.mean([r[0] for r in grp])), min(4, len(grp)), float(np.mean([r[1] for r in grp]))
        out.append(_ev(t, "suction", G["suction_db"] + 1.5 * m, pan_of(xn, G), f"{len(grp)} shape(s) collapse", dur=0.38))
        out.append(_ev(t, "crystal", G["crystal_db"] + 1.0 * m, pan_of(xn, G), "collapse 4 kHz micro-click"))
    return out


def _hints(tl, G):
    cuts = [c["t"] for c in tl["cuts"]]
    out = []
    for s in tl["sfx"]:
        role, t, d = s["role"], float(s["t"]), float(s.get("dur", 0.6))
        if role == "riser":
            out.append(_ev(t, "riser", float(s.get("gain_db", -8)) - 2, float(s.get("pan", 0)), "agent hint", dur=d))
        elif role == "impact":
            out.append(_ev(t, "impact", float(s.get("gain_db", -8)), float(s.get("pan", 0)), "agent hint", s=float(np.clip((s.get("gain_db", -8) + 24) / 22, 0.2, 1))))
        elif role == "whoosh" and all(abs(t - c) > 0.35 for c in cuts):
            out.append(_ev(t, "whoosh", float(s.get("gain_db", -10)), float(s.get("pan", 0)), "agent hint", pre=d * 0.45, post=d * 0.55, s=0.4))
    return out


def build_events(tl: dict[str, Any], tels: list[Tel], G: dict[str, float]) -> list[dict[str, Any]]:
    evs = [*_transitions(tl, tels, G), *_expansions(tels, G), *_phrases(_notes(tels, G), G),
           *_typography(tl, tels, G), *_contractions(tels, G), *_hints(tl, G)]
    return sorted([e for e in evs if 0 <= e["t"] <= tl["duration"]], key=lambda e: (e["t"], e["role"]))
