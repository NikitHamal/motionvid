"""Motion-design showreel, 21 s, authored with motionvid itself. Run: python examples/showreel.py"""

from __future__ import annotations

import json
import pathlib

from reel_lib import H, W, Reel, orbit

R = Reel(21.0, "cream")
C = (W / 2, H / 2)
E = [3.5, 7.5, 11.5, 15.5]  # scene boundaries: the moment each color flood closes


def scene1():
    R.add("cookie", "blob", "coral", w=640, h=640, n=10, x=[(0, 960)], y=[(0, 540)],
          scale=[(0.2, 0, None), (0.9, 1, "outBack")], amp=[(0.2, 0.02), (1.1, 0.1, "outBack")],
          rotation=[(0.2, 0), (E[0], 320)])
    xs, ys = orbit(*C, 520, -150, 330, 0.7, E[0] - 0.4)
    R.add("orb_lime", "blob", "lime", w=200, h=200, n=6, amp=0.14, x=xs, y=ys,
          scale=[(0.6, 0), (1.1, 1, "outBack")], rotation=[(0.6, 0), (E[0], 500)])
    R.add("ring", "ring", "ink", w=[(0.9, 700), (1.8, 1700, "outExpo")], stroke=14,
          opacity=[(0.899, 0), (0.9, 1), (1.8, 0)], x=[(0, 960)], y=[(0, 540)])
    R.add("motion", "text", "ink", text="MOTION", size=290, split=True, stagger=0.12, x=[(0, 960)], y=[(0, 470)],
          p=[(1.0, 0), (2.0, 1)])
    R.split_clicks(1.0, 6, 1.0, 0.12)
    R.add("reel", "text", "ink", text="REEL 2026", size=120, type={"t": 2.2, "cps": 12, "n": 9},
          x=[(0, 960)], y=[(0, 700)])
    R.sfx(0.55, "ui_pop", 0.25, -9)
    R.flood("flood_ink", "ink", E[0], dur=0.5)


def scene2():
    b = E[0]
    rows = [("coral", 330, 1250), ("butter", 490, 880), ("lime", 650, 1400), ("pink", 810, 700)]
    R.add("label", "text", "cream", text="SPRING", size=150, split=True, x=[(0, 960)], y=[(0, 150)],
          p=[(b + 0.05, 0), (b + 0.85, 1)])
    R.split_clicks(b + 0.05, 6, 0.8, 0.12)
    for i, (col, y, w) in enumerate(rows):
        t0 = b + 0.2 + i * 0.12
        wt = [(t0, 0), (t0 + 0.5, w, "outBack")]
        for j in range(4):  # equalizer dance on the beat
            tb = b + 1.0 + j * 0.5
            wt.append((tb + 0.28, [w, 420, 1500, 960, 1250][(i + j * 2) % 5] * (0.8 + 0.2 * ((i + j) % 2)), "outBack"))
            R.sfx(tb + 0.1, "ui_pop", 0.15, -19 + (j % 2) * 2, pan=(i - 1.5) * 0.35)
        wt.append((b + 3.0, 130, "inBack"))
        R.add(f"pill{i}", "rrect", col, r="pill", h=130, x=[(0, 960)], y=[(0, y), (b + 2.55, y), (b + 3.2, 540, "inCubic")],
              w=wt)
        R.sfx(t0 + 0.25, "ui_pop", 0.25, -11, pan=(i - 1.5) * 0.4)
    R.flood("flood_lime", "lime", E[1])


def scene3():
    b = E[1]
    R.add("ground", "rrect", "ink", w=[(b + 0.1, 0), (b + 0.5, 1560, "outExpo")], h=30, r="pill",
          x=[(0, 960)], y=[(0, 905)])
    t0, td = b + 0.35, 1.1
    contacts = [t0 + td * u for u in (1 / 2.75, 2 / 2.75, 2.5 / 2.75, 1.0)]
    R.add("ball", "blob", "coral", n=7, amp=0.1, w=210, h=210, x=[(0, 300), (b + 1.7, 300), (b + 3.1, 1620, "inOutCubic")],
          y=[(t0, -160), (t0 + td, 785, "outBounce")], rotation=[(t0, 0), (b + 3.1, 900)])
    for tc, g in zip(contacts, (-5, -9, -14, -20)):
        R.sfx(tc, "impact", 0.3, g, pan=-0.6)
    for i, (word, ws, we) in enumerate([("SHAPE", 0.45, 1.45), ("TIME", 1.45, 2.3), ("SOUND", 2.3, 3.4)]):
        R.add(f"w{i}", "text", "ink", text=word, size=400, x=[(0, 1170)], y=[(0, 400)],
              scale=[(b + ws, 1.35), (b + ws + 0.2, 1, "outBack")],
              opacity=[(b + ws - 0.001, 0), (b + ws, 1), (b + we - 0.001, 1), (b + we, 0)])
        R.sfx(b + ws + 0.04, "ui_pop", 0.3, -8, pan=0.3)
    R.sfx(b + 2.0, "whoosh", 0.8, -13, pan=0.0)
    R.flood("flood_coral", "coral", E[2])


