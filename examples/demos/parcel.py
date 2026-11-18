"""Parcel: delivery service. 34 s, 60 fps, 5 acts. Run: python examples/demos/parcel.py"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, three  # noqa: E402

S = Scene(34, "butter", fps=60)
W, H = S.W, S.H

# Act 1 (0-6): promise
S.headline("a_1", "Door", 0.3, 400, 330, "ink", dur=1.0)
S.headline("a_2", "to door.", 0.8, 700, 250, "tomato", dur=1.0)
bx = three.box(S, "a_b", 1.0, 1560, 860, 230, "tomato", rx=-20, ry=(10, 200), t1=5.8, items=[ui.pill(120, 18, "cream", y=-30), ui.pill(70, 18, "cream", x=-25, y=10)])
three.orb(S, "a_o", 1.6, 1640, 280, 150, "ink")
S.cam(zoom=[(0, 1.05), (6, 1, "inOutSine")])
S.wipe(6.0, "ink", "x", -1)

# Act 2 (6-14): route
b = 6.0
S.headline("r_h", "Every stop.", b + 0.3, 170, 190, "cream", dur=0.9)
route = [(300, 820), (620, 520), (960, 760), (1300, 440), (1640, 700)]
pts = [[x, y] for x, y in route]
S.add("r_p", "path", "#4A4036", pts=[[a - 0, c] for a, c in route], x=0, y=0, stroke=28, p=[(b + 0.8, 0), (b + 1.6, 1, "m3Std")])
S.add("r_q", "path", "cream", pts=pts, x=0, y=0, stroke=10, p=[(b + 1.0, 0), (b + 5.4, 1, "inOutSine")])
seg = [(b + 1.0 + 4.4 * i / (len(route) - 1)) for i in range(len(route))]
for i, (x, y) in enumerate(route):
    S.add(f"r_n{i}", "circle", "butter" if i < 4 else "tomato", w=64, x=x, y=y, scale=[(seg[i] - 0.1, 0.3), (seg[i] + 0.35, 1, "spring")], opacity=[(b + 0.8, 0), (b + 0.81, 1)])
    S.sfx(seg[i], "chime" if i == 4 else "pop", 0.4, -13, S.pan_of(x), freq=659)
three.box(S, "r_b", b + 1.0, [(b + 1.0, route[0][0])] + [(seg[i], route[i][0], "inOutSine") for i in range(1, 5)], [(b + 1.0, route[0][1] - 90)] + [(seg[i], route[i][1] - 90, "inOutSine") for i in range(1, 5)], 120, "tomato", rx=-22, ry=(0, 360), t1=b + 5.4, sound="swipe")
S.iris(14.0, "tomato", 1640, 700)

# Act 3 (14-21): volume
b = 14.0
S.headline("v_h", "Any volume.", b + 0.3, 160, 190, "ink", dur=0.9)
cols = ["cream", "ink", "butter"]
for r in range(2):
    for c in range(4):
        i = r * 4 + c
        three.box(S, f"v_b{i}", b + 0.8 + i * 0.12, 420 + c * 360, 400 + r * 240, 200, cols[i % 3], h=170, d=200, rx=-24, ry=(24, 30 + i * 6), t1=b + 6.5, sound="pop" if i % 2 == 0 else None)
cn = S.place("v_n", ui.counter("ink", 160, 960, 900, 0, 1284, b + 2.2, 2.0, suf=" parcels")); S.appear(cn, b + 2.2, sound=None)
S.count(cn, b + 2.2, b + 4.2, 0, 1284, ticks=9)
S.wipe(21.0, "cream", "y", 1)

# Act 4 (21-28): arriving
b = 21.0
ui.phone(S, "t_ph", b + 0.3, 600, 590, 900, "ink", "butter", items=[
    ui.text("Arriving", "ink", 60, y=-250, weight=700), ui.counter("ink", 110, 0, -90, 12, 2, b + 1.6, 2.4, suf=" min"),
    *ui.progress_ring("tomato", 330, b + 1.6, 2.4, 0.9, 30, 0, 170, "cream")], rx=-4, ry=[(b + 0.3, -50), (b + 1.4, -14, "m3Dec"), (b + 6.5, 12, "inOutSine")])
S.headline("t_h", "On the way.", b + 0.6, 380, 170, "ink", x=1400, dur=0.9)
ui.button(S, "t_btn", b + 2.4, 1400, 640, 480, 140, "Track", "ink", "butter", press=b + 4.6)
ui.cursor(S, "t_cur", [(b + 3.3, 1750, 940), (b + 4.6, 1420, 660, "m3Dec")], [b + 4.6])
ui.notification(S, "t_n", b + 5.2, 1400, 900, 600, 130, "Delivered", "ink", "mint", "cream")
S.iris(28.0, "ink", 1400, 900)

# Act 5 (28-34): brand
b = 28.0
three.box(S, "b_x", b + 0.2, 960, 400, 340, "tomato", rx=-18, ry=(-30, 240), t1=b + 5.6, items=[ui.pill(240, 30, "cream", y=-60), ui.pill(150, 30, "cream", x=-45, y=20)])
for i, c in enumerate(["butter", "cream", "tomato"]):
    S.add(f"b_r{i}", "ring", c, stroke=14, x=960, y=470, w=[(b + 0.9 + i * .3, 440), (b + 2.0 + i * .3, 2400, "m3Dec")], opacity=[(b + 0.89 + i * .3, 0), (b + 0.9 + i * .3, 1), (b + 2.0 + i * .3, 0)])
S.headline("b_n", "Parcel", b + 0.9, 830, 260, "butter", mode="split", dur=1.1)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(33, 0), (34, 1, "inQuad")])

S.save(Path(__file__).with_name("parcel.json"))
