"""SON MOLA: karanlık tema, dizi arka planları, nesneler, hareketli sis, gerilim müziği ve kapanış kartı.
Bölüm JSON'unda "theme": "karanlik" olunca render.py bu modülü kullanır."""
import math
import random

import cairo
import numpy as np

from .draw import W, H, PX, PY, PW, PH, sx, sy, set_font, text_width, TITLE_FONT, CAPTION_FONT, HAND_FONT

# --------------------------------------------------------------------------
# Renkler
# --------------------------------------------------------------------------
BG = (0.035, 0.045, 0.075)          # sayfa zemini
SKY_TOP = (0.03, 0.05, 0.10)
SKY_BOT = (0.10, 0.13, 0.20)
GROUND = (0.07, 0.08, 0.11)
INK = (0.93, 0.94, 0.97)            # çöp adam ve çizgiler
DIM = (0.45, 0.48, 0.56)
WALL = (0.13, 0.14, 0.19)
WALL2 = (0.17, 0.18, 0.24)
LAMP = (1.0, 0.80, 0.48)
RED = (0.93, 0.25, 0.22)
FRAME = (0.22, 0.24, 0.30)

BACKGROUNDS = {"tesis_dis", "tesis_ic", "yol", "karanlik", "pencere", "peron"}
PROPS = {"saat", "liste", "bardak", "telefon", "mont", "tabela", "fener", "kapi", "lamba", "defter", "resim", "far"}


def make_paper(seed=7):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.05, 0.06, 0.10)
    g.add_color_stop_rgb(1, 0.015, 0.02, 0.035)
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(seed)
    for _ in range(5000):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        ctx.set_source_rgba(0.7, 0.75, 0.9, rnd.uniform(0.01, 0.035))
        ctx.arc(x, y, rnd.uniform(0.5, 1.8), 0, 2 * math.pi)
        ctx.fill()
    return surf


def _glow(ctx, x, y, r, col, a=0.5):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col, a)
    g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def _rect(ctx, x, y, w, h, fill, stroke=None, lw=4):
    ctx.rectangle(x, y, w, h)
    ctx.set_source_rgb(*fill)
    if stroke:
        ctx.fill_preserve()
        ctx.set_source_rgb(*stroke)
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def _text(ctx, s, cx, cy, family, size, col, a=1.0):
    set_font(ctx, family, size)
    ctx.set_source_rgba(*col, a)
    ctx.move_to(cx - text_width(ctx, s) / 2, cy + size * 0.35)
    ctx.show_text(s)


def _flicker(t, seed=0):
    """Lamba titremesi: çoğunlukla 1, arada kısa sönmeler."""
    v = 0.92 + 0.08 * math.sin(t * 13 + seed) * math.sin(t * 7.3 + seed * 2)
    if (math.sin(t * 1.7 + seed) > 0.985) or (0.0 < (t * 0.37 + seed) % 5.0 < 0.06):
        v *= 0.35
    return v


# --------------------------------------------------------------------------
# Arka planlar
# --------------------------------------------------------------------------
def draw_bg(ctx, bg, t, sc=None):
    sc = sc or {}
    g = cairo.LinearGradient(0, PY, 0, PY + PH)
    g.add_color_stop_rgb(0, *SKY_TOP)
    g.add_color_stop_rgb(1, *SKY_BOT)
    ctx.set_source(g)
    ctx.rectangle(PX, PY, PW, PH)
    ctx.fill()
    if sc.get("gunduz"):
        g = cairo.LinearGradient(0, PY, 0, PY + PH)
        g.add_color_stop_rgb(0, 0.30, 0.33, 0.40)
        g.add_color_stop_rgb(1, 0.52, 0.50, 0.48)
        ctx.set_source(g)
        ctx.rectangle(PX, PY, PW, PH)
        ctx.fill()
    if bg == "karanlik":
        _rect(ctx, PX, sy(0.92), PW, PY + PH - sy(0.92), (0.04, 0.045, 0.06))
        return
    if bg in ("tesis_dis", "peron"):
        _ground(ctx, 0.80)
        _building(ctx, t, sc, 0.47 if bg == "tesis_dis" else 0.75, big=(bg == "tesis_dis"))
        if bg == "peron":
            _bench(ctx, sx(0.30), sy(0.80))
            _bus_stop_sign(ctx, sx(0.12), sy(0.80))
        else:
            _pump(ctx, sx(0.12), sy(0.80))
            _streetlamp(ctx, sx(0.86), sy(0.80), t)
    elif bg == "yol":
        _road(ctx, t, sc)
    elif bg == "tesis_ic":
        _interior(ctx, t, sc)
    elif bg == "pencere":
        _window_view(ctx, t, sc)


