"""Çöp Tarih - çizim kütüphanesi (pycairo).

Tüm çizimler kodla yapılır: çöp adamlar, şapkalar, aksesuarlar, arka planlar.
Sahne koordinatları 0..1 aralığındadır; panel içine ölçeklenir.
"""
import math
import random
import cairo

W, H = 1080, 1920
# Çizgi film paneli (sahnenin çizildiği kutu)
PX, PY, PW, PH = 40, 300, 1000, 1000

PAPER = (0.95, 0.91, 0.82)
PANEL_DAY = (1.0, 0.985, 0.95)
PANEL_NIGHT = (0.15, 0.20, 0.36)
INK_DAY = (0.10, 0.10, 0.11)
INK_NIGHT = (0.96, 0.93, 0.85)
RED = (0.84, 0.29, 0.20)
YELLOW = (1.0, 0.82, 0.25)
GOLD = (0.95, 0.76, 0.30)
WOOD = (0.63, 0.40, 0.23)
STONE = (0.85, 0.80, 0.69)
WATER_DAY = (0.55, 0.76, 0.90)
WATER_NIGHT = (0.13, 0.31, 0.50)
GRASS_DAY = (0.80, 0.89, 0.66)
GRASS_NIGHT = (0.22, 0.36, 0.30)
WHITE = (1, 1, 1)

TITLE_FONT = "Bangers"
HAND_FONT = "Patrick Hand"
CAPTION_FONT = "Poppins"


def sx(x):
    return PX + x * PW


