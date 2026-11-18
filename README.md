# motionvid
Agent-driven motion video pipeline where **sound lands exactly on the motion**. An LLM writes a JSON timeline; motionvid derives every
sound cue from the physics of the motion, renders it with a code-native DSP engine (no samples, no weights) and renders the frames.

```bash
pip install -e ".[dev]" && npm install
python -m motionvid video examples/reel2.json out/ --xray --blur 3   # final.mp4, xray.mp4, audio.wav, cues.json
python scripts/build_media.py                                    # regenerate site + Studio media
python -m pytest -q && python bench/soundaudit.py                # gates + FlawBench
npm run build                                                    # Studio -> dist/index.html
```
Site: `docs/` (GitHub Pages). Demos: `docs/media/` (showreel, x-ray, launch). Agents start at `AGENT.md`; state is in `STATUS.md`.
Measured on 4 CPUs: sync median error 59 ms -> 2.3 ms (25.8x; 3.9x under a stricter detector), 150-cue render 6.0x faster,
intensity to loudness 0.11 -> 0.98, 0 model bytes. Sound renderer derived from [ORB](https://github.com/stdevMac/orb-audio) (Apache-2.0), see `NOTICE`. Not a fork.

Sound engine (v0.3+): scene telemetry drives sub-bass, pan, motion foley, humanized glyphs, pre-rolled transitions and a mastering bus.
FlawBench on the same reel: classic 2/9 passes, scene 9/9 (holdout reel 8/9). Every version is kept in `docs/media/`. Rules: `docs/DESIGN.md`.
