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
- Session 5: L2 code proposal (`scene-L2-five-root-bugs`: exact scheduler offset rules for `suction`/`whoosh`/`sub+impact`, 24 dB/oct `Q=2.2` resonant LPF sweeps, `92->36 Hz` + `165->62 Hz` + `>2.2 kHz` `tanh` impact, zero-pitch-drop `text_tick` + 1 hero `pluck` per scene, detuned `2093+3136 Hz` `crystal`, continuous `motion_energy`/`pan_x` bed, and `12.85->13.40s` climax riser) lifted dev (`showreel.json`) `0.987 -> 0.996` (`9/9`), holdout 1 (`reel2.json`) `0.968 -> 0.997` (`9/9`), and holdout 2 (`launch.json`) `0.993 -> 1.000` (`9/9`, **3.05x** over classic `0.328`).
- Session 6: L2 code proposal (`studio-L2-rev6`): engine rev 6 from a reviewer audit; new gate-protected StudioBench (17 gates). FlawBench `9/9` held on 5 reels, StudioBench `17/17`. Caveat: `reel2` score `0.997 -> 0.951` (glyph phrasing), logged as next action 3.