def _ground(ctx, gy):
    _rect(ctx, PX, sy(gy), PW, PY + PH - sy(gy), GROUND)
    ctx.set_source_rgba(*DIM, 0.6)
    ctx.set_line_width(3)
    ctx.move_to(PX, sy(gy))
    ctx.line_to(PX + PW, sy(gy))
    ctx.stroke()


def _building(ctx, t, sc, x_center, big=True):
    bw = 620 if big else 420
    bh = 300 if big else 230
    x0 = sx(x_center) - bw / 2
    y1 = sy(0.80)
    y0 = y1 - bh
    _rect(ctx, x0, y0, bw, bh, WALL, FRAME, 5)
    # çatı saçağı
    ctx.move_to(x0 - 30, y0)
    ctx.line_to(x0 + bw + 30, y0)
    ctx.line_to(x0 + bw + 10, y0 - 34)
    ctx.line_to(x0 - 10, y0 - 34)
    ctx.close_path()
    ctx.set_source_rgb(*WALL2)
    ctx.fill_preserve()
    ctx.set_source_rgb(*FRAME)
    ctx.set_line_width(4)
    ctx.stroke()
    # tabela
    tw, th = (360, 70) if big else (260, 54)
    tx, ty = x0 + bw / 2 - tw / 2, y0 - 34 - th - 14
    fl = _flicker(t, 3)
    _glow(ctx, tx + tw / 2, ty + th / 2, tw * 0.9, LAMP, 0.18 * fl)
    _rect(ctx, tx, ty, tw, th, (0.10, 0.10, 0.12), (0.85, 0.75, 0.55), 4)
    _text(ctx, "SON MOLA", tx + tw / 2, ty + th / 2, CAPTION_FONT, 44 if big else 34, LAMP, 0.55 + 0.45 * fl)
    # pencereler (sarı ışık) + kapı
    n = 3 if big else 2
    ww, wh = (120, 110) if big else (95, 90)
    gap = (bw - n * ww - 120) / (n + 1)
    for i in range(n):
        wx = x0 + gap + i * (ww + gap)
        wy = y0 + 70
        lit = sc.get("isik", True)
        col = tuple(c * (0.55 + 0.45 * _flicker(t, i)) for c in LAMP) if lit else (0.08, 0.09, 0.12)
        if lit:
            _glow(ctx, wx + ww / 2, wy + wh / 2, ww * 1.2, LAMP, 0.15)
        _rect(ctx, wx, wy, ww, wh, col, FRAME, 4)
        ctx.set_source_rgb(*FRAME)
        ctx.set_line_width(3)
        ctx.move_to(wx + ww / 2, wy)
        ctx.line_to(wx + ww / 2, wy + wh)
        ctx.stroke()
    dx = x0 + bw - 120 - gap / 2
    _rect(ctx, dx, y1 - 170, 100, 170, (0.09, 0.09, 0.12), FRAME, 4)
    ctx.set_source_rgb(*LAMP)
    ctx.arc(dx + 82, y1 - 85, 5, 0, 2 * math.pi)
    ctx.fill()


