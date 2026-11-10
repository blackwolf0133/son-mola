"""Örnek hesabın en çok beğenilen Reels'lerini Gemini ile izletip yapısını/üretim tarzını çözer.
Videolar sadece geçici olarak indirilir, hiçbir yere yüklenmez/paylaşılmaz; çıktı yalnızca metin analizdir."""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import publisher as P  # noqa: E402

SORU = """Bu Instagram Reels videosunu dikkatle izle ve Türkçe, maddeler halinde analiz et:
1) İlk 3 saniye: ekranda ne var, ne söyleniyor/yazıyor (kanca)?
2) Hikâye/yapı: sahne sahne kısaca ne oluyor, kaç saniye, nasıl bitiyor (ders/mesaj/twist)?
3) Görsel üretim: gerçek çekim mi, yapay zekâ videosu mu, animasyon mu? Yapay zekâysa hangi tür araçlarla
   yapılmış olabilir (ör. metinden video / görselden video modelleri, 3D karakter, tutarlı karakter) ve neden öyle düşünüyorsun
   (filigran, hareket tarzı, yüz/el hataları, ışık, kamera hareketi). Kesin bilmiyorsan tahmin olduğunu söyle.
4) Ses: dış ses var mı (insan mı, yapay zekâ sesi mi), müzik, efektler; altyazı stili (font, renk, kelime kelime mi).
5) Karakterler: hayvan mı insan mı, sabit/tekrar eden bir karakter var mı?
6) Neden bu kadar izlenmiş/beğenilmiş olabilir: duygusal tetik, paylaşılabilirlik, merak, yorum tetikleyici.
7) Bizim kanallar için çıkarılabilecek 2 somut ders.
Kısa ve net yaz."""


def modeller(key):
    adlar = ["gemini-3.8-flash", "gemini-flash-lite-latest"]
    try:
        req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200",
                                     headers={"x-goog-api-key": key})
        for m in json.load(urllib.request.urlopen(req, timeout=30)).get("models", []):
            ad = m["name"].split("/")[-1]
            if ("flash" in ad and "generateContent" in m.get("supportedGenerationMethods", [])
                    and not any(x in ad for x in ("tts", "image", "live", "audio", "embedding", "thinking"))
                    and ad not in adlar):
                adlar.append(ad)
    except Exception as e:  # noqa: BLE001
        print("model listesi alınamadı:", e)
    return adlar[:6]


def sor(key, mp4):
    data = base64.b64encode(open(mp4, "rb").read()).decode()
    body = {"contents": [{"role": "user", "parts": [{"inline_data": {"mime_type": "video/mp4", "data": data}},
                                                    {"text": SORU}]}]}
    for model in modeller(key):
        try:
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                data=json.dumps(body).encode(), headers={"x-goog-api-key": key, "Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=300))
            return model, r["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            print(f"  {model}: HTTP {e.code} {e.read()[:200]!r}")
        except Exception as e:  # noqa: BLE001
            print(f"  {model}: {e}")
    return None, "(analiz yapılamadı)"


ad = sys.argv[1].strip().lstrip("@")
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
t = os.environ["IG_ACCESS_TOKEN"]
key = os.environ["GEMINI_API_KEY"]
m = P.detect_mode(t)
uid = P.resolve_user_id(t, m)
r = P._request("GET", f"https://{P._host(m)}/{P.API_VERSION}/{uid}",
               {"fields": f"business_discovery.username({ad}){{media.limit(60){{caption,like_count,comments_count,"
                          f"timestamp,media_type,media_url,permalink}}}}", "access_token": t})
media = [x for x in r["business_discovery"]["media"]["data"] if x.get("media_type") == "VIDEO" and x.get("media_url")]
media.sort(key=lambda x: x.get("like_count") or 0, reverse=True)
secim = media[:n]
print(f"{len(media)} video bulundu, en çok beğenilen {len(secim)} tanesi analiz ediliyor.\n")
for i, x in enumerate(secim, 1):
    yol = f"/tmp/v{i}.mp4"
    urllib.request.urlretrieve(x["media_url"], yol)
    sure = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", yol],
                          capture_output=True, text=True).stdout.strip()
    kucuk = f"/tmp/k{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", yol, "-vf", "scale=-2:640", "-r", "15", "-c:v", "libx264",
                    "-crf", "30", "-c:a", "aac", "-b:a", "64k", kucuk], check=True)
    model, metin = sor(key, kucuk)
    print(f"===== VİDEO {i}: {x['timestamp'][:10]} · {x.get('like_count')} beğeni · {x.get('comments_count')} yorum "
          f"· {float(sure or 0):.0f} sn · {x['permalink']}")
    print(f"Açıklama: {(x.get('caption') or '')[:200]}")
    print(f"[{model}]\n{metin}\n")
    os.remove(yol)
    os.remove(kucuk)
