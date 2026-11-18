"""Reel III (v0.4): 20.4 s, 60 fps motion-design résumé showreel authored with motionvid. Run: python examples/reel2.py"""

from __future__ import annotations

import json
import math
import pathlib

from reel_lib import H, W, Reel, orbit

R = Reel(20.4, "ink", fps=60)
E = [3.3, 7.0, 10.6, 13.6, 17.2]  # scene boundaries: exact moments each color flood closes
COLS = ["coral", "lime", "butter", "pink", "mint"]


def scene1():
    # 0:00.0 - 0:03.3: Coral blob scales up + concentric ring pulse + MOTION DESIGN + 6 mini blobs + kinetic pill accents
    R.add("bg_halo", "blob", "butter", w=1260, h=1260, n=8, x=[(0, 960)], y=[(0, 540)],
          scale=[(0.0, 0), (0.85, 1, "outExpo")], amp=[(0.0, 0.04), (1.2, 0.08, "inOutQuad")],
          opacity=[(0.0, 0.18), (E[0], 0.18)], rotation=[(0.0, 0), (E[0], -120)])
    R.add("cookie", "blob", "coral", w=1020, h=1020, n=12, x=[(0, 960)], y=[(0, 540)],
          scale=[(0.05, 0), (0.95, 1, "outElastic")], amp=[(0.05, 0.02), (0.95, 0.09, "outBack")], rotation=[(0.05, 0), (E[0], 210)])
    for i, (c, t) in enumerate([("butter", 0.48), ("lime", 0.74), ("pink", 1.0)]):
        R.add(f"ring{i}", "ring", c, stroke=16, x=[(0, 960)], y=[(0, 540)], w=[(t, 480), (t + 0.9, 2240, "outExpo")],
              opacity=[(t - 0.001, 0), (t, 1), (t + 0.9, 0)])
    R.add("t1", "text", "cream", text="MOTION", size=300, split=True, stagger=0.09, x=[(0, 960)], y=[(0, 410)], p=[(0.65, 0), (1.45, 1)])
    R.add("t2", "text", "butter", text="DESIGN", size=300, split=True, stagger=0.09, x=[(0, 960)], y=[(0, 700)], p=[(0.98, 0), (1.78, 1)])
    for i in range(6):
        xs, ys = orbit(960, 540, 490, i * 60, i * 60 + 165, 1.35 + 0.05 * i, E[0] - 0.3, steps=20)
        R.add(f"o{i}", "blob", COLS[i % 5], n=5 + i % 4, amp=0.15, w=135, h=135, x=xs, y=ys,
              scale=[(1.35 + 0.05 * i, 0), (1.72 + 0.05 * i, 1, "outBack")], rotation=[(1.35, 0), (E[0], 380)])
    R.flood("f1", "butter", E[0])


def scene2():
    # 0:03.3 - 0:07.0: SPRING + 7 colored bars stretching/retracting, collapsing into a single center dot at 0:06.5
    b = E[0]
    R.add("spring", "text", "ink", text="SPRING", size=190, split=True, x=[(0, 960)], y=[(0, 145)], p=[(b + 0.05, 0), (b + 0.8, 1)])
    for i, c in enumerate(["coral", "ink", "cream", "mint", "pink", "lime", "ink"]):
        y, t0, w1 = 295 + i * 95, b + 0.14 + i * 0.06, [1520, 920, 1340, 740, 1140, 1560, 860][i]
        wt = [(t0, 0), (t0 + 0.48, w1, "outBack")]
        for j in range(3):
            wt.append((b + 1.15 + j * 0.55, [440, 1480, 820, 1320, 620][(i + 2 * j) % 5], "outElastic"))
        wt.append((6.5, 90, "inBack"))
        R.add(f"bar{i}", "rrect", c, r="pill", h=72, x=[(0, 960)], y=[(0, y), (6.1, y), (6.5, 580, "inCubic")], w=wt)
    R.add("center_dot", "circle", "coral", x=[(0, 960)], y=[(0, 580)],
          w=[(6.42, 0), (6.55, 220, "outBack")])
    R.flood("f2", "coral", E[1], 960, 580)


