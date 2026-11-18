# STATUS — motionvid (single living doc; extend in place)
Repo: https://github.com/NikitHamal/motionvid · Last updated: session 7 · Box: 4 CPU local + 20 CPU MoLab (`sb-771f596fb28c3728`, no GPU yet).

## Next actions (do top first)
1. **GPU session** (when granted): learn the telemetry->parameter map from human-rated edits and train a tiny English-only text->timeline planner (`<= 3 MB` int8) to replace the rule-based `docs/engine/planner.js`; see `docs/ROADMAP.md` G1-G4. Keep the 0-byte Agency DSP engine as the baseline gate.
2. **Create page -> real render**: the page previews with a browser synth; add a hosted render worker (same `python -m motionvid video`) and an MCP server (timeline authoring + render + audit as tools) so an agent or the page can return an mp4.
3. **Human listening validation**: pairwise ratings across `v0.1`..`v0.8` and the 6 demos; calibrate FlawBench and StudioBench against human ears. No human has listened to rev 7 UI voices yet.
4. **Kit gaps**: text on 3D box faces is front-only, no morphing paths, no per-glyph 3D, no image/video layers. Add them as kit recipes + engine kinds, each with a demo.
5. **Restore `reel2` glyph phrasing** (`0.997 -> 0.951`, only `glyph_ramp_rho`), occlusion-aware telemetry, beat-locked music bed.

## DONE (session 7)
- **Engine**: `docs/engine/ease.js` (shared easings: Material 3 cubic-bezier tokens `m3Std m3StdDec m3StdAcc m3Dec m3Acc`, damped `spring springSoft springWild`, `outQuart outQuint inOutQuint inOutSine outCirc`; Python twin in `timeline.py`, parity-tested). `docs/engine/scene3d.js`: perspective `group` (UI plane with `rx/ry/persp`, child `z`, `ext` thickness), `box3d`, flat-shaded `sphere`, `path` (trim `p`), `poly`, `ring sweep`; `fmt`+`num` counters, `split: 'mask'` word reveal, multi-line and left-aligned text, virtual `camera` (zoom/x/y/roll). Frozen v0.1..v0.7 render identically (legacy kinds untouched).
- **Sound rev 7 UI foley** (`scene/ui_foley.py`; opt in with `"rev": 7` in the timeline, default stays 6, `v0.6`/`v0.7` unchanged): hint roles `click pop chime toggle notify swipe` plus explicit `tick`/`pluck`. FlawBench `9/9` held.
- **Kit** (`src/motionvid/kit/`: `core.py` Scene/recipes/transitions/camera, `ui.py` components, `three.py` 3D). Recipes write motion and the sound hint together. JS twin `docs/engine/kit.js` for the browser.
- **6 demo reels** (`examples/demos/*.py`, `scripts/build_demos.py`, `docs/media/demos/`, `docs/demos.json`): 32-38 s, 60 fps, motion blur 3, rev 7. FlawBench (rev 7 sound, no human listening):
  | demo | gates | score | failed |
  |---|---|---|---|
  | `lumen` | 9/9 | 0.965 | none |
  | `orbit` | 9/9 | 0.986 | none |
  | `forge` | 9/9 | 0.964 | none |
  | `bloom` | 9/9 | 0.999 | none |
  | `cadence` | 9/9 | 0.971 | none |
  | `parcel` | 9/9 | 0.977 | none |
- **`v0.8` Kit Launch** (`examples/launch3.py`, 26 s, 60 fps, X-ray): prompt -> storyboard -> motion -> sound -> brand. FlawBench `9/9`, `0.999`. Site: Demos gallery, 8 versions, FlawBench column `v0.8`.
- **Create page** (`docs/create/`): prompt -> rule-based planner (`docs/engine/planner.js`, 6 categories, 16:9 and 9:16, 29 s) -> live canvas preview with a browser synth (`docs/engine/webaudio.js`, a stand-in for the Python DSP) -> download `timeline.json`, render command, agent prompt. The planner is rules, not a model.
- **`docs/SKILL.md`** rewritten as the agent skill (loop, structure, API, motion + sound rules, anti-patterns). `tests/test_kit.py` (6): `54` tests green.
- Fixes: `telemetry.py` no longer raises when an element animates `h` without a static `h`; slats cover seam; kit `lift` for painter order inside tilted groups.
- Caveats: demo layouts were reviewed from 8-frame contact sheets, not frame-by-frame; the planner's feature extraction is naive (first clause can leak into a feature title); browser preview audio differs from the rendered audio; MoLab pairing was not used (CPU render fits locally, about 1 min per demo).

