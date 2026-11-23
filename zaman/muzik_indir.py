"""Freesound'dan bölüme uygun telifsiz (CC0) hüzünlü piyano parçası indirir.
Kullanım: FREESOUND_API_KEY=... python zaman/muzik_indir.py <bolum.json> <cikti.mp3>
Başarısız olursa sessizce çıkar (kurgu sentetik piyanoya düşer)."""
import json
import random
import sys
import urllib.parse
import urllib.request
import os

ANAHTAR = os.environ.get("FREESOUND_API_KEY", "").strip()
SORGULAR = ["sad piano", "melancholic piano", "emotional piano", "nostalgic piano", "slow piano melody"]


def ara(sorgu):
    q = urllib.parse.urlencode({
        "query": sorgu,
        "filter": 'license:"Creative Commons 0" duration:[40 TO 240] avg_rating:[3.5 TO 5]',
        "fields": "id,name,username,duration,previews,avg_rating,num_downloads,tags",
        "sort": "rating_desc", "page_size": 40, "token": ANAHTAR})
    with urllib.request.urlopen("https://freesound.org/apiv2/search/text/?" + q, timeout=30) as r:
        return json.load(r).get("results", [])


def main(bolum, cikti):
    if not ANAHTAR:
        print("FREESOUND_API_KEY yok, sentetik müzik kullanılacak.")
        return
    B = json.load(open(bolum, encoding="utf-8"))
    rnd = random.Random(B["id"])
    sorgular = B.get("muzik_sorgu") and [B["muzik_sorgu"]] or SORGULAR[:]
    rnd.shuffle(sorgular)
    yasak = ("drum", "beat", "loop", "edm", "rock", "trap", "glitch", "noise")
    for s in sorgular:
        try:
            sonuc = [x for x in ara(s) if not any(y in " ".join(x.get("tags", [])).lower() + x["name"].lower() for y in yasak)]
        except Exception as e:
            print("arama hatası:", e)
            continue
        if not sonuc:
            continue
        sec = rnd.choice(sonuc[:12])
        url = sec["previews"]["preview-hq-mp3"]
        urllib.request.urlretrieve(url, cikti)
        print(f"Müzik: '{sec['name']}' — {sec['username']} (CC0) https://freesound.org/s/{sec['id']}/")
        open(cikti + ".txt", "w").write(f"{sec['name']} — {sec['username']} (CC0, freesound.org/s/{sec['id']})")
        return
    print("Uygun parça bulunamadı, sentetik müzik kullanılacak.")


if __name__ == "__main__":
    main(*sys.argv[1:3])
