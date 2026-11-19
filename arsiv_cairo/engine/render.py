"""SON MOLA - bölüm JSON'undan karanlık temalı dikey Reels videosu üretir."""
import json
import math
import os
import subprocess
import sys
import wave

import cairo
import numpy as np

from . import draw as D
from .draw import W, H, PX, PY, PW, PH
from . import props2 as P2
from . import sm as SM

FPS = 30
SR = 22050
SCENE_PAD = 0.45          # her sahnenin sesinden sonra bekleme (sn)
PUNCH = 0.22              # sahne girişindeki zoom süresi
END_CARD = 3.2            # kapanış kartı ("BÖLÜM N+1 · YARIN 20:00") süresi
SM_BACK = {"tabela", "kapi", "mont", "lamba", "far"}
_FOG = {"f": None}


# --------------------------------------------------------------------------
# Seslendirme
# --------------------------------------------------------------------------

def _piper(text, out_wav, voice_model, length_scale):
    subprocess.run(
        [sys.executable, "-m", "piper", "-m", voice_model, "-f", out_wav,
         "--length-scale", str(length_scale), "--sentence-silence", "0.25"],
        input=text.encode("utf-8"), check=True, capture_output=True)


def _trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    return a[max(0, idx[0] - 200): idx[-1] + 600]


_POCKET = {"tts": None, "voice": None}


def pocket_tts(text, out_wav, emotion=None):
    """pocket-tts-turkish ile seslendirme. VOICE_REF verilmişse o kişinin sesi klonlanır
    (kullanıcının kendi sesi), yoksa POCKET_VOICE hazır sesi kullanılır."""
    from pocket_tts_turkish import TurkishTTS, save_wav
    if _POCKET["tts"] is None:
        _POCKET["tts"] = TurkishTTS.from_pretrained(device="cpu")
        ref = os.environ.get("VOICE_REF", "")
        if ref and os.path.exists(ref):
            _POCKET["voice"] = _POCKET["tts"].voice_from_file(ref)
            print("Ses: kullanıcının kendi sesi (klon)")
        else:
            _POCKET["voice"] = os.environ.get("POCKET_VOICE", "male_1")
            print("Ses: hazır ses", _POCKET["voice"])
    t = _POCKET["tts"]
    kw = {"voice": _POCKET["voice"], "seed": 7}
    if emotion:
        kw["emotion"] = emotion
    raw = out_wav + ".raw.wav"
    save_wav(raw, t.generate(text, **kw), t.sample_rate)
    tempo = float(os.environ.get("VOICE_TEMPO", "1.0"))
    af = (f"atempo={tempo}," if abs(tempo - 1.0) > 0.01 else "") + \
        "highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=5:release=60,loudnorm=I=-16:TP=-1.5:LRA=6"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", out_wav], check=True)
    os.remove(raw)


_CB = {"m": None, "n": 0}
_CB_EX = {"şaşkın": 0.7, "mutlu": 0.65, "kızgın": 0.7, "sakin": 0.4, "üzgün": 0.45}


def chatterbox_tts(text, out_wav, emotion=None):
    """Chatterbox Multilingual (MIT) ile kullanıcının KENDİ sesinin klonu (VOICE_REF, 10 numaralı seçim)."""
    import torch, wave
    ref = os.environ.get("VOICE_REF", "")
    if not (ref and os.path.exists(ref)):
        raise RuntimeError("VOICE_REF yok")
    if _CB["m"] is None:
        _load = torch.load
        torch.load = lambda *a, **k: _load(*a, **{**k, "map_location": "cpu"})
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        _CB["m"] = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        print("Ses: Chatterbox, kullanıcının kendi sesi (klon)")
    m = _CB["m"]
    _CB["n"] += 1
    torch.manual_seed(7 + _CB["n"])
    ex = _CB_EX.get(emotion or "", float(os.environ.get("CB_EXAGGERATION", "0.5")))
    a = m.generate(text, language_id="tr", audio_prompt_path=ref, exaggeration=ex,
                   cfg_weight=float(os.environ.get("CB_CFG", "0.5"))).squeeze(0).numpy()
    raw = out_wav + ".raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(m.sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    tempo = float(os.environ.get("CB_TEMPO", "1.0"))
    af = (f"atempo={tempo}," if abs(tempo - 1.0) > 0.01 else "") + \
        "highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=5:release=60,loudnorm=I=-16:TP=-1.5:LRA=6"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", out_wav], check=True)
    os.remove(raw)



GEMINI_TON = ("Sosyal medyada izleyiciyi ilk saniyede yakalayan, enerjik ve meraklı bir Türk hikâye anlatıcısı "
              "gibi oku. Canlı tempo, heyecanlı ama doğal.")
_GEM = {"model": None, "dead": set()}


def _gem_models():
    """Önce bu bölümde çalışmış model, sonra sıradakiler; kotası dolanlar atlanır."""
    order = os.environ.get("GEMINI_TTS_MODELS",
                           "gemini-3.8-flash-lite-tts,gemini-3.1-flash-tts-preview,gemini-2.5-flash-preview-tts").split(",")
    order = [m.strip() for m in order if m.strip()]
    if _GEM["model"]:
        order = [_GEM["model"]] + [m for m in order if m != _GEM["model"]]
    return [m for m in order if m not in _GEM["dead"]]


_GEM_TON = {"şaşkın": " Sound genuinely surprised and amazed.", "sakin": " Sound calm and thoughtful.",
            "mutlu": " Sound happy and playful.", "üzgün": " Sound a little sad.", "kızgın": " Sound annoyed."}