def scene3():
    # 0:07.0 - 0:10.6: Black track appears; cream blob bounces on left (SHAPE -> TIME), slides right 0:08.8-0:09.7 (SOUND), lime dot pops at 0:10.0
    b = E[1]
    R.add("ground", "rrect", "ink", w=[(b + 0.08, 0), (b + 0.5, 1580, "outExpo")], h=32, r="pill", x=[(0, 960)], y=[(0, 905)])
    t0, td = b + 0.3, 1.15
    R.add("ball", "blob", "cream", n=7, amp=0.1, w=220, h=220,
          x=[(0, 300), (8.8, 300), (9.7, 1620, "inOutCubic")],
          y=[(t0, -160), (t0 + td, 780, "outBounce")], rotation=[(t0, 0), (9.7, 900)])
    for u, g in zip((1 / 2.75, 2 / 2.75, 2.5 / 2.75, 1.0), (-6, -10, -14, -19)):
        R.sfx(t0 + td * u, "impact", 0.28, g, pan=-0.6)
    for i, (word, ws, we) in enumerate([("SHAPE", 0.35, 1.15), ("TIME", 1.15, 1.8), ("SOUND", 1.8, 3.0)]):
        R.add(f"w{i}", "text", "ink", text=word, size=390, x=[(0, 960)], y=[(0, 390)],
              scale=[(b + ws, 1.32), (b + ws + 0.2, 1, "outBack")],
              opacity=[(b + ws - 0.001, 0), (b + ws, 1), (b + we - 0.001, 1), (b + we, 0)])
    R.add("lime_dot", "blob", "lime", n=8, amp=0.12, w=320, h=320, x=[(0, 1620)], y=[(0, 780)],
          scale=[(9.92, 0), (10.12, 1, "outBack")], rotation=[(9.92, 0), (E[2], 140)])
    R.flood("f3", "lime", E[2], 1620, 780, size=3800)


def scene4():
    # 0:10.6 - 0:13.6: 3x5 grid (15 blobs) pops in, morphs from spiky stars to soft waves (0:11.3-0:13.0), then RHYTHM expands
    b = E[2]
    cols = ["coral", "ink", "pink", "mint", "butter"]
    for j in range(3):
        for i in range(5):
            x, y, d = 960 + (i - 2) * 330, 540 + (j - 1) * 300, math.hypot(i - 2, (j - 1) * 1.1)
            t0 = 10.72 + d * 0.09
            R.add(f"g{i}{j}", "blob", cols[int(round(d)) % 5], n=6 + (i + j) % 5, w=205, h=205,
                  amp=[(t0, 0.04), (11.3, 0.24, "outBack"), (12.95, 0.03, "inOutQuad")],
                  x=[(0, x), (12.65, x), (13.0, 960, "inCubic")], y=[(0, y), (12.65, y), (13.0, 540, "inCubic")],
                  scale=[(t0, 0), (t0 + 0.32, 1, "outBack"), (12.95, 1), (13.02, 0)],
                  rotation=[(t0, 0), (13.0, 240 * (1 if (i + j) % 2 else -1))])
    R.add("hero", "blob", "cream", n=12, amp=0.1, w=1340, h=1340, x=[(0, 960)], y=[(0, 540)],
          scale=[(12.98, 0), (13.38, 1, "outElastic")], rotation=[(12.98, 0), (E[3], 40)])
    R.add("rhythm", "text", "ink", text="RHYTHM", size=260, split=True, x=[(0, 960)], y=[(0, 540)], p=[(13.0, 0), (13.48, 1)])
    R.sfx(12.92, "riser", 0.75, -13)
    R.flood("f4", "cream", E[3], 1700, 200, size=4200)


