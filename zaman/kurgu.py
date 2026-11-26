"""Zaman Durağı kurgu: render karelerini 1080x1920'e büyütür, yıl sayacı + zaman çizelgesi + serif yazılar
bindirir, ses katmanını ekler ve Instagram'a uygun mp4 üretir.

Akış (26 Kasım sürümü, izlenme süresi için):
  0.0-0.7 sn  KANCA: odanın SON hâli (terk edilmiş) + büyük soru yazısı
  0.7-1.6 sn  GERİ SAR: kareler tersine hızla akar (VHS kayması, ◀◀), yıl sayacı geriye döner
  sonra       asıl hikâye; her dönem geçişinde flaş + yakınlaşma vuruşu + "whoosh"
  alt-üst     yıl sayacı (altın), altında dönemleri gösteren ilerleme çizgisi
  son         son soru + "YORUMLARA YAZ"
Kullanım: python zaman/kurgu.py <bolum.json> <kare_klasoru> <cikti.mp4>"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from zaman import muzik  # noqa: E402

W, H = 1080, 1920
F_DUZ = os.path.join(ROOT, "fonts", "Lora-Variable.ttf")
F_ITA = os.path.join(ROOT, "fonts", "Lora-Italic-Variable.ttf")
KREM = (250, 243, 228)
ALTIN = (255, 207, 120)
BASLIK = os.environ.get("ZAMAN_BASLIK", "Z A M A N   D U R A Ğ I")
SR = 44100
KANCA_K = 21      # kanca karesi (durağan son hâl)
GERI_K = 27       # geri sarma
ON = KANCA_K + GERI_K


def font(yol, boy, agirlik="Regular"):
    f = ImageFont.truetype(yol, boy)
    try:
        f.set_variation_by_name(agirlik)
    except Exception:
        pass
    return f


def yazi_katmani(metin, fnt, satir_aralik=1.22, renk=KREM, golge=14, kutu=False):
    """Ortalanmış çok satırlı yazı + yumuşak gölge (+ isteğe bağlı koyu yarı saydam kutu); RGBA döner."""
    satirlar = metin.split("\n")
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * satir_aralik)
    gen = max(int(fnt.getlength(s)) for s in satirlar) + 120
    yuk = lh * len(satirlar) + 90
    lay = Image.new("RGBA", (gen, yuk), (0, 0, 0, 0))
    gol = Image.new("RGBA", (gen, yuk), (0, 0, 0, 0))
    d, g = ImageDraw.Draw(lay), ImageDraw.Draw(gol)
    if kutu:
        g.rounded_rectangle((18, 22, gen - 18, yuk - 18), radius=34, fill=(6, 6, 10, 150))
    for i, s in enumerate(satirlar):
        x = (gen - fnt.getlength(s)) / 2
        y = 42 + i * lh
        g.text((x, y + 4), s, font=fnt, fill=(0, 0, 0, 230))
        d.text((x, y), s, font=fnt, fill=(*renk, 255))
    gol = gol.filter(ImageFilter.GaussianBlur(golge if not kutu else 6))
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


def zarf(f, a, b, gir=10, cik=12, son_kare=None):
    if f < a or f > b:
        return 0.0
    v = kolay((f - a) / gir)
    if son_kare is None or b < son_kare:
        v = min(v, kolay((b - f) / cik))
    return v


def plan(B):
    """Ekranda hangi yazı ne zaman (asıl hikâye kareleri): [(metin, a, b, tür)]"""
    D = B["donemler"]
    out = [(B["kanca"], 1, 52, "kanca")]
    for i, d in enumerate(D):
        a = d["bas"] + (62 if i == 0 else 16)
        if d.get("son"):
            n = len(B.get("kapanis", []))
            dilim = (d["bit"] - a) // (n + 1)
            out.append((d["yazi"], a, a + dilim - 6, "alt"))
            for j, k in enumerate(B.get("kapanis", [])):
                s = a + dilim * (j + 1)
                out.append((k, s, d["bit"] if j == n - 1 else s + dilim - 6, "son" if j == n - 1 else "alt"))
        else:
            out.append((d["yazi"], a, d["bit"] - 20, "alt"))
    return out


def yil_degeri(B, f):
    D = B["donemler"]
    for i, d in enumerate(D):
        if d["bas"] <= f <= d["bit"]:
            if i == 0:
                return d["yil"], 1.0
            k = kolay((f - d["bas"]) / 20)
            onceki = D[i - 1]["yil"]
            return int(round(onceki + (d["yil"] - onceki) * k)), k
    return D[-1]["yil"], 1.0


def ilerleme(B, f):
    """0..len(D)-1 arası sürekli konum (çizelgedeki işaret)."""
    D = B["donemler"]
    for i, d in enumerate(D):
        if d["bas"] <= f <= d["bit"]:
            if i == 0:
                return 0.0
            return i - 1 + kolay((f - d["bas"]) / 20)
    return len(D) - 1.0


# ------------------------------------------------------------------ ses
def _oku(yol):
    with wave.open(yol) as w:
        n, ch = w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32767
    return x.reshape(-1, ch).mean(axis=1) if ch > 1 else x


def _yaz(yol, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], axis=1)
    with wave.open(yol, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def _lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def ses_kur(B, ses, cikti, fps):
    rng = np.random.default_rng(7)
    muz = _oku(ses)
    on_t = ON / fps
    N = int(SR * (on_t + B["kare"] / fps)) + SR // 2
    out = np.zeros(N, dtype=np.float32)
    i0 = int(on_t * SR)
    out[i0:i0 + len(muz)] += muz[:N - i0]
    # 0. sn: alçak darbe (dikkat)
    n = int(SR * 0.9)
    t = np.arange(n) / SR
    out[:n] += (np.sin(2 * np.pi * 52 * t) * np.exp(-t * 4.5) * 0.55 + _lp(rng.normal(0, 1, n), 30) * np.exp(-t * 18) * 0.25)
    # geri sarma: hızlanan bant sesi
    a = int(KANCA_K / fps * SR)
    n = int(GERI_K / fps * SR) + int(0.12 * SR)
    t = np.arange(n) / SR
    frek = 300 + 2400 * (t / t[-1]) ** 1.6
    faz = 2 * np.pi * np.cumsum(frek) / SR
    bant = (np.sin(faz) * 0.18 + np.sign(np.sin(faz * 0.5)) * 0.05 + _lp(rng.normal(0, 1, n), 4) * 0.22)
    bant *= np.minimum(1, t / 0.04) * np.minimum(1, (t[-1] - t) / 0.06) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
    out[a:a + n] += bant * 0.7
    # dönem geçişleri: whoosh
    for d in B["donemler"][1:]:
        s = int((ON + d["bas"] - 9) / fps * SR)
        n = int(SR * 0.75)
        t = np.arange(n) / SR
        zr = np.exp(-((t - 0.3) / 0.13) ** 2)
        gur = rng.normal(0, 1, n)
        ws = (_lp(gur, 6) - _lp(gur, 60)) * zr * 0.5 + np.sin(2 * np.pi * (90 - 40 * t) * t) * zr * 0.2
        out[s:s + n] += ws[:max(0, min(n, N - s))]
    tmp = cikti + ".ham.wav"
    _yaz(tmp, out * 0.9)
    T = N / SR - 0.5
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=10,aformat=channel_layouts=stereo", "-t", "%.3f" % T,
                    "-ar", str(SR), cikti], check=True)
    os.remove(tmp)


# ------------------------------------------------------------------ görüntü efektleri
def vhs(im, guc, rng):
    """Geri sarma görünümü: kanal kayması + tarama çizgileri + bant bozulması."""
    r, g, b = im.convert("RGB").split()
    dx = int(6 + 14 * guc)
    r = ImageChops.offset(r, dx, 0)
    b = ImageChops.offset(b, -dx, 0)
    out = Image.merge("RGB", (r, g, b))
    d = ImageDraw.Draw(out, "RGBA")
    for y in range(0, H, 6):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 55))
    for _ in range(3):
        y = int(rng.uniform(0, H))
        h = int(rng.uniform(10, 40))
        bant = out.crop((0, y, W, y + h))
        out.paste(bant, (int(rng.uniform(-40, 40)), y))
        d.rectangle((0, y, W, y + 2), fill=(255, 255, 255, 60))
    return out.convert("RGBA")


def geri_isareti(im, alfa):
    d = ImageDraw.Draw(im, "RGBA")
    cx, cy = 150, 1700
    a = int(230 * alfa)
    for k in range(2):
        x = cx + k * 46
        d.polygon([(x, cy), (x + 46, cy - 30), (x + 46, cy + 30)], fill=(255, 255, 255, a))
    f = font(F_DUZ, 40, "Bold")
    d.text((cx + 115, cy - 26), "GERİ SAR", font=f, fill=(255, 255, 255, a))


def kurgula(bolum, kareler, cikti):
    B = json.load(open(bolum, encoding="utf-8"))
    FR = B["kare"]
    fps = B.get("fps", 30)
    D = B["donemler"]
    ham = cikti + ".muz.wav"
    muzik.uret(bolum, ham)
    ses = cikti + ".ses.wav"
    ses_kur(B, ham, ses, fps)
    os.remove(ham)

    f_ust = font(F_DUZ, 30, "SemiBold")
    f_yil = font(F_DUZ, 196, "Bold")
    f_cz = font(F_DUZ, 30, "SemiBold")
    f_alt = font(F_ITA, 62, "SemiBold Italic")
    f_kanca = font(F_DUZ, 84, "Bold")
    f_son = font(F_DUZ, 68, "Bold")
    f_cta = font(F_DUZ, 46, "Bold")
    ust = yazi_katmani(BASLIK, f_ust, renk=(240, 228, 205), golge=8)
    cta = yazi_katmani("Y O R U M L A R A   Y A Z", f_cta, renk=ALTIN, golge=10)
    cache = {}

    def lay(metin, tur):
        if (metin, tur) not in cache:
            fn = {"kanca": f_kanca, "alt": f_alt, "son": f_son}[tur]
            cache[(metin, tur)] = yazi_katmani(metin, fn, golge=16, kutu=(tur == "alt"))
        return cache[(metin, tur)]

    yil_cache = {}

    def yil_lay(y):
        if y not in yil_cache:
            yil_cache[y] = yazi_katmani(str(y), f_yil, renk=ALTIN, golge=22)
        return yil_cache[y]

    P = plan(B)
    perde = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(perde)
    for y in range(0, 520):
        pd.line([(0, y), (W, y)], fill=(6, 6, 10, int(150 * (1 - y / 520) ** 1.5)))
    for y in range(1280, H):
        pd.line([(0, y), (W, y)], fill=(6, 6, 10, int(160 * ((y - 1280) / (H - 1280)) ** 1.3)))
    # çizelge: dönem noktaları
    X0, X1, CY = 190, 890, 455
    xs = [X0 + (X1 - X0) * i / max(1, len(D) - 1) for i in range(len(D))]
    cizelge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cizelge)
    cd.line([(X0, CY), (X1, CY)], fill=(250, 243, 228, 110), width=4)
    for x, d in zip(xs, D):
        cd.ellipse((x - 8, CY - 8, x + 8, CY + 8), fill=(250, 243, 228, 160))
        s = str(d["yil"])
        cd.text((x - f_cz.getlength(s) / 2 + 1, CY + 22 + 2), s, font=f_cz, fill=(0, 0, 0, 160))
        cd.text((x - f_cz.getlength(s) / 2, CY + 22), s, font=f_cz, fill=(250, 243, 228, 200))

    def cizelge_ciz(im, konum, alfa=1.0):
        im.alpha_composite(cizelge if alfa >= 0.99 else Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)), cizelge, alfa))
        i = int(min(konum, len(D) - 1.001))
        x = xs[i] + (xs[min(i + 1, len(D) - 1)] - xs[i]) * (konum - i)
        d = ImageDraw.Draw(im, "RGBA")
        d.line([(X0, CY), (x, CY)], fill=(*ALTIN, int(255 * alfa)), width=6)
        for j, xx in enumerate(xs):
            if xx <= x + 1:
                d.ellipse((xx - 9, CY - 9, xx + 9, CY + 9), fill=(*ALTIN, int(255 * alfa)))
        d.ellipse((x - 20, CY - 20, x + 20, CY + 20), fill=(*ALTIN, int(70 * alfa)))
        d.ellipse((x - 12, CY - 12, x + 12, CY + 12), fill=(255, 245, 220, int(255 * alfa)))

    def kare_yolu(f):
        p = os.path.join(kareler, f"{f:05d}.png")
        while not os.path.exists(p) and f > 1:
            f -= 1
            p = os.path.join(kareler, f"{f:05d}.png")
        return p

    def taban(f, olcek=1.0):
        im = Image.open(kare_yolu(f)).convert("RGB")
        if olcek > 1.001:
            w, h = im.size
            cw, ch = w / olcek, h / olcek
            im = im.crop(((w - cw) / 2, (h - ch) / 2, (w + cw) / 2, (h + ch) / 2))
        return im.resize((W, H), Image.LANCZOS).convert("RGBA")

    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
         "-i", ses, "-vf", "eq=saturation=1.12:contrast=1.04,vignette=angle=PI/5,noise=alls=3:allf=t",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", cikti], stdin=subprocess.PIPE)
    rng = np.random.default_rng(1)
    son_bas = next((d["bas"] for d in D if d.get("son")), FR)
    K_SON = son_bas + int((FR - son_bas) * 0.55)
    kanca = lay(B.get("kanca_geri", B["kanca"]), "kanca")
    ilk, son_yil = D[0]["yil"], D[-1]["yil"]

    # ---- 1) kanca: son hâl, durağan + hafif yakınlaşma
    for k in range(KANCA_K):
        im = taban(K_SON, 1.08 - 0.03 * k / KANCA_K)
        im.alpha_composite(perde)
        bindir(im, ust, W / 2, 150, 0.9)
        bindir(im, yil_lay(son_yil), W / 2, 300, 1.0, 1.0 + 0.12 * (1 - kolay(k / 6)))
        cizelge_ciz(im, len(D) - 1.0, 0.9)
        bindir(im, kanca, W / 2, 1540, kolay(k / 4), 1.0 + 0.08 * (1 - kolay(k / 6)))
        ff.stdin.write(im.convert("RGB").tobytes())
    # ---- 2) geri sar: kareler hızlanarak geriye
    for k in range(GERI_K):
        u = (k + 1) / GERI_K
        f = max(1, int(round(K_SON - (K_SON - 1) * u ** 1.35)))
        im = vhs(taban(f, 1.05), 1 - abs(0.5 - u) * 2 if u < 0.9 else 0.2, rng)
        im.alpha_composite(perde)
        bindir(im, ust, W / 2, 150, 0.9)
        y = int(round(son_yil - (son_yil - ilk) * u ** 1.35))
        bindir(im, yil_lay(y), W / 2, 300, 1.0)
        cizelge_ciz(im, (len(D) - 1) * (1 - u ** 1.35), 0.9)
        bindir(im, kanca, W / 2, 1540, 1.0)
        geri_isareti(im, 1.0 if (k // 4) % 2 == 0 else 0.55)
        ff.stdin.write(im.convert("RGB").tobytes())

    # ---- 3) asıl hikâye
    gecisler = [d["bas"] for d in D[1:]]
    for f in range(1, FR + 1):
        vur = 1.0
        flas = 0.0
        if f <= 8:
            flas = 0.55 * (1 - f / 8)
        for g in gecisler:
            if 0 <= f - g < 14:
                vur = 1.0 + 0.045 * (1 - kolay((f - g) / 14))
                flas = max(flas, 0.42 * (1 - (f - g) / 9)) if f - g < 9 else flas
        im = taban(f, vur)
        im.alpha_composite(perde)
        if flas > 0:
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 248, 235, int(255 * flas))))
        bindir(im, ust, W / 2, 150, 0.9)
        y, k = yil_degeri(B, f)
        pulse = 1.0 + 0.1 * (1 - k) if k < 1 else 1.0
        bindir(im, yil_lay(y), W / 2, 300, 1.0, pulse)
        cizelge_ciz(im, ilerleme(B, f))
        for metin, a, b, tur in P:
            al = zarf(f, a, b, son_kare=FR)
            if al > 0:
                cy = {"kanca": 1540, "alt": 1580, "son": 1540}[tur]
                kay = (1 - kolay((f - a) / 10)) * 22
                bindir(im, lay(metin, tur), W / 2, cy + kay, al)
                if tur == "son" and f - a > 12:
                    nab = 1.0 + 0.04 * np.sin((f - a) / 5.0)
                    bindir(im, cta, W / 2, 1745, kolay((f - a - 12) / 10), nab)
        ff.stdin.write(im.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    os.remove(ses)
    if ff.returncode:
        raise SystemExit("ffmpeg hata")


if __name__ == "__main__":
    kurgula(*sys.argv[1:4])
