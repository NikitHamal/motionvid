"""Reel II: 20.4 s, 60 fps motion-design showreel authored with motionvid. Run: python examples/reel2.py"""

from __future__ import annotations

import json
import math
import pathlib

from reel_lib import H, W, Reel, orbit

R = Reel(20.4, "ink", fps=60)
E = [3.4, 6.8, 10.4, 14.0, 17.2]  # scene boundaries: the moment each color flood closes
COLS = ["coral", "lime", "butter", "pink", "mint"]


def scene1():
    R.add("cookie", "blob", "coral", w=1000, h=1000, n=12, x=[(0, 960)], y=[(0, 540)],
          scale=[(0.1, 0), (1.0, 1, "outElastic")], amp=[(0.1, 0.02), (1.0, 0.09, "outBack")], rotation=[(0.1, 0), (E[0], 200)])
    for i, (c, t) in enumerate([("butter", 0.55), ("lime", 0.8), ("pink", 1.05)]):
        R.add(f"ring{i}", "ring", c, stroke=16, x=[(0, 960)], y=[(0, 540)], w=[(t, 500), (t + 0.9, 2200, "outExpo")],
              opacity=[(t - 0.001, 0), (t, 1), (t + 0.9, 0)])
    R.add("t1", "text", "cream", text="MOTION", size=300, split=True, stagger=0.1, x=[(0, 960)], y=[(0, 410)], p=[(0.7, 0), (1.5, 1)])
    R.add("t2", "text", "butter", text="DESIGN", size=300, split=True, stagger=0.1, x=[(0, 960)], y=[(0, 700)], p=[(1.0, 0), (1.8, 1)])
    for i in range(8):
        xs, ys = orbit(960, 540, 470, i * 45, i * 45 + 160, 1.4 + 0.06 * i, E[0] - 0.35, steps=20)
        R.add(f"o{i}", "blob", COLS[i % 5], n=5 + i % 4, amp=0.15, w=130, h=130, x=xs, y=ys,
              scale=[(1.4 + 0.06 * i, 0), (1.8 + 0.06 * i, 1, "outBack")], rotation=[(1.4, 0), (E[0], 400)])
    R.flood("f1", "butter", E[0])


def scene2():
    b = E[0]
    R.add("spring", "text", "ink", text="SPRING", size=190, split=True, x=[(0, 960)], y=[(0, 150)], p=[(b + 0.05, 0), (b + 0.85, 1)])
    for i, c in enumerate(["coral", "ink", "cream", "mint", "pink", "lime", "cream"]):
        y, t0, w1 = 300 + i * 95, b + 0.15 + i * 0.07, [1500, 900, 1300, 700, 1100, 1550, 820][i]
        wt = [(t0, 0), (t0 + 0.5, w1, "outBack")]
        for j in range(3):
            wt.append((b + 1.42 + j * 0.55, [420, 1450, 800, 1300, 600][(i + 2 * j) % 5], "outElastic"))
        wt.append((b + 2.75, 90, "inBack"))
        R.add(f"bar{i}", "rrect", c, r="pill", h=70, x=[(0, 960)], y=[(0, y), (b + 2.5, y), (b + 3.05, 600, "inCubic")], w=wt)
    R.flood("f2", "coral", E[1], 960, 600)


def scene3():
    b = E[1]
    R.add("ground", "rrect", "ink", w=[(b + 0.1, 0), (b + 0.55, 1560, "outExpo")], h=30, r="pill", x=[(0, 960)], y=[(0, 905)])
    t0, td = b + 0.35, 1.1
    R.add("ball", "blob", "cream", n=7, amp=0.1, w=210, h=210, x=[(0, 300), (b + 1.7, 300), (b + 3.1, 1620, "inOutCubic")],
          y=[(t0, -160), (t0 + td, 785, "outBounce")], rotation=[(t0, 0), (b + 3.1, 900)])
    for u, g in zip((1 / 2.75, 2 / 2.75, 2.5 / 2.75, 1.0), (-5, -9, -14, -20)):
        R.sfx(t0 + td * u, "impact", 0.3, g, pan=-0.6)
    for i, (word, ws, we) in enumerate([("SHAPE", 0.45, 1.45), ("TIME", 1.45, 2.3), ("SOUND", 2.3, 3.3)]):
        R.add(f"w{i}", "text", "ink", text=word, size=400, x=[(0, 960)], y=[(0, 390)], scale=[(b + ws, 1.35), (b + ws + 0.2, 1, "outBack")],
              opacity=[(b + ws - 0.001, 0), (b + ws, 1), (b + we - 0.001, 1), (b + we, 0)])
    R.flood("f3", "lime", E[2])


