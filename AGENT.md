# AGENT.md — operating manual for any AI agent working on motionvid

Read this first, then `STATUS.md` (the single living status doc). Do not create new status files; extend in place.

## Mission
Build the world's best LLM/agent-driven pipeline for launch videos, motion videos and any dynamic video, **with sound
that lands exactly on the motion**. Sound engine = code-native DSP (no samples, no model needed for the motion path).
Long-term: recursive self-improvement (RSI) — the system measures itself, proposes changes, and keeps only gated wins.

## Pickup protocol (every session)
1. `git pull`, read `STATUS.md` top section ("Next actions"), `LEDGER.jsonl` tail, `docs/ROADMAP.md`.
2. Run `python3 -m pytest -q` (≈12 s) — must be green before and after your work.
3. Do the top "Next action". Never redo anything marked DONE in STATUS.md; never re-run a benchmark just to re-print it.
4. Update STATUS.md in place (move finished items to DONE with numbers), append to LEDGER.jsonl via `motionvid rsi` when
   the compiler genome changes, commit small, push to `origin main` after each milestone.

## Map
- `src/motionvid/timeline.py` schema + easings (JS twin lives in `preview.py`; keep both identical).
- `src/motionvid/cues.py` motion → cues (physics: peak speed, abrupt stop, scale pop, fast fade, typing, cuts, agent hints).
- `src/motionvid/genome.py` + `genome.json` tunable thresholds (RSI mutates these).
- `src/motionvid/compose.py` anchor-aligned, cached, parallel mixer. `src/motionvid/sonic/` vendored DSP (see NOTICE).
- `src/motionvid/rsi/` ground truth (`gt.py`) + loop (`loop.py`). `bench/motionsync.py` sync/throughput/dynamics bench.
- `docs/SKILL.md` how an LLM writes timelines. `docs/` architecture, benchmarks, RSI rules, roadmap, decisions.

- `src/motionvid/scene/` the scene audio engine (default): `telemetry.py` (240 Hz element signals), `score.py` (events, phrasing, humanization), `foley.py`
  (continuous layers), `voices.py` (DSP voices), `master.py` (reverb, tilt, glue, LUFS, true-peak limiter), `engine.py`, `params.py` + `scene_genome.json` (RSI tunes these).
- `bench/soundaudit.py` FlawBench (9 audio flaws as numbers, classic vs scene). `src/motionvid/rsi/scene_loop.py` scene RSI (`motionvid rsi --scene`).
- `examples/showreel.py` (v0.2/v0.3 visuals), `examples/reel2.py` (v0.4, 60 fps). `docs/versions.json` registry. `docs/DESIGN.md` design rules and owner preferences.

## Surfaces (what ships)
- Frames: `docs/engine/render.js` (+`xray.js`) is the ONE canvas engine for site, Studio (`src/App.tsx`), `preview.py` and `tools/render_video.mjs`.
  Schema additions live there and in `timeline.py` (easings are parity-tested). Element kinds: rrect, circle, ring, blob, text.
- Video: `python -m motionvid video tl.json out/ --xray` -> `final.mp4` (+`xray.mp4`). Audio by Python, frames by Node, mux by ffmpeg-static.
- Site: `docs/index.html` (GitHub Pages, plain HTML/CSS/JS). Studio: `npm run build` -> `dist/index.html` (single file).
- Media: `python scripts/build_media.py` rebuilds v0.3 and v0.4 in `docs/media/` (+ `flawbench.json`). v0.1 and v0.2 are frozen: never rebuild or delete any version. Never hand-edit generated files.
- New version recipe: write `examples/<name>.py`, add it to `BUILDS` in `scripts/build_media.py`, add an entry to `docs/versions.json`, run build, update STATUS.
- Gates: `pytest -q` (41 tests), FlawBench via `python bench/soundaudit.py` and `python bench/reelcheck.py` (baseline in `bench/results/reelcheck.json`).

## Design rules: see `docs/DESIGN.md` (tested in tests/test_rules.py)
Material 3 Expressive: solid color containers, extra-large shapes, spring motion, Bricolage Grotesque. No box/text shadows, no emojis,
no LIVE badges, no blue/purple gradients (palette: cream, ink, coral, lime, butter, pink, mint). Cut taglines and helper text;
if a screen needs them to make sense, fix the layout.

## Hard rules
- **No regressions**: tests green, `bench/motionsync.py` headline numbers must not get worse than `bench/results/motionsync.json`
  (update that file only when numbers improve, and say so in STATUS.md).
- **Honesty**: report measured numbers with their caveats (proxy labels, CPU box, detector choice). Never claim what wasn't run.
- RSI may change `genome.json` and compiler code. It may NOT edit gates, labels (`rsi/gt.py` holdout seeds), or tests to pass.
- Secrets (GitHub PAT, MoLab token) never go in tracked files, logs, or commit messages. `/tmp/gitenv.sh` supplies the PAT.
- Attribution: `src/motionvid/sonic/` derives from ORB (Apache-2.0). Keep NOTICE accurate. Not a fork.
- English only. No i18n, no multilingual tokenizers or strings anywhere (see docs/DECISIONS.md D2).
- Keep files < ~300 lines; prefer new modules over growing old ones.

## Environment notes
- Sandbox: `pip install --break-system-packages numpy scipy pytest`; the platform preview serves `docs/` through an untracked stub package.json (`/tmp/health_server.js`): never commit that stub, the real package.json is the Studio's. 4 CPU, ~3 GB RAM, no GPU, no uvx/claude CLI, no system browser libs (Playwright Chromium cannot launch: libnspr4 missing).
  `pip install --break-system-packages numpy pytest`; `npm install` provides ffmpeg-static + @napi-rs/canvas (works offline of system ffmpeg).
- The repo root also holds the Vite Studio app (package.json, src/*.tsx). Python package is `src/motionvid`.
- MoLab box (CPU-only, then GPU later) can't be paired from this sandbox (no `uvx`/`claude`); GPU work is queued in ROADMAP "GPU phase".

## RSI quick start
`python -m motionvid rsi --scene --cycles 6` mutates `scene_genome.json`, scores dev (showreel) and holdout (reel2) on FlawBench, appends to `LEDGER.jsonl`.
Parameter RSI has plateaued (6/6 rejected, session 3); the next gains are code-level (STATUS next action 2). Never edit CHECKS thresholds or tests to pass.