def sy(y):
    return PY + y * PH


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def elastic(t):
    """Pop efekti için yaylanma (0 -> 1, hafif taşma)."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 1 + 2 ** (-10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3)


def hill_y(x):
    """Tepe eğrisi (sahne koordinatı)."""
    xx = max(0.0, min(1.0, x))
    return 0.96 - 0.44 * math.sin(math.pi * xx) ** 1.3


def hill_slope(x):
    e = 0.002
    return (hill_y(x + e) - hill_y(x - e)) / (2 * e)


# --------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------

def stroke_fill(ctx, fill, ink, lw):
    if fill is not None:
        ctx.set_source_rgb(*fill)
        ctx.fill_preserve()
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(lw)
    ctx.stroke()


def line(ctx, p1, p2, ink, lw):
    ctx.move_to(*p1)
    ctx.line_to(*p2)
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(lw)
    ctx.stroke()


def set_font(ctx, family, size, bold=False):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_width(ctx, s):
    return ctx.text_extents(s).x_advance


def tr_upper(s):
    """Türkçe büyük harf: i->İ, ı->I."""
    return s.replace("i", "İ").replace("ı", "I").upper()


def outlined_text(ctx, s, cx, cy, family, size, fill, ink, outline=10, rot=0.0, scale=1.0):
    if family == TITLE_FONT:
        s = tr_upper(s)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(math.radians(rot))
    ctx.scale(scale, scale)
    set_font(ctx, family, size)
    ext = ctx.text_extents(s)
    ctx.move_to(-ext.x_advance / 2, size * 0.35)
    ctx.text_path(s)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(outline)
    ctx.stroke_preserve()
    ctx.set_source_rgb(*fill)
    ctx.fill()
    ctx.restore()


def make_paper(seed=7):
    """Hafif kâğıt dokulu arka plan (bir kez üretilir)."""
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*PAPER)
    ctx.paint()
    rnd = random.Random(seed)
    for _ in range(9000):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        a = rnd.uniform(0.02, 0.06)
        ctx.set_source_rgba(0.45, 0.35, 0.2, a)
        ctx.arc(x, y, rnd.uniform(0.6, 2.2), 0, 2 * math.pi)
        ctx.fill()
    return surf


# --------------------------------------------------------------------------
# Çöp adam
# --------------------------------------------------------------------------

# Açılar derece: 0 = aşağı, +90 = baktığı yöne yatay, 180 = yukarı, -90 = arkaya
POSES = {
    "stand":   dict(fa=(15, 8), ba=(-15, -8), fl=(10, 4), bl=(-10, -4), lean=0),
    "point":   dict(fa=(100, 96), ba=(-22, -10), fl=(12, 4), bl=(-12, -4), lean=-3),
    "hips":    dict(fa=(45, -50), ba=(-45, 50), fl=(14, 6), bl=(-14, -6), lean=0),
    "relax":   dict(fa=(150, -100), ba=(-150, 100), fl=(16, 6), bl=(-16, -6), lean=-7),
    "shock":   dict(fa=(145, 172), ba=(-145, -172), fl=(20, 8), bl=(-20, -8), lean=-6),
    "think":   dict(fa=(44, 200), ba=(35, 100), fl=(10, 4), bl=(-10, -4), lean=2),
    "push":    dict(fa=(80, 84), ba=(72, 80), fl=(20, 0), bl=(-20, -30), lean=14),
    "cheer":   dict(fa=(165, 172), ba=(-40, -20), fl=(14, 6), bl=(-14, -6), lean=0),
    "sad":     dict(fa=(6, 0), ba=(-6, 0), fl=(6, 2), bl=(-6, -2), lean=10),
    "stretch": dict(fa=(170, 178), ba=(-170, -178), fl=(8, 2), bl=(-8, -2), lean=-4),
    "shrug":   dict(fa=(55, 145), ba=(-55, -145), fl=(10, 4), bl=(-10, -4), lean=0),
    "open":    dict(fa=(115, 135), ba=(-115, -135), fl=(12, 4), bl=(-12, -4), lean=-2),
    "open_arms": dict(fa=(110, 115), ba=(-110, -115), fl=(25, 15), bl=(-25, -35), lean=12),
}

L_HEAD, L_TORSO, L_UARM, L_LARM, L_ULEG, L_LLEG = 34, 112, 58, 55, 68, 66


def blend_pose(p1, p2, k):
    out = {}
    for key in p1:
        a, b = p1[key], p2[key]
        if isinstance(a, tuple):
            out[key] = tuple(x + (y - x) * k for x, y in zip(a, b))
        else:
            out[key] = a + (b - a) * k
    return out


GLOBAL_SCALE = 1.15


def figure_height(scale):
    return (2 * L_HEAD + L_TORSO + L_ULEG + L_LLEG + 8) * scale


def draw_figure(ctx, x, y, scale, pose, face, hat, facing, ink, t,
                talking=False, anim="idle", lean_extra=0.0, wings=False, holds=None):
    """Çöp adamı çizer. x,y piksel (ayak hizası). Eklem noktalarını döndürür."""
    pose = dict(pose)
    scale *= GLOBAL_SCALE
    lw = 9 * scale
    f = facing

    # Animasyonlar
    bob = 0.0
    if anim == "idle":
        bob = 3 * math.sin(t * 2 * math.pi * 1.1) * scale
        pose["fa"] = (pose["fa"][0] + 4 * math.sin(t * 2.3), pose["fa"][1] + 4 * math.sin(t * 2.3))
    elif anim == "bounce":
        bob = -abs(math.sin(t * math.pi * 2.2)) * 28 * scale
    elif anim == "shake":
        x += math.sin(t * 70) * 5 * scale
    elif anim == "walk":
        s = math.sin(t * 2 * math.pi * 1.8)
        fl0, bl0 = pose["fl"], pose["bl"]
        pose["fl"] = (fl0[0] + 22 * s, fl0[1] + 22 * s - 18 * max(0, -s))
        pose["bl"] = (bl0[0] - 22 * s, bl0[1] - 22 * s - 18 * max(0, s))
        bob = -abs(math.cos(t * 2 * math.pi * 1.8)) * 5 * scale

    def vec(angle_deg, length):
        a = math.radians(angle_deg)
        return (f * math.sin(a) * length * scale, math.cos(a) * length * scale)

    lean = math.radians(pose["lean"] + lean_extra)

    # Kalçanın yüksekliği: aşağıda kalan ayak yere değsin
    def leg_drop(angles):
        return (math.cos(math.radians(angles[0])) * L_ULEG + math.cos(math.radians(angles[1])) * L_LLEG) * scale

    drop = max(leg_drop(pose["fl"]), leg_drop(pose["bl"]))
    hip = (x, y - drop + bob)
    up = (f * math.sin(lean), -math.cos(lean))
    neck = (hip[0] + up[0] * L_TORSO * scale, hip[1] + up[1] * L_TORSO * scale)
    shoulder = (neck[0] - up[0] * 8 * scale, neck[1] - up[1] * 8 * scale)
    head = (neck[0] + up[0] * (L_HEAD + 5) * scale, neck[1] + up[1] * (L_HEAD + 5) * scale)

    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    joints = {"hip": hip, "neck": neck, "head": head, "head_r": L_HEAD * scale}

    def limb(start, angles, l1, l2, extra=0.0):
        a1 = angles[0] + extra
        a2 = angles[1] + extra
        v1 = vec(a1, l1)
        mid = (start[0] + v1[0], start[1] + v1[1])
        v2 = vec(a2, l2)
        end = (mid[0] + v2[0], mid[1] + v2[1])
        ctx.move_to(*start)
        ctx.line_to(*mid)
        ctx.line_to(*end)
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(lw)
        ctx.stroke()
        return end

    lean_deg = pose["lean"] + lean_extra
    if wings:
        from .props2 import draw_wings
        draw_wings(ctx, shoulder, scale, t)
    limb(hip, pose["bl"], L_ULEG, L_LLEG)
    joints["back_hand"] = limb(shoulder, pose["ba"], L_UARM, L_LARM, lean_deg)
    line(ctx, hip, neck, ink, lw)
    limb(hip, pose["fl"], L_ULEG, L_LLEG)
    joints["hand"] = limb(shoulder, pose["fa"], L_UARM, L_LARM, lean_deg)

    # Kafa
    r = L_HEAD * scale
    ctx.arc(head[0], head[1], r, 0, 2 * math.pi)
    stroke_fill(ctx, WHITE if ink == INK_DAY else (0.92, 0.89, 0.80), ink, lw * 0.85)
    draw_face(ctx, head, r, f, face, ink, t, talking, lw)
    if hat:
        draw_hat(ctx, head, r, f, hat, ink, lw, t)
    if holds:
        from .props2 import draw_held
        draw_held(ctx, holds, joints["hand"], f, scale, t)
    return joints


def draw_face(ctx, head, r, f, face, ink, t, talking, lw):
    cx, cy = head
    ink_face = INK_DAY
    e1 = (cx + f * r * 0.12, cy - r * 0.12)
    e2 = (cx + f * r * 0.55, cy - r * 0.12)
    m = (cx + f * r * 0.35, cy + r * 0.42)
    ctx.set_source_rgb(*ink_face)

    def dot(p, rr):
        ctx.arc(p[0], p[1], rr, 0, 2 * math.pi)
        ctx.set_source_rgb(*ink_face)
        ctx.fill()

    eye_r = r * 0.11
    # Göz kırpma
    blink = (t % 3.1) < 0.12
    if face == "sleepy" or blink:
        for e in (e1, e2):
            line(ctx, (e[0] - r * 0.1, e[1]), (e[0] + r * 0.1, e[1]), ink_face, lw * 0.4)
    elif face == "shock":
        for e in (e1, e2):
            ctx.arc(e[0], e[1], r * 0.17, 0, 2 * math.pi)
            stroke_fill(ctx, WHITE, ink_face, lw * 0.3)
            dot(e, r * 0.07)
    elif face == "think":
        for e in (e1, e2):
            dot((e[0] + f * r * 0.04, e[1] - r * 0.07), eye_r)
    else:
        for e in (e1, e2):
            dot(e, eye_r)

    # Kaşlar
    if face in ("confident", "effort"):
        for e, s in ((e1, 1), (e2, -1)):
            line(ctx, (e[0] - r * 0.13, e[1] - r * 0.28 - s * f * 0), (e[0] + r * 0.13, e[1] - r * 0.22),
                 ink_face, lw * 0.35)
    elif face == "sad":
        for e in (e1, e2):
            line(ctx, (e[0] - r * 0.13, e[1] - r * 0.20), (e[0] + r * 0.13, e[1] - r * 0.30), ink_face, lw * 0.35)
    elif face == "smug":
        for e in (e1, e2):
            line(ctx, (e[0] - r * 0.14, e[1] - r * 0.06), (e[0] + r * 0.14, e[1] - r * 0.06), ink_face, lw * 0.35)

    # Ağız
    open_mouth = talking and (int(t * 9) % 3 != 0)
    ctx.new_path()
    mw = r * 0.32
    if face == "shock" or (open_mouth and face not in ("sleepy",)):
        h = r * (0.26 if face == "shock" else 0.12 + 0.08 * abs(math.sin(t * 17)))
        ctx.save()
        ctx.translate(m[0], m[1])
        ctx.scale(mw * 0.7, h)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, (0.45, 0.12, 0.12), ink_face, lw * 0.3)
    elif face in ("happy", "confident", "smile"):
        ctx.arc(m[0], m[1] - r * 0.12, mw, math.radians(25), math.radians(155))
        ctx.set_source_rgb(*ink_face)
        ctx.set_line_width(lw * 0.4)
        ctx.stroke()
    elif face == "sad":
        ctx.arc(m[0], m[1] + r * 0.18, mw * 0.8, math.radians(205), math.radians(335))
        ctx.set_source_rgb(*ink_face)
        ctx.set_line_width(lw * 0.4)
        ctx.stroke()
    elif face == "smug":
        ctx.move_to(m[0] - mw * 0.6, m[1])
        ctx.curve_to(m[0], m[1] + r * 0.05, m[0] + f * mw * 0.5, m[1], m[0] + f * mw * 0.8, m[1] - r * 0.15)
        ctx.set_source_rgb(*ink_face)
        ctx.set_line_width(lw * 0.4)
        ctx.stroke()
    elif face == "effort":
        ctx.rectangle(m[0] - mw * 0.6, m[1] - r * 0.08, mw * 1.2, r * 0.16)
        stroke_fill(ctx, WHITE, ink_face, lw * 0.3)
        line(ctx, (m[0], m[1] - r * 0.08), (m[0], m[1] + r * 0.08), ink_face, lw * 0.2)
        # Ter damlası
        dx = cx - f * r * 0.7
        dy = cy - r * 0.5 + (t * 40 % 20)
        ctx.move_to(dx, dy - r * 0.18)
        ctx.curve_to(dx + r * 0.12, dy, dx + r * 0.1, dy + r * 0.12, dx, dy + r * 0.12)
        ctx.curve_to(dx - r * 0.1, dy + r * 0.12, dx - r * 0.12, dy, dx, dy - r * 0.18)
        stroke_fill(ctx, (0.6, 0.82, 0.96), ink_face, lw * 0.2)
    elif face == "sleepy":
        ctx.arc(m[0], m[1], r * 0.08, 0, 2 * math.pi)
        stroke_fill(ctx, None, ink_face, lw * 0.3)
    else:  # neutral / think
        line(ctx, (m[0] - mw * 0.4, m[1]), (m[0] + mw * 0.4, m[1]), ink_face, lw * 0.4)


def draw_hat(ctx, head, r, f, hat, ink, lw, t):
    cx, cy = head
    lw2 = lw * 0.7
    if hat == "sarik":  # Osmanlı sarığı (büyük, yuvarlak, kırmızı tepeli)
        tcx, tcy = cx - f * r * 0.05, cy - r * 0.95
        ctx.save()
        ctx.translate(tcx, tcy - r * 0.55)
        ctx.scale(r * 0.45, r * 0.5)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, RED, ink, lw * 0.5)
        ctx.save()
        ctx.translate(tcx, tcy)
        ctx.scale(r * 1.25, r * 0.9)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, WHITE, ink, lw2)
        for k in (-0.35, 0.05, 0.42):
            ctx.save()
            ctx.translate(tcx, tcy + k * r - r * 0.25)
            ctx.scale(r * 1.1, r * 0.45)
            ctx.arc(0, 0, 1, math.radians(25), math.radians(155))
            ctx.restore()
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(lw * 0.3)
            ctx.stroke()
    elif hat == "crown":
        base = cy - r * 0.75
        pts = [(-0.85, 0), (-0.85, -0.75), (-0.45, -0.3), (0, -0.95), (0.45, -0.3), (0.85, -0.75), (0.85, 0)]
        ctx.move_to(cx + pts[0][0] * r, base + pts[0][1] * r)
        for px, py in pts[1:]:
            ctx.line_to(cx + px * r, base + py * r)
        ctx.close_path()
        stroke_fill(ctx, GOLD, ink, lw2)
        for px in (-0.45, 0, 0.45):
            ctx.arc(cx + px * r, base - r * 0.15, r * 0.09, 0, 2 * math.pi)
            stroke_fill(ctx, RED, ink, lw * 0.25)
    elif hat == "helmet":  # Bizans askeri miğferi + sorguç
        ctx.arc(cx, cy - r * 0.05, r * 1.05, math.pi, 2 * math.pi)
        ctx.close_path()
        stroke_fill(ctx, (0.65, 0.70, 0.76), ink, lw2)
        line(ctx, (cx - r * 1.15, cy - r * 0.05), (cx + r * 1.15, cy - r * 0.05), ink, lw2)
        ctx.move_to(cx - f * r * 0.7, cy - r * 0.95)
        ctx.curve_to(cx - f * r * 0.3, cy - r * 1.8, cx + f * r * 0.6, cy - r * 1.7, cx + f * r * 0.9, cy - r * 1.0)
        ctx.curve_to(cx + f * r * 0.4, cy - r * 1.3, cx - f * r * 0.2, cy - r * 1.3, cx - f * r * 0.7, cy - r * 0.95)
        stroke_fill(ctx, RED, ink, lw * 0.45)
    elif hat == "bork":  # Yeniçeri börkü
        ctx.move_to(cx - r * 0.8, cy - r * 0.55)
        ctx.line_to(cx + r * 0.8, cy - r * 0.55)
        ctx.curve_to(cx + r * 0.7, cy - r * 1.6, cx - f * r * 0.2, cy - r * 2.2, cx - f * r * 0.9, cy - r * 1.9)
        ctx.curve_to(cx - f * r * 1.6, cy - r * 1.4, cx - f * r * 1.4, cy - r * 0.3, cx - f * r * 1.5, cy + r * 0.3)
        ctx.curve_to(cx - f * r * 1.1, cy - r * 0.2, cx - f * r * 1.0, cy - r * 0.5, cx - r * 0.8, cy - r * 0.55)
        stroke_fill(ctx, WHITE, ink, lw2)
        ctx.rectangle(cx - r * 0.85, cy - r * 0.75, r * 1.7, r * 0.25)
        stroke_fill(ctx, GOLD, ink, lw * 0.4)
    else:
        from .props2 import draw_hat2
        draw_hat2(ctx, head, r, f, hat, ink, lw, t)


# --------------------------------------------------------------------------
# Aksesuarlar
# --------------------------------------------------------------------------

def draw_ship(ctx, x, y, scale, tilt, ink, t):
    """x,y: omurga (gövde altı) ortası, piksel."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(tilt)
    ctx.scale(scale, scale)
    lw = 8
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # Kürekler
    for k in range(-3, 4):
        line(ctx, (k * 32, -30), (k * 32 - 18, 22), ink, 5)
    # Gövde
    ctx.move_to(-175, -75)
    ctx.curve_to(-150, -50, -140, -60, -120, -55)
    ctx.line_to(140, -55)
    ctx.curve_to(165, -60, 175, -80, 190, -95)
    ctx.curve_to(170, -30, 120, 0, 60, 0)
    ctx.line_to(-90, 0)
    ctx.curve_to(-140, 0, -165, -35, -175, -75)
    ctx.close_path()
    stroke_fill(ctx, WOOD, ink, lw)
    line(ctx, (-140, -30), (160, -30), ink, 3)
    for k in range(-2, 3):
        ctx.arc(k * 45, -42, 6, 0, 2 * math.pi)
        stroke_fill(ctx, (0.3, 0.2, 0.12), ink, 2)
    # Direk + yelken
    line(ctx, (0, -55), (0, -300), ink, lw)
    bulge = 25 + 8 * math.sin(t * 3)
    ctx.move_to(-85, -270)
    ctx.line_to(85, -270)
    ctx.curve_to(85 + bulge, -200, 85 + bulge, -150, 85, -95)
    ctx.line_to(-85, -95)
    ctx.curve_to(-85 + bulge, -150, -85 + bulge, -200, -85, -270)
    ctx.close_path()
    stroke_fill(ctx, (0.99, 0.97, 0.92), ink, lw * 0.8)
    # Yelkende hilal
    ctx.new_path()
    ctx.arc(10, -183, 34, 0, 2 * math.pi)
    ctx.set_source_rgb(*RED)
    ctx.fill()
    ctx.arc(22, -183, 28, 0, 2 * math.pi)
    ctx.set_source_rgb(0.99, 0.97, 0.92)
    ctx.fill()
    # Flama
    wave = math.sin(t * 6) * 8
    ctx.move_to(0, -300)
    ctx.curve_to(30, -310 + wave, 55, -290 - wave, 80, -300 + wave)
    ctx.line_to(0, -280)
    ctx.close_path()
    stroke_fill(ctx, RED, ink, 3)
    ctx.restore()


