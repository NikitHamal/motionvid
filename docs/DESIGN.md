# Design rules and owner preferences (single source; tests in tests/test_rules.py and tests/test_scene.py enforce what can be enforced)

## Visual & UI Hard Rules
- No box shadows or text shadows. No emojis anywhere (UI, docs, code). No LIVE badges. No blue or purple gradients.
- Palette: cream (`#F6EFE3`), ink (`#17130F`), coral (`#FF6A45`), lime (`#C9F13B`), butter (`#FFD54A`), pink (`#FF9DBB`), mint (`#3DDBA7`). Font: Bricolage Grotesque.
- Cut taglines, helper text and secondary labels. If a screen needs them to make sense, fix the layout instead.
- A corner is never unrounded, not even for one frame. Radius transitions use `--ease-shape` (no overshoot) and only between two real radii;
  never animate a radius from or to `--shape-full` (999px); springs may animate transforms only.
- Play/pause is one button driven by `data-playing`, never by `hidden` on inline svg.
- The GitHub button carries the GitHub mark. Nav hover and press animations stay (rounded-to-rounded shape morph).
- Material 3 Expressive: solid containers, extra-large shapes, spring motion, big type.

## Agency DSP & Audio Synthesis Rules
1. **No Pure Sine/FM Bells (`1.2–3.5 kHz`)**: Use a **120 ms damped triangle/saw marimba body** (`180–420 Hz`, low-pass filter closing `1.8 kHz -> 300 Hz` over `90 ms`) + a **6 ms woody click transient** (`800–2200 Hz` bandpass impulse).
2. **Strict 3-Voice Burst Polyphony Budget & Cooldown (`110 ms`)**: Never sonify individual particles or oscillating bars one-to-one. Collapse multi-element bursts within `400 ms` into **at most 3 staggered low-mid voices** (`0 dB`, `-5 dB`, `-10 dB`, `>= 110 ms` spacing), tucking mini-blobs `-15 dB` to `-25 dB` behind hero transients. Mute individual oscillating bar triggers in favor of one composite continuous low-pass brush/elastic sweep.
3. **Never Emit Bandpass Noise Without a Sub-Layer**: Every transition whoosh sums two locked layers:
   - **Air layer**: Pink noise through a low-`Q` (`Q = 1.2`) low-pass filter sweeping `250 Hz -> 1.6 kHz -> 200 Hz`.
   - **Weight layer**: Sine wave sweeping `90 Hz -> 42 Hz` over `220 ms` peaking right on the cut frame.
4. **Constrain Pitch Sweeps to Realistic Physics (`<= 4` Semitones)**: Cap scale/pop pitch envelopes to `+2 to +4 semitones` over `35–60 ms` (`pop`), harmonic risers to `<= 4 semitones`, and heavy impacts/sub-drops to `-5 to -12 semitones` over `180–300 ms`. No upward cartoon laser chirps.
5. **Global Spectral Tilt & Space**: Master bus runs `12%` wet short room reverb (`0.35s` decay, high-passed at `300 Hz`) -> wide bell cut at **`2.5 kHz` (`-4 dB`, `Q = 1.0`)** -> low shelf boost at **`75 Hz` (`+3 dB`)** -> 2:1 glue -> `-16 LUFS` -> `-1.0 dBTP` true-peak limiter.

## Product & Evolution Preferences
- Keep every evolution version (`v0.1`..`v0.5`; old 6 s `v0.1` launch stub removed and versions renumbered so `v0.1` = Showreel, `v0.2` = Scene sound, `v0.3` = Reel II, `v0.4` = Agency Reel, `v0.5` = Launch).
- Published versions `v0.1`, `v0.2`, and `v0.3` in `docs/media/` are frozen; new breakthroughs ship as new versions in `docs/versions.json`.
- Elevate UX, DX, and AX simultaneously: readable zero-clutter M3 Expressive site, one-command media build, deterministic JSON-in/JSON-out CLI and RSI loop for agents.
- Docs are never duplicated. State lives in `STATUS.md`, rules here, agent manual in `AGENT.md`. Extend in place; pick up where the last session ended.
