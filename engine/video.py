"""SON MOLA video motoru (19 Kasım: Kayıp Vakalar motorundan uyarlandı; seçimli "Sen olsan?" dizileri).
Sahne = yapay zekâ çizimi (hareketli: parallax + parçacık) + karanlık renk + film greni + sis + kelime kelime alt yazı
+ isteğe bağlı TELEFON ekranı (grup mesajları / bildirim) + sonda A/B SEÇİM kartı.
Kullanım: python -m engine.video <bölüm.json> <resim_klasörü> <çıktı.mp4>"""
import json
import re
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import ses as S

W, H, FPS = 1080, 1920, 30
IMG_Y, IMG_H = 210, 1440
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "fonts", "Poppins-Bold.ttf")
HANDLE = "@sonmola.dizi"
RED = (226, 58, 52)
WHITE = (240, 240, 244)
LEAD, GAP, FADE, END = 0.4, 0.45, 0.6, 3.2
CAP_Y = 1360


def font(size):
    return ImageFont.truetype(FONT, size)


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


# --------------------------------------------------------------------------
# Sabit katmanlar
# --------------------------------------------------------------------------
def bolum_etiketi(ep):
    """Üst başlık: "MAHALLE GRUBU · 2. GECE" gibi (dizi_adi + gece); yoksa başlık."""
    if ep.get("dizi_adi"):
        g = f" · {ep['gece']}. GECE" if ep.get("gece") else ""
        return tr_upper(f"{ep['dizi_adi']}{g}")
    return tr_upper(ep["title"])


def header(ep):
    im = Image.new("RGB", (W, H), (6, 7, 10))
    d = ImageDraw.Draw(im)
    f1 = font(30)
    t1 = "S O N   M O L A   ·   S E N   O L S A N ?"
    d.text(((W - d.textlength(t1, font=f1)) / 2, 52), t1, font=f1, fill=RED)
    size = 54
    t2 = bolum_etiketi(ep)
    while d.textlength(t2, font=font(size)) > W - 80 and size > 34:
        size -= 2
    d.text(((W - d.textlength(t2, font=font(size))) / 2, 104), t2, font=font(size), fill=WHITE)
    fh = font(36)
    d.text(((W - d.textlength(HANDLE, font=fh)) / 2, 1690), HANDLE, font=fh, fill=(110, 112, 122))
    return np.asarray(im, np.float32)


def edge_mask():
    m = np.ones((IMG_H, W), np.float32)
    g = 140
    m[:g] *= (np.linspace(0, 1, g) ** 1.5)[:, None]
    m[-260:] *= (np.linspace(1, 0, 260) ** 1.2)[:, None]
    yy, xx = np.mgrid[0:IMG_H, 0:W].astype(np.float32)
    dist = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - IMG_H / 2) / (IMG_H * 0.62)) ** 2)
    vig = np.clip(1.15 - dist ** 2 * 0.55, 0.25, 1.0)
    return m[..., None], vig[..., None]


def grains(n=6, seed=9):
    rng = np.random.default_rng(seed)
    return [rng.normal(0, 4, (IMG_H // 2, W // 2)).astype(np.float32).repeat(2, 0).repeat(2, 1)[..., None]
            for _ in range(n)]


class Fog:
    """Dikişsiz (periyodik) yavaş akan sis dokusu."""

    def __init__(self, h=IMG_H, w=W, seed=3):
        rng = np.random.default_rng(seed)
        fy = np.fft.fftfreq(h)[:, None]
        fx = np.fft.fftfreq(w)[None, :]
        acc = np.zeros((h, w), np.float32)
        for sigma, wgt in ((16, 0.45), (45, 0.35), (110, 0.2)):
            n = rng.random((h, w)).astype(np.float32)
            b = np.real(np.fft.ifft2(np.fft.fft2(n) * np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))))
            acc += ((b - b.mean()) / (b.std() + 1e-6)).astype(np.float32) * wgt
        acc = np.clip((np.clip(0.5 + acc * 0.32, 0, 1) - 0.35) * 2.0, 0, 1)
        self.tex = np.concatenate([acc, acc], axis=1)
        self.w = w
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        self.band = np.clip((yy - 0.25) / 0.6, 0.2, 1.0)

    def alpha(self, t, k):
        o1 = int((t * 22) % self.w)
        o2 = int((t * 9 + self.w / 2) % self.w)
        a = 0.6 * self.tex[:, o1:o1 + self.w] + 0.4 * self.tex[::-1, o2:o2 + self.w]
        return (a * self.band * k)[..., None]


