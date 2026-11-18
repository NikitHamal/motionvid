# motionvid
Agent-driven motion video pipeline where **sound lands exactly on the motion**. An LLM writes a JSON timeline; motionvid derives every
sound cue and continuous telemetry layer from the physics of the motion, renders it with an agency-grade 48 kHz DSP engine (no samples, no weights) and renders the frames.

```bash
pip install -e ".[dev]" && npm install
python -m motionvid video examples/reel2.json out/ --xray --blur 3   # final.mp4, xray.mp4, audio.wav, cues.json
python scripts/build_media.py                                    # regenerate v0.4 + v0.5 media and flawbench.json
python -m pytest -q && python bench/soundaudit.py                # 43 gates + FlawBench
npm run build                                                    # Studio -> dist/index.html
```
Site: `docs/` (GitHub Pages). Evolution demos: `docs/media/v0.1..v0.5` (`v0.1` Showreel, `v0.2` Scene sound, `v0.3` Reel II, `v0.4` Agency Reel, `v0.5` Launch). Agents start at `AGENT.md`; state is in `STATUS.md`.
Measured on 4 CPUs: sync median error 59 ms -> 2.3 ms (25.8x; 3.9x under a stricter detector), 150-cue render 6.0x faster,
intensity to loudness 0.11 -> 0.98, 0 model bytes. Sound renderer derived from [ORB](https://github.com/stdevMac/orb-audio) (Apache-2.0), see `NOTICE`. Not a fork.

Agency DSP scene engine (`v0.4+` / Session 5): 24 dB/oct resonant LPF (`Q=2.2`) exponential sweeps (`140 Hz -> 3.4 kHz` `suction` anticipation hard-gated at `event.time`; `2.6 kHz -> 120 Hz` `whoosh` with `pre=0.16s, post=0.18s`), locked `0 ms` `sub + impact` (`92 -> 36 Hz` over `190 ms` + triangle `165 -> 62 Hz` over `55 ms` + `5 ms` HP click `> 2.2 kHz` through `tanh`), non-pitched tactile `text_tick` (`1.4–2.8 kHz` bandpass noise + stationary damped body, `+-3 dB` jitter, zero pitch drop), 1 hero `pluck` per scene, detuned `crystal` (`2093 + 3136 Hz`, `+7 cents`, `120 ms` glassy decay + stereo shimmer), and a continuous `motion_energy`/`pan_x` drone + pink-noise bed (`cutoff = 180 + motion_energy * 1400 Hz`, `gain = -34 + motion_energy * 16 dB`).
FlawBench: classic `2/9` (`0.33–0.41`), Agency DSP + RSI **`9/9` across all 3 reels** (`showreel` **`0.996`**, `reel2` `v0.4` **`0.997`**, `launch` `v0.5` **`1.000`**). Rules: `docs/DESIGN.md`.

Latest: `v0.6` Studio Reel and `v0.7` Studio Launch (engine rev 6, StudioBench 17/17). Status: `STATUS.md`. Agents: `AGENT.md`.

## Make a video (agents: read `docs/SKILL.md` first)
```
python scripts/build_demos.py sheet lumen   # contact sheet to check layout
python scripts/build_demos.py lumen         # video + audio + poster
```
Twelve demo reels (six 32-38 s, six new 45-58 s with real photos, footage, real UI and a lit 3D mesh engine) (`examples/demos/`), the `v0.1`..`v0.8` evolution, and the prompt-to-video Create page live on the GitHub Pages site (`docs/`, `docs/create/`).

Create page (`docs/create/`): prompt -> category, 3D hero object, real UI screen, real photos, preview with sound; `Reroll` for variants. Skill for agents: `docs/SKILL.md` (v2). Latest: `v0.9` Mesh Launch.
