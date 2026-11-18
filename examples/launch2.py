"""Social launch video (v0.7): 20 s, 60 fps, 5 acts, engine rev 6. Run: python examples/launch2.py"""

from __future__ import annotations

import json
import pathlib

from reel_lib import H, W, Reel, orbit

R = Reel(20.0, "ink", fps=60)
E = [3.2, 6.8, 10.8, 15.2]
COLS = ["coral", "lime", "butter", "pink", "mint"]


def act1_prompt():
    R.add("p_pill", "rrect", "cream", h=420, r="pill", x=[(0, 960)], y=[(0, 520)], w=[(0.05, 200), (0.7, 1560, "outBack")], scale=[(0.05, 0.3), (0.5, 1, "outBack")])
    R.add("p_dot1", "blob", "coral", w=300, h=300, n=9, x=[(0.2, 960), (0.9, 250, "outExpo")], y=[(0, 520)], scale=[(0.2, 0), (0.7, 1, "outBack")],
          amp=[(0.2, 0.04), (1.5, 0.15, "inOutQuad")], rotation=[(0.2, 0), (E[0], 240)])
    R.add("p_dot2", "blob", "mint", w=260, h=260, n=7, x=[(0.3, 960), (1.0, 1670, "outExpo")], y=[(0, 520)], scale=[(0.3, 0), (0.8, 1, "outBack")],
          amp=[(0.3, 0.05), (1.6, 0.16, "inOutQuad")], rotation=[(0.3, 0), (E[0], -220)])
    R.add("p_t1", "text", "ink", text="PROMPT", size=250, split=True, stagger=0.09, x=[(0, 960)], y=[(0, 470)], p=[(0.55, 0), (1.35, 1)])
    R.add("p_t2", "text", "coral", text="TO VIDEO", size=120, type={"t": 1.5, "cps": 12, "n": 8}, x=[(0, 960)], y=[(0, 640)])
    R.flood("f1", "lime", E[0])


def act2_json():
    b = E[0]
    R.add("j_t", "text", "ink", text="JSON", size=200, split=True, stagger=0.08, x=[(0, 960)], y=[(0, 150)], p=[(b + 0.06, 0), (b + 0.75, 1)])
    for i in range(6):
        y, t0 = 300 + i * 105, b + 0.12 + i * 0.06
        w1 = [1300, 760, 1100, 900, 1420, 640][i]
        R.add(f"j_l{i}", "rrect", ["ink", "coral", "ink", "butter", "ink", "mint"][i], r="pill", h=70, x=[(0, 560 + w1 / 2 - 400)],
              y=[(0, y), (b + 2.55, y), (b + 3.05, 560, "inCubic")],
              w=[(t0, 0), (t0 + 0.45, w1, "outBack"), (b + 1.5, w1 * 0.55, "outElastic"), (b + 2.2, w1 * 0.9, "outElastic"), (b + 2.95, 90, "inBack")])
    R.flood("f2", "coral", E[1], 960, 560)


def act3_sound():
    b = E[1]
    R.add("s_t", "text", "ink", text="SOUND", size=230, split=True, stagger=0.07, x=[(0, 960)], y=[(0, 170)], p=[(b + 0.06, 0), (b + 0.8, 1)])
    R.add("s_track", "rrect", "ink", r="pill", h=34, x=[(0, 960)], y=[(0, 900)], w=[(b + 0.08, 0), (b + 0.5, 1600, "outExpo")])
    t0, td = b + 0.35, 1.0
    R.add("s_ball", "blob", "cream", n=9, amp=0.11, w=230, h=230, x=[(0, 1630), (b + 1.65, 1630), (b + 2.95, 290, "inOutCubic")],
          y=[(t0, -150), (t0 + td, 765, "outBounce")], rotation=[(t0, 0), (b + 2.95, -840)])
    for u, g in zip((1 / 2.75, 2 / 2.75, 2.5 / 2.75, 1.0), (-6, -10, -14, -19)):
        R.sfx(t0 + td * u, "impact", 0.28, g, pan=0.6)
    for i, (word, ws, we) in enumerate([("48 KHZ", 0.5, 1.4), ("0 SAMPLES", 1.4, 2.35)]):
        R.add(f"s_n{i}", "text", "ink", text=word, size=270, x=[(0, 960)], y=[(0, 450)], scale=[(b + ws, 1.3), (b + ws + 0.2, 1.0, "outBack")],
              opacity=[(b + ws - 0.001, 0), (b + ws, 1), (b + we - 0.001, 1), (b + we, 0)])
    R.add("s_hero", "blob", "lime", n=8, amp=0.12, w=290, h=290, x=[(0, 290)], y=[(0, 765)], scale=[(b + 2.95, 0), (b + 3.2, 1, "outBack")], rotation=[(b + 2.95, 0), (E[2], 140)])
    R.flood("f3", "butter", E[2], 290, 765, size=3800)