def grade(img, sicak=False):
    g = img.mean(axis=2, keepdims=True)
    img = img * 0.62 + g * 0.38
    tint = np.array([1.02, 0.96, 0.86] if sicak else [0.90, 0.97, 1.08], np.float32)
    img = img * tint
    return (img - 128) * 1.08 + 122


# --------------------------------------------------------------------------
# Alt yazı
# --------------------------------------------------------------------------
def word_times(text, start, dur):
    words = text.split()
    w = [len(x) + 2 for x in words]
    tot = sum(w)
    out, t = [], start
    for x, k in zip(words, w):
        d = dur * k / tot
        out.append((x, t, t + d))
        t += d
    return out


def chunks(timed, maxw=W - 140, size=62):
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f = font(size)
    res, cur = [], []
    for item in timed:
        trial = " ".join(x for x, _, _ in cur + [item])
        if cur and (d.textlength(trial, font=f) > maxw or len(cur) >= 4 or cur[-1][0][-1] in ".!?:"):
            res.append(cur)
            cur = []
        cur.append(item)
    if cur:
        res.append(cur)
    return res


_CAP = {}


def caption_layer(ch, hi, size=62):
    key = (id(ch), hi)
    if key in _CAP:
        return _CAP[key]
    f = font(size)
    lay = Image.new("RGBA", (W, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    words = [x for x, _, _ in ch]
    sp = d.textlength(" ", font=f)
    widths = [d.textlength(x, font=f) for x in words]
    x = (W - (sum(widths) + sp * (len(words) - 1))) / 2
    for i, (wd, wtxt) in enumerate(zip(widths, words)):
        if i == hi:
            d.rectangle([x - 10, 22, x + wd + 10, 112], fill=RED + (235,))
        d.text((x + 3, 28), wtxt, font=f, fill=(0, 0, 0, 170))
        d.text((x, 24), wtxt, font=f, fill=WHITE + (255,))
        x += wd + sp
    arr = np.asarray(lay, np.float32)
    _CAP[key] = arr
    return arr


def paste(frame, lay, y, alpha=1.0):
    h = lay.shape[0]
    a = lay[..., 3:4] / 255 * alpha
    frame[y:y + h] = frame[y:y + h] * (1 - a) + lay[..., :3] * a


def tag_layer(text):
    f = font(30)
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = int(d.textlength(text, font=f))
    lay = Image.new("RGBA", (tw + 40, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, tw + 39, 55], fill=(8, 8, 10, 200), outline=RED + (255,), width=3)
    d.text((20, 9), text, font=f, fill=WHITE + (255,))
    return np.asarray(lay, np.float32)


# --------------------------------------------------------------------------
# 0. saniye kanca yazısı (13 Kasım): sessiz izleyen de ilk karede ne olduğunu anlasın
# --------------------------------------------------------------------------
KANCA_SURE, ZOOM_SURE = 3.0, 0.8


def kanca_metni(ep):
    """Bölümde "kanca_yazi" varsa o; yoksa açıklamanın ilk satırı (zaten kanca olarak yazılıyor)."""
    t = (ep.get("kanca_yazi") or "").strip()
    if not t:
        t = ((ep.get("caption") or ep.get("instagram_caption") or "").strip().split("\n") or [""])[0]
    t = "".join(ch for ch in t if ord(ch) < 0x2190 or ch in "…’‘“”–—").strip()
    t = " ".join(t.split())
    if len(t) > 60:                      # uzunsa sadece ilk cümle
        m = re.match(r"(.+?[.?!…])(\s|$)", t)
        if m and len(m.group(1)) >= 15:
            t = m.group(1)
    w = t.split()
    if len(w) > 18:
        t = " ".join(w[:17]) + "…"
    return t


def _kanca_sar(d, metin, f, maxw):
    satirlar, cur = [], ""
    for w in metin.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > maxw and cur:
            satirlar.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        satirlar.append(cur)
    return satirlar


def kanca_layer(text, size=78):
    if not text:
        return None
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    while size > 54:
        lines = _kanca_sar(d, text, font(size), W - 170)
        if len(lines) <= 3:
            break
        size -= 4
    f = font(size)
    lh = int(size * 1.25)
    h = lh * len(lines) + 70
    lay = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    bw = max(dd.textlength(ln, font=f) for ln in lines) + 90
    dd.rounded_rectangle([(W - bw) / 2, 0, (W + bw) / 2, h - 1], 34, fill=(8, 8, 10, 175))
    y = 35
    for ln in lines:
        dd.text(((W - dd.textlength(ln, font=f)) / 2, y), ln, font=f, fill=(255, 255, 255, 255),
                stroke_width=6, stroke_fill=(10, 8, 6, 255))
        y += lh
    return np.asarray(lay, np.float32)


def zoom_region(region, t):
    """İlk 0,8 sn: %14 yakından başlayıp normale inen hızlı zoom (kalıp kırma)."""
    if t >= ZOOM_SURE:
        return region
    k = 1 - (1 - t / ZOOM_SURE) ** 3
    z = 1.14 - 0.14 * k
    h, w = region.shape[:2]
    ch, cw = int(h / z), int(w / z)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    crop = Image.fromarray(region[y0:y0 + ch, x0:x0 + cw].clip(0, 255).astype(np.uint8))
    return np.asarray(crop.resize((w, h), Image.BILINEAR), np.float32)


def _sar(d, metin, f, maxw):
    return _kanca_sar(d, metin, f, maxw)


def end_card(ep, k):
    """Seçim varsa A/B kartı ("SEN OLSAN NE YAPARDIN?"), yoksa dizi finali kartı."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    a = max(0.0, min(1.0, k))
    c = lambda col: tuple(int(v * a) for v in col)  # noqa: E731
    secim = ep.get("secim")
    if secim:
        f1 = font(70)
        t1 = "SEN OLSAN NE YAPARDIN?"
        while d.textlength(t1, font=f1) > W - 80:
            f1 = font(f1.size - 4)
        d.text(((W - d.textlength(t1, font=f1)) / 2, 420), t1, font=f1, fill=c(WHITE))
        y = 600
        for harf in ("A", "B"):
            f2 = font(52)
            lines = _sar(d, secim[harf], f2, W - 330)[:3]
            bh = 70 * len(lines) + 70
            renk = RED if harf == "A" else (70, 110, 200)
            d.rounded_rectangle([90, y, W - 90, y + bh], 30, outline=c(renk), width=6, fill=c((14, 14, 18)))
            fh = font(96)
            d.text((130, y + bh / 2 - 62), harf, font=fh, fill=c(renk))
            yy = y + 35
            for ln in lines:
                d.text((260, yy), ln, font=f2, fill=c(WHITE))
                yy += 70
            y += bh + 50
        f3 = font(46)
        t3 = "Yorumlara A ya da B yaz"
        d.text(((W - d.textlength(t3, font=f3)) / 2, y + 30), t3, font=f3, fill=c(WHITE))
        f4 = font(38)
        t4 = "En çok seçilen yol yarın gerçek olacak"
        d.text(((W - d.textlength(t4, font=f4)) / 2, y + 100), t4, font=f4, fill=c((170, 172, 185)))
    else:
        t1 = ep.get("son_kart", "SON MOLA")
        f1 = font(84)
        d.text(((W - d.textlength(t1, font=f1)) / 2, 760), t1, font=f1, fill=c(RED))
        f2 = font(46)
        t2 = ep.get("son_alt", "Yeni hikâye yarın akşam")
        d.text(((W - d.textlength(t2, font=f2)) / 2, 890), t2, font=f2, fill=c(WHITE))
    f3 = font(42)
    d.text(((W - d.textlength(HANDLE, font=f3)) / 2, 1560), HANDLE, font=f3, fill=c((150, 152, 165)))
    return np.asarray(im, np.float32)


# --------------------------------------------------------------------------
# Telefon ekranı (19 Kasım): sahnede "telefon" alanı varsa çizimin üstüne telefon gelir.
#   "telefon": {"baslik": "Apartman Sakinleri", "alt": "24 kişi",
#               "mesajlar": [{"kim": "Kapıcı", "metin": "Kimse kapısını açmasın."}, {"ben": true, "metin": "Ne oldu?"}],
#               "bildirim": "Bilinmeyen numara: Arkana bakma."}   (bildirim tek başına da olabilir)
# Mesajlar sahne süresine yayılarak tek tek belirir. Telefon sahne başında aşağıdan kayarak gelir.
# --------------------------------------------------------------------------
PH_W, PH_H = 700, 940


def _metin_sar(d, metin, f, maxw):
    satir, cur = [], ""
    for w in metin.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > maxw and cur:
            satir.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        satir.append(cur)
    return satir


class Telefon:
    def __init__(self, spec):
        self.spec = spec
        self.msgs = spec.get("mesajlar", [])
        self.cache = {}

    def layer(self, n, bildirim_a):
        key = (n, round(bildirim_a, 1))
        if key in self.cache:
            return self.cache[key]
        im = Image.new("RGBA", (PH_W + 40, PH_H + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 20, PH_W + 20, PH_H + 20], 70, fill=(8, 8, 10, 255), outline=(60, 62, 70, 255), width=6)
        x0, y0, x1, y1 = 44, 44, PH_W - 4, PH_H - 4
        d.rounded_rectangle([x0, y0, x1, y1], 52, fill=(17, 27, 33, 255))
        d.rounded_rectangle([x0, y0, x1, y0 + 120], 52, fill=(31, 44, 52, 255))
        d.rectangle([x0, y0 + 70, x1, y0 + 120], fill=(31, 44, 52, 255))
        d.text((x0 + 40, y0 + 20), "03:12", font=font(26), fill=(220, 220, 225, 255))
        if self.spec.get("baslik"):
            d.ellipse([x0 + 30, y0 + 58, x0 + 82, y0 + 110], fill=(90, 96, 110, 255))
            d.text((x0 + 100, y0 + 54), self.spec["baslik"][:26], font=font(32), fill=(240, 240, 244, 255))
            if self.spec.get("alt"):
                d.text((x0 + 100, y0 + 90), self.spec["alt"][:40], font=font(20), fill=(150, 160, 170, 255))
        y = y0 + 150
        fm, fk = font(30), font(22)
        bloklar = []
        for m in self.msgs[:n]:
            ben = m.get("ben")
            lines = _metin_sar(d, m["metin"], fm, PH_W - 230)
            h = 40 * len(lines) + (70 if not ben and m.get("kim") else 40)
            bloklar.append((m, lines, h))
        toplam = sum(h + 18 for _, _, h in bloklar)
        alan = (y1 - 40) - y
        if toplam > alan:          # eski mesajlar yukarı kayar
            y -= toplam - alan
        for m, lines, h in bloklar:
            ben = m.get("ben")
            bw = max(d.textlength(ln, font=fm) for ln in lines) + 50
            if not ben and m.get("kim"):
                bw = max(bw, d.textlength(m["kim"], font=fk) + 50)
            bx = x1 - 30 - bw if ben else x0 + 30
            if y + h > y0 + 130:
                d.rounded_rectangle([bx, y, bx + bw, y + h], 22,
                                    fill=(0, 92, 75, 255) if ben else (32, 44, 51, 255))
                yy = y + 14
                if not ben and m.get("kim"):
                    d.text((bx + 24, yy), m["kim"], font=fk, fill=m.get("renk_rgba", (233, 113, 90, 255)))
                    yy += 32
                for ln in lines:
                    d.text((bx + 24, yy), ln, font=fm, fill=(236, 238, 240, 255))
                    yy += 40
            y += h + 18
        d.rectangle([0, 0, PH_W + 40, 20], fill=(0, 0, 0, 0))
        if self.spec.get("bildirim") and bildirim_a > 0:
            a = int(255 * bildirim_a)
            fb = font(30)
            lines = _metin_sar(d, self.spec["bildirim"], fb, PH_W - 120)[:3]
            bh = 44 * len(lines) + 40
            d.rounded_rectangle([x0 + 16, y0 + 130, x1 - 16, y0 + 130 + bh], 26, fill=(235, 235, 240, a))
            yy = y0 + 150
            for ln in lines:
                d.text((x0 + 44, yy), ln, font=fb, fill=(20, 20, 24, a))
                yy += 44
        arr = np.asarray(im, np.float32)
        self.cache[key] = arr
        return arr

    def ciz(self, frame, t0, dur, t):
        """Sahne başlangıcı t0, süresi dur; t anındaki telefonu kareye bindirir."""
        e = t - t0
        if e < 0:
            return
        gir = min(1.0, e / 0.45)
        gir = 1 - (1 - gir) ** 3
        n = len(self.msgs)
        if n:
            adim = max(0.6, (dur - 0.6) / n)
            goster = min(n, 1 + int(max(0.0, e - 0.35) / adim))
        else:
            goster = 0
        b_a = 0.0
        if self.spec.get("bildirim"):
            bt = 0.5 if not n else max(0.5, dur * 0.6)
            b_a = max(0.0, min(1.0, (e - bt) / 0.3))
        lay = self.layer(goster, b_a)
        h, w = lay.shape[:2]
        x = (W - w) // 2
        y = int(IMG_Y + 150 + (1 - gir) * 900)
        y2 = min(H, y + h)
        if y2 <= y:
            return
        sub = lay[: y2 - y]
        al = sub[..., 3:4] / 255
        frame[y:y2, x:x + w] = frame[y:y2, x:x + w] * (1 - al) + sub[..., :3] * al


# --------------------------------------------------------------------------
# Ana akış
# --------------------------------------------------------------------------
def plan(durs):
    starts, t = [], LEAD
    for d in durs:
        starts.append(t)
        t += d + GAP
    return starts, round(t + 0.6, 2)


def render_episode(ep_path, img_dir, out):
    from .motion import SceneMotion
    ep = json.load(open(ep_path, encoding="utf-8"))
    work = os.path.join(os.path.dirname(os.path.abspath(out)), "work_" + ep["id"])
    os.makedirs(work, exist_ok=True)
    sc = ep["scenes"]
    parts = S.seslendir([s.get("say", s["text"]) for s in sc], work)
    starts, speech_end = plan([d for _, d in parts])
    total = speech_end + END
    audio = os.path.join(work, "audio.wav")
    S.birlestir(parts, starts, total, audio, work, sting_at=max(1.0, speech_end - 1.4), seed=int(ep.get("seed", 7)) % 100000 + 7)
    print(f"Süre: {total:.1f} sn", flush=True)

    hdr = header(ep)
    klay = kanca_layer(kanca_metni(ep))
    kbit = max(2.2, min(KANCA_SURE, starts[0] + parts[0][1]))
    emask, vig = edge_mask()
    gr = grains()
    fog = Fog()
    prepared = []
    for i, (s, st, (_, d)) in enumerate(zip(sc, starts, parts)):
        img = os.path.join(img_dir, f"sahne{i + 1}.png")
        mot = SceneMotion(img, s.get("prompt", ""), W, IMG_H, seed=i + 1)
        p = (s.get("prompt", "") or "").lower()
        sis = s.get("sis", 0.35 if any(k in p for k in ("fog", "mist", "haze")) else 0.12)
        prepared.append({"t": 0.0 if i == 0 else st - 0.3, "mot": mot, "sis": sis, "sicak": s.get("sicak", False),
                         "caps": chunks(word_times(s["text"], st, d)),
                         "tag": tag_layer(s["yer"]) if s.get("yer") else None,
                         "tel": Telefon(s["telefon"]) if s.get("telefon") else None, "st": st, "dur": d})
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for fi in range(n):
        t = fi / FPS
        if t >= speech_end:
            k = (t - speech_end) / 0.8
            ff.stdin.write(end_card(ep, k).clip(0, 255).astype(np.uint8).tobytes())
            continue
        idx = max(i for i, p in enumerate(prepared) if p["t"] <= t)
        frame = hdr.copy()
        region = np.zeros((IMG_H, W, 3), np.float32)
        layers = []
        if idx > 0 and t - prepared[idx]["t"] < FADE:
            layers.append((idx - 1, 1.0))
            layers.append((idx, (t - prepared[idx]["t"]) / FADE))
        else:
            layers.append((idx, 1.0))
        for j, a in layers:
            p = prepared[j]
            nxt = prepared[j + 1]["t"] if j + 1 < len(prepared) else speech_end
            img = grade(p["mot"].frame(t - p["t"], (t - p["t"]) / max(0.5, nxt - p["t"] + FADE)), p["sicak"])
            if p["sis"] > 0:
                fa = fog.alpha(t, p["sis"])
                img = img * (1 - fa) + np.array([150, 156, 168], np.float32) * fa
            region = region * (1 - a) + img * a
        flick = 0.97 + 0.03 * math.sin(t * 9.1) * math.sin(t * 3.7)
        region = region * vig * flick + gr[fi % len(gr)]
        region = zoom_region(region, t)
        frame[IMG_Y:IMG_Y + IMG_H] = frame[IMG_Y:IMG_Y + IMG_H] * (1 - emask) + region * emask
        cur = prepared[idx]
        if cur["tag"] is not None:
            ta = min(1.0, max(0.0, (t - cur["t"] - 0.2) / 0.4))
            th, tw = cur["tag"].shape[:2]
            sub = frame[IMG_Y + 40:IMG_Y + 40 + th, 40:40 + tw]
            al = cur["tag"][..., 3:4] / 255 * ta
            frame[IMG_Y + 40:IMG_Y + 40 + th, 40:40 + tw] = sub * (1 - al) + cur["tag"][..., :3] * al
        if cur.get("tel") is not None:
            cur["tel"].ciz(frame, cur["t"] + 0.1, cur["dur"] + (cur["st"] - cur["t"]), t)
        for ch in ([] if (klay is not None and t < kbit - 0.3) else cur["caps"]):
            if ch[0][1] - 0.05 <= t <= ch[-1][2] + 0.2:
                hi = max([i for i, (_, s0, _) in enumerate(ch) if s0 <= t] or [0])
                paste(frame, caption_layer(ch, hi), CAP_Y)
                break
        if klay is not None and t < kbit:
            paste(frame, klay, IMG_Y + int(IMG_H * 0.36), min(1.0, (kbit - t) / 0.3))
        ff.stdin.write(frame.clip(0, 255).astype(np.uint8).tobytes())
        if fi % 300 == 0:
            print(f"  kare {fi}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print(f"Hazır: {out} ({total:.1f} sn)")


if __name__ == "__main__":
    render_episode(sys.argv[1], sys.argv[2], sys.argv[3])
