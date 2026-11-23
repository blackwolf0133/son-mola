"""Freesound'da Türk ezgisi/enstrüman adaylarını bulur, her birinden 14 sn'lik parça ile
numaralı bir dinleme kolajı (katalog.mp3) ve liste (katalog.json) üretir."""
import json, os, subprocess, urllib.parse, urllib.request

K = os.environ["FREESOUND_API_KEY"].strip()
SORGU = ["ney taksim", "turkish ney", "ney flute", "oud taksim", "oud improvisation", "oud sad", "baglama",
         "saz turkish", "kanun", "kemence", "duduk", "turkish traditional", "anatolian", "makam", "hicaz"]
seen, liste = set(), []
for s in SORGU:
    q = urllib.parse.urlencode({"query": s, "filter": 'duration:[25 TO 400] license:("Creative Commons 0" OR "Attribution")',
                                "fields": "id,name,username,duration,previews,license,num_downloads,avg_rating,tags",
                                "sort": "downloads_desc", "page_size": 15, "token": K})
    try:
        r = json.load(urllib.request.urlopen("https://freesound.org/apiv2/search/text/?" + q, timeout=30))["results"]
    except Exception as e:
        print(s, "hata", e); continue
    n = 0
    for x in r:
        t = (x["name"] + " " + " ".join(x["tags"])).lower()
        if x["id"] in seen or any(y in t for y in ("drum", "beat", "loop", "edm", "trap", "techno", "remix", "hiphop")):
            continue
        seen.add(x["id"]); liste.append(dict(no=len(liste) + 1, sorgu=s, **{k: x[k] for k in ("id", "name", "username", "duration", "license")}, url=x["previews"]["preview-hq-mp3"]))
        n += 1
        if n >= 3:
            break
os.makedirs("kat", exist_ok=True)
parcalar = []
for it in liste[:36]:
    f = f"kat/{it['no']:02d}.mp3"
    try:
        urllib.request.urlretrieve(it["url"], f)
    except Exception:
        continue
    o = f"kat/{it['no']:02d}.wav"
    bas = min(8, max(0, it["duration"] / 4))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(bas), "-i", f, "-t", "14", "-ac", "2", "-ar", "44100",
                    "-af", "afade=t=in:d=0.5,afade=t=out:st=13:d=1,loudnorm=I=-16", o], check=True)
    # numarayı bip sayısıyla değil, kısa sessizlikle ayır; numara listeden okunur
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1.2", f"kat/s{it['no']:02d}.wav"], check=True)
    parcalar += [f"kat/s{it['no']:02d}.wav", o]
    it["kolaj_bas"] = None
open("kat/l.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parcalar))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "kat/l.txt", "-b:a", "160k", "katalog.mp3"], check=True)
# zaman damgaları
t = 0.0
for it in liste[:36]:
    if os.path.exists(f"kat/{it['no']:02d}.wav"):
        t += 1.2; it["kolaj_bas"] = f"{int(t//60)}:{int(t%60):02d}"; t += 14
json.dump([x for x in liste[:36] if x.get("kolaj_bas")], open("katalog.json", "w"), ensure_ascii=False, indent=1)
for x in liste[:36]:
    if x.get("kolaj_bas"): print(x["no"], x["kolaj_bas"], x["sorgu"], "|", x["name"][:60], "|", x["license"])