def _pump(ctx, x, y):
    _rect(ctx, x - 30, y - 150, 60, 150, (0.20, 0.08, 0.08), FRAME, 4)
    _rect(ctx, x - 20, y - 130, 40, 40, (0.12, 0.12, 0.14), FRAME, 3)
    ctx.set_source_rgb(*FRAME)
    ctx.set_line_width(5)
    ctx.move_to(x + 30, y - 110)
    ctx.curve_to(x + 60, y - 100, x + 55, y - 40, x + 40, y - 30)
    ctx.stroke()


def _streetlamp(ctx, x, y, t):
    fl = _flicker(t, 7)
    ctx.set_source_rgb(*FRAME)
    ctx.set_line_width(10)
    ctx.move_to(x, y)
    ctx.line_to(x, y - 420)
    ctx.line_to(x - 70, y - 420)
    ctx.stroke()
    _glow(ctx, x - 70, y - 405, 230, LAMP, 0.30 * fl)
    ctx.set_source_rgba(*LAMP, 0.08 * fl)
    ctx.move_to(x - 95, y - 405)
    ctx.line_to(x - 45, y - 405)
    ctx.line_to(x + 60, y)
    ctx.line_to(x - 200, y)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(*(c * fl for c in LAMP))
    ctx.arc(x - 70, y - 405, 12, 0, 2 * math.pi)
    ctx.fill()


def _bench(ctx, x, y):
    ctx.set_source_rgb(*FRAME)
    ctx.set_line_width(8)
    for dx in (-110, 110):
        ctx.move_to(x + dx, y)
        ctx.line_to(x + dx, y - 70)
        ctx.stroke()
    _rect(ctx, x - 140, y - 80, 280, 18, (0.30, 0.22, 0.15), FRAME, 3)
    _rect(ctx, x - 140, y - 150, 280, 16, (0.30, 0.22, 0.15), FRAME, 3)


def _bus_stop_sign(ctx, x, y):
    ctx.set_source_rgb(*FRAME)
    ctx.set_line_width(8)
    ctx.move_to(x, y)
    ctx.line_to(x, y - 300)
    ctx.stroke()
    ctx.arc(x, y - 330, 42, 0, 2 * math.pi)
    ctx.set_source_rgb(0.15, 0.30, 0.55)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.85, 0.85, 0.9)
    ctx.set_line_width(4)
    ctx.stroke()
    _text(ctx, "O", x, y - 332, CAPTION_FONT, 40, (0.9, 0.9, 0.95))


def _road(ctx, t, sc):
    hz = sy(0.42)
    _rect(ctx, PX, hz, PW, PY + PH - hz, GROUND)
    cx = sx(0.5)
    ctx.move_to(cx - 18, hz)
    ctx.line_to(cx + 18, hz)
    ctx.line_to(sx(0.92), PY + PH)
    ctx.line_to(sx(0.08), PY + PH)
    ctx.close_path()
    ctx.set_source_rgb(0.12, 0.12, 0.15)
    ctx.fill()
    # orta şerit (hafif akan)
    for i in range(9):
        u = ((i + (t * 0.25 if sc.get("akis") else 0)) % 9) / 9
        y0 = hz + (PY + PH - hz) * u ** 1.6
        y1 = hz + (PY + PH - hz) * min(1, (u + 0.05)) ** 1.6
        w0, w1 = 2 + 10 * u, 2 + 10 * min(1, u + 0.05)
        ctx.move_to(cx - w0, y0)
        ctx.line_to(cx + w0, y0)
        ctx.line_to(cx + w1, y1)
        ctx.line_to(cx - w1, y1)
        ctx.close_path()
        ctx.set_source_rgba(0.85, 0.80, 0.55, 0.55)
        ctx.fill()
    # ufukta tesisin ışığı (yol hep oraya çıkar)
    if sc.get("ufukta_tesis", True):
        _glow(ctx, cx, hz - 8, 90, LAMP, 0.35)
        _rect(ctx, cx - 40, hz - 26, 80, 26, WALL, FRAME, 2)
        ctx.set_source_rgb(*LAMP)
        ctx.rectangle(cx - 30, hz - 18, 14, 10)
        ctx.rectangle(cx + 6, hz - 18, 14, 10)
        ctx.fill()


