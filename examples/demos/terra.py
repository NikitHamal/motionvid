"""Terra: urban climate, real city footage, bar descent, extruded 3D leaf, globe and dashboard laptop. 54 s, 16:9, 60 fps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(54, "cream")
W, H = S.W, S.H


def vid(id, t, x, y, w, h, r, **kw):
    f = media.footage("citynight", w, h, t0=t, r=r, loop="pp", **kw)
    el = S.add(id, "video", None, x=x, y=y, **{k: v for k, v in f.items() if k != "kind"})
    return S.appear(el, t, frm=0.8)


# Act 1 (0-9)
S.headline("a1", "Cities that", 0.4, 360, 150, "ink", x=580, dur=0.9)
S.headline("a2", "breathe.", 0.9, 600, 210, "moss", x=580, dur=1.0)
vid("a_v", 1.0, 1450, 540, 780, 640, 90, zoom=[(1.0, 1.0), (9, 1.25, "inOutSine")])
S.add("a_leaf", "blob", "lime", w=210, x=880, y=170, n=5, amp=0.12, rotation=[(1.5, 0), (9, 90, "inOutSine")], opacity=[(1.4, 0), (1.5, 1)])
S.cam(zoom=[(0, 1), (9, 1.05, "inOutSine")])
S.wipe(9.0, "moss", "x", 1)

# Act 2 (9-18)
b = 9.0
S.headline("b1", "Less carbon.", b + 0.4, 130, 150, "cream", dur=1.0)
vid("b_v", b + 0.5, 960, 600, 1700, 760, 90, ss=1.0, zoom=[(b + 0.5, 1.0), (b + 8.5, 1.18, "inOutSine")], tint="#2F5D3A", tintA=0.3)
S.appear(S.add("b_p", "rrect", "butter", w=640, h=200, r="pill", x=520, y=880), b + 1.6, frm=0.6)
c = S.place("b_n", ui.counter("ink", 150, 520, 880, 0, 42, b + 1.8, 2.2, pre="-", suf="%"))
S.appear(c, b + 1.7, sound=None)
S.count(c, b + 1.8, b + 4.0, 0, 42, ticks=9)
S.iris(18.0, "butter", 520, 880)

# Act 3 (18-27)
b = 18.0
S.headline("c1", "Down,", b + 0.4, 340, 250, "ink", x=560, dur=0.9)
S.headline("c2", "every year.", b + 0.9, 580, 150, "moss", x=560, dur=0.9)
mesh.mesh(S, "c_b", b + 0.4, 1400, 640, mesh.bars3d([1.0, 0.86, 0.72, 0.58, 0.44, 0.3], b + 0.9, 800, 600, ["moss", "ink"], 140, 0.16, 0.5, 22), 1200, rx=-14, ry=spin(b + 0.4, b + 9, -28, 14), persp=2200)
S.slats(27.0, "sage", 6)

# Act 4 (27-36): extruded leaf
b = 27.0
leaf = [[0, -230], [70, -170], [120, -80], [135, 20], [100, 120], [0, 230], [-100, 120], [-135, 20], [-120, -80], [-70, -170]]
parts = [part("extrude", "moss", pts=leaf, d=70, gloss=14, s=[(b + 0.6, 0.1), (b + 1.8, 1, "spring")]),
         part("extrude", "lime", pts=[[0, -160], [20, -100], [20, 160], [-20, 100], [-20, -100]], d=84, pos=[0, 20, 0], gloss=14),
         part("torus", "butter", R=360, r=14, seg=64, rx=[(b + 0.6, 90)], rz=[(b + 0.6, 0), (b + 8.5, 160, "inOutSine")])]
parts += mesh.orbit_parts(lambda i: part("sphere", ["butter", "cream", "moss"][i], r=34, gloss=22), 3, 360, b + 0.8, b + 8.8, 1.0)
mesh.mesh(S, "d_l", b + 0.4, 960, 620, parts, 1200, rx=-14, ry=spin(b + 0.4, b + 8.8, -50, 70), persp=2000)
S.headline("d1", "Grow green.", b + 0.4, 120, 190, "moss", dur=1.0)
S.wipe(36.0, "moss", "y", -1)

# Act 5 (36-45)
b = 36.0
S.headline("e1", "Track every ton.", b + 0.4, 120, 150, "cream", dur=1.0)
mesh.mesh(S, "e_l", b + 0.5, 960, 660, mesh.laptop3d(screens.dashboard(S, 893, 542, b + 1.4, "moss", "butter"), 950, "sand", "white"), 1300, rx=-12, ry=spin(b + 0.4, b + 8.8, -28, 14), persp=2000)
S.iris(45.0, "cream", 960, 660)

# Act 6 (45-54)
b = 45.0
mesh.mesh(S, "f_g", b + 0.3, 420, 540, mesh.globe(230, "moss", "lime"), 600, rx=-18, ry=spin(b + 0.2, b + 8, 0, 240), persp=2000)
S.headline("f_n", "Terra", b + 0.6, 500, 330, "moss", x=1180, mode="split", dur=1.1)
ui.button(S, "f_b", b + 2.0, 1180, 780, 560, 140, "See your city", "lime", "ink", press=b + 4.0)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(53, 0), (54, 1, "inQuad")])
S.save(Path(__file__).with_name("terra.json"))
