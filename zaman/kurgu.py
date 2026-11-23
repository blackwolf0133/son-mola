"""Zaman Durağı kurgu: render karelerini 1080x1920'e büyütür, yıl sayacı + serif yazılar bindirir,
ses katmanını ekler ve Instagram'a uygun mp4 üretir.
Kullanım: python zaman/kurgu.py <bolum.json> <kare_klasoru> <cikti.mp4>"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from zaman import muzik  # noqa: E402

W, H = 1080, 1920
F_DUZ = os.path.join(ROOT, "fonts", "Lora-Variable.ttf")
F_ITA = os.path.join(ROOT, "fonts", "Lora-Italic-Variable.ttf")
KREM = (250, 243, 228)
BASLIK = os.environ.get("ZAMAN_BASLIK", "Z A M A N   D U R A Ğ I")


def font(yol, boy, agirlik="Regular"):
    f = ImageFont.truetype(yol, boy)
    try:
        f.set_variation_by_name(agirlik)
    except Exception:
        pass
    return f


def yazi_katmani(metin, fnt, satir_aralik=1.25, renk=KREM, golge=14):
    """Ortalanmış çok satırlı yazı + yumuşak gölge; kırpılmış RGBA döner."""
    satirlar = metin.split("\n")
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * satir_aralik)
    gen = max(int(fnt.getlength(s)) for s in satirlar) + 80
    yuk = lh * len(satirlar) + 80
    lay = Image.new("RGBA", (gen, yuk), (0, 0, 0, 0))
    gol = Image.new("RGBA", (gen, yuk), (0, 0, 0, 0))
    d, g = ImageDraw.Draw(lay), ImageDraw.Draw(gol)
    for i, s in enumerate(satirlar):
        x = (gen - fnt.getlength(s)) / 2
        y = 40 + i * lh
        g.text((x, y + 3), s, font=fnt, fill=(0, 0, 0, 190))
        d.text((x, y), s, font=fnt, fill=(*renk, 255))
    gol = gol.filter(ImageFilter.GaussianBlur(golge))
    return Image.alpha_composite(gol, lay)


def bindir(kare, lay, cx, cy, alfa=1.0, olcek=1.0):
    if alfa <= 0.01:
        return
    if abs(olcek - 1) > 0.005:
        lay = lay.resize((max(1, int(lay.width * olcek)), max(1, int(lay.height * olcek))), Image.LANCZOS)
    if alfa < 0.999:
        a = lay.getchannel("A").point(lambda v: int(v * alfa))
        lay = lay.copy()
        lay.putalpha(a)
    kare.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


def kolay(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def zarf(f, a, b, gir=14, cik=14, son_kare=None):
    """a..b arası görünürlük (yumuşak giriş/çıkış)."""
    if f < a or f > b:
        return 0.0
    v = kolay((f - a) / gir)
    if son_kare is None or b < son_kare:
        v = min(v, kolay((b - f) / cik))
    return v


def plan(B):
    """Ekranda hangi yazı ne zaman: [(metin, a, b, tür)]"""
    D = B["donemler"]
    out = [(B["kanca"], 1, 84, "kanca")]
    for i, d in enumerate(D):
        a = d["bas"] + (96 if i == 0 else 22)
        if d.get("son"):
            n = len(B.get("kapanis", []))
            dilim = (d["bit"] - a) // (n + 1)
            out.append((d["yazi"], a, a + dilim - 6, "alt"))
            for j, k in enumerate(B.get("kapanis", [])):
                s = a + dilim * (j + 1)
                out.append((k, s, d["bit"] if j == n - 1 else s + dilim - 6, "son" if j == n - 1 else "alt"))
        else:
            out.append((d["yazi"], a, d["bit"] - 26, "alt"))
    return out


def yil_degeri(B, f):
    D = B["donemler"]
    for i, d in enumerate(D):
        if d["bas"] <= f <= d["bit"]:
            if i == 0:
                return d["yil"], 1.0
            k = kolay((f - d["bas"]) / 26)
            onceki = D[i - 1]["yil"]
            return int(round(onceki + (d["yil"] - onceki) * k)), k
    return D[-1]["yil"], 1.0


def kurgula(bolum, kareler, cikti):
    B = json.load(open(bolum, encoding="utf-8"))
    FR = B["kare"]
    fps = B.get("fps", 30)
    ses = cikti + ".ses.wav"
    muzik.uret(bolum, ses)

    f_ust = font(F_DUZ, 30, "SemiBold")
    f_yil = font(F_DUZ, 168, "Bold")
    f_alt = font(F_ITA, 60, "Medium")
    f_kanca = font(F_DUZ, 76, "Bold")
    f_son = font(F_DUZ, 64, "Bold")
    ust = yazi_katmani(BASLIK, f_ust, renk=(240, 228, 205), golge=8)
    cache = {}

    def lay(metin, tur):
        if (metin, tur) not in cache:
            fn = {"kanca": f_kanca, "alt": f_alt, "son": f_son}[tur]
            cache[(metin, tur)] = yazi_katmani(metin, fn, golge=16)
        return cache[(metin, tur)]

    yil_cache = {}
    P = plan(B)
    # okunurluk için üst/alt hafif karartma
    perde = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(perde)
    for y in range(0, 460):
        pd.line([(0, y), (W, y)], fill=(10, 8, 14, int(105 * (1 - y / 460) ** 1.6)))
    for y in range(1300, H):
        pd.line([(0, y), (W, y)], fill=(10, 8, 14, int(125 * ((y - 1300) / (H - 1300)) ** 1.4)))
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
         "-i", ses, "-vf", "vignette=angle=PI/5.5,noise=alls=3:allf=t", "-c:v", "libx264", "-preset", "medium",
         "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", cikti], stdin=subprocess.PIPE)
    son_png = None
    for f in range(1, FR + 1):
        p = os.path.join(kareler, f"{f:05d}.png")
        if os.path.exists(p):
            son_png = p
        im = Image.open(son_png).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
        im.alpha_composite(perde)
        # üst başlık + yıl
        bindir(im, ust, W / 2, 150, 0.9)
        y, k = yil_degeri(B, f)
        if y not in yil_cache:
            yil_cache[y] = yazi_katmani(str(y), f_yil, golge=18)
        pulse = 1.0 + 0.06 * (1 - k) if k < 1 else 1.0
        bindir(im, yil_cache[y], W / 2, 290, 1.0, pulse)
        # alt yazılar
        for metin, a, b, tur in P:
            al = zarf(f, a, b, son_kare=FR)
            if al > 0:
                cy = {"kanca": 1540, "alt": 1580, "son": 1560}[tur]
                kay = (1 - kolay((f - a) / 14)) * 18
                bindir(im, lay(metin, tur), W / 2, cy + kay, al)
        ff.stdin.write(im.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    os.remove(ses)
    if ff.returncode:
        raise SystemExit("ffmpeg hata")


if __name__ == "__main__":
    kurgula(*sys.argv[1:4])
