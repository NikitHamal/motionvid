"""Kernel: developer infrastructure, typed code in 3D laptop, server racks, real CPU footage, extruded hex logo. 58 s, 16:9, 60 fps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(58, "ink")
W, H = S.W, S.H
CODE = [[("import ", "kw"), ("{ agent }", "txt"), (" from ", "kw"), ("'kernel'", "str")], [("const ", "kw"), ("app", "txt"), (" = ", "mut"), ("agent", "fn"), ("(", "mut"), ("'ship it'", "str"), (")", "mut")],
        [("await ", "kw"), ("app.", "txt"), ("deploy", "fn"), ("({ ", "mut"), ("region", "txt"), (": ", "mut"), ("'edge'", "str"), (" })", "mut")], [("app.", "txt"), ("scale", "fn"), ("(", "mut"), ("0", "str"), (", ", "mut"), ("'auto'", "str"), (")", "mut")]]

# Act 1 (0-9)
S.headline("a1", "Ship", 0.4, 340, 300, "cream", x=560, dur=0.9)
S.headline("a2", "agents.", 0.9, 600, 220, "lime", x=560, dur=1.0)
ui.card(S, "a_c", 1.0, 1400, 540, 960, 620, "ink", 40, screens.code_editor(S, 960, 620, 1.3, CODE, 22, 44, 40), rx=-6, ry=[(1.0, -34), (9, -8, "inOutSine")])
S.cam(zoom=[(0, 1), (9, 1.05, "inOutSine")])
S.wipe(9.0, "lime", "x", 1)

# Act 2 (9-18)
b = 9.0
S.headline("b1", "Scale to zero.", b + 0.4, 130, 170, "ink", dur=1.0)
racks = []
for i, x in enumerate((-460, 0, 460)):
    for p in mesh.rack(260, 5, "ink", "coral"):
        p["pos"][0] += x
        p.setdefault("tracks", {})["s"] = [{"t": b + 0.6 + i * 0.25, "v": 0.1}, {"t": b + 1.5 + i * 0.25, "v": 1.0, "ease": "spring"}]
        racks.append(p)
mesh.mesh(S, "b_r", b + 0.4, 960, 640, racks, 1500, rx=-10, ry=spin(b + 0.4, b + 8.8, -24, 20), persp=2400)
c = S.place("b_n", ui.counter("ink", 130, 960, 960, 0, 99.99, b + 1.8, 2.2, suf="%", dec=2))
S.appear(c, b + 1.7, sound=None)
S.count(c, b + 1.8, b + 4.0, 0, 99.99, ticks=9)
S.iris(18.0, "ink", 960, 960)

# Act 3 (18-27)
b = 18.0
f = media.footage("cpu", 900, 560, t0=b + 0.5, r=80, loop="pp", zoom=[(b + 0.5, 1.0), (b + 8.5, 1.2, "inOutSine")], tint="#17130F", tintA=0.35)
S.appear(S.add("c_v", "video", None, x=560, y=560, **{k: v for k, v in f.items() if k != "kind"}), b + 0.5, frm=0.8)
S.headline("c1", "Every", b + 0.5, 330, 200, "cream", x=1450, dur=0.9)
S.headline("c2", "cycle", b + 0.9, 540, 200, "lime", x=1450, dur=0.9)
S.headline("c3", "counted.", b + 1.3, 750, 170, "cream", x=1450, dur=0.9)
S.wipe(27.0, "coral", "x", -1)

# Act 4 (27-37)
b = 27.0
S.headline("d1", "Deploy by prompt.", b + 0.4, 120, 150, "ink", dur=1.0)
mesh.mesh(S, "d_l", b + 0.5, 960, 660, mesh.laptop3d(screens.code_editor(S, 893, 542, b + 1.4, CODE, 20, 40, 8), 950, "sand", "ink"), 1300, rx=-12, ry=spin(b + 0.4, b + 9.4, -30, 12), persp=2000)
S.slats(37.0, "cream", 6)

# Act 5 (37-47)
b = 37.0
hexp = [[200 * __import__("math").cos(i * 1.0472 + 0.5236), 200 * __import__("math").sin(i * 1.0472 + 0.5236)] for i in range(6)]
hexi = [[120 * __import__("math").cos(i * 1.0472 + 0.5236), 120 * __import__("math").sin(i * 1.0472 + 0.5236)] for i in range(6)]
parts = [part("extrude", "ink", pts=hexp, d=90, gloss=16, s=[(b + 0.6, 0.1), (b + 1.8, 1, "spring")]), part("extrude", "lime", pts=hexi, d=110, gloss=16),
         part("torus", "coral", R=330, r=16, seg=64, rx=90, rz=[(b + 0.6, 0), (b + 9, 200, "inOutSine")]), part("torus", "butter", R=400, r=12, seg=64, rx=90, ry=[(b + 0.6, 0), (b + 9, -160, "inOutSine")])]
mesh.mesh(S, "e_h", b + 0.4, 960, 620, parts, 1100, rx=-14, ry=spin(b + 0.4, b + 9, -45, 60), persp=2000)
S.headline("e1", "One command.", b + 0.4, 130, 180, "ink", dur=1.0)
S.iris(47.0, "lime", 960, 620)

# Act 6 (47-58)
b = 47.0
S.headline("f_n", "Kernel", b + 0.6, 470, 330, "ink", mode="split", dur=1.1)
ui.button(S, "f_b", b + 2.0, 960, 780, 600, 140, "Start building", "ink", "lime", press=b + 4.0)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(57, 0), (58, 1, "inQuad")])
S.save(Path(__file__).with_name("kernel.json"))
