"""Gerçek Instagram'a dokunmadan paylaşım akışını test eder (sahte HTTP)."""
import os, sys, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import publisher as P

calls = []
def fake(method, url, params=None, headers=None, data=None, timeout=120):
    calls.append((method, url.split("?")[0], dict(params or {}), dict(headers or {}), len(data or b"")))
    if url.endswith("/media"):
        return {"id": "C123", "uri": "https://rupload.facebook.com/ig-api-upload/v26.0/C123"}
    if "rupload" in url:
        return {"success": True}
    if url.endswith("/C123"):
        n = sum(1 for c in calls if c[1].endswith("/C123"))
        return {"status_code": "IN_PROGRESS" if n < 2 else "FINISHED"}
    if url.endswith("/media_publish"):
        return {"id": "M999"}
    if url.endswith("/M999"):
        return {"permalink": "https://www.instagram.com/reel/abc/"}
    raise AssertionError(url)

P._request = fake
P.wait_for_url = lambda u, timeout=300: True
P.time.sleep = lambda s: None

# 1) Instagram ile giriş (video_url)
r = P.publish_reel(video_url="https://u.github.io/r/videos/001.mp4", caption="Merhaba #tarih",
                   mode="instagram", user_id="17841", token="TOK")
assert r == {"media_id": "M999", "permalink": "https://www.instagram.com/reel/abc/", "container_id": "C123"}, r
c0 = calls[0]
assert c0[1] == "https://graph.instagram.com/v26.0/17841/media" and c0[2]["media_type"] == "REELS"
assert c0[2]["video_url"].endswith("001.mp4") and c0[2]["caption"] == "Merhaba #tarih"
assert any(c[1].endswith("/media_publish") and c[2]["creation_id"] == "C123" for c in calls)
print("instagram modu: OK")

# 2) Facebook ile giriş (dosyadan resumable yükleme)
calls.clear()
with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as fh:
    fh.write(b"x" * 12345)
r = P.publish_reel(video_path=fh.name, caption="c", mode="facebook", user_id="17841", token="TOK")
assert calls[0][1] == "https://graph.facebook.com/v26.0/17841/media" and calls[0][2]["upload_type"] == "resumable"
up = [c for c in calls if "rupload" in c[1]][0]
assert up[3]["offset"] == "0" and up[3]["file_size"] == "12345" and up[4] == 12345
print("facebook modu (dosya): OK")

# 2b) Facebook modu, adresten çekme (file_url) - dosya gönderilmemeli
calls.clear()
r = P.publish_reel(video_path=fh.name, video_url="https://github.com/u/r/releases/download/video-002/002.mp4",
                   caption="c", mode="facebook", user_id="17841", token="TOK")
ups = [c for c in calls if "rupload" in c[1]]
assert len(ups) == 1 and ups[0][3]["file_url"].endswith("002.mp4") and ups[0][4] == 0, ups
print("facebook modu (file_url): OK")

# 2c) file_url reddedilirse dosyaya düşsün
calls.clear()
orig = P._request
def flaky(method, url, params=None, headers=None, data=None, timeout=120):
    if "rupload" in url and (headers or {}).get("file_url"):
        raise P.PublishError("HTTP 400 ProcessingFailedError")
    return orig(method, url, params, headers, data, timeout)
P._request = flaky
r = P.publish_reel(video_path=fh.name, video_url="https://x/y.mp4", caption="c", mode="facebook", user_id="1", token="TOK")
assert r["media_id"] == "M999"
P._request = orig
print("facebook modu (yedek yol): OK")

# 3) Hata durumu
def fake_err(method, url, params=None, headers=None, data=None, timeout=120):
    if url.endswith("/media"): return {"id": "C1"}
    return {"status_code": "ERROR", "status": "Error: video too short"}
P._request = fake_err
try:
    P.publish_reel(video_url="https://x/y.mp4", mode="instagram", user_id="1", token="t")
    raise SystemExit("hata yakalanmadı")
except P.PublishError as e:
    assert "too short" in str(e)
print("hata yakalama: OK")

# 4) Anahtar türünü otomatik tanıma
os.environ.pop("IG_MODE", None)
assert P.detect_mode("IGAAxyz") == "instagram"
assert P.detect_mode("EAAGabc") == "facebook"
print("anahtar türü tanıma: OK")

# 3) Hesap doğrulama: anahtar birden çok kanala erişse de yalnızca @sonmola.dizi seçilir
def fake2(method, url, params=None, headers=None, data=None, timeout=120):
    if url.endswith("/me/accounts"):
        return {"data": [{"instagram_business_account": {"id": "111", "username": "copadamlatarih"}},
                         {"instagram_business_account": {"id": "444", "username": "sonmola.dizi"}}]}
    if url.endswith("/me/businesses"):
        return {"data": []}
    if url.endswith("/111"):
        return {"username": "copadamlatarih"}
    raise AssertionError(url)
P._request = fake2
os.environ.pop("IG_USER_ID", None)
P.VARSAYILAN_KIMLIK = ""
assert P.resolve_user_id("EAA", "facebook") == "444"
os.environ["IG_USER_ID"] = "111"
try:
    P.resolve_user_id("EAA", "facebook"); raise SystemExit("yanlış hesap engellenmedi!")
except P.PublishError:
    pass
os.environ.pop("IG_USER_ID")
print("hesap doğrulama: OK")
