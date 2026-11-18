"""Continuous layers bound to scene telemetry. Each layer is rendered only where its signal is active.

  velocity -> filtered-noise texture + servo hum   (cutoff 300 Hz at rest -> 4.5 kHz at peak speed, gain follows speed)
  w-rate   -> rubbery stretch tone                 (pitch follows the width, gain follows how fast it stretches)
  amp-rate -> morph shimmer                        (pitch follows lobe sharpness; fills what used to be dead air)
  x(t)     -> constant-power pan, per sample       (moving objects move across the stereo field)
"""

from __future__ import annotations

import numpy as np

from .score import note_hz, seed_of
from .telemetry import HZ, Tel, smooth, windows
from .voices import SR, TAU, biquad_tv

SHAPED = ("blob", "circle", "rrect")


def _slice(T: Tel, i0: int, i1: int):
    n = int((i1 - i0) / HZ * SR)
    tt = np.linspace(T.ts[i0], T.ts[i1], n, endpoint=False)
    return n, tt, lambda a: np.interp(tt, T.ts, a)


def _stereo(mono: np.ndarray, xn: np.ndarray, G, spread: float = 0.0) -> np.ndarray:
    p = np.clip((xn - 0.5) * 2 * G["pan_width"] + spread, -1, 1)
    th = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(th), mono * np.sin(th)], axis=1) * np.sqrt(2)


def _add(buf: np.ndarray, T: Tel, i0: int, st: np.ndarray) -> None:
    s = int(T.ts[i0] * SR)
    e = min(len(buf), s + len(st))
    buf[s:e] += st[: e - s]


def _vis(T: Tel) -> np.ndarray:
    return (T.op > 0.02) & (T.scale > 0.05)


def texture(buf, T: Tel, G) -> None:
    if T.kind not in SHAPED or T.area.max() >= 2.0:
        return
    sm = smooth(T.speed, 0.04)
    rng = np.random.default_rng(seed_of(T.id, "tex"))
    size = float(np.clip(np.sqrt(T.area.mean() + 1e-9), 0, 1))
    for i0, i1 in windows((sm > 0.06) & _vis(T)):
        n, tt, f = _slice(T, i0, i1)
        if n < 64:
            continue
        env = np.clip(f(sm) / 1.2, 0, 1)
        y = biquad_tv(rng.standard_normal(n), 300 + 4200 * env ** 0.8, 0.7, "lp")
        am = (0.5 + 0.5 * np.sin(np.cumsum(TAU * (10 + 70 * env) / SR))) ** 1.5
        hum = np.sin(np.cumsum(TAU * (70 + 110 * env) / SR)) * 0.3
        g = 10 ** ((G["texture_db"] + 8 * size - 4) / 20)
        _add(buf, T, i0, _stereo((y * (0.45 + 0.55 * am) + hum) * env ** 1.15 * g, f(T.xn), G))


def stretch(buf, T: Tel, G, deg: int) -> None:
    if T.kind != "rrect" or float(T.w.max() - T.w.min()) < 200:
        return
    W = float(T.x.max() * 0 + 1920)
    sm = smooth(np.abs(np.gradient(T.w)) * HZ / W, 0.05)
    spread = (((seed_of(T.id) % 1000) / 1000) - 0.5) * 0.7
    for i0, i1 in windows((sm > 0.2) & _vis(T)):
        n, tt, f = _slice(T, i0, i1)
        if n < 64:
            continue
        gn = np.clip(f(sm) / 2.5, 0, 1) ** 0.8
        fr = note_hz(deg, 1) * 2 ** (f(T.w) / W - 0.3) * (1 + 0.012 * np.sin(TAU * 6.5 * tt))
        ph = np.cumsum(TAU * fr / SR)
        y = biquad_tv(np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph), 700 + 3500 * gn, 0.7, "lp")
        _add(buf, T, i0, _stereo(y * gn * 10 ** (G["stretch_db"] / 20), f(T.xn), G, spread))


def shimmer(buf, T: Tel, G, deg: int) -> None:
    if T.kind != "blob" or "amp" not in T.el.get("tracks", {}):
        return
    sm = smooth(np.abs(np.gradient(T.amp)) * HZ, 0.05)
    for i0, i1 in windows((sm > 0.03) & _vis(T)):
        n, tt, f = _slice(T, i0, i1)
        if n < 64:
            continue
        gn = np.clip(f(sm) / 0.25, 0, 1) ** 0.7
        ph = np.cumsum(TAU * note_hz(deg, 2) * (1 + 1.5 * f(T.amp)) / SR)
        y = np.sin(ph) + 0.5 * np.sin(2.005 * ph) + 0.25 * np.sin(3.01 * ph)
        _add(buf, T, i0, _stereo(y * gn * 10 ** (G["shimmer_db"] / 20), f(T.xn), G))


def render_layers(buf: np.ndarray, tels: list[Tel], G) -> dict[str, int]:
    k = {"texture": 0, "stretch": 0, "shimmer": 0}
    sd = si = 0
    for T in tels:
        before = float(np.abs(buf).sum())
        texture(buf, T, G)
        k["texture"] += float(np.abs(buf).sum()) > before
        before = float(np.abs(buf).sum())
        stretch(buf, T, G, sd % 4)
        if float(np.abs(buf).sum()) > before:
            sd += 1; k["stretch"] += 1
        before = float(np.abs(buf).sum())
        shimmer(buf, T, G, si)
        if float(np.abs(buf).sum()) > before:
            si += 1; k["shimmer"] += 1
    return {a: int(b) for a, b in k.items()}
