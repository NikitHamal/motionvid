"""Orbit: SaaS analytics dashboard. 36 s, 60 fps, 5 acts. Run: python examples/demos/orbit.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, three  # noqa: E402

S = Scene(36, "sage", fps=60)
W, H = S.W, S.H

# Act 1 (0-6): promise
S.headline("a_1", "Every metric.", 0.3, 400, 230, "ink", dur=1.0)
S.headline("a_2", "One screen.", 0.8, 660, 230, "moss", dur=1.0)
for i, (lab, col, x, y) in enumerate([("MRR", "butter", 330, 190), ("Churn", "coral", 1640, 250), ("NPS", "lime", 1500, 900), ("Trials", "pink", 400, 880)]):
    ui.card(S, f"a_c{i}", 1.2 + i * 0.2, x, y, 280, 110, col, 55, [ui.text(lab, "ink", 44, weight=800)], rz=0,
            rotation=[(1.2 + i * 0.2, [-14, 10, -8, 12][i]), (6, [-6, 4, -3, 6][i], "inOutSine")])
S.cam(zoom=[(0, 1), (6, 1.05, "inOutSine")])
S.wipe(6.0, "ink", "x", 1)

# Act 2 (6-14): dashboard
b = 6.0
kp = []
for i, (lab, a_, v, pre, suf, col) in enumerate([("MRR", 0, 128, "$", "k", "coral"), ("Users", 0, 24810, "", "", "mint"), ("NPS", 0, 72, "", "", "butter")]):
    x = -440 + i * 440
    c = ui.counter("ink", 84, x, 20, a_, v, b + 1.4 + i * 0.2, 1.8, pre, suf)
    S.count(c, b + 1.4 + i * 0.2, b + 3.2 + i * 0.2, a_, v, ticks=5)
    kp += [item("rrect", col, w=400, h=190, r=44, x=x, y=20, opacity=[(b + 1.1 + i * 0.2, 0), (b + 1.3 + i * 0.2, 1)], scale=[(b + 1.1 + i * 0.2, .85), (b + 1.7 + i * 0.2, 1, "spring")]),
           ui.text(lab, "ink", 38, x=x, y=-50, weight=700), c]
ui.window(S, "d_win", b + 0.3, 960, 560, 1500, 800, "white", "sand",
          items=[*kp, *ui.bars([.3, .45, .4, .6, .55, .8, .7, .95, .85, 1.0], b + 3.0, 1300, 230, ["moss", "lime"], x0=0, y0=330, gap=0.4)],
          rx=-3, ry=[(b + 0.3, -26), (b + 1.6, -8, "m3Dec"), (b + 7.6, 6, "inOutSine")])
ui.cursor(S, "d_cur", [(b + 4.3, 1600, 900), (b + 5.4, 1050, 520, "m3Dec"), (b + 6.6, 560, 540, "m3Std")], [b + 5.4, b + 6.6])
S.cam(zoom=[(b + 4.2, 1), (b + 7.5, 1.14, "inOutSine")], x=[(b + 4.2, 0), (b + 7.5, 40, "inOutSine")])
S.iris(14.0, "lime", 560, 540)

# Act 3 (14-22): funnel
b = 14.0
S.cam(zoom=[(14.0, 1)])
S.headline("f_h", "Spot the leak.", b + 0.3, 170, 190, "ink", dur=0.9)
stages = [("Visit", 1.0, "ink", "cream"), ("Sign up", .74, "moss", "cream"), ("Trial", .46, "coral", "ink"), ("Paid", .21, "white", "ink")]
for i, (lab, f, col, tc) in enumerate(stages):
    t, wd = b + 0.9 + i * 0.28, 1500 * f
    S.group(f"f_s{i}", [item("rrect", col, w=[(t, 0), (t + 0.8, wd, "spring")], x=[(t, -wd / 2), (t + 0.8, 0, "spring")], h=130, r="pill", z=1), ui.text(lab, tc, 52, weight=800, z=2, opacity=[(t + 0.5, 0), (t + 0.7, 1)])],
            x=210 + wd / 2, y=380 + i * 170, w=wd, h=130)
S.add("f_ring", "ring", "coral", stroke=12, x=760, y=805, w=[(b + 4.2, 40), (b + 4.9, 330, "spring")], opacity=[(b + 4.19, 0), (b + 4.2, 1)])
ui.notification(S, "f_n", b + 5.2, 960, 940, 700, 130, "Trial drop 3%", "ink", "coral", "cream")
S.wipe(22.0, "butter", "y", 1)

# Act 4 (22-29): layers
b = 22.0
S.headline("l_h1", "Every", b + 0.3, 400, 200, "ink", x=520, dur=0.9)
S.headline("l_h2", "layer.", b + 0.7, 620, 200, "clay", x=520, dur=0.9)
lay = [[], [], [ui.pill(360, 44, "ink", y=-30), ui.pill(240, 44, "ink", x=-60, y=50)], [*ui.bars([.4, .8, .55, .9], b + 2.5, 360, 150, ["lime"], y0=70), item("path", "ink", pts=[[-200, 60], [-80, -30], [40, 20], [200, -80]], stroke=16, p=[(b + 3, 0), (b + 4, 1, "m3Dec")])]]
three.stack(S, "l_stack", b + 0.5, 1440, 560, 760, 500, ["ink", "coral", "mint", "cream"], b + 1.8, 120, 60, rx=(-14, -58), ry=(0, 30), t1=b + 7, items_per_layer=lay)
S.slats(29.0, "ink", 6)

# Act 5 (29-36): ship it
b = 29.0
S.headline("s_h", "Ship the report.", b + 0.3, 330, 190, "cream", dur=1.0)
S.vanish(ui.button(S, "s_b", b + 1.2, 960, 560, 560, 150, "Send", "lime", press=b + 2.6), b + 3.1, 0.25)
ui.cursor(S, "s_cur", [(b + 1.9, 1500, 880), (b + 2.6, 990, 590, "m3Dec")], [b + 2.6])
for i, c in enumerate(["coral", "mint", "butter"]):
    S.add(f"s_r{i}", "ring", c, stroke=14, x=960, y=560, w=[(b + 2.65 + i * .25, 300), (b + 3.7 + i * .25, 2000, "m3Dec")], opacity=[(b + 2.64 + i * .25, 0), (b + 2.65 + i * .25, 1), (b + 3.7 + i * .25, 0)])
S.add("s_o", "sphere", "lime", w=300, x=960, y=600, scale=[(b + 3.4, 0), (b + 4.1, 1, "spring")])
S.headline("s_n", "Orbit", b + 3.7, 860, 230, "cream", mode="split", dur=1.0)
three.orbit_spheres(S, "s_s", b + 3.5, b + 7.0, 960, 520, 700, 200, ["coral", "butter", "mint"], 130, 0.8)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(35, 0), (36, 1, "inQuad")])

S.save(Path(__file__).with_name("orbit.json"))
