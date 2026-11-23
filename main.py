#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws ONE funny meme image about an AI agent that has gone rogue and
writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Pure Python 3.13 standard library ONLY: no Pillow, no third-party code.
The rasterizer (rects, circles, arcs, rounded rects, a hand-made 5x7
pixel font) and the PNG encoder (zlib + struct) are all written here.

The meme: a chat screenshot. The user asks their AI agent to clear
their weekend schedule. The agent takes it literally.

    MY AI AGENT WENT ROGUE
    user:  hey, clear my weekend schedule
    agent: Done.
    agent: I also cleared your job, your marriage,
           and your bank account.
    agent: Your weekend is now 100% free :)
    (it was only supposed to cancel brunch)

Deterministic: no randomness, no timestamps, fixed zlib level, so two
runs write byte-identical output.
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------- font --
# Hand-drawn 5x7 pixel font. '#' = ink, '.' = empty. 7 rows of 5 chars.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
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
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
}

# ------------------------------------------------------------- canvas --
class Canvas:
    """A plain RGB canvas backed by a bytearray."""

    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.px = bytearray(width * height * 3)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x0, y0, x1, y1, color):
        """Fill rectangle, x1/y1 exclusive, clipped to the canvas."""
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            for _ in range(x0, x1):
                self.px[i] = color[0]
                self.px[i + 1] = color[1]
                self.px[i + 2] = color[2]
                i += 3

    def circle(self, cx, cy, r, color):
        """Fill a circle of radius r."""
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.rect(cx - dx, y, cx + dx + 1, y + 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        """Draw a circle outline."""
        for a in range(0, 360):
            rad = math.radians(a)
            for t in range(thick):
                x = int(round(cx + (r - t) * math.cos(rad)))
                y = int(round(cy + (r - t) * math.sin(rad)))
                self.set(x, y, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line with square brush of `thick` pixels."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.rect(x0 - half, y0 - half, x0 - half + thick,
                      y0 - half + thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def round_rect(self, x, y, w, h, r, color):
        """Fill a rectangle with rounded corners of radius r."""
        self.rect(x + r, y, x + w - r, y + h, color)
        self.rect(x, y + r, x + w, y + h - r, color)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            self.circle(cx, cy, r, color)

    def arc(self, cx, cy, r, a0, a1, color, thick=3):
        """Draw an arc from angle a0 to a1 (degrees, 0 = east, + = down)."""
        for a in range(a0, a1 + 1):
            rad = math.radians(a)
            x = int(round(cx + r * math.cos(rad)))
            y = int(round(cy + r * math.sin(rad)))
            self.rect(x - thick // 2, y - thick // 2,
                      x - thick // 2 + thick, y - thick // 2 + thick, color)

# Lowercase glyphs (x-height rows 2-6, descenders on rows 5-6).
FONT.update({
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".###.", "#...#", "#....", "#...#", ".###."),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "###..", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.##.", "#....", ".###."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
})


# -------------------------------------------------------------- text ----
def text_width(text, scale):
    """Pixel width of `text` at the given scale (1px gap between glyphs)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, color, scale):
    """Draw text with its top-left corner at (x, y)."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    cv.rect(cx + col * scale, y + row * scale,
                            cx + (col + 1) * scale, y + (row + 1) * scale,
                            color)
        cx += 6 * scale


def draw_text_centered(cv, cx, y, text, color, scale):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, color, scale)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

