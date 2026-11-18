"""Ledgerly: finance SaaS, 3D laptop dashboard, bar towers, coin stack, banking app with real avatars. 56 s, 16:9, 60 fps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, mesh, screens  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(56, "cream")
W, H = S.W, S.H

# Act 1 (0-9)
S.headline("a1", "Money,", 0.4, 360, 300, "ink", x=620, dur=0.9)
S.headline("a2", "in motion.", 0.9, 640, 190, "moss", x=620, dur=1.0)
mesh.mesh(S, "a_l", 0.8, 1450, 600, mesh.laptop3d(screens.dashboard(S, 773, 469, 1.8, "moss", "butter"), 820), 1100, rx=-12, ry=spin(0.6, 9, -32, 8), persp=2000)
S.cam(zoom=[(0, 1), (9, 1.05, "inOutSine")])
S.wipe(9.0, "moss", "x", 1)

# Act 2 (9-18): growth tower
b = 9.0
c = S.place("b_n", ui.counter("butter", 330, 520, 440, 0, 38, b + 0.6, 2.2, pre="+", suf="%"))
S.appear(c, b + 0.5, sound=None)
S.count(c, b + 0.6, b + 2.8, 0, 38, ticks=9)
S.headline("b_h", "growth.", b + 1.2, 720, 200, "cream", x=520, dur=0.9)
mesh.mesh(S, "b_t", b + 0.4, 1320, 650, mesh.bars3d([0.25, 0.38, 0.34, 0.52, 0.6, 0.78, 0.88, 1.0], b + 0.9, 1000, 640, ["cream", "butter"], 140, 0.14, 0.45, 22), 1300,
          rx=-14, ry=spin(b + 0.4, b + 9, -26, 20), persp=2200)
S.iris(18.0, "butter", 1320, 650)

# Act 3 (18-27): coin stack
b = 18.0
S.headline("c1", "Every cent", b + 0.4, 330, 200, "ink", x=640, dur=0.9)
S.headline("c2", "counted.", b + 0.9, 560, 200, "moss", x=640, dur=0.9)
c = S.place("c_n", ui.counter("ink", 240, 640, 840, 0, 2.4, b + 1.6, 2.0, pre="$", suf="M", dec=1))
S.appear(c, b + 1.5, sound=None)
S.count(c, b + 1.6, b + 3.6, 0, 2.4, ticks=7)
cols = ["clay", "cream", "moss", "clay", "cream"]
coins = []
for i, col in enumerate(cols):
    ty = 190 - i * 58
    coins.append(part("cyl", col, r=210, h=52, b=20, gloss=24, y=[(b + 0.8 + i * 0.3, -1000), (b + 1.5 + i * 0.3, ty, "spring")]))
    S.sfx(b + 1.2 + i * 0.3, "pop", 0.2, -11, 0.4)
mesh.mesh(S, "c_s", b + 0.4, 1420, 620, coins, 1000, rx=-22, ry=spin(b + 0.4, b + 9, -20, 160), persp=2000)
S.slats(27.0, "cream", 6)

# Act 4 (27-37): the app
b = 27.0
S.headline("d1", "Pay in", b + 0.4, 330, 200, "ink", x=560, dur=0.9)
S.headline("d2", "one tap.", b + 0.9, 570, 200, "coral", x=560, dur=0.9)
mesh.mesh(S, "d_p", b + 0.5, 1400, 560, mesh.phone3d(screens.wallet(S, 390, 820, b + 1.4, ["fash1", "fash2", "fash3", "fash4"]), 420, 860), 900, rx=-6, ry=spin(b + 0.4, b + 9.5, -36, 8))
ui.notification(S, "d_n", b + 4.6, 560, 880, 640, 140, "Paid", "ink", "lime", "cream")
S.wipe(37.0, "ink", "y", 1)

# Act 5 (37-47): reports window
b = 37.0
S.headline("e1", "Reports in a click.", b + 0.4, 120, 130, "cream", dur=1.0)
ui.window(S, "e_w", b + 0.5, 960, 620, 1500, 800, "white", "sand", screens.shift(screens.dashboard(S, 1500, 712, b + 1.3, "moss", "butter"), 44), rx=-8, ry=[(b + 0.5, -26), (b + 9, 10, "inOutSine")])
ui.cursor(S, "e_c", [(b + 3.0, 1550, 980), (b + 4.4, 1180, 300, "m3Dec"), (b + 6.0, 700, 800, "m3Dec")], [b + 4.4])
S.iris(47.0, "moss", 960, 620)

# Act 6 (47-56): brand
b = 47.0
mesh.mesh(S, "f_c", b + 0.3, 330, 540, mesh.coin(150, "butter", "clay", 44), 600, rx=-10, ry=spin(b + 0.2, b + 6, 0, 360, "inOutSine"), persp=2000)
S.headline("f_n", "Ledgerly", b + 0.6, 500, 250, "butter", x=1200, mode="split", dur=1.1)
ui.button(S, "f_b", b + 2.0, 1200, 780, 560, 140, "Start free", "butter", "ink", press=b + 4.0)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(55, 0), (56, 1, "inQuad")])
S.save(Path(__file__).with_name("ledgerly.json"))
