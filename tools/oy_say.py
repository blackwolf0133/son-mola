"""Bir Reels'in yorumlarındaki A/B oylarını sayar (Son Mola seçimli dizi, 19 Kasım).
Kullanım: python tools/oy_say.py <media_id>   -> {"A": n, "B": m, "toplam_yorum": k, "izin": true/false}
Kural: yorumun başındaki ya da tek başına duran A/B harfi (ör. "A", "a!", "B olsun", "kesin B") sayılır;
aynı kişinin birden çok oyu tek sayılır (son oyu geçerli)."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import publisher as P

OY = re.compile(r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])([ABab])(?![A-Za-zÇĞİÖŞÜçğıöşü])")


def oylar(media_id, token=None):
    token = token or os.environ["IG_ACCESS_TOKEN"]
    mode = P.detect_mode(token)
    base = f"https://{P._host(mode)}/{P.API_VERSION}"
    url, params = f"{base}/{media_id}/comments", {"fields": "text,username,timestamp", "limit": 100, "access_token": token}
    kisi, toplam = {}, 0
    for _ in range(30):
        d = P._request("GET", url, params)
        for c in d.get("data", []):
            toplam += 1
            m = OY.findall(c.get("text") or "")
            if m:
                kisi[c.get("username") or c.get("id")] = m[-1].upper()
        nxt = (d.get("paging") or {}).get("next")
        if not nxt:
            break
        url, params = nxt, None
    a = sum(1 for v in kisi.values() if v == "A")
    b = sum(1 for v in kisi.values() if v == "B")
    return {"A": a, "B": b, "toplam_yorum": toplam}


if __name__ == "__main__":
    try:
        print(json.dumps(oylar(sys.argv[1]), ensure_ascii=False))
    except P.PublishError as e:
        print(json.dumps({"hata": str(e)[:300]}, ensure_ascii=False))
        sys.exit(1)
