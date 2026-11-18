"""Helio: solar energy, morphing sun, wave field, dashboard laptop, city footage, bar tower, globe. 64 s, 16:9, 60 fps."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(64, "butter")
W, H = S.W, S.H
RAMP = ["ink", "moss", "butter", "coral"]

# Act 1 (0-9): the sun
S.headline("a1", "Sun", 0.4, 340, 330, "ink", x=560, dur=0.9)
S.headline("a2", "to socket.", 0.9, 640, 190, "tomato", x=560, dur=1.0)
sun = [part("blob", "coral", r=230, amp=0.2, speed=1.3, gloss=18), part("torus", "ink", R=330, r=8, seg=96, rx=82, rz=[(1.4, 0), (9, 90, "inOutSine")]),
       part("torus", "moss", R=390, r=6, seg=96, rx=70, ry=[(1.4, 0), (9, -70, "inOutSine")])]
mesh.mesh(S, "a_sun", 0.9, 1560, 540, sun, 1100, rx=-14, ry=spin(0.9, 9, -10, 40), persp=2200, rim=0.3, hemi=0.5)
S.cam(zoom=[(0, 1), (9, 1.05, "inOutSine")])
S.wipe(9.0, "moss", "x", 1)

# Act 2 (9-18): the field
b = 9.0
S.headline("b1", "Every roof counts.", b + 0.4, 150, 170, "cream", dur=1.0)
field = [part("wave", ramp=RAMP, ao=0.5, w=1700, d=950, amp=[(b + 0.5, 10), (b + 2.5, 120, "spring")], speed=1.1, seg=52, y=0)]
mesh.mesh(S, "b_w", b + 0.4, 960, 600, field, 2000, rx=-27, ry=spin(b + 0.4, b + 9, -22, 14), persp=2300, hemi=0.7)
c = S.place("b_n", ui.counter("butter", 150, 1560, 960, 0, 4.2, b + 1.8, 2.4, suf=" GW", dec=1))
S.appear(c, b + 1.7, sound=None)
S.count(c, b + 1.8, b + 4.2, 0, 4.2, ticks=9)
S.iris(18.0, "cream", 960, 700)

# Act 3 (18-27): the dashboard
b = 18.0
S.headline("c1", "Know every watt.", b + 0.4, 130, 180, "ink", dur=1.0)
mesh.mesh(S, "c_l", b + 0.5, 960, 650, mesh.laptop3d(screens.dashboard(S, 893, 542, b + 1.4, "moss", "butter"), 1000), 1300, rx=-12, ry=spin(b + 0.4, b + 9, -28, 14), persp=2000)
S.wipe(27.0, "ink", "y", 1)

# Act 4 (27-36): real city, lit by it
b = 27.0
f = media.footage("citynight", W, H, t0=b + 0.2, r=0, loop="pp", zoom=[(b + 0.2, 1.0), (b + 8.8, 1.18, "inOutSine")], tint="#17130F", tintA=0.38)
S.appear(S.add("d_v", "video", None, x=W / 2, y=H / 2, **{k: v for k, v in f.items() if k != "kind"}), b + 0.2, frm=1.0, sound=None)
S.headline("d1", "Cities", b + 0.6, 440, 300, "cream", x=700, dur=0.9)
S.headline("d2", "run on it.", b + 1.1, 720, 230, "butter", x=700, dur=1.0)
S.slats(36.0, "moss", 6)

# Act 5 (36-45): growth tower
b = 36.0
S.headline("e1", "+38%", b + 0.5, 420, 400, "butter", x=620, dur=1.0)
S.headline("e2", "output.", b + 1.0, 720, 220, "cream", x=620, dur=1.0)
tower = mesh.bars3d([0.2, 0.32, 0.28, 0.45, 0.55, 0.5, 0.72, 0.85, 1.0], b + 0.8, 760, 640, ["butter", "cream"], depth=140)
mesh.mesh(S, "e_t", b + 0.6, 1450, 640, tower, 1200, rx=-14, ry=spin(b + 0.5, b + 9, -34, -4), persp=2200, rim=0.25)
S.iris(45.0, "butter", 960, 540)

# Act 6 (45-54): the globe
b = 45.0
pins = []
for la, lo, col in [(20, 30, "coral"), (-10, 110, "ink"), (35, -60, "coral"), (-30, -20, "ink"), (5, 200, "coral"), (45, 120, "ink")]:
    r, a, o = 330 * 1.02, math.radians(la), math.radians(lo)
    pins.append(part("sphere", col, r=17, pos=[r * math.cos(a) * math.cos(o), -r * math.sin(a), r * math.cos(a) * math.sin(o)], gloss=20))
mesh.mesh(S, "f_g", b + 0.3, 520, 540, mesh.globe(330, "moss", "ink") + pins, 800, rx=-16, ry=spin(b + 0.2, b + 9, 0, 210), persp=2200, rz=[(b, 12)])
S.headline("f1", "One grid.", b + 0.5, 360, 190, "ink", x=1380, dur=0.9)
S.headline("f2", "Every sky.", b + 1.0, 580, 190, "tomato", x=1380, dur=1.0)
S.wipe(54.0, "ink", "x", -1)

# Act 7 (54-64): sign-off
b = 54.0
S.headline("g_n", "Helio", b + 0.6, 470, 360, "butter", mode="split", dur=1.1)
ui.button(S, "g_b", b + 2.0, 960, 780, 620, 140, "Get the sun", "butter", "ink", press=b + 4.2)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(63, 0), (64, 1, "inQuad")])
S.save(Path(__file__).with_name("helio.json"))