def gemini_tts(text, out_wav, emotion=None):
    """Google Gemini TTS (GEMINI_API_KEY). Ses: GEMINI_VOICE (varsayılan Puck), ton yazıyla verilir."""
    import base64, time, urllib.error, urllib.request
    key = os.environ["GEMINI_API_KEY"]
    voice = os.environ.get("GEMINI_VOICE", "Puck")
    prompt = ("Read this Turkish text aloud like an energetic, curious storyteller who hooks a social media "
              "audience in the first second. Natural, fluent Istanbul Turkish, lively pace."
              + _GEM_TON.get(emotion or "", "") + "\n\n" + text)
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                           "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}).encode()
    pcm, last = None, None
    for model in _gem_models():
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    data=body, headers={"x-goog-api-key": key, "Content-Type": "application/json"})
                r = json.load(urllib.request.urlopen(req, timeout=90))
                pcm = base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
                if _GEM["model"] != model:
                    print(f"Gemini sesi: {model}", flush=True)
                _GEM["model"] = model          # bölümün geri kalanı aynı modelle (tutarlı ses)
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode()[:300]
                last = f"{model}: HTTP {e.code} {msg}"
                print(f"::warning::{last}", flush=True)
                if e.code == 429 and "quota" in msg.lower() and "minute" not in msg.lower():
                    _GEM["dead"].add(model)    # günlük kota dolu: bu çalıştırmada bir daha deneme
                    break
                if e.code in (429, 500, 503):
                    time.sleep(10 * (attempt + 1))
                    continue
                _GEM["dead"].add(model)
                break
            except (KeyError, IndexError, TimeoutError, urllib.error.URLError) as e:
                last = f"{model}: {e}"
                print(f"::warning::{last}", flush=True)
                time.sleep(3)
        if pcm:
            break
    if not pcm:
        raise RuntimeError(last)
    raw = out_wav + ".raw.pcm"
    open(raw, "wb").write(pcm)
    tempo = float(os.environ.get("GEMINI_TEMPO", "1.0"))
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,")
    af = trim + (f"atempo={tempo}," if abs(tempo - 1.0) > 0.01 else "") + \
        "highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=5:release=60,loudnorm=I=-16:TP=-1.5:LRA=6"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", raw,
                    "-af", af, "-ar", str(SR), "-ac", "1", out_wav], check=True)
    os.remove(raw)


def tts(text, out_wav, voice_model, length_scale=1.0, fx=None, emotion=None):
    """Seslendirme. TTS_ENGINE=chatterbox: kullanıcının sesi (Chatterbox klon); pocket: eski klon;
    değilse Piper. Hata olursa Piper'a düşer, paylaşım aksamaz."""
    from .numbers import seslendirme_metni
    text = seslendirme_metni(text)  # rakam / Roma rakamı / sıra sayısı -> yazı (tüm motorlar için)
    if os.environ.get("TTS_ENGINE") == "sessiz":  # yerel önizleme: metin uzunluğunda sessizlik
        n = int(SR * max(1.2, len(text) * 0.062))
        with wave.open(out_wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(np.zeros(n, np.int16).tobytes())
        return out_wav
    if os.environ.get("TTS_ENGINE") == "gemini":
        try:
            return gemini_tts(text, out_wav, emotion)
        except Exception as e:  # noqa: BLE001
            print(f"::warning::Gemini sesi çalışmadı, yedek sese geçiliyor: {e}")
            os.environ["TTS_ENGINE"] = "chatterbox" if os.path.exists(os.environ.get("VOICE_REF", "/yok")) else "piper"
    if os.environ.get("TTS_ENGINE") == "chatterbox":
        try:
            return chatterbox_tts(text, out_wav, emotion)
        except Exception as e:  # noqa: BLE001
            print(f"::warning::Chatterbox çalışmadı, Piper'a geçiliyor: {e}")
            os.environ["TTS_ENGINE"] = "piper"
    if os.environ.get("TTS_ENGINE") == "pocket":
        try:
            return pocket_tts(text, out_wav, emotion)
        except Exception as e:  # noqa: BLE001
            print(f"::warning::Pocket TTS çalışmadı, Piper'a geçiliyor: {e}")
            os.environ["TTS_ENGINE"] = "piper"
    return piper_tts(text, out_wav, voice_model, length_scale, fx)


def piper_tts(text, out_wav, voice_model, length_scale=1.0, fx=None):
    """Piper ile Türkçe seslendirme - sabit tonlu, titremesiz ayar.
    - Sayılar yazıya çevrilir ve cümle TEK seferde okunur (ton kopukluğu olmaz)
    - noise_scale / noise_w düşük: her cümle aynı tonda, dalgalanmasız
    - Karikatür tınısı: perde, zaman-esnetme yapılmadan yeniden örnekleme ile yükseltilir
      (bozulma/titreme üretmez)"""
    from .numbers import _sayilari_yaz
    fx = fx or {}
    pitch = fx.get("pitch", 1.0)
    raw = out_wav + ".raw.wav"
    subprocess.run(
        [sys.executable, "-m", "piper", "-m", voice_model, "-f", raw,
         "--length-scale", str(length_scale * fx.get("slow", 1.0) * pitch),
         "--noise-scale", str(fx.get("noise", 0.2)), "--noise-w-scale", str(fx.get("noise_w", 0.3)),
         "--sentence-silence", "0.3"],
        input=_sayilari_yaz(text).encode("utf-8"), check=True, capture_output=True)
    af = (f"asetrate={int(22050 * pitch)},aresample={SR}," if pitch != 1.0 else "") + \
        "highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=5:release=60,loudnorm=I=-16:TP=-1.5:LRA=6"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", out_wav], check=True)
    os.remove(raw)


DEFAULT_VOICE_FX = {"pitch": 1.15, "noise": 0.2, "noise_w": 0.3}


def apply_voice_fx(wav_path, fx):
    """Karikatür ses efekti: perde yükseltme + tempo (rubberband) + parlaklık."""
    if not fx:
        return
    tmp = wav_path + ".fx.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav_path, "-af",
                    f"rubberband=pitch={fx.get('pitch', 1.0)}:tempo={fx.get('tempo', 1.0)},"
                    "equalizer=f=3000:t=q:w=1:g=3",
                    "-ar", str(SR), "-ac", "1", tmp], check=True)
    os.replace(tmp, wav_path)