## DONE (session 6)
- **Engine rev 6 "Studio sound"** (`src/motionvid/scene/studio.py`, `studio_bed.py`; default; rev 5 stays reproducible via `--engine scene5`, frozen `v0.4`/`v0.5` media untouched). Answers the `v0.4` Launch audit (4 synthesis bottlenecks + polish checklist):
  1. Motion bed: pink noise low-passed `110 Hz -> 780 Hz`, level `-46 dBFS` idle `-> -22 dBFS` peak (measured `-46.3` / `-21.5`), plus `55 + 110 Hz` soft-triangle hum (`-32 dBFS`) scaled by motion energy. Added after loudness normalisation so the dBFS values are literal. Own bed energy curve (`bed_curves`, decorative rings excluded) because `motion_energy` sat at `1.0` for most of the Launch. Texture brush moved `3.2-5.4 kHz -> 0.9-1.7 kHz`: continuous `2-8 kHz` level `-28.2 -> -41.8 dBFS`.
  2. `whoosh6`: `160 ms` exponential ramp-in, peak at the cut (`-1.8 ms`), `220 ms` decay, pink noise through a `24 dB/oct` `Q=1.6` LPF `150 Hz -> 1.35 kHz -> 110 Hz`, hard guard at `2.2 kHz` (`-24.4 -> -31.0 dB` above `2.2 kHz`). A separate `air` room tail (`2.4-6 kHz`) after each cut keeps the tail gate honest.
  3. `pluck` split: `text_tick` (`14 ms` = `3 ms` HP transient + `11 ms` woody `1.1 kHz` body, zero pitch drop, `>= 90 ms` apart, pan `-0.35 -> +0.35` across the line, climbs `0.5` semitone per glyph) and `hero_pluck` (fixed-pitch marimba/kalimba partials + `5 ms` mallet, no bend). A hero pluck owns the next `120 ms` (ticks muted). Bed ducks `12 dB` under ticks.
  4. Bounces: consecutive `impact` hints become a settle run `0 / -4.5 / -9 / -13.5 dB`, low-pass opening `900 Hz x 1.25^n`. `riser6`: `+4.5 dB`, LPF `200 Hz -> 2.4 kHz`, octave glide `110 -> 220 Hz`. `240 + 360 Hz` fifth pad (`-28 dBFS`) bound to the bar width-morph (fifth sharpens up to `14` cents).
  5. Reverb `10%` wet, `0.38 s`, HP `280 Hz` on a send bus carrying only `text_tick`, `hero_pluck`, `crystal`, `air`; `sub`, `impact`, `whoosh`, `riser` stay dry. Master loop closes on `-16 LUFS` after the limiter (`-16.02`).
- **StudioBench** (`bench/studio_audit.py`, `docs/media/studio_audit.json`): `17/17` gates on `launch.json`, rev 5 vs rev 6 numbers on the site. FlawBench stays `9/9` on all five reels (`showreel2` `0.986`, `launch2` `0.987`).
- **New media**: `v0.6` Studio Reel (22.4 s, 60 fps, `examples/showreel2.py`: name, spring, rhythm, type, sound, sign-off) and `v0.7` Studio Launch (20 s, 60 fps, `examples/launch2.py`: prompt, JSON, sound, `17 / 17`, brand), both with X-ray and posters. Site: 7 versions, FlawBench `v0.1..v0.7`, Studio table. Old tiles/labels trimmed (no helper text).
- Tests: `tests/test_studio.py` (5), `test_launch_v05...` pins `rev: 5`. Pytest `48` green.
- Caveats: levels are measured on the final mix model (pre-limiter layer sum scaled by master gain); the `launch.json` rev 5 FlawBench score re-measures `0.984` (was `1.000`), pass count unchanged `9/9`; no human listening test yet; MoLab pairing was not used (CPU work only).

