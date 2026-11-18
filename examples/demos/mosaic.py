"""Mosaic: design suite, portrait 4:5 (1080x1350). Morphing blob, phones with real UI, photo grid, cube, laptop, wave. 66 s."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(66, "pink", width=1080, height=1350)
W, H = S.W, S.H

# Act 1 (0-10): blob
S.headline("a1", "Make", 0.4, 220, 270, "ink", dur=0.9)
S.headline("a2", "it yours.", 0.9, 430, 215, "cream", dur=1.0)
mesh.mesh(S, "a_b", 0.9, 540, 930, [part("blob", ramp=["coral", "butter", "lime", "coral"], cycle=2, r=300, amp=0.26, speed=1.3, gloss=16)], 1100, rx=-14, ry=spin(0.9, 10, 0, 90), persp=2200, rim=0.35, hemi=0.5)
S.wipe(10.0, "cream", "x", 1)

# Act 2 (10-20): two phones, real UI
b = 10.0
S.headline("b1", "Every screen.", b + 0.4, 160, 150, "ink", dur=1.0)
mesh.mesh(S, "b_p1", b + 0.7, 320, 800, mesh.phone3d(screens.product_page(S, 390, 820, b + 1.5, "fash3", "Add to bag", b + 4.0, "coral"), 450, 920), 1100, rx=-6, ry=spin(b + 0.6, b + 9.4, 30, 6), persp=2200)
mesh.mesh(S, "b_p2", b + 1.1, 780, 900, mesh.phone3d(screens.travel_feed(S, 390, 820, b + 1.9, ["lake", "palms", "shore"], "Trips", (90, 560)), 450, 920), 1100, rx=-6, ry=spin(b + 1.0, b + 9.4, -34, -8), persp=2200)
S.slats(20.0, "ink", 7)

# Act 3 (20-30): photo grid
b = 20.0
S.headline("c1", "Your brand.", b + 0.3, 130, 170, "cream", dur=1.0)
names = ["fash1", "studio1", "fash2", "sneaker", "studio2", "fash4"]
for i, n in enumerate(names):
    x, y = 200 + (i % 3) * 340, 480 + (i // 3) * 450
    S.appear(S.add(f"c_i{i}", "image", None, src=f"media/assets/{n}.jpg", w=310, h=420, r=60, x=x, y=[(b + 0.5, y + 30), (b + 9, y - 20, "inOutSine")], rotation=[-3, 2, -2, 3, -2, 2][i], zoom=[(b, 1.0), (b + 9, 1.15, "inOutSine")]), b + 0.7 + i * 0.22, frm=0.6)
S.headline("c2", "Every size.", b + 1.6, 1240, 150, "butter", dur=1.0)
S.iris(30.0, "butter", 540, 700)

# Act 4 (30-40): cube
b = 30.0
S.headline("d1", "Any angle.", b + 0.4, 170, 190, "ink", dur=1.0)
cube = mesh.cube_photos(480, {"front": "fash1", "right": "fash2", "left": "fash4", "back": "studio3", "top": "studio1"}, "ink", 34)
orb = mesh.orbit_parts(lambda i: part("torus", ["coral", "cream", "moss"][i], R=50, r=16, seg=40, rx=60), 3, 470, b + 0.8, b + 9.4, 1.0)
mesh.mesh(S, "d_c", b + 0.5, 540, 780, cube + orb, 1200, rx=-22, ry=spin(b + 0.4, b + 9.4, -30, 150), persp=2200)
S.wipe(40.0, "moss", "y", 1)

# Act 5 (40-50): laptop
b = 40.0
S.headline("e1", "Ship in a click.", b + 0.4, 170, 120, "cream", dur=1.0)
mesh.mesh(S, "e_l", b + 0.5, 540, 760, mesh.laptop3d(screens.dashboard(S, 893, 542, b + 1.4, "moss", "butter"), 1000), 1300, rx=-12, ry=spin(b + 0.4, b + 9.4, -26, 18), persp=2200)
mesh.mesh(S, "e_k", b + 1.2, 540, 1215, [part("knot", ramp=["butter", "coral", "cream", "butter"], cycle=2, R=90, r=24, p=2, q=3, gloss=16)], 500, rx=-20, ry=spin(b + 1.1, b + 9.4, 0, 200), persp=2000, rim=0.3)
S.iris(50.0, "coral", 540, 760)

# Act 6 (50-58): color moves
b = 50.0
S.headline("f1", "Colour", b + 0.4, 190, 230, "ink", dur=0.9)
S.headline("f2", "that moves.", b + 0.9, 380, 170, "cream", dur=1.0)
mesh.mesh(S, "f_w", b + 0.6, 540, 940, [part("wave", ramp=["ink", "tomato", "butter", "cream"], ao=0.5, w=880, d=700, amp=[(b + 0.6, 10), (b + 2.4, 120, "spring")], speed=1.2, seg=48)], 1500, rx=-26, ry=spin(b + 0.5, b + 7.8, -20, 20), persp=2300, hemi=0.6)
S.wipe(58.0, "ink", "y", -1)

# Act 7 (58-66): sign-off
b = 58.0
S.headline("g_n", "Mosaic", b + 0.5, 600, 250, "pink", mode="split", dur=1.1)
ui.button(S, "g_b", b + 1.8, 540, 780, 560, 130, "Start designing", "pink", "ink", press=b + 4.0)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(65, 0), (66, 1, "inQuad")])
S.save(Path(__file__).with_name("mosaic.json"))
