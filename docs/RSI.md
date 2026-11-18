# Recursive self-improvement protocol
Loop (`python -m motionvid rsi`): measure -> mutate -> select on DEV -> gate on HOLDOUT + regression -> write -> ledger.
- Accept only if DEV F1 +0.002 or more, HOLDOUT F1 not lower, `_gate` passes (hints survive, example keeps >= 20 cues).
- Everything is logged to `LEDGER.jsonl` (append-only, one JSON per cycle, accepted or not). Never rewrite history.
- Levels: L1 parameters (done, cycle 1) -> L2 code proposals by an agent, accepted by the same gates -> L3 the agent proposes new
  benchmarks/labels, **human-approved** (labels are not self-editable) -> L4 GPU-trained components enter via the same gates.
- Anti-gaming: holdout seeds >= 10000 are never used for selection; benchmark numbers in STATUS.md must come from files in
  `bench/results/` or `docs/media/flawbench.json`; tests may only be strengthened.
- Known weakness: labels are synthetic. Replace with human labels before trusting gains beyond ~0.95 F1.

## Scene audio loop (sessions 3-4)
`python -m motionvid rsi --scene`: mutate 3 of `params.BOUNDS` in `scene_genome.json`, evaluate FlawBench score and pass counts on dev (`showreel.json`) and
holdouts (`reel2.json`, `launch.json`). Accept only if dev score rises by more than 0.002, holdout scores do not drop, and no pass count drops.
- Session 3: 6 L1 cycles, 0 accepted (saturated at 9/9 dev `0.942`, 8/9 holdout `0.913` due to symmetric-motion pan cancellation).
- Session 4: L2 code proposal (`scene-L2-agency-dsp`: 5 Agency DSP synthesis constraints + composite area sub-coupling + composite `vx` felt slide + 3-voice burst polyphony budget) lifted dev `0.942 -> 0.981` (`9/9`), holdout `reel2` `0.913 (8/9) -> 0.963 (9/9)`, and `launch` to `0.987 (9/9)`. Subsequent L1 parameter cycle `scene-1795031292-1` was **ACCEPTED**, lifting dev to **`0.987` (`9/9`)**, holdout `reel2` to **`0.968` (`9/9`)**, and holdout `launch` to **`0.993` (`9/9`)**.
