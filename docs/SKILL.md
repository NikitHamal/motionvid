# motionvid skill: make a top-tier motion video with sound from a prompt

You are the motion designer. Write a Python scene with `motionvid.kit`, check it as a contact sheet, render it. Motion and sound are written together, so they cannot drift apart. Read `docs/DESIGN.md` for the look.

## Loop (do not skip the check)
1. Brief -> acts (below). 2. Write `examples/demos/<name>.py` from `examples/demos/lumen.py`. 3. `python scripts/build_demos.py sheet <name>` and look at `out/<name>_sheet.png`.
4. Fix overlap, contrast, dead frames. 5. `python scripts/build_demos.py <name>` (video + audio + poster). Register the id in `DEMOS` in `scripts/build_demos.py`.

## Structure that always works (30-40 s, 5-6 acts of 5-8 s)
Hook (promise in 2 lines) -> Product (UI in 3D, one number counting up, one tap) -> Features (3 cards) -> Proof (big number + rings or chart) -> Brand (name, one URL). Each act ends on a transition, and the transition hit is the sound of the cut.
One idea per act. Max 3 text elements on screen. No taglines, no helper text, no secondary labels: if an act needs them, fix the layout.

## API (all in `from motionvid.kit import Scene, item, ui, three`)
- `S = Scene(duration, bg, fps=60, width=1920, height=1080)`; vertical: `width=1080, height=1920`.
- Tracks: a list of `(t, value[, ease])`. A number on `x y scale opacity rotation rx ry rz z` is a constant. Static: `w h r text size ...`.
- Text: `S.headline(id, text, t, y, size, color, mode='mask'|'split'|'type')`. Counters: `ui.counter(...)` + `S.count(el, t0, t1, a, b)` (ticks included).
- Components (each adds its sound): `ui.card ui.button(press=t) ui.phone ui.window ui.toggle ui.bars ui.line ui.progress_ring ui.cursor(moves, clicks) ui.notification ui.typed`.
- 3D: `three.box` (solid, spins), `three.orb`, `three.stack` (exploded layers), `three.orbit_spheres`; any group tilts with `rx`/`ry` tracks (perspective, depth via `z`).
- Transitions (end time = hit time): `S.iris(t, color, x, y)`, `S.wipe(t, color, 'x'|'y', sign)`, `S.slats(t, color)`. They hide the previous act for you. Elements added after a transition draw above it.
- Camera: `S.cam(zoom=[...], x=[...], roll=[...])`. A 4-6 % push over an act reads as polish.
- Last element of every video: `S.add("outro", "rrect", "ink", w=W, h=H, x=W/2, y=H/2, opacity=[(T-1, 0), (T, 1, "inQuad")])` (the engine keeps the last 1.4 s trigger-free).
- Sound hints: `S.sfx(t, role, dur, gain_db, pan, freq=..., st=...)`. Roles: `click pop chime toggle notify swipe tick pluck whoosh impact riser`. Use `pluck(freq=...)` in a pentatonic (392 440 523 587 659 784) for melodic moments.

## Motion rules
- Ease by purpose: arrivals `spring` (UI, cards, numbers), `m3Dec` (big moves, counters, charts), `m3Std` (cursor, wipes), exits and covers `m3Acc`, ambient drift `inOutSine`. Never `linear` except trim and scrub.
- Durations: UI pop 0.5-0.6 s, headline 0.9-1.1 s, count-up 1.6-2.4 s, transition 0.45-0.55 s, hold a finished frame for at least 1.2 s.
- Stagger siblings 0.18-0.3 s; never animate 3+ things at once with the same ease and start.
- Depth: tilt phones/cards `ry` -60 -> -14 on entry, then drift +-12 over the act. Layer order is z first, then position. Put content on `z >= 1` above a body.
- Hierarchy: headline 170-300 px, UI text 40-60 px, one accent color per act. Contrast: ink on light, cream on ink. Never ink text over an ink shape.
- Text fit: width ~= chars * 0.56 * size. Keep inside 85 % of the frame. Two lines max.
- Everything animates in and out. An element with no `appear` is visible from t = 0.

## Sound rules (the engine does the rest)
- Every visible action has a hint: pop on arrival, `click` on press, `toggle` on switch, `notify` on a notification, `swipe` on mask reveal, `chime` on success. Cuts get whoosh pre-roll + impact + sub automatically.
- Gains: UI -9 to -15 dB, ticks -21, chimes -11, never louder than the cut hit. Pan follows x (`S.pan_of(x)`).
- Do not stack more than 3 simultaneous hits. The engine thins ticks (90 ms) and keeps the master at -16 LUFS.

## Palette and shape
cream ink coral lime butter pink mint + clay moss sand tomato sage. No blue or purple, no gradients, no shadows, no emojis, no status badges. Rounded extra-large shapes, solid containers, Bricolage Grotesque.

## Prompt -> video (what the Create page does)
Brief fields: name, category, 3 features, one stat, CTA. Category picks the palette and hook. `docs/engine/planner.js` is the rule-based reference; copy its act structure and adapt it.

## Anti-patterns
Stacked text walls, more than 3 colors in an act, linear easing, a transition without a hit, silent UI actions, an act shorter than 4 s, text under 40 px at 1080p, content that never leaves the frame, a hero that is not centered in its act.
