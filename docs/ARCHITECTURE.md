# Architecture
```
LLM/agent ──► timeline.json ──► cues.compile_cues (physics, genome.json) ──► cues[]
                                                                         │
 audio.wav ◄── compose.render_cues (anchor-align, cache, parallel) ◄─────┘
 preview.html (canvas animation + audio)      cues.json (explainable: every cue has `why`)
```
- **Timeline**: elements with keyframed tracks (`x y scale opacity rotation`), `cuts`, typed text, explicit `sfx` hints.
- **Cues**: `t` is the instant the hit must be *heard*. Physics: peak speed → whoosh; abrupt stop (speed collapses inside
  `impact_stop_window`) → impact; scale rise → ui_pop at apex; fast fade-in → soft pop; typed chars → click; cuts by kind.
  Intensity (speed) → gain through `intensity_gamma`; x position → pan.
- **Anchor**: each rendered clip's audible hit = first 70 %-of-peak crossing of a 5 ms envelope. Placement subtracts it, sample exact.
- **Cache/parallel**: clips keyed (role, duration bucket, 3 variants); distinct keys rendered in a process pool; pan applied as
  equal-power balance on the centred clip (identical to upstream for mono roles).
- **Sonic**: vendored 47-role DSP (numpy only). No torch, no weights.
- **Why no model on the motion path**: motion timing is a known quantity; a model would only add error and megabytes.
  Models are reserved for what code can't know: text → timeline planning and timbre detail (GPU phase).