def _interior(ctx, t, sc):
    # duvar + zemin
    _rect(ctx, PX, PY, PW, PH * 0.80, (0.11, 0.12, 0.16))
    for i in range(0, 1000, 50):  # ince lambri çizgileri
        ctx.set_source_rgba(1, 1, 1, 0.025)
        ctx.rectangle(PX + i, PY + PH * 0.48, 2, PH * 0.32)
        ctx.fill()
    _rect(ctx, PX, sy(0.80), PW, PH * 0.20, (0.08, 0.07, 0.07))
    # tavan lambası
    fl = _flicker(t, 11)
    ctx.set_source_rgb(*FRAME)
    ctx.set_line_width(4)
    ctx.move_to(sx(0.5), PY)
    ctx.line_to(sx(0.5), PY + 90)
    ctx.stroke()
    _glow(ctx, sx(0.5), PY + 110, 520, LAMP, 0.22 * fl)
    ctx.move_to(sx(0.5) - 60, PY + 120)
    ctx.line_to(sx(0.5) + 60, PY + 120)
    ctx.line_to(sx(0.5) + 30, PY + 90)
    ctx.line_to(sx(0.5) - 30, PY + 90)
    ctx.close_path()
    ctx.set_source_rgb(0.25, 0.25, 0.28)
    ctx.fill()
    # tezgâh
    if sc.get("tezgah", True):
        _rect(ctx, sx(0.58), sy(0.62), PW * 0.40, PH * 0.18, (0.28, 0.19, 0.13), FRAME, 4)
        _rect(ctx, sx(0.56), sy(0.60), PW * 0.44, 22, (0.36, 0.25, 0.17), FRAME, 3)


def _window_view(ctx, t, sc):
    # içeriden pencereye bakış: koyu duvar, ortada büyük pencere, dışarısı sis
    _rect(ctx, PX, PY, PW, PH, (0.09, 0.10, 0.13))
    wx, wy, ww, wh = sx(0.14), sy(0.12), PW * 0.72, PH * 0.62
    g = cairo.LinearGradient(0, wy, 0, wy + wh)
    g.add_color_stop_rgb(0, 0.30, 0.33, 0.40)
    g.add_color_stop_rgb(1, 0.45, 0.47, 0.52)
    ctx.set_source(g)
    ctx.rectangle(wx, wy, ww, wh)
    ctx.fill()
    ctx.set_source_rgb(*FRAME)
    ctx.set_line_width(14)
    ctx.rectangle(wx, wy, ww, wh)
    ctx.stroke()
    ctx.set_line_width(8)
    ctx.move_to(wx + ww / 2, wy)
    ctx.line_to(wx + ww / 2, wy + wh)
    ctx.stroke()
    _rect(ctx, wx - 30, wy + wh, ww + 60, 24, (0.20, 0.16, 0.12), FRAME, 3)
    _rect(ctx, PX, sy(0.86), PW, PH * 0.14, (0.08, 0.07, 0.07))
    sil = sc.get("golge")
    if sil:  # siste uzak, belirsiz bir insan siluti (asla net görünmez, hafifçe salınır)
        x = wx + ww * sil.get("x", 0.7) + 6 * math.sin(t * 0.6)
        k = 0.55 + 0.15 * math.sin(t * 0.8)
        hy = wy + wh * 0.40
        ctx.set_source_rgba(0.06, 0.07, 0.09, k)
        ctx.arc(x, hy, 20, 0, 2 * math.pi)
        ctx.fill()
        ctx.move_to(x - 14, hy + 22)
        ctx.curve_to(x - 40, hy + 34, x - 44, hy + 70, x - 36, wy + wh)
        ctx.line_to(x + 36, wy + wh)
        ctx.curve_to(x + 44, hy + 70, x + 40, hy + 34, x + 14, hy + 22)
        ctx.close_path()
        ctx.fill()