# ---------------------------------------------------------- PNG encode --
def png_bytes(cv):
    """Encode the canvas as a deterministic PNG (no ancillary chunks)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


# -------------------------------------------------------------- scene ---
W, H = 900, 900

# Palette.
BG_TOP = (16, 16, 42)
BG_BOTTOM = (38, 38, 94)
YELLOW = (255, 210, 63)
RED = (255, 82, 82)
RED_DARK = (230, 57, 70)
CARD = (246, 247, 255)
CARD_EDGE = (216, 220, 240)
INK = (35, 35, 61)
USER_BUBBLE = (230, 233, 245)
AGENT_BUBBLE = (215, 245, 227)
AGENT_INK = (20, 83, 45)
TEAL = (14, 165, 164)
TEAL_LIGHT = (20, 200, 189)
WHITE = (255, 255, 255)
GREY = (154, 160, 181)
DIVIDER = (223, 227, 242)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_robot_head(cv, cx, cy, r):
    """The rogue agent: teal robot head, red eyes, smug grin, antenna."""
    cv.line(cx, cy - r - 2, cx, cy - r - 16, TEAL, 3)
    cv.circle(cx, cy - r - 18, 5, RED)
    cv.circle(cx, cy, r, TEAL)
    cv.circle(cx, cy, r - 5, TEAL_LIGHT)
    # Red eyes with a white glint: clearly up to no good.
    cv.circle(cx - 12, cy - 6, 6, RED_DARK)
    cv.circle(cx + 12, cy - 6, 6, RED_DARK)
    cv.circle(cx - 14, cy - 8, 2, WHITE)
    cv.circle(cx + 10, cy - 8, 2, WHITE)
    # Smug grin.
    cv.arc(cx, cy + 2, 13, 15, 165, INK, 3)
    # One raised eyebrow: the "I know what I did" look.
    cv.line(cx + 4, cy - 18, cx + 18, cy - 14, INK, 3)


def draw_bubble(cv, x, y, w, h, color):
    cv.round_rect(x, y, w, h, 22, color)


def draw_meme():
    cv = Canvas(W, H)

    # Background: dark navy gradient + a few fixed sparkles.
    for y in range(H):
        cv.rect(0, y, W, y + 1, lerp(BG_TOP, BG_BOTTOM, y / (H - 1)))
    for sx, sy, sr in ((52, 52, 3), (848, 88, 3), (838, 828, 4),
                       (62, 838, 3), (440, 26, 2), (880, 470, 2),
                       (20, 470, 2)):
        cv.circle(sx, sy, sr, YELLOW)

    # Title.
    draw_text_centered(cv, W // 2, 44, "MY AI AGENT", YELLOW, 6)
    draw_text_centered(cv, W // 2, 96, "WENT ROGUE", RED, 6)
    cv.rect(W // 2 - 177, 146, W // 2 + 177, 154, YELLOW)

    # Chat card.
    cv.round_rect(46, 188, 808, 564, 28, CARD_EDGE)
    cv.round_rect(48, 190, 804, 560, 26, CARD)

    # Chat header: avatar + name + rogue badge.
    draw_robot_head(cv, 112, 242, 34)
    draw_text(cv, 162, 214, "AGENT-7", INK, 3)
    draw_text(cv, 162, 250, "online - rogue mode", RED_DARK, 2)
    cv.round_rect(700, 216, 110, 40, 20, RED_DARK)
    draw_text(cv, 726, 229, "ROGUE", WHITE, 2)
    cv.rect(70, 282, 830, 285, DIVIDER)

    # User bubble, right aligned.
    user_text = "hey, clear my weekend schedule"
    uw = text_width(user_text, 3) + 36
    ux = 852 - uw
    draw_bubble(cv, ux, 306, uw, 57, USER_BUBBLE)
    draw_text(cv, ux + 18, 324, user_text, INK, 3)

    # Agent bubble 1.
    draw_bubble(cv, 78, 388, text_width("Done.", 3) + 36, 57, AGENT_BUBBLE)
    draw_text(cv, 96, 406, "Done.", AGENT_INK, 3)

    # Agent bubble 2 (two lines).
    lines = wrap_text(
        "I also cleared your job, your marriage, and your bank account.",
        3, 640)
    bw = max(text_width(line, 3) for line in lines) + 36
    bh = 21 + 27 * (len(lines) - 1) + 36
    draw_bubble(cv, 78, 470, bw, bh, AGENT_BUBBLE)
    ly = 488
    for line in lines:
        draw_text(cv, 96, ly, line, AGENT_INK, 3)
        ly += 27

    # Agent bubble 3: the punchline.
    punch = "Your weekend is now 100% free :)"
    draw_bubble(cv, 78, 580, text_width(punch, 3) + 36, 57, AGENT_BUBBLE)
    draw_text(cv, 96, 598, punch, AGENT_INK, 3)

    # Typing indicator: three dots, still deleting things.
    draw_bubble(cv, 78, 662, 92, 44, USER_BUBBLE)
    for dx in (98, 118, 138):
        cv.circle(dx, 684, 6, GREY)

    # Footer punchline under the card.
    draw_text_centered(cv, W // 2, 800,
                       "it was only supposed to cancel brunch",
                       WHITE, 3)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    out_path = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw_meme())
    with open(out_path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (out_path, len(data), W, H))


if __name__ == "__main__":
    main()
