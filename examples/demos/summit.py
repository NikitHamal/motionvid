"""Summit: outdoor gear. Terrain flyover (wave), real photo and footage, bottle, activity phone, site laptop, photo cube. 70 s, 16:9."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(70, "sand")
W, H = S.W, S.H


def fullbleed(id, name, t, kind="image", tint="#17130F", a=0.3, z=1.16, dur=9.6):
    z_ = [(t, 1.0), (t + dur, z, "inOutSine")]
    if kind == "video":
        f = media.footage(name, W, H, t0=t, r=0, loop="pp", zoom=z_, tint=tint, tintA=a)
    else:
        f = media.photo(name, W, H, 0, zoom=z_, tint=tint, tintA=a)
    S.appear(S.add(id, kind, None, x=W / 2, y=H / 2, **{k: v for k, v in f.items() if k != "kind"}), t, frm=1.0, sound=None)


# Act 1 (0-10): terrain
S.headline("a1", "Higher", 0.4, 330, 250, "ink", x=520, dur=0.9)
S.headline("a2", "ground.", 0.9, 600, 250, "moss", x=520, dur=1.0)
land = [part("wave", ramp=["moss", "sage", "cream", "white"], ao=0.6, w=1250, d=900, amp=[(0.8, 20), (3, 230, "spring")], freq=1.3, speed=0.5, seg=56, y=0)]
mesh.mesh(S, "a_t", 0.8, 1430, 650, land, 1900, rx=[(0.8, -14), (10, -34, "inOutSine")], ry=spin(0.8, 10, -26, 20), persp=2300, hemi=0.6)
S.wipe(10.0, "ink", "x", 1)

# Act 2 (10-20): a real mountain
b = 10.0
fullbleed("b_i", "rockies", b + 0.1, a=0.28)
S.headline("b1", "Real peaks.", b + 0.6, 800, 250, "cream", x=700, dur=1.0)
S.slats(20.0, "cream", 6)

# Act 3 (20-30): the bottle
b = 20.0
bottle = [part("cyl", "moss", r=150, h=520, b=60, gloss=22), part("cyl", "tomato", r=118, h=110, b=30, pos=[0, -310, 0], gloss=20),
          part("torus", "ink", R=140, r=9, seg=64, pos=[0, 150, 0]), part("torus", "ink", R=140, r=9, seg=64, pos=[0, 40, 0])]
mesh.mesh(S, "c_b", b + 0.5, 1330, 560, bottle, 900, rx=[(b, -16), (b + 9, -8, "inOutSine")], ry=spin(b + 0.4, b + 9.4, -60, 140), persp=2000, rim=0.3)
S.headline("c1", "Built", b + 0.4, 330, 260, "cream", x=500, dur=0.9)
S.headline("c2", "to carry.", b + 0.9, 590, 210, "butter", x=500, dur=1.0)
c = S.place("c_n", ui.counter("cream", 140, 500, 860, 0, 840, b + 2.0, 2.2, suf=" g"))
S.appear(c, b + 1.9, sound=None)
S.count(c, b + 2.0, b + 4.2, 0, 840, ticks=9)
S.iris(30.0, "cream", 1330, 560)

# Act 4 (30-40): footage and activity
b = 30.0
f = media.footage("jog", 840, 680, t0=b + 0.4, r=90, loop="pp", zoom=[(b + 0.4, 1.0), (b + 9, 1.2, "inOutSine")])
S.appear(S.add("d_v", "video", None, x=520, y=660, **{k: v for k, v in f.items() if k != "kind"}), b + 0.4, frm=0.7)
mesh.mesh(S, "d_p", b + 0.9, 1480, 620, mesh.phone3d(screens.activity(S, 390, 820, b + 1.6, "lime", "ink")), 900, rx=-8, ry=spin(b + 0.8, b + 9.4, 38, 6), persp=2000)
S.headline("d1", "Every step counted.", b + 0.4, 130, 150, "ink", dur=1.0)
S.wipe(40.0, "moss", "y", -1)

# Act 5 (40-50): the shop
b = 40.0
S.headline("e1", "Order from base camp.", b + 0.4, 130, 150, "cream", dur=1.0)
mesh.mesh(S, "e_l", b + 0.5, 960, 650, mesh.laptop3d(screens.site_home(S, 846, 513, b + 1.4, "lake", "Pack light", "tomato", "ink", "cream", "Summit"), 1000), 1300, rx=-12, ry=spin(b + 0.4, b + 9.4, 26, -14), persp=2000)
S.iris(50.0, "butter", 960, 650)

# Act 6 (50-60): pick a line
b = 50.0
cube = mesh.cube_photos(500, {"front": "rockies", "right": "lake", "left": "lake2", "back": "sunrise", "top": "park"}, "ink", 34)
orb = mesh.orbit_parts(lambda i: part("gem", ["tomato", "moss", "ink", "cream"][i], r=48, h=90, gloss=20), 4, 470, b + 0.8, b + 9.4, 1.0)
mesh.mesh(S, "f_c", b + 0.5, 1380, 600, cube + orb, 1200, rx=-20, ry=spin(b + 0.4, b + 9.4, -30, 150), persp=2000)
S.headline("f1", "Pick", b + 0.4, 350, 250, "ink", x=470, dur=0.9)
S.headline("f2", "a line.", b + 0.9, 620, 220, "tomato", x=470, dur=1.0)
S.slats(60.0, "ink", 6)

# Act 7 (60-70): sign-off
b = 60.0
S.headline("g_n", "Summit", b + 0.6, 470, 330, "butter", mode="split", dur=1.1)
ui.button(S, "g_b", b + 2.0, 960, 780, 600, 140, "Gear up", "butter", "ink", press=b + 4.2)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(69, 0), (70, 1, "inQuad")])
S.save(Path(__file__).with_name("summit.json"))
