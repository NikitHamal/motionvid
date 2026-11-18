"""Pipeline launch (v0.8): 26 s, 60 fps, 5 acts, kit + engine rev 7. Run: python examples/launch3.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from motionvid.kit import Scene, item, ui, three  # noqa: E402

S = Scene(26, "ink", fps=60)
W, H = S.W, S.H

# Act 1 (0-5.6): prompt
S.headline("a_h", "Prompt.", 0.3, 220, 200, "cream", dur=0.9)
ui.card(S, "a_in", 0.5, 960, 520, 1560, 190, "cream", 95, [ui.typed(S, "a launch video for my app", 1.0, 16, -690, 0, 66, "ink", 700)])
ui.button(S, "a_b", 2.2, 960, 790, 440, 130, "Make", "coral", "ink", press=4.1)
ui.cursor(S, "a_cur", [(3.0, 1500, 960), (4.1, 980, 810, "m3Dec")], [4.1], "cream")
S.iris(5.6, "coral", 960, 800)

# Act 2 (5.6-11): storyboard
b = 5.6
S.headline("b_h", "Storyboard.", b + 0.3, 170, 190, "ink", dur=0.9)
for i, (c, x) in enumerate([("cream", 420), ("lime", 800), ("butter", 1180), ("pink", 1560)]):
    t = b + 0.8 + i * 0.25
    ui.card(S, f"b_c{i}", t, x, 640, 340, 460, c, 48, [item("circle", "ink", w=110, y=-90), ui.pill(220, 26, "ink", y=40), ui.pill(150, 26, "ink", x=-35, y=90)],
            rx=-6, ry=[(t, -85), (t + 0.9, [-12, -4, 4, 12][i], "spring"), (b + 5.2, [8, 3, -3, -8][i], "inOutSine")], sound="swipe")
S.wipe(11.0, "lime", "y", 1)

# Act 3 (11-17): motion
b = 11.0
S.headline("m_h", "Motion.", b + 0.3, 170, 190, "ink", dur=0.9)
ui.phone(S, "m_ph", b + 0.7, 480, 610, 700, "ink", "white", items=[*ui.bars([.4, .7, .5, .9], b + 1.8, 220, 200, ["coral", "mint", "butter", "lime"], y0=220), ui.text("12k", "ink", 90, y=-160, weight=800)],
         ry=[(b + 0.7, -50), (b + 1.8, -14, "m3Dec"), (b + 5.8, 12, "inOutSine")], rx=-4)
ui.window(S, "m_win", b + 1.1, 1180, 650, 760, 480, "white", "sand", items=ui.line([[-280, 120], [-140, 40], [-20, 80], [120, -70], [280, -120]], b + 2.0, 1.6, "coral", 14), ry=[(b + 1.1, -30), (b + 2.0, -8, "m3Dec"), (b + 5.8, 8, "inOutSine")])
three.box(S, "m_bx", b + 1.5, 1640, 380, 210, "coral", rx=-22, ry=(0, 200), t1=b + 5.8)
three.orb(S, "m_o", b + 2.0, 1700, 850, 170, "ink")
S.iris(17.0, "ink", 960, 540)

# Act 4 (17-22): sound
b = 17.0
S.headline("s_h", "Sound.", b + 0.3, 190, 200, "cream", dur=0.9)
vals = [.3, .6, .45, .8, .55, .95, .7, .4, .85, .6, .35, .75]
S.group("s_g", ui.bars(vals, b + 0.8, 1500, 340, ["lime", "coral", "butter", "mint"], y0=170, gap=0.3, stagger=0.1), x=960, y=560, w=1500, h=340)
for i, f in enumerate([392, 523, 587, 659, 784, 659]):
    S.sfx(b + 0.9 + i * 0.2, "pluck", 0.5, -11, S.pan_of(220 + i * 270), freq=f)
c = S.place("s_n", ui.counter("cream", 190, 960, 920, 0, 48, b + 1.6, 1.6, suf=" kHz")); S.appear(c, b + 1.6, sound=None)
S.count(c, b + 1.6, b + 3.2, 0, 48, ticks=8)
S.wipe(22.0, "coral", "x", 1)

# Act 5 (22-26): brand
b = 22.0
S.add("c_o", "sphere", "ink", w=560, x=960, y=470, scale=[(b + 0.1, 0), (b + 0.9, 1, "spring")])
for i, cc in enumerate(["butter", "lime", "cream"]):
    S.add(f"c_r{i}", "ring", cc, stroke=14, x=960, y=470, w=[(b + 0.4 + i * .3, 560), (b + 1.5 + i * .3, 2400, "m3Dec")], opacity=[(b + 0.39 + i * .3, 0), (b + 0.4 + i * .3, 1), (b + 1.5 + i * .3, 0)])
S.headline("c_n", "motionvid", b + 0.6, 470, 240, "cream", mode="split", dur=1.1)
S.headline("c_u", "github.com/NikitHamal/motionvid", b + 1.8, 800, 66, "ink", mode="type", cps=18)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(25, 0), (26, 1, "inQuad")])

S.save(Path(__file__).with_name("launch3.json"))
