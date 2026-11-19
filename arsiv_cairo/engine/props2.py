"""Genişletilmiş çizim kütüphanesi: yeni şapkalar, elde tutulan eşyalar,
aksesuarlar ve arka planlar. Hepsi kodla çizilir (telifsiz)."""
import math
import random

import cairo

from .draw import (INK_DAY, RED, GOLD, WOOD, STONE, WHITE, YELLOW, PX, PY, PW, PH,
                   sx, sy, stroke_fill, line, set_font, text_width, HAND_FONT)

SAND = (0.94, 0.82, 0.55)
SAND_DARK = (0.85, 0.70, 0.42)
BLUE = (0.20, 0.35, 0.70)
GREEN = (0.30, 0.60, 0.30)
BROWN = (0.45, 0.30, 0.18)
FUR = (0.55, 0.40, 0.25)


# --------------------------------------------------------------------------
# Şapkalar
# --------------------------------------------------------------------------

def draw_hat2(ctx, head, r, f, hat, ink, lw, t):
    """draw.draw_hat'in tanımadığı şapkalar. Çizildiyse True döner."""
    cx, cy = head
    lw2 = lw * 0.7
    if hat == "bicorne":  # Napolyon şapkası
        ctx.move_to(cx - r * 1.6, cy - r * 0.55)
        ctx.curve_to(cx - r * 1.0, cy - r * 1.7, cx + r * 1.0, cy - r * 1.7, cx + r * 1.6, cy - r * 0.55)
        ctx.curve_to(cx + r * 0.8, cy - r * 0.85, cx - r * 0.8, cy - r * 0.85, cx - r * 1.6, cy - r * 0.55)
        stroke_fill(ctx, (0.12, 0.12, 0.15), ink, lw2)
        ctx.arc(cx + f * r * 0.1, cy - r * 1.05, r * 0.2, 0, 2 * math.pi)
        stroke_fill(ctx, RED, ink, lw * 0.3)
        ctx.arc(cx + f * r * 0.1, cy - r * 1.05, r * 0.1, 0, 2 * math.pi)
        stroke_fill(ctx, BLUE, ink, lw * 0.2)
        return True
    if hat == "nemes":  # Firavun başlığı
        ctx.move_to(cx - r * 1.05, cy - r * 0.2)
        ctx.curve_to(cx - r * 1.1, cy - r * 1.3, cx + r * 1.1, cy - r * 1.3, cx + r * 1.05, cy - r * 0.2)
        ctx.line_to(cx + r * 1.25, cy + r * 1.1)
        ctx.line_to(cx + r * 0.75, cy + r * 1.1)
        ctx.line_to(cx + r * 0.75, cy - r * 0.35)
        ctx.line_to(cx - r * 0.75, cy - r * 0.35)
        ctx.line_to(cx - r * 0.75, cy + r * 1.1)
        ctx.line_to(cx - r * 1.25, cy + r * 1.1)
        ctx.close_path()
        stroke_fill(ctx, GOLD, ink, lw2)
        for k in range(4):
            yy = cy - r * 0.05 + k * r * 0.3
            line(ctx, (cx - r * 1.15, yy), (cx - r * 0.8, yy), BLUE, lw * 0.5)
            line(ctx, (cx + r * 0.8, yy), (cx + r * 1.15, yy), BLUE, lw * 0.5)
        ctx.arc(cx, cy - r * 0.9, r * 0.15, 0, 2 * math.pi)
        stroke_fill(ctx, RED, ink, lw * 0.3)
        return True
    if hat == "selcuk":  # Selçuklu kürklü börk + tüy
        ctx.rectangle(cx - r * 0.95, cy - r * 0.95, r * 1.9, r * 0.38)
        stroke_fill(ctx, FUR, ink, lw2)
        ctx.move_to(cx - r * 0.75, cy - r * 0.95)
        ctx.curve_to(cx - r * 0.7, cy - r * 1.8, cx + r * 0.7, cy - r * 1.8, cx + r * 0.75, cy - r * 0.95)
        ctx.close_path()
        stroke_fill(ctx, RED, ink, lw2)
        ctx.move_to(cx - f * r * 0.2, cy - r * 1.55)
        ctx.curve_to(cx - f * r * 0.6, cy - r * 2.4, cx - f * r * 1.1, cy - r * 2.3, cx - f * r * 1.2, cy - r * 2.0)
        ctx.curve_to(cx - f * r * 0.9, cy - r * 2.0, cx - f * r * 0.5, cy - r * 1.9, cx - f * r * 0.2, cy - r * 1.55)
        stroke_fill(ctx, WHITE, ink, lw * 0.35)
        return True
    if hat == "slouch":  # Avustralya asker şapkası
        ctx.save()
        ctx.translate(cx, cy - r * 0.6)
        ctx.scale(r * 1.6, r * 0.28)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, (0.62, 0.55, 0.38), ink, lw2)
        ctx.move_to(cx - r * 0.75, cy - r * 0.62)
        ctx.curve_to(cx - r * 0.7, cy - r * 1.55, cx + r * 0.7, cy - r * 1.55, cx + r * 0.75, cy - r * 0.62)
        ctx.close_path()
        stroke_fill(ctx, (0.62, 0.55, 0.38), ink, lw2)
        ctx.rectangle(cx - r * 0.75, cy - r * 0.85, r * 1.5, r * 0.18)
        stroke_fill(ctx, BROWN, ink, lw * 0.3)
        return True
    if hat == "greek":  # Antik Yunan miğferi (Korint) + at kılı sorguç
        ctx.arc(cx, cy - r * 0.05, r * 1.08, math.pi * 0.95, math.pi * 2.05)
        ctx.close_path()
        stroke_fill(ctx, (0.78, 0.60, 0.25), ink, lw2)
        ctx.move_to(cx - r * 0.9, cy - r * 0.95)
        ctx.curve_to(cx - r * 0.5, cy - r * 2.1, cx + r * 0.5, cy - r * 2.1, cx + r * 0.9, cy - r * 0.95)
        ctx.curve_to(cx + r * 0.5, cy - r * 1.4, cx - r * 0.5, cy - r * 1.4, cx - r * 0.9, cy - r * 0.95)
        stroke_fill(ctx, RED, ink, lw * 0.45)
        return True
    if hat == "fez":
        ctx.move_to(cx - r * 0.55, cy - r * 0.8)
        ctx.line_to(cx - r * 0.42, cy - r * 1.6)
        ctx.line_to(cx + r * 0.42, cy - r * 1.6)
        ctx.line_to(cx + r * 0.55, cy - r * 0.8)
        ctx.close_path()
        stroke_fill(ctx, RED, ink, lw2)
        ctx.move_to(cx, cy - r * 1.6)
        ctx.curve_to(cx - f * r * 0.4, cy - r * 1.5, cx - f * r * 0.6, cy - r * 1.2, cx - f * r * 0.6, cy - r * 0.9)
        ctx.set_source_rgb(*INK_DAY)
        ctx.set_line_width(lw * 0.35)
        ctx.stroke()
        return True
    if hat == "tophat":  # silindir şapka (İngiliz)
        ctx.rectangle(cx - r * 1.3, cy - r * 0.85, r * 2.6, r * 0.2)
        stroke_fill(ctx, (0.12, 0.12, 0.15), ink, lw2)
        ctx.rectangle(cx - r * 0.75, cy - r * 2.0, r * 1.5, r * 1.2)
        stroke_fill(ctx, (0.12, 0.12, 0.15), ink, lw2)
        ctx.rectangle(cx - r * 0.75, cy - r * 1.1, r * 1.5, r * 0.18)
        stroke_fill(ctx, RED, ink, lw * 0.3)
        return True
    if hat == "kavuk":  # IV. Murad tarzı büyük padişah kavuğu + sorguç
        ctx.save()
        ctx.translate(cx, cy - r * 1.15)
        ctx.scale(r * 1.0, r * 1.05)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, WHITE, ink, lw2)
        for k in (-0.5, 0.0, 0.5):
            ctx.move_to(cx - r * 0.9, cy - r * 1.15 + k * r)
            ctx.curve_to(cx - r * 0.3, cy - r * 0.95 + k * r, cx + r * 0.3, cy - r * 1.35 + k * r, cx + r * 0.9, cy - r * 1.15 + k * r)
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(lw * 0.3)
            ctx.stroke()
        ctx.arc(cx + f * r * 0.2, cy - r * 1.55, r * 0.17, 0, 2 * math.pi)
        stroke_fill(ctx, (0.2, 0.7, 0.4), ink, lw * 0.3)
        ctx.move_to(cx + f * r * 0.2, cy - r * 1.7)
        ctx.curve_to(cx + f * r * 0.1, cy - r * 2.5, cx + f * r * 0.6, cy - r * 2.6, cx + f * r * 0.5, cy - r * 2.2)
        ctx.curve_to(cx + f * r * 0.45, cy - r * 2.0, cx + f * r * 0.35, cy - r * 1.8, cx + f * r * 0.2, cy - r * 1.7)
        stroke_fill(ctx, WHITE, ink, lw * 0.3)
        return True
    return False


