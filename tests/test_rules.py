"""Design rules from the brief, enforced mechanically so no agent has to remember them."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [p for pat in ("docs/*.css", "docs/*.html", "docs/*.js", "docs/engine/*.js", "src/*.tsx", "src/*.css", "tools/*.mjs", "examples/*.py")
         for p in ROOT.glob(pat)]
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2B55\U0001F000-\U0001F2FF]")
BLUE_PURPLE = re.compile(r"(blue|indigo|violet|purple|#[0-9a-f]{3,6})", re.I)


def hue(hex_: str) -> float | None:
    h = hex_.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 0.15:
        return None
    d = mx - mn
    hh = ((g - b) / d) % 6 if mx == r else (b - r) / d + 2 if mx == g else (r - g) / d + 4
    return hh * 60


def test_files_found():
    assert len(FILES) >= 10


def test_no_shadows_except_the_reset():
    for p in FILES:
        for line in p.read_text().splitlines():
            if re.search(r"(box|text|drop)-shadow|shadowBlur|shadowColor", line):
                assert "none" in line, f"{p.name}: {line.strip()}"


def test_no_emoji_or_live_badges():
    for p in FILES:
        text = p.read_text()
        assert not EMOJI.search(text), p.name
        assert not re.search(r">\s*LIVE\s*<|\bLIVE\b badge", text), p.name


def test_no_blue_or_purple_gradients():
    for p in FILES:
        for line in p.read_text().splitlines():
            if "gradient" in line:
                for m in BLUE_PURPLE.findall(line):
                    if m.startswith("#"):
                        h = hue(m)
                        assert h is None or not 200 <= h <= 310, f"{p.name}: {line.strip()}"
                    else:
                        assert False, f"{p.name}: {line.strip()}"
