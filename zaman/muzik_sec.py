"""Zaman Durağı müzik seçimi: Kevin MacLeod (incompetech.com) — dünyada en çok kullanılan telifsiz
müzik kataloğu, CC BY 4.0. Sadece duygusal/nostaljik parçalar. Her bölüme sırayla farklı parça düşer;
bölüm JSON'unda "muzik": "<ad>" ile elle de seçilebilir."""
import re

PARCALAR = [
    "Gymnopedie No 1",   # piyano, en nostaljik
    "Heartbreaking",     # yaylılar + piyano, hüzün
    "Sad Trio",          # piyano, keman, çello
    "Lasting Hope",      # piyano, umutlu hüzün
    "At Rest",           # ağır yaylılar
    "Rains Will Fall",   # piyano, yağmur hissi
    "Bittersweet",       # tatlı-acı
    "Long Road Ahead",   # sinematik hüzün
    "Eternal Hope",      # duygusal final
]


def sec(ep):
    if ep.get("muzik"):
        return ep["muzik"]
    m = re.search(r"\d+", ep.get("id", "0"))
    n = int(m.group()) if m else 0
    return PARCALAR[(n - 1) % len(PARCALAR)]


def url(ad):
    return "https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + ad.replace(" ", "%20") + ".mp3"


def kredi(ep):
    return f'Müzik: "{sec(ep)}" Kevin MacLeod (incompetech.com) · CC BY 4.0'