def draw_chain(ctx, x1, x2, y, ink, t, shake=False):
    n = int(abs(x2 - x1) / 34)
    jitter = math.sin(t * 50) * 4 if shake else 0
    for i in range(n + 1):
        u = i / max(1, n)
        x = x1 + (x2 - x1) * u
        sag = 40 * math.sin(math.pi * u)
        yy = y + sag + jitter * math.sin(u * 9)
        ctx.save()
        ctx.translate(x, yy)
        if i % 2 == 0:
            ctx.scale(24, 13)
        else:
            ctx.scale(22, 5)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, None, (0.35, 0.36, 0.40), 9)
        ctx.save()
        ctx.translate(x, yy)
        ctx.scale(24 if i % 2 == 0 else 22, 13 if i % 2 == 0 else 5)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, None, (0.62, 0.64, 0.68), 4)


def draw_wall(ctx, cx, w, h, ink, towers=True):
    left, right = sx(cx - w / 2), sx(cx + w / 2)
    top, bottom = sy(1 - h), sy(1.02)
    lw = 7
    ctx.rectangle(left, top, right - left, bottom - top)
    stroke_fill(ctx, STONE, ink, lw)
    # Mazgallar
    mw = 38
    x = left + 6
    while x < right - mw:
        ctx.rectangle(x, top - 30, mw, 32)
        stroke_fill(ctx, STONE, ink, lw)
        x += mw * 1.9
    # Taş çizgileri
    rnd = random.Random(int(cx * 1000))
    yy = top + 45
    row = 0
    while yy < bottom:
        line(ctx, (left, yy), (right, yy), ink, 2.5)
        off = 0 if row % 2 == 0 else 40
        xx = left + off
        while xx < right:
            line(ctx, (xx, yy - 45), (xx, yy), ink, 2.5)
            xx += 80 + rnd.uniform(-8, 8)
        yy += 45
        row += 1
    if towers:
        for tx in (left - 10, right - 80):
            ctx.rectangle(tx, top - 90, 90, bottom - top + 90)
            stroke_fill(ctx, (0.80, 0.74, 0.62), ink, lw)
            for k in range(2):
                ctx.rectangle(tx + 4 + k * 50, top - 120, 32, 32)
                stroke_fill(ctx, (0.80, 0.74, 0.62), ink, lw)
            ctx.rectangle(tx + 33, top - 50, 24, 40)
            stroke_fill(ctx, (0.25, 0.22, 0.2), ink, 4)


