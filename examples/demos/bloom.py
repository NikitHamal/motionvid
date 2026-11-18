"""Bloom: wellness app, vertical 9:16. 32 s, 60 fps, 5 acts. Run: python examples/demos/bloom.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, three  # noqa: E402

S = Scene(32, "cream", fps=60, width=1080, height=1920)
W, H = S.W, S.H
CX = W / 2

# Act 1 (0-6): promise
S.add("a_b1", "blob", "mint", n=7, w=1000, x=CX, y=1650, amp=[(0, 0.04), (6, 0.16, "inOutSine")], rotation=[(0, 0), (6, 60)], scale=[(0.2, 0), (1.2, 1, "spring")])
S.add("a_b2", "blob", "butter", n=6, w=520, x=880, y=330, amp=[(0, 0.05), (6, 0.2, "inOutSine")], rotation=[(0, 0), (6, -90)], scale=[(0.4, 0), (1.4, 1, "spring")])
S.sfx(0.3, "pop", 0.3, -14, 0)
S.sfx(0.5, "pop", 0.3, -14, 0.5)
S.headline("a_1", "Small", 0.5, 760, 300, "ink", dur=1.0)
S.headline("a_2", "habits.", 1.0, 1030, 250, "coral", dur=1.0)
three.orb(S, "a_o", 2.0, 200, 1200, 170, "pink")
S.iris(6.0, "mint", CX, 1380)

# Act 2 (6-13): streak
b = 6.0
S.headline("s_h", "Streak.", b + 0.3, 230, 220, "ink", dur=0.9)
rings = [("coral", 560, 0.86), ("butter", 430, 0.7), ("ink", 300, 0.52)]
its = [x for i, (c, d, to) in enumerate(rings) for x in ui.progress_ring(c, d, b + 1.4 + i * 0.3, 1.8, to, 36, 0, -80, "sand")]
cnt = ui.counter("ink", 170, 0, -80, 0, 12, b + 2.0, 1.6)
S.count(cnt, b + 2.0, b + 3.6, 0, 12, ticks=6)
ui.phone(S, "s_ph", b + 0.4, CX, 1060, 1280, "ink", "white", items=[*its, cnt, *ui.bars([.3, .5, .45, .7, .6, .9, .8], b + 3.2, 460, 190, ["coral", "butter", "mint"], y0=480)],
         rx=[(b + 0.4, -8), (b + 6, -2)], ry=[(b + 0.4, -50), (b + 1.5, -12, "m3Dec"), (b + 6.8, 14, "inOutSine")])
S.wipe(13.0, "butter", "y", 1)

# Act 3 (13-20): check in
b = 13.0
S.headline("c_h", "Check in.", b + 0.3, 230, 190, "ink", dur=0.9)
for i, col in enumerate(["coral", "mint", "pink", "cream"]):
    t = b + 0.8 + i * 0.3
    y = 560 + i * 270
    on = b + 2.4 + i * 0.5
    ui.card(S, f"c_c{i}", t, [(t, -700), (t + 0.8, CX, "spring")], y, 880, 200, "white", 100,
            [item("circle", col, w=110, x=-340), ui.pill(250, 30, "ink", x=-130, y=-18), ui.pill(160, 24, "sand", x=-175, y=26), *ui.toggle(S, 300, 0, on, "mint", 170)], sound="swipe")
    S.add(f"c_k{i}", "path", "ink", pts=[[-34, 0], [-8, 26], [36, -24]], stroke=16, x=CX - 340, y=y, p=[(on + 0.15, 0), (on + 0.45, 1, "m3Dec")])
S.iris(20.0, "pink", CX, 1700)

# Act 4 (20-26): feel it
b = 20.0
S.appear(S.add("f_card", "group", items=[*ui.progress_ring("ink", 720, b + 0.8, 2.2, 0.92, 52, 0, 0, "white")], x=CX, y=860, w=720, h=720), b + 0.5, sound="pop")
cn = S.place("f_n", ui.counter("ink", 280, CX, 860, 0, 92, b + 0.8, 2.0, suf="%"))
S.appear(cn, b + 0.8, sound=None, frm=0.9)
S.count(cn, b + 0.8, b + 2.8, 0, 92, ticks=9)
S.sfx(b + 3.0, "chime", 0.6, -11, 0, freq=784)
three.orbit_spheres(S, "f_s", b + 0.5, b + 5.8, CX, 860, 520, 1000, ["butter", "coral", "mint", "cream"], 150, 1.0)
S.headline("f_h", "Feel it.", b + 1.2, 1560, 250, "ink", dur=1.0)
S.wipe(26.0, "ink", "x", 1)

# Act 5 (26-32): brand
b = 26.0
S.add("b_o", "sphere", "mint", w=900, x=CX, y=860, scale=[(b + 0.1, 0), (b + 1.0, 1, "spring")])
for i, c in enumerate(["butter", "pink", "coral"]):
    S.add(f"b_r{i}", "ring", c, stroke=16, x=CX, y=860, w=[(b + 0.4 + i * .3, 700), (b + 1.5 + i * .3, 2600, "m3Dec")], opacity=[(b + 0.39 + i * .3, 0), (b + 0.4 + i * .3, 1), (b + 1.5 + i * .3, 0)])
S.headline("b_n", "Bloom", b + 0.7, 860, 250, "ink", mode="split", dur=1.1)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(31, 0), (32, 1, "inQuad")])

S.save(Path(__file__).with_name("bloom.json"))