def read_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:  # basit yeniden örnekleme
        idx = np.linspace(0, len(data) - 1, int(len(data) * SR / sr))
        data = np.interp(idx, np.arange(len(data)), data)
    return data


ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "audio")


def load_asset(name):
    """assets/audio/<name>.(mp3|wav|ogg) varsa yükler (Pixabay vb. telifsiz sesler), yoksa None."""
    for ext in ("mp3", "wav", "ogg", "m4a"):
        path = os.path.join(ASSET_DIR, f"{name}.{ext}")
        if os.path.exists(path):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1",
                                  "-ar", str(SR), "-"], capture_output=True, check=True).stdout
            return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    return None


VOICE_FILTER = ("highpass=f=80,lowpass=f=11000,afftdn=nf=-25,"
                "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=7")


def load_voice_recording(path):
    """Kullanıcının kendi ses kaydı: gürültü azaltma + sıkıştırma + ses seviyesi eşitleme."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", VOICE_FILTER, "-f", "s16le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def split_by_pauses(a, n, min_pause=0.45):
    """Tek parça kaydı, en uzun n-1 sessizlikten keserek n sahneye böler."""
    if n <= 1:
        return [_trim(a, 0.02)]
    hop = int(SR * 0.02)
    rms = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, mode="same"))[::hop]
    thr = max(0.012, np.percentile(rms, 30) * 1.5)
    silent = rms < thr
    runs, start = [], None
    for i, sl in enumerate(np.append(silent, False)):
        if sl and start is None:
            start = i
        elif not sl and start is not None:
            if (i - start) * 0.02 >= min_pause and start > 0:
                runs.append((i - start, (start + i) // 2))
            start = None
    if len(runs) < n - 1:
        raise ValueError(f"Kayıtta {n} sahne için yeterli duraklama yok ({len(runs) + 1} parça bulundu). "
                         "Sahneler arasında 1-2 saniye bekleyerek tekrar kaydedin.")
    cuts = sorted(c for _, c in sorted(runs, reverse=True)[: n - 1])
    bounds = [0] + [c * hop for c in cuts] + [len(a)]
    return [_trim(a[bounds[i]:bounds[i + 1]], 0.02) for i in range(n)]


def sfx(name, fallback, gain=0.6):
    a = load_asset(name)
    return a * gain if a is not None else fallback()


def sfx_pop():
    t = np.linspace(0, 0.14, int(SR * 0.14), endpoint=False)
    f = 900 * np.exp(-t * 18) + 180
    return 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)


def sfx_ding():
    t = np.linspace(0, 0.6, int(SR * 0.6), endpoint=False)
    return 0.22 * (np.sin(2 * np.pi * 1760 * t) + 0.6 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 7)


def sfx_boing():
    t = np.linspace(0, 0.45, int(SR * 0.45), endpoint=False)
    f = 220 + 160 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4) + 200 * t
    return 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)


def sfx_darbe():
    """Kanca açılışı için alçak, ani darbe (boom)."""
    n = int(SR * 1.1)
    t = np.arange(n) / SR
    f = 38 + 70 * np.exp(-t * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    rng = np.random.default_rng(7)
    hit = np.convolve(rng.standard_normal(n), np.ones(12) / 12, mode="same") * np.exp(-t * 30)
    return 0.75 * body + 0.25 * hit / (np.abs(hit).max() + 1e-6)


def sfx_geri_sar():
    """Kancadan hikâyeye dönüşte kısa, yükselen geri sarma sesi."""
    n = int(SR * 0.4)
    t = np.arange(n) / SR
    f = 200 + 1600 * (t / t[-1]) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.minimum(1, t / 0.05) * np.exp(-((t - 0.32) / 0.12) ** 2 * 0.5)
    out = 0.16 * tone * env
    w = sfx_whoosh()
    out[n - len(w):] += 0.8 * w
    return out


def sfx_whoosh():
    n = int(SR * 0.3)
    rng = np.random.default_rng(1)
    noise = rng.standard_normal(n)
    # yumuşatılmış gürültü (basit alçak geçiren filtre)
    k = np.ones(25) / 25
    noise = np.convolve(noise, k, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return 0.18 * noise * env / (np.abs(noise).max() + 1e-6)


# --------------------------------------------------------------------------
# Altyazı zamanlaması
# --------------------------------------------------------------------------

def word_timings(text, duration):
    words = text.split()
    weights = []
    for w in words:
        wt = len(w.strip('.,!?:;"…')) + 1.5
        if w.endswith(("...", "…")):
            wt += 5
        elif w[-1] in ".!?":
            wt += 4
        elif w[-1] in ",:;\"":
            wt += 2
        weights.append(wt)
    total = sum(weights)
    out, acc = [], 0.0
    for w, wt in zip(words, weights):
        s = acc / total * duration
        acc += wt
        out.append((w, s, acc / total * duration))
    return out


def chunk_words(timed, ctx, max_w=900):
    D.set_font(ctx, D.CAPTION_FONT, 64, bold=True)
    chunks, cur = [], []
    for item in timed:
        trial = " ".join(x[0] for x in cur + [item])
        if cur and (D.text_width(ctx, trial) > max_w or len(cur) >= 4):
            chunks.append(cur)
            cur = [item]
        else:
            cur.append(item)
        if item[0][-1] in ".!?" and len(cur) >= 2:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def draw_caption(ctx, chunks, t):
    active = None
    for ch in chunks:
        if ch[0][1] - 0.05 <= t <= ch[-1][2] + 0.25:
            active = ch
    if not active:
        return
    D.set_font(ctx, D.CAPTION_FONT, 64, bold=True)
    words = [w for w, _, _ in active]
    space = D.text_width(ctx, " ")
    widths = [D.text_width(ctx, w) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    x = W / 2 - total / 2
    y = 1450
    appear = ease = D.ease_out((t - active[0][1] + 0.05) / 0.15)
    ctx.save()
    ctx.translate(W / 2, y)
    ctx.scale(0.9 + 0.1 * ease, 0.9 + 0.1 * ease)
    ctx.translate(-W / 2, -y)
    for (w, s, e), wd in zip(active, widths):
        if s <= t < e + 0.05:
            ctx.rectangle(x - 10, y - 58, wd + 20, 76)
            ctx.set_source_rgba(*SM.RED, 0.92)
            ctx.fill()
        ctx.move_to(x + 3, y + 4)
        ctx.text_path(w)
        ctx.set_source_rgba(0, 0, 0, 0.7 * appear)
        ctx.fill()
        ctx.move_to(x, y)
        ctx.text_path(w)
        ctx.set_source_rgba(*SM.INK, appear)
        ctx.fill()
        x += wd + space
    ctx.restore()


# --------------------------------------------------------------------------
# Sahne çizimi
# --------------------------------------------------------------------------

def scene_ship_pos(prop, st, dur):
    """Gemi konumu: (x_norm, y_norm, eğim_radyan)."""
    if prop.get("path") == "hill":
        k = D.ease_in_out(st / max(0.1, dur - 0.2))
        x = prop["from"] + (prop["to"] - prop["from"]) * k
        y = D.hill_y(x) + 0.005
        tilt = math.atan(D.hill_slope(x) * PH / PW)
        return x, y, tilt
    x, y, tilt = prop["x"], prop["y"], 0.0
    anim = prop.get("anim")
    if anim == "bob":
        ph = prop.get("delay", 0) * 7
        y += 0.008 * math.sin(st * 2.5 + ph)
        tilt = 0.04 * math.sin(st * 2 + ph)
    elif anim == "bump":
        # zincire çarpıp geri sekme döngüsü
        cyc = (st % 1.6) / 1.6
        x += 0.06 * (math.sin(cyc * math.pi) if cyc < 0.5 else 0) - 0.02 * (1 if cyc >= 0.5 else 0) * math.sin((cyc - 0.5) * 2 * math.pi)
        tilt = -0.06 * math.sin(cyc * math.pi * 2) if cyc > 0.45 else 0.0
        y += 0.006 * math.sin(st * 2.5)
    return x, y, tilt


def resolve_beats(beats, st, voice_dur, voice_delay, default_pose, default_face, poses):
    """Zamanlanmış hareketler: her beat {'t': sn} ya da {'f': konuşma oranı}."""
    def bt(b):
        return b["t"] if "t" in b else voice_delay + b["f"] * voice_dur
    seq = sorted(beats, key=bt)
    pose, face, since = poses[default_pose], default_face, 99.0
    prev = pose
    for b in seq:
        tb = bt(b)
        if st >= tb:
            prev = pose
            pose = poses[b.get("pose")] if b.get("pose") else pose
            face = b.get("face", face)
            since = st - tb
    if since < 0.22:
        pose = D.blend_pose(prev, pose, D.ease_in_out(since / 0.22))
    return pose, face, since


def draw_narrator_scene(ctx, scene, st, dur, voice_dur, voice_delay):
    D.draw_burst(ctx, st)
    n = scene["narrator"]
    pose, face, since = resolve_beats(n.get("beats", []), st, voice_dur, voice_delay,
                                      n.get("pose", "idle"), n.get("face", "happy"), D.NARRATOR_POSES)
    # aşağıdan zıplayarak giriş + esneme
    k = st / 0.4
    rise = (1 - D.ease_out(k)) * 0.9
    squash = 1.0
    if 0.4 <= st < 0.75:
        q = (st - 0.4) / 0.35
        squash = 1 + 0.12 * math.sin(q * math.pi * 2) * (1 - q)
    elif st < 0.4:
        squash = 1.12
    wink_k = 0.0
    if face == "wink":
        wink_k = 1.0 if since < 0.6 else 0.0
    talking = voice_delay <= st < voice_delay + voice_dur
    x, y = D.sx(n.get("x", 0.5)), D.sy(n.get("y", 0.97) + rise)
    j = D.draw_narrator(ctx, x, y, n.get("scale", 1.25), pose, face, st, talking,
                        "idle", squash, wink_k)
    if face == "wink" and since < 0.7:
        ex, ey = j["eye_l"]
        D.draw_sparkle(ctx, ex - j["head_r"] * 0.9, ey - j["head_r"] * 0.5,
                       60 * D.elastic(since / 0.35) * (1 - max(0, since - 0.45) / 0.25), st)
    return {"hoca": j}


def wall_top(scene, x):
    walls = [p for p in scene["props"] if p["type"] == "wall"]
    if not walls:
        return None
    w = min(walls, key=lambda p: abs(p["x"] - x))
    return 1 - w["h"]


def draw_scene(ctx, scene, st, dur, voice_dur):
    night = True
    ink = SM.INK
    ctx.save()
    ctx.rectangle(PX, PY, PW, PH)
    ctx.clip()

    # Yavaş, ürkütücü yaklaşma (punch-in yerine): sahne boyunca %0-6 zoom
    z = 1 + scene.get("zoom", 0.05) * min(1.0, st / max(1.0, dur))
    if scene.get("sarsinti") and st > scene.get("sarsinti_t", 0):
        ctx.translate(6 * math.sin(st * 53), 5 * math.sin(st * 37 + 1))
    ctx.translate(PX + PW / 2, PY + PH / 2)
    ctx.scale(z, z)
    ctx.translate(-(PX + PW / 2), -(PY + PH / 2))

    joints = {}
    if scene.get("narrator"):
        joints = draw_narrator_scene(ctx, scene, st, dur, voice_dur, scene.get("voice_delay", 0.12))
    elif scene.get("bg", "karanlik") in SM.BACKGROUNDS:
        SM.draw_bg(ctx, scene.get("bg", "karanlik"), st, scene)
    else:
        D.draw_background(ctx, scene.get("bg", "plain"), night, st)

    props = scene.get("props", [])
    ships = {}
    # Arka katman aksesuarlar
    for i, p in enumerate(props):
        if p["type"] == "wall":
            D.draw_wall(ctx, p["x"], p["w"], p["h"], D.INK_DAY, p.get("towers", True))
        elif p["type"] == "ship":
            x, y, tilt = scene_ship_pos(p, st, dur)
            ships[i] = (x, y)
            D.draw_ship(ctx, D.sx(x), D.sy(y), p.get("scale", 1.0), tilt, D.INK_DAY, st)
        elif p["type"] == "chain":
            D.draw_chain(ctx, D.sx(p["x1"]), D.sx(p["x2"]), D.sy(p["y"]), ink, st, p.get("anim") == "shake")
        elif p["type"] in SM_BACK:
            SM.draw_prop(ctx, p, st)
        elif p["type"] in P2.BACK_PROPS:
            P2.draw_prop2(ctx, p, st, ink)

    # Karakterler
    first_ship = next(iter(ships.values()), None)
    for a in scene.get("actors", []):
        x = a["x"]
        if a.get("follow") == "ship" and first_ship:
            x = first_ship[0] + a.get("offset", -0.15)
        y = a.get("y", 0.93)
        if scene.get("bg") == "hill" and not a.get("stand_on"):
            y = D.hill_y(x)
        if a.get("stand_on") == "wall":
            wt = wall_top(scene, x)
            if wt is not None:
                y = wt
        if "to_x" in a or "to_y" in a:
            u = (st - a.get("move_start", 0.0)) / a.get("move_dur", max(0.5, voice_dur))
            u = D.ease_in_out(u)
            if "to_x" in a:
                x = x + (a["to_x"] - x) * u
            if "to_y" in a:
                y0 = y
                y = y0 + (a["to_y"] - y0) * u
                if a.get("arc"):
                    y -= a["arc"] * math.sin(math.pi * u)
        if a.get("enter"):
            k = D.ease_out(st / 0.55)
            x += (-0.6 if a["enter"] == "left" else 0.6) * (1 - k)
        pose = D.POSES[a.get("pose", "stand")]
        face = a.get("face", "neutral")
        anim = a.get("anim", "idle")
        if a.get("pose2"):
            sw = a.get("switch", 0.5) * voice_dur
            k = D.ease_in_out((st - sw) / 0.25)
            pose = D.blend_pose(pose, D.POSES[a["pose2"]], k)
            if st >= sw:
                face = a.get("face2", face)
                anim = a.get("anim2", anim)
        lean_extra = 0.0
        if a.get("follow") == "ship" and scene.get("bg") == "hill":
            lean_extra = -math.degrees(math.atan(D.hill_slope(x) * PH / PW)) * 0.25
        talking = a.get("talk", False) and st < voice_dur
        facing = -1 if a.get("flip") else 1
        j = D.draw_figure(ctx, D.sx(x), D.sy(y), a.get("scale", 1.0), pose, face, a.get("hat"),
                          facing, ink, st + sum(map(ord, a["id"])) % 7, talking, anim, lean_extra,
                          wings=a.get("wings", False), holds=a.get("holds"))
        joints[a["id"]] = j

    # Ön katman aksesuarlar
    for p in props:
        t0 = p["delay"] if "delay" in p else scene.get("voice_delay", 0.12) + p.get("f", 0) * voice_dur
        k = st - t0
        until = None
        if "until" in p:
            until = p["until"]
        elif "until_f" in p:
            until = scene.get("voice_delay", 0.12) + p["until_f"] * voice_dur
        if p["type"] == "pop" and k > 0 and (until is None or st < until + 0.2):
            s = D.elastic(k / 0.45)
            if until is not None and st > until:
                s *= max(0.0, 1 - (st - until) / 0.2)
            s = min(1.0, D.ease_out(k / 0.35))
            if until is not None and st > until:
                s *= max(0.0, 1 - (st - until) / 0.2)
            D.outlined_text(ctx, p["text"], D.sx(p["x"]), D.sy(p["y"]), D.CAPTION_FONT, p.get("size", 90),
                            SM.RED, (0.02, 0.02, 0.03), outline=12, rot=p.get("rot", 0), scale=max(0.01, 0.92 + 0.08 * s))
        elif p["type"] == "bubble" and k > 0:
            D.draw_bubble(ctx, p["text"], D.sx(p["x"]), D.sy(p["y"]) + 40, D.sx(p["tx"]), D.sy(p["ty"]),
                          ink, max(0.01, D.elastic(k / 0.4)))
        elif p["type"] == "bulb" and k > 0:
            j = joints.get(p.get("actor"))
            if j:
                bx, by = j["head"][0], j["head"][1] - j["head_r"] * 4.6
            else:
                bx, by = D.sx(p["x"]), D.sy(p["y"])
            D.draw_bulb(ctx, bx, by, ink, st, D.elastic(k / 0.4))
        elif p["type"] == "flag":
            j = joints.get(p.get("actor"))
            if j:
                D.draw_flag(ctx, j["hand"], ink, st, p.get("emblem", True))
        elif p["type"] in SM.PROPS:
            if p["type"] not in SM_BACK and (k > 0 or ("delay" not in p and "f" not in p)):
                SM.draw_prop(ctx, p, st)
        elif p["type"] not in ("wall", "ship", "chain", "sfx", "pop", "bubble", "bulb", "flag", "label") \
                and p["type"] not in P2.BACK_PROPS:
            P2.draw_prop2(ctx, p, st, ink)
        elif p["type"] == "label" and k > 0:
            ctx.save()
            D.set_font(ctx, D.HAND_FONT, 52)
            a = D.ease_out(k / 0.3)
            ctx.set_source_rgba(*ink, a)
            tx = D.sx(p["x"]) - D.text_width(ctx, p["text"]) / 2
            ctx.move_to(tx, D.sy(p["y"]))
            ctx.show_text(p["text"])
            ctx.restore()

    ctx.restore()

    # Sis (sahnenin "sis" yoğunluğu, 0..1) — zamanla yavaşça artabilir
    sis = scene.get("sis", 0.0)
    if scene.get("sis_to") is not None:
        sis = sis + (scene["sis_to"] - sis) * min(1.0, st / max(0.5, dur))
    if sis > 0:
        if _FOG["f"] is None:
            _FOG["f"] = SM.Fog()
        _FOG["f"].apply(ctx.get_target(), st + scene.get("_t0", 0), sis)
    # Vinyet (kenarlar karanlık)
    g = cairo.RadialGradient(PX + PW / 2, PY + PH / 2, PW * 0.30, PX + PW / 2, PY + PH / 2, PW * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, scene.get("vinyet", 0.55))
    ctx.rectangle(PX, PY, PW, PH)
    ctx.set_source(g)
    ctx.fill()
    # Karartma: "karart": [baş, son] saniye aralığında ışıklar söner
    kr = scene.get("karart")
    if kr and kr[0] <= st:
        a = min(1.0, (st - kr[0]) / 0.08) if st < kr[1] else max(0.0, 1 - (st - kr[1]) / 0.15)
        ctx.rectangle(PX, PY, PW, PH)
        ctx.set_source_rgba(0, 0, 0, 0.96 * a)
        ctx.fill()

    # Panel çerçevesi
    ctx.rectangle(PX, PY, PW, PH)
    ctx.set_source_rgb(*SM.FRAME)
    ctx.set_line_width(6)
    ctx.stroke()


def draw_kanca(ctx, scene, st, dur):
    """Soğuk açılış: ilk kareden itibaren panelde büyük kırmızı kanca yazısı;
    sahnenin son ~0,35 sn'sinde 'geri sarma' parazit geçişi."""
    txt = scene.get("kanca_yazi")
    if txt:
        txt = D.tr_upper(txt)
        size = 92
        D.set_font(ctx, D.CAPTION_FONT, size, bold=True)
        while D.text_width(ctx, txt) > PW - 120 and size > 50:
            size -= 4
            D.set_font(ctx, D.CAPTION_FONT, size, bold=True)
        tw = D.text_width(ctx, txt)
        cy = PY + PH * scene.get("kanca_y", 0.19)
        # hafif titreme (ilk kare sabit ve okunaklı kalır)
        jx = 3 * math.sin(st * 41) if st > 0.6 else 0
        bw, bh = tw + 60, size * 1.35
        ctx.rectangle(PX + PW / 2 - bw / 2 + jx, cy - bh / 2, bw, bh)
        ctx.set_source_rgba(0.02, 0.02, 0.03, 0.82)
        ctx.fill()
        ctx.set_source_rgb(*SM.RED)
        ctx.move_to(PX + PW / 2 - tw / 2 + jx, cy + size * 0.36)
        ctx.show_text(txt)
    # Geri sarma geçişi
    g0 = dur - 0.35
    if st > g0:
        u = min(1.0, (st - g0) / 0.35)
        rng = np.random.default_rng(int(st * 1000))
        for _ in range(int(10 + 30 * u)):
            y = PY + rng.random() * PH
            h = 2 + rng.random() * 14
            ctx.rectangle(PX, y, PW, h)
            ctx.set_source_rgba(1, 1, 1, 0.10 + 0.35 * rng.random() * u)
            ctx.fill()
        ctx.rectangle(PX, PY, PW, PH)
        ctx.set_source_rgba(1, 1, 1, 0.55 * u ** 2)
        ctx.fill()


