"""SON MOLA (@sonmola.dizi) - günlük otomasyon (her gün 17:45).

Komutlar:
  python daily.py status                 -> sırada kaç bölüm var, son paylaşılanlar
  python daily.py render                 -> sıradaki bölümün videosunu üretir (output/today.json)
  python daily.py publish --video-url U  -> üretilen videoyu Instagram'a yükler ve kaydeder
  python daily.py check                  -> Instagram bağlantısını test eder
  python daily.py refresh-token          -> erişim anahtarını 60 gün uzatır
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ROOT, "state", "posted.json")
TODAY = os.path.join(ROOT, "output", "today.json")
VOICE = os.environ.get("COPTARIH_VOICE", os.path.join(ROOT, "models", "tr_TR-fahrettin-medium.onnx"))


def today_tr():
    """Türkiye tarihi (UTC+3)."""
    return (dt.datetime.utcnow() + dt.timedelta(hours=3)).date().isoformat()


def set_output(key, val):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"{key}={val}\n")


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"posted": []}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def queue():
    """Paylaşılmamış bölümler, dosya adı sırasıyla (001_..., 002_...)."""
    done = {p["id"] for p in load_state()["posted"]}
    eps = []
    for path in sorted(glob.glob(os.path.join(ROOT, "episodes", "[0-9]*.json"))):
        ep = json.load(open(path, encoding="utf-8"))
        if ep["id"] not in done and not ep.get("skip"):
            eps.append((path, ep))
    return eps


def cmd_status(_):
    q = queue()
    st = load_state()
    print(f"Sırada {len(q)} bölüm var.")
    for path, ep in q[:10]:
        print(f"  {ep['id']}  {ep['title']}")
    if len(q) < 4:
        print("::warning::Sırada 4'ten az bölüm kaldı - yeni senaryolar eklenmeli!")
    for p in st["posted"][-5:]:
        print(f"  [paylaşıldı {p['date']}] {p['id']} {p.get('permalink') or ''}")


def cmd_render(_):
    sys.path.insert(0, ROOT)
    from engine import render as R
    q = queue()
    if not q:
        print("::error::Sırada bölüm yok! episodes/ klasörüne yeni bölüm ekleyin.")
        sys.exit(1)
    # GitHub zamanlayıcısı saatlerce gecikebiliyor: otomatik tetiklemede Türkiye saati 17:00-21:00
    # dışındaysa paylaşma; yedek alarm elle başlatır.
    hour_tr = (dt.datetime.utcnow() + dt.timedelta(hours=3)).hour
    if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and not (17 <= hour_tr < 21):
        print(f"Zamanlayıcı geç tetiklendi (TR saat {hour_tr}:xx), gece paylaşımı yapılmıyor.")
        set_output("skip", "true")
        return
    if os.environ.get("FORCE") != "1" and not os.path.exists(os.path.join(ROOT, "assets", "yayinda")):
        print("Dizi henüz yayında değil (assets/yayinda dosyası yok). Ses ve ilk bölüm onaylanınca açılacak.")
        set_output("skip", "true")
        return
    if os.environ.get("FORCE") != "1" and any(p.get("date") == today_tr() for p in load_state()["posted"]):
        print(f"Bugün ({today_tr()}) zaten paylaşım yapılmış, ikinci video üretilmiyor.")
        set_output("skip", "true")
        return
    set_output("skip", "false")
    path, ep = q[0]
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    out = os.path.join(ROOT, "output", f"{ep['id']}.mp4")
    R.render_episode(path, out, VOICE, workdir=os.path.join(ROOT, "build", ep["id"]))
    json.dump({"id": ep["id"], "path": out, "title": ep["title"],
               "caption": ep.get("instagram_caption", ep["title"])},
              open(TODAY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Hazır: {out}")
    if len(q) - 1 < 4:
        print(f"::warning::Bu bölümden sonra sırada {len(q) - 1} bölüm kalacak.")



def paylas_tekrarli(publisher, video_path, video_url, caption, deneme=3):
    """Meta videoyu arada bir işleyemiyor (ProcessingFailedError). Hata yayınlamadan ÖNCEKİ aşamadaysa
    1-2 dk bekleyip YENİ bir yükleme kaydıyla tekrar dener; 2. denemede videoyu doğrudan yükler.
    media_publish aşamasındaki hatalar tekrar denenmez (çift paylaşım olmasın)."""
    import time
    for n in range(deneme):
        url = video_url if (n != 1 or not video_path) else None
        try:
            return publisher.publish_reel(video_path=video_path, video_url=url, caption=caption)
        except publisher.PublishError as e:
            if "media_publish" in str(e) or n == deneme - 1:
                raise
            bekle = 60 * (n + 1)
            print(f"::warning::Paylaşım denemesi {n + 1} olmadı, {bekle} sn sonra yeni kayıtla tekrar: {str(e)[:200]}",
                  flush=True)
            time.sleep(bekle)


def hikaye_paylas(publisher, video_path, video_url):
    """Reel'den sonra aynı videoyu hikâyeye koyar. Hata olursa sadece uyarı verir:
    Reel zaten paylaşıldı ve kaydı yazıldı, hikâye yüzünden iş akışı ASLA başarısız olmamalı."""
    if os.environ.get("HIKAYE_KAPALI") == "1":
        print("Hikâye paylaşımı kapalı (HIKAYE_KAPALI=1).")
        return None
    try:
        r = publisher.publish_story(video_path=video_path, video_url=video_url)
        print(f"Hikâye paylaşıldı: {r['media_id']}")
        return r["media_id"]
    except Exception as e:
        print(f"::warning::Hikâye paylaşılamadı (Reel etkilenmedi): {str(e)[:300]}")
        return None


def cmd_publish(a):
    import publisher
    today = json.load(open(TODAY, encoding="utf-8"))
    res = paylas_tekrarli(publisher, today["path"], a.video_url, today["caption"])
    st = load_state()
    st["posted"].append({"id": today["id"], "title": today["title"], "date": today_tr(),
                         "media_id": res["media_id"], "permalink": res.get("permalink")})
    save_state(st)
    print(f"Paylaşıldı: {today['title']} -> {res.get('permalink')}")
    hid = hikaye_paylas(publisher, today["path"], a.video_url)
    if hid:
        st = load_state()
        st["posted"][-1]["story_id"] = hid
        save_state(st)


def cmd_check(_):
    import publisher
    me, lim = publisher.check_account()
    print("Hesap:", me.get("username"), "| kimlik:", me.get("id"), "| Paylaşım kotası:", lim)


def cmd_refresh(_):
    import publisher
    if os.environ.get("IG_ACCESS_TOKEN", "").startswith("EAA"):
        print("Sistem kullanıcı anahtarı süresizdir, yenileme gerekmez.")
        return
    tok, exp = publisher.refresh_token()
    if not tok:
        print("::error::Token yenilenemedi")
        sys.exit(1)
    days = (exp or 0) // 86400
    print(f"Token yenilendi, {days} gün geçerli.")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        # Token loglara yazılmasın diye maskele
        print(f"::add-mask::{tok}")
        with open(out, "a") as fh:
            fh.write(f"token={tok}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("render")
    p = sub.add_parser("publish")
    p.add_argument("--video-url", default=None)
    sub.add_parser("check")
    sub.add_parser("refresh-token")
    a = ap.parse_args()
    {"status": cmd_status, "render": cmd_render, "publish": cmd_publish,
     "check": cmd_check, "refresh-token": cmd_refresh}[a.cmd](a)
