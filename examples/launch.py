"""Social-media Launch Video (v0.5): 16.8 s, 60 fps pipeline launch video for motionvid. Run: python examples/launch.py"""

from __future__ import annotations

import json
import math
import pathlib

from reel_lib import H, W, Reel, orbit

R = Reel(16.8, "cream", fps=60)
E = [3.2, 6.6, 10.2, 13.4]  # 5 tight social-media launch acts
COLS = ["coral", "lime", "butter", "pink", "mint"]


def act1_problem_to_hook():
    # 0:00.0 - 0:03.2: "CODE" + "TO MOTION" kinetic hero reveal with M3 Expressive morphing badge + orbiting satellite pills
    R.add("hero_pill", "rrect", "ink", w=[(0.05, 220), (0.65, 1360, "outBack")], h=460, r="pill", x=[(0, 960)], y=[(0, 540)],
          scale=[(0.05, 0.2), (0.55, 1.0, "outBack")])
    R.add("cookie_l", "blob", "coral", w=340, h=340, n=10, x=[(0.15, 960), (0.85, 340, "outExpo")], y=[(0, 540)],
          scale=[(0.15, 0), (0.65, 1, "outBack")], amp=[(0.15, 0.04), (1.4, 0.14, "inOutQuad")], rotation=[(0.15, 0), (E[0], 240)])
    R.add("cookie_r", "blob", "lime", w=300, h=300, n=8, x=[(0.25, 960), (0.95, 1580, "outExpo")], y=[(0, 540)],
          scale=[(0.25, 0), (0.75, 1, "outBack")], amp=[(0.25, 0.05), (1.5, 0.15, "inOutQuad")], rotation=[(0.25, 0), (E[0], -220)])
    R.add("hook1", "text", "cream", text="TIMELINE", size=215, split=True, stagger=0.09, x=[(0, 960)], y=[(0, 445)], p=[(0.55, 0), (1.35, 1)])
    R.add("hook2", "text", "butter", text="JSON TO CINEMA", size=110, type={"t": 1.45, "cps": 14, "n": 14}, x=[(0, 960)], y=[(0, 650)], weight=800)
    for i, (c, t) in enumerate([("coral", 0.55), ("mint", 0.9)]):
        R.add(f"a1_ring{i}", "ring", c, stroke=14, x=[(0, 960)], y=[(0, 540)], w=[(t, 420), (t + 0.85, 2100, "outExpo")],
              opacity=[(t - 0.001, 0), (t, 1), (t + 0.85, 0)])
    R.flood("f_a1", "ink", E[0])


def act2_telemetry_sweep():
    # 0:03.2 - 0:06.6: 240 Hz Scene Telemetry — 5 reactive bars stretch & collapse into center
    b = E[0]
    R.add("tel_title", "text", "cream", text="240 HZ", size=200, split=True, stagger=0.08, x=[(0, 960)], y=[(0, 155)], p=[(b + 0.06, 0), (b + 0.75, 1)])
    for i, c in enumerate(COLS):
        y, t0, w1 = 320 + i * 125, b + 0.14 + i * 0.07, [1480, 920, 1360, 820, 1520][i]
        wt = [(t0, 0), (t0 + 0.45, w1, "outBack"), (b + 1.35, 520 + i * 160, "outElastic"), (b + 2.15, 1440 - i * 110, "outElastic"), (b + 2.85, 90, "inBack")]
        R.add(f"col{i}", "rrect", c, r="pill", h=86, x=[(0, 960)], y=[(0, y), (b + 2.45, y), (b + 2.95, 560, "inCubic")], w=wt)
    R.flood("f_a2", "coral", E[1], 960, 560)


def act3_agency_dsp():
    # 0:06.6 - 0:10.2: 48 kHz Agency DSP — left bounce then tactile L->R slide across the stereo stage
    b = E[1]
    R.add("dsp_track", "rrect", "ink", w=[(b + 0.08, 0), (b + 0.5, 1600, "outExpo")], h=34, r="pill", x=[(0, 960)], y=[(0, 895)])
    t0, td = b + 0.3, 1.1
    R.add("pendulum", "blob", "cream", n=9, amp=0.11, w=230, h=230,
          x=[(0, 290), (b + 1.65, 290), (b + 2.95, 1630, "inOutCubic")],
          y=[(t0, -150), (t0 + td, 765, "outBounce")], rotation=[(t0, 0), (b + 2.95, 840)])
    for u, g in zip((1 / 2.75, 2 / 2.75, 2.5 / 2.75, 1.0), (-6, -10, -14, -19)):
        R.sfx(t0 + td * u, "impact", 0.28, g, pan=-0.6)
    for i, (word, ws, we) in enumerate([("48 KHZ", 0.35, 1.25), ("0 BYTES", 1.25, 2.15), ("25.8X SYNC", 2.15, 3.25)]):
        R.add(f"stat{i}", "text", "ink", text=word, size=310, x=[(0, 960)], y=[(0, 380)],
              scale=[(b + ws, 1.3), (b + ws + 0.2, 1.0, "outBack")],
              opacity=[(b + ws - 0.001, 0), (b + ws, 1), (b + we - 0.001, 1), (b + we, 0)])
    R.add("sync_badge", "blob", "lime", n=8, amp=0.12, w=300, h=300, x=[(0, 1630)], y=[(0, 765)],
          scale=[(b + 2.95, 0), (b + 3.2, 1, "outBack")], rotation=[(b + 2.95, 0), (E[2], 140)])
    R.flood("f_a3", "lime", E[2], 1630, 765, size=3800)


