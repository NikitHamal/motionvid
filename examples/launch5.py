"""v0.10 Prism Launch: the motionvid launch for social. 44 s, 16:9, 60 fps. Mesh v3 heroes (knot, wave, blob, helix), the Studio page as real UI, real footage."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from motionvid.kit import Scene, item, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(44, "ink")
W, H = S.W, S.H

# 1 (0-7): one prompt, whole film
S.headline("a1", "One prompt.", 0.4, 330, 190, "cream", x=640, dur=0.9)
S.headline("a2", "Whole film.", 0.9, 560, 190, "lime", x=640, dur=1.0)
mesh.mesh(S, "a_k", 0.9, 1610, 540, [part("knot", ramp=["lime", "butter", "coral", "cream", "lime"], cycle=3, R=200, r=54, p=2, q=3, gloss=18)], 1100, rx=-20, ry=spin(0.9, 7, 0, 140), rz=[(0.9, -8), (7, 12, "inOutSine")], persp=2000, rim=0.35)
S.cam(zoom=[(0, 1), (7, 1.05, "inOutSine")])
S.wipe(7.0, "lime", "x", 1)

# 2 (7-15): the Studio, as real UI
b = 7.0
chips = [ui.pill(120, 64, "ink", x=-300 + i * 150, y=40) for i in range(3)]
labels = [item("text", "cream", text=t, size=30, weight=700, x=-300 + i * 150, y=40) for i, t in enumerate(("16:9", "9:16", "4:5"))]
thumbs = [media.photo(n, 250, 140, 24, x=300 + (i % 2) * 280, y=-170 + (i // 2) * 170, zoom=[(b + 3, 1.0), (b + 8, 1.15, "inOutSine")], opacity=[(b + 3.4 + i * 0.25, 0), (b + 3.7 + i * 0.25, 1)]) for i, n in enumerate(("lake", "fash1", "rockies", "desk"))]
items = [ui.typed(S, "a fitness app with real runs", b + 1.4, 16, -620, -160, 46, "ink", 800), *chips, *labels, *thumbs, ui.pill(240, 84, "coral", x=-500, y=190), item("text", "ink", text="Generate", size=34, weight=800, x=-500, y=190)]
ui.window(S, "b_w", b + 0.5, 960, 640, 1500, 700, "cream", "sand", items)
S.headline("b1", "Describe it.", b + 0.3, 130, 160, "ink", dur=1.0)
S.iris(15.0, "cream", 960, 640)

# 3 (15-23): smooth 3D
b = 15.0
S.headline("c1", "Smooth 3D.", b + 0.3, 130, 170, "ink", dur=1.0)
mesh.mesh(S, "c_w", b + 0.4, 960, 700, [part("wave", ramp=["ink", "moss", "butter", "coral"], ao=0.5, w=1500, d=850, amp=[(b + 0.5, 10), (b + 2.2, 110, "spring")], speed=1.1, seg=52)], 1900, rx=-26, ry=spin(b + 0.4, b + 7.8, -20, 16), persp=2300, hemi=0.7)
mesh.mesh(S, "c_b", b + 1.0, 1560, 360, [part("blob", ramp=["coral", "pink", "butter"], r=150, amp=0.28, speed=1.5, gloss=18)], 500, rx=-10, ry=spin(b + 1, b + 7.8, 0, 120), rim=0.3, hemi=0.5)
mesh.mesh(S, "c_h", b + 1.3, 360, 380, [part("helix", ramp=["moss", "lime", "butter"], R=110, r=20, h=320, turns=3, gloss=14)], 500, rx=-8, ry=spin(b + 1.2, b + 7.8, 0, 240), rim=0.3)
S.wipe(23.0, "coral", "x", -1)

# 4 (23-31): real footage, real UI
b = 23.0
f = media.footage("jog", 780, 700, t0=b + 0.4, r=90, loop="pp", zoom=[(b + 0.4, 1.0), (b + 7.5, 1.2, "inOutSine")])
S.appear(S.add("d_v", "video", None, x=500, y=620, **{k: v for k, v in f.items() if k != "kind"}), b + 0.4, frm=0.7)
mesh.mesh(S, "d_p", b + 0.9, 1400, 620, mesh.phone3d(screens.activity(S, 390, 820, b + 1.6, "lime", "ink")), 900, rx=-8, ry=spin(b + 0.8, b + 7.6, 38, 6), persp=2000)
S.headline("d1", "Real footage. Real UI.", b + 0.3, 130, 140, "ink", dur=1.0)
S.slats(31.0, "butter", 6)

# 5 (31-38): proof
b = 31.0
for i, (v, suf, x, lab) in enumerate(((11, "", 480, "demos"), (70, " s", 960, "longest"), (0, " B", 1440, "samples"))):
    ui.card(S, f"e_k{i}", b + 0.4 + i * 0.25, x, 600, 400, 520, "ink", 80)
    c = S.place(f"e_n{i}", ui.counter("butter", 150, x, 560, 0, v, b + 1.0 + i * 0.25, 1.6, suf=suf))
    S.appear(c, b + 0.9 + i * 0.25, sound=None)
    S.count(c, b + 1.0 + i * 0.25, b + 2.6 + i * 0.25, 0, v, ticks=5)
    S.add(f"e_l{i}", "text", "cream", text=lab, size=64, weight=700, x=x, y=730, opacity=[(b + 1.4 + i * 0.25, 0), (b + 1.6 + i * 0.25, 1)])
S.headline("e1", "Proven.", b + 0.2, 150, 190, "ink", dur=0.9)
S.iris(38.0, "ink", 960, 600)

# 6 (38-44): brand
b = 38.0
S.headline("f_n", "motionvid", b + 0.4, 460, 250, "cream", mode="split", dur=1.1)
ui.button(S, "f_b", b + 1.8, 960, 720, 560, 140, "Make yours", "lime", "ink", press=b + 3.4)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(43, 0), (44, 1, "inQuad")])
S.save(Path(__file__).with_name("launch5.json"))
