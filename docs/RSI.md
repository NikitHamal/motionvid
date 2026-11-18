# Recursive self-improvement protocol
Loop (`python -m motionvid rsi`): measure → mutate → select on DEV → gate on HOLDOUT + regression → write → ledger.
- Accept only if DEV F1 +0.002 or more, HOLDOUT F1 not lower, `_gate` passes (hints survive, example keeps ≥ 20 cues).
- Everything is logged to `LEDGER.jsonl` (append-only, one JSON per cycle, accepted or not). Never rewrite history.
- Levels: L1 parameters (done, cycle 1) → L2 code proposals by an agent, accepted by the same gates → L3 the agent proposes new
  benchmarks/labels, **human-approved** (labels are not self-editable) → L4 GPU-trained components enter via the same gates.
- Anti-gaming: holdout seeds ≥ 10000 are never used for selection; benchmark numbers in STATUS.md must come from files in
  `bench/results/`; tests may only be strengthened.
- Known weakness: labels are synthetic. Replace with human labels before trusting gains beyond ~0.95 F1.
