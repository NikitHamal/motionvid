"""Mix the three decoders into one stereo cue, with stems."""

from __future__ import annotations

import numpy as np

from ..grammar import DEFAULT_BED_DB
from ..score import AMBIENCE_TEXTURES, Score
from .dsp import db_to_gain, rms
from .events import FOLEY_ROLES, render_event
from .music import render_track
from .texture import render_texture

END_FADE = 0.01  # s

# The neural detail stage was trained on the original ten roles and eight
# noise beds. The physical models (every foley, nature, everyday and action
# role) and the scene beds are rendered at full band already, and the stage
# can only blur them, so they bypass it: see `apply_detail_routed`.
DSP_ONLY_ROLES = frozenset(FOLEY_ROLES)
DSP_ONLY_TEXTURES = frozenset(AMBIENCE_TEXTURES)


def _add_at(out: np.ndarray, sig: np.ndarray, t: float, sr: int) -> None:
    start = max(0, int(round(t * sr)))
    end = min(len(out), start + len(sig))
    if end > start:
        out[start:end] += sig[: end - start]


def _active_ref(x: np.ndarray, sr: int, frame: float = 0.05) -> float:
    """Loudness reference: 95th percentile of active-frame RMS.

    Whole-cue RMS depends on duty cycle, so a sparse cue gets boosted far more
    than a dense one: the same -30 dB bed lands 26 dB louder in a one-pop cue
    than in a five-event one. Measuring only the frames that carry signal keeps
    the foreground loudness stable across cue densities.
    """
    mono = x.mean(axis=1) if x.ndim > 1 else x
    win = max(1, int(frame * sr))
    hop = max(1, win // 2)
    if len(mono) < win:
        return float(np.sqrt(np.mean(mono**2) + 1e-12))
    frames = np.lib.stride_tricks.sliding_window_view(mono, win)[::hop]
    fr = np.sqrt(np.mean(frames**2, axis=1) + 1e-18)
    peak = float(fr.max())
    if peak <= 1e-9:
        return 0.0
    active = fr[fr > 0.05 * peak]
    return float(np.percentile(active, 95)) if active.size else 0.0


def render_stems(score: Score, normalize: bool = True) -> dict[str, np.ndarray]:
    """Render a score to separate stems plus a mix.

    Returns a dict with `music`, `texture`, `events`, and `mix`, each (n, 2)
    float32. The stems sum to the mix, and every stem receives the same safety
    gain, so the stems always reconstruct it.
    """
    score.validate()
    sr = score.sample_rate
    n = int(score.duration * sr)
    music = np.zeros((n, 2), dtype=np.float64)
    texture = np.zeros((n, 2), dtype=np.float64)
    events = np.zeros((n, 2), dtype=np.float64)
    # The part of `texture` and `events` that bypasses the detail stage.
    # Tracked separately so the sums above stay bit-identical.
    tex_dsp = np.zeros((n, 2), dtype=np.float64)
    ev_dsp = np.zeros((n, 2), dtype=np.float64)

    for i, track in enumerate(score.music):
        music += render_track(track, sr, n, seed=score.seed + i)
    for i, tex in enumerate(score.textures):
        clip = render_texture(tex, sr, seed=score.seed + 100 + i)
        _add_at(texture, clip, tex.t, sr)
        if tex.character in DSP_ONLY_TEXTURES:
            _add_at(tex_dsp, clip, tex.t, sr)
    for i, event in enumerate(score.events):
        seed = event.seed if event.seed else score.seed + 200 + i
        # tail=True: reverb rings out past the event instead of being cut.
        clip = render_event(event, sr, seed=seed, tail=True)
        _add_at(events, clip, event.t, sr)
        if event.role in DSP_ONLY_ROLES:
            _add_at(ev_dsp, clip, event.t, sr)

    # Each texture removes its own DC before its edge fades (render_texture);
    # removing the stem mean here would put a step back at sample 0.
    music -= music.mean(axis=0, keepdims=True)

    # A reverb tail or a note that runs past the end of the cue is cut there;
    # fade the last few ms so the cut is not a step.
    b = min(n, int(END_FADE * sr))
    if b > 1:
        ramp = np.linspace(1.0, 0.0, b)[:, None]
        events[n - b :] *= ramp
        music[n - b :] *= ramp
        ev_dsp[n - b :] *= ramp

    if normalize:
        # The foreground sets the loudness; the bed is placed relative to it.
        # Normalising the whole mix instead lets the bed absorb the gain the
        # foreground did not use, which is what made sparse cues hiss.
        fg = music + events
        target = db_to_gain(score.target_lufs)
        fg_peak = float(np.abs(fg).max()) if fg.size else 0.0

        if fg_peak > 1e-6:
            # SFX convention: the foreground peaks just under full scale.
            g_fg = 0.89 / fg_peak
            # The bed sits `gain_db` below the foreground's *active* loudness,
            # so its level does not depend on how sparse the events are.
            fg_ref = _active_ref(fg, sr) * g_fg
            bed_db = score.textures[0].gain_db if score.textures else DEFAULT_BED_DB
            bed_target = fg_ref * db_to_gain(bed_db)
            tex_rms = max(rms(texture), 1e-9)
            g_tex = min(bed_target / tex_rms, fg_ref / tex_rms)
        else:
            # Ambience-only cue: the bed is the sound, so it takes the target.
            g_fg = 0.0
            tex_rms = max(rms(texture), 1e-9)
            g_tex = target / tex_rms
            tex_peak = float(np.abs(texture).max())
            if tex_peak > 1e-9:
                g_tex = min(g_tex, 0.89 / tex_peak)

        music *= g_fg
        events *= g_fg
        texture *= g_tex
        ev_dsp *= g_fg
        tex_dsp *= g_tex

    mix = music + texture + events

    # One safety gain for every stem, so they still sum to the mix.
    peak = float(np.abs(mix).max()) if mix.size else 0.0
    if peak > 0.98:
        s = 0.98 / peak
        music *= s
        texture *= s
        events *= s
        mix *= s
        ev_dsp *= s
        tex_dsp *= s

    return {
        "music": music.astype(np.float32),
        "texture": texture.astype(np.float32),
        "events": events.astype(np.float32),
        "mix": mix.astype(np.float32),
        # Not a stem of its own (it overlaps `texture` and `events`): the
        # share of the mix that skips the detail stage.
        "dsp_only": (ev_dsp + tex_dsp).astype(np.float32),
    }


def apply_detail_routed(stems: dict[str, np.ndarray], detail, seed: int = 0, strength: float = 1.0) -> np.ndarray:
    """Run the detail stage on the part of the mix it was trained on.

    The physical-model roles and the scene beds (`stems["dsp_only"]`) are
    added back after the stage, untouched. A cue without them goes through
    exactly the original path, so its output is bit-identical to before.
    """
    from .detail import apply_detail  # torch: imported only when used

    mix = stems["mix"]
    keep = stems.get("dsp_only")
    if keep is None or not np.any(keep):
        return np.asarray(apply_detail(mix, detail, seed=seed, strength=strength), dtype=np.float32)
    rest = mix - keep
    if not np.any(np.abs(rest) > 1e-7):
        return mix.astype(np.float32)
    out = np.asarray(apply_detail(rest.astype(np.float32), detail, seed=seed, strength=strength), dtype=np.float64) + keep
    peak = float(np.abs(out).max()) if out.size else 0.0
    if peak > 0.98:
        out *= 0.98 / peak
    return out.astype(np.float32)


def render(
    score: Score,
    normalize: bool = True,
    detail=None,
    detail_strength: float = 1.0,
) -> np.ndarray:
    """Render a score to stereo float32, shape (n, 2).

    `detail` is an optional `DetailUNet`; when given, the neural detail stage
    runs after the DSP mix and before the result is returned.
    """
    stems = render_stems(score, normalize)
    if detail is None:
        return stems["mix"]
    # The physical models and scene beds bypass the detail stage.
    return apply_detail_routed(stems, detail, seed=score.seed, strength=detail_strength)
