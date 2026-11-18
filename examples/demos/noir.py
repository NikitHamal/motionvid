"""Noir: fashion drop, square 1:1, real portrait photos, photo carousel in 3D, product page. 45 s, 60 fps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, item, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(45, "ink", width=1080, height=1080)
W, H = S.W, S.H
PICS = ["fash1", "fash2", "fash3", "fash4", "studio1", "studio3"]

# Act 1 (0-8)
S.headline("a1", "Drop 04.", 0.4, 170, 220, "cream", dur=1.0)
img = S.add("a_i", "image", None, src="media/assets/fash4.jpg", w=800, h=680, r=80, x=540, y=660, rotation=[(0.8, -6), (8, 3, "inOutSine")], zoom=[(0.8, 1.0), (8, 1.25, "inOutSine")], py=[(0.8, -0.6), (8, 0.4, "inOutSine")])
S.appear(img, 0.8, frm=0.7)
S.appear(S.add("a_p", "rrect", "pink", w=300, h=110, r="pill", x=820, y=300), 2.0, frm=0.5)
S.add("a_t", "text", "ink", text="04", size=70, weight=800, x=820, y=300, opacity=[(1.9, 0), (2.0, 1)])
S.iris(8.0, "pink", 540, 660)

# Act 2 (8-17): carousel
b = 8.0
S.headline("b1", "Six looks.", b + 0.4, 150, 170, "ink", dur=1.0)
cards = mesh.orbit_parts(lambda i: part("rbox", "ink", w=300, h=420, d=14, r=26, seg=3,
                                       screen=[{"face": f, "items": [media.photo(PICS[i], 276, 396, 18)], "w": 276, "h": 396, "r": 18, "bg": "#E9DCC3"} for f in ("front", "back")]), 6, 560, b + 0.6, b + 8.8, 0.5, face_out=True)
mesh.mesh(S, "b_c", b + 0.4, 540, 620, cards, 1500, rx=-16, ry=[(b + 0.4, 0)], persp=2000)
S.iris(17.0, "butter", 540, 640)

# Act 3 (17-26): product
b = 17.0
S.headline("c1", "Own it.", b + 0.4, 140, 210, "ink", dur=0.9)
mesh.mesh(S, "c_p", b + 0.5, 540, 700, mesh.phone3d(screens.product_page(S, 316, 668, b + 1.4, "sneaker", "Add to bag", b + 5.0, "coral"), 340, 700, "ink", "cream", 40), 800, rx=-6, ry=spin(b + 0.4, b + 9, -34, 12))
for i, (n, x, y, rot) in enumerate([("studio2", 150, 780, -8), ("studio1", 930, 470, 7)]):
    S.appear(S.add(f"c_c{i}", "image", None, src=f"media/assets/{n}.jpg", w=250, h=320, r=50, x=x, y=[(b + 1, y + 30), (b + 9, y - 30, "inOutSine")], rotation=rot, zoom=1.0), b + 1.8 + i * 0.4, frm=0.5)
S.slats(26.0, "pink", 6)

# Act 4 (26-35): cube
b = 26.0
S.headline("d1", "Wear the", b + 0.4, 130, 160, "ink", dur=0.9)
S.headline("d2", "moment.", b + 0.9, 290, 160, "cream", dur=0.9)
cube = mesh.cube_photos(380, {"front": "fash1", "right": "fash2", "left": "fash3", "back": "fash4", "top": "studio3"}, "ink", 30)
orb = mesh.orbit_parts(lambda i: part("gem", ["butter", "cream", "coral"][i], r=44, h=78, gloss=22), 3, 340, b + 0.8, b + 8.6, 1.0)
mesh.mesh(S, "d_c", b + 0.5, 540, 660, cube + orb, 1100, rx=-22, ry=spin(b + 0.4, b + 8.8, -30, 150), persp=1900)
S.wipe(35.0, "pink", "x", 1)

# Act 5 (35-45): brand
b = 35.0
mesh.mesh(S, "e_g", b + 0.3, 540, 290, [part("gem", "coral", r=130, h=230, gloss=24, seg=8)], 500, rx=-12, ry=spin(b + 0.2, b + 8, 0, 300), persp=1900)
S.headline("e_n", "NOIR", b + 0.6, 640, 400, "ink", mode="split", dur=1.1)
ui.button(S, "e_b", b + 2.0, 540, 880, 460, 130, "Shop the drop", "ink", "pink", press=b + 4.0)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(44, 0), (45, 1, "inQuad")])
S.save(Path(__file__).with_name("noir.json"))
