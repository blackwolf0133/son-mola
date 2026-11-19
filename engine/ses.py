"""Kayıp Vakalar seslendirme + gerilim müziği.
Gemini TTS (bölüm başına TEK istek, sahnelere bölünür). Gemini olmazsa bölümün tamamı Piper ile okunur
(yarım yamalak karışık ses olmaz). Müzik tamamen sentetik (telifsiz) karanlık bir uğultu."""
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPO = float(os.environ.get("GEMINI_TEMPO", "1.0"))
MUSIC_VOL = float(os.environ.get("MUSIC_VOL", "0.32"))
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,")
FILTERS = ("highpass=f=70,lowpass=f=11500,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,"
           "loudnorm=I=-16:TP=-1.5:LRA=7")
PIPER = os.environ.get("PIPER_MODEL", os.path.join(ROOT, "models", "tr_TR-fahrettin-medium.onnx"))


def temiz(text):
    from .numbers import seslendirme_metni
    t = text.replace("\n", " ").replace('"', "").replace("“", "").replace("”", "")
    return seslendirme_metni(" ".join(t.split()))


def sure(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def _isle(raw_args, dst):
    af = TRIM + (f"atempo={TEMPO}," if abs(TEMPO - 1) > 0.01 else "") + FILTERS
    subprocess.run(["ffmpeg", "-v", "error", "-y", *raw_args, "-af", af, "-ar", str(SR), "-ac", "1", dst], check=True)


def _gemini(metinler, workdir):
    from . import gemini_ses
    a24, _ = gemini_ses.seslendir(metinler)
    out = []
    for i, part in enumerate(gemini_ses.bol(a24, 24000, metinler), 1):
        raw = os.path.join(workdir, f"v{i}.pcm")
        (np.clip(part, -1, 1) * 32767).astype("<i2").tofile(raw)
        dst = os.path.join(workdir, f"v{i}.wav")
        _isle(["-f", "s16le", "-ar", "24000", "-ac", "1", "-i", raw], dst)
        os.remove(raw)
        out.append((dst, sure(dst)))
    return out


def _piper(metinler, workdir):
    out = []
    for i, m in enumerate(metinler, 1):
        raw = os.path.join(workdir, f"p{i}.wav")
        subprocess.run([sys.executable, "-m", "piper", "-m", PIPER, "-f", raw, "--sentence-silence", "0.25"],
                       input=m.encode(), check=True, capture_output=True)
        dst = os.path.join(workdir, f"v{i}.wav")
        _isle(["-i", raw], dst)
        out.append((dst, sure(dst)))
    return out


def sessiz(metinler, workdir):
    """Yerel önizleme: metin uzunluğunda sessizlik."""
    out = []
    for i, m in enumerate(metinler, 1):
        dst = os.path.join(workdir, f"v{i}.wav")
        yaz(dst, np.zeros(int(SR * max(1.5, len(m) * 0.062)), np.float32))
        out.append((dst, sure(dst)))
    return out


def seslendir(satirlar, workdir):
    os.makedirs(workdir, exist_ok=True)
    metinler = [temiz(s) for s in satirlar]
    motor = os.environ.get("TTS_ENGINE", "gemini")
    if motor == "sessiz":
        return sessiz(metinler, workdir)
    if motor == "gemini" and os.environ.get("GEMINI_API_KEY"):
        try:
            return _gemini(metinler, workdir)
        except Exception as e:  # noqa: BLE001
            print(f"::warning::Gemini sesi alınamadı, bölümün tamamı yedek sesle okunacak: {e}", flush=True)
    return _piper(metinler, workdir)


# --------------------------------------------------------------------------
# Gerilim müziği (sentetik)
# --------------------------------------------------------------------------
def drone(seconds, sr=SR, seed=4, sting_at=None):
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    t = np.arange(n) / sr
    out = np.zeros(n, np.float32)
    for f, a in ((49.0, 0.5), (49.6, 0.4), (24.5, 0.35), (73.4, 0.14), (103.8, 0.06)):
        lfo = 0.7 + 0.3 * np.sin(2 * np.pi * rng.uniform(0.03, 0.09) * t + rng.uniform(0, 6))
        out += (a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * lfo).astype(np.float32)
    noise = rng.normal(0, 1, n).astype(np.float32)
    k = int(sr * 0.004)
    wind = np.convolve(noise, np.ones(k, np.float32) / k, mode="same")
    wind *= (0.5 + 0.5 * np.sin(2 * np.pi * 0.06 * t) ** 2).astype(np.float32)
    out += wind * 0.55
    for _ in range(max(1, int(seconds / 12))):
        s = rng.uniform(2, max(3, seconds - 4))
        i0 = int(s * sr)
        d = np.arange(int(sr * 3.5)) / sr
        ping = (0.11 * np.sin(2 * np.pi * rng.choice([277.2, 311.1, 369.9]) * d) * np.exp(-d * 1.3)).astype(np.float32)
        e = min(n, i0 + len(ping))
        out[i0:e] += ping[: e - i0]
    if sting_at is not None:
        i0 = int(sting_at * sr)
        d = np.arange(int(sr * 2.2)) / sr
        sweep = np.sin(2 * np.pi * (70 + 280 * d ** 2) * d) * (d / 2.2) ** 2 * 0.6
        m = int(sr * 0.25)
        hit = np.zeros_like(d)
        hit[-m:] = rng.normal(0, 1, m) * np.exp(-np.arange(m) / (sr * 0.05))
        seg = (sweep + hit * 0.7).astype(np.float32)
        e = min(n, i0 + len(seg))
        if e > i0:
            out[i0:e] += seg[: e - i0]
    out *= np.minimum(1, t / 2.0).astype(np.float32)
    return out / (np.abs(out).max() + 1e-6)


def acilis_sesi(sr=SR, seed=11):
    """0. saniye ürperti (14 Kasım, kullanıcı isteği): derinden boom + uyumsuz tını + yükselen fısıltı/rüzgâr.
    ~2,6 sn; anlatıcının altında kalacak kadar alçak ve çoğu alçak frekansta."""
    rng = np.random.default_rng(seed)
    n = int(2.6 * sr)
    t = np.arange(n) / sr
    boom = 0.55 * np.sin(2 * np.pi * (52 - 14 * t) * t) * np.exp(-t * 2.2)
    kume = np.zeros(n)
    for f in (233.1, 246.9, 311.1):
        kume += np.sin(2 * np.pi * f * t + 0.004 * np.sin(2 * np.pi * 5.5 * t) * f)
    kume *= 0.07 * np.minimum(1, t / 0.5) * np.exp(-np.maximum(0, t - 0.6) * 1.4)
    g = rng.normal(0, 1, n)
    a, b = int(sr * 0.0006), int(sr * 0.004)
    bant = np.convolve(g, np.ones(a) / a, "same") - np.convolve(g, np.ones(b) / b, "same")
    fisilti = 0.9 * bant * (t / 2.0) ** 2 * (t < 2.0) + 0.9 * bant * np.exp(-(t - 2.0) * 9) * (t >= 2.0)
    out = (boom + kume + fisilti).astype(np.float32)
    out *= np.minimum(1, (2.6 - t) / 0.3).astype(np.float32)
    return 0.42 * out / (np.abs(out).max() + 1e-6)


def yaz(path, a, sr=SR):
    a = np.clip(a, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def oku(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def birlestir(parcalar, baslar, toplam, out_path, workdir, sting_at=None, seed=4):
    """Konuşmaları zamanlarına yerleştirir, altına gerilim müziği koyar (konuşurken kısılır)."""
    voice = np.zeros(int(toplam * SR) + SR, dtype=np.float32)
    for (path, _), st in zip(parcalar, baslar):
        a = oku(path)
        s = int(st * SR)
        voice[s:s + len(a)] += a[: len(voice) - s]
    voice = voice[: int(toplam * SR)]
    if os.environ.get("ACILIS_SESI", "1") == "1":  # 0. saniye ürperti sesi
        ac = acilis_sesi()
        voice[: len(ac)] += ac[: len(voice)]
    vw = os.path.join(workdir, "voice_full.wav")
    mw = os.path.join(workdir, "music.wav")
    yaz(vw, voice)
    yaz(mw, drone(toplam, SR, seed=seed, sting_at=sting_at))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vw, "-i", mw, "-filter_complex",
                    f"[1]lowpass=f=4000,volume={MUSIC_VOL},afade=t=in:d=1.5,"
                    f"afade=t=out:st={max(0.1, toplam - 1.5):.2f}:d=1.4[m];"
                    "[0]asplit=2[v][sc];"
                    "[m][sc]sidechaincompress=threshold=0.03:ratio=3:attack=80:release=600[md];"
                    "[v][md]amix=inputs=2:duration=first:normalize=0", "-ar", str(SR), out_path], check=True)