def draw_bubble(ctx, text, x, y, tx, ty, ink, k=1.0):
    set_font(ctx, HAND_FONT, 58)
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(ctx, trial) > 640 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    lines.append(cur)
    bw = max(text_width(ctx, l) for l in lines) + 70
    bh = len(lines) * 66 + 40
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(k, k)
    ctx.translate(-x, -y)
    l, tp = x - bw / 2, y - bh / 2
    rr = 34
    ctx.new_path()
    ctx.arc(l + bw - rr, tp + rr, rr, -math.pi / 2, 0)
    ctx.arc(l + bw - rr, tp + bh - rr, rr, 0, math.pi / 2)
    ctx.line_to(x + 30, tp + bh)
    ctx.line_to(tx, ty)
    ctx.line_to(x - 20, tp + bh)
    ctx.arc(l + rr, tp + bh - rr, rr, math.pi / 2, math.pi)
    ctx.arc(l + rr, tp + rr, rr, math.pi, 3 * math.pi / 2)
    ctx.close_path()
    stroke_fill(ctx, WHITE, INK_DAY, 7)
    ctx.set_source_rgb(*INK_DAY)
    for i, ln in enumerate(lines):
        ctx.move_to(x - text_width(ctx, ln) / 2, tp + 70 + i * 66)
        ctx.show_text(ln)
    ctx.restore()


