"""Pulse: fitness wearable, vertical 9:16, real running footage, 3D activity rings and bars. 50 s, 60 fps. Run: python examples/demos/pulse.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(50, "ink", width=1080, height=1920)
W, H = S.W, S.H
CX = W / 2

# Act 1 (0-8): footage hook
S.headline("a1", "Move", 0.4, 260, 330, "lime", dur=0.9)
S.headline("a2", "more.", 0.9, 560, 330, "cream", dur=1.0)
v = S.add("a_v", "video", None, **{k: v for k, v in media.footage("jog", 900, 700, t0=1.0, r=90, loop="pp", zoom=[(1.0, 1.0), (8, 1.2, "inOutSine")]).items() if k not in ("kind",)})
v["tracks"]["y"] = [{"t": 0, "v": 1240}]
S.appear(v, 1.0, frm=0.7)
S.appear(S.add("a_p", "rrect", "lime", w=420, h=130, r="pill", x=300, y=1520), 2.4, frm=0.5)
c = S.place("a_n", ui.counter("ink", 84, 300, 1520, 0, 62, 2.6, 1.8, suf=" min"))
S.appear(c, 2.5, sound=None)
S.count(c, 2.6, 4.4, 0, 62, ticks=7)
S.wipe(8.0, "lime", "y", 1)

# Act 2 (8-17): the phone
b = 8.0
S.headline("b1", "Close", b + 0.4, 190, 230, "ink", dur=0.9)
S.headline("b2", "the rings.", b + 0.8, 400, 160, "ink", dur=0.9)
mesh.mesh(S, "b_ph", b + 0.6, CX, 1180, mesh.phone3d(screens.activity(S, 560, 1180, b + 1.4, "lime", "ink"), 620, 1260, "ink", "cream", 52), 1400, rx=-6, ry=spin(b + 0.5, b + 9, -34, 12), persp=2300)
S.iris(17.0, "coral", CX, 1180)

# Act 3 (17-26): 3D rings
b = 17.0
parts = [part("torus", c_, R=R_, r=46, seg=64, gloss=18, rx=[(b + 0.6 + i * 0.3, 90), (b + 8.5, 90 + 40 * (i + 1), "inOutSine")], rz=[(b + 0.6, 0), (b + 8.5, 120 - 40 * i, "inOutSine")], s=[(b + 0.6 + i * 0.3, 0.1), (b + 1.6 + i * 0.3, 1, "spring")])
         for i, (c_, R_) in enumerate((("lime", 390), ("ink", 290), ("cream", 190)))]
parts.append(part("sphere", "butter", r=92, gloss=26, s=[(b + 1.4, 0.1), (b + 2.4, 1, "spring")]))
mesh.mesh(S, "c_r", b + 0.4, CX, 1010, parts, 1100, rx=-20, ry=spin(b + 0.4, b + 9, -30, 30), persp=2200)
S.headline("c1", "Three", b + 0.4, 170, 230, "cream", dur=1.0)
S.headline("c2", "rings.", b + 0.8, 380, 230, "ink", dur=1.0)
c = S.place("c_n", ui.counter("ink", 230, CX, 1650, 0, 12480, b + 1.6, 2.4))
S.appear(c, b + 1.5, sound=None)
S.count(c, b + 1.6, b + 4.0, 0, 12480, ticks=9)
S.slats(26.0, "cream", 8)

# Act 4 (26-35): week bars
b = 26.0
bars = mesh.bars3d([0.4, 0.62, 0.5, 0.85, 0.7, 1.0, 0.58], b + 0.8, 900, 760, ["ink", "coral", "ink", "coral", "ink", "lime", "ink"], 120, 0.14, 0.5, 22)
mesh.mesh(S, "d_b", b + 0.5, CX, 1150, bars, 1200, rx=-16, ry=spin(b + 0.4, b + 8.8, -28, 24), persp=2200)
S.headline("d1", "Every day", b + 0.4, 220, 180, "ink", dur=0.9)
S.headline("d2", "counts.", b + 0.9, 420, 220, "coral", dur=0.9)
S.wipe(35.0, "ink", "x", -1)

# Act 5 (35-44): footage full bleed
b = 35.0
fv = media.footage("jog", 960, 1500, t0=b, ss=2.0, r=100, loop="pp", zoom=[(b, 1.0), (b + 8.5, 1.25, "inOutSine")], tint="#17130F", tintA=0.28)
S.appear(S.add("e_v", "video", None, **{k: v for k, v in fv.items() if k != "kind"}), b + 0.3, frm=0.88)
S.headline("e1", "Run", b + 0.8, 1150, 330, "cream", dur=0.9)
S.headline("e2", "your way.", b + 1.3, 1420, 190, "lime", dur=0.9)
ui.notification(S, "e_n", b + 3.5, CX, 300, 700, 150, "New best", "lime", "coral")
S.iris(44.0, "lime", CX, 1000)

# Act 6 (44-50): brand
b = 44.0
mesh.mesh(S, "f_c", b + 0.3, CX, 760, mesh.coin(260, "butter", "clay", 60) + [part("extrude", "ink", pts=[[40, -150], [-90, 20], [-5, 20], [-40, 150], [90, -20], [5, -20]], d=18, pos=[0, 0, 40], rx=0)], 800, rx=-10, ry=spin(b + 0.2, b + 5.5, 0, 360, "inOutSine"), persp=2200)
S.headline("f_n", "Pulse", b + 0.6, 1230, 380, "ink", mode="split", dur=1.1)
ui.button(S, "f_b", b + 1.8, CX, 1520, 520, 140, "Join free", "ink", "lime", press=b + 3.6)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(49, 0), (50, 1, "inQuad")])
S.save(Path(__file__).with_name("pulse.json"))
