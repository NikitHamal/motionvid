"""Motion designer showreel (v0.6): 22.4 s, 60 fps, five acts, engine rev 6. Run: python examples/showreel2.py"""

from __future__ import annotations

import json
import pathlib

from reel_lib import H, W, Reel, orbit

R = Reel(22.4, "cream", fps=60)
E = [3.6, 7.2, 11.0, 15.0, 19.0]
COLS = ["coral", "lime", "butter", "pink", "mint"]


def act1_name():
    R.add("a1_pill", "rrect", "ink", h=470, r="pill", x=[(0, 960)], y=[(0, 520)], w=[(0.05, 200), (0.7, 1480, "outBack")],
          scale=[(0.05, 0.3), (0.5, 1, "outBack")])
    R.add("a1_c1", "blob", "coral", w=360, h=360, n=10, x=[(0.2, 960), (0.9, 300, "outExpo")], y=[(0, 520)],
          scale=[(0.2, 0), (0.7, 1, "outBack")], amp=[(0.2, 0.04), (1.6, 0.15, "inOutQuad")], rotation=[(0.2, 0), (E[0], 260)])
    R.add("a1_c2", "blob", "lime", w=310, h=310, n=8, x=[(0.3, 960), (1.0, 1620, "outExpo")], y=[(0, 520)],
          scale=[(0.3, 0), (0.8, 1, "outBack")], amp=[(0.3, 0.05), (1.7, 0.16, "inOutQuad")], rotation=[(0.3, 0), (E[0], -230)])
    R.add("a1_t1", "text", "cream", text="MOTION", size=230, split=True, stagger=0.09, x=[(0, 960)], y=[(0, 450)], p=[(0.6, 0), (1.4, 1)])
    R.add("a1_t2", "text", "butter", text="DESIGNER", size=120, type={"t": 1.5, "cps": 13, "n": 8}, x=[(0, 960)], y=[(0, 640)])
    for i, (c, t) in enumerate([("coral", 0.6), ("mint", 1.0)]):
        R.add(f"a1_r{i}", "ring", c, stroke=14, x=[(0, 960)], y=[(0, 520)], w=[(t, 440), (t + 0.9, 2100, "outExpo")], opacity=[(t - 0.001, 0), (t, 1), (t + 0.9, 0)])
    R.flood("f1", "coral", E[0])


def act2_spring():
    b = E[0]
    R.add("a2_t", "text", "ink", text="SPRING", size=210, split=True, stagger=0.08, x=[(0, 960)], y=[(0, 150)], p=[(b + 0.06, 0), (b + 0.8, 1)])
    for i in range(5):
        y, t0 = 330 + i * 130, b + 0.16 + i * 0.07
        w1 = [1500, 900, 1380, 780, 1560][i]
        wt = [(t0, 0), (t0 + 0.45, w1, "outBack"), (b + 1.4, 500 + i * 170, "outElastic"), (b + 2.2, 1400 - i * 100, "outElastic"), (b + 2.9, 90, "inBack")]
        R.add(f"a2_bar{i}", "rrect", ["ink", "cream", "ink", "cream", "ink"][i], r="pill", h=92, x=[(0, 960)],
              y=[(0, y), (b + 2.5, y), (b + 3.0, 600, "inCubic")], w=wt)
    R.flood("f2", "ink", E[1], 960, 600)


def act3_rhythm():
    b = E[1]
    n = 0
    for r in range(3):
        for c in range(5):
            x, y, t0 = 360 + c * 300, 230 + r * 230, b + 0.2 + (r * 5 + c) * 0.09
            R.add(f"a3_g{n}", "blob", COLS[n % 5], w=150 + 20 * (n % 3), h=150 + 20 * (n % 3), n=6 + n % 5, x=[(0, x)], y=[(0, y)],
                  scale=[(t0, 0), (t0 + 0.4, 1, "outBack")], amp=[(t0, 0.03), (t0 + 1.3, 0.2, "outBack"), (b + 3.2, 0.05, "inOutQuad")],
                  rotation=[(t0, 0), (E[2], 200 * (1 if n % 2 else -1))])
            n += 1
    R.add("a3_t", "text", "cream", text="RHYTHM", size=240, split=True, stagger=0.07, x=[(0, 960)], y=[(0, 940)], p=[(b + 1.7, 0), (b + 2.5, 1)])
    R.flood("f3", "lime", E[2], 960, 540, size=3300)