def draw_bulb(ctx, x, y, ink, t, k):
    if k <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(k, k)
    pulse = 1 + 0.08 * math.sin(t * 10)
    for i in range(8):
        a = i * math.pi / 4 + t * 0.5
        line(ctx, (math.cos(a) * 62 * pulse, math.sin(a) * 62 * pulse - 10),
             (math.cos(a) * 88 * pulse, math.sin(a) * 88 * pulse - 10), (0.95, 0.65, 0.1), 7)
    ctx.arc(0, -10, 44, math.radians(140), math.radians(40))
    ctx.line_to(18, 48)
    ctx.line_to(-18, 48)
    ctx.close_path()
    stroke_fill(ctx, YELLOW, INK_DAY, 6)
    ctx.rectangle(-20, 48, 40, 22)
    stroke_fill(ctx, (0.7, 0.7, 0.72), INK_DAY, 5)
    ctx.restore()


def draw_flag(ctx, hand, ink, t, emblem=True):
    hx, hy = hand
    top = hy - 230
    line(ctx, (hx, hy + 30), (hx, top), (0.45, 0.3, 0.18), 9)
    ctx.move_to(hx, top)
    pts = []
    for i in range(11):
        u = i / 10
        pts.append((hx + u * 190, top + 12 * math.sin(t * 6 - u * 5) * u))
    for p in pts:
        ctx.line_to(*p)
    for i in range(10, -1, -1):
        u = i / 10
        ctx.line_to(hx + u * 190, top + 120 + 12 * math.sin(t * 6 - u * 5) * u)
    ctx.close_path()
    stroke_fill(ctx, RED, INK_DAY, 6)
    if not emblem:
        return
    cx, cy = hx + 85, top + 60 + 8 * math.sin(t * 6 - 2.2) * 0.45
    ctx.arc(cx, cy, 34, 0, 2 * math.pi)
    ctx.set_source_rgb(*WHITE)
    ctx.fill()
    ctx.arc(cx + 13, cy, 28, 0, 2 * math.pi)
    ctx.set_source_rgb(*RED)
    ctx.fill()


