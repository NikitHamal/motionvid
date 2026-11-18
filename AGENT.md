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
  - `telemetry.py`: 240 Hz per-element signals + `motion_curves()` (`motion_energy` `0.0..1.0` from bbox velocity + morph delta, `pan_x` `-1.0..+1.0`).
  - `score.py`: discrete events with exact offset rules (`suction` at `collapse - 0.25s` hard-gated at `collapse`, `whoosh` `pre=0.16s, post=0.18s`, locked `sub.time === impact.time === cut.time` with `0 ms` offset, `<= 1` hero `pluck` per scene, non-pitched `tick` text reveals, no triggers after `15.40s` on `launch.json`).
  - `foley.py`: continuous `motion_bed` (`pink noise + root-fifth drone` through `cutoff = 180 + motion_energy * 1400 Hz`, `gain = -34 + motion_energy * 16 dB`, panned by `pan_x`) + dB-linear tactile `L->R` felt/brush slide, elastic bar stretch, warm morph pad.
  - `voices.py`: agency-grade DSP voices (`whoosh`/`suction` 24 dB/oct resonant LPF `Q=2.2` exponential sweeps `140 Hz -> 3.4 kHz` and `2.6 kHz -> 120 Hz`; `impact+sub` `92 -> 36 Hz` over `190 ms` + triangle `165 -> 62 Hz` over `55 ms` + `5 ms` HP click `> 2.2 kHz` through `tanh`; zero-pitch-drop `text_tick` in `1.4-2.8 kHz`; detuned `2093 + 3136 Hz` `+7 cents` `crystal` with `120 ms` glassy decay + stereo shimmer).
  - `master.py`: `12%` wet short room reverb (`0.35s` decay, HP `300 Hz`) -> `-4 dB` bell cut at `2.5 kHz` (`Q=1.0`) -> `+3 dB` low shelf at `75 Hz` -> 2:1 glue -> `-16 LUFS` -> `-1.0 dBTP` true-peak limiter.
  - `params.py` + `scene_genome.json`: tunable parameters (RSI tunes these across `showreel.json`, `reel2.json`, and `launch.json`).
- `src/motionvid/scene/studio.py` + `studio_bed.py`: engine rev 6 (default). Voices `whoosh6`, `text_tick6`, `hero_pluck6`, `riser6`, `air6`, `settle`; absolute-dBFS bed/hum/pad with tick ducking; send-bus reverb. `params.DEFAULT['rev']` picks the revision; `--engine scene5` reproduces `v0.4`/`v0.5`.
- `bench/soundaudit.py` FlawBench (9 audio flaws as numbers, classic vs scene). `bench/studio_audit.py` StudioBench (17 gates from the Launch audit, rev 5 vs rev 6).
- `examples/showreel.py` (`v0.1`/`v0.2`), `examples/reel2.py` (`v0.4` Agency Reel, 20.4 s 60 fps), `examples/launch.py` (`v0.5` Launch, 16.8 s 60 fps), `examples/showreel2.py` (`v0.6`, 22.4 s), `examples/launch2.py` (`v0.7`, 20 s).
- `docs/versions.json` registry (`v0.1`..`v0.7`). `docs/DESIGN.md` design rules and owner preferences.

## Surfaces (what ships)
- Frames: `docs/engine/render.js` (+`xray.js`) is the ONE canvas engine for site, Studio (`src/App.tsx`), `preview.py` and `tools/render_video.mjs`.
- Video: `python -m motionvid video tl.json out/ --xray --blur 3` -> `final.mp4` (+`xray.mp4`). Audio by Python, frames by Node, mux by ffmpeg-static.
- Site: `docs/index.html` (GitHub Pages, plain HTML/CSS/JS). Studio: `npm run build` -> `dist/index.html` (single file).
- Media: `python scripts/build_media.py` rebuilds `v0.6` and `v0.7` (rev 6) in `docs/media/` (+ `flawbench.json`). `v0.1`..`v0.5` are frozen: never rebuild or delete any version. A new evolution step = new `vX.Y` + new example script, not an edit of an old one.
- Gates: `pytest -q` (48 tests), StudioBench `python bench/studio_audit.py`, FlawBench via `python bench/soundaudit.py` and `python bench/reelcheck.py`.

## Design & Audio rules: see `docs/DESIGN.md` (tested in `tests/test_rules.py` and `tests/test_scene.py`)
Material 3 Expressive: solid color containers, extra-large shapes, spring motion, Bricolage Grotesque. No box/text shadows, no emojis,
no LIVE badges, no blue/purple gradients (palette: cream, ink, coral, lime, butter, pink, mint). Cut taglines and helper text;
if a screen needs them to make sense, fix the layout.

## Audit-to-fix loop (RSI, how a review becomes a version)
1. Turn each reviewer claim into a number in a bench (`bench/studio_audit.py`), thresholds from the review text.
2. Add the fix behind a new engine `rev` so older versions stay reproducible.
3. Run FlawBench + StudioBench + pytest; keep pass counts; record the cycle in `LEDGER.jsonl`.
4. Build the next `vX.Y` media and add it to `docs/versions.json`. Report numbers with caveats.

## Hard rules
- **No regressions**: tests green, `bench/motionsync.py` and `bench/soundaudit.py` headline numbers must not regress.
- **Honesty**: report measured numbers with their caveats (proxy labels, CPU box, detector choice). Never claim what wasn't run.
- RSI may change `genome.json`, `scene_genome.json`, and compiler/scene code. It may NOT edit gates, labels (`rsi/gt.py` holdout seeds), or tests to pass.
- Secrets (GitHub PAT, MoLab token) never go in tracked files, logs, or commit messages. `/tmp/gitenv.sh` supplies the PAT.
- Attribution: `src/motionvid/sonic/` derives from ORB (Apache-2.0). Keep NOTICE accurate. Not a fork.
- English only. No i18n, no multilingual tokenizers or strings anywhere (see docs/DECISIONS.md D2).
- Keep files < ~300 lines; prefer new modules over growing old ones.
