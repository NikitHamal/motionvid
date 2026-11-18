"""Forge: developer tool launch. 34 s, 60 fps, 5 acts. Run: python examples/demos/forge.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, three  # noqa: E402

S = Scene(34, "ink", fps=60)
W, H = S.W, S.H

# Act 1 (0-6.5): promise
S.headline("a_1", "git push,", 0.3, 420, 250, "cream", dur=1.0)
S.headline("a_2", "shipped.", 0.8, 680, 250, "lime", dur=1.0)
for i, (c, x, y, d) in enumerate([("butter", 300, 220, 160), ("coral", 1650, 300, 220), ("mint", 1560, 880, 150), ("pink", 330, 880, 190)]):
    three.orb(S, f"a_o{i}", 1.2 + i * 0.2, x, y, d, c)
S.cam(zoom=[(0, 1.06), (6.5, 1, "inOutSine")])
S.iris(6.5, "butter", 960, 540)

# Act 2 (6.5-14.5): terminal
b = 6.5
tw, th = 1500, 780
L = -tw / 2 + 80
lines = [("$ forge deploy", "lime", 1.2), ("building 128 modules", "cream", 2.5), ("tests 412 / 412 passed", "mint", 4.0), ("shipped in 4.2s", "butter", 5.6)]
its = [ui.typed(S, s, b + t, 20, L, -230 + i * 100, 56, c, 700) for i, (s, c, t) in enumerate(lines)]
its += [item("rrect", "#3A332A", w=1300, h=34, r="pill", x=0, y=250), item("rrect", "lime", r="pill", h=34, w=[(b + 2.5, 0), (b + 6.2, 1300, "inOutSine")], x=[(b + 2.5, -650), (b + 6.2, 0, "inOutSine")], y=250, z=2)]
ui.window(S, "t_win", b + 0.3, 960, 560, tw, th, "#1F1A15", "#2E2820", items=its, rx=[(b + 0.3, -3), (b + 7, -3)], ry=[(b + 0.3, 24), (b + 1.5, 10, "m3Dec"), (b + 7.5, -8, "inOutSine")])
S.cam(zoom=[(b + 4, 1), (b + 7.8, 1.1, "inOutSine")])
S.wipe(14.5, "lime", "x", -1)

# Act 3 (14.5-21.5): commit graph
b = 14.5
S.cam(zoom=[(14.5, 1)])
S.headline("g_h", "Every branch.", b + 0.3, 170, 190, "ink", dur=0.9)
lanes = [(330, "ink"), (540, "coral"), (750, "moss")]
for i, (y, c) in enumerate(lanes):
    S.add(f"g_l{i}", "path", c, pts=[[220, y], [1700, y]], x=0, y=0, stroke=14, p=[(b + 0.8 + i * 0.2, 0), (b + 2.0 + i * 0.2, 1, "m3Dec")])
    for j in range(6):
        x = 300 + j * 270 + i * 40
        S.add(f"g_n{i}{j}", "circle", "ink" if j % 2 else "white", w=54, x=x, y=y, scale=[(b + 1.4 + j * 0.25 + i * 0.1, 0), (b + 1.9 + j * 0.25 + i * 0.1, 1, "spring")])
        S.sfx(b + 1.45 + j * 0.25 + i * 0.1, "pop", 0.2, -19 + j * 0.3, S.pan_of(x))
for i, (y0, y1) in enumerate([(540, 330), (750, 330)]):
    S.add(f"g_m{i}", "path", "coral" if i == 0 else "moss", pts=[[1500, y0], [1620, y0], [1620, y1], [1740, y1]], x=0, y=0, stroke=14, p=[(b + 4.2 + i * 0.5, 0), (b + 5.0 + i * 0.5, 1, "m3Std")])
S.add("g_b", "sphere", "lime", w=130, x=[(b + 4.2, 1500), (b + 5.0, 1740, "m3Std")], y=[(b + 4.2, 540), (b + 5.0, 330, "m3Std")], scale=[(b + 4.1, 0), (b + 4.5, 1, "spring")])
S.sfx(b + 5.0, "chime", 0.6, -12, 0.3, freq=660)
S.slats(21.5, "ink", 6)

# Act 4 (21.5-28.5): servers
b = 21.5
S.headline("s_h", "Deploy.", b + 0.3, 270, 220, "cream", x=540, dur=0.9)
for i, (c, y) in enumerate([("coral", 720), ("butter", 560), ("lime", 400)]):
    three.box(S, f"s_b{i}", b + 0.6 + i * 0.3, 1350, y, 360, c, h=130, d=300, rx=-22, ry=(30, 8 + i * 6), t1=b + 6.8, sound="pop",
              items=[item("circle", "ink", w=36, x=-120, y=0), ui.pill(150, 20, "ink", x=40, y=0)])
S.place("s_c", ui.counter("lime", 210, 620, 640, 0, 4.2, b + 2.0, 1.8, suf="s", dec=1)); S.appear(S.tl["elements"][-1], b + 2.0, sound=None)
S.count(S.tl["elements"][-1], b + 2.0, b + 3.8, 0, 4.2, ticks=8)
S.place("s_r", ui.progress_ring("lime", 330, b + 3.0, 1.8, 1.0, 26, 620, 880)[1]); S.appear(S.tl["elements"][-1], b + 3.0, sound="chime", frm=0.6)
S.wipe(28.5, "butter", "y", -1)

# Act 5 (28.5-34): brand
b = 28.5
S.add("b_o", "sphere", "coral", w=560, x=960, y=500, scale=[(b + 0.1, 0), (b + 0.9, 1, "spring")])
for i, c in enumerate(["coral", "lime", "mint"]):
    S.add(f"b_r{i}", "ring", c, stroke=14, x=960, y=500, w=[(b + 0.4 + i * .3, 560), (b + 1.5 + i * .3, 2300, "m3Dec")], opacity=[(b + 0.39 + i * .3, 0), (b + 0.4 + i * .3, 1), (b + 1.5 + i * .3, 0)])
S.headline("b_n", "forge", b + 0.6, 520, 300, "ink", mode="split", dur=1.1)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(33, 0), (34, 1, "inQuad")])

S.save(Path(__file__).with_name("forge.json"))