def make_header(ep, paper):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_surface(paper)
    ctx.paint()
    # Dizi rozeti: "SON MOLA · BÖLÜM N"
    D.set_font(ctx, D.CAPTION_FONT, 40, bold=True)
    label = f"SON MOLA  ·  BÖLÜM {int(ep['id'])}"
    tw = D.text_width(ctx, label)
    bx, by, bw, bh = W / 2 - tw / 2 - 30, 72, tw + 60, 64
    ctx.rectangle(bx, by, bw, bh)
    ctx.set_source_rgb(*SM.RED)
    ctx.fill()
    ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(W / 2 - tw / 2, by + 46)
    ctx.show_text(label)
    # Başlık
    title = D.tr_upper(ep["title"])
    size = 74
    D.set_font(ctx, D.CAPTION_FONT, size, bold=True)
    while D.text_width(ctx, title) > 980 and size > 44:
        size -= 3
        D.set_font(ctx, D.CAPTION_FONT, size, bold=True)
    ctx.set_source_rgb(*SM.INK)
    ctx.move_to(W / 2 - D.text_width(ctx, title) / 2, 238)
    ctx.show_text(title)
    return surf


def draw_year_tag(ctx, txt):
    """Panelin sol üst köşesinde kırmızı dijital saat etiketi (ör. 16:44 ya da GÜN 3)."""
    D.set_font(ctx, D.CAPTION_FONT, 40, bold=True)
    tw = D.text_width(ctx, txt)
    x, y = PX + 22, PY + 22
    ctx.rectangle(x, y, tw + 36, 60)
    ctx.set_source_rgba(0.02, 0.02, 0.03, 0.85)
    ctx.fill_preserve()
    ctx.set_source_rgb(*SM.RED)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.move_to(x + 18, y + 45)
    ctx.show_text(txt)


