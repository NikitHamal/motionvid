# Decisions
- D1 New repo, not a fork. Vendored only ORB's Apache-2.0 DSP renderer, with NOTICE.
- D2 English only: nothing multilingual was vendored (ORB's site i18n, multi-language UI strings, and the free-text planner are
  excluded). The planner (the only language component) is deferred to G1 and will be English-only and smaller.
- D3 No model on the motion→sound path: deterministic physics gives exact timing with 0 bytes of weights.
- D4 Honest benchmark protocol: naive vs anchor on identical clips; independent detector; sustained roles reported separately.
- D5 RSI starts at parameter level with gates the loop cannot edit.
- D6 One frame engine (`docs/engine/`) for every surface; frames are a pure function of (timeline, t), so video, site and Studio match.
- D7 Video = Node canvas + ffmpeg-static, not a headless browser: no system libraries, deterministic, 21 s reel renders in ~9 s.
- D8 Material 3 Expressive with solid containers and spring easing; shadows, emojis, LIVE badges and blue/purple gradients banned and tested.
- D9 Site is plain HTML/CSS/JS in `docs/` (Pages); the React app is a separate surface (Studio) that imports the same engine and tokens.

- D10 Scene engine is default; classic engine stays selectable (`--engine classic`) so v0.2 can be reproduced and benchmarks stay comparable.
- D11 Sound is bound to continuous telemetry (area, x, speed, rates), not only to trigger times; the master bus is part of the engine, not a post step.
- D12 FlawBench thresholds come from the expert review text, not from our results; where the review was wrong about raw metrics we say so in STATUS.
- D13 Versions are append-only (`docs/media/v0.x`, `docs/versions.json`); old media is never rebuilt.
- D14 Radius transitions never use springs (negative radius clamps to square). Enforced by test.
- D15 Engine revisions: new sound = new `rev` (`params.DEFAULT['rev']`), old revs stay reproducible (`--engine scene5`). Tests that pin v0.4/v0.5 behaviour pin `rev: 5`.
- D16 Levels the reviewer states in dBFS are applied after loudness normalisation (absolute layer), everything else stays relative to the mix.
- D17 A hero pluck mutes text ticks for 120 ms and ticks duck the bed by 12 dB: masking is solved in the mix, not by editing the benchmark.
