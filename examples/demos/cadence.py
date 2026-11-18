"""Cadence: 3D hardware reveal (a speaker). 36 s, 60 fps, 5 acts. Run: python examples/demos/cadence.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, three  # noqa: E402

S = Scene(36, "sand", fps=60)
W, H = S.W, S.H
NOTES = [392, 440, 523, 587, 659, 784, 659, 587]


def face(t):
    return [item("circle", "ink", w=230, y=-10), item("ring", "cream", w=300, stroke=10, y=-10), item("circle", "clay", w=70, y=-10, scale=[(t, 0.6), (t + 0.6, 1, "spring")]),
            ui.pill(120, 14, "ink", y=120)]


# Act 1 (0-6): promise
S.headline("a_1", "Sound,", 0.3, 420, 270, "ink", x=720, dur=1.0)
S.headline("a_2", "made solid.", 0.8, 700, 200, "clay", x=720, dur=1.0)
three.box(S, "a_b", 1.0, 1520, 560, 360, "clay", h=360, d=360, rx=-20, ry=(10, 170), t1=6.0, items=[item("circle", "ink", w=170), item("circle", "cream", w=50)])
three.orb(S, "a_o", 1.8, 1700, 250, 150, "butter")
S.cam(zoom=[(0, 1), (6, 1.06, "inOutSine")])
S.wipe(6.0, "clay", "x", 1)

# Act 2 (6-14): the speaker plays
b = 6.0
three.box(S, "d_box", b + 0.3, 960, 470, 700, "cream", h=420, d=380, rx=-14, ry=(-34, 24), t1=b + 7.6, items=face(b + 1.0),
          faces={"top": "#F6EFE3", "left": "#E9DCC3", "right": "#E9DCC3"})
for i, f in enumerate(NOTES):
    t = b + 1.3 + i * 0.85
    S.add(f"d_w{i}", "ring", "cream", stroke=12, x=[(t, 760 + 40 * (i % 3))], y=[(t, 470)], w=[(t, 300), (t + 1.1, 1500, "m3Dec")], h=[(t, 300), (t + 1.1, 1500, "m3Dec")], opacity=[(t - 0.001, 0), (t, 0.9), (t + 1.1, 0)])
    S.sfx(t, "pluck", 0.5, -10, S.pan_of(760 + 40 * (i % 3)), freq=f)
S.headline("d_h", "Feel the beat.", b + 0.5, 900, 150, "cream", dur=0.9)
S.iris(14.0, "ink", 960, 600)

# Act 3 (14-22): exploded
b = 14.0
S.headline("e_h", "Layer by layer.", b + 0.3, 170, 170, "cream", dur=0.9)
top = [item("circle", "ink", w=200, y=-10), item("ring", "cream", w=260, stroke=8, y=-10), ui.pill(160, 16, "ink", y=120)]
three.stack(S, "e_st", b + 0.5, 960, 600, 760, 440, ["ink", "coral", "butter", "cream"], b + 2.2, 130, 70, rx=(-12, -56), ry=(-6, 28), t1=b + 7.4, items_per_layer=[[], [], [], top])
S.slats(22.0, "butter", 6)

# Act 4 (22-29): pick one
b = 22.0
S.headline("p_h", "Pick one.", b + 0.3, 170, 190, "ink", dur=0.9)
for i, (c, x) in enumerate([("clay", 520), ("ink", 960), ("mint", 1400)]):
    three.box(S, f"p_b{i}", b + 0.8 + i * 0.25, x, 600, 300, c, h=300, d=300, rx=-16, ry=(-30 + i * 20, 40 + i * 20), t1=b + 6.6, items=[item("circle", "cream", w=140), item("circle", c if c != "ink" else "coral", w=44)])
ui.cursor(S, "p_cur", [(b + 2.6, 1700, 960), (b + 3.8, 1000, 780, "m3Dec")], [b + 3.8])
S.add("p_sel", "ring", "ink", stroke=12, x=960, y=600, w=[(b + 3.85, 380), (b + 4.4, 470, "spring")], opacity=[(b + 3.84, 0), (b + 3.85, 1)])
S.sfx(b + 3.9, "chime", 0.6, -12, 0, freq=659)
c = S.place("p_n", ui.counter("ink", 200, 960, 950, 0, 48, b + 4.2, 1.6, suf=" h")); S.appear(c, b + 4.2, sound=None)
S.count(c, b + 4.2, b + 5.8, 0, 48, ticks=7)
S.iris(29.0, "ink", 960, 950)

# Act 5 (29-36): brand
b = 29.0
S.add("b_o", "sphere", "clay", w=640, x=960, y=500, scale=[(b + 0.1, 0), (b + 1.0, 1, "spring")])
S.headline("b_n", "Cadence", b + 0.7, 520, 270, "cream", mode="split", dur=1.1)
three.orbit_spheres(S, "b_s", b + 0.8, b + 6.0, 960, 800, 800, 260, ["butter", "mint", "pink", "lime"], 120, 1.0)
for i, cc in enumerate(["butter", "pink", "mint"]):
    S.add(f"b_r{i}", "ring", cc, stroke=14, x=960, y=500, w=[(b + 0.4 + i * .3, 640), (b + 1.5 + i * .3, 2400, "m3Dec")], opacity=[(b + 0.39 + i * .3, 0), (b + 0.4 + i * .3, 1), (b + 1.5 + i * .3, 0)])
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(35, 0), (36, 1, "inQuad")])

S.save(Path(__file__).with_name("cadence.json"))
