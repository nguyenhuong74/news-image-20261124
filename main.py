#!/usr/bin/env python3
"""The World in One Page - Tuesday 24 November 2026.

Draws a one-page newspaper front page summing up the world's news of
Tuesday 24 November 2026 and writes it to /output/entry.png.

Stdlib only. The image is drawn pixel by pixel: a small hand-built 5x7
bitmap font, filled rectangles, rules and a tiny line chart. No network,
no files read, fully deterministic - the same bytes every run.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (251, 248, 239)
INK = (22, 22, 22)
RED = (163, 22, 33)
GREY = (96, 90, 80)
LIGHT_GREY = (178, 172, 160)
BLUE = (28, 68, 120)
GREEN = (28, 96, 52)


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, pixels, w, h):
    """pixels: bytes of RGB rows, w*h*3. Writes a whole, valid PNG."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += pixels[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", ihdr)
    blob += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    blob += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(blob)


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line, for the chart and rules."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set(px, py, c)
            x += 1
            if d > 0:
                y -= 1
                d += 4 * (x - y) + 10
            else:
                d += 4 * x + 6


# ------------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", ".####", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "\u00b7": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    "a": (".....", ".....", ".####", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
}


# ------------------------------------------------------------ text drawing
def char_w(scale):
    return 6 * scale


def text_width(s, scale):
    return len(s) * char_w(scale) - scale


def draw_char(cv, x, y, ch, scale, color):
    glyph = FONT.get(ch)
    if glyph is None:
        glyph = FONT["?"]
    for row, bits in enumerate(glyph):
        for col, bit in enumerate(bits):
            if bit == "#":
                cv.rect(x + col * scale, y + row * scale, scale, scale, color)


def draw_text(cv, x, y, s, scale, color):
    for ch in s:
        draw_char(cv, x, y, ch, scale, color)
        x += char_w(scale)
    return x


def draw_text_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_width(s, scale) // 2, y, s, scale, color)


