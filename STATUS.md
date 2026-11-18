# STATUS — motionvid (single living doc; extend in place)
Repo: https://github.com/NikitHamal/motionvid · Last updated: session 1 · Box: 4 CPU / 3 GB / no GPU.

## Next actions (do top first)
1. **RSI cycle 2: calibrate per-role anchors.** 25 % of defined-hit roles still miss ±5 ms (multi-hit/long roles:
   thunder, footsteps, applause, owl, siren, wind_gust). Add per-role `anchor_frac`/mode to `compose.py`, gate on
   `bench/motionsync.py` (`defined_hit_within_5ms` 0.748 → ≥ 0.90, no other metric worse).
2. Real frame renderer: headless Chromium (Playwright) screenshots of `preview.py` page per frame → ffmpeg mux with `audio.wav`
   (needs ffmpeg; not available in this sandbox — implement + test where available, keep `video.mp4`/`final.mp4` hook in cli.py).
3. Human-labelled cue set (replace proxy labels in `rsi/gt.py`); add 20 real launch-video timelines to `examples/`.
4. Music bed/beat grid: snap cues to beats (render/music.py is vendored but unused).
5. GPU phase (when a GPU session is given): see `docs/ROADMAP.md`.

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
  | render 150 cues / 60 s (4 CPU) | 9.05 s | **1.59 s** | **5.7×** (1 worker: 1.9×; warm cache 41×) |
  | intensity→loudness Pearson (whoosh) | 0.11 | **0.98** | capability, was absent |
  | model/weights needed for motion path | 20 MB planner | **0** | — |
  Caveats: "upstream-style" = event start placed at cue time (what a caption/score engine does when an agent writes `@t`);
  clips are the same renderer, so timbre is unchanged by construction (no regression, no improvement). Sustained sounds
  (owl, siren, wind) have no single "hit"; reported separately. Detector for eval differs from placement detector.
- Found and worked around 3 upstream renderer defects at short durations (owl crash fixed in `natural.py`; coin_drop raises,
  fireworks silent → `compose._render_key` grows dur ×1.5 until valid).
- **RSI cycle 1** accepted (LEDGER.jsonl #1): cue F1 dev 0.934→0.948, holdout 0.899→0.911 (4 genome params changed).
- CLI (`cues`, `render`, `bench`, `rsi`), HTML preview synced to audio, 14 tests green, docs (AGENT, SKILL, ARCHITECTURE, RSI, ROADMAP, DECISIONS).

## Known limits (honest)
- This is **not yet** a "2–5× better timbre" model. Timbre = ORB's physical models, unchanged. The proven wins are exact sync,
  throughput, motion-conditioned dynamics, and zero-weight operation. Timbre/size breakthroughs are the GPU phase (ROADMAP G1–G4).
- Ground truth for RSI is synthetic designer-intent labels (proxy). Holdout F1 0.911 is on the same generator family.
- No video frames are produced yet — only audio + synchronized HTML preview.
- MoLab pairing not possible from this sandbox (no `uvx`/`claude`); no remote GPU/CPU box was used.
