"""Zaman Durağı ses katmanı — tamamen sentetik (telifsiz):
hüzünlü piyano (La minör), duvar saati tik-takı (son dönemde durur), soba çıtırtısı, final tek nota."""
import json
import subprocess
import sys
import wave

import numpy as np

SR = 44100
NOTA = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(ad):
    n, o = ad[:-1], int(ad[-1])
    return 440.0 * 2 ** ((NOTA[n] + 12 * (o + 1) - 69) / 12)


def piyano(f, sure, hiz=1.0, rng=None):
    """Basit fiziksel-ilhamlı piyano: harmonikler, farklı sönümler, hafif detune, keçe vuruşu."""
    n = int(SR * sure)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for h, a in [(1, 1.0), (2, 0.42), (3, 0.2), (4, 0.11), (5, 0.06), (6, 0.03)]:
        fh = f * h * (1 + 0.0004 * h * h)
        sonum = np.exp(-t * (1.1 + 0.9 * h) * (f / 440) ** 0.35)
        det = 1 + (rng.uniform(-0.0008, 0.0008) if rng is not None else 0)
        s += a * sonum * (np.sin(2 * np.pi * fh * t) + 0.6 * np.sin(2 * np.pi * fh * det * t + 0.3))
    atak = np.minimum(1, t / 0.006)
    keçe = np.exp(-t * 60) * np.random.default_rng(int(f)).normal(0, 0.05, n)
    return (s * atak + keçe) * hiz


def ekle(buf, sig, t0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def uret(bolum, cikti):
    B = json.load(open(bolum, encoding="utf-8"))
    fps = B.get("fps", 30)
    T = B["kare"] / fps
    son_t = next((d["bas"] for d in B["donemler"] if d.get("son")), B["kare"]) / fps
    rng = np.random.default_rng(3)
    N = int(SR * (T + 0.5))
    muz = np.zeros(N)
    # La minör hüzün döngüsü: Am - F - C - G (son dönemde Am - F - Dm - E)
    akor1 = [["A2", "E3", "A3", "C4"], ["F2", "C3", "F3", "A3"], ["C3", "G3", "C4", "E4"], ["G2", "D3", "G3", "B3"]]
    akor2 = [["A2", "E3", "A3", "C4"], ["F2", "C3", "F3", "A3"], ["D2", "A2", "D3", "F3"], ["E2", "B2", "E3", "G#3"]]
    ezgi1 = [["E5", "", "C5", "D5"], ["C5", "", "A4", ""], ["G4", "", "E5", "D5"], ["D5", "", "B4", ""]]
    ezgi2 = [["C5", "", "", "B4"], ["A4", "", "", ""], ["F4", "", "A4", ""], ["G#4", "", "", ""]]
    bpm = 68
    vurus = 60 / bpm
    t = 0.25
    olcu = 0
    while t < T - 1.5:
        son = t >= son_t
        ak = (akor2 if son else akor1)[olcu % 4]
        ez = (ezgi2 if son else ezgi1)[olcu % 4]
        sira = [0, 1, 2, 3, 2, 1, 2, 3]  # arpej (sekizlik)
        for k, i in enumerate(sira):
            nt = t + k * vurus / 2 + rng.uniform(0, 0.012)
            ekle(muz, piyano(hz(ak[i]), 3.2, (0.42 if k == 0 else 0.27) * (0.8 if son else 1), rng), nt)
        for k, nn in enumerate(ez):
            if nn and (not son or k == 0 or olcu % 2 == 1):
                ekle(muz, piyano(hz(nn), 3.5, 0.33, rng), t + k * vurus + rng.uniform(0, 0.015))
        t += 4 * vurus
        olcu += 1
    # final: tek, uzun La notası
    ekle(muz, piyano(hz("A4"), 5.0, 0.4, rng) + piyano(hz("A3"), 5.0, 0.3, rng), T - 1.6)

    # saat tik-tak (son dönemde yavaşlayıp durur)
    ortam = np.zeros(N)
    tk = 0.5
    aralik = 0.5
    i = 0
    while tk < T:
        if tk > son_t:
            aralik *= 1.18
            if tk > son_t + 1.6:
                break
        n = int(SR * 0.03)
        tt = np.arange(n) / SR
        frek = 2600 if i % 2 == 0 else 2150
        klik = np.sin(2 * np.pi * frek * tt) * np.exp(-tt * 260) + rng.normal(0, 0.25, n) * np.exp(-tt * 500)
        ekle(ortam, klik * 0.16, tk)
        tk += aralik
        i += 1
    # soba çıtırtısı (soba olan dönemlerde)
    for d in B["donemler"]:
        if "soba" in d["esyalar"]:
            a, b = d["bas"] / fps, d["bit"] / fps
            for _ in range(int((b - a) * 7)):
                n = int(SR * 0.012)
                ekle(ortam, rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 400) * rng.uniform(0.02, 0.08), rng.uniform(a, b))
    # oda tonu (çok hafif uğultu)
    ortam += np.convolve(rng.normal(0, 1, N), np.ones(400) / 400, mode="same") * 0.05

    def yaz(ad, x):
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.8
        with wave.open(ad, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((x * 32767).astype(np.int16).tobytes())

    yaz(cikti + ".muz.wav", muz)
    yaz(cikti + ".ort.wav", ortam)
    # piyanoya oda yankısı, ortamla karıştır, yüksek sesi standartlaştır
    _karistir(cikti, T)


def _karistir(cikti, T):
    import os
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", cikti + ".muz.wav", "-i", cikti + ".ort.wav", "-filter_complex",
                    "[0]aecho=0.8:0.75:70|140|280|430:0.35|0.25|0.18|0.12,lowpass=f=6500,volume=1.0[m];"
                    "[1]volume=0.55[o];[m][o]amix=inputs=2:normalize=0,afade=t=out:st=%.2f:d=1.2,"
                    "loudnorm=I=-15:TP=-1.5:LRA=9,aformat=channel_layouts=stereo" % (T - 1.2),
                    "-t", "%.3f" % T, "-ar", str(SR), cikti], check=True)
    for e in (".muz.wav", ".ort.wav"):
        os.remove(cikti + e)


if __name__ == "__main__":
    uret(sys.argv[1], sys.argv[2])