# --------------------------------------------------------------------------
# Nesneler
# --------------------------------------------------------------------------
def draw_prop(ctx, p, st, ink=INK):
    tp = p["type"]
    x, y = sx(p.get("x", 0.5)), sy(p.get("y", 0.5))
    s = p.get("scale", 1.0)
    if tp == "saat":
        r = 95 * s
        _rect(ctx, x - r * 1.3, y - r * 0.8, r * 2.6, r * 1.6, (0.06, 0.06, 0.07), FRAME, 5)
        blink = 1.0 if (st % 1.0) < 0.6 or p.get("sabit") else 0.25
        txt = p.get("text", "16:44")
        set_font(ctx, CAPTION_FONT, int(r * 0.95), bold=True)
        tw = text_width(ctx, txt)
        _glow(ctx, x, y, r * 1.5, RED, 0.22 * blink)
        ctx.set_source_rgba(*RED, blink)
        ctx.move_to(x - tw / 2, y + r * 0.33)
        ctx.show_text(txt)
    elif tp == "lamba":
        _streetlamp(ctx, x, y, st)
    elif tp == "liste":
        w, h = 230 * s, 300 * s
        _rect(ctx, x - w / 2, y - h / 2, w, h, (0.82, 0.78, 0.66), (0.35, 0.25, 0.15), 8)
        _text(ctx, "1987", x, y - h / 2 + 30 * s, CAPTION_FONT, int(30 * s), (0.25, 0.18, 0.12))
        n = p.get("satir", 12)
        for i in range(n):
            yy = y - h / 2 + (62 + i * 19) * s
            ctx.set_source_rgba(0.25, 0.20, 0.15, 0.8)
            ctx.set_line_width(3)
            ctx.move_to(x - w / 2 + 22 * s, yy)
            ctx.line_to(x + w / 2 - (22 + (i * 37 % 60)) * s, yy)
            ctx.stroke()
        for i in p.get("cizik", []):
            yy = y - h / 2 + (62 + i * 19) * s
            ctx.set_source_rgba(*RED, 0.95)
            ctx.set_line_width(5)
            ctx.move_to(x - w / 2 + 14 * s, yy - 2)
            ctx.line_to(x + w / 2 - 14 * s, yy + 2)
            ctx.stroke()
    elif tp == "bardak":
        n = p.get("adet", 9)
        k = min(n, max(0, int((st - p.get("delay", 0)) / p.get("aralik", 0.0001)) + 1)) if p.get("aralik") else n
        gap = 52 * s
        x0 = x - (n - 1) * gap / 2
        for i in range(k):
            bx = x0 + i * gap
            ctx.move_to(bx - 15 * s, y - 50 * s)
            ctx.curve_to(bx - 9 * s, y - 28 * s, bx - 17 * s, y - 10 * s, bx - 11 * s, y)
            ctx.line_to(bx + 11 * s, y)
            ctx.curve_to(bx + 17 * s, y - 10 * s, bx + 9 * s, y - 28 * s, bx + 15 * s, y - 50 * s)
            ctx.close_path()
            ctx.set_source_rgba(0.62, 0.22, 0.10, 0.9)
            ctx.fill_preserve()
            ctx.set_source_rgba(1, 1, 1, 0.7)
            ctx.set_line_width(2.5)
            ctx.stroke()
            ctx.set_source_rgba(0.9, 0.9, 0.95, 0.5)
            ctx.rectangle(bx - 20 * s, y, 40 * s, 5 * s)
            ctx.fill()
            if i == n - 1 and p.get("fazla"):
                _glow(ctx, bx, y - 25 * s, 45 * s, RED, 0.3 + 0.2 * math.sin(st * 4))
    elif tp == "telefon":
        w, h = 120 * s, 220 * s
        ctx.save()
        ctx.translate(x, y)
        rot = p.get("rot", -8) + (3.5 * math.sin(st * 45) if p.get("titre") and (st % 1.4) < 0.9 else 0)
        if p.get("titre"):
            _glow(ctx, 0, 0, w * 1.6, (0.55, 0.65, 1.0), 0.18 + 0.1 * math.sin(st * 6))
        ctx.rotate(math.radians(rot))
        _rect(ctx, -w / 2, -h / 2, w, h, (0.05, 0.05, 0.06), (0.6, 0.6, 0.65), 4)
        _rect(ctx, -w / 2 + 8, -h / 2 + 16, w - 16, h - 32, (0.12, 0.16, 0.24))
        _text(ctx, p.get("text", "16:44"), 0, -h / 2 + 60 * s, CAPTION_FONT, int(30 * s), (0.95, 0.95, 1.0))
        _text(ctx, p.get("alt", "Şebeke yok"), 0, -h / 2 + 110 * s, CAPTION_FONT, int(16 * s), (0.95, 0.6, 0.55))
        ctx.restore()
    elif tp == "mont":
        _bench(ctx, x, y) if p.get("bank", True) else None
        ctx.move_to(x - 70 * s, y - 80 * s)
        ctx.line_to(x + 70 * s, y - 80 * s)
        ctx.line_to(x + 60 * s, y - 118 * s)
        ctx.line_to(x - 60 * s, y - 118 * s)
        ctx.close_path()
        ctx.set_source_rgb(0.20, 0.30, 0.50)
        ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.5)
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.move_to(x - 58 * s, y - 100 * s)
        ctx.line_to(x + 58 * s, y - 100 * s)
        ctx.stroke()
    elif tp == "tabela":
        w, h = 330 * s, 130 * s
        ctx.set_source_rgb(*FRAME)
        ctx.set_line_width(10 * s)
        ctx.move_to(x, y)
        ctx.line_to(x, y - 260 * s)
        ctx.stroke()
        bx, by = x - w / 2, y - 260 * s - h
        _rect(ctx, bx, by, w, h, (0.08, 0.32, 0.20), (0.92, 0.92, 0.92), 5)
        lines = p.get("text", "SON MOLA|0 KM").split("|")
        for i, ln in enumerate(lines):
            _text(ctx, ln, x, by + h * (i + 1) / (len(lines) + 1), CAPTION_FONT, int(40 * s), (0.97, 0.97, 0.97))
        if p.get("ok", "sag"):
            d = 1 if p.get("ok", "sag") == "sag" else -1
            ax = x + d * (w / 2 + 6)
            ctx.move_to(ax, by + h / 2 - 30 * s)
            ctx.line_to(ax + d * 40 * s, by + h / 2)
            ctx.line_to(ax, by + h / 2 + 30 * s)
            ctx.close_path()
            ctx.set_source_rgb(0.08, 0.32, 0.20)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.92, 0.92, 0.92)
            ctx.set_line_width(4)
            ctx.stroke()
    elif tp == "fener":
        # elde fener ışığı: (x,y) kaynaktan "dx" yönüne koni
        d = p.get("dx", 1)
        fl = _flicker(st, 5)
        ctx.set_source_rgba(1.0, 0.95, 0.75, 0.16 * fl)
        ctx.move_to(x, y)
        ctx.line_to(x + d * 520 * s, y - 160 * s)
        ctx.line_to(x + d * 520 * s, y + 200 * s)
        ctx.close_path()
        ctx.fill()
        _glow(ctx, x, y, 40, (1.0, 0.95, 0.75), 0.6)
    elif tp == "kapi":
        w, h = 200 * s, 360 * s
        _rect(ctx, x - w / 2, y - h, w, h, (0.08, 0.08, 0.10), FRAME, 6)
        if p.get("aralik"):
            _glow(ctx, x, y - h / 2, 200 * s, (0.75, 0.78, 0.85), 0.18)
            _rect(ctx, x - w / 2 + 6, y - h + 6, 30 * s, h - 12, (0.55, 0.58, 0.65))
        ctx.set_source_rgb(*LAMP)
        ctx.arc(x + w / 2 - 26 * s, y - h / 2, 6 * s, 0, 2 * math.pi)
        ctx.fill()
    elif tp == "defter":
        _rect(ctx, x - 70 * s, y - 90 * s, 140 * s, 180 * s, (0.55, 0.15, 0.12), (0.9, 0.85, 0.8), 3)
        for i in range(5):
            ctx.set_source_rgba(1, 1, 1, 0.3)
            ctx.rectangle(x - 50 * s, y - 60 * s + i * 25 * s, 100 * s, 3)
            ctx.fill()
    elif tp == "resim":
        w, h = 260 * s, 200 * s
        _rect(ctx, x - w / 2, y - h / 2, w, h, (0.95, 0.94, 0.90), (0.5, 0.5, 0.5), 3)
        ctx.set_source_rgba(0.2, 0.2, 0.25, 0.8)
        ctx.set_line_width(4)
        cx, cy = x + w * 0.15, y + h * 0.1
        ctx.arc(cx, cy - 50 * s, 13 * s, 0, 2 * math.pi)
        ctx.stroke()
        for a, b in (((cx, cy - 37 * s), (cx, cy + 10 * s)), ((cx, cy + 10 * s), (cx - 15 * s, cy + 45 * s)),
                     ((cx, cy + 10 * s), (cx + 15 * s, cy + 45 * s)), ((cx, cy - 25 * s), (cx - 20 * s, cy))):
            ctx.move_to(*a)
            ctx.line_to(*b)
            ctx.stroke()
        for i in range(6):  # karalanmış sis
            ctx.set_source_rgba(0.5, 0.52, 0.6, 0.5)
            ctx.arc(x - w * 0.3 + i * 30 * s, y + h * 0.3, 26 * s, 0, 2 * math.pi)
            ctx.fill()
    elif tp == "far":
        k = min(1, max(0, (st - p.get("delay", 0)) / 2.0))
        for dx in (-70, 70):
            _glow(ctx, x + dx * s, y, 160 * s * k + 1, (1.0, 0.97, 0.85), 0.55 * k)
            ctx.set_source_rgba(1, 1, 0.95, k)
            ctx.arc(x + dx * s, y, 16 * s, 0, 2 * math.pi)
            ctx.fill()


