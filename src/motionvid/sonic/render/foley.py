"""Natural and foley roles: thunder, door_slam, knock, footsteps, water_drop,
explosion.

Each one is a small physical model in numpy, like the roles in `events.py`,
but built from the physics of the real sound rather than from sound-design
primitives:

* thunder: the shock waves of a tortuous lightning channel (thousands of
  N-wave pulses, one per few metres of channel, arriving in order of distance),
  with return strokes and terrain echoes.
* door_slam: an air-pressure whump (40-90 Hz), the panel's thick low modes
  (70-180 Hz) and a damped mid knock, the frame thump, a quiet latch tick, and
  a room (early reflections and a short dark tail).
* knock: 2-3 knuckle raps exciting the damped modes of a wooden door.
* footsteps: heel-toe steps across `dur`, with a varied cadence.
* water_drop: a Minnaert bubble whose pitch glides up as it rises.
* explosion: a blast transient, a sub body, a rumble and a debris crackle.

The event `seed` picks the variant deterministically (documented per role in
`VARIANTS`) and also seeds the noise; the event time adds the fine noise, the
same way the other roles do. Unlike the wide roles in `events.py`, `pan` always
applies: a stereo source is narrowed as it is panned, then placed with the
same constant-power law as the mono roles.

Every clip is zero outside `[0, dur]` plus its reverb tail, starts and ends at
exactly zero, and is high-passed at 20 Hz and low-passed (flat to 9 kHz, a
smooth slope to nothing at 12 kHz) after every envelope, attack and reverb, so
it carries no DC, no subsonic offset and no fizz to Nyquist. Every noise
attack opens over at least a millisecond.
"""

from __future__ import annotations

import numpy as np

from ..score import EVENT_ROLES, Event
from .dsp import LN1000, TAU, bandlimit, db_to_gain, pan, reverb, saturate

ROLES = ("thunder", "door_slam", "knock", "footsteps", "water_drop", "explosion")

# What the seed selects. Kept as data so the docs, the MCP tool description
# and the tests all read the same table.
VARIANTS = {
    "thunder": "seed % 4 = distance: 0 close crack, 1 near, 2 mid, 3 far rumble",
    "door_slam": ("seed % 3 = door: 0 heavy, 1 medium, 2 light interior; (seed // 3) % 3 = room: "
                  "0 small room, 1 hallway, 2 large room; seed % 2 = 1 adds a latch rattle; "
                  "(seed // 9) % 2 = 1 adds the swing's air before the hit"),
    "knock": "seed % 2 = raps: 0 two, 1 three; (seed // 2) % 3 = door size",
    "footsteps": "seed % 3 = surface: 0 hard floor, 1 stone, 2 gravel; (seed // 3) % 3 = pace: slow, walk, brisk",
    "water_drop": "seed % 2 = 0 drip (small, high), 1 plop (larger bubble, splash, second bubble)",
    "explosion": "seed % 3 = 0 close and big, 1 medium, 2 distant",
}

FOLEY_PARAMS: dict[str, dict[str, float]] = {
    "thunder": dict(width=0.8, reverb=0.0),
    "door_slam": dict(f0=95.0, width=0.35, reverb=0.28, reverb_decay=0.8),
    "knock": dict(f0=185.0, width=0.25, reverb=0.16, reverb_decay=0.5),
    "footsteps": dict(f0=190.0, width=0.2, reverb=0.14, reverb_decay=0.45),
    "water_drop": dict(width=0.3, reverb=0.18, reverb_decay=0.6),
    "explosion": dict(f0=60.0, width=0.7, reverb=0.18, reverb_decay=1.4),
}

HI = 12000.0  # nothing above this in any foley clip (matches events.ATTACK_HI)
HI_PASS = 9000.0  # flat up to here, then a smooth slope to zero at HI
LO = 20.0  # high-pass: no DC, no subsonic drift


# -- helpers -----------------------------------------------------------------


def _fftconv(a: np.ndarray, b: np.ndarray, n_out: int) -> np.ndarray:
    m = len(a) + len(b) - 1
    nfft = 1 << (m - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(a, nfft) * np.fft.rfft(b, nfft), nfft)
    return y[:n_out]


def _modes_ir(freqs, t60s, gains, sr: int, n_max: int) -> np.ndarray:
    """Impulse response of a bank of damped modes (a struck object)."""
    n = int(min(n_max, max(16, 1.1 * max(t60s) * sr)))
    t = np.arange(n) / sr
    ir = np.zeros(n)
    for f, d, g in zip(freqs, t60s, gains):
        if 20.0 < f < 0.45 * sr:
            ir += g * np.exp(-LN1000 * t / max(d, 1e-3)) * np.sin(TAU * f * t)
    return ir


def _ring(exc: np.ndarray, freqs, t60s, gains, sr: int) -> np.ndarray:
    """Excite a mode bank with the force `exc`; same length as `exc`.

    The mode bank is a displacement response; a vibrating surface radiates
    pressure in proportion to its acceleration, so the force is differentiated
    twice (12 dB/octave below each mode, as for a real plate). Without this a
    slow force pulse (a heel, a slammed door) leaks its DC content through
    every mode as a sub-bass thud far below the object's lowest mode.
    """
    acc = np.diff(np.diff(exc, prepend=0.0), prepend=0.0)
    return _fftconv(acc, _modes_ir(freqs, t60s, gains, sr, len(exc)), len(exc))


def _burst(
    rng: np.random.Generator, n: int, at: int, length: int, tau: float, sr: int, rise: float = 0.001
) -> np.ndarray:
    """A white-noise burst starting at sample `at`, exponential decay `tau` s.

    The burst opens with a raised-cosine `rise` (1 ms by default) rather than
    a step: a step onset is a full-band click that no later band limit can
    take back out of the attack."""
    out = np.zeros(n)
    if at >= n:
        return out
    k = max(1, min(length, n - at))
    t = np.arange(k) / sr
    env = np.exp(-t / max(tau, 1e-4))
    r = min(k, max(1, int(rise * sr)))
    env[:r] *= 0.5 - 0.5 * np.cos(np.pi * (np.arange(r) + 0.5) / r)
    out[at : at + k] = rng.standard_normal(k) * env
    return out


