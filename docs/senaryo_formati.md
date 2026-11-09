# Son Mola · bölüm JSON formatı

Dosya: `episodes/NNN_kisa_ad.json`. Sıradaki paylaşılmamış bölüm her gün 17:45'te paylaşılır.

```json
{
  "id": "004", "title": "Fazla Bardak", "year": "16:44",
  "instagram_caption": "1-2 cümle ürpertici özet 🌫️\n\nBölüm 4/30\n\nYarın 17:45'te devamı. Kaçırmamak için takip et 🌫️\n\n#gizem #korkuhikayesi #kısadizi #çöpadam #sonmola",
  "scenes": [ { "say": "...", "text": "...", "bg": "tesis_ic", "actors": [], "props": [] } ]
}
```

## Sahne alanları
| Alan | Anlamı |
|---|---|
| `say` | Okunacak metin. Rakam yerine yazı: "on altı kırk dört". |
| `text` | Ekrandaki alt yazı (rakam ve tırnak serbest). Yoksa `say` kullanılır. |
| `bg` | `tesis_dis`, `tesis_ic`, `peron`, `yol`, `pencere`, `karanlik` |
| `sis` / `sis_to` | Sis yoğunluğu 0–1; `sis_to` verilirse sahne boyunca oraya yükselir |
| `zoom` | Sahne boyunca yavaş yaklaşma (0.05 varsayılan, 0.12 = gerilimli) |
| `sarsinti`, `sarsinti_t` | Kamera titremesi ve başlama saniyesi |
| `karart` | `[baş, son]` saniyeleri arasında ışıklar söner |
| `tezgah` (tesis_ic) | `false` → tezgâh çizilmez |
| `isik` (tesis_dis) | `false` → pencereler karanlık |
| `gunduz` | Soluk sabah ışığı |
| `golge` (pencere) | `{"x":0.7}` → siste belirsiz bir siluet. Asla net gösterme. |
| `tag` | Sol üst etiket (varsayılan "16:44"), ör. "GÜN 3" |

## Karakterler (`actors`)
`{"id":"deniz","x":0.5,"y":0.93,"pose":"stand","face":"neutral","scale":0.9,"flip":false,"talk":true}`
- pose: stand, point, hips, relax, shock, think, push, sad, shrug, open, stretch, cheer
- face: neutral, smile, happy, sad, shock, think, sleepy, confident, effort, smug
- Hareket: `to_x` / `to_y` + `move_dur`. Ece için `scale` 0.55–0.6.

## Nesneler (`props`)
`saat` (16:44, `sabit`), `telefon` (`text`, `alt`), `bardak` (`adet`, `aralik` = tek tek dizilir, `fazla` = sonuncusu kırmızı parlar),
`liste` (1987 listesi, `cizik`: üstü çizili satırlar), `tabela` (`text` "SON MOLA|0 KM", `ok` sol/sag), `mont` (bankta katlanmış),
`kapi` (`aralik`), `defter`, `resim` (Ece'nin çizimi), `fener`, `lamba`, `far` (sisteki farlar), `pop` (kırmızı büyük yazı, `f` = sesin yüzde kaçında).
Zamanlama: `delay` (sn) ya da `f` (konuşmanın oranı).

Kapanış kartı ("BÖLÜM N+1 · YARIN 17:45") ve gerilim müziği otomatik eklenir.

## Haftalık trend raporu (last30days)
Her pazartesi blackwolf0133/cop-adamla-tarih deposundaki "Trend araştırma" iş akışı son 30 günün trendlerini 6 kanal için tarar
(YouTube, Reddit vb.; SCRAPECREATORS anahtarı varsa Instagram ve TikTok da). Yeni bölüm yazmadan önce en yeni raporu oku:

```bash
TAG=$(gh api "repos/blackwolf0133/cop-adamla-tarih/releases?per_page=20" --jq '[.[]|select(.tag_name|startswith("trend-"))][0].tag_name')
ID=$(gh api "repos/blackwolf0133/cop-adamla-tarih/releases/tags/$TAG" --jq '.assets[]|select(.name=="sonmola.md").id')
gh api -H "Accept: application/octet-stream" "repos/blackwolf0133/cop-adamla-tarih/releases/assets/$ID" > /tmp/trend.md
```
Bu kanalın dosyası: **sonmola.md**. Rapordaki tutan kanca kalıplarını, konu açılarını ve formatları kendi kurallarımıza uyarlayarak kullan;
başka içerik üreticilerinin metnini, videosunu ya da hikâyesini kopyalama. Rapor yoksa ya da eskiyse (14 günden eski) bu adımı atla.
