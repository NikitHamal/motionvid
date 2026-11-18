# STATUS — motionvid (single living doc; extend in place)
Repo: https://github.com/NikitHamal/motionvid · Last updated: session 3 · Box: 4 CPU / 3 GB / no GPU.

## Next actions (do top first)
1. **Visual QA in a real browser**: site (`docs/index.html`) and Studio are verified by build, Node tests and rule tests only (sandbox cannot launch
   Chromium). Open both; confirm play/pause toggles, nav hover never shows a square corner, version buttons switch audio+timeline. Screenshot to `docs/media/`.
2. **Code-level audio gains (parameter RSI has plateaued)**: Reel II holdout fails `pan_corr` (0.44 < 0.5) and `sub_coupling` is 0.75 (v0.3: 0.89).
   Ideas: pan the dominant mover only when several elements move symmetrically; add sub to ring/pop clusters; occlusion (do not sound elements hidden under a flood).
3. **GPU session** (when granted): learn the telemetry->parameter map from human-rated edits; see `docs/ROADMAP.md` G1. Keep 0-byte engine as the baseline gate.
4. Human labels for "what is the hit" of broad sounds (whoosh, riser); calibrate classic anchors. Gate: `bench/motionsync.py` both detectors no worse.
5. Music bed on a beat grid (`render/music.py` vendored, unused); MCP server for agents; 20 real launch timelines.

## DONE (session 3)
- **Scene audio engine** (`src/motionvid/scene/`, 0 weights, English-only, ~900 lines): sound is bound to continuous scene telemetry, not only trigger times.
  area growth -> pitch-dropping sub (95->42 Hz); x(t) -> constant-power pan in [-0.65, 0.65], per sample for moving layers; speed -> filtered-noise texture
  (300 Hz rest -> 4.5 kHz peak) + servo hum; width rate -> rubbery stretch tone; lobe-amp rate -> shimmer; glyph triggers from each character's real easing curve
  (whitespace skipped, +-45 cents, +-2.5 dB, +1 semitone per 3.5 glyphs); scale pops phrase into an A-minor pentatonic cascade; collapses get suction + 3-6 kHz crystal;
  every cut gets a whoosh that ramps up 190-210 ms early and peaks on the cut frame; chord bed + room tone remove dead air;
  master bus = 10% short room reverb (HP 250 Hz send) -> tilt EQ (+3 dB < 85 Hz, +2.5 dB > 9 kHz) -> 2:1 glue (10/80 ms) -> -16 LUFS -> -1.0 dBTP limiter.
- **FlawBench** (`bench/soundaudit.py`): the nine flaws from the expert review as numbers, thresholds from the review text. Same timeline, same checks:
  | reel | classic (v0.2 sound) | scene (new) |
  |---|---|---|
  | showreel (dev) | 2/9, score 0.41 | **9/9, score 0.94** (2.3x) |
  | Reel II (holdout) | 2/9, score 0.41 | **8/9, score 0.91** (2.2x) |
  Honest notes: the review overstated two things. The classic mix already has strong 20-80 Hz energy (+5 dB vs mids) and 3 click variants, so those raw
  metrics passed for v0.2; what was missing was *coupling* (sub on growth: 0.78 -> 0.89, glyph phrasing rho 0.40 -> 0.96), dead air (5.5 s -> 0), pre-roll,
  pan tracking, tails and loudness (-22.1 LUFS, -0.96 dBTP -> -16.0, -1.0). Composite score is our own proxy, not a listening test.
- **Reel II** (`examples/reel2.py`): 20.4 s, 60 fps, 81 elements, six scenes, real motion blur (`--blur 3`, tools/render_video.mjs sub-frame accumulation).
- **Evolution kept**: `docs/media/v0.1..v0.4/`, registry `docs/versions.json` drives the site player and cards. v0.1/v0.2 are frozen and never rebuilt.
  v0.3 = v0.2 visuals + scene sound; v0.4 = Reel II + scene sound.
- **Site**: play/pause fixed (inline-svg `hidden` is unreliable; now `data-playing` + CSS), GitHub logo in the button, nav hover no longer flashes square corners
  (cause: spring easing overshoot made the interpolated radius negative, clamped to 0). Rule is now a test. Studio had the same bug, fixed.
- **RSI**: `motionvid rsi --scene` (dev + holdout, accept only if nothing regresses). 6 cycles run, 0 accepted: parameter space is saturated, see next action 2.
- Tests 24 -> 41 (scene determinism, master limits, pre-roll, humanization, voice anchors, FlawBench gate, radius/play-pause/GitHub/version-media rules).
- Mix-level ReelCheck cannot judge the dense scene engine (a 70 % envelope crossing picks the loudest neighbour); isolated impacts on the mix: median 2.4-3.6 ms,
  78-80 % within one 30 fps frame. Per-voice anchors are gated in tests instead.
- Not done: MoLab pairing (no `claude`/`uvx` in the sandbox), GPU phase, browser QA.

## DONE (session 2)
- **Real frame renderer** (was next-action 2): `tools/render_video.mjs` (Node canvas + ffmpeg-static) and `motionvid video`.
  Same engine as the site. 21 s / 630 frames at 1280x720 + audio muxed in ~9 s on 4 CPUs.