# --------------------------------------------------------------------------
# Elde tutulan eşyalar
# --------------------------------------------------------------------------

def draw_held(ctx, item, hand, f, scale, t):
    hx, hy = hand
    s = scale
    if item == "sword":
        ctx.save()
        ctx.translate(hx, hy)
        ctx.rotate(f * math.radians(-35 + 8 * math.sin(t * 4)))
        line(ctx, (0, 0), (0, -150 * s), (0.75, 0.78, 0.82), 12 * s)
        line(ctx, (0, 0), (0, -150 * s), INK_DAY, 3 * s)
        line(ctx, (-24 * s, -10 * s), (24 * s, -10 * s), GOLD, 10 * s)
        ctx.restore()
    elif item == "mug":  # bira testisi
        ctx.rectangle(hx - 4 * s, hy - 52 * s, 44 * s, 56 * s)
        stroke_fill(ctx, (0.95, 0.70, 0.20), INK_DAY, 5 * s)
        ctx.rectangle(hx - 6 * s, hy - 64 * s, 48 * s, 16 * s)
        stroke_fill(ctx, WHITE, INK_DAY, 4 * s)
    elif item == "cup":  # kahve fincanı + buhar
        ctx.move_to(hx - 22 * s, hy - 30 * s)
        ctx.line_to(hx + 22 * s, hy - 30 * s)
        ctx.curve_to(hx + 20 * s, hy, hx - 20 * s, hy, hx - 22 * s, hy - 30 * s)
        stroke_fill(ctx, WHITE, INK_DAY, 5 * s)
        for k in (-8, 8):
            ctx.move_to(hx + k * s, hy - 38 * s)
            ctx.curve_to(hx + (k - 10) * s, hy - (55 + 5 * math.sin(t * 4)) * s, hx + (k + 10) * s,
                         hy - 70 * s, hx + k * s, hy - 88 * s)
            ctx.set_source_rgba(0.5, 0.5, 0.5, 0.7)
            ctx.set_line_width(4 * s)
            ctx.stroke()
    elif item == "scroll":
        ctx.rectangle(hx - 10 * s, hy - 70 * s, 70 * s, 90 * s)
        stroke_fill(ctx, (0.98, 0.93, 0.78), INK_DAY, 5 * s)
        for k in range(4):
            line(ctx, (hx, hy - 50 * s + k * 18 * s), (hx + 50 * s, hy - 50 * s + k * 18 * s), INK_DAY, 2.5 * s)
    elif item == "torch":
        line(ctx, (hx, hy + 20 * s), (hx, hy - 60 * s), WOOD, 10 * s)
        fl = 1 + 0.15 * math.sin(t * 15)
        ctx.move_to(hx, hy - 120 * s * fl)
        ctx.curve_to(hx + 30 * s, hy - 80 * s, hx + 20 * s, hy - 55 * s, hx, hy - 55 * s)
        ctx.curve_to(hx - 20 * s, hy - 55 * s, hx - 30 * s, hy - 80 * s, hx, hy - 120 * s * fl)
        stroke_fill(ctx, (1.0, 0.55, 0.15), INK_DAY, 4 * s)


