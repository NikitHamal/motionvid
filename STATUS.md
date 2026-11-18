# STATUS — motionvid (single living doc; extend in place)
Repo: https://github.com/NikitHamal/motionvid · Last updated: session 2 · Box: 4 CPU / 3 GB / no GPU.

## Next actions (do top first)
1. **Visual QA in a real browser**: site (`docs/index.html`) and Studio were verified by build + Node tests only (sandbox cannot launch
   Chromium). Open both, fix anything off, then record a screenshot set in `docs/media/`.
2. **Human decision + labels for 'what is the hit' of broad sounds** (whoosh, riser, noise_sweep, paper_rustle, glitch); calibrate
   per-role anchors in `compose.py`. Gate: `bench/motionsync.py` both detectors no worse than the table below.
3. RSI cycle 3 on ReelCheck: p95 error 70.7 ms and within-1-frame 0.769 are dominated by overlapping/broad cues. Try code-level
   change (cluster-aware anchoring) and keep only if `bench/reelcheck.py` improves with all gates green.
4. Music bed on a beat grid (`render/music.py` vendored, unused); `motionvid video --bed` is wired for textures only.
5. More example timelines (20 real launch videos), MCP server for agents, GPU phase per `docs/ROADMAP.md`.

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