def act4_rsi_loop():
    # 0:10.2 - 0:13.4: Recursive Self-Improvement — 8-node orbital ring converges into the 9/9 FlawBench badge
    b = E[2]
    for i in range(8):
        xs, ys = orbit(960, 540, 420, i * 45, i * 45 + 200, b + 0.12, b + 2.15, steps=18)
        xs.append((b + 2.5, 960, "inCubic"))
        ys.append((b + 2.5, 540, "inCubic"))
        t0 = b + 0.1 + (i % 4) * 0.06
        R.add(f"node{i}", "blob", COLS[i % 5], n=6 + i % 4, w=175, h=175,
              amp=[(t0, 0.04), (b + 1.1, 0.2, "outBack"), (b + 2.2, 0.04, "inOutQuad")],
              x=xs, y=ys, scale=[(t0, 0), (t0 + 0.3, 1, "outBack"), (b + 2.45, 1), (b + 2.52, 0)],
              rotation=[(t0, 0), (b + 2.5, 300 * (1 if i % 2 else -1))])
    R.add("rsi_core", "blob", "ink", n=12, amp=0.09, w=1200, h=1200, x=[(0, 960)], y=[(0, 540)],
          scale=[(b + 2.42, 0), (b + 2.88, 1, "outElastic")], rotation=[(b + 2.42, 0), (E[3], 45)])
    R.add("rsi_txt", "text", "butter", text="9 / 9", size=310, split=True, x=[(0, 960)], y=[(0, 540)], p=[(b + 2.46, 0), (b + 2.96, 1)])
    # Trigger riser from 12.85s -> 13.40s right into the 13.40s cut impact for the motionvid hero reveal
    R.sfx(12.85, "riser", 0.55, -10)
    R.flood("f_a4", "ink", E[3])


def act5_finale():
    # 0:13.4 - 0:16.8: Brand lockup — motionvid + PIPELINE LAUNCH 2026 + 4 M3 Expressive corner seals
    b = E[3]
    R.add("fin_halo", "blob", "coral", n=12, amp=0.08, w=940, h=940, x=[(0, 960)], y=[(0, 500)],
          scale=[(b + 0.05, 0), (b + 0.75, 1, "outElastic")], rotation=[(b, 0), (16.8, 70)])
    for i, (c, t) in enumerate([("butter", 0.35), ("lime", 0.68), ("mint", 1.0)]):
        R.add(f"fin_r{i}", "ring", c, stroke=15, x=[(0, 960)], y=[(0, 500)], w=[(b + t, 420), (b + t + 0.9, 2240, "outExpo")],
              opacity=[(b + t - 0.001, 0), (b + t, 1), (b + t + 0.9, 0)])
    R.add("brand", "text", "cream", text="motionvid", size=265, split=True, stagger=0.08, x=[(0, 960)], y=[(0, 495)], p=[(b + 0.25, 0), (b + 1.1, 1)])
    R.add("cta", "text", "butter", text="PIPELINE LAUNCH 2026", size=82, weight=700, type={"t": b + 1.15, "cps": 16, "n": 20}, x=[(0, 960)], y=[(0, 735)])
    for i, (c, x, y) in enumerate([("lime", 250, 240), ("butter", 1680, 260), ("pink", 1600, 870), ("mint", 310, 860)]):
        R.add(f"seal{i}", "blob", c, n=6 + i, amp=0.14, w=170, h=170, x=[(0, x)], y=[(0, y)],
              scale=[(b + 1.55 + i * 0.12, 0), (b + 1.95 + i * 0.12, 1, "outBack")],
              rotation=[(b + 1.55, 0), (16.8, 180 * (1 if i % 2 else -1))])
    # No triggers after 15.40s so 15.80s-16.80s decays naturally into silence
    R.add("outro", "rrect", "cream", w=W, h=H, opacity=[(16.15, 0), (16.8, 1, "inQuad")], x=[(0, 960)], y=[(0, 540)])


for act in (act1_problem_to_hook, act2_telemetry_sweep, act3_agency_dsp, act4_rsi_loop, act5_finale):
    act()
out = pathlib.Path(__file__).with_name("launch.json")
out.write_text(json.dumps(R.build(), separators=(",", ":")))
print(f"wrote {out.name}: {len(R.tl['elements'])} elements, {len(R.tl['sfx'])} sfx hints")