# --------------------------------------------------------------------------
# Arka planlar
# --------------------------------------------------------------------------

def draw_background(ctx, bg, night, t):
    ink = INK_NIGHT if night else INK_DAY
    ctx.rectangle(PX, PY, PW, PH)
    ctx.set_source_rgb(*(PANEL_NIGHT if night else PANEL_DAY))
    ctx.fill()

    if night:
        rnd = random.Random(3)
        for _ in range(40):
            x, y = sx(rnd.random()), sy(rnd.random() * 0.5)
            tw = 0.5 + 0.5 * math.sin(t * 3 + x)
            ctx.arc(x, y, 2 + 2 * tw, 0, 2 * math.pi)
            ctx.set_source_rgb(1, 0.95, 0.75)
            ctx.fill()
        ctx.arc(sx(0.82), sy(0.14), 55, 0, 2 * math.pi)
        ctx.set_source_rgb(0.99, 0.95, 0.78)
        ctx.fill()
        ctx.arc(sx(0.85), sy(0.12), 48, 0, 2 * math.pi)
        ctx.set_source_rgb(*PANEL_NIGHT)
        ctx.fill()
    else:
        if bg not in ("desert", "palace"):
            ctx.arc(sx(0.86), sy(0.13), 60, 0, 2 * math.pi)
            stroke_fill(ctx, (1.0, 0.88, 0.45), INK_DAY, 5)
        # bulutlar
        for cxx, cyy, s in ((0.18 + 0.01 * math.sin(t * 0.5), 0.12, 1.0), (0.55 + 0.01 * math.sin(t * 0.4 + 1), 0.07, 0.75)):
            circles = ((-40, 0, 32), (0, -18, 40), (42, 0, 30), (0, 8, 30))
            for dx, dy, rr in circles:
                ctx.new_sub_path()
                ctx.arc(sx(cxx) + dx * s, sy(cyy) + dy * s, rr * s, 0, 2 * math.pi)
            ctx.set_source_rgb(*INK_DAY)
            ctx.set_line_width(9)
            ctx.stroke_preserve()
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()

    water = WATER_NIGHT if night else WATER_DAY
    grass = GRASS_NIGHT if night else GRASS_DAY

    if bg == "sea":
        # uzakta şehir silueti
        ctx.set_source_rgba(*(ink), 0.18)
        base = sy(0.80)
        for cxx, rr in ((0.62, 40), (0.72, 60), (0.84, 45), (0.93, 35)):
            ctx.rectangle(sx(cxx) - rr, base - rr * 0.8, rr * 2, rr * 0.8)
            ctx.fill()
            ctx.arc(sx(cxx), base - rr * 0.8, rr * 0.8, math.pi, 2 * math.pi)
            ctx.fill()
        draw_water(ctx, 0.80, water, ink, t)
    elif bg == "hill":
        draw_water(ctx, 0.90, water, ink, t)
        ctx.move_to(sx(-0.02), sy(1.05))
        for i in range(0, 101):
            x = i / 100
            ctx.line_to(sx(x), sy(hill_y(x)))
        ctx.line_to(sx(1.02), sy(1.05))
        ctx.close_path()
        stroke_fill(ctx, grass, ink, 7)
        # yağlı kızaklar (tahta raylar)
        for i in range(4, 97, 4):
            x = i / 100
            y = hill_y(x)
            a = math.atan(hill_slope(x) * PH / PW)
            ctx.save()
            ctx.translate(sx(x), sy(y) + 6)
            ctx.rotate(a)
            ctx.rectangle(-6, -5, 12, 14)
            ctx.restore()
            stroke_fill(ctx, WOOD, ink, 3)
    else:
        from .props2 import draw_background2
        if draw_background2(ctx, bg, night, t):
            return
        # plain
        g = sy(0.93)
        ctx.rectangle(PX, g, PW, PY + PH - g)
        ctx.set_source_rgb(*grass)
        ctx.fill()
        line(ctx, (PX, g), (PX + PW, g), ink, 7)
        rnd = random.Random(11)
        for _ in range(14):
            x = sx(rnd.random())
            for d in (-8, 0, 8):
                line(ctx, (x, g + 4), (x + d, g - 14), ink, 3)


def draw_water(ctx, level, color, ink, t):
    top = sy(level)
    ctx.move_to(PX, PY + PH)
    ctx.line_to(PX, top)
    for i in range(0, 101):
        u = i / 100
        ctx.line_to(PX + u * PW, top + 8 * math.sin(u * 22 + t * 2.5))
    ctx.line_to(PX + PW, PY + PH)
    ctx.close_path()
    stroke_fill(ctx, color, ink, 6)
    for k in range(3):
        yy = top + 50 + k * 45
        if yy > PY + PH:
            break
        for j in range(5):
            x0 = PX + ((j * 230 + k * 110 + t * 30) % (PW + 100)) - 50
            ctx.move_to(x0, yy)
            ctx.curve_to(x0 + 15, yy - 10, x0 + 30, yy - 10, x0 + 45, yy)
            ctx.set_source_rgba(1, 1, 1, 0.6)
            ctx.set_line_width(4)
            ctx.stroke()