# --------------------------------------------------------------------------
# Hareketli sis (panelin üstüne, numpy ile)
# --------------------------------------------------------------------------
class Fog:
    def __init__(self, seed=3):
        rng = np.random.default_rng(seed)
        h, w = PH, PW
        fy = np.fft.fftfreq(h)[:, None]
        fx = np.fft.fftfreq(w)[None, :]
        acc = np.zeros((h, w), np.float32)
        for sigma, wgt in ((14, 0.45), (40, 0.35), (95, 0.20)):   # yatayda/dikeyde dikişsiz (periyodik) bulanık gürültü
            n = rng.random((h, w)).astype(np.float32)
            g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
            b = np.real(np.fft.ifft2(np.fft.fft2(n) * g)).astype(np.float32)
            b = (b - b.mean()) / (b.std() + 1e-6)
            acc += b * wgt
        acc = np.clip(0.5 + acc * 0.32, 0, 1)
        acc = np.clip((acc - 0.35) * 2.0, 0, 1)
        self.tex = np.concatenate([acc, acc], axis=1)
        self.col = np.array([0.72, 0.74, 0.80], np.float32) * 255

    def apply(self, surf, t, k, low=0.45):
        """k: yoğunluk 0..1. low: sisin yoğunlaştığı yükseklik (0 üst, 1 alt; altta daha yoğun)."""
        if k <= 0:
            return
        surf.flush()
        buf = np.ndarray((H, W, 4), np.uint8, surf.get_data())
        reg = buf[PY:PY + PH, PX:PX + PW, :3]
        off = int((t * 26) % PW)
        a = self.tex[:, off:off + PW]
        off2 = int((t * 11 + PW / 2) % PW)
        a = 0.6 * a + 0.4 * self.tex[::-1, off2:off2 + PW]
        yy = np.linspace(0, 1, PH, dtype=np.float32)[:, None]
        band = np.clip((yy - low * 0.6) / 0.5, 0.15, 1.0)
        alpha = (a * band * k)[..., None]
        reg[:] = (reg * (1 - alpha) + self.col[::-1] * alpha).astype(np.uint8)   # BGR
        surf.mark_dirty()


