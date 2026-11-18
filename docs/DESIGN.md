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
1. **Scheduler Offset Rules (`score.py`)**:
   - `suction`: anticipation sweep with `start = event.time - 0.25s`, `end = event.time` (hard gate at `0.0s` offset right when `crystal` hits).
   - `whoosh` (on scene cuts): `start = event.time - 0.16s`, peak filter cutoff at `event.time`, tail out `+0.18s`.
   - `sub` + `impact`: lock `sub.time === impact.time === cut.time` with `0 ms` offset between them (stacked vertically on the X-ray HUD).
   - Climax & fade-out: trigger final `riser` from `12.85s -> 13.40s` into `impact` at `13.40s` for the brand reveal; zero new triggers after `15.40s`.
2. **4 Core Synth Presets (`voices.py`)**:
   - `whoosh` / `suction`: pink noise -> **24 dB/oct resonant Low-Pass Filter** (`Q = 2.2`) sweeping exponentially `140 Hz -> 3.4 kHz` (`suction`) or `2.6 kHz -> 120 Hz` (`whoosh`).
   - `impact` + `sub`: sum a **sine sub-drop** (`92 Hz -> 36 Hz` over `190 ms`) + a **triangle mid-punch** (`165 Hz -> 62 Hz` over `55 ms`) + a **`5 ms` high-passed click** (`> 2.2 kHz`) through a soft-clipper (`tanh`).
   - `text_tick` (`tick`, split from `pluck`): ultra-short (`18–30 ms`) bandpass-filtered noise (`1.4 kHz – 2.8 kHz`) + stationary damped resonator (`3 ms` attack, `15 ms` exponential decay, `+-3 dB` velocity jitter, **zero sine pitch drop**). Keep stationary pitched marimba `pluck` strictly for **1 hero arrival per scene**.
   - `crystal`: layer two detuned high-frequency sine/triangle partials (`2,093 Hz` + `3,136 Hz`, `+7 cents` detune) with a `120 ms` glassy decay and stereo shimmer.
3. **Continuous Motion Bed (`telemetry.py` + `foley.py`)**:
   - Export `motion_energy` (`0.0 – 1.0` per frame from bbox velocity + morph delta) and `pan_x` (`-1.0` to `+1.0`).
   - Drive a continuous warm filtered noise + root-fifth drone bed through an LPF (`cutoff = 180 Hz + motion_energy * 1400 Hz`, `gain = -34 dB + motion_energy * 16 dB`, panned by `pan_x`).
4. **Global Spectral Tilt & Space (`master.py`)**: Master bus runs `12%` wet short room reverb (`0.35s` decay, high-passed at `300 Hz`) -> wide bell cut at **`2.5 kHz` (`-4 dB`, `Q = 1.0`)** -> low shelf boost at **`75 Hz` (`+3 dB`)** -> 2:1 glue -> `-16 LUFS` -> `-1.0 dBTP` true-peak limiter.

## Product & Evolution Preferences
- Keep every evolution version (`v0.1`..`v0.5`; old 6 s `v0.1` launch stub removed and versions renumbered so `v0.1` = Showreel, `v0.2` = Scene sound, `v0.3` = Reel II, `v0.4` = Agency Reel, `v0.5` = Launch).
- Published versions `v0.1`, `v0.2`, and `v0.3` in `docs/media/` are frozen; new breakthroughs ship as new versions in `docs/versions.json`.
- Elevate UX, DX, and AX simultaneously: readable zero-clutter M3 Expressive site, one-command media build, deterministic JSON-in/JSON-out CLI and RSI loop for agents.
- Docs are never duplicated. State lives in `STATUS.md`, rules here, agent manual in `AGENT.md`. Extend in place; pick up where the last session ended.

## Site copy rule
No taglines, helper text or secondary labels in tiles or tables; if a screen needs them, fix the layout. Tables carry numbers only.


## Owner preferences (session 7)
- No box shadows (3D uses flat shading only), no emojis, no status badges, no blue/purple gradients. Cut taglines, helper text and secondary labels: fix the layout instead.
- Best decision for UX, DX and AX at once, without breaking anything. Demos must be 30 s+ and differ in category, palette and format. 3D is part of the pipeline.
- The paid prompt-to-video product starts as static GitHub Pages (`docs/create/`); keep it client-side until a render worker exists.

## Owner preferences (session 8)
- Different demo videos, 5+, longer (45 s+), each with a different category, palette, format and hero 3D object. Never reuse the same objects every time.
- 3D must look real: lit rounded solids, torus, extrusions, textured screens; real UI on devices; real photos and real footage; polish over quantity.
- Best motion skill for any agent: `docs/SKILL.md` v2 is the contract; fix patterns in the kit, never twice in demos.
- Product direction: a paid prompt-to-video tool for businesses, startups, apps and services. It starts as the static GitHub Pages Create page (`docs/create/`), client-side, until a render worker exists.
- RSI: every defect found in a contact sheet becomes a rule in SKILL.md, a kit default, or a test.
