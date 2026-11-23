"""Bölümün müziğini indirir (incompetech, CC BY 4.0). Başarısız olursa sessizce çıkar
(kurgu sentetik piyanoya düşer).  Kullanım: python zaman/muzik_indir.py <bolum.json> <cikti.mp3>"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zaman import muzik_sec  # noqa: E402


def main(bolum, cikti):
    ep = json.load(open(bolum, encoding="utf-8"))
    ad = muzik_sec.sec(ep)
    try:
        req = urllib.request.Request(muzik_sec.url(ad), headers={"User-Agent": "Mozilla/5.0"})
        open(cikti, "wb").write(urllib.request.urlopen(req, timeout=60).read())
        print("Müzik:", muzik_sec.kredi(ep))
    except Exception as e:
        print("Müzik indirilemedi:", e)
        if os.path.exists(cikti):
            os.remove(cikti)


if __name__ == "__main__":
    main(*sys.argv[1:3])