# --------------------------------------------------------------------------
# Gerilim müziği (sentetik, telifsiz)
# --------------------------------------------------------------------------
def drone(seconds, sr, seed=4, sting_at=None):
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    t = np.arange(n) / sr
    out = np.zeros(n, np.float32)
    # derin uğultu: iki yakın frekans (vuru) + alt oktav
    for f, a in ((55.0, 0.5), (55.7, 0.4), (27.5, 0.35), (82.4, 0.12), (116.5, 0.06)):
        lfo = 0.7 + 0.3 * np.sin(2 * np.pi * rng.uniform(0.03, 0.09) * t + rng.uniform(0, 6))
        out += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * lfo
    # rüzgâr: süzülmüş gürültü
    noise = rng.normal(0, 1, n).astype(np.float32)
    k = int(sr * 0.004)
    wind = np.convolve(noise, np.ones(k) / k, mode="same")
    wind *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t) ** 2
    out += wind * 0.6
    # ara sıra uzak metalik tını
    for _ in range(max(1, int(seconds / 14))):
        s = rng.uniform(2, max(3, seconds - 4))
        i0 = int(s * sr)
        d = np.arange(int(sr * 3.5)) / sr
        ping = 0.12 * np.sin(2 * np.pi * rng.choice([311.1, 349.2, 415.3]) * d) * np.exp(-d * 1.4)
        out[i0:i0 + len(ping)] += ping[: max(0, n - i0)]
    if sting_at is not None:  # uçurumda: ani yükselen gerilim + kesik
        i0 = int(sting_at * sr)
        d = np.arange(int(sr * 2.2)) / sr
        sweep = np.sin(2 * np.pi * (80 + 300 * d ** 2) * d) * (d / 2.2) ** 2 * 0.6
        hit = np.zeros_like(d)
        hit[-int(sr * 0.25):] = rng.normal(0, 1, int(sr * 0.25)) * np.exp(-np.arange(int(sr * 0.25)) / (sr * 0.05))
        seg = (sweep + hit * 0.7).astype(np.float32)
        out[i0:i0 + len(seg)] += seg[: max(0, n - i0)]
    fade = np.minimum(1, t / 2.0)
    out *= fade
    return out / (np.abs(out).max() + 1e-6)


