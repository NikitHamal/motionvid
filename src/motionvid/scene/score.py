"""Scene telemetry -> discrete sound events (what happens), with musical phrasing and humanization.

Events: {t, role, gain_db, pan, seed, why, p}. `t` is when the HIT is heard. Roles map to voices.py.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np

from ..timeline import sample
from .telemetry import HZ, SHAPES, Tel, first_cross

PENT = (0, 3, 5, 7, 10)  # A minor pentatonic, semitones above A


def seed_of(*parts: Any) -> int:
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:7], 16)


def note_hz(deg: int, octave: int = 1) -> float:
    o, d = divmod(int(deg), 5)
    return 220.0 * 2 ** ((PENT[d] + 12 * (o + octave - 1)) / 12)


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
        if kind in ("flash", "cut"):
            out.append(_ev(tc + 0.012, "crystal", G["crystal_db"] - 4, 0.0, f"cut:{kind} air"))
    return out


def _expansions(tels, G):
    out = []
    for T in tels:
        if T.kind not in SHAPES or T.kind == "ring":
            continue
        A, n, i = T.area, len(T.area), 0
        while i < n - 1:
            j = min(n - 1, i + int(0.9 * HZ))
            if A[i:j + 1].max() - A[i] >= 0.02 and A[min(n - 1, i + 1)] > A[i] + 1e-9:
                k = i + int(np.argmax(A[i:j + 1]))
                dA = float(A[k] - A[i])
                if A[k] < 2.0:  # full-frame floods get their sub from the cut impact
                    s = min(1.0, math.sqrt(dA) / 0.9)
                    t = first_cross(A, A[i] + 0.85 * dA, i, k) / HZ
                    out.append(_ev(t, "sub", G["sub_db"] - 16 * (1 - s), pan_of(float(T.xn[k]), G),
                                   f"{T.id}: area +{dA * 100:.1f}% of frame", s=s, f0=G["sub_f0"] + 30 * (1 - s), f1=G["sub_f1"] + 28 * (1 - s)))
                i = k + int(0.3 * HZ)
            else:
                i += 1
    return out


def _spread(T: Tel, G) -> float:
    xn = float(T.xn[len(T.xn) // 2])
    base = pan_of(xn, G)
    return base + (((seed_of(T.id) % 1000) / 1000) - 0.5) * 0.7 if abs(xn - 0.5) < 0.02 and T.x.std() < 1e-3 else base


def _notes(tels, G):
    notes = []
    for T in tels:
        if (T.kind == "text" and (T.el.get("split") or T.el.get("type"))) or (T.kind == "circle" and T.area.max() >= 2.0):
            continue
        mass = (lambda k: math.sqrt(float(T.area[k]))) if T.kind != "text" else (lambda k: min(1.0, float(T.el.get("size", 96)) / 600))
        sc, n, i, popped = T.scale, len(T.scale), 0, False
        while i < n - 1:
            j = min(n - 1, i + int(0.55 * HZ))
            if sc[i:j + 1].max() - sc[i] >= 0.25 and sc[min(n - 1, i + 1)] - sc[i] > 1e-6:
                k = i + int(np.argmax(sc[i:j + 1]))
                notes.append((first_cross(sc, sc[i] + 0.85 * (sc[k] - sc[i]), i, k) / HZ, T, mass(k)))
                popped = True
                i = k + int(0.25 * HZ)
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
    out, prev, idx = [], -9.0, 0
    for t, T, s in sorted(notes, key=lambda n: n[0]):
        idx = 0 if t - prev > 0.5 else idx + 1
        prev = t
        oct_ = 0 if s > 0.5 else (2 if s < 0.12 else 1)
        rng = np.random.default_rng(seed_of(T.id, round(t, 3)))
        f = note_hz(idx % 10, oct_) * 2 ** (rng.uniform(-G["jitter_cents"], G["jitter_cents"]) / 1200 / 3)
        g = G["pluck_db"] + rng.uniform(-1.5, 1.5) + (1.5 if idx == 0 else 0)
        out.append(_ev(t, "pluck", g, _spread(T, G), f"{T.id}: pop, note {idx} of phrase", freq=f, bell=T.kind == "ring", dur=0.9 if T.kind == "ring" else 0.45))
    return out


def _typography(tl, tels, G):
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
        if not times:
            continue
        base = snap_pent(float(np.clip(900 * (120 / size) ** 0.3, 450, 1400)))
        tot = len(text) * 0.58 * size
        for k, (i, c, t) in enumerate(times):
            rng = np.random.default_rng(seed_of(T.id, i))
            f = base * 2 ** (math.floor(k / G["semitone_every"]) / 12) * 2 ** (rng.uniform(-G["jitter_cents"], G["jitter_cents"]) / 1200)
            xc = float(np.interp(t, T.ts, T.x)) - tot / 2 + (i + 0.5) * 0.58 * size
            g = G["tick_db"] + rng.uniform(-G["vel_jitter_db"], G["vel_jitter_db"]) + (2.0 if k == 0 else 0) - 0.15 * min(k, 15) + (2 if size > 200 else 0)
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
        grp = [r for r in raw if r[0] - t0 < 0.1]
        raw = raw[len(grp):]
        t, m, xn = float(np.mean([r[0] for r in grp])), min(4, len(grp)), float(np.mean([r[1] for r in grp]))
        out.append(_ev(t, "suction", G["suction_db"] + 2 * m, pan_of(xn, G), f"{len(grp)} shape(s) collapse", dur=0.45))
        out.append(_ev(t, "crystal", G["crystal_db"] + 1.5 * m, pan_of(xn, G), "collapse payoff"))
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
    ev = _transitions(tl, tels, G) + _expansions(tels, G) + _phrases(_notes(tels, G), G) + _typography(tl, tels, G)
    ev += _contractions(tels, G) + _hints(tl, G)
    return sorted(ev, key=lambda e: (e["t"], e["role"]))
