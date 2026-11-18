"""Tempo: music app, vertical 9:16. Torus knot hero, equalizer, phone, cube of covers, helix. 66 s, 1080x1920."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motionvid.kit import Scene, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(66, "coral", width=1080, height=1920)
W, H = S.W, S.H
KN = ["coral", "butter", "lime", "pink", "coral"]

# Act 1 (0-10): knot
S.headline("a1", "Feel", 0.4, 330, 340, "ink", dur=0.9)
S.headline("a2", "the beat.", 0.9, 570, 205, "cream", dur=1.0)
mesh.mesh(S, "a_k", 0.9, 540, 1250, [part("knot", ramp=["#17130F", "#F6EFE3", "#FFD54A", "#17130F"], cycle=3, R=300, r=74, p=2, q=3, gloss=18)], 1100, rx=-22, ry=spin(0.9, 10, 0, 150), rz=[(0.9, -10), (10, 14, "inOutSine")], persp=2000, rim=0.35)
S.wipe(10.0, "ink", "y", 1)

# Act 2 (10-20): equalizer
b = 10.0
S.headline("b1", "Every", b + 0.4, 280, 260, "cream", dur=0.9)
S.headline("b2", "frequency.", b + 0.9, 500, 165, "lime", dur=1.0)
eq = mesh.bars3d([0.3, 0.6, 0.9, 0.5, 1.0, 0.7, 0.4, 0.8, 0.55, 0.95, 0.35], b + 0.8, 860, 760, ["lime", "coral", "butter"], depth=130, stagger=0.09, r=24)
mesh.mesh(S, "b_e", b + 0.6, 540, 1230, eq, 1200, rx=-16, ry=spin(b + 0.5, b + 9.4, -28, 28), persp=2200, rim=0.3)
S.iris(20.0, "butter", 540, 1230)

# Act 3 (20-30): the player
b = 20.0
S.headline("c1", "Pocket-size", b + 0.4, 240, 150, "ink", dur=1.0)
S.headline("c2", "stage.", b + 0.9, 420, 260, "coral", dur=1.0)
mesh.mesh(S, "c_p", b + 0.8, 540, 1250, mesh.phone3d(screens.activity(S, 420, 860, b + 1.5, "coral", "ink"), 520, 1060), 1200, rx=-8, ry=spin(b + 0.7, b + 9.4, -38, 12), persp=2200)
S.slats(30.0, "ink", 8)

# Act 4 (30-40): real city night
b = 30.0
f = media.footage("citynight", 920, 1180, t0=b + 0.3, r=90, loop="pp", zoom=[(b + 0.3, 1.0), (b + 9.4, 1.25, "inOutSine")])
S.appear(S.add("d_v", "video", None, x=540, y=1150, **{k: v for k, v in f.items() if k != "kind"}), b + 0.3, frm=0.7)
S.headline("d1", "Night", b + 0.4, 250, 240, "cream", dur=0.9)
S.headline("d2", "shift.", b + 0.9, 430, 240, "butter", dur=1.0)
S.wipe(40.0, "butter", "x", 1)

# Act 5 (40-50): covers
b = 40.0
cube = mesh.cube_photos(560, {"front": "studio1", "right": "studio2", "left": "studio3", "back": "fash1", "top": "fash2"}, "ink", 36)
orb = mesh.orbit_parts(lambda i: part("sphere", ["coral", "ink", "cream"][i], r=52, gloss=22), 3, 560, b + 0.8, b + 9.4, 1.0)
mesh.mesh(S, "e_c", b + 0.5, 540, 1200, cube + orb, 1300, rx=-22, ry=spin(b + 0.4, b + 9.4, -30, 150), persp=2200)
S.headline("e1", "Your", b + 0.4, 250, 260, "ink", dur=0.9)
S.headline("e2", "covers.", b + 0.9, 440, 260, "coral", dur=1.0)
S.iris(50.0, "ink", 540, 1200)

# Act 6 (50-58): spiral
b = 50.0
S.headline("f1", "Never", b + 0.4, 270, 260, "cream", dur=0.9)
S.headline("f2", "stops.", b + 0.9, 460, 260, "lime", dur=1.0)
mesh.mesh(S, "f_h", b + 0.6, 540, 1260, [part("helix", ramp=KN, R=240, r=44, h=900, turns=3.2, gloss=16)], 1000, rx=-8, ry=spin(b + 0.5, b + 7.8, 0, 260), rz=[(b + 0.5, 14)], persp=2200, rim=0.3)
S.wipe(58.0, "coral", "y", -1)

# Act 7 (58-66): sign-off
b = 58.0
S.headline("g_n", "Tempo", b + 0.5, 800, 250, "ink", mode="split", dur=1.1)
ui.button(S, "g_b", b + 1.8, 540, 1080, 560, 140, "Play", "ink", "cream", press=b + 4.0)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(65, 0), (66, 1, "inQuad")])
S.save(Path(__file__).with_name("tempo.json"))
