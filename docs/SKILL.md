# SKILL: write a motionvid timeline (for LLM agents)
Output ONE JSON object. Times in seconds, positions in pixels (default 1920×1080).
```json
{"fps":30,"duration":6,"width":1920,"height":1080,
 "elements":[{"id":"logo","kind":"shape","tracks":{"x":[{"t":0.2,"v":-300},{"t":0.9,"v":960,"ease":"inCubic"}]}}],
 "cuts":[{"t":4.4,"kind":"wipe"}],
 "sfx":[{"t":5.2,"role":"riser","dur":0.8,"gain_db":-10}]}
```
Rules: keyframes sorted by time; `ease` belongs to the keyframe the segment ENDS on. Eases: linear, inQuad, outQuad, inOutQuad,
inCubic, outCubic, inOutCubic, inExpo, outExpo, outBack, outBounce.
- Want a thud on arrival → end a fast move with an ease-in (inCubic/inExpo/linear). Soft landing → outCubic (whoosh only).
- Pop-in → scale 0.2→1 with outBack in 0.12–0.35 s. Typewriter → `"type":{"t":3,"cps":14,"n":22}`.
- Cut kinds: cut, flash, wipe, glitch, dissolve. Build-ups: `sfx` with role riser/swell ending on the hit time.
- Never place sound times by hand unless you need a hint; the compiler derives them. `sfx.t` is the *heard hit* time.
Roles: see `src/motionvid/sonic/score.py` `EVENT_ROLES` (47: whoosh, impact, ui_pop, riser, swell, click, bell, sub_drop, glitch, ...).
Run: `python -m motionvid render tl.json out/ [--bed wind]` → `out/audio.wav`, `out/cues.json`, `out/preview.html`.