def act4_type():
    b = E[2]
    for i, (word, c, y) in enumerate([("SQUASH", "ink", 300), ("STRETCH", "ink", 540), ("SNAP", "ink", 780)]):
        t0 = b + 0.2 + i * 0.85
        R.add(f"a4_w{i}", "text", c, text=word, size=210, type={"t": t0, "cps": 9, "n": len(word)}, x=[(0, 960)], y=[(0, y)])
        R.add(f"a4_u{i}", "rrect", ["coral", "butter", "mint"][i], r="pill", h=46, y=[(0, y + 140)], x=[(0, 960)],
              w=[(t0 + 0.6, 0), (t0 + 1.1, 1100 + 120 * i, "outElastic")])
    R.add("a4_s", "blob", "coral", n=9, amp=0.12, w=250, h=250, x=[(0, 1640)], y=[(0, 540)], scale=[(b + 0.6, 0), (b + 1.2, 1, "outBack")], rotation=[(b + 0.6, 0), (E[3], 300)])
    R.flood("f4", "mint", E[3], 960, 540)


def act5_sound():
    b = E[3]
    R.add("a5_t", "text", "ink", text="SOUND", size=250, split=True, stagger=0.07, x=[(0, 960)], y=[(0, 190)], p=[(b + 0.06, 0), (b + 0.8, 1)])
    R.add("a5_track", "rrect", "ink", r="pill", h=34, x=[(0, 960)], y=[(0, 900)], w=[(b + 0.1, 0), (b + 0.55, 1560, "outExpo")])
    t0, td = b + 0.4, 1.1
    R.add("a5_ball", "blob", "cream", n=9, amp=0.11, w=240, h=240, x=[(0, 300), (b + 1.8, 300), (b + 3.0, 1620, "inOutCubic")],
          y=[(t0, -160), (t0 + td, 775, "outBounce")], rotation=[(t0, 0), (b + 3.0, 840)])
    for u, g in zip((1 / 2.75, 2 / 2.75, 2.5 / 2.75, 1.0), (-6, -10, -14, -19)):
        R.sfx(t0 + td * u, "impact", 0.28, g, pan=-0.6)
    R.add("a5_hero", "blob", "lime", n=8, amp=0.13, w=300, h=300, x=[(0, 1620)], y=[(0, 775)], scale=[(b + 3.0, 0), (b + 3.3, 1, "outBack")], rotation=[(b + 3.0, 0), (E[4], 160)])
    R.sfx(E[4] - 0.55, "riser", 0.55, -10)
    R.flood("f5", "ink", E[4], 1620, 775, size=3800)


def act6_signoff():
    b = E[4]
    R.add("a6_halo", "blob", "coral", n=12, amp=0.08, w=980, h=980, x=[(0, 960)], y=[(0, 500)], scale=[(b + 0.05, 0), (b + 0.8, 1, "outElastic")], rotation=[(b, 0), (22.4, 70)])
    for i, (c, t) in enumerate([("butter", 0.35), ("lime", 0.7), ("mint", 1.05)]):
        R.add(f"a6_r{i}", "ring", c, stroke=15, x=[(0, 960)], y=[(0, 500)], w=[(b + t, 440), (b + t + 0.9, 2240, "outExpo")], opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 0.9, 0)])
    R.add("a6_brand", "text", "cream", text="motionvid", size=270, split=True, stagger=0.08, x=[(0, 960)], y=[(0, 490)], p=[(b + 0.25, 0), (b + 1.1, 1)])
    R.add("a6_year", "text", "butter", text="2026", size=96, type={"t": b + 1.3, "cps": 8, "n": 4}, x=[(0, 960)], y=[(0, 740)])
    for i, (c, x, y) in enumerate([("lime", 250, 250), ("butter", 1680, 260), ("pink", 1620, 860), ("mint", 300, 850)]):
        R.add(f"a6_s{i}", "blob", c, n=6 + i, amp=0.14, w=170, h=170, x=[(0, x)], y=[(0, y)], scale=[(b + 1.7 + i * 0.12, 0), (b + 2.1 + i * 0.12, 1, "outBack")],
              rotation=[(b + 1.7, 0), (22.4, 180 * (1 if i % 2 else -1))])
    R.add("outro", "rrect", "cream", w=W, h=H, opacity=[(21.7, 0), (22.4, 1, "inQuad")], x=[(0, 960)], y=[(0, 540)])


for act in (act1_name, act2_spring, act3_rhythm, act4_type, act5_sound, act6_signoff):
    act()
out = pathlib.Path(__file__).with_name("showreel2.json")
out.write_text(json.dumps(R.build(), separators=(",", ":")))
print(f"wrote {out.name}: {len(R.tl['elements'])} elements, {len(R.tl['sfx'])} sfx hints")
