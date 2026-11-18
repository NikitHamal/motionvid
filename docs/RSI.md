# Recursive self-improvement protocol
Loop (`python -m motionvid rsi`): measure → mutate → select on DEV → gate on HOLDOUT + regression → write → ledger.
- Accept only if DEV F1 +0.002 or more, HOLDOUT F1 not lower, `_gate` passes (hints survive, example keeps ≥ 20 cues).
- Everything is logged to `LEDGER.jsonl` (append-only, one JSON per cycle, accepted or not). Never rewrite history.
- Levels: L1 parameters (done, cycle 1) → L2 code proposals by an agent, accepted by the same gates → L3 the agent proposes new
  benchmarks/labels, **human-approved** (labels are not self-editable) → L4 GPU-trained components enter via the same gates.
- Anti-gaming: holdout seeds ≥ 10000 are never used for selection; benchmark numbers in STATUS.md must come from files in
  `bench/results/`; tests may only be strengthened.
- Known weakness: labels are synthetic. Replace with human labels before trusting gains beyond ~0.95 F1.

## Scene audio loop (session 3)
`python -m motionvid rsi --scene`: mutate 3 of `params.BOUNDS` in `scene_genome.json`, evaluate FlawBench score and pass counts on dev (showreel.json) and
holdout (reel2.json). Accept only if dev score rises by more than 0.002, holdout score does not drop, and no pass count drops. Result so far: 6 cycles, 0 accepted
(saturated at 9/9 dev, 8/9 holdout). The remaining failure is structural (pan tracking on symmetric motion), so it needs a code proposal, gated the same way.
