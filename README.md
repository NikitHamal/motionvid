# motionvid
Agent-driven motion video pipeline where **sound lands exactly on the motion**. An LLM writes a JSON timeline; motionvid derives every
sound cue and continuous telemetry layer from the physics of the motion, renders it with an agency-grade 48 kHz DSP engine (no samples, no weights) and renders the frames.

```bash
pip install -e ".[dev]" && npm install
python -m motionvid video examples/reel2.json out/ --xray --blur 3   # final.mp4, xray.mp4, audio.wav, cues.json
python scripts/build_media.py                                    # regenerate v0.4 + v0.5 media and flawbench.json
python -m pytest -q && python bench/soundaudit.py                # 42 gates + FlawBench
npm run build                                                    # Studio -> dist/index.html
```
Site: `docs/` (GitHub Pages). Evolution demos: `docs/media/v0.1..v0.5` (`v0.1` Showreel, `v0.2` Scene sound, `v0.3` Reel II, `v0.4` Agency Reel, `v0.5` Launch). Agents start at `AGENT.md`; state is in `STATUS.md`.
Measured on 4 CPUs: sync median error 59 ms -> 2.3 ms (25.8x; 3.9x under a stricter detector), 150-cue render 6.0x faster,
intensity to loudness 0.11 -> 0.98, 0 model bytes. Sound renderer derived from [ORB](https://github.com/stdevMac/orb-audio) (Apache-2.0), see `NOTICE`. Not a fork.

Agency DSP scene engine (`v0.4+`): damped triangle/saw marimba bodies (`180–420 Hz`, `1.8 kHz -> 300 Hz` LP over `90 ms`) + `6 ms` woody click transients, strict 3-voice burst polyphony budget (`110 ms` cooldown), locked pink-noise (`Q=1.2` LP) + `90 -> 42 Hz` sub-drop whooshes, realistic `<= 4` semitone pitch sweeps, tactile `L -> R` felt slides, and a master bus (`12%` `0.35s` reverb HP `300 Hz`, `-4 dB` at `2.5 kHz`, `+3 dB` at `75 Hz`, `-16 LUFS`, `-1.0 dBTP`).
FlawBench: classic `2/9` (`0.41`), Agency DSP + RSI **`9/9` across all 3 reels** (`showreel` **`0.987`**, `reel2` `v0.4` **`0.968`**, `launch` `v0.5` **`0.993`**). Rules: `docs/DESIGN.md`.
