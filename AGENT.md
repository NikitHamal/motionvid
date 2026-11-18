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

## Surfaces (what ships)
- Frames: `docs/engine/render.js` (+`xray.js`) is the ONE canvas engine for site, Studio (`src/App.tsx`), `preview.py` and `tools/render_video.mjs`.
  Schema additions live there and in `timeline.py` (easings are parity-tested). Element kinds: rrect, circle, ring, blob, text.
- Video: `python -m motionvid video tl.json out/ --xray` -> `final.mp4` (+`xray.mp4`). Audio by Python, frames by Node, mux by ffmpeg-static.
- Site: `docs/index.html` (GitHub Pages, plain HTML/CSS/JS). Studio: `npm run build` -> `dist/index.html` (single file).
- Media: `python scripts/build_media.py` regenerates everything in `docs/media/` from `examples/showreel.py`. Never hand-edit those files.
- Gates: `pytest -q` (34 tests) and `python bench/reelcheck.py` (baseline in `bench/results/reelcheck.json`).

## Design rules (tested in tests/test_rules.py)
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
- Sandbox: 4 CPU, ~3 GB RAM, no GPU, no uvx/claude CLI, no system browser libs (Playwright Chromium cannot launch: libnspr4 missing).
  `pip install --break-system-packages numpy pytest`; `npm install` provides ffmpeg-static + @napi-rs/canvas (works offline of system ffmpeg).
- The repo root also holds the Vite Studio app (package.json, src/*.tsx). Python package is `src/motionvid`.
- MoLab box (CPU-only, then GPU later) can't be paired from this sandbox (no `uvx`/`claude`); GPU work is queued in ROADMAP "GPU phase".