def _pulse(n: int, at: int, width: int) -> np.ndarray:
    """A half-sine force pulse (a knuckle or a heel meeting a surface)."""
    out = np.zeros(n)
    if at >= n:
        return out
    k = max(2, min(width, n - at))
    out[at : at + k] = np.sin(np.pi * (np.arange(k) + 0.5) / k)
    return out


def _smooth(rng: np.random.Generator, n: int, sr: int, rate: float) -> np.ndarray:
    """A smooth random curve in [0, 1] with about `rate` turns per second."""
    k = max(2, int(n / sr * rate) + 2)
    pts = rng.uniform(0.0, 1.0, k)
    x = np.linspace(0.0, k - 1.0, n)
    i = np.minimum(np.floor(x).astype(int), k - 2)
    w = 0.5 - 0.5 * np.cos(np.pi * (x - i))
    return pts[i] * (1.0 - w) + pts[i + 1] * w


def _fade_out(n: int, sr: int, length: float) -> np.ndarray:
    """1 everywhere, then a raised-cosine to exactly 0 over the last `length` s."""
    env = np.ones(n)
    b = min(n, max(2, int(length * sr)))
    env[-b:] = 0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, b))
    return env


def _norm(x: np.ndarray) -> np.ndarray:
    m = float(np.max(np.abs(x))) if x.size else 0.0
    return x if m < 1e-12 else x / m


def _attack(n: int, sr: int, at: float, rise: float) -> np.ndarray:
    """0 before `at`, raised-cosine rise over `rise` s, then 1."""
    t = np.arange(n) / sr
    u = np.clip((t - at) / max(rise, 1e-4), 0.0, 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * u)


# -- thunder -----------------------------------------------------------------


C_AIR = 343.0  # speed of sound, m/s

# Tuned against AudioSet and CLAP judges (scored against ESC-50 thunderstorm clips): short N-waves (~4 ms),
# a gentle loudness fall-off with distance (r**-0.43, multipath and ground focusing in place
# of free-field 1/r), a nearly isotropic segment pattern, a 63 Hz microphone high-pass and a
# mild compressor, as in a field recording.
THUNDER = dict(t_n=0.0038, t_grow=0.19, rise0=0.0006, rise_exp=0.80, amp_exp=0.43, dir_floor=1.18,
               span=0.90, echo=1.35, hp=63.0, step=3.2, cloud_e=0.43, dist=1.35, h_decay=8300.0, jitter=0.33,
               branch_e=0.63, comp=0.12, t_pow=0.88, taper=0.44, t60_lo=1.8, t60_hi=1.1)


