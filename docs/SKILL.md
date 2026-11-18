# motionvid skill v2: make a top-tier motion video with sound from a prompt

You are the motion designer. Write a Python scene with `motionvid.kit`, check it as a contact sheet, render it. Motion and sound are written together, so they cannot drift apart. Look rules: `docs/DESIGN.md`. Reference scenes: `examples/demos/*.py` (atlas, pulse, ledgerly, noir, terra, kernel).

## Loop (never skip the check)
1. Brief -> category, palette, 6 acts. 2. Copy the nearest demo to `examples/demos/<name>.py`. 3. `python scripts/build_demos.py sheet <name>` and LOOK at `out/<name>_sheet.png` (8 frames).
4. Fix every defect in the kit if it is a pattern, in the script if it is a one-off. 5. Register in `DEMOS` of `scripts/build_demos.py`, then `python scripts/build_demos.py <name>`.
Real media first: `python scripts/get_assets.py` (photos `docs/media/assets/*.jpg`, footage `docs/media/footage/<id>/`, credits in `credits.json`). Add new files by extending `extra_photos.json` / `extra_videos.json`.

## Structure that works (45-60 s, 6 acts of 7-10 s)
Hook (promise, 2 lines) -> Product (real UI on a 3D device) -> Proof (one number counting up) -> Texture (3D object or real footage) -> Reach (second device, globe, carousel) -> Brand (name, one button). Each act ends on a transition; the transition hit is the sound of the cut.
Never repeat an act recipe across acts, and pick a different hero object per video: phone, laptop, photo cube, ring carousel, bar tower, coin stack, globe, rack, extruded logo, torus rings.
One idea per act, at most 3 text elements, no taglines, no helper text, no secondary labels.

## Kit API (`from motionvid.kit import Scene, item, ui, mesh, screens, media`)
- `S = Scene(duration, bg, fps=60, width=1920, height=1080)`; vertical `1080x1920`, square `1080x1080`.
- Text: `S.headline(id, text, t, y, size, color, mode='mask'|'split'|'type', x=)`. Counters: `ui.counter(...)` -> `S.place` -> `S.appear` -> `S.count(el, t0, t1, a, b)`.
- Real media: `media.photo(name, w, h, r, zoom=[(t,1),(t+8,1.2,'inOutSine')], px=, py=)` (Ken Burns); `media.footage(name, w, h, t0, r, ss, loop='pp'|'wrap'|'clamp', tint, tintA)`; add as element with `S.add(id, 'image', None, src='media/assets/x.jpg', ...)` or `S.add(id, 'video', None, **footage_props)`.
- Real UI screens (flat items, animate in, add sound): `screens.travel_feed product_page activity dashboard site_home wallet code_editor`, helpers `rise shift tap nav`. Put them on a device `screen` or in `ui.window` / `ui.card`.
- 3D mesh (`mesh.mesh(S, id, t, x, y, parts, size, rx, ry, rz, persp)`): parts `part('rbox'|'cyl'|'sphere'|'cone'|'capsule'|'torus'|'gem'|'extrude', color, w h d r b len R, pos=[x,y,z], rot=[rx,ry,rz], gloss=, faces={}, screen={...})`. Ready objects: `phone3d laptop3d bars3d globe rack coin cube_photos orbit_parts`. Lists on part x y z rx ry rz s opacity w h d r R are keyframes. All parts of one mesh depth-sort together, so orbiting spheres can pass in front of and behind a cube correctly.
- Flat groups with depth: `ui.card ui.window ui.phone`, `three.stack`, `three.orbit_spheres` (older, flat-shaded).
- Transitions (end time = hit time): `S.iris S.wipe S.slats`. Camera: `S.cam(zoom=[...])`, a 4-6 % push per act. Last element: the `outro` ink rect over the final second.
- Sound: every recipe adds its hint. Manual: `S.sfx(t, role, dur, gain_db, pan, freq=)`, roles `click pop chime toggle notify swipe tick pluck whoosh impact riser`.

## Motion rules
- Ease by purpose: arrivals `spring`, big moves and counters `m3Dec`, cursor and wipes `m3Std`, exits and covers `m3Acc`, ambient `inOutSine`. Never `linear` except trim and scrub.
- Durations: UI pop 0.5-0.6 s, headline 0.9-1.1 s, count-up 1.6-2.4 s, transition 0.45-0.55 s, hold a finished frame 1.2 s+. Stagger siblings 0.18-0.3 s.
- 3D: a device enters at `ry -45 -> -10` and keeps drifting over the whole act (never freeze); rx -6 to -22; `persp` 1700-2400 (higher = flatter). Spin a hero at most 180 degrees per act. Bevel radius 10-14 % of the short side. Parts get `gloss` 10-26 for a lit edge.
- Real UI on a device must show an action: a counter running, a toggle, a press, a typed line. Photos always carry a slow zoom.
- Z order is element order: headlines added after a mesh draw over it; add them last when they overlap.
- Text fit (width ~= chars * 0.56 * size) must stay under 85 % of the frame: at 1080 wide, 9 chars max 180 px. Two lines max per headline block. Min 40 px at 1080p.
- Footage: dull it with a flat `tint` (ink or the act color, `tintA` 0.25-0.35) when text sits on it. Never over-stretch: footage frames are 960 px wide, show them at 1700 px wide at most.

## Sound rules (the engine does the rest)
Every visible action has a hint. Cuts get whoosh pre-roll + impact + sub automatically. Gains: UI -9 to -15 dB, ticks -21, chimes -11. Pan follows x. Do not stack more than 3 simultaneous hits. Master -16 LUFS, no triggers in the last 1.4 s.

## Palette and shape
cream ink coral lime butter pink mint clay moss sand tomato sage. No blue or purple, no gradients, no shadows, no emojis, no status badges. Real photos with blue sky are allowed; UI chrome never is blue. Extra-large rounded shapes, solid containers, Bricolage Grotesque.

## Prompt -> video (what the Create page does)
Brief fields: name, category, 3 features, one stat, CTA. Category picks the palette, hero object, device screen and act order (`docs/engine/planner.js`). Same brief + different seed = different hero object and layout.

## Anti-patterns
Stacked text walls, more than 3 colors in an act, linear easing, a transition without a hit, silent UI actions, a static 3D object, the same hero object in two acts, an act shorter than 6 s, a device with an empty screen, text over untinted footage, a hero that is not centered in its act, tiny photos (a photo is a hero: 600 px+).