# --------------------------------------------------------------------------
# Aksesuarlar (sahne nesneleri)
# --------------------------------------------------------------------------

def draw_pyramid(ctx, x, y, size, progress=1.0):
    """x,y taban ortası (piksel). progress<1 ise yarım (inşaat hâlinde)."""
    w = size
    h = size * 0.62
    top = y - h * progress
    half_top = w / 2 * (1 - progress)
    ctx.move_to(x - w / 2, y)
    ctx.line_to(x - half_top, top)
    ctx.line_to(x + half_top, top)
    ctx.line_to(x + w / 2, y)
    ctx.close_path()
    stroke_fill(ctx, SAND, INK_DAY, 7)
    rows = 9
    for i in range(1, rows):
        yy = y - h * i / rows
        if yy < top:
            break
        hw = w / 2 * (1 - i / rows)
        line(ctx, (x - hw, yy), (x + hw, yy), SAND_DARK, 3)
    ctx.move_to(x + half_top, top)
    ctx.line_to(x + w / 2, y)
    ctx.line_to(x + w * 0.18, y)
    ctx.line_to(x + max(half_top, 1) * 0.2, top)
    ctx.close_path()
    ctx.set_source_rgba(0, 0, 0, 0.08)
    ctx.fill()


def draw_block(ctx, x, y, s=1.0):
    ctx.rectangle(x - 45 * s, y - 50 * s, 90 * s, 50 * s)
    stroke_fill(ctx, SAND, INK_DAY, 5 * s)
    line(ctx, (x - 45 * s, y - 25 * s), (x + 45 * s, y - 25 * s), SAND_DARK, 2)


def draw_palm(ctx, x, y, s=1.0, t=0):
    ctx.move_to(x, y)
    ctx.curve_to(x + 10 * s, y - 100 * s, x - 10 * s, y - 180 * s, x + 15 * s, y - 260 * s)
    ctx.set_source_rgb(*BROWN)
    ctx.set_line_width(18 * s)
    ctx.stroke()
    tx, ty = x + 15 * s, y - 260 * s
    for k in range(6):
        a = -math.pi / 2 + (k - 2.5) * 0.55 + 0.05 * math.sin(t * 2 + k)
        ex, ey = tx + math.cos(a) * 120 * s, ty + math.sin(a) * 60 * s + 40 * s
        ctx.move_to(tx, ty)
        ctx.curve_to(tx + math.cos(a) * 60 * s, ty + math.sin(a) * 80 * s - 20 * s, ex, ey - 20 * s, ex, ey)
        ctx.set_source_rgb(*GREEN)
        ctx.set_line_width(14 * s)
        ctx.stroke()