# --------------------------------------------------------------------------
# Kapanış kartı
# --------------------------------------------------------------------------
def draw_end_card(ctx, k, next_no, saat="21:30"):
    """k: 0..1 kartın görünme oranı."""
    ctx.set_source_rgba(0, 0, 0, min(1, k * 1.5))
    ctx.rectangle(0, 0, W, H)
    ctx.fill()
    if k < 0.25:
        return
    a = min(1, (k - 0.25) / 0.3)
    _text(ctx, f"BÖLÜM {next_no}", W / 2, H * 0.42, CAPTION_FONT, 96, (0.95, 0.95, 0.98), a)
    _glow(ctx, W / 2, H * 0.52, 260, RED, 0.25 * a)
    _text(ctx, f"YARIN {saat}", W / 2, H * 0.52, CAPTION_FONT, 76, RED, a)
    _text(ctx, "@sonmola.dizi", W / 2, H * 0.64, HAND_FONT, 52, (0.75, 0.77, 0.85), a * 0.85)


def draw_title_overlay(ctx, ep, k):
    """Bölümün ilk ~1.6 sn'si: panelin üstünde 'SON MOLA · BÖLÜM N' rozeti."""
    if k <= 0:
        return
    _text(ctx, f"BÖLÜM {int(ep['id'])}", sx(0.5), sy(0.06), CAPTION_FONT, 40, (0.95, 0.95, 0.98), k)
