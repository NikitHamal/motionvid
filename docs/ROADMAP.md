# Roadmap
## CPU phase (now)
C1 per-role anchor calibration · C2 frame renderer + ffmpeg mux (DONE session 2) · C3 human labels (listening test to validate FlawBench) · C4 beat grid/music · C5 MCP server for agents.
C6 scene engine DONE (session 3) · C7 occlusion-aware sound and symmetric-pan handling · C8 more reels via `docs/versions.json`.
## GPU phase (queued; start only when a GPU session exists)
- G1 **Tiny English-only text→timeline planner**: ORB's planner is 5.1M/20 MB. Target ≤ 3 M params, int8 ≤ 3 MB, trained on
  synthetic (prompt, timeline) pairs from this repo's compiler. Gate: no drop on grammar-exact set vs ORB v8 baseline.
- G2 **Differentiable sound-design search**: optimise role params (`ROLE_PARAMS`) against a perceptual loss (multi-res STFT + CLAP)
  to lift the "still weak" roles (wind, engine, clock tick, can opening). Gate: ORB's frozen render baseline hashes not needed for
  changed roles; every unchanged role stays bit-identical.
- G3 **Neural detail residual** (optional, Apache-licensed data only; ORB's detail model is CC BY-NC → not used).
- G4 Learned cue timing refinement from human-labelled launch videos.
Target after GPU: 2–5× on timbre judges (AST/CLAP rank on role set) AND ≥ 2× smaller planner, zero regression on sync bench.
- S6 done: rev 6 Studio sound, StudioBench, `v0.6` and `v0.7`. Next before GPU: restore `reel2` glyph phrasing; human A/B across `v0.1`..`v0.7`.
