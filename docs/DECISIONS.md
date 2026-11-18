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

