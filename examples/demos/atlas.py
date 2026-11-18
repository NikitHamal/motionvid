"""Atlas: travel app launch with real photos, 3D phone, laptop, photo cube and globe. 54 s, 16:9, 60 fps. Run: python examples/demos/atlas.py"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(54, "sand")
W, H = S.W, S.H
PH = (390, 820)

# Act 1 (0-9): hook + phone with the feed
S.headline("a1", "Go", 0.4, 330, 300, "ink", x=560, dur=0.9)
S.headline("a2", "somewhere", 0.8, 560, 185, "tomato", x=560, dur=1.0)
S.headline("a3", "real.", 1.2, 820, 300, "ink", x=560, dur=1.0)
mesh.mesh(S, "a_ph", 1.0, 1450, 560, mesh.phone3d(screens.travel_feed(S, *PH, 1.8, ["beach", "palms", "shore"])), 900, rx=-8, ry=spin(1.0, 9.0, -44, -8))
for i, (n, x, y, rot) in enumerate([("sunrise", 1090, 250, -7), ("palms", 1880, 800, 6)]):
    S.appear(S.add(f"a_c{i}", "image", None, src=f"media/assets/{n}.jpg", w=270, h=340, r=50, x=x, y=[(2 + i, y + 40), (9, y - 30, "inOutSine")], rotation=rot, zoom=1.0), 2.4 + i * 0.4, frm=0.5)
S.cam(zoom=[(0, 1), (9, 1.05, "inOutSine")])
S.wipe(9.0, "moss", "x", 1)

# Act 2 (9-18): a full photo and one number
b = 9.0
S.headline("b1", "Four hundred places.", b + 0.4, 150, 170, "cream", dur=1.0)
S.appear(S.add("b_img", "image", None, src="media/assets/rockies.jpg", w=1640, h=700, r=90, x=960, y=640, zoom=[(b + 0.3, 1.0), (b + 8.5, 1.22, "inOutSine")], px=[(b + 0.3, -0.5), (b + 8.5, 0.5, "inOutSine")]), b + 0.4, frm=0.9)
S.appear(S.add("b_pill", "rrect", "butter", w=560, h=170, r="pill", x=620, y=900), b + 1.4, frm=0.6)
c = S.place("b_num", ui.counter("ink", 120, 620, 900, 0, 400, b + 1.6, 2.2, pre="+"))
S.appear(c, b + 1.5, sound=None)
S.count(c, b + 1.6, b + 3.8, 0, 400, ticks=9)
S.cam(zoom=[(b, 1), (b + 9, 1.04, "inOutSine")])
S.iris(18.0, "tomato", 960, 640)

# Act 3 (18-27): laptop + phone
b = 18.0
mesh.mesh(S, "c_lp", b + 0.5, 780, 690, mesh.laptop3d(screens.site_home(S, 846, 513, b + 1.4, "lake", "Plan it", "tomato", "ink", "cream"), 900), 1100, rx=-12, ry=spin(b + 0.4, b + 9, -30, 10), persp=2000)
mesh.mesh(S, "c_ph", b + 0.9, 1580, 690, mesh.phone3d(screens.travel_feed(S, *PH, b + 1.8, ["lake", "rockies", "lake2"], "Trips", (90, 560))), 900, rx=-6, ry=spin(b + 0.8, b + 9, 30, 6))
S.headline("c1", "Any screen.", b + 0.4, 140, 210, "cream", dur=1.0)
S.slats(27.0, "butter", 6)

# Act 4 (27-36): the cube, every angle
b = 27.0
cube = mesh.cube_photos(520, {"front": "beach", "right": "palms", "left": "shore", "back": "lake", "top": "sunrise"}, "ink", 34)
orbit = mesh.orbit_parts(lambda i: part("sphere", ["coral", "moss", "tomato", "cream"][i], r=46, gloss=22), 4, 560, b + 0.8, b + 9, 1.0)
mesh.mesh(S, "d_cube", b + 0.5, 960, 600, cube + orbit, 1200, rx=-22, ry=spin(b + 0.4, b + 9, -30, 150, "inOutSine"), persp=2000)
S.headline("d1", "Every angle.", b + 0.4, 130, 190, "ink", dur=1.0)
S.wipe(36.0, "ink", "y", 1)

# Act 5 (36-45): globe
b = 36.0
c = S.place("e_num", ui.counter("butter", 330, 560, 430, 0, 190, b + 0.6, 2.2))
S.appear(c, b + 0.5, sound=None)
S.count(c, b + 0.6, b + 2.8, 0, 190, ticks=9)
S.headline("e_h", "countries.", b + 1.4, 700, 190, "cream", x=560, dur=0.9)
pins = []
for i, (la, lo, col) in enumerate([(20, 30, "coral"), (-10, 110, "butter"), (35, -60, "cream"), (-30, -20, "coral"), (5, 200, "butter"), (45, 120, "cream")]):
    r, a, o = 330 * 1.02, math.radians(la), math.radians(lo)
    pins.append(part("sphere", col, r=17, pos=[r * math.cos(a) * math.cos(o), -r * math.sin(a), r * math.cos(a) * math.sin(o)], gloss=20))
mesh.mesh(S, "e_g", b + 0.3, 1400, 560, mesh.globe(330, "moss", "butter") + pins, 800, rx=-18, ry=spin(b + 0.2, b + 9, 0, 200, "inOutSine"), persp=2200, rz=[(b, 12)])
S.iris(45.0, "cream", 1400, 560)

# Act 6 (45-54): brand
b = 45.0
mesh.mesh(S, "f_ph", b + 0.3, 460, 560, mesh.phone3d(screens.travel_feed(S, *PH, b + 1.0, ["sunrise", "beach", "palms"], "Atlas")), 900, rx=-6, ry=spin(b + 0.2, b + 8, -26, 10))
S.headline("f_n", "Atlas", b + 0.6, 460, 360, "ink", x=1240, mode="split", dur=1.1)
ui.button(S, "f_b", b + 2.0, 1240, 780, 520, 140, "Get the app", "tomato", "cream", press=b + 4.0)
for i, cc in enumerate(["butter", "sage", "tomato"]):
    S.add(f"f_r{i}", "ring", cc, stroke=14, x=1240, y=520, w=[(b + 0.4 + i * .3, 400), (b + 1.6 + i * .3, 2400, "m3Dec")], opacity=[(b + 0.39 + i * .3, 0), (b + 0.4 + i * .3, 1), (b + 1.6 + i * .3, 0)])
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(53, 0), (54, 1, "inQuad")])
S.save(Path(__file__).with_name("atlas.json"))