def _tortuous(crng: np.random.Generator, start: np.ndarray, heading: np.ndarray, length: float, step: float,
              wander: float, pull: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """A tortuous channel: `length` m of `step`-m segments from `start`.

    Lightning is a chain of short straight segments whose directions scatter
    by ~16 degrees around a slowly meandering mean direction. Returns the
    segment midpoints and unit directions."""
    k = max(1, int(length / step))
    mean = heading / np.linalg.norm(heading)
    mids = np.empty((k, 3))
    dirs = np.empty((k, 3))
    pos = np.array(start, dtype=np.float64)
    for i in range(k):
        mean = mean + wander * crng.standard_normal(3)
        if pull is not None:
            mean = mean + 0.08 * pull
        mean /= np.linalg.norm(mean)
        d = mean + 0.30 * crng.standard_normal(3)
        d /= np.linalg.norm(d)
        mids[i] = pos + 0.5 * step * d
        dirs[i] = d
        pos = pos + step * d
    return mids, dirs


def _thunder(ev: Event, sr: int, rng: np.random.Generator, crng: np.random.Generator, p: dict, seed: int):
    """Thunder as it is made: a shock wave from every segment of a tortuous
    lightning channel (Few 1969).

    The flash heats a jagged channel kilometres long. Every few metres of it
    launches a short N-shaped pressure pulse (compression, linear fall,
    rarefaction). The listener hears the pulses in order of distance: the
    nearest part of the channel first, the cloud top seconds later. Where the
    channel runs across the line of sight many pulses arrive at once (a clap);
    where it runs along it they string out into a roll. Distance stretches each
    pulse and softens its shock fronts (air absorbs the highs), so the start is
    a bright crack and the tail a dark rumble. Subsequent return strokes re-use
    the main channel tens of milliseconds later, and the ground and terrain
    return late echoes.
    """
    n = max(1, int(ev.dur * sr))
    dur = n / sr
    cls = seed % 4
    # horizontal distance to the strike, by variant
    K = THUNDER
    dist_m = (350.0, 1200.0, 3000.0, 7500.0)[cls] * float(crng.uniform(0.8, 1.25)) * K['dist']
    az0 = float(crng.uniform(-0.9, 0.9))  # strike bearing, radians from straight ahead
    ground = np.array([dist_m * np.sin(az0), dist_m * np.cos(az0), 0.0])
    ear = np.array([0.0, 0.0, 1.6])

    # Channel: the main stroke from the ground up to the cloud, a long branch
    # wandering through the cloud, and a few side branches off the main stroke.
    top = float(crng.uniform(2500.0, 4500.0))
    up = np.array([0.0, 0.0, 1.0])
    step = K['step']
    main, main_d = _tortuous(crng, ground, up + 0.3 * crng.standard_normal(3) * [1, 1, 0], top, step, 0.04, up)
    cloud_parts, cloud_dirs = [], []
    for _ in range(int(crng.integers(1, 3))):
        h = np.array([crng.standard_normal(), crng.standard_normal(), 0.0])
        m, d = _tortuous(crng, main[-1], h, float(crng.uniform(2000.0, 6000.0)), 6.0, 0.05,
                         np.array([0.0, 0.0, -0.05]))
        cloud_parts.append(m)
        cloud_dirs.append(d)
    br_parts, br_dirs = [], []
    for _ in range(int(crng.integers(3, 7))):
        at = int(crng.uniform(0.15, 0.8) * len(main))
        h = np.array([crng.standard_normal(), crng.standard_normal(), -0.8])
        m, d = _tortuous(crng, main[at], h, float(crng.uniform(150.0, 700.0)), step, 0.06)
        br_parts.append(m)
        br_dirs.append(d)

    def segs(mids, dirs, step, energy):
        return mids, dirs, np.full(len(mids), step), np.full(len(mids), energy)

    groups = [segs(main, main_d, step, 1.0)]
    groups += [segs(m, d, 6.0, K['cloud_e']) for m, d in zip(cloud_parts, cloud_dirs)]
    groups += [segs(m, d, step, K['branch_e']) for m, d in zip(br_parts, br_dirs)]
    mids = np.concatenate([g[0] for g in groups])
    dirs = np.concatenate([g[1] for g in groups])
    seglen = np.concatenate([g[2] for g in groups])
    energy = np.concatenate([g[3] for g in groups])
    # the return-stroke current (and so the energy per metre) falls with height
    energy = energy * np.exp(-np.maximum(mids[:, 2], 0.0) / K['h_decay'])
    # 1-3 subsequent strokes down the main channel only (they do not branch)
    strokes = int(crng.integers(0, 3))
    offsets = np.zeros(len(mids))
    if strokes:
        extra = np.arange(len(main))
        for s in range(strokes):
            mids = np.concatenate([mids, main])
            dirs = np.concatenate([dirs, main_d])
            seglen = np.concatenate([seglen, np.full(len(main), step)])
            e = np.exp(-np.maximum(main[:, 2], 0.0) / K['h_decay']) * float(crng.uniform(0.35, 0.7))
            energy = np.concatenate([energy, e])
            offsets = np.concatenate([offsets, np.full(len(extra), (s + 1) * float(crng.uniform(0.04, 0.11)))])

    rel = mids - ear
    r = np.maximum(np.linalg.norm(rel, axis=1), 30.0)
    los = rel / r[:, None]
    # a cylindrical shock radiates broadside to its segment
    sin2 = 1.0 - np.sum(los * dirs, axis=1) ** 2
    amp = energy * seglen / 3.0 * (K['dir_floor'] + sin2) / r ** K['amp_exp']
    amp *= rng.lognormal(0.0, K['jitter'], len(amp))

    # Arrival times. A real roll lasts 5-20 s; when the channel's arrivals
    # span more than the event allows, the whole time axis is scaled to fit
    # (a power below 1 keeps the opening a little more spread out).
    t_real = (r - r.min()) / C_AIR
    onset = 0.03
    span = max(0.4, K['span'] * dur)
    t_max = float(t_real.max()) + 1e-9
    t_arr = onset + (span * (t_real / t_max) ** K['t_pow'] if t_max > span else t_real) + offsets
    # the far end of the channel fades in strength instead of stopping dead
    amp *= 0.5 + 0.5 * np.cos(np.pi * np.clip((t_real / t_max - K['taper']) / (1.0 - K['taper']), 0.0, 1.0))

    # The N-wave: length grows slowly with distance, the shock fronts soften
    # (air absorption) faster.
    t_n = K['t_n'] * rng.lognormal(0.0, 0.3, len(r)) * np.sqrt(np.sqrt(np.maximum(energy, 0.05)))
    t_n *= 1.0 + K['t_grow'] * np.log10(r / 300.0).clip(0.0, None)
    rise = np.minimum(K['rise0'] * (r / 300.0) ** K['rise_exp'], 0.35 * t_n)

    # stereo: each pulse comes from its own bearing
    bearing = np.sin(np.arctan2(rel[:, 0], rel[:, 1]))
    g_l = np.sqrt(0.5 * (1.0 - 0.85 * bearing))
    g_r = np.sqrt(0.5 * (1.0 + 0.85 * bearing))

    left = np.zeros(n)
    right = np.zeros(n)
    keep = t_arr < dur
    t_arr, t_n, rise, amp, g_l, g_r = t_arr[keep], t_n[keep], rise[keep], amp[keep], g_l[keep], g_r[keep]
    width = int(np.ceil((t_n.max() + rise.max()) * sr)) + 2 if len(t_arr) else 0
    for c0 in range(0, len(t_arr), 400):
        sl = slice(c0, c0 + 400)
        i0 = np.floor((t_arr[sl] - 0.5 * rise[sl]) * sr).astype(int)
        idx = i0[:, None] + np.arange(width)[None, :]
        u = idx / sr - t_arr[sl][:, None]  # time since the pulse's front
        T = t_n[sl][:, None]
        tr = rise[sl][:, None]
        front = 0.5 - 0.5 * np.cos(np.pi * np.clip(u / tr + 0.5, 0.0, 1.0))
        back = 0.5 + 0.5 * np.cos(np.pi * np.clip((u - T) / tr + 0.5, 0.0, 1.0))
        wave = front * back * (1.0 - 2.0 * np.clip(u, 0.0, None) / T) * amp[sl][:, None]
        ok = (idx >= 0) & (idx < n)
        left += np.bincount(idx[ok], weights=(wave * g_l[sl][:, None])[ok], minlength=n)[:n]
        right += np.bincount(idx[ok], weights=(wave * g_r[sl][:, None])[ok], minlength=n)[:n]

    # Ground, terrain and cloud echoes: a few late, darker copies.
    # Reverberation from terrain, clouds and the boundary layer: a dense,
    # diffuse tail (not discrete taps) whose highs die faster than its lows,
    # independent per ear.
    n_ir = min(n, int(2.5 * sr))
    if n_ir > int(0.2 * sr) and K['echo'] > 0.0:
        ti = np.arange(n_ir) / sr
        onset_ir = np.clip((ti - 0.05) / 0.25, 0.0, 1.0) ** 2
        for ch in (left, right):
            w = crng.standard_normal(n_ir)
            lo = bandlimit(w, sr, None, 350.0, order=2) * np.exp(-6.91 * ti / K['t60_lo'])
            hi = bandlimit(w, sr, 350.0, None, order=2) * np.exp(-6.91 * ti / K['t60_hi'])
            ir = (lo + 0.6 * hi) * onset_ir
            ir *= K['echo'] / np.sqrt(np.sum(ir ** 2) + 1e-12)
            ch += _fftconv(ch, ir, n)

    if K['hp'] > 25.0:  # what a microphone and a speaker keep of it
        left = bandlimit(left, sr, K['hp'], None, order=2)
        right = bandlimit(right, sr, K['hp'], None, order=2)
    if K['comp'] > 0.0:  # the ear hears the roll, not just the loudest clap
        env = np.sqrt(_fftconv(left ** 2 + right ** 2, np.hanning(int(0.08 * sr)) / (0.04 * sr), n) + 1e-12)
        g = (env / env.max() + 1e-4) ** (-K['comp'])
        left, right = left * g, right * g
    tail = _fade_out(n, sr, min(0.25 * dur, 1.2))
    level = 1.0 - 0.35 * cls / 3.0  # distance costs level
    return left * tail * level, right * tail * level


# -- door slam ---------------------------------------------------------------


DOOR_WHUMP, DOOR_LO, DOOR_MID, DOOR_FRAME = 0.4, 0.6, 1.4, 0.9


def _door_slam(ev: Event, sr: int, rng: np.random.Generator, crng: np.random.Generator, p: dict, seed: int):
    """A door slammed in a room: mostly low and mid, a wooden WHUMP.

    Five parts, loudest first: the air-pressure whump (the door shoves the
    air in the gap and stops dead, a 40-90 Hz push), the panel's thick low
    modes (70-180 Hz) and a damped mid knock (250-700 Hz), the frame and wall
    taking the hit (short, below 3 kHz), a quiet latch tick 12-18 dB under
    the body, and the room: early reflections here and a short, dark diffuse
    tail from the shared reverb (set per room below). Some seeds add the
    faint air of the swing before the hit.
    """
    n = max(1, int(ev.dur * sr))
    weight = (1.0, 0.8, 0.62)[seed % 3]  # heavy, medium, light interior door
    room = (seed // 3) % 3  # 0 small room, 1 hallway, 2 large room
    swing = (seed // 9) % 2 == 1
    t0 = 0.002 + (0.11 if swing else 0.0)
    at = int(t0 * sr)
    t = np.arange(n) / sr

    # 1. Air whump: one and a half cycles of a low push under a smooth window,
    # plus a breath of low noise as the air squeezes out of the gap.
    fw = crng.uniform(46.0, 58.0) / weight**0.8
    L = min(n - at, int(1.5 / fw * sr))
    whump = np.zeros(n)
    if L > 2:
        tw = np.arange(L) / sr
        whump[at : at + L] = np.sin(TAU * fw * tw) * np.sin(np.pi * (np.arange(L) + 0.5) / L) ** 2
    puff = bandlimit(_burst(rng, n, at, int(0.15 * sr), 0.03, sr, rise=0.004), sr, 30.0, 160.0, order=2)
    whump = _norm(whump) + 0.45 * _norm(puff)

    # 2. The panel. A slow push (the slam) drives the low modes; a shorter,
    # rougher contact drives the mids. Inharmonic, damped in 100-250 ms.
    f_lo = 74.0 / weight * crng.uniform(0.94, 1.06)
    lo_f = f_lo * np.array((1.0, 1.29, 1.71, 2.18)) * crng.uniform(0.97, 1.03, 4)
    lo_t = np.array((0.25, 0.21, 0.17, 0.13)) * (0.65 + 0.35 * weight)
    lo_g = (1.0, 0.8, 0.6, 0.4)
    push = _pulse(n, at, int((0.006 + 0.004 * weight) * sr))
    body_lo = _fftconv(push, _modes_ir(lo_f, lo_t, lo_g, sr, n), n)
    k_mid = 6
    mid_f = np.sort(crng.uniform(250.0, 700.0, k_mid)) / weight**0.3
    mid_t = crng.uniform(0.05, 0.11, k_mid)
    mid_g = crng.uniform(0.5, 1.0, k_mid) * np.linspace(1.0, 0.5, k_mid)
    contact = _pulse(n, at, int(0.0018 * sr)) + 0.3 * _burst(rng, n, at, int(0.006 * sr), 0.0015, sr)
    body_mid = _fftconv(contact, _modes_ir(mid_f, mid_t, mid_g, sr, n), n)
    body = DOOR_LO * _norm(body_lo) + DOOR_MID * _norm(body_mid)

    # 3. Frame and wall: a short, dull thump-crack, mostly below 3 kHz.
    frame = bandlimit(_burst(rng, n, at, int(0.05 * sr), 0.009, sr, rise=0.0012), sr, 110.0, 2600.0, order=4)

    # 4. Latch: a small metal tick just after the hit, 12-18 dB under the body,
    # with a rattle on odd seeds.
    lf = crng.uniform(2300.0, 3600.0)
    latch_ir = _modes_ir((lf, lf * 1.47, lf * 1.93), (0.03, 0.022, 0.015), (1.0, 0.55, 0.35), sr, n)
    l_at = at + int(crng.uniform(0.004, 0.016) * sr)
    latch = _fftconv(_burst(rng, n, l_at, int(0.002 * sr), 0.0005, sr), latch_ir, n)
    if seed % 2:
        for _ in range(int(crng.integers(1, 3))):
            r_at = l_at + int(crng.uniform(0.025, 0.075) * sr)
            latch += crng.uniform(0.25, 0.45) * _fftconv(_burst(rng, n, r_at, int(0.0015 * sr), 0.0004, sr), latch_ir, n)
    latch_db = crng.uniform(-18.0, -13.0)

    dry = DOOR_WHUMP * whump + body + DOOR_FRAME * _norm(frame)
    dry = _norm(dry) + db_to_gain(latch_db) * _norm(latch)

    # 5. Optional swing: the faint air of the door moving before it lands.
    if swing:
        u = np.clip(t / t0, 0.0, 1.0)
        env = (0.5 - 0.5 * np.cos(np.pi * u)) * np.exp(-np.maximum(t - t0, 0.0) / 0.008)
        air = bandlimit(rng.standard_normal(n), sr, 150.0, 1200.0, order=2)
        dry = dry + 0.1 * _norm(air) * env

    # Early reflections: a dozen irregular, darkened copies in the first
    # 4-45 ms (walls, floor, a hallway's far end), different per ear. Many
    # weak, randomly spaced taps rather than a few strong ones, so they blur
    # into a room instead of combing.
    span = (0.018, 0.04, 0.045)[room]
    first = (0.003, 0.004, 0.008)[room]

    def early() -> np.ndarray:
        er = np.zeros(n)
        for _ in range(12):
            d = int(crng.uniform(first, first + span) * sr)
            if d < n:
                er[d:] += crng.uniform(0.08, 0.22) * np.exp(-(d / sr) / 0.035) * dry[: n - d]
        return bandlimit(er, sr, 80.0, 2800.0, order=2)

    # The room's diffuse tail is the shared dark reverb: small room, hallway,
    # large room.
    p["reverb"] = (0.3, 0.36, 0.42)[room]
    p["reverb_decay"] = (0.45, 0.7, 0.9)[room]
    return dry + early(), dry + early()


# -- knock -------------------------------------------------------------------


def _knock(ev: Event, sr: int, rng: np.random.Generator, crng: np.random.Generator, p: dict, seed: int):
    n = max(1, int(ev.dur * sr))
    dur = n / sr
    raps = 2 + seed % 2
    size = (1.0, 0.85, 1.2)[(seed // 2) % 3]
    f0 = float(p["f0"]) / size * crng.uniform(0.95, 1.05)
    ratios = np.array((1.0, 1.59, 2.14, 2.65, 3.61, 4.43)) * crng.uniform(0.97, 1.03, 6)
    t60 = (0.10, 0.08, 0.06, 0.045, 0.035, 0.025)
    gains = (1.0, 0.85, 0.7, 0.5, 0.35, 0.25)

    # Spacing: a natural knock is 0.12-0.22 s apart; fit them in `dur`.
    gap = float(np.clip((dur - 0.15) / max(1, raps - 1), 0.07, crng.uniform(0.15, 0.21)))
    force = np.zeros(n)
    click = np.zeros(n)
    tm = 0.002
    for i in range(raps):
        at = int(tm * sr)
        if at >= n:
            break
        a = crng.uniform(0.8, 1.0) * (1.08 if i == raps - 1 else 1.0)
        width = int(crng.uniform(0.0010, 0.0016) * sr)  # knuckle contact time
        force += a * _pulse(n, at, width)
        click += a * _burst(rng, n, at, int(0.003 * sr), 0.0007, sr)
        tm += gap * crng.uniform(0.92, 1.05)
    panel = _ring(force, f0 * ratios, t60, gains, sr)
    # the whole door moves a little: one low mode under the panel
    door = _ring(force, (crng.uniform(55, 75) / size,), (0.12,), (1.0,), sr)
    click = bandlimit(click, sr, 1200.0, 6000.0, order=4)
    mono = _norm(panel) + 0.25 * _norm(door) + 0.22 * _norm(click)
    return mono, mono


# -- footsteps ---------------------------------------------------------------


def _step_env(n: int, sr: int, at: float, rise: float, tau: float, length: float) -> tuple[int, np.ndarray]:
    """A short envelope (raised-cosine rise, exponential fall), placed at `at`
    s; returns (start sample, envelope) so it can be added in place."""
    a = int(at * sr)
    k = min(n - a, int(length * sr))
    if a < 0 or k < 4:
        return 0, np.zeros(0)
    t = np.arange(k) / sr
    e = np.exp(-t / tau)
    r = min(k, max(2, int(rise * sr)))
    e[:r] *= 0.5 - 0.5 * np.cos(np.pi * (np.arange(r) + 0.5) / r)
    return a, e


def _footsteps(ev: Event, sr: int, rng: np.random.Generator, crng: np.random.Generator, p: dict, seed: int):
    """Someone walking: each step is a heel strike, the sole rolling down and
    the ball of the foot landing 50-120 ms later, then a little scuff as it
    pushes off. The floor is heavily damped, so a step is shaped noise, not a
    ringing tone: a dull low thud (the body's weight into the floor), a
    broadband slap of the sole, a hard heel's click on hard floors, the
    friction of the sole, and on gravel the stones crunching under the whole
    foot. Between footfalls the swinging leg's trousers brush past the
    other leg. The cadence is a human walk (left and right not quite even, every
    step a little different), and the room or street answers.
    """
    n = max(1, int(ev.dur * sr))
    dur = n / sr
    surface = seed % 3  # 0 hard floor, 1 stone, 2 gravel
    pace = (seed // 3) % 3  # slow, walk, brisk
    interval = (0.62, 0.53, 0.44)[pace] * crng.uniform(0.95, 1.05)
    limp = crng.uniform(-0.03, 0.03)  # left/right steps are not quite even
    shoe_hard = (crng.uniform(0.6, 1.0), crng.uniform(0.5, 0.9), 0.3)[surface]

    # Excitation envelopes per component, summed over the steps; each noise
    # band is then filtered once over the whole clip.
    e_thud, e_slap, e_click, e_scuff, e_crunch, e_cloth = (np.zeros(n) for _ in range(6))

    def put(dst, at, rise, tau, length, a):
        s, e = _step_env(n, sr, at, rise, tau, length)
        dst[s : s + len(e)] += a * e

    tm = crng.uniform(0.02, 0.12)
    step = 0
    while tm < dur - 0.2 or step == 0:
        foot = step % 2
        a = db_to_gain(crng.uniform(-2.5, 1.5) - (1.0 if foot else 0.0))
        roll = crng.uniform(0.05, 0.11) * (1.15 if pace == 0 else 1.0)  # heel to ball
        # heel strike: the body's weight lands on the heel
        put(e_thud, tm, 0.002, 0.03, 0.18, a)
        put(e_slap, tm, 0.002, 0.022, 0.12, a)
        put(e_click, tm, 0.0004, 0.002, 0.015, a * shoe_hard)
        # the sole rolls down and the ball lands, much softer: the weight
        # is already on the foot
        b = a * crng.uniform(0.2, 0.35)
        put(e_thud, tm + roll, 0.003, 0.014, 0.1, 0.6 * b)
        put(e_slap, tm + roll, 0.002, 0.014, 0.08, b)
        # the sole rolling flat between the two: a soft, low smear
        put(e_slap, tm + 0.01, roll * 0.6, roll * 0.5, roll * 1.2, 0.25 * a)
        put(e_click, tm + roll, 0.0005, 0.002, 0.015, 0.35 * b * shoe_hard)
        # friction: the sole sliding a little on landing and on push-off
        put(e_scuff, tm + 0.004, 0.006, 0.025, 0.12, a * crng.uniform(0.2, 0.5))
        put(e_scuff, tm + roll + crng.uniform(0.1, 0.18), 0.02, 0.03, 0.12, a * crng.uniform(0.1, 0.35))
        if surface == 2:
            put(e_crunch, tm, 0.002, 0.06, 0.25, a)
            put(e_crunch, tm + roll, 0.004, 0.07, 0.25, 0.8 * b)
        # the swing leg: trousers brushing past the standing leg mid-stride,
        # a soft fabric swish between the footfalls
        put(e_cloth, tm + 0.12 * interval, 0.35 * interval, 0.18 * interval, 0.7 * interval, a * crng.uniform(0.5, 1.0))
        step += 1
        tm += interval * crng.uniform(0.95, 1.05) * (1.0 + (limp if foot else -limp))
        if step > 64:
            break

    lo_f = (crng.uniform(110, 160), crng.uniform(130, 190), crng.uniform(90, 130))[surface]
    thud = bandlimit(rng.standard_normal(n) * e_thud, sr, 45.0, lo_f * 2.2, order=2)
    slap = bandlimit(rng.standard_normal(n) * e_slap, sr, (150.0, 200.0, 150.0)[surface], (1600.0, 2000.0, 1400.0)[surface], order=2)
    click = bandlimit(rng.standard_normal(n) * e_click, sr, 1500.0, 4500.0, order=2)
    scuff = bandlimit(rng.standard_normal(n) * e_scuff, sr, 400.0, 3000.0, order=2)
    cloth = bandlimit(rng.standard_normal(n) * e_cloth, sr, 300.0, 2500.0, order=2)
    mix = (
        2.0 * thud / (np.abs(thud).max() + 1e-12)
        + (0.8, 0.8, 0.4)[surface] * _norm(slap)
        + (0.22, 0.3, 0.05)[surface] * _norm(click)
        + (0.3, 0.35, 0.15)[surface] * _norm(scuff)
        + 0.07 * _norm(cloth)
    )
    if surface == 2:
        # gravel: stones crushed and shifting under the foot, a dense crackle
        # of tiny impacts thinning out over a quarter second
        cnt = int(1800 * dur)
        tt = crng.uniform(0.0, dur, cnt)
        idx = (tt * sr).astype(int)
        amp = e_crunch[idx] * crng.uniform(0.2, 1.0, cnt) ** 2
        grains = np.zeros(n)
        np.add.at(grains, idx, amp * rng.choice((-1.0, 1.0), cnt))
        crunch = bandlimit(grains, sr, 500.0, 6000.0, order=2) + 0.5 * bandlimit(grains, sr, 150.0, 900.0, order=2)
        mix = mix + 1.2 * _norm(crunch)

    # the room (hard floor), a stone passage, or open air over gravel
    first, span, lvl = ((0.004, 0.03, 0.18), (0.006, 0.05, 0.22), (0.008, 0.03, 0.08))[surface]

    def early() -> np.ndarray:
        er = np.zeros(n)
        for _ in range(10):
            d = int(crng.uniform(first, first + span) * sr)
            if d < n:
                er[d:] += crng.uniform(0.4, 1.0) * lvl * mix[: n - d]
        return bandlimit(er, sr, 80.0, 4000.0, order=2)

    p["reverb"], p["reverb_decay"] = (0.3, 0.35, 0.15)[surface], (0.8, 1.0, 0.5)[surface]
    return mix + early(), mix + early()


# -- water drop --------------------------------------------------------------


def _bubble(n: int, sr: int, at: int, f0: float, damp_scale: float = 0.7, rise: float = 0.1) -> np.ndarray:
    """A Minnaert bubble (van den Doel 2005): f(t) = f0 (1 + rise * d * t),
    amplitude exp(-d t), d = 0.043 f0 + 0.0014 f0^1.5. The pitch glides up as
    the bubble nears the surface."""
    out = np.zeros(n)
    if at >= n:
        return out
    d = (0.043 * f0 + 0.0014 * f0**1.5) * damp_scale
    k = min(n - at, int(LN1000 / d * 1.2 * sr))
    t = np.arange(k) / sr
    f = f0 * (1.0 + rise * d * t)
    ph = TAU * np.cumsum(f) / sr
    # a 2 ms raised-cosine onset: a sub-millisecond window on a sine has
    # sidelobes every 1/window Hz, a comb that runs to Nyquist
    a = min(k, max(2, int(0.002 * sr)))
    env = np.exp(-d * t)
    env[:a] *= 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, a))
    out[at : at + k] = np.sin(ph) * env
    return out


def _drip_bubble(n: int, sr: int, at: float, f0: float, amp: float, damp: float = 1.0, rise: float = 0.15) -> np.ndarray:
    """One Minnaert bubble as `_bubble`, with a 0.6 ms onset (a drop's
    bubble is born abruptly, it does not fade in) and the time in seconds."""
    out = np.zeros(n)
    i = int(at * sr)
    if i >= n or i < 0:
        return out
    d = (0.043 * f0 + 0.0014 * f0**1.5) * damp
    k = min(n - i, int(6.0 / d * sr))
    t = np.arange(k) / sr
    a = min(k, max(2, int(0.0006 * sr)))
    env = np.exp(-d * t)
    env[:a] *= 0.5 - 0.5 * np.cos(np.pi * (np.arange(a) + 0.5) / a)
    out[i : i + k] = amp * np.sin(TAU * f0 * (t + 0.5 * rise * d * t * t)) * env
    return out


def _water_drop(ev: Event, sr: int, rng: np.random.Generator, crng: np.random.Generator, p: dict, seed: int):
    """A drop falling into water. The impact is a tiny, sharp, broadband tick
    (well under a millisecond: the drop's own size); a few milliseconds
    later the crater closes over a small air bubble that rings at its
    Minnaert pitch and glides up as it rises, dying within tens of ms (the
    "plink"). The crater's rebound throws up a thin jet whose tip falls back
    as a much smaller droplet a few tens of ms later: a second, fainter,
    higher plink. A larger drop (the plop) also throws a short crown of
    spray and its bigger bubble rings lower and longer."""
    n_ev = max(1, int(ev.dur * sr))
    # everything has died away within 0.6 s: render that much, then pad
    n = min(n_ev, int(0.6 * sr))
    t0 = 0.004
    if seed % 2 == 0:
        # drip: a 3-4 mm drop, bubble ~1 mm: 1.2 - 2.6 kHz
        f0 = crng.uniform(1200.0, 2600.0)
        tick = bandlimit(_burst(rng, n, int(t0 * sr), int(0.002 * sr), 0.0003, sr, rise=0.0002), sr, 1500.0, 11000.0, order=2)
        bub = _drip_bubble(n, sr, t0 + crng.uniform(0.003, 0.008), f0, 1.0, crng.uniform(0.9, 1.2), crng.uniform(0.2, 0.35))
        tj = t0 + crng.uniform(0.05, 0.11)
        jet = bandlimit(_burst(rng, n, int(tj * sr), int(0.0015 * sr), 0.0002, sr, rise=0.0002), sr, 2500.0, 11000.0, order=2)
        bub2 = _drip_bubble(n, sr, tj + 0.002, f0 * crng.uniform(1.4, 2.0), 1.0, 1.1, 0.25)
        mono = _norm(bub) + 0.6 * _norm(tick) + crng.uniform(0.1, 0.3) * (_norm(bub2) + 0.4 * _norm(jet))
    else:
        # plop: a big drop (or a pebble-sized blob), bubble 3-6 mm
        f0 = crng.uniform(550.0, 1100.0)
        tick = bandlimit(_burst(rng, n, int(t0 * sr), int(0.004 * sr), 0.0006, sr, rise=0.0003), sr, 600.0, 10000.0, order=2)
        crown = bandlimit(_burst(rng, n, int(t0 * sr), int(0.05 * sr), 0.008, sr, rise=0.001), sr, 900.0, 8000.0, order=2)
        bub = _drip_bubble(n, sr, t0 + crng.uniform(0.008, 0.016), f0, 1.0, crng.uniform(0.55, 0.75), crng.uniform(0.3, 0.45))
        bub2 = _drip_bubble(n, sr, t0 + crng.uniform(0.02, 0.05), f0 * crng.uniform(1.8, 2.6), 1.0, 1.0, 0.2)
        tj = t0 + crng.uniform(0.09, 0.16)
        bub3 = _drip_bubble(n, sr, tj, f0 * crng.uniform(2.2, 3.0), 1.0, 1.1, 0.25)
        mono = (_norm(bub) + 0.5 * _norm(tick) + 0.35 * _norm(crown) + 0.3 * _norm(bub2)
                + crng.uniform(0.15, 0.3) * _norm(bub3))
    mono = np.pad(mono, (0, n_ev - n))
    return mono, mono


# -- explosion ---------------------------------------------------------------


def _explosion(ev: Event, sr: int, rng: np.random.Generator, crng: np.random.Generator, p: dict, seed: int):
    n = max(1, int(ev.dur * sr))
    dur = n / sr
    t = np.arange(n) / sr
    dist = (0.0, 0.4, 0.85)[seed % 3]
    f0 = float(p["f0"]) * crng.uniform(0.85, 1.15)
    at = 0.002

    # Sub body: the pressure wave, a falling low sine with a fast attack.
    f_sub = f0 * (1.0 + 1.2 * np.exp(-t / 0.06)) * (0.8 + 0.2 * np.exp(-t / max(0.6, 0.3 * dur)))
    sub = np.sin(TAU * np.cumsum(f_sub) / sr) * _attack(n, sr, at, 0.004) * np.exp(-t / 0.45)

    # Blast: broadband noise whose brightness falls fast (fireball to rumble).
    bright = bandlimit(_burst(rng, n, int(at * sr), int(0.6 * sr), 0.07 + 0.03 * dist, sr), sr, 300.0, 9000.0 - 6000.0 * dist, order=2)
    mid = bandlimit(_burst(rng, n, int(at * sr), int(min(dur, 2.0) * sr), 0.35, sr), sr, 90.0, 1600.0, order=2)
    blast = (1.0 - 0.6 * dist) * _norm(bright) + 1.1 * _norm(mid)

    # Rumble: low noise that rolls on, like distant thunder.
    roll = bandlimit(rng.standard_normal(n), sr, 40.0, 260.0, order=2)
    roll_env = _attack(n, sr, at, 0.03 + 0.15 * dist) * np.exp(-t / max(0.25 * dur, 0.3)) * (0.6 + 0.4 * _smooth(crng, n, sr, 2.0))

    # Debris: falling grains and chunks, dense just after the blast.
    span = max(0.2, 0.85 * dur)
    cnt = int(crng.integers(60, 140) * span)
    tt = 0.12 + crng.exponential(span * 0.3, cnt)
    tt = tt[tt < dur - 0.02]
    grains = np.zeros(n)
    np.add.at(grains, (tt * sr).astype(int), rng.standard_normal(len(tt)) * np.exp(-(tt - 0.12) / (span * 0.45)))
    debris = _ring(grains, (crng.uniform(1800, 2600), crng.uniform(3200, 4400), crng.uniform(900, 1300)),
                   (0.012, 0.008, 0.02), (1.0, 0.6, 0.5), sr)
    debris = bandlimit(debris, sr, 600.0, 8000.0, order=4)

    tail = _fade_out(n, sr, min(0.3 * dur, 1.2))
    mono = (0.55 * _norm(sub) + blast + 0.45 * _norm(roll) * roll_env + (0.3 - 0.15 * dist) * _norm(debris)) * tail
    mono = saturate(_norm(mono) * 1.2, 1.6)
    # a second, decorrelated rumble and debris for width
    roll2 = bandlimit(rng.standard_normal(n), sr, 40.0, 260.0, order=2)
    side = 0.35 * (_norm(roll2) - _norm(roll)) * roll_env * tail
    level = 1.0 - 0.3 * dist
    return (mono + side) * level, (mono - side) * level


_FNS = {
    "thunder": _thunder,
    "door_slam": _door_slam,
    "knock": _knock,
    "footsteps": _footsteps,
    "water_drop": _water_drop,
    "explosion": _explosion,
}


def _smooth_lowpass(x: np.ndarray, sr: int, f_pass: float = HI_PASS, f_stop: float = HI, pad: int = 2048) -> np.ndarray:
    """Zero-phase low-pass: flat to `f_pass`, a raised-cosine slope to exactly
    zero at `f_stop`, nothing above. The slope is 3 kHz wide, so the impulse
    response is a fraction of a millisecond long and does not ring; a
    Butterworth of the same corner leaves -24 dB at Nyquist under a hard
    transient, which is what used to fizz up to 24 kHz on every attack."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n == 0:
        return x
    m = n + 2 * pad
    f = np.fft.rfftfreq(m, 1.0 / sr)
    u = np.clip((f - f_pass) / (f_stop - f_pass), 0.0, 1.0)
    mag = 0.5 + 0.5 * np.cos(np.pi * u)
    return np.fft.irfft(np.fft.rfft(np.pad(x, (pad, pad)), m) * mag, m)[pad : pad + n]


def _edges(x: np.ndarray, sr: int) -> np.ndarray:
    """Raised-cosine fades: 1.5 ms in, 12 ms out, both ends exactly zero."""
    n = len(x)
    a = min(n, max(2, int(0.0015 * sr)))
    b = min(n, max(2, int(0.012 * sr)))
    x[:a] *= 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, a))
    x[-b:] *= 0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, b))
    return x


def _finish(x: np.ndarray, sr: int) -> np.ndarray:
    """High-pass, smooth low-pass (after every envelope and attack), remove
    DC, and fade both ends to exactly zero."""
    x = bandlimit(x, sr, LO, None, order=4)
    x = _smooth_lowpass(x, sr)
    return _edges(x - x.mean(), sr)


def render_foley(ev: Event, sr: int, rng: np.random.Generator, p: dict, seed: int, tail: bool) -> np.ndarray:
    """Render one foley event to stereo, shape (n, 2). See `render_event`."""
    idx = EVENT_ROLES.index(ev.role)
    # The variant (distance, surface, door size...) depends on the seed only,
    # not on where the event sits in the cue.
    crng = np.random.default_rng((seed * 2_654_435_761 + idx * 40_503 + 0x0F01E) & 0xFFFFFFFF)
    fn = _FNS.get(ev.role)
    if fn is None:  # the everyday / nature / action library (v0.3)
        from .natural import FNS as _NAT

        fn = _NAT[ev.role]
    left, right = fn(ev, sr, rng, crng, p, int(seed))
    left, right = _finish(left, sr), _finish(right, sr)
    peak = max(float(np.abs(left).max()), float(np.abs(right).max()), 1e-12)
    left, right = left / peak, right / peak

    wet = float(p.get("reverb", 0.0))
    if wet > 0:
        decay = float(p.get("reverb_decay", 0.5))
        s1, s2 = int(rng.integers(1 << 31)), int(rng.integers(1 << 31))
        left = reverb(left, sr, decay=decay, wet=wet, seed=s1, tail=tail)
        right = reverb(right, sr, decay=decay, wet=wet, seed=s2, tail=tail)

    # The reverb follows the band limit; band-limit and fade once more at the
    # very end, so nothing added after `_finish` can reach past HI.
    left = _edges(_smooth_lowpass(left, sr), sr)
    right = _edges(_smooth_lowpass(right, sr), sr)

    # Narrow the image as it is panned, then place the mid with the same
    # constant-power law as the mono roles (centre = 0.707 per channel).
    width = float(np.clip(p.get("width", 0.0), 0.0, 1.0)) * (1.0 - abs(float(ev.pan)))
    mid = 0.5 * (left + right)
    side = 0.5 * (left - right) * width * np.sqrt(0.5)
    out_l, out_r = pan(mid, ev.pan)
    return np.stack([out_l + side, out_r - side], axis=1) * db_to_gain(ev.gain_db)
