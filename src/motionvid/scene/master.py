"""Mastering bus: short room reverb (HP 250 Hz send) -> tilt EQ -> glue compressor -> loudness -> room tone -> true-peak limiter."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt

from .voices import SR, TAU


def reverb(x: np.ndarray, wet: float, t60: float, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int((t60 * 1.3 + 0.012) * SR)
    t = np.arange(n) / SR
    env = np.exp(-6.9 * np.maximum(t - 0.012, 0) / t60) * (t >= 0.012)
    ir = lfilter([0.6], [1, -0.4], rng.standard_normal((n, 2)) * env[:, None], axis=0)
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True))
    send = sosfilt(butter(2, 250, "hp", fs=SR, output="sos"), x, axis=0)
    wet_sig = np.stack([fftconvolve(send[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return x + wet * wet_sig


def shelf(x: np.ndarray, f: float, gain_db: float, high: bool) -> np.ndarray:
    A, w = 10 ** (gain_db / 40), TAU * f / SR
    c, s = np.cos(w), np.sin(w)
    al = s / 2 * np.sqrt(2)
    r = 2 * np.sqrt(A) * al
    if high:
        b = [A * ((A + 1) + (A - 1) * c + r), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - r)]
        a = [(A + 1) - (A - 1) * c + r, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - r]
    else:
        b = [A * ((A + 1) - (A - 1) * c + r), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - r)]
        a = [(A + 1) + (A - 1) * c + r, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - r]
    return lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)


def glue(x: np.ndarray, ratio: float = 2.0, attack_ms: float = 10.0, release_ms: float = 80.0, below_peak_db: float = 6.0):
    blk = SR // 1000
    m = len(x) // blk * blk
    lvl = 20 * np.log10(np.abs(x[:m]).max(axis=1).reshape(-1, blk).max(axis=1) + 1e-9)
    thr = lvl.max() - below_peak_db
    target = np.maximum(lvl - thr, 0) * (1 - 1 / ratio)
    a, r = np.exp(-1 / attack_ms), np.exp(-1 / release_ms)
    g, out = 0.0, np.empty_like(target)
    for i, tg in enumerate(target):
        k = a if tg > g else r
        g = k * g + (1 - k) * tg
        out[i] = g
    gain = np.interp(np.arange(len(x)) / blk, np.arange(len(out)) + 0.5, out)
    return x * (10 ** (-gain / 20))[:, None], float(out.max())


def lufs(x: np.ndarray) -> float:
    """Integrated loudness, ITU-R BS.1770 K-weighting with absolute and relative gates."""
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1, -2, 1], [1, -1.99004745483398, 0.99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0) ** 2
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    c = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y, axis=0)])
    starts = np.arange(0, max(1, len(y) - blk + 1), hop)
    z = (c[starts + blk] - c[starts]).sum(axis=1) / blk
    z = z[z > 1e-12]
    if z.size == 0:
        return -70.0
    keep = z[-0.691 + 10 * np.log10(z) > -70]
    if keep.size == 0:
        return -70.0
    keep = keep[-0.691 + 10 * np.log10(keep) > -0.691 + 10 * np.log10(keep.mean()) - 10]
    return float(-0.691 + 10 * np.log10(keep.mean())) if keep.size else -70.0


def true_peak_db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.abs(resample_poly(x, 4, 1, axis=0)).max() + 1e-12))


def limit(x: np.ndarray, ceiling_db: float = -1.0, look_ms: float = 2.0) -> np.ndarray:
    ceil = 10 ** (ceiling_db / 20)
    os_ = np.abs(resample_poly(x, 4, 1, axis=0)).max(axis=1)
    g = np.minimum(1.0, ceil / (os_ + 1e-12))[: len(x) * 4].reshape(-1, 4).min(axis=1)
    w = int(look_ms * SR / 1000) * 2 + 1
    g = uniform_filter1d(minimum_filter1d(g, w), w)
    y = x * g[:, None]
    over = true_peak_db(y)
    return y * 10 ** ((ceiling_db - over) / 20) if over > ceiling_db else y


def room_tone(n: int, dbfs: float, seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pink = lfilter([0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400],
                   rng.standard_normal((n, 2)), axis=0)
    pink = sosfilt(butter(2, 3000, "lp", fs=SR, output="sos"), pink, axis=0)
    return pink * (10 ** (dbfs / 20) / np.sqrt((pink ** 2).mean()))


def master(mix: np.ndarray, G: dict[str, float]) -> tuple[np.ndarray, dict[str, float]]:
    x = reverb(mix, G["reverb_wet"], G["reverb_t60"])
    x = shelf(shelf(x, 85, G["tilt_low_db"], False), 9000, G["tilt_high_db"], True)
    x, gr = glue(x, G["glue_ratio"])
    x *= 10 ** ((G["target_lufs"] - lufs(x)) / 20)
    x = x + room_tone(len(x), G["room_dbfs"])
    x = limit(x, G["tp_ceiling_db"])
    f = min(len(x), int(0.9 * SR))
    x[-f:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f)))[:, None]
    n_in = min(len(x), int(0.004 * SR))
    x[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    return x, {"glue_max_gr_db": round(gr, 2), "lufs": round(lufs(x), 2), "true_peak_dbtp": round(true_peak_db(x), 2)}