def scene5():
    # 0:13.6 - 0:17.2: Black blob expands & contracts + TIMING + 14 mini blobs (0:14.8)
    b = E[3]
    R.add("big", "blob", "ink", n=14, amp=0.07, w=1520, h=1520, x=[(0, 960)], y=[(0, 540)],
          scale=[(b, 0), (b + 0.85, 1, "outElastic"), (14.6, 1), (15.1, 0.86, "inOutQuad"), (16.6, 0.96, "inOutQuad")],
          rotation=[(b, 0), (E[4], 55)])
    for i, (c, t) in enumerate([("coral", 0.45), ("butter", 0.85)]):
        R.add(f"pulse{i}", "ring", c, stroke=18, x=[(0, 960)], y=[(0, 540)], w=[(b + t, 500), (b + t + 0.9, 2300, "outExpo")],
              opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 0.9, 0)])
    R.add("timing", "text", "cream", text="TIMING", size=255, split=True, x=[(0, 960)], y=[(0, 540)], p=[(14.72, 0), (15.35, 1)])
    for i in range(14):
        a, r, tb = math.radians(i * (360 / 14)), 540 + (i % 2) * 160, 14.8 + (i % 4) * 0.04
        R.add(f"s{i}", "blob", COLS[i % 5], n=5 + i % 5, amp=0.14, w=115, h=115,
              x=[(0, 960), (tb, 960), (tb + 0.75, 960 + r * math.cos(a), "outExpo")],
              y=[(0, 540), (tb, 540), (tb + 0.75, 540 + 0.7 * r * math.sin(a), "outExpo")],
              scale=[(tb, 0), (tb + 0.16, 1, "outBack"), (16.5, 1), (16.9, 0, "inBack")],
              rotation=[(tb, 0), (16.9, 280 * (1 if i % 2 else -1))])
    R.flood("f5", "ink", E[4])


def scene6():
    # 0:17.2 - 0:20.4: motionvid / MOTION DESIGN REEL + 4 corner blobs
    b = E[4]
    R.add("name", "text", "cream", text="motionvid", size=255, split=True, stagger=0.09, x=[(0, 960)], y=[(0, 495)], p=[(17.55, 0), (18.4, 1)])
    for i, (c, t) in enumerate([("coral", 0.45), ("lime", 0.78), ("pink", 1.1)]):
        R.add(f"r{i}", "ring", c, stroke=14, x=[(0, 960)], y=[(0, 540)], w=[(b + t, 420), (b + t + 0.95, 2200, "outExpo")],
              opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 0.95, 0)])
    R.add("sub", "text", "butter", text="MOTION DESIGN REEL", size=84, weight=700, type={"t": 18.45, "cps": 15, "n": 18}, x=[(0, 960)], y=[(0, 720)])
    for i, (c, x, y) in enumerate([("coral", 250, 250), ("butter", 1700, 300), ("pink", 1560, 880), ("lime", 330, 860)]):
        R.add(f"c{i}", "blob", c, n=5 + i, amp=0.14, w=175, h=175, x=[(0, x)], y=[(0, y)],
              scale=[(18.8 + i * 0.14, 0), (19.25 + i * 0.14, 1, "outBack")],
              rotation=[(18.8, 0), (20.4, 180 * (1 if i % 2 else -1))])
    R.sfx(19.45, "riser", 0.85, -13)
    R.sfx(19.5, "impact", 0.85, -5)
    R.add("end", "rrect", "cream", w=W, h=H, opacity=[(19.7, 0), (20.4, 1, "inQuad")], x=[(0, 960)], y=[(0, 540)])


for s in (scene1, scene2, scene3, scene4, scene5, scene6):
    s()
out = pathlib.Path(__file__).with_name("reel2.json")
out.write_text(json.dumps(R.build(), separators=(",", ":")))
print(f"wrote {out.name}: {len(R.tl['elements'])} elements, {len(R.tl['sfx'])} sfx hints")