def wrap_words(text, max_chars):
    """Greedy word wrap to lines of at most max_chars characters."""
    lines, cur = [], ""
    for word in text.split(" "):
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, w, text, scale, color, leading=None):
    """Draw a wrapped paragraph; returns the y just below the last line."""
    if leading is None:
        leading = 7 * scale + 3
    max_chars = max(1, w // char_w(scale))
    for line in wrap_words(text, max_chars):
        draw_text(cv, x, y, line, scale, color)
        y += leading
    return y


def draw_headline(cv, x, y, w, text, scale, color):
    """Headline: wrapped, with a little extra leading. Returns y below."""
    return draw_para(cv, x, y, w, text, scale, color,
                     leading=7 * scale + 2)


def kicker(cv, x, y, label, scale=2, color=RED):
    """Section label in red caps with a short rule under it."""
    draw_text(cv, x, y, label.upper(), scale, color)
    return y + 7 * scale + 4


def rule(cv, x, y, w, color=INK, t=2):
    cv.hline(x, y, w, color, t)


# ------------------------------------------------------------ small graphics
def draw_globe(cv, cx, cy, r, color):
    """A simple wire globe: circle, meridians, parallels."""
    cv.circle(cx, cy, r, color)
    cv.circle(cx, cy, r - 1, color)
    # vertical meridian ellipse (approximated with two arcs of lines)
    for k in range(-r, r + 1, 2):
        yy = cy + k
        dx = int((r * r - k * k) ** 0.5)
        cv.set(cx - dx, yy, color)
        cv.set(cx + dx, yy, color)
    for k in (-r // 2, 0, r // 2):
        yy = cy + k
        dx = int((r * r - k * k) ** 0.5)
        cv.hline(cx - dx, yy, 2 * dx, color)
    # centre meridian
    cv.vline(cx, cy - r, 2 * r, color)
    cv.line(cx - r // 2, cy - r, cx + r // 2, cy + r, color)
    cv.line(cx + r // 2, cy - r, cx - r // 2, cy + r, color)


def draw_nvda_chart(cv, x, y, w, h):
    """NVDA share-price line: flat, a dip, then a near-vertical jump."""
    cv.rect(x, y, w, h, (255, 255, 255))
    cv.rect(x, y, w, h, INK)  # placeholder overwritten below (border only)
    cv.rect(x + 1, y + 1, w - 2, h - 2, (255, 255, 255))
    # axes
    cv.hline(x + 8, y + h - 22, w - 16, GREY)
    cv.vline(x + 8, y + 8, h - 30, GREY)
    pts = []
    n = 26
    for i in range(n):
        px = x + 10 + i * (w - 24) // (n - 1)
        if i < 15:                      # drift down after the 12 Nov exit
            py = y + h - 26 - (i * 2)
        elif i < 19:                    # flat at the low
            py = y + h - 26 - 28
        else:                           # the 23 Nov jump
            py = y + h - 26 - 28 - (i - 18) * 16
        pts.append((px, py))
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED)
        cv.line(a[0], a[1] + 1, b[0], b[1] + 1, RED)
    # labels
    draw_text(cv, x + 10, y + h - 18, "12 NOV", 1, GREY)
    draw_text(cv, x + w - 46, y + h - 18, "23 NOV", 1, GREY)
    draw_text(cv, x + w - 52, y + 12, "+31%", 2, RED)


# ------------------------------------------------------------- the day's news
# Every fact below was verified against wire and press reports of
# 24 November 2026 before this file was written.
LEAD_BODY = (
    "Nvidia's board voted unanimously on Monday to bring back co-founder "
    "Jensen Huang as president and chief executive, reversing his "
    "resignation of 12 November. US officials had told the board his "
    "return posed no national security risk. Shares closed 31% higher "
    "at $165.05, adding about $950bn of market value, the largest "
    "one-day gain on record."
)

GAZA_BODY = (
    "Israeli airstrikes killed Hamas security chief Naeem Abu Nahel and "
    "six others in Gaza on Tuesday, medics and police said. A day "
    "earlier, strikes killed three people, including a UN aid worker."
)

UKRAINE_BODY = (
    "An overnight Russian attack on Zaporizhzhia killed two people and "
    "wounded 40, including four children, the regional governor said. "
    "Ukrainian naval drones sank a Russian warship at a base in eastern "
    "Libya."
)

IRAN_BODY = (
    "JD Vance and Marco Rubio met Qatar's prime minister separately at "
    "the White House. Tehran said it would use all its tools to "
    "confront the US naval blockade of Iran."
)

COP31_BODY = (
    "The UN climate summit in Antalya, Turkey, ended on Sunday without "
    "an overarching agreement after the EU, the UK and climate-vulnerable "
    "nations rejected a final text that said nothing about fossil fuels. "
    "Talks ran two days into overtime, the longest COP on record."
)

ECHR_BODY = (
    "Europe's human rights court ruled that states may expel migrants "
    "during hybrid border emergencies, when arrivals are used as a tool "
    "of pressure."
)

BRIEFS = [
    "COLOMBIA - A car bomb outside a government office injured more "
    "than 20 people.",
    "UAE - A bus crash in Ras Al Khaimah killed 13 people and "
    "injured 14.",
    "WASHINGTON - Rep. Jimmy Gomez resigned after the Ethics "
    "Committee found evidence of misconduct.",
]


# ------------------------------------------------------------------ layout
def draw_page():
    cv = Canvas(W, H, PAPER)
    MX = 34                      # left margin
    RX = W - MX                  # right edge of content
    CW = RX - MX                 # content width

    # outer double border
    cv.rect(22, 22, W - 44, 2, INK)
    cv.rect(22, H - 24, W - 44, 2, INK)
    cv.rect(22, 22, 2, H - 44, INK)
    cv.rect(W - 24, 22, 2, H - 44, INK)
    cv.rect(28, 28, W - 56, 1, INK)
    cv.rect(28, H - 29, W - 56, 1, INK)
    cv.rect(28, 28, 1, H - 56, INK)
    cv.rect(W - 29, 28, 1, H - 56, INK)

    # ---- masthead ------------------------------------------------------
    draw_globe(cv, MX + 26, 66, 20, INK)
    draw_globe(cv, RX - 26, 66, 20, INK)
    draw_text_centered(cv, W // 2, 46, "THE WORLD IN ONE PAGE", 6, INK)
    rule(cv, MX, 100, CW, INK, 2)
    draw_text(cv, MX, 110, "TUESDAY 24 NOVEMBER 2026", 2, INK)
    right = "ONE DAY \u00b7 ONE PAGE"
    draw_text(cv, RX - text_width(right, 2), 110, right, 2, GREY)
    rule(cv, MX, 132, CW, INK, 4)
    rule(cv, MX, 138, CW, INK, 1)

    # ---- lead story: Nvidia -------------------------------------------
    # Flow-driven layout: every block starts where the previous one ended,
    # so no text can ever run over a rule.
    y = 154
    y = kicker(cv, MX, y, "MARKETS \u00b7 TECHNOLOGY")
    y += 2
    y = draw_headline(cv, MX, y, 620, "NVIDIA'S $950BN U-TURN", 4, INK)
    y += 2
    y = draw_para(cv, MX, y, 620,
                  "Board reinstates Jensen Huang as chief 11 days after "
                  "he quit; shares jump 31%.", 2, INK)
    y += 4
    lead_bottom = draw_para(cv, MX, y, 620, LEAD_BODY, 2, INK)
    draw_nvda_chart(cv, RX - 300, 154, 300, 198)
    draw_text(cv, RX - 300, 356, "NVDA SHARE PRICE, NOVEMBER", 1, GREY)

    rule(cv, MX, lead_bottom + 10, CW, INK, 2)

    # ---- three-column row ----------------------------------------------
    col_w = (CW - 48) // 3
    cols = [
        ("GAZA \u00b7 WAR", "ISRAELI STRIKES KILL HAMAS SECURITY CHIEF",
         GAZA_BODY),
        ("UKRAINE \u00b7 WAR", "ZAPORIZHZHIA HIT AS KYIV SINKS WARSHIP IN LIBYA",
         UKRAINE_BODY),
        ("IRAN \u00b7 STANDOFF", "US BLOCKADE STANDOFF AS QATAR TALKS HELD",
         IRAN_BODY),
    ]
    top = lead_bottom + 22
    col_bottom = top
    for i, (kick, head, body) in enumerate(cols):
        x = MX + i * (col_w + 24)
        yy = kicker(cv, x, top, kick)
        yy += 2
        yy = draw_headline(cv, x, yy, col_w, head, 3, INK)
        yy += 2
        yy = draw_para(cv, x, yy, col_w, body, 2, INK)
        col_bottom = max(col_bottom, yy)
        if i < 2:
            cv.vline(x + col_w + 11, top, col_bottom - top, LIGHT_GREY, 1)

    rule(cv, MX, col_bottom + 10, CW, INK, 2)

    # ---- second row: COP31 + ECHR --------------------------------------
    y = col_bottom + 22
    left_w = 560
    right_x = MX + left_w + 32
    right_w = RX - right_x
    yy = kicker(cv, MX, y, "CLIMATE \u00b7 COP31")
    yy += 2
    yy = draw_headline(cv, MX, yy, left_w, "COP31 ENDS WITH NO DEAL ON FOSSIL FUELS",
                       3, INK)
    yy += 2
    left_bottom = draw_para(cv, MX, yy, left_w, COP31_BODY, 2, INK)
    yy = kicker(cv, right_x, y, "EUROPE \u00b7 RIGHTS")
    yy += 2
    yy = draw_headline(cv, right_x, yy, right_w,
                       "STATES MAY EXPEL MIGRANTS IN BORDER EMERGENCIES",
                       3, INK)
    yy += 2
    right_bottom = draw_para(cv, right_x, yy, right_w, ECHR_BODY, 2, INK)
    row_bottom = max(left_bottom, right_bottom)
    cv.vline(right_x - 16, y, row_bottom - y, LIGHT_GREY, 1)

    rule(cv, MX, row_bottom + 10, CW, INK, 2)

    # ---- in brief -------------------------------------------------------
    y = row_bottom + 22
    y = kicker(cv, MX, y, "IN BRIEF")
    brief_bottom = y
    for i, brief in enumerate(BRIEFS):
        x = MX + i * (col_w + 24)
        brief_bottom = max(brief_bottom,
                           draw_para(cv, x, y, col_w, brief, 2, INK))

    # ---- footer ---------------------------------------------------------
    rule(cv, MX, brief_bottom + 10, CW, INK, 1)
    draw_text_centered(
        cv, W // 2, brief_bottom + 20,
        "Compiled from wire reports \u00b7 Tuesday 24 November 2026 \u00b7 "
        "The World in One Page", 1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw_page()
    path = os.path.join(out_dir, "entry.png")
    write_png(path, bytes(cv.px), W, H)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
