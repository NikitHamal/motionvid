# Design rules and owner preferences (single source; tests in tests/test_rules.py enforce what can be enforced)

## Hard rules
- No box shadows or text shadows. No emojis anywhere (UI, docs, code). No LIVE badges. No blue or purple gradients.
- Palette: cream, ink, coral, lime, butter, pink, mint. Font: Bricolage Grotesque.
- Cut taglines, helper text and secondary labels. If a screen needs them to make sense, fix the layout instead.
- A corner is never unrounded, not even for one frame. Radius transitions use `--ease-shape` (no overshoot) and only between two real radii;
  never animate a radius from or to `--shape-full` (999px); springs may animate transforms only. Cause of the old bug: a spring overshoots below 0, a negative radius clamps to 0.
- Play/pause is one button driven by `data-playing`, never by `hidden` on inline svg.
- The GitHub button carries the GitHub mark. Nav hover and press animations stay (rounded-to-rounded shape morph).
- Material 3 Expressive: solid containers, extra-large shapes, spring motion, big type.

## Product preferences
- Keep every version. `docs/media/v0.x/` is frozen once published; new work becomes a new version and a new entry in `docs/versions.json`.
- Every evolution is shown: site cards and the FlawBench table list each version side by side.
- Decide for UX, DX and AX together without breaking anything: readable site, one-command build, JSON in and JSON out for agents.
- Docs are never duplicated. State lives in `STATUS.md`, rules here, agent manual in `AGENT.md`. Extend in place; pick up where the last session ended.
- Showreel quality bar: 15 s or more, dynamic, motion blur, sound bound to the motion, loudness -16 LUFS and -1.0 dBTP.