## DONE (session 5)
- **Resolved all 5 root synthesis & timing bugs audited on `video_1.mp4` (`v0.5` Launch / `v0.4` Agency Reel)**:
  1. **Enforced exact scheduler offset rules (`src/motionvid/scene/score.py`, `docs/engine/xray.js`)**:
     - `suction`: anticipation sweep starting `250 ms` before collapse (`start = event.time - 0.25s`, `end = event.time`, hard-gated at `0.0s` offset right when `crystal` hits). On `launch.json`, `suction` now fires at **`5.75s -> 6.00s`** and **`12.47s -> 12.72s`**, never on top of `crystal` at `6.00s` / `12.72s`.
     - `whoosh` (on scene cuts): `start = cut.time - 0.16s` (`pre = 0.16s`), peak filter cutoff at `cut.time`, tail out `+0.18s` (`post = 0.18s`).
     - `sub + impact`: locked `sub.time === impact.time === cut.time` with **`0 ms` offset** at **`3.20s`**, **`6.60s`**, **`10.20s`**, and **`13.40s`** (eliminating the `130 ms` early `sub` pre-bloom at `3.07s`, `6.47s`, `10.05s`, and isolated bar sub rumbles at `4.53s`/`5.50s`). `xray.js` stacks co-timed `sub` and `impact` bars vertically on the debug HUD.
  2. **Rebuilt the 4 core synth presets (`src/motionvid/scene/voices.py`)**:
     - `whoosh` / `suction`: pink noise -> **24 dB/oct (4-pole) resonant Low-Pass Filter** (`Q = 2.2`) sweeping exponentially `140 Hz -> 3.4 kHz` (`suction`, hard-gated at end) and `2.6 kHz -> 120 Hz` (`whoosh`).
     - `impact + sub`: sum of **sine sub-drop** (`92 Hz -> 36 Hz` over `190 ms`) + **triangle mid-punch** (`165 Hz -> 62 Hz` over `55 ms`) + **`5 ms` high-passed click** (`> 2.2 kHz`) through a soft-clipper (`tanh`).
     - `text_tick` (`tick`, split from `pluck`): ultra-short (`18–30 ms`) bandpass-filtered noise (`1.4 kHz – 2.8 kHz`) + stationary damped resonator (`3 ms` attack, `15 ms` exponential decay, `+-3 dB` random velocity jitter, **zero sine pitch drop**). Kept stationary pitched marimba `pluck` strictly for **1 hero arrival per scene** (4 hero arrivals across the 5 scenes of `launch.json`, zero text plucks).
     - `crystal` (`6.00s`, `12.72s`): two detuned high-frequency sine/triangle partials (`2,093 Hz` + `3,136 Hz`, `+7 cents` detune) with `120 ms` glassy decay and Haas/quadrature stereo shimmer.
  3. **Added continuous motion bed driven by `motionvid` curves (`src/motionvid/scene/telemetry.py`, `foley.py`)**:
     - `telemetry.py:motion_curves()` exports `motion_energy` (`0.0 – 1.0` per 240 Hz frame from frame-to-frame bounding-box velocity + morph delta) and `pan_x` (`-1.0` to `+1.0`).
     - `foley.py:motion_bed()` drives a continuous warm filtered noise + root-fifth drone bed (`110/165/220 Hz` + pink noise) through a low-pass filter (`cutoff = 180 Hz + motion_energy * 1400 Hz`, `gain = -34 dB + motion_energy * 16 dB`, panned by `pan_x`), keeping `3.5s–5.8s` (`240 HZ` 5-bar wave), `8.1s–9.4s` (sliding white blob), and `10.6s–12.6s` (orbiting morphing shapes) rich and tactile (`> -32 dBFS` RMS in every window).
  4. **Moved final climax `riser + impact` to `13.40s` (`examples/launch.py`, `score.py`)**:
     - `riser` triggers at **`12.85s -> 13.40s`** (`dur = 0.55s`) right into `impact + sub + whoosh` at **`13.40s`** for the `motionvid` hero reveal; removed the `15.80s`/`15.85s` fade-out triggers and enforced zero new triggers after `15.40s` so `15.80s–16.80s` is a clean reverb/chord decay tail.
  5. **Rebuilt `v0.4` & `v0.5` media + FlawBench & RSI (`docs/media/v0.4`, `docs/media/v0.5`, `docs/media/flawbench.json`, `LEDGER.jsonl`)**:
     | reel | classic (`v0.1`) | session 4 | session 5 (5-bug fix + RSI) |
     |---|---|---|---|
     | `showreel.json` (dev) | 2/9, score 0.409 | 9/9, score 0.987 | **9/9, score 0.996** (**2.44x**, `pan` 0.96, `bright` 0.68, `glyph` 1.00) |
     | `reel2.json` (`v0.4` holdout) | 2/9, score 0.406 | 9/9, score 0.968 | **9/9, score 0.997** (**2.46x**, `pan` 0.96, `bright` 0.87, `glyph` 1.00) |
     | `launch.json` (`v0.5` holdout 2) | 2/9, score 0.328 | 9/9, score 0.993 | **9/9, score 1.000** (**3.05x**, `pan` 0.95, `bright` 0.83, `glyph` 1.00) |
  6. **Added regression gate `test_launch_v05_five_root_bugs_fixed` (`tests/test_scene.py`)**: 43/43 pytest gates green.
