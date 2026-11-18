"""Lumen: fintech app launch. 38 s, 60 fps, 6 acts. Run: python examples/demos/lumen.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, three  # noqa: E402

S = Scene(38, "cream", fps=60)
W, H = S.W, S.H

# Act 1 (0-6.2): the promise
S.headline("a_t1", "Money", 0.35, 430, 300, "ink", dur=1.0)
S.headline("a_t2", "moves.", 0.75, 700, 300, "coral", dur=1.0)
three.orb(S, "a_o1", 0.6, 1620, 300, 280, "lime")
three.orb(S, "a_o2", 0.9, 1730, 760, 170, "pink")
three.orb(S, "a_o3", 1.1, 250, 820, 200, "butter")
three.box(S, "a_b", 1.3, 260, 270, 180, "mint", rx=-24, ry=(10, 80), t1=6)
S.cam(zoom=[(0, 1), (6.2, 1.07, "inOutSine"), (6.3, 1)])
S.iris(6.2, "ink", 1620, 300)

# Act 2 (6.2-13): the app
b = 6.2
bal = ui.counter("coral", 100, 0, -250, 0, 48200, b + 1.2, 1.8, pre="$")
S.count(bal, b + 1.2, b + 3.0, 0, 48200)
ui.phone(S, "p_phone", b + 0.25, 640, 560, 940, "cream", "white",
         rx=[(b + 0.25, -10), (b + 5, -4)], ry=[(b + 0.25, -62), (b + 1.3, -18, "m3Dec"), (b + 6.5, 12, "inOutSine")],
         items=[ui.text("Balance", "ink", 44, y=-340, weight=600), bal,
                *ui.bars([.35, .55, .42, .8, .62, .95], b + 2.2, 330, 240, ["coral", "lime", "butter", "mint", "pink", "coral"], y0=250),
                ui.pill(300, 70, "ink", y=-120), ui.text("+ 12%", "lime", 38, y=-120, weight=800)])
S.headline("p_h1", "One tap.", b + 1.0, 330, 190, "cream", x=1360, dur=0.9)
ui.button(S, "p_btn", b + 2.6, 1360, 640, 520, 140, "Send", "coral", press=b + 4.9)
ui.cursor(S, "p_cur", [(b + 3.7, 1700, 900), (b + 4.9, 1380, 650, "m3Dec")], [b + 4.9])
ui.notification(S, "p_note", b + 5.4, 1360, 860, 640, 130, "Sent", "mint", "ink")
S.wipe(13.0, "lime", "x", 1)

# Act 3 (13-20): cards
b = 13.0
S.headline("c_h", "Every card.", b + 0.3, 200, 170, "ink", dur=0.9)
for i, (col, x, y, ink) in enumerate([("ink", 520, 640, "cream"), ("coral", 960, 600, "ink"), ("white", 1400, 640, "ink")]):
    t = b + 0.9 + i * 0.22
    ui.card(S, f"c_card{i}", t, x, y, 520, 330, col, 56, [
        item("circle", "butter" if col != "coral" else "ink", w=70, x=-160, y=-90), ui.text(f"•••• {4021 + i * 117}", ink, 44, y=70, weight=700),
        ui.pill(200, 22, ink, x=-110, y=-10)],
        rx=[(t, 10), (t + 3, 10)], ry=[(t, -80), (t + 0.9, [-14, 0, 14][i], "spring"), (b + 6.5, [-6, 0, 6][i], "inOutSine")])
S.slats(20.0, "cream", 6)

# Act 4 (20-27): growth
b = 20.0
curve = [[-440, 220], [-300, 150], [-200, 190], [-60, 40], [60, 90], [200, -90], [320, -60], [440, -200]]
ui.window(S, "g_win", b + 0.3, 640, 590, 1000, 640, "white", "sand", items=ui.line(curve, b + 1.0, 2.0, "coral", 14), ry=[(b + 0.3, -6), (b + 6.5, 6, "inOutSine")], rx=-4)
big = S.place("g_big", ui.counter("ink", 250, 1520, 380, 0, 24, b + 0.8, 1.6, pre="+", suf="%"))
S.appear(big, b + 0.8, sound=None, frm=0.9)
S.count(big, b + 0.8, b + 2.4, 0, 24)
for i, (c, to, x) in enumerate([("mint", .8, 1290), ("coral", .62, 1520), ("butter", .9, 1750)]):
    ui.card(S, f"g_r{i}", b + 2.2 + i * 0.18, x, 800, 210, 210, "white", 105, [*ui.progress_ring(c, 150, b + 2.5 + i * 0.18, 1.2, to, 22)])
S.wipe(27.0, "coral", "y", -1)

# Act 5 (27-33): zero fees
b = 27.0
S.headline("z_h1", "Zero", b + 0.3, 300, 330, "ink", x=760, dur=1.0)
S.headline("z_h2", "fees.", b + 0.7, 590, 330, "cream", x=760, dur=1.0)
ui.card(S, "z_tg", b + 1.6, 1560, 560, 420, 190, "ink", 95, ui.toggle(S, 0, 0, b + 2.3, "mint", 220))
three.orbit_spheres(S, "z_o", b + 0.4, b + 6.0, 960, 880, 820, 200, ["butter", "lime", "pink", "ink"], 150, 1.2)
S.iris(33.0, "ink", 960, 540)

# Act 6 (33-38): brand
b = 33.0
for i, c in enumerate(["butter", "lime", "mint"]):
    S.add(f"b_r{i}", "ring", c, stroke=14, x=960, y=520, w=[(b + 0.3 + i * .3, 420), (b + 1.3 + i * .3, 2200, "m3Dec")], opacity=[(b + 0.29 + i * .3, 0), (b + 0.3 + i * .3, 1), (b + 1.3 + i * .3, 0)])
S.add("b_halo", "sphere", "coral", w=520, x=960, y=500, scale=[(b + 0.05, 0), (b + 0.9, 1, "spring")])
S.headline("b_n", "Lumen", b + 0.5, 520, 300, "cream", mode="split", dur=1.1)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(37, 0), (38, 1, "inQuad")])

S.save(Path(__file__).with_name("lumen.json"))