def scene4():
    b = E[2]
    cols = ["cream", "ink", "butter", "pink", "lime", "cream", "mint", "butter", "ink"]
    ns = [5, 6, 7, 8, 9, 10, 12, 6, 8]
    for idx in range(9):
        i, j = idx % 3, idx // 3
        x, y = 960 + (i - 1) * 400, 540 + (j - 1) * 330
        order = (i + j) * 0.09 + (0.04 if (i + j) % 2 else 0)
        t0 = b + 0.1 + order
        R.add(f"g{idx}", "blob", cols[idx], n=ns[idx], w=270, h=270, amp=[(t0, 0.03), (t0 + 0.4, 0.16, "outBack"), (b + 2.4, 0.04, "inOutQuad")],
              x=[(0, x), (b + 2.55, x), (b + 3.0, 960, "inCubic")], y=[(0, y), (b + 2.55, y), (b + 3.0, 540, "inCubic")],
              scale=[(t0, 0), (t0 + 0.4, 1, "outBack"), (b + 3.0, 1), (b + 3.01, 0)],
              rotation=[(t0, 0), (b + 3.0, 240 * (1 if idx % 2 else -1))])
    R.add("hero", "blob", "cream", n=12, amp=0.11, w=1000, h=1000, x=[(0, 960)], y=[(0, 540)],
          scale=[(b + 3.0, 0), (b + 3.45, 1, "outElastic")], rotation=[(b + 3.0, 0), (b + 3.6, 40)])
    R.add("craft", "text", "ink", text="CRAFT", size=300, split=True, x=[(0, 960)], y=[(0, 540)],
          p=[(b + 3.05, 0), (b + 3.7, 1)])
    R.sfx(b + 2.95, "riser", 1.0, -12)
    R.flood("flood_cream", "cream", E[3])


def scene5():
    b = E[3]
    R.add("big", "blob", "ink", n=14, amp=0.07, w=1560, h=1560, x=[(0, 960)], y=[(0, 540)],
          scale=[(b + 0.0, 0), (b + 0.9, 1, "outElastic"), (b + 3.4, 1), (b + 3.9, 1.1, "inOutQuad")],
          rotation=[(b, 0), (b + 5.5, 60)])
    for i, t in enumerate((0.45, 0.8, 1.15)):
        R.add(f"pulse{i}", "ring", ["coral", "butter", "pink"][i], stroke=18, x=[(0, 960)], y=[(0, 540)],
              w=[(b + t, 500), (b + t + 0.9, 2300, "outExpo")], opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 0.9, 0)])
    R.add("name", "text", "cream", text="motionvid", size=250, split=True, stagger=0.1, x=[(0, 960)], y=[(0, 520)],
          p=[(b + 0.7, 0), (b + 1.7, 1)])
    R.split_clicks(b + 0.7, 9, 1.0, 0.1)
    R.add("sub", "text", "butter", text="MOTION DESIGN REEL", size=84, type={"t": b + 2.1, "cps": 14, "n": 18},
          x=[(0, 960)], y=[(0, 720)], weight=700)
    for i, (col, x, y) in enumerate([("coral", 250, 250), ("butter", 1700, 300), ("pink", 1560, 880), ("lime", 330, 860)]):
        R.add(f"dot{i}", "blob", col, n=5 + i, amp=0.15, w=190, h=190, x=[(0, x)], y=[(0, y)],
              scale=[(b + 1.8 + i * 0.18, 0), (b + 2.3 + i * 0.18, 1, "outBack")], rotation=[(b + 1.8, 0), (b + 5.5, 200 * (1 if i % 2 else -1))])
    R.sfx(b + 4.1, "riser", 0.9, -12)
    R.sfx(b + 4.15, "impact", 0.9, -4)
    R.add("end", "rrect", "ink", w=W, h=H, opacity=[(b + 4.6, 0), (b + 5.5, 1, "inQuad")], x=[(0, 960)], y=[(0, 540)])


for s in (scene1, scene2, scene3, scene4, scene5):
    s()
out = pathlib.Path(__file__).with_name("showreel.json")
out.write_text(json.dumps(R.build(), separators=(",", ":")))
print(f"wrote {out.name}: {len(R.tl['elements'])} elements, {len(R.tl['sfx'])} sfx hints")
