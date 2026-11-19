"""Quill: AI writing SaaS, dark theme. Ribbon, typed editor window, site laptop, number, desk photo, helix and blob. 68 s, 16:9."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(68, "ink")
W, H = S.W, S.H

# Act 1 (0-10): ribbon
S.headline("a1", "Words", 0.4, 340, 300, "cream", x=520, dur=0.9)
S.headline("a2", "on demand.", 0.9, 620, 165, "lime", x=500, dur=1.0)
rib = [part("ribbon", ramp=["lime", "butter", "coral", "cream", "lime"], both=True, w=340, len=860, R=240, turns=1.6, speed=0.8, seg=110, gloss=0)]
mesh.mesh(S, "a_r", 0.9, 1530, 540, rib, 1300, rx=-18, ry=spin(0.9, 10, -30, 30), rz=-12, persp=2200, rim=0.4)
S.wipe(10.0, "lime", "x", 1)

# Act 2 (10-20): the editor types itself
b = 10.0
lines = ["Launch notes", "Quill drafts the first", "version in seconds.", "You keep the voice."]
items = [ui.typed(S, s, b + 1.4 + sum(len(x) for x in lines[:i]) / 22 + i * 0.3, 22, -600, -170 + i * 120, 72 if i == 0 else 56, "ink" if i else "moss", 800 if i == 0 else 600, pan=-0.2) for i, s in enumerate(lines)]
ui.window(S, "b_w", b + 0.5, 960, 620, 1500, 760, "cream", "sand", items)
S.headline("b1", "Drafts in seconds.", b + 0.3, 120, 140, "ink", dur=1.0)
S.iris(20.0, "cream", 960, 620)

# Act 3 (20-30): the site
b = 20.0
S.headline("c1", "Publish anywhere.", b + 0.3, 130, 160, "ink", dur=0.9)
mesh.mesh(S, "c_l", b + 0.3, 960, 650, mesh.laptop3d(screens.site_home(S, 846, 513, b + 0.4, "desk", "Write less", "lime", "ink", "cream", "Quill"), 1000, "ink", "cream"), 1300, rx=-12, ry=spin(b + 0.3, b + 9.4, -28, 16), persp=2000)
S.slats(30.0, "butter", 6)

# Act 4 (30-40): the number
b = 30.0
c = S.place("d_n", ui.counter("ink", 520, 640, 470, 1, 12, b + 0.6, 2.4, suf="x"))
S.appear(c, b + 0.5, sound=None)
S.count(c, b + 0.6, b + 3.0, 1, 12, ticks=10)
S.headline("d1", "faster.", b + 1.6, 800, 240, "ink", x=640, dur=0.9)
tower = mesh.bars3d([0.12, 0.18, 0.22, 0.3, 0.38, 0.5, 0.66, 0.8, 1.0], b + 0.8, 640, 620, ["ink", "cream"], depth=130)
mesh.mesh(S, "d_t", b + 0.6, 1520, 600, tower, 1100, rx=-14, ry=spin(b + 0.5, b + 9.4, -32, -2), persp=2200, rim=0.2)
S.wipe(40.0, "ink", "y", 1)

# Act 5 (40-50): a real desk
b = 40.0
f = media.photo("desk", W, H, 0, zoom=[(b + 0.1, 1.0), (b + 9.8, 1.2, "inOutSine")], tint="#17130F", tintA=0.4)
S.appear(S.add("e_i", "image", None, x=W / 2, y=H / 2, **{k: v for k, v in f.items() if k != "kind"}), b + 0.1, frm=1.0, sound=None)
S.headline("e1", "Made for", b + 0.6, 400, 250, "cream", x=640, dur=0.9)
S.headline("e2", "writers.", b + 1.1, 650, 250, "lime", x=640, dur=1.0)
S.iris(50.0, "coral", 960, 540)

# Act 6 (50-60): one voice
b = 50.0
S.headline("f1", "One voice.", b + 0.4, 130, 170, "ink", dur=1.0)
mind = [part("blob", "ink", r=200, amp=0.24, speed=1.6, gloss=16), part("helix", ramp=["cream", "lime", "butter"], R=330, r=26, h=760, turns=2.4, gloss=14, rz=[(b, 20)])]
mesh.mesh(S, "f_m", b + 0.5, 960, 650, mind, 1200, rx=-10, ry=spin(b + 0.4, b + 9.4, 0, 220), persp=2200, rim=0.35, hemi=0.4)
S.wipe(60.0, "ink", "x", -1)

# Act 7 (60-68): sign-off
b = 60.0
S.headline("g_n", "Quill", b + 0.6, 470, 360, "lime", mode="split", dur=1.1)
ui.button(S, "g_b", b + 2.0, 960, 780, 620, 140, "Start writing", "lime", "ink", press=b + 4.2)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(67, 0), (68, 1, "inQuad")])
S.save(Path(__file__).with_name("quill.json"))