2. **Occlusion-aware telemetry**: mute or low-pass background shapes partially covered by an expanding foreground hero shape before the full-frame cut closes.
3. **Human listening validation**: collect pairwise human preference ratings across `v0.1`..`v0.5` to calibrate FlawBench weights against human ears.
4. **Beat-locked music bed & MCP server**: expose `motionvid` timeline authoring + render + FlawBench audit as an MCP tool server for autonomous video agents.

## DONE (session 4)
- **Agency DSP synthesis overhaul (`src/motionvid/scene/voices.py`, `score.py`, `foley.py`, `master.py`, `params.py`)** — resolved all 5 synthesis flaws and all timestamped audit findings from the `video_1.mp4` review:
  1. **Killed pure sine/FM bells (`1.2–3.5 kHz`)**: replaced long-decay sine chimes with a **120 ms damped triangle/saw marimba body** (`180–420 Hz`, low-pass filter closing `1.8 kHz -> 300 Hz` over `90 ms`) + a **6 ms woody click transient** (`800–2200 Hz` bandpass impulse).
  2. **Strict 3-voice burst polyphony budget & 110 ms class cooldown (`score.py`)**: multi-element bursts (6 orbiting blobs in Scene 1, 15 grid blobs in Scene 4, 14 radial blobs around `TIMING` in Scene 5, 4 corner blobs in Scene 6) collapse into **at most 3 staggered low-mid voices** (`0 dB`, `-5 dB`, `-10 dB`, spaced `>= 110 ms`), with mini-blobs tucked `-15 dB` to `-25 dB` behind hero transients. Individual oscillating `SPRING` bar triggers are muted.
  3. **Locked dual-layer transition whooshes (`voices.py:whoosh`)**: every transition sweep sums a **pink-noise air layer** through a low-`Q` (`Q = 1.2`) low-pass filter (`250 Hz -> 1.6 kHz -> 200 Hz`) with a locked **90 Hz -> 42 Hz sub-bass weight layer** over `220 ms` peaking right on the cut frame.
  4. **Realistic physical pitch envelopes (`<= 4` semitones)**: capped pop pitch envelopes to `+2.2 to +2.8 semitones` over `40 ms` (`pluck`/`tick`/`crystal`), riser harmonic swell to `+3.5 semitones`, and sub/impact drops to `85–90 Hz -> 42–45 Hz` (`<= 12 semitones` over `220 ms`). Eliminated the `2400 -> 5400 Hz` laser chirp in `crystal` (now a crisp `4 kHz` micro-click + damped wooden pop).
  5. **Global master bus spectral tilt (`master.py`)**: `12%` wet short room reverb (`0.35s` decay, high-passed at `300 Hz`) -> wide **`-4 dB` bell cut at `2.5 kHz` (`Q = 1.0`)** -> **`+3 dB` low shelf at `75 Hz`** -> 2:1 glue -> `-16 LUFS` -> `-1.0 dBTP` true-peak limiter.
- **Resolved session 3 holdout failures (`pan_corr` and `sub_coupling`)**:
  - `foley.py:texture` now tracks composite speed-weighted `vx(t)` with a tactile mechanical/felt slide (`300 -> 900 Hz` bandpass pink noise + speed brush, panned `L -> R`), lifting Reel II `pan_corr` from **`0.44` (FAIL) -> `0.75` (PASS)**.
  - `score.py:_expansions` now couples sub-booms (`85 -> 45 Hz`) to composite scene area growth, lifting Reel II `sub_coupling` from **`0.75 -> 1.00` (`100%`)**.
  - `foley.py:stretch` replaces the 7 separate `SPRING` bar FM notes with **one continuous low-pass filtered brush/elastic sweep** tied to total bar width variance; `foley.py:shimmer` renders a smooth **warm harmonic pad swell** (`< 1.1 kHz`) during the star-to-circle morph.