def draw_horse(ctx, x, y, s=1.0, f=1, t=0, gallop=False, wooden=False):
    """Çöp at. x,y toynak hizası ortası."""
    col = WOOD if wooden else (0.55, 0.35, 0.20)
    lw = 10 * s
    bob = abs(math.sin(t * 8)) * 10 * s if gallop else 0
    body_y = y - 120 * s - bob
    # bacaklar
    for i, bx in enumerate((-60, -35, 40, 65)):
        swing = (math.sin(t * 8 + i * 1.6) * 25 if gallop else 0)
        a = math.radians(swing)
        top = (x + f * bx * s, body_y + 15 * s)
        foot = (top[0] + f * math.sin(a) * 105 * s, top[1] + math.cos(a) * 105 * s)
        line(ctx, top, foot, INK_DAY if not wooden else BROWN, lw)
    # gövde
    ctx.save()
    ctx.translate(x, body_y)
    ctx.scale(95 * s, 38 * s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    stroke_fill(ctx, col, INK_DAY, lw * 0.7)
    # boyun + kafa
    nx, ny = x + f * 75 * s, body_y - 15 * s
    hx, hy = x + f * 125 * s, body_y - 95 * s
    line(ctx, (nx, ny), (hx - f * 10 * s, hy + 15 * s), col, 34 * s)
    ctx.save()
    ctx.translate(hx + f * 15 * s, hy)
    ctx.rotate(f * 0.5)
    ctx.scale(42 * s, 22 * s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    stroke_fill(ctx, col, INK_DAY, lw * 0.6)
    ctx.arc(hx + f * 8 * s, hy - 8 * s, 5 * s, 0, 2 * math.pi)
    ctx.set_source_rgb(*INK_DAY)
    ctx.fill()
    # yele + kuyruk
    for k in range(4):
        line(ctx, (nx + f * (k * 12 - 10) * s, ny - (k * 20 + 5) * s),
             (nx + f * (k * 12 - 30) * s, ny - (k * 20 - 5) * s), INK_DAY, 6 * s)
    tail = math.sin(t * 6) * 10 * s
    ctx.move_to(x - f * 95 * s, body_y - 5 * s)
    ctx.curve_to(x - f * 130 * s, body_y + tail, x - f * 130 * s, body_y + 40 * s, x - f * 120 * s, body_y + 70 * s)
    ctx.set_source_rgb(*INK_DAY)
    ctx.set_line_width(9 * s)
    ctx.stroke()
    if wooden:
        for k in (-40, 0, 40):
            line(ctx, (x + k * s, body_y - 35 * s), (x + k * s, body_y + 35 * s), BROWN, 3 * s)


def draw_trojan(ctx, x, y, s=1.0, t=0, roll=False, open_door=False):
    """Truva atı: tekerlekli dev tahta at. x,y tekerlek altı ortası."""
    plat_y = y - 40 * s
    ctx.rectangle(x - 170 * s, plat_y - 25 * s, 340 * s, 25 * s)
    stroke_fill(ctx, BROWN, INK_DAY, 7 * s)
    rot = t * 3 if roll else 0
    for wx in (-120, 120):
        cx, cy = x + wx * s, y - 25 * s
        ctx.arc(cx, cy, 30 * s, 0, 2 * math.pi)
        stroke_fill(ctx, WOOD, INK_DAY, 7 * s)
        for k in range(3):
            a = rot + k * math.pi / 3
            line(ctx, (cx - math.cos(a) * 28 * s, cy - math.sin(a) * 28 * s),
                 (cx + math.cos(a) * 28 * s, cy + math.sin(a) * 28 * s), INK_DAY, 4 * s)
    draw_horse(ctx, x - 10 * s, plat_y - 25 * s, 1.6 * s, 1, t, False, wooden=True)
    if open_door:
        ctx.rectangle(x - 40 * s, plat_y - 25 * s - 230 * s, 70 * s, 50 * s)
        stroke_fill(ctx, (0.15, 0.1, 0.05), INK_DAY, 5 * s)


def draw_tower(ctx, x, y, s=1.0, ink=INK_DAY):
    """Galata Kulesi: silindir gövde + konik çatı. x,y taban ortası."""
    w, h = 130 * s, 520 * s
    ctx.rectangle(x - w / 2, y - h, w, h)
    stroke_fill(ctx, STONE, ink, 7)
    for k in range(1, 7):
        line(ctx, (x - w / 2, y - h + k * h / 7), (x + w / 2, y - h + k * h / 7), (0.7, 0.64, 0.53), 3)
    for k in range(3):
        ctx.rectangle(x - 12 * s, y - h + 80 * s + k * 130 * s, 24 * s, 45 * s)
        stroke_fill(ctx, (0.25, 0.22, 0.2), ink, 3)
    ctx.rectangle(x - w / 2 - 12 * s, y - h - 20 * s, w + 24 * s, 24 * s)
    stroke_fill(ctx, STONE, ink, 6)
    ctx.move_to(x - w / 2 - 6 * s, y - h - 20 * s)
    ctx.line_to(x, y - h - 190 * s)
    ctx.line_to(x + w / 2 + 6 * s, y - h - 20 * s)
    ctx.close_path()
    stroke_fill(ctx, (0.35, 0.40, 0.50), ink, 6)


def draw_wings(ctx, shoulder, s, t, flap=True):
    a = math.sin(t * 10) * 0.35 if flap else 0.15
    for side in (-1, 1):
        ctx.save()
        ctx.translate(*shoulder)
        ctx.rotate(side * (0.3 + a))
        ctx.move_to(0, 0)
        ctx.curve_to(side * 60 * s, -80 * s, side * 170 * s, -70 * s, side * 210 * s, -20 * s)
        for k in range(4):
            ctx.line_to(side * (180 - k * 40) * s, (10 + k * 8) * s)
            ctx.line_to(side * (165 - k * 40) * s, (-5 + k * 6) * s)
        ctx.close_path()
        ctx.restore()
        stroke_fill(ctx, (0.97, 0.95, 0.90), INK_DAY, 5 * s)


def draw_emu(ctx, x, y, s=1.0, f=1, t=0, run=False):
    """Emu kuşu. x,y ayak hizası."""
    lw = 7 * s
    body_y = y - 110 * s - (abs(math.sin(t * 9)) * 8 * s if run else 0)
    for i in range(2):
        sw = math.sin(t * 9 + i * math.pi) * 30 if run else (-8 + 16 * i)
        a = math.radians(sw)
        hip = (x + f * (-5 + 10 * i) * s, body_y + 20 * s)
        knee = (hip[0] + f * math.sin(a) * 50 * s, hip[1] + math.cos(a) * 50 * s)
        foot = (knee[0] - f * 10 * s, y)
        ctx.move_to(*hip)
        ctx.line_to(*knee)
        ctx.line_to(*foot)
        ctx.set_source_rgb(*INK_DAY)
        ctx.set_line_width(lw)
        ctx.stroke()
        line(ctx, foot, (foot[0] + f * 22 * s, foot[1]), INK_DAY, lw)
    # tüylü gövde
    ctx.save()
    ctx.translate(x, body_y)
    ctx.scale(70 * s, 45 * s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    stroke_fill(ctx, (0.40, 0.33, 0.27), INK_DAY, lw)
    rnd = random.Random(5)
    for _ in range(14):
        px, py = x + rnd.uniform(-55, 45) * s, body_y + rnd.uniform(-30, 30) * s
        line(ctx, (px, py), (px - f * 14 * s, py + 10 * s), (0.25, 0.2, 0.16), 3 * s)
    # boyun
    nx, ny = x + f * 50 * s, body_y - 20 * s
    hx, hy = x + f * 75 * s, body_y - 120 * s + (math.sin(t * 9) * 6 * s if run else 0)
    ctx.move_to(nx, ny)
    ctx.curve_to(nx + f * 30 * s, ny - 40 * s, hx - f * 15 * s, hy + 50 * s, hx, hy)
    ctx.set_source_rgb(0.30, 0.45, 0.60)
    ctx.set_line_width(14 * s)
    ctx.stroke()
    ctx.arc(hx, hy, 18 * s, 0, 2 * math.pi)
    stroke_fill(ctx, (0.30, 0.45, 0.60), INK_DAY, lw * 0.6)
    ctx.move_to(hx + f * 14 * s, hy - 4 * s)
    ctx.line_to(hx + f * 40 * s, hy + 3 * s)
    ctx.line_to(hx + f * 14 * s, hy + 8 * s)
    ctx.close_path()
    stroke_fill(ctx, (0.25, 0.2, 0.15), INK_DAY, 3 * s)
    ctx.arc(hx + f * 4 * s, hy - 5 * s, 6 * s, 0, 2 * math.pi)
    stroke_fill(ctx, WHITE, INK_DAY, 2 * s)
    ctx.arc(hx + f * 6 * s, hy - 5 * s, 3 * s, 0, 2 * math.pi)
    ctx.set_source_rgb(*INK_DAY)
    ctx.fill()


def draw_tent(ctx, x, y, s=1.0, color=RED):
    ctx.move_to(x - 160 * s, y)
    ctx.line_to(x, y - 200 * s)
    ctx.line_to(x + 160 * s, y)
    ctx.close_path()
    stroke_fill(ctx, color, INK_DAY, 7)
    ctx.move_to(x - 40 * s, y)
    ctx.line_to(x, y - 110 * s)
    ctx.line_to(x + 40 * s, y)
    ctx.close_path()
    stroke_fill(ctx, (0.2, 0.1, 0.08), INK_DAY, 5)
    line(ctx, (x, y - 200 * s), (x, y - 250 * s), INK_DAY, 5)
    ctx.move_to(x, y - 250 * s)
    ctx.line_to(x + 40 * s, y - 238 * s)
    ctx.line_to(x, y - 226 * s)
    ctx.close_path()
    stroke_fill(ctx, YELLOW, INK_DAY, 3)


def draw_cezve(ctx, x, y, s=1.0, t=0):
    """Büyük kahve fincanı + buhar (yasak işareti için de kullanılır)."""
    ctx.move_to(x - 70 * s, y - 120 * s)
    ctx.line_to(x + 70 * s, y - 120 * s)
    ctx.curve_to(x + 65 * s, y - 10 * s, x - 65 * s, y - 10 * s, x - 70 * s, y - 120 * s)
    stroke_fill(ctx, WHITE, INK_DAY, 7 * s)
    ctx.save()
    ctx.translate(x, y - 120 * s)
    ctx.scale(70 * s, 14 * s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    stroke_fill(ctx, (0.35, 0.2, 0.1), INK_DAY, 5 * s)
    ctx.save()
    ctx.translate(x, y - 8 * s)
    ctx.scale(110 * s, 16 * s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    stroke_fill(ctx, WHITE, INK_DAY, 6 * s)
    for k in (-25, 5, 35):
        ctx.move_to(x + k * s, y - 140 * s)
        ctx.curve_to(x + (k - 25) * s, y - (175 + 8 * math.sin(t * 3 + k)) * s, x + (k + 25) * s,
                     y - 210 * s, x + k * s, y - 250 * s)
        ctx.set_source_rgba(0.45, 0.45, 0.45, 0.6)
        ctx.set_line_width(7 * s)
        ctx.stroke()


def draw_ban(ctx, x, y, r):
    """Yasak işareti (kırmızı daire + çizgi)."""
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*RED)
    ctx.set_line_width(r * 0.18)
    ctx.stroke()
    a = math.radians(45)
    line(ctx, (x - math.cos(a) * r * 0.9, y - math.sin(a) * r * 0.9),
         (x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9), RED, r * 0.18)


def draw_ruler(ctx, x, y_base, y_top, labels):
    """Boy ölçme cetveli. labels: [(oran 0..1, yazı)]"""
    ctx.rectangle(x - 30, y_top, 60, y_base - y_top)
    stroke_fill(ctx, (1.0, 0.92, 0.6), INK_DAY, 5)
    n = 20
    for i in range(n + 1):
        yy = y_base - (y_base - y_top) * i / n
        line(ctx, (x - 30, yy), (x - 30 + (30 if i % 5 == 0 else 15), yy), INK_DAY, 3)
    set_font(ctx, HAND_FONT, 52)
    for frac, txt in labels:
        yy = y_base - (y_base - y_top) * frac
        line(ctx, (x + 30, yy), (x + 60, yy), RED, 5)
        ctx.set_source_rgb(*RED)
        ctx.move_to(x + 68, yy + 12)
        ctx.show_text(txt)


def draw_fence(ctx, x1, x2, y, s=1.0):
    xx = x1
    while xx <= x2:
        ctx.rectangle(xx - 8 * s, y - 90 * s, 16 * s, 90 * s)
        stroke_fill(ctx, WOOD, INK_DAY, 4)
        xx += 70 * s
    for h in (30, 65):
        line(ctx, (x1, y - h * s), (x2, y - h * s), WOOD, 12 * s)
        line(ctx, (x1, y - h * s - 6 * s), (x2, y - h * s - 6 * s), INK_DAY, 2)


def draw_wheat(ctx, x, y, s=1.0, t=0):
    for k in range(5):
        bx = x + (k - 2) * 14 * s
        sway = math.sin(t * 2 + k) * 4 * s
        line(ctx, (bx, y), (bx + sway, y - 70 * s), (0.8, 0.65, 0.2), 4 * s)
        ctx.save()
        ctx.translate(bx + sway, y - 80 * s)
        ctx.scale(7 * s, 16 * s)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, (0.95, 0.80, 0.3), INK_DAY, 2)


def draw_label_sign(ctx, x, y, text, s=1.0):
    """Tahta tabela."""
    set_font(ctx, HAND_FONT, 46 * s)
    tw = text_width(ctx, text)
    line(ctx, (x, y), (x, y - 140 * s), WOOD, 12 * s)
    ctx.rectangle(x - tw / 2 - 20 * s, y - 210 * s, tw + 40 * s, 75 * s)
    stroke_fill(ctx, (0.85, 0.65, 0.40), INK_DAY, 5)
    ctx.set_source_rgb(*INK_DAY)
    ctx.move_to(x - tw / 2, y - 158 * s)
    ctx.show_text(text)


def draw_coin_bag(ctx, x, y, s=1.0):
    ctx.move_to(x - 50 * s, y)
    ctx.curve_to(x - 75 * s, y - 70 * s, x - 30 * s, y - 100 * s, x - 15 * s, y - 105 * s)
    ctx.line_to(x + 15 * s, y - 105 * s)
    ctx.curve_to(x + 30 * s, y - 100 * s, x + 75 * s, y - 70 * s, x + 50 * s, y)
    ctx.close_path()
    stroke_fill(ctx, (0.75, 0.6, 0.35), INK_DAY, 6 * s)
    line(ctx, (x - 20 * s, y - 100 * s), (x + 20 * s, y - 100 * s), BROWN, 8 * s)
    for dx, dy in ((-30, -118), (0, -128), (30, -116)):
        ctx.arc(x + dx * s, y + dy * s, 16 * s, 0, 2 * math.pi)
        stroke_fill(ctx, GOLD, INK_DAY, 3 * s)


# --------------------------------------------------------------------------
# Yeni arka planlar
# --------------------------------------------------------------------------

def draw_background2(ctx, bg, night, t):
    """draw.draw_background'ın üstüne ek zeminler. Çizdiyse True."""
    if bg == "desert":
        g = sy(0.86)
        ctx.move_to(PX, g)
        for i in range(0, 101):
            u = i / 100
            ctx.line_to(PX + u * PW, g + 18 * math.sin(u * 7 + 1))
        ctx.line_to(PX + PW, PY + PH)
        ctx.line_to(PX, PY + PH)
        ctx.close_path()
        stroke_fill(ctx, SAND, INK_DAY, 7)
        rnd = random.Random(2)
        for _ in range(10):
            xx, yy = sx(rnd.random()), sy(0.9 + rnd.random() * 0.08)
            ctx.move_to(xx, yy)
            ctx.curve_to(xx + 15, yy - 6, xx + 30, yy - 6, xx + 45, yy)
            ctx.set_source_rgb(*SAND_DARK)
            ctx.set_line_width(3)
            ctx.stroke()
        return True
    if bg == "farm":
        g = sy(0.90)
        ctx.rectangle(PX, g, PW, PY + PH - g)
        ctx.set_source_rgb(0.86, 0.80, 0.50)
        ctx.fill()
        line(ctx, (PX, g), (PX + PW, g), INK_DAY, 7)
        for k in range(9):
            draw_wheat(ctx, sx(0.05 + k * 0.115), g + 70, 0.9, t)
        return True
    if bg == "city":  # İstanbul silueti
        g = sy(0.93)
        base = sy(0.80)
        ctx.set_source_rgba(0.1, 0.1, 0.1, 0.13)
        for cxx, rr in ((0.12, 50), (0.30, 75), (0.52, 55), (0.70, 85), (0.88, 50)):
            ctx.rectangle(sx(cxx) - rr, base - rr * 0.7, rr * 2, rr * 0.7 + (g - base))
            ctx.fill()
            ctx.arc(sx(cxx), base - rr * 0.7, rr * 0.8, math.pi, 2 * math.pi)
            ctx.fill()
            for m in (-1.25, 1.25):
                ctx.rectangle(sx(cxx) + m * rr - 6, base - rr * 2.2, 12, rr * 2.2)
                ctx.fill()
        ctx.rectangle(PX, g, PW, PY + PH - g)
        ctx.set_source_rgb(0.80, 0.89, 0.66)
        ctx.fill()
        line(ctx, (PX, g), (PX + PW, g), INK_DAY, 7)
        return True
    if bg == "battlefield":
        g = sy(0.90)
        ctx.move_to(PX, g)
        for i in range(0, 101):
            u = i / 100
            ctx.line_to(PX + u * PW, g + 10 * math.sin(u * 5))
        ctx.line_to(PX + PW, PY + PH)
        ctx.line_to(PX, PY + PH)
        ctx.close_path()
        stroke_fill(ctx, (0.78, 0.82, 0.55), INK_DAY, 7)
        # uzakta dağlar
        ctx.move_to(PX, sy(0.62))
        for xx, yy in ((0.15, 0.45), (0.3, 0.60), (0.5, 0.40), (0.68, 0.58), (0.85, 0.47), (1.0, 0.6)):
            ctx.line_to(sx(xx), sy(yy))
        ctx.line_to(PX + PW, g)
        ctx.line_to(PX, g)
        ctx.close_path()
        ctx.set_source_rgba(0.45, 0.5, 0.6, 0.25)
        ctx.fill()
        return True
    if bg == "palace":  # saray içi
        ctx.rectangle(PX, PY, PW, PH)
        ctx.set_source_rgb(0.96, 0.90, 0.80)
        ctx.fill()
        for k in range(5):
            xx = sx(0.1 + k * 0.2)
            ctx.move_to(xx - 60, sy(0.75))
            ctx.line_to(xx - 60, sy(0.35))
            ctx.arc(xx, sy(0.35), 60, math.pi, 2 * math.pi)
            ctx.line_to(xx + 60, sy(0.75))
            stroke_fill(ctx, (0.75, 0.86, 0.92), INK_DAY, 5)
        g = sy(0.93)
        ctx.rectangle(PX, g, PW, PY + PH - g)
        ctx.set_source_rgb(0.70, 0.25, 0.22)
        ctx.fill()
        line(ctx, (PX, g), (PX + PW, g), INK_DAY, 7)
        for k in range(12):
            xx = sx(k / 11)
            line(ctx, (xx, g + 10), (xx + 20, g + 60), GOLD, 4)
        return True
    return False


def draw_sun_big(ctx, x, y, t):
    for i in range(12):
        a = i * math.pi / 6 + t * 0.3
        line(ctx, (x + math.cos(a) * 85, y + math.sin(a) * 85), (x + math.cos(a) * 120, y + math.sin(a) * 120),
             (1.0, 0.75, 0.2), 9)
    ctx.arc(x, y, 70, 0, 2 * math.pi)
    stroke_fill(ctx, (1.0, 0.85, 0.35), INK_DAY, 6)


# --------------------------------------------------------------------------
# Tek giriş noktası: sahne nesnesi çiz
# --------------------------------------------------------------------------

def draw_prop2(ctx, p, st, ink):
    """render.draw_scene'in bilmediği nesne türleri. Çizdiyse True."""
    tp = p["type"]
    k = st - p.get("delay", 0.0)
    if "delay" in p and k < 0 and tp not in ("pyramid",):
        return True  # henüz görünmüyor
    x, y = p.get("x", 0.5), p.get("y", 0.93)
    # Hareket: {"to_x": hedef} süre boyunca kayar
    if "to_x" in p:
        dur = p.get("move_dur", 3.0)
        u = max(0.0, min(1.0, (st - p.get("move_start", 0.0)) / dur))
        u = u * u * (3 - 2 * u)
        x = x + (p["to_x"] - x) * u
    s = p.get("scale", 1.0)
    f = -1 if p.get("flip") else 1
    if tp == "pyramid":
        prog = p.get("progress", 1.0)
        if "build" in p:  # zamanla yükselir
            prog = max(0.08, min(1.0, st / p["build"]))
        draw_pyramid(ctx, sx(x), sy(y), 420 * s, prog)
    elif tp == "block":
        draw_block(ctx, sx(x), sy(y), s)
    elif tp == "palm":
        draw_palm(ctx, sx(x), sy(y), s, st)
    elif tp == "horse":
        draw_horse(ctx, sx(x), sy(y), s, f, st, p.get("anim") == "gallop")
    elif tp == "trojan":
        draw_trojan(ctx, sx(x), sy(y), s, st, "to_x" in p, p.get("open", False))
    elif tp == "tower":
        draw_tower(ctx, sx(x), sy(y), s)
    elif tp == "emu":
        draw_emu(ctx, sx(x), sy(y), s, f, st, p.get("anim") == "run")
    elif tp == "tent":
        draw_tent(ctx, sx(x), sy(y), s)
    elif tp == "cezve":
        draw_cezve(ctx, sx(x), sy(y), s, st)
    elif tp == "ban":
        sc = min(1.0, max(0.0, k / 0.3)) if "delay" in p else 1.0
        draw_ban(ctx, sx(x), sy(y), 150 * s * sc)
    elif tp == "ruler":
        draw_ruler(ctx, sx(x), sy(p.get("y_base", 0.93)), sy(p.get("y_top", 0.25)),
                   [(a, b) for a, b in p.get("labels", [])])
    elif tp == "fence":
        draw_fence(ctx, sx(p.get("x1", 0.0)), sx(p.get("x2", 1.0)), sy(y), s)
    elif tp == "sign":
        draw_label_sign(ctx, sx(x), sy(y), p["text"], s)
    elif tp == "coins":
        draw_coin_bag(ctx, sx(x), sy(y), s)
    elif tp == "sun":
        draw_sun_big(ctx, sx(x), sy(y), st)
    else:
        return False
    return True


BACK_PROPS = {"pyramid", "palm", "tower", "tent", "fence", "trojan", "sun", "ruler", "sign"}