def scene4():
    b = E[2]
    cols = ["coral", "ink", "pink", "mint", "butter"]
    for j in range(3):
        for i in range(5):
            x, y, d = 960 + (i - 2) * 330, 540 + (j - 1) * 300, math.hypot(i - 2, (j - 1) * 1.1)
            t0, tw = b + 0.15 + d * 0.12, b + 1.1 + d * 0.1
            R.add(f"g{i}{j}", "blob", cols[int(round(d)) % 5], n=5 + (i + j) % 6, w=210, h=210,
                  amp=[(t0, 0.03), (t0 + 0.4, 0.2, "outBack"), (b + 1.9, 0.05, "inOutQuad")],
                  x=[(0, x), (b + 2.2, x), (b + 2.6, 960, "inCubic")], y=[(0, y), (b + 2.2, y), (b + 2.6, 540, "inCubic")],
                  scale=[(t0, 0), (t0 + 0.4, 1, "outBack"), (tw, 1), (tw + 0.2, 1.3, "outBack"), (tw + 0.45, 1, "inOutQuad"), (b + 2.6, 1), (b + 2.61, 0)],
                  rotation=[(t0, 0), (b + 2.6, 260 * (1 if (i + j) % 2 else -1))])
    R.add("hero", "blob", "cream", n=12, amp=0.11, w=1300, h=1300, x=[(0, 960)], y=[(0, 540)], scale=[(b + 2.62, 0), (b + 3.05, 1, "outElastic")],
          rotation=[(b + 2.62, 0), (b + 3.6, 40)])
    R.add("rhythm", "text", "ink", text="RHYTHM", size=260, split=True, x=[(0, 960)], y=[(0, 540)], p=[(b + 2.65, 0), (b + 3.2, 1)])
    R.sfx(b + 2.55, "riser", 0.9, -12)
    R.flood("f4", "cream", E[3], 1700, 200, size=4200)


def scene5():
    b = E[3]
    R.add("big", "blob", "ink", n=14, amp=0.07, w=1500, h=1500, x=[(0, 960)], y=[(0, 540)],
          scale=[(b, 0), (b + 0.9, 1, "outElastic"), (b + 2.8, 1), (b + 3.2, 0.9, "inOutQuad")], rotation=[(b, 0), (b + 3.2, 50)])
    for i, (c, t) in enumerate([("coral", 0.5), ("butter", 0.9)]):
        R.add(f"pulse{i}", "ring", c, stroke=18, x=[(0, 960)], y=[(0, 540)], w=[(b + t, 500), (b + t + 0.9, 2300, "outExpo")],
              opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 0.9, 0)])
    R.add("timing", "text", "cream", text="TIMING", size=250, split=True, x=[(0, 960)], y=[(0, 540)], p=[(b + 0.6, 0), (b + 1.4, 1)])
    for i in range(18):
        a, r, tb = math.radians(i * 20), 520 + (i % 3) * 170, b + 0.95 + (i % 6) * 0.05
        R.add(f"s{i}", "blob", COLS[i % 5], n=5 + i % 5, amp=0.14, w=110 + (i % 3) * 30, h=110 + (i % 3) * 30,
              x=[(0, 960), (tb, 960), (tb + 0.8, 960 + r * math.cos(a), "outExpo")], y=[(0, 540), (tb, 540), (tb + 0.8, 540 + 0.7 * r * math.sin(a), "outExpo")],
              scale=[(tb, 0), (tb + 0.15, 1, "outBack"), (b + 2.6, 1), (b + 3.0, 0, "inBack")], rotation=[(tb, 0), (b + 3.0, 300 * (1 if i % 2 else -1))])
    R.flood("f5", "ink", E[4])


def scene6():
    b = E[4]
    R.add("name", "text", "cream", text="motionvid", size=250, split=True, stagger=0.1, x=[(0, 960)], y=[(0, 500)], p=[(b + 0.2, 0), (b + 1.2, 1)])
    for i, (c, t) in enumerate([("coral", 0.5), ("lime", 0.8), ("pink", 1.1)]):
        R.add(f"r{i}", "ring", c, stroke=14, x=[(0, 960)], y=[(0, 540)], w=[(b + t, 400), (b + t + 1.0, 2200, "outExpo")],
              opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 1.0, 0)])
    R.add("sub", "text", "butter", text="MOTION DESIGN REEL", size=84, weight=700, type={"t": b + 1.2, "cps": 14, "n": 18}, x=[(0, 960)], y=[(0, 720)])
    for i, (c, x, y) in enumerate([("coral", 250, 250), ("butter", 1700, 300), ("pink", 1560, 880), ("lime", 330, 860)]):
        R.add(f"c{i}", "blob", c, n=5 + i, amp=0.15, w=190, h=190, x=[(0, x)], y=[(0, y)], scale=[(b + 1.9 + i * 0.18, 0), (b + 2.4 + i * 0.18, 1, "outBack")],
              rotation=[(b + 1.9, 0), (b + 3.2, 200 * (1 if i % 2 else -1))])
    R.sfx(b + 2.3, "riser", 0.9, -12)
    R.sfx(b + 2.35, "impact", 0.9, -4)
    R.add("end", "rrect", "cream", w=W, h=H, opacity=[(b + 2.5, 0), (b + 3.2, 1, "inQuad")], x=[(0, 960)], y=[(0, 540)])


for s in (scene1, scene2, scene3, scene4, scene5, scene6):
    s()
out = pathlib.Path(__file__).with_name("reel2.json")
out.write_text(json.dumps(R.build(), separators=(",", ":")))
print(f"wrote {out.name}: {len(R.tl['elements'])} elements, {len(R.tl['sfx'])} sfx hints")