# --------------------------------------------------------------------------
# Ana akış
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# 0. saniye kanca yazısı + ilk 0,8 sn zoom (13 Kasım): sessiz izleyen ilk karede anlasın
# --------------------------------------------------------------------------
KANCA_SURE, ZOOM_SURE = 2.8, 0.8


def kanca_metni(ep):
    import re
    t = (ep.get("kanca_yazi") or "").strip()
    if not t:
        t = ((ep.get("instagram_caption") or ep.get("caption") or "").strip().split("\n") or [""])[0]
    t = "".join(ch for ch in t if ord(ch) < 0x2190 or ch in "…’‘“”–—").strip()
    t = " ".join(t.split())
    if len(t) > 45:
        m = re.match(r"(.+?[.?!…])(\s|$)", t)
        if m and len(m.group(1)) >= 12:
            t = m.group(1)
    w = t.split()
    if len(w) > 12:
        t = " ".join(w[:11]) + "…"
    return t


def _kanca_satirlar(ctx, txt, maxw):
    out, cur = [], ""
    for w in txt.split():
        s = (cur + " " + w).strip()
        if D.text_width(ctx, s) > maxw and cur:
            out.append(cur)
            cur = w
        else:
            cur = s
    if cur:
        out.append(cur)
    return out


def draw_kanca_yazi(ctx, txt, t, bitis):
    if not txt or t >= bitis:
        return
    a = min(1.0, (bitis - t) / 0.3)
    size = 76
    while True:
        D.set_font(ctx, D.CAPTION_FONT, size, bold=True)
        lines = _kanca_satirlar(ctx, txt, PW - 140)
        if len(lines) <= 3 or size <= 50:
            break
        size -= 4
    lh = size * 1.25
    bw = max(D.text_width(ctx, ln) for ln in lines) + 80
    bh = lh * len(lines) + 50
    x0, y0 = PX + PW / 2 - bw / 2, PY + PH * 0.18 - bh / 2
    ctx.rectangle(x0, y0, bw, bh)
    ctx.set_source_rgba(0.03, 0.03, 0.05, 0.84 * a)
    ctx.fill()
    for i, ln in enumerate(lines):
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.move_to(PX + PW / 2 - D.text_width(ctx, ln) / 2, y0 + 25 + lh * i + size * 0.95)
        ctx.show_text(ln)


