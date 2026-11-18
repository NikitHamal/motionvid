# AGENT.md — operating manual for any AI agent working on motionvid

Read this first, then `STATUS.md` (the single living status doc). Do not create new status files; extend in place.

## Mission
Build the world's best LLM/agent-driven pipeline for launch videos, motion videos and any dynamic video, **with sound
that lands exactly on the motion**. Sound engine = code-native Agency DSP (no samples, no model weights needed for the motion path).
Long-term: recursive self-improvement (RSI) — the system measures itself, proposes changes, and keeps only gated wins.

## Pickup protocol (every session)
1. `git pull`, read `STATUS.md` top section ("Next actions"), `LEDGER.jsonl` tail, `docs/ROADMAP.md`.
2. Run `python3 -m pytest -q` (≈25 s) — must be green before and after your work.
3. Do the top "Next action". Never redo anything marked DONE in STATUS.md; never re-run a benchmark just to re-print it.
4. Update STATUS.md in place (move finished items to DONE with numbers), append to LEDGER.jsonl via `motionvid rsi` when
   the compiler or scene genome changes, commit small, push to `origin main` after each milestone.

## Map
- `src/motionvid/timeline.py` schema + easings (JS twin lives in `docs/engine/render.js`; keep both identical).
- `src/motionvid/cues.py` motion -> cues (physics: peak speed, abrupt stop, scale pop, fast fade, typing, cuts, agent hints).
- `src/motionvid/genome.py` + `genome.json` tunable thresholds (RSI mutates these).
- `src/motionvid/compose.py` anchor-aligned, cached, parallel mixer. `src/motionvid/sonic/` vendored DSP (see NOTICE).
- `src/motionvid/rsi/` ground truth (`gt.py`) + loop (`loop.py`) + `scene_loop.py`. `bench/motionsync.py` sync/throughput/dynamics bench.
- `src/motionvid/scene/` the Agency DSP scene audio engine (default):
  - `telemetry.py`: 240 Hz per-element & composite signals.
  - `score.py`: discrete events with musical phrasing, 3-voice burst polyphony budget, 110 ms class cooldown, hero wooden transients.
  - `foley.py`: composite continuous layers (tactile L->R felt slide, single low-pass elastic bar brush, warm harmonic morph pad).
  - `voices.py`: agency-grade DSP voices (120 ms damped triangle/saw marimba bodies `180-420 Hz` with `1.8 kHz -> 300 Hz` LP over `90 ms` + `6 ms` woody click; dual-layer pink-noise `Q=1.2` LP + `90 -> 42 Hz` sub-drop whooshes; realistic `<= 4` semitone pitch sweeps).
  - `master.py`: `12%` wet short room reverb (`0.35s` decay, HP `300 Hz`) -> `-4 dB` bell cut at `2.5 kHz` (`Q=1.0`) -> `+3 dB` low shelf at `75 Hz` -> 2:1 glue -> `-16 LUFS` -> `-1.0 dBTP` true-peak limiter.
  - `params.py` + `scene_genome.json`: tunable parameters (RSI tunes these across `showreel.json`, `reel2.json`, and `launch.json`).
- `bench/soundaudit.py` FlawBench (9 audio flaws as numbers, classic vs scene).
- `examples/showreel.py` (`v0.1`/`v0.2`), `examples/reel2.py` (`v0.4` Agency Reel, 20.4 s 60 fps), `examples/launch.py` (`v0.5` Launch, 16.8 s 60 fps).
- `docs/versions.json` registry (`v0.1`..`v0.5`). `docs/DESIGN.md` design rules and owner preferences.

## Surfaces (what ships)
- Frames: `docs/engine/render.js` (+`xray.js`) is the ONE canvas engine for site, Studio (`src/App.tsx`), `preview.py` and `tools/render_video.mjs`.
- Video: `python -m motionvid video tl.json out/ --xray --blur 3` -> `final.mp4` (+`xray.mp4`). Audio by Python, frames by Node, mux by ffmpeg-static.
- Site: `docs/index.html` (GitHub Pages, plain HTML/CSS/JS). Studio: `npm run build` -> `dist/index.html` (single file).
- Media: `python scripts/build_media.py` rebuilds `v0.4` and `v0.5` in `docs/media/` (+ `flawbench.json`). `v0.1`, `v0.2`, and `v0.3` are frozen: never rebuild or delete any version.
- Gates: `pytest -q` (42 tests), FlawBench via `python bench/soundaudit.py` and `python bench/reelcheck.py`.

## Design & Audio rules: see `docs/DESIGN.md` (tested in `tests/test_rules.py` and `tests/test_scene.py`)
Material 3 Expressive: solid color containers, extra-large shapes, spring motion, Bricolage Grotesque. No box/text shadows, no emojis,
no LIVE badges, no blue/purple gradients (palette: cream, ink, coral, lime, butter, pink, mint). Cut taglines and helper text;
if a screen needs them to make sense, fix the layout.

## Hard rules
- **No regressions**: tests green, `bench/motionsync.py` and `bench/soundaudit.py` headline numbers must not regress.
- **Honesty**: report measured numbers with their caveats (proxy labels, CPU box, detector choice). Never claim what wasn't run.
- RSI may change `genome.json`, `scene_genome.json`, and compiler/scene code. It may NOT edit gates, labels (`rsi/gt.py` holdout seeds), or tests to pass.
- Secrets (GitHub PAT, MoLab token) never go in tracked files, logs, or commit messages. `/tmp/gitenv.sh` supplies the PAT.
- Attribution: `src/motionvid/sonic/` derives from ORB (Apache-2.0). Keep NOTICE accurate. Not a fork.
- English only. No i18n, no multilingual tokenizers or strings anywhere (see docs/DECISIONS.md D2).
- Keep files < ~300 lines; prefer new modules over growing old ones.
