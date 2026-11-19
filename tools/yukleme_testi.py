"""Instagram'a YAYINLAMADAN yükleme testi: hangi video biçimini işleyebiliyor? (15 Kasım)
Kullanım: python tools/yukleme_testi.py <dosya1> [<dosya2> ...]   (ve/veya URL=... ortam değişkeni)"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import publisher as P

tok = os.environ["IG_ACCESS_TOKEN"]
mode = P.detect_mode(tok)
uid = P.resolve_user_id(tok, mode)
host = P._host(mode)
base = f"https://{host}/{P.API_VERSION}"
print("mod:", mode, "kullanıcı:", uid)


def bekle(cid, sure=600):
    t0 = time.time()
    while time.time() - t0 < sure:
        try:
            i = P._request("GET", f"{base}/{cid}", {"fields": "status_code,status", "access_token": tok})
        except P.PublishError as e:
            print("   sorgu hatası:", str(e)[:150]); time.sleep(60); continue
        if i.get("status_code") in ("FINISHED", "ERROR", "EXPIRED"):
            return i, int(time.time() - t0)
        time.sleep(20)
    return {"status_code": "ZAMAN_ASIMI"}, int(time.time() - t0)


def dosya(path):
    c = P._request("POST", f"{base}/{uid}/media", {"media_type": "REELS", "upload_type": "resumable",
                                                    "caption": "test", "share_to_feed": "false", "access_token": tok})
    uri = c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{P.API_VERSION}/{c['id']}"
    data = open(path, "rb").read()
    try:
        P._request("POST", uri, headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(len(data)),
                                         "Content-Type": "application/octet-stream"}, data=data, timeout=600)
        y = "yükleme ok"
    except P.PublishError as e:
        y = "yükleme hatası: " + str(e)[-160:]
    return c["id"], y


def klasik(url):
    c = P._request("POST", f"{base}/{uid}/media", {"media_type": "REELS", "video_url": url, "caption": "test",
                                                    "share_to_feed": "false", "access_token": tok})
    return c["id"], "klasik video_url"


isler = [("dosya:" + p, dosya, p) for p in sys.argv[1:]]
if os.environ.get("URL"):
    isler.append(("klasik:" + os.environ["URL"], klasik, os.environ["URL"]))
for ad, fn, arg in isler:
    try:
        cid, y = fn(arg)
        st, sn = bekle(cid)
        print(f"=== {ad}: {st.get('status_code')} ({sn} sn) | {y} | {st.get('status')}", flush=True)
    except Exception as e:
        print(f"=== {ad}: HATA {str(e)[:200]}", flush=True)
    time.sleep(30)