def act4_gates():
    b = E[2]
    for i in range(8):
        xs, ys = orbit(960, 540, 400, i * 45, i * 45 + 210, b + 0.12, b + 2.3, steps=18)
        xs.append((b + 2.7, 960, "inCubic"))
        ys.append((b + 2.7, 540, "inCubic"))
        t0 = b + 0.1 + (i % 4) * 0.06
        R.add(f"g_n{i}", "blob", COLS[i % 5], n=6 + i % 4, w=170, h=170, amp=[(t0, 0.04), (b + 1.2, 0.2, "outBack"), (b + 2.4, 0.04, "inOutQuad")],
              x=xs, y=ys, scale=[(t0, 0), (t0 + 0.3, 1, "outBack"), (b + 2.65, 1), (b + 2.72, 0)], rotation=[(t0, 0), (b + 2.7, 300 * (1 if i % 2 else -1))])
    R.add("g_core", "blob", "ink", n=12, amp=0.09, w=1240, h=1240, x=[(0, 960)], y=[(0, 540)], scale=[(b + 2.6, 0), (b + 3.1, 1, "outElastic")], rotation=[(b + 2.6, 0), (E[3], 45)])
    R.add("g_txt", "text", "butter", text="17 / 17", size=300, split=True, x=[(0, 960)], y=[(0, 540)], p=[(b + 2.65, 0), (b + 3.2, 1)])
    R.sfx(E[3] - 0.55, "riser", 0.55, -10)
    R.flood("f4", "ink", E[3])


def act5_brand():
    b = E[3]
    R.add("b_halo", "blob", "coral", n=12, amp=0.08, w=960, h=960, x=[(0, 960)], y=[(0, 500)], scale=[(b + 0.05, 0), (b + 0.8, 1, "outElastic")], rotation=[(b, 0), (20.0, 60)])
    for i, (c, t) in enumerate([("butter", 0.35), ("lime", 0.7), ("mint", 1.05)]):
        R.add(f"b_r{i}", "ring", c, stroke=15, x=[(0, 960)], y=[(0, 500)], w=[(b + t, 440), (b + t + 0.9, 2240, "outExpo")], opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 0.9, 0)])
    R.add("b_name", "text", "cream", text="motionvid", size=275, split=True, stagger=0.08, x=[(0, 960)], y=[(0, 490)], p=[(b + 0.25, 0), (b + 1.1, 1)])
    R.add("b_cta", "text", "butter", text="OPEN SOURCE", size=90, type={"t": b + 1.35, "cps": 12, "n": 11}, x=[(0, 960)], y=[(0, 745)])
    for i, (c, x, y) in enumerate([("lime", 250, 250), ("butter", 1680, 260), ("pink", 1620, 860), ("mint", 300, 850)]):
        R.add(f"b_s{i}", "blob", c, n=6 + i, amp=0.14, w=170, h=170, x=[(0, x)], y=[(0, y)], scale=[(b + 1.7 + i * 0.12, 0), (b + 2.1 + i * 0.12, 1, "outBack")],
              rotation=[(b + 1.7, 0), (20.0, 180 * (1 if i % 2 else -1))])
    R.add("outro", "rrect", "ink", w=W, h=H, opacity=[(19.3, 0), (20.0, 1, "inQuad")], x=[(0, 960)], y=[(0, 540)])


for act in (act1_prompt, act2_json, act3_sound, act4_gates, act5_brand):
    act()
out = pathlib.Path(__file__).with_name("launch2.json")
out.write_text(json.dumps(R.build(), separators=(",", ":")))
print(f"wrote {out.name}: {len(R.tl['elements'])} elements, {len(R.tl['sfx'])} sfx hints")
