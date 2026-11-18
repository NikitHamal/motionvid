# Decisions
- D1 New repo, not a fork. Vendored only ORB's Apache-2.0 DSP renderer, with NOTICE.
- D2 English only: nothing multilingual was vendored (ORB's site i18n, multi-language UI strings, and the free-text planner are
  excluded). The planner (the only language component) is deferred to G1 and will be English-only and smaller.
- D3 No model on the motion→sound path: deterministic physics gives exact timing with 0 bytes of weights.
- D4 Honest benchmark protocol: naive vs anchor on identical clips; independent detector; sustained roles reported separately.
- D5 RSI starts at parameter level with gates the loop cannot edit.
