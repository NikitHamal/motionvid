# motionvid
Agent-driven motion-video pipeline where **sound lands exactly on the motion**. An LLM writes a JSON timeline; motionvid derives
every sound cue from the physics of the motion and renders it with a code-native DSP engine (no samples, no weights, numpy only).

```bash
pip install -e ".[dev]"
python -m motionvid render examples/launch.json out/   # audio.wav + cues.json + preview.html
python -m pytest -q
python bench/motionsync.py                              # reproduces STATUS.md numbers
```
Measured on 4 CPUs: sync median error **59 ms → 2.3 ms (25.8×)**, 150-cue render **5.7× faster**, intensity→loudness 0.11 → 0.98, 0 model bytes.
See `STATUS.md` (honest state + next actions), `AGENT.md` (agents start here), `docs/`.
Sound renderer derived from [ORB](https://github.com/stdevMac/orb-audio) (Apache-2.0) — see `NOTICE`. Not a fork.