- **Showreel**: `examples/showreel.py` -> 21 s, 41 elements, 100 compiled cues (48 click, 25 ui_pop, 12 impact, 10 whoosh, 5 riser...),
  five scenes with color floods whose hit lands on the closing frame; bounce contacts of a real outBounce get per-contact impacts.
- Engine: new kinds (blob/cookie, ring, circle, rrect with pill radius), per-char split text, `outElastic`/`inBack` easings, cue x-ray.
- **ReelCheck** (`bench/reelcheck.py`): rendered-audio hit alignment on the real showreel: median 1.9 ms, p95 70.7 ms (broad sounds and
  clustered cues), 76.9 % within one 30 fps frame, peak 0.89. Gates: median <= 12 ms, within-1-frame >= 0.75, peak <= 0.98.
- Surfaces: GitHub Pages site (plain HTML/CSS/JS, M3 Expressive), Studio (React, cue inspector), demo MP4s (showreel, x-ray, launch).
- Tests 14 -> 24 (easing parity JS/Python, preview, video smoke, design rules). `scripts/build_media.py` regenerates all artifacts.
- Preview page now uses the shared engine (old duplicate JS removed).

## Known limits (session 2)
- Still not a "2-5x better timbre" model; timbre is ORB's DSP. No GPU session used. Proven wins remain sync, throughput, dynamics, zero weights.
- ReelCheck is a new metric with no upstream baseline; it gates regressions, it does not prove a multiple.
- No browser verification of the site/Studio yet (see next action 1). Audio autoplay needs a user click by browser policy.

## DONE (session 1)
- New repo created (not a fork); ORB DSP renderer vendored with attribution (NOTICE); nothing multilingual vendored.
- **Motion→sound compiler** (`cues.py`): 0 params, 0 weights, no language; physics-derived cues from a JSON timeline.
- **Anchor-aligned cached parallel mixer** (`compose.py`) + `MotionSync-Bench`. Results (CPU, `bench/results/motionsync.json`):
  | metric | upstream-style | motionvid | gain |
  |---|---|---|---|
  | sync error, median over 141 role×dur cases | 59.1 ms | **2.3 ms** | **25.8×** |
  | sync error, p95 (all) | 453 ms | 76 ms | 5.9× |
  | sync error, p95 (defined-hit roles) | 468 ms | 64.7 ms | 7.2× |
  | within 1 frame @30 fps | 43 % | **89 %** | 2.1× |
  | render 150 cues / 60 s (4 CPU) | ~9.1 s | **~1.5 s** | **6.0×** (1 worker: 1.8×; warm cache 41×) |
  | intensity→loudness Pearson (whoosh) | 0.11 | **0.98** | capability, was absent |
  | model/weights needed for motion path | 20 MB planner | **0** | — |
  **Detector dependence (important)**: the sync rows use detector 1 (80 % crossing, 8 ms, L channel). A structurally different
  detector 2 (loudest 20 ms window) gives median 109 → 27.8 ms (**3.9×**) and within-1-frame 28 % → 54 %. Both are reported in
  `bench/results/motionsync.json`. For broad-peaked sounds (whoosh, riser, noise_sweep, paper_rustle, glitch) "the hit" is perceptual,
  so the two disagree; transient roles (impact, click, ui_pop, bell, ...) agree. Anchor-definition experiment (offline): crossing-70 %
  (current) 1.9/27.8 ms medians on det1/det2; loudest-window 17.4/0.0; midpoint 9.9/13.9 — no free lunch, needs human labels.
  Caveats: "upstream-style" = event start placed at cue time (what a caption/score engine does when an agent writes `@t`);
  clips are the same renderer, so timbre is unchanged by construction (no regression, no improvement). Sustained sounds
  (owl, siren, wind) have no single "hit"; reported separately. Detector for eval differs from placement detector.
- Found and worked around 3 upstream renderer defects at short durations (owl crash fixed in `natural.py`; coin_drop raises,
  fireworks silent → `compose._render_key` grows dur ×1.5 until valid).
- **RSI cycle 2**: no accepted candidate (60 mutations, parameter level saturated at dev 0.948 / holdout 0.911); logged in LEDGER.jsonl. Next gain needs code-level (L2) change or label decision.
- **RSI cycle 1** accepted (LEDGER.jsonl #1): cue F1 dev 0.934→0.948, holdout 0.899→0.911 (4 genome params changed).
- CLI (`cues`, `render`, `bench`, `rsi`), HTML preview synced to audio, 14 tests green, docs (AGENT, SKILL, ARCHITECTURE, RSI, ROADMAP, DECISIONS).

## Known limits (honest)
- This is **not yet** a "2–5× better timbre" model. Timbre = ORB's physical models, unchanged. The proven wins are exact sync,
  throughput, motion-conditioned dynamics, and zero-weight operation. Timbre/size breakthroughs are the GPU phase (ROADMAP G1–G4).
- Ground truth for RSI is synthetic designer-intent labels (proxy). Holdout F1 0.911 is on the same generator family.
- No video frames are produced yet — only audio + synchronized HTML preview.
- MoLab pairing not possible from this sandbox (no `uvx`/`claude`); no remote GPU/CPU box was used.