def zoom_bas(ctx, t):
    if t >= ZOOM_SURE:
        return False
    z = 1.14 - 0.14 * (1 - (1 - t / ZOOM_SURE) ** 3)
    ctx.save()
    ctx.rectangle(PX, PY, PW, PH)
    ctx.clip()
    cx, cy = PX + PW / 2, PY + PH / 2
    ctx.translate(cx, cy)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)
    return True


def render_episode(ep_path, out_mp4, voice_model, workdir="build", handle="@sonmola.dizi"):
    ep = json.load(open(ep_path, encoding="utf-8"))
    os.makedirs(workdir, exist_ok=True)

    # 1) Seslendirme
    voice_parts, timeline = [], []
    t_cursor = 0.0
    base = os.path.dirname(os.path.abspath(ep_path))
    recorded = None
    if ep.get("narration"):  # tüm bölüm tek kayıt (sahneler arası duraklamalı)
        recorded = split_by_pauses(load_voice_recording(os.path.join(base, ep["narration"])), len(ep["scenes"]))
    if recorded is None and os.environ.get("TTS_ENGINE") == "gemini" \
            and not any(sc.get("audio") for sc in ep["scenes"]):
        # Gemini: bölüm başına TEK istek, sonra duraklamalardan sahnelere böl (tutarlı ses, kotaya sığar)
        try:
            from . import gemini_ses
            from .numbers import seslendirme_metni
            metinler = [seslendirme_metni(sc["say"]) for sc in ep["scenes"]]
            a24, _ = gemini_ses.seslendir(metinler, GEMINI_TON)
            raw = os.path.join(workdir, "gemini.pcm")
            (np.clip(a24, -1, 1) * 32767).astype("<i2").tofile(raw)
            tempo = float(os.environ.get("GEMINI_TEMPO", "1.0"))
            af = (f"atempo={tempo}," if abs(tempo - 1) > 0.01 else "") + \
                "highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=5:release=60,loudnorm=I=-16:TP=-1.5:LRA=6"
            pcm = subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", raw,
                                  "-af", af, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                                 capture_output=True, check=True).stdout
            a = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
            recorded = [_trim(p, 0.02) for p in gemini_ses.bol(a, SR, metinler)]
        except Exception as e:  # noqa: BLE001
            print(f"::warning::Gemini sesi alınamadı, bölümün tamamı yedek sesle okunacak: {e}", flush=True)
            os.environ["TTS_ENGINE"] = "chatterbox" if os.path.exists(os.environ.get("VOICE_REF", "/yok")) \
                or os.environ.get("CB_REF") else "piper"
    for i, sc in enumerate(ep["scenes"]):
        wav = os.path.join(workdir, f"s{i:02d}.wav")
        if recorded is not None:
            a = recorded[i]
        elif sc.get("audio"):  # sahneye özel kayıt
            a = _trim(load_voice_recording(os.path.join(base, sc["audio"])), 0.02)
        else:
            tts(sc["say"], wav, voice_model, fx=ep.get("voice_fx", DEFAULT_VOICE_FX), emotion=sc.get("emotion"))
            a = read_wav(wav)
        vd = len(a) / SR
        vdl = sc.get("voice_delay", 0.12)
        dur = vdl + vd + SCENE_PAD
        timeline.append((t_cursor, dur, vd))
        voice_parts.append((t_cursor + vdl, a))
        t_cursor += dur
    scenes_end = t_cursor + 0.4
    total = scenes_end + END_CARD
    print(f"Toplam süre: {total:.1f} sn")

    # 2) Ses miksajı (konuşma + efektler)
    mix = np.zeros(int(total * SR) + SR)
    for start, a in voice_parts:
        s = int(start * SR)
        mix[s:s + len(a)] += a
    # Sahneye özel efektler: props içinde {"type":"sfx","name":"rimshot","delay":1.0} ya da "f"
    for i, (s0, dur, vd) in enumerate(timeline):
        sc = ep["scenes"][i]
        vdl = sc.get("voice_delay", 0.12)
        for p in sc.get("props", []):
            if p["type"] == "sfx":
                a = load_asset(p["name"])
                if a is None:
                    continue
                tp = p["delay"] if "delay" in p else vdl + p.get("f", 0) * vd
                s = int((s0 + tp) * SR)
                a = a[: max(0, len(mix) - s)] * p.get("gain", 0.6)
                mix[s:s + len(a)] += a
    # Kanca (soğuk açılış) sahneleri: başta darbe, sonda geri sarma
    for i, (s0, dur, vd) in enumerate(timeline):
        if ep["scenes"][i].get("kanca"):
            for a, tp in ((sfx_darbe(), s0), (sfx_geri_sar(), s0 + dur - 0.42)):
                st_i = int(max(0, tp) * SR)
                a = a[: max(0, len(mix) - st_i)]
                mix[st_i:st_i + len(a)] += a
    # Arka plan müziği (assets/audio/music.*): döngü + konuşmada otomatik kısma
    music = load_asset(ep["music"]) if ep.get("music") else None
    if music is None:  # sentetik gerilim müziği, son sahnenin sonunda yükselip kesilir
        last_s0, _, last_vd = timeline[-1]
        sting = ep.get("sting_at", last_s0 + ep["scenes"][-1].get("voice_delay", 0.12) + last_vd - 1.6)
        music = SM.drone(total + 1, SR, seed=int(ep["id"]) + 11, sting_at=max(0.5, sting))
    if music is not None:
        need = len(mix)
        reps = int(np.ceil(need / len(music)))
        bed = np.tile(music, reps)[:need]
        voice_env = np.zeros(need)
        for start, a in voice_parts:
            s = int(start * SR)
            voice_env[s:s + len(a)] = 1
        k = int(SR * 0.25)
        voice_env = np.convolve(voice_env, np.ones(k) / k, mode="same")
        gain = ep.get("music_vol", 0.30) - 0.14 * voice_env
        fade = np.ones(need)
        fl = int(SR * 1.2)
        fade[-fl:] = np.linspace(1, 0, fl)
        bed = bed / (np.abs(bed).max() + 1e-6)
        mix += bed * gain * fade
    mix = np.clip(mix / max(1.0, np.abs(mix).max() / 0.95), -1, 1)
    audio_path = os.path.join(workdir, "mix.wav")
    with wave.open(audio_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

    # 3) Görüntü
    paper = SM.make_paper()
    header = make_header(ep, paper)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    chunks_per_scene = [chunk_words(word_timings(sc["text"], vd), ctx)
                        for sc, (_, _, vd) in zip(ep["scenes"], timeline)]

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", audio_path,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_mp4],
        stdin=subprocess.PIPE)

    for i, (s0, _, _) in enumerate(timeline):
        ep["scenes"][i]["_t0"] = s0
    nframes = int(total * FPS)
    for fi in range(nframes):
        t = fi / FPS
        if t >= scenes_end:  # kapanış kartı
            ctx.set_source_surface(header)
            ctx.paint()
            SM.draw_end_card(ctx, (t - scenes_end) / 0.8, int(ep["id"]) + 1, ep.get("next_time", "20:00"))
            surf.flush()
            ff.stdin.write(bytes(surf.get_data()))
            continue
        idx = 0
        for i, (s0, dur, vd) in enumerate(timeline):
            if t >= s0:
                idx = i
        s0, dur, vd = timeline[idx]
        st = t - s0
        ctx.set_source_surface(header)
        ctx.paint()
        _z = zoom_bas(ctx, t)
        # ilk sahnede çizimler 0,45 sn ileriden başlar: ilk karede boş panel olmasın
        draw_scene(ctx, ep["scenes"][idx], st + (0.45 if idx == 0 else 0.0), dur, vd)
        if _z:
            ctx.restore()
        if ep["scenes"][idx].get("kanca"):
            draw_kanca(ctx, ep["scenes"][idx], st, dur)
        tag = ep["scenes"][idx].get("tag", "BİRAZ SONRA" if ep["scenes"][idx].get("kanca") else ep.get("year"))
        if tag:
            draw_year_tag(ctx, tag)
        # İlerleme çubuğu
        ctx.rectangle(PX, PY + PH + 16, PW * (t / scenes_end), 6)
        ctx.set_source_rgb(*SM.RED)
        ctx.fill()
        draw_caption(ctx, chunks_per_scene[idx], st - ep["scenes"][idx].get("voice_delay", 0.12))
        # Kanal adı
        D.set_font(ctx, D.HAND_FONT, 44)
        ctx.set_source_rgba(*SM.INK, 0.45)
        ctx.move_to(W / 2 - D.text_width(ctx, handle) / 2, 1640)
        ctx.show_text(handle)
        surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
        if fi % 300 == 0:
            print(f"  kare {fi}/{nframes}")
    ff.stdin.close()
    ff.wait()
    print("Bitti:", out_mp4)
    return out_mp4