# --------------------------------------------------------------------------
# Anlatıcı: "Tarih Hoca" (kameraya dönük karikatür)
# --------------------------------------------------------------------------

# Açılar: 0 = aşağı, + = dışa doğru, 180 = yukarı, negatif = içe (gövdeye doğru)
NARRATOR_POSES = {
    "idle":  dict(la=(18, 8), ra=(18, 8)),
    "open":  dict(la=(115, 135), ra=(115, 135)),
    "point": dict(la=(18, 8), ra=(95, 88)),
    "think": dict(la=(35, -85), ra=(28, -165)),
    "wave":  dict(la=(18, 8), ra=(140, 172)),
    "hips":  dict(la=(55, -40), ra=(55, -40)),
    "shrug": dict(la=(75, 150), ra=(75, 150)),
    "up":    dict(la=(18, 8), ra=(150, 178)),
}

N_HEAD, N_TORSO, N_UARM, N_LARM, N_ULEG, N_LLEG = 62, 120, 72, 66, 78, 72


def draw_burst(ctx, t, c1=(1.0, 0.86, 0.35), c2=(1.0, 0.93, 0.62)):
    """Dikkat çekici dönen ışın arka planı."""
    ctx.rectangle(PX, PY, PW, PH)
    ctx.set_source_rgb(*c2)
    ctx.fill()
    cx, cy = PX + PW / 2, PY + PH * 0.48
    n = 18
    rot = t * 0.35
    for i in range(n):
        a1 = rot + i * 2 * math.pi / n
        a2 = a1 + math.pi / n
        ctx.move_to(cx, cy)
        ctx.line_to(cx + math.cos(a1) * 1500, cy + math.sin(a1) * 1500)
        ctx.line_to(cx + math.cos(a2) * 1500, cy + math.sin(a2) * 1500)
        ctx.close_path()
        ctx.set_source_rgb(*c1)
        ctx.fill()


def draw_sparkle(ctx, x, y, size, t):
    if size <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(t * 3)
    ctx.new_path()
    for i in range(8):
        a = i * math.pi / 4
        rr = size if i % 2 == 0 else size * 0.25
        p = (math.sin(a) * rr, -math.cos(a) * rr)
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK_DAY)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()


