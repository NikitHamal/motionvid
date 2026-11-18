"""v0.9 Mesh Launch: the motionvid pipeline launch video for social. 30 s, 16:9, 60 fps. Prompt -> real UI, real photos, real 3D, sound on the motion."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from motionvid.kit import Scene, ui, mesh, screens, media  # noqa: E402
from motionvid.kit.mesh import part, spin  # noqa: E402

S = Scene(30, "cream")
W, H = S.W, S.H
CODE = [[("scene", "fn"), ("(", "mut"), ("'Atlas, travel app'", "str"), (")", "mut")], [("await ", "kw"), ("render", "fn"), ("(", "mut"), ("'4k'", "str"), (")", "mut")]]

# 1 (0-6): the prompt
S.headline("a1", "Prompt in.", 0.4, 300, 250, "ink", dur=0.9)
S.headline("a2", "Video out.", 0.9, 560, 250, "coral", dur=1.0)
ui.card(S, "a_c", 1.6, 960, 840, 1200, 150, "ink", 75, [ui.typed(S, "a travel app with real photos", 2.0, 17, -520, 0, 52, "cream", 700)])
S.cam(zoom=[(0, 1), (6, 1.05, "inOutSine")])
S.iris(6.0, "ink", 960, 840)

# 2 (6-13): real UI on real devices
b = 6.0
mesh.mesh(S, "b_l", b + 0.4, 640, 660, mesh.laptop3d(screens.site_home(S, 846, 513, b + 1.2, "lake", "Plan it", "coral", "ink", "cream"), 900), 1100, rx=-12, ry=spin(b + 0.3, b + 7, -30, 10), persp=2000)
mesh.mesh(S, "b_p", b + 0.8, 1520, 640, mesh.phone3d(screens.travel_feed(S, 390, 820, b + 1.6, ["beach", "palms", "shore"])), 900, rx=-6, ry=spin(b + 0.7, b + 7, 34, 6))
S.headline("b1", "Real UI.", b + 0.4, 150, 190, "cream", dur=0.9)
S.wipe(13.0, "coral", "x", 1)

# 3 (13-19): real 3D
b = 13.0
cube = mesh.cube_photos(480, {"front": "beach", "right": "sunrise", "left": "shore", "back": "palms", "top": "lake"}, "ink", 32)
orb = mesh.orbit_parts(lambda i: part("gem", ["butter", "cream", "lime", "ink"][i], r=46, h=82, gloss=24), 4, 520, b + 0.8, b + 5.8, 1.0)
mesh.mesh(S, "c_c", b + 0.4, 960, 620, cube + orb, 1300, rx=-22, ry=spin(b + 0.3, b + 5.8, -30, 150), persp=2000)
S.headline("c1", "Real 3D.", b + 0.4, 150, 190, "cream", dur=0.9)
S.slats(19.0, "lime", 6)

# 4 (19-25): proof
b = 19.0
for i, (v, suf, x, lab) in enumerate(((6, "", 480, "demos"), (54, " s", 960, "longest"), (0, " B", 1440, "samples"))):
    ui.card(S, f"d_k{i}", b + 0.4 + i * 0.25, x, 600, 400, 520, "ink", 80)
    c = S.place(f"d_n{i}", ui.counter("lime", 150, x, 560, 0, v, b + 1.0 + i * 0.25, 1.6, suf=suf))
    S.appear(c, b + 0.9 + i * 0.25, sound=None)
    S.count(c, b + 1.0 + i * 0.25, b + 2.6 + i * 0.25, 0, v, ticks=5)
    S.add(f"d_l{i}", "text", "cream", text=lab, size=64, weight=700, x=x, y=730, opacity=[(b + 1.4 + i * 0.25, 0), (b + 1.6 + i * 0.25, 1)])
S.headline("d1", "Proven.", b + 0.2, 150, 190, "ink", dur=0.9)
S.iris(25.0, "ink", 960, 600)

# 5 (25-30): brand
b = 25.0
S.headline("e_n", "motionvid", b + 0.4, 460, 250, "cream", mode="split", dur=1.1)
ui.button(S, "e_b", b + 1.8, 960, 720, 560, 140, "Make yours", "lime", "ink", press=b + 3.2)
S.add("outro", "rrect", "ink", w=W, h=H, x=W / 2, y=H / 2, opacity=[(29, 0), (30, 1, "inQuad")])
S.save(Path(__file__).with_name("launch4.json"))
