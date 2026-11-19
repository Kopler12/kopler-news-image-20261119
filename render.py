#!/usr/bin/env python3
"""Render 'THE WORLD TODAY' — a one-image news poster for Thursday 19 November 2026.

Draws a premium newspaper front page at 1024x1024 with PIL only:
masthead with a huge date, a neon-sunset lead panel for the GTA VI launch,
a grid of illustrated story panels, and an 'ALSO TODAY' strip.
Saves entry.png next to this script.
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

W = H = 1024
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------- palette ----------
PAPER = (247, 242, 231)
INK = (26, 26, 38)
MUTE = (84, 84, 96)
CARD = (255, 253, 247)
BORDER = (206, 198, 178)
NAVY = (20, 38, 66)
RED = (178, 44, 36)
GOLD = (255, 197, 61)

_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tsize(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]


def ctext(d, cx, y, s, f, fill):
    w, _ = tsize(d, s, f)
    d.text((cx - w / 2, y), s, font=f, fill=fill)


def wrap(d, s, f, maxw):
    lines, cur = [], ""
    for word in s.split():
        t = (cur + " " + word).strip()
        if tsize(d, t, f)[0] <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def lerp(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def vgrad(d, box, stops):
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    for i in range(h):
        t = i / (h - 1) if h > 1 else 0
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=grad_color(stops, t))


def grad_color(stops, t):
    for j in range(len(stops) - 1):
        p0, c0 = stops[j]
        p1, c1 = stops[j + 1]
        if p0 <= t <= p1:
            return lerp(c0, c1, (t - p0) / max(p1 - p0, 1e-6))
    return stops[-1][1]


# ---------- lead-panel artwork helpers ----------

def palm(d, x, base_y, height, lean, color, w_trunk=7, seed=0):
    """A palm silhouette: curved trunk of segments + drooping fronds."""
    rng = random.Random(seed)
    pts = []
    steps = 14
    for i in range(steps + 1):
        t = i / steps
        px = x + lean * (t * t) * height * 0.35
        py = base_y - t * height
        pts.append((px, py))
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=color, width=w_trunk)
    cx, cy = pts[-1]
    for k in range(8):
        ang = math.radians(-172 + k * 23 + rng.uniform(-4, 4))
        L = height * (0.38 + rng.uniform(0, 0.08))
        # quadratic bezier: crown -> control (out & up) -> tip (out & drooping)
        p0 = (cx, cy)
        pc = (cx + math.cos(ang) * L * 0.55, cy + math.sin(ang) * L * 0.55 - L * 0.16)
        p2 = (cx + math.cos(ang) * L, pc[1] + L * 0.42)
        prev = p0
        steps = 9
        for i in range(1, steps + 1):
            t = i / steps
            qx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * pc[0] + t ** 2 * p2[0]
            qy = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * pc[1] + t ** 2 * p2[1]
            wdt = max(2, (w_trunk - 2) - int(t * 3))
            d.line([prev, (qx, qy)], fill=color, width=wdt)
            prev = (qx, qy)
    d.ellipse([cx - 5, cy - 2, cx + 5, cy + 8], fill=color)


def skyline(d, box, base_y, color, rng, min_h, max_h, win=None):
    x0, _, x1, _ = box
    x = x0 - 6
    while x < x1:
        bw = rng.randint(26, 58)
        bh = rng.randint(min_h, max_h)
        d.rectangle([x, base_y - bh, x + bw, base_y], fill=color)
        if rng.random() < 0.4:
            d.rectangle([x + bw // 2 - 2, base_y - bh - 9, x + bw // 2 + 2, base_y - bh], fill=color)
        if win:
            for _ in range(rng.randint(1, 5)):
                wx = rng.randint(int(x) + 5, int(x + bw) - 7)
                wy = rng.randint(int(base_y - bh) + 6, int(base_y) - 10)
                d.rectangle([wx, wy, wx + 3, wy + 4], fill=win)
        x += bw + rng.randint(2, 9)


def car(d, cx, base_y):
    """Low sports-car silhouette with a neon rim light and underglow."""
    dark = (10, 4, 22)
    neon = (255, 46, 136)
    cw = 258
    x0, x1 = cx - cw // 2, cx + cw // 2
    d.line([(x0 + 18, base_y + 4), (x1 - 18, base_y + 4)], fill=neon, width=5)
    d.line([(x0 + 34, base_y + 10), (x1 - 34, base_y + 10)], fill=(150, 30, 90), width=3)
    d.rounded_rectangle([x0, base_y - 40, x1, base_y - 4], radius=16, fill=dark)
    d.rounded_rectangle([cx - 58, base_y - 70, cx + 66, base_y - 34], radius=16, fill=dark)
    d.rounded_rectangle([cx - 44, base_y - 64, cx - 3, base_y - 40], radius=7, fill=(64, 30, 92))
    d.rounded_rectangle([cx + 7, base_y - 64, cx + 52, base_y - 40], radius=7, fill=(64, 30, 92))
    d.line([(x0 + 14, base_y - 40), (cx - 62, base_y - 40)], fill=neon, width=3)
    d.line([(cx + 70, base_y - 40), (x1 - 14, base_y - 40)], fill=neon, width=3)
    d.polygon([(x1 - 26, base_y - 30), (x1 - 2, base_y - 24), (x1 - 26, base_y - 20)], fill=(255, 224, 130))
    for wx in (x0 + 50, x1 - 50):
        d.ellipse([wx - 19, base_y - 24, wx + 19, base_y + 14], fill=(4, 2, 10), outline=neon, width=3)
        d.ellipse([wx - 6, base_y - 11, wx + 6, base_y + 1], outline=neon, width=2)


# ---------- grid-panel icons (drawn inside the coloured band, ~64px tall) ----------

def icon_chart(d, box):
    x0, y0, x1, y1 = box
    base = y1 - 6
    top = y0 + 4
    span = base - top
    d.line([(x0 + 14, top), (x0 + 14, base), (x1 - 12, base)], fill=(255, 255, 255), width=3)
    heights = [0.30, 0.50, 0.72, 0.97]
    bw = 24
    tops = []
    for i, hf in enumerate(heights):
        bx = x0 + 30 + i * (bw + 13)
        hh = span * hf
        d.rectangle([bx, base - hh, bx + bw, base], fill=(255, 255, 255))
        tops.append((bx + bw // 2, base - hh - 4))
    d.line(tops, fill=GOLD, width=4)
    ax, ay = tops[-1]
    d.polygon([(ax, ay), (ax - 14, ay + 1), (ax - 3, ay + 12)], fill=GOLD)
    ccx, ccy, r = x1 - 36, y0 + 22, 17
    d.ellipse([ccx - r, ccy - r, ccx + r, ccy + r], fill=GOLD, outline=(255, 255, 255), width=3)
    f = F(SANS_B, 22)
    w, h = tsize(d, "$", f)
    d.text((ccx - w / 2, ccy - h / 2 - 2), "$", font=f, fill=(90, 60, 0))


def icon_voyager(d, box):
    x0, y0, x1, y1 = box
    rng = random.Random(7)
    for _ in range(40):
        sx = rng.randint(x0 + 4, x1 - 4)
        sy = rng.randint(y0 + 2, y1 - 2)
        r = rng.choice([1, 1, 1, 2])
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(220, 230, 255))
    ex, ey = x1 - 26, y0 + 16
    d.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], fill=(86, 156, 255))
    d.arc([ex - 8, ey - 8, ex + 8, ey + 8], start=200, end=320, fill=(120, 220, 160), width=3)
    cy = (y0 + y1) // 2
    bx, by = x0 + 74, cy + 12
    d.rectangle([bx - 11, by - 8, bx + 11, by + 10], fill=(232, 236, 244))
    d.line([(bx, by - 8), (bx + 20, by - 22)], fill=(232, 236, 244), width=3)
    dcx, dcy = bx + 34, by - 30
    d.ellipse([dcx - 17, dcy - 17, dcx + 17, dcy + 17], fill=(245, 247, 250))
    d.ellipse([dcx - 10, dcy - 10, dcx + 10, dcy + 10], outline=(160, 170, 190), width=2)
    d.line([(dcx, dcy), (bx + 20, by - 22)], fill=(232, 236, 244), width=3)
    d.line([(bx - 10, by + 6), (x0 + 12, y1 - 4)], fill=(200, 208, 224), width=3)
    d.rectangle([x0 + 7, y1 - 9, x0 + 17, y1 - 2], fill=(200, 208, 224))
    for r in (10, 17, 24):
        d.arc([dcx + 10 - r // 3, dcy - 8 - r, dcx + 10 + r, dcy - 8 + r // 2],
              start=300, end=60, fill=(140, 200, 255), width=2)


def icon_capitol(d, box):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    base = y1 - 2
    white = (246, 248, 250)
    for i, hw in enumerate((88, 78, 68)):
        d.rectangle([cx - hw, base - i * 5, cx + hw, base - i * 5 + 4], fill=white)
    d.rectangle([cx - 58, base - 25, cx + 58, base - 14], fill=white)
    for i in range(6):
        lx = cx - 47 + i * 19
        d.line([(lx, base - 24), (lx, base - 15)], fill=(51, 82, 110), width=3)
    # dome: tall half-ellipse on a drum
    d.rectangle([cx - 34, base - 33, cx + 34, base - 24], fill=white)
    d.pieslice([cx - 34, base - 62, cx + 34, base - 2], start=180, end=360, fill=white)
    d.rectangle([cx - 2, base - 66, cx + 2, base - 58], fill=white)
    d.ellipse([cx - 4, base - 71, cx + 4, base - 63], fill=GOLD)


def icon_bridge(d, box):
    x0, y0, x1, y1 = box
    white = (240, 245, 252)
    deck = y1 - 14
    scx, scy, sr = x0 + 26, y0 + 15, 11
    for k in range(8):
        a = math.radians(k * 45)
        sx, sy = scx + sr * math.cos(a), scy + sr * math.sin(a)
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=GOLD)
    tower_top = y0 + 8
    for tx in (x0 + 58, x1 - 72):
        d.rectangle([tx, tower_top, tx + 11, deck], fill=white)
    d.line([(x0 + 6, deck), (x1 - 6, deck)], fill=white, width=4)
    spans = [(x0 + 6, x0 + 64, deck, tower_top), (x0 + 64, x1 - 66, tower_top, tower_top),
             (x1 - 66, x1 - 6, tower_top, deck)]
    for sx, ex, ty0, ty1 in spans:
        pts = []
        for i in range(17):
            t = i / 16
            px = sx + (ex - sx) * t
            if ty0 == ty1:
                py = ty0 + math.sin(t * math.pi) * 13
            else:
                py = ty0 * (1 - t) + ty1 * t + math.sin(t * math.pi) * 4
            pts.append((px, py))
        d.line(pts, fill=white, width=2)
    for wx in range(x0 + 16, x1 - 40, 46):
        d.arc([wx, deck + 3, wx + 24, deck + 11], start=180, end=360, fill=(170, 205, 245), width=2)


def icon_tanker(d, box):
    x0, y0, x1, y1 = box
    sea = y1 - 12
    hull = (16, 32, 48)
    cols = [(214, 90, 60), (240, 170, 70), (90, 160, 120), (90, 130, 200), (200, 90, 140)]
    for i in range(5):
        for j in range(2):
            bx = x0 + 40 + i * 32
            by = sea - 16 - 11 - j * 12
            d.rectangle([bx, by, bx + 28, by + 11], fill=cols[(i + j) % len(cols)])
    d.rectangle([x1 - 58, sea - 52, x1 - 32, sea - 16], fill=(240, 244, 248))
    d.rectangle([x1 - 54, sea - 46, x1 - 36, sea - 39], fill=(70, 110, 140))
    d.line([(x1 - 45, sea - 52), (x1 - 45, sea - 60)], fill=(240, 244, 248), width=3)
    d.polygon([(x0 + 14, sea - 16), (x1 - 14, sea - 16), (x1 - 34, sea + 1), (x0 + 30, sea + 1)], fill=hull)
    d.line([(x0 + 14, sea - 16), (x1 - 14, sea - 16)], fill=(224, 84, 70), width=4)
    for wx in range(x0 + 12, x1 - 36, 44):
        d.arc([wx, sea + 3, wx + 24, sea + 11], start=180, end=360, fill=(190, 230, 240), width=2)


def icon_missile(d, box):
    x0, y0, x1, y1 = box
    pts = []
    for i in range(25):
        t = i / 24
        px = x0 + 22 + (x1 - x0 - 64) * t
        py = (y1 - 8) - (y1 - y0 - 26) * (t ** 1.4)
        pts.append((px, py))
    for i in range(0, len(pts) - 1, 2):
        d.line([pts[i], pts[i + 1]], fill=(255, 190, 170), width=3)
    cx, cy = x1 - 56, y0 + 22
    ang = math.radians(-38)
    ux, uy = math.cos(ang), math.sin(ang)
    px_, py_ = -uy, ux
    L, Wd = 66, 14
    tip = (cx + ux * L * 0.62, cy + uy * L * 0.62)
    tail = (cx - ux * L * 0.38, cy - uy * L * 0.38)
    body = [
        (tail[0] + px_ * Wd / 2, tail[1] + py_ * Wd / 2),
        (tip[0] + px_ * 2, tip[1] + py_ * 2),
        (tip[0] - px_ * 2, tip[1] - py_ * 2),
        (tail[0] - px_ * Wd / 2, tail[1] - py_ * Wd / 2),
    ]
    d.polygon(body, fill=(245, 246, 248))
    nose = [(tip[0] + px_ * 2, tip[1] + py_ * 2), (tip[0] - px_ * 2, tip[1] - py_ * 2),
            (tip[0] + ux * 15, tip[1] + uy * 15)]
    d.polygon(nose, fill=(224, 60, 50))
    for s in (1, -1):
        fin = [(tail[0], tail[1]),
               (tail[0] - ux * 15 + px_ * s * 15, tail[1] - uy * 15 + py_ * s * 15),
               (tail[0] + px_ * s * (Wd / 2), tail[1] + py_ * s * (Wd / 2))]
        d.polygon(fin, fill=(200, 205, 215))
    flame = [(tail[0] - ux * 4, tail[1] - uy * 4),
             (tail[0] - ux * 27 + px_ * 5, tail[1] - uy * 27 + py_ * 5),
             (tail[0] - ux * 27 - px_ * 5, tail[1] - uy * 27 - py_ * 5)]
    d.polygon(flame, fill=(255, 150, 50))


def icon_crescent(d, box):
    x0, y0, x1, y1 = box
    cy = (y0 + y1) // 2
    cx = x0 + 46
    r = (y1 - y0) // 2 - 4
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
    d.ellipse([cx - r + 14, cy - r - 5, cx + r + 14, cy + r - 5], fill=(91, 62, 153))
    sx, sy = cx + 30, cy - 13
    d.polygon([(sx, sy - 7), (sx + 2, sy - 2), (sx + 7, sy), (sx + 2, sy + 2),
               (sx, sy + 7), (sx - 2, sy + 2), (sx - 7, sy), (sx - 2, sy - 2)], fill=(255, 255, 255))
    pts = [(x0 + 100, y1 - 10), (x0 + 138, y1 - 22), (x0 + 176, y1 - 34), (x0 + 218, y0 + 10)]
    d.line(pts, fill=(255, 255, 255), width=4)
    for (px, py) in pts:
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 255, 255))
    ax, ay = pts[-1]
    d.polygon([(ax, ay), (ax - 14, ay + 1), (ax - 4, ay + 11)], fill=(255, 255, 255))
    f = F(SANS_B, 13)
    d.text((pts[0][0] - 28, pts[0][1] - 28), "2026", font=f, fill=(230, 222, 255))
    d.text((pts[-1][0] - 68, y0 + 2), "2035", font=f, fill=(255, 255, 255))


ICONS = {
    "chart": icon_chart,
    "voyager": icon_voyager,
    "capitol": icon_capitol,
    "bridge": icon_bridge,
    "tanker": icon_tanker,
    "missile": icon_missile,
    "crescent": icon_crescent,
}

BAND_H = 64


def panel(d, box, color, icon, category, headline, caption, head_size=24, cap_size=14, band_h=BAND_H):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=CARD)
    # band: rounded top corners, square bottom edge exactly at y0+band_h
    d.rounded_rectangle([x0, y0, x1, y0 + band_h], radius=10, fill=color)
    d.rectangle([x0, y0 + band_h - 10, x1, y0 + band_h], fill=color)
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=BORDER, width=2)
    ICONS[icon](d, (x0 + 6, y0 + 3, x1 - 6, y0 + band_h - 1))
    tx = x0 + 14
    maxw = (x1 - x0) - 28
    d.text((tx, y0 + band_h + 6), category, font=F(SANS_B, 12), fill=color)
    fh = F(SANS_B, head_size)
    lines = wrap(d, headline, fh, maxw)
    ly = y0 + band_h + 24
    for ln in lines[:2]:
        d.text((tx, ly), ln, font=fh, fill=INK)
        ly += head_size + 5
    fc = F(SANS, cap_size)
    cy = y0 + band_h + 24 + 2 * (head_size + 5) + 3
    for ln in wrap(d, caption, fc, maxw)[:3]:
        d.text((tx, cy), ln, font=fc, fill=MUTE)
        cy += cap_size + 4


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    MX = 36
    RX = W - MX

    # ================= masthead =================
    d.line([(MX, 28), (RX, 28)], fill=INK, width=4)
    d.line([(MX, 36), (RX, 36)], fill=INK, width=1)
    ctext(d, W // 2, 46, "ONE  IMAGE  ·  ALL  THE  DAY'S  NEWS", F(SANS_B, 15), RED)
    ctext(d, W // 2, 68, "THE WORLD TODAY", F(SERIF_B, 74), INK)
    d.rectangle([MX, 156, RX, 214], fill=NAVY)
    ctext(d, W // 2, 166, "THURSDAY · 19 NOVEMBER 2026", F(SANS_B, 42), (255, 255, 255))
    d.line([(MX, 220), (RX, 220)], fill=RED, width=3)

    # ================= lead panel: GTA VI =================
    LX0, LY0, LX1, LY1 = MX, 234, 660, 494
    SKY = [(0.0, (22, 10, 51)), (0.40, (75, 30, 110)), (0.65, (166, 43, 110)),
           (0.85, (232, 78, 122)), (1.0, (255, 154, 61))]
    horizon = 398
    vgrad(d, (LX0, LY0, LX1, horizon), SKY)
    rng = random.Random(19)
    for _ in range(40):
        sx = rng.randint(LX0 + 6, LX1 - 6)
        sy = rng.randint(LY0 + 6, LY0 + 62)
        d.point((sx, sy), fill=(255, 240, 220))
    sun_cx, sun_cy, sun_r = (LX0 + LX1) // 2, horizon - 52, 92
    d.ellipse([sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r], fill=(255, 183, 71))
    for (sy, sh) in ((sun_cy + 18, 4), (sun_cy + 34, 6), (sun_cy + 54, 8)):
        col = grad_color(SKY, (sy - LY0) / (horizon - LY0))
        d.rectangle([sun_cx - sun_r, sy, sun_cx + sun_r, sy + sh], fill=col)
    skyline(d, (LX0, LY0, LX1, horizon), horizon, (42, 17, 80), random.Random(3), 46, 104)
    skyline(d, (LX0, LY0, LX1, horizon), horizon, (22, 9, 44), random.Random(5), 26, 66, win=(255, 209, 102))
    palm(d, LX0 + 86, horizon + 2, 126, -0.45, (13, 5, 28), seed=11)
    palm(d, LX1 - 92, horizon + 2, 140, 0.4, (13, 5, 28), seed=23)
    d.rectangle([LX0, horizon, LX1, horizon + 6], fill=(16, 6, 32))
    car(d, (LX0 + LX1) // 2, horizon - 16)
    chip = "LEAD STORY · CULTURE"
    fchip = F(SANS_B, 14)
    cw, _ = tsize(d, chip, fchip)
    d.rounded_rectangle([LX0 + 14, LY0 + 12, LX0 + 14 + cw + 20, LY0 + 40], radius=6, fill=RED)
    d.text((LX0 + 24, LY0 + 18), chip, font=fchip, fill=(255, 255, 255))
    d.rectangle([LX0, horizon + 6, LX1, LY1], fill=(16, 7, 34))
    d.text((LX0 + 20, horizon + 14), "GTA VI LAUNCHES WORLDWIDE", font=F(SERIF_B, 30), fill=(255, 255, 255))
    d.text((LX0 + 20, horizon + 53), "After a 13-year wait, the biggest game launch in", font=F(SANS, 16), fill=(216, 205, 235))
    d.text((LX0 + 20, horizon + 74), "history begins its global rollout today.", font=F(SANS, 16), fill=(216, 205, 235))
    d.rectangle([LX0, LY0, LX1, LY1], outline=(40, 20, 70), width=2)

    # ================= side panel: Anthropic =================
    panel(d, (676, 234, RX, 494), (14, 124, 102), "chart", "BUSINESS · ARTIFICIAL INTELLIGENCE",
          "ANTHROPIC RAISES $81.3BN",
          "The biggest IPO of all time — a record-breaking stock market debut for the AI company.",
          head_size=26, cap_size=15, band_h=104)

    # ================= grid rows =================
    stories = [
        ((36, 512, 340, 718), (16, 32, 66), "voyager", "SPACE",
         "VOYAGER 1 HITS ONE LIGHT-DAY",
         "NASA's probe, launched in 1977, is now a full light-day from Earth."),
        ((360, 512, 664, 718), (51, 82, 110), "capitol", "US POLITICS",
         "JEFFRIES SET TO BE SPEAKER",
         "Hakeem Jeffries will be the first African-American Speaker of the US House."),
        ((684, 512, 988, 718), (43, 94, 167), "bridge", "EUROPE · UKRAINE",
         "EU'S €45BN UKRAINE LOAN",
         "Repayable once Russia pays reparations; drones exchanged amid Abu Dhabi talks."),
        ((36, 734, 340, 940), (29, 110, 126), "tanker", "MIDDLE EAST",
         "TANKER STRUCK IN HORMUZ STRAIT",
         "UKMTO reports the strike; Saudi-led coalition hits Yemen, Saudi cities stood down after alert."),
        ((360, 734, 664, 940), (110, 20, 35), "missile", "ASIA",
         "N. KOREA FIRES BALLISTIC MISSILES",
         "Launched hours after US, South Korean and Japanese joint drills ended."),
        ((684, 734, 988, 940), (91, 62, 153), "crescent", "SOCIETY · RELIGION",
         "ISLAM LARGEST FAITH BY 2035",
         "A Pew study projects Islam will become the world's largest religion by 2035."),
    ]
    for args in stories:
        panel(d, *args)

    # ================= ALSO TODAY strip =================
    SY = 958
    d.line([(MX, SY - 10), (RX, SY - 10)], fill=INK, width=2)
    d.text((MX, SY), "ALSO TODAY", font=F(SANS_B, 17), fill=RED)
    items = [
        ("PRAGUE", "Protests defend media independence"),
        ("SPAIN", "General strike disrupts ports, factories"),
        ("ESTONIA", "Plans to close border with Russia"),
        ("KENYA", "Drought deepens milk shortage"),
    ]
    fb, fr = F(SANS_B, 14), F(SANS, 14)
    positions = [(192, SY - 1), (576, SY - 1), (192, SY + 25), (576, SY + 25)]
    for (place, rest), (px, py) in zip(items, positions):
        d.text((px, py), place, font=fb, fill=INK)
        pw, _ = tsize(d, place, fb)
        d.text((px + pw + 8, py), "— " + rest, font=fr, fill=MUTE)

    img.save(OUT, optimize=True)
    print("saved", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