def draw_narrator(ctx, x, y, scale, pose, face, t, talking=False, anim="idle",
                  squash=1.0, wink_k=0.0):
    """Tarih Hoca: kocaman kafa, yuvarlak gözlük, bıyık, papyon. x,y ayak hizası."""
    scale *= GLOBAL_SCALE
    ink = INK_DAY
    lw = 10 * scale
    bob = 0.0
    if anim == "idle":
        bob = 4 * math.sin(t * 2 * math.pi * 1.0) * scale
    elif anim == "bounce":
        bob = -abs(math.sin(t * math.pi * 2.0)) * 30 * scale
    ctx.save()
    # zıplama sırasında esneme-büzülme
    ctx.translate(x, y)
    ctx.scale(1 / math.sqrt(squash), squash)
    ctx.translate(-x, -y)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    legs = (N_ULEG + N_LLEG) * scale
    hip = (x, y - legs + bob)
    neck = (x, hip[1] - N_TORSO * scale)
    head = (x, neck[1] - (N_HEAD - 6) * scale)

    def vec(a, l, side):
        a = math.radians(a)
        return (side * math.sin(a) * l * scale, math.cos(a) * l * scale)

    def limb(start, angles, l1, l2, side):
        v1 = vec(angles[0], l1, side)
        mid = (start[0] + v1[0], start[1] + v1[1])
        v2 = vec(angles[1], l2, side)
        end = (mid[0] + v2[0], mid[1] + v2[1])
        ctx.move_to(*start)
        ctx.line_to(*mid)
        ctx.line_to(*end)
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(lw)
        ctx.stroke()
        return end

    # bacaklar
    for side in (-1, 1):
        limb(hip, (8, 3), N_ULEG, N_LLEG, side)
        foot = (hip[0] + side * (math.sin(math.radians(8)) * N_ULEG + math.sin(math.radians(3)) * N_LLEG) * scale, y + bob * 0)
        ctx.save()
        ctx.translate(foot[0] + side * 12 * scale, y - 6 * scale)
        ctx.scale(24 * scale, 10 * scale)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, INK_DAY, ink, lw * 0.3)
    # gövde
    line(ctx, hip, neck, ink, lw)
    shoulder = (neck[0], neck[1] + 12 * scale)
    pose = dict(pose)
    if "wave" in str(pose.get("_name", "")):
        pass
    lh = limb(shoulder, pose["la"], N_UARM, N_LARM, -1)
    rh = limb(shoulder, pose["ra"], N_UARM, N_LARM, 1)
    for hnd in (lh, rh):
        ctx.arc(hnd[0], hnd[1], 10 * scale, 0, 2 * math.pi)
        stroke_fill(ctx, WHITE, ink, lw * 0.5)
    # papyon
    bx, by = neck[0], neck[1] + 6 * scale
    for side in (-1, 1):
        ctx.move_to(bx, by)
        ctx.line_to(bx + side * 30 * scale, by - 16 * scale)
        ctx.line_to(bx + side * 30 * scale, by + 16 * scale)
        ctx.close_path()
        stroke_fill(ctx, RED, ink, lw * 0.4)
    ctx.arc(bx, by, 8 * scale, 0, 2 * math.pi)
    stroke_fill(ctx, RED, ink, lw * 0.4)

    # kafa
    r = N_HEAD * scale
    cx, cy = head
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    stroke_fill(ctx, WHITE, ink, lw * 0.85)
    # saç perçemi
    ctx.move_to(cx - r * 0.25, cy - r * 0.95)
    ctx.curve_to(cx - r * 0.1, cy - r * 1.45, cx + r * 0.25, cy - r * 1.35, cx + r * 0.15, cy - r * 0.98)
    ctx.move_to(cx + r * 0.05, cy - r * 0.98)
    ctx.curve_to(cx + r * 0.25, cy - r * 1.3, cx + r * 0.55, cy - r * 1.2, cx + r * 0.45, cy - r * 0.88)
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(lw * 0.6)
    ctx.stroke()

    # gözler + gözlük
    look = (0.0, 0.0)
    if face == "think":
        look = (r * 0.07, -r * 0.08)
    eyes = [(cx - r * 0.36, cy - r * 0.12), (cx + r * 0.36, cy - r * 0.12)]
    blink = (t % 3.3) < 0.1 and face not in ("wink",)
    for i, (ex, ey) in enumerate(eyes):
        closed = blink or (face == "wink" and i == 0 and wink_k > 0.5)
        if closed:
            ctx.arc(ex, ey + r * 0.04, r * 0.11, math.radians(200), math.radians(340))
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(lw * 0.45)
            ctx.stroke()
        else:
            er = r * (0.12 if face != "surprised" else 0.15)
            ctx.arc(ex + look[0], ey + look[1], er, 0, 2 * math.pi)
            ctx.set_source_rgb(*ink)
            ctx.fill()
            ctx.arc(ex + look[0] - er * 0.3, ey + look[1] - er * 0.35, er * 0.3, 0, 2 * math.pi)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
        ctx.arc(ex, ey, r * 0.27, 0, 2 * math.pi)
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(lw * 0.4)
        ctx.stroke()
    line(ctx, (cx - r * 0.09, cy - r * 0.14), (cx + r * 0.09, cy - r * 0.14), ink, lw * 0.4)
    # kaşlar
    for i, (ex, ey) in enumerate(eyes):
        lift = 0.0
        if face == "wink" and i == 1:
            lift = r * 0.16 * wink_k
        if face == "surprised":
            lift = r * 0.12
        if face == "think" and i == 1:
            lift = r * 0.12
        tilt = 0.06 * r if (face == "wink" and i == 0) else 0
        ctx.move_to(ex - r * 0.2, ey - r * 0.42 - lift + (tilt if i == 0 else 0))
        ctx.curve_to(ex - r * 0.05, ey - r * 0.52 - lift, ex + r * 0.08, ey - r * 0.52 - lift,
                     ex + r * 0.2, ey - r * 0.44 - lift - (0 if i == 0 else 0))
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(lw * 0.5)
        ctx.stroke()
    # burun
    ctx.arc(cx, cy + r * 0.18, r * 0.09, math.radians(-30), math.radians(210))
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(lw * 0.35)
    ctx.stroke()
    # ağız
    my = cy + r * 0.58
    open_mouth = talking and (int(t * 9) % 3 != 0)
    if open_mouth or face == "surprised":
        h = r * (0.2 if face == "surprised" else 0.08 + 0.1 * abs(math.sin(t * 15)))
        ctx.save()
        ctx.translate(cx, my)
        ctx.scale(r * 0.24, h)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        stroke_fill(ctx, (0.55, 0.15, 0.15), ink, lw * 0.35)
    elif face == "wink":
        ctx.move_to(cx - r * 0.25, my - r * 0.02)
        ctx.curve_to(cx - r * 0.05, my + r * 0.12, cx + r * 0.2, my + r * 0.08, cx + r * 0.32, my - r * 0.12)
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(lw * 0.45)
        ctx.stroke()
    elif face == "think":
        line(ctx, (cx - r * 0.08, my), (cx + r * 0.16, my - r * 0.03), ink, lw * 0.45)
    else:
        ctx.arc(cx, my - r * 0.12, r * 0.24, math.radians(25), math.radians(155))
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(lw * 0.45)
        ctx.stroke()
    # bıyık
    for side in (-1, 1):
        ctx.move_to(cx, cy + r * 0.33)
        ctx.curve_to(cx + side * r * 0.2, cy + r * 0.22, cx + side * r * 0.42, cy + r * 0.3,
                     cx + side * r * 0.5, cy + r * 0.2)
        ctx.curve_to(cx + side * r * 0.45, cy + r * 0.45, cx + side * r * 0.2, cy + r * 0.45, cx, cy + r * 0.38)
        ctx.close_path()
        ctx.set_source_rgb(0.25, 0.18, 0.12)
        ctx.fill_preserve()
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(lw * 0.25)
        ctx.stroke()
    ctx.restore()
    return {"head": head, "head_r": r, "hand": rh, "eye_l": eyes[0]}