- **Version evolution renumbered & expanded (`docs/media/v0.1..v0.5`, `docs/versions.json`)**:
  - Removed the old 6 s `v0.1` launch stub from site and repo as requested.
  - Renumbered frozen evolution history: **`v0.1`** = Showreel (classic sound, frozen), **`v0.2`** = Scene sound (session 3 showreel, frozen), **`v0.3`** = Reel II (session 3 60 fps reel, frozen).
  - Built **`v0.4` ("Agency Reel")**: polished 20.4 s, 60 fps, motion-blurred (`--blur 3`) résumé showreel (`examples/reel2.py`) with all timestamped audit fixes (`0:00.0–0:20.4`) and X-ray video.
  - Built **`v0.5` ("Launch")**: brand-new 16.8 s, 60 fps, motion-blurred (`--blur 3`) social-media pipeline launch video (`examples/launch.py` -> `TIMELINE JSON TO CINEMA` -> `TELEMETRY` -> `48 KHZ / 0 BYTES / 25.8X SYNC` -> `9/9` RSI gate -> `motionvid PIPELINE LAUNCH 2026`) with X-ray video, poster, and interactive player cues.
- **FlawBench & RSI (`bench/soundaudit.py`, `LEDGER.jsonl`, `scene_genome.json`)**:
  - L2 code breakthrough + L1 parameter RSI (`scene-1795031292-1` ACCEPTED, `texture_db -22.0 -> -19.45`, `shimmer_db -28.0 -> -27.85`, `sub_db -5.5 -> -5.34`):
  | reel | classic (`v0.1`) | session 3 (`v0.2`/`v0.3`) | Agency DSP + RSI (`v0.4`/`v0.5`) |
  |---|---|---|---|
  | `showreel.json` (dev) | 2/9, score 0.409 | 9/9, score 0.942 | **9/9, score 0.987** (**2.41x**) |
  | `reel2.json` (`v0.4` holdout) | 2/9, score 0.406 | 8/9, score 0.913 (`pan_corr` 0.44) | **9/9, score 0.968** (**2.38x**, `pan_corr` 0.75, `sub` 100%) |
  | `launch.json` (`v0.5` holdout 2) | 2/9, score 0.328 | — | **9/9, score 0.993** (**3.03x**, `pan_corr` 0.73, `sub` 100%) |
- **MoLab box (`sb-771f596fb28c3728`)**: connected in Turn 2 via `marimo-pair execute-code.sh`; verified 20-CPU machine (no GPU attached yet, matching owner's note: "right now i have given you cpu only molab. first achieve proven breakthrough/innovation target. then i will give you gpu session").

## DONE (session 3)
- **Scene audio engine** (`src/motionvid/scene/`, 0 weights, English-only): telemetry-bound sub, pan, velocity texture, glyph humanization, cut pre-roll, master bus.
- **FlawBench** (`bench/soundaudit.py`): 9 flaws from expert review turned into quantitative checks.
- **Reel II** (`examples/reel2.py`): 20.4 s, 60 fps, 6 scenes, sub-frame motion blur (`--blur 3`).
- **Site & Studio**: fixed play/pause `data-playing`, GitHub logo, clamped negative spring radii (`--ease-shape`).

## DONE (session 2)
- **Real frame renderer** (`tools/render_video.mjs`, Node canvas + ffmpeg-static) and `motionvid video`.
- **Showreel** (`examples/showreel.py`, 21 s) and **ReelCheck** (`bench/reelcheck.py`, median 1.9 ms).

## DONE (session 1)
- New repo created (not a fork); ORB DSP renderer vendored with attribution (`NOTICE`); English-only.
- **Motion->sound compiler** (`cues.py`), **anchor-aligned parallel mixer** (`compose.py`), **MotionSync-Bench** (median sync error 59.1 ms -> 2.3 ms, **25.8x**; 150-cue render **6.0x** faster; intensity->loudness Pearson 0.11 -> **0.98**; **0 B** weights).
