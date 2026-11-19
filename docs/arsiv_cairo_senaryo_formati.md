# Son Mola · bölüm JSON formatı

Dosya: `episodes/NNN_kisa_ad.json`. Sıradaki paylaşılmamış bölüm her gün 20:00'de paylaşılır.

```json
{
  "id": "004", "title": "Fazla Bardak", "year": "16:44",
  "instagram_caption": "1-2 cümle ürpertici özet 🌫️\n\nBölüm 4/30\n\nYarın 20:00'de devamı. Kaçırmamak için takip et 🌫️\n\n#gizem #korkuhikayesi #kısadizi #çöpadam #sonmola",
  "scenes": [ { "say": "...", "text": "...", "bg": "tesis_ic", "actors": [], "props": [] } ]
}
```

## İlk sahne: KANCA (zorunlu, ilk 3 saniye)
İlk istatistik: izleyiciler ~8 saniyede çıkıyor. Bu yüzden **her bölüm** kısa bir "biraz sonra" sahnesiyle açılır:
bölümün en ürpertici anından bir kesit (cevabı vermeden), sonra geri sarma efektiyle hikâyeye dönülür.

```json
{ "kanca": true, "kanca_yazi": "SAKIN CEVAP VERME", "voice_delay": 0.0,
  "say": "Gece yarısı kapıdan babamın sesi geldi. Ama babam hastanedeydi.",
  "bg": "pencere", "golge": {"x": 0.62}, "sis": 0.65, "zoom": 0.12, "sarsinti": true, "sarsinti_t": 2.0,
  "actors": [], "props": [] }
```
- `say`: en fazla **10–12 kelime**, 2 kısa cümle; ikinci cümle çelişki/şok ("Ama…"). Bölümün son uçurumunu ele verme.
- `kanca_yazi`: 2–3 kelimelik büyük kırmızı yazı; **ilk kareden** görünür (kapak karesi olur).
- Etiket otomatik "BİRAZ SONRA" olur; başta darbe sesi, sonda geri sarma sesi ve parazit geçişi otomatik eklenir.
- İkinci sahne önceki bölümün uçurumunu tek cümlede bağlar, sonra hikâye başlar.
- Kanca sahnesi dahil toplam süre ~55 sn'yi geçmesin (gerekirse diğer sahneleri kısalt).

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
| `tag` | Sol üst etiket (varsayılan "16:44", kancada "BİRAZ SONRA"), ör. "GÜN 3" |
| `kanca`, `kanca_yazi`, `kanca_y` | Soğuk açılış sahnesi (yukarıya bak); `kanca_y` yazının dikey yeri (0.19) |

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

Kapanış kartı ("BÖLÜM N+1 · YARIN 20:00") ve gerilim müziği otomatik eklenir.

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

## Antoloji formatı (12 Kasım)
İlk 3 dizi bölümünde izleyicinin neredeyse tamamı kanalı ilk kez gördü, hikâyenin ortasına girdi ve 7-8 sn'de kaydırdı
(izlenme 157 → 130 → 118). Bu yüzden SON MOLA artık bir **antoloji**: her bölüm kendi içinde başlayıp biten ayrı bir kısa korku hikâyesi.
- Ortak tema: gece yolculuğu ve yol kenarı molaları (otobüs molası, benzinlik, yol kenarı lokantası, köprü, terk edilmiş tesis, otogar, tır parkı…).
- Her bölümde yeni, sıradan karakterler (şoför, muavin, yolcu, benzinlikçi, çaycı); birinci tekil şahıs anlatım ("O gece…").
  Eski dizinin karakterlerine/sırlarına (Deniz, Ece, Kerem, 16:44…) atıf YOK. Arşiv: `episodes/arsiv_dizi/` (daily.py okumaz).
- 6-7 sahne, 65-80 kelime, kapanış kartı dahil 30-40 sn (42 sn'yi aşma).
- Yapı: KANCA (en ürpertici an, ≤12 kelime, sonucu vermeden) → kim, nerede, gece kaçta (1 cümle) → tuhaflık büyür (2-3 sahne)
  → ters köşe / son olay (gösterilmez, ima edilir) → izleyiciye tek soru ("Sen olsan…?"). Mümkünse son cümle kancadaki bir kelimeyi yankılasın (tekrar izleme).
- "Devamı yarın" yok. Tehlike gösterilmez (sis, ses, siluet, boş koltuk, çalan telefon). Şiddet/kan yok; gerçek marka, başka film/dizi göndermesi yok.
- `year` = hikâyenin saati ("03:40"); sol üst etiket olarak görünür. Actor `id` serbest (ör. "sofor", "muavin"); poz/yüz listesi aynı.
- Açıklama: 1. satır kısa ürpertici cümle (cevapsız) + açık uçlu soru + "Her akşam 20:00'de yeni bir hikâye. Takip et 🌫️" + tam 5 etiket, sonuncusu #sonmola. "Bölüm N/30" yazma.
- Not: kapanış kartı motor tarafında hâlâ "BÖLÜM N+1 · YARIN 20:00" yazar; antolojiyle uyumlu.

---

## 13 Kasım: İLK 3 SANİYE kuralları (ZORUNLU, diğer kurallarla çelişirse bu geçerli)

Veri: 8 kanalda izleyici ortalama 5-13 sn'de kaydırıyor. Instagram videoyu önce küçük bir test grubuna gösteriyor; izlenme süresi, sona kadar izlenme ve DM ile gönderilme iyi değilse yaymıyor. Reels izleyicisi ~1,4 sn'de karar veriyor ve izlemelerin yarısından fazlası ses kapalı başlıyor.

**Motor ne yapıyor (otomatik):** 0. saniyede ekranda büyük kanca yazısı (~3 sn) + ilk 0,8 sn hızlı zoom. Yazı bölümdeki `"kanca_yazi"` alanından gelir; yoksa açıklamanın (caption / instagram_caption) ilk satırından, o da uzunsa ilk cümlesinden. Bu yüzden:
- Her bölüme `"kanca_yazi"` ekle: en fazla 8 kelime, sessizken tek başına merak uyandıran cümle (cevabı vermeden). Seslendirilen ilk cümleyle aynı olmak zorunda değil ama aynı merakı açsın. (Son Mola'da bu alan sahne içindedir ve 2-3 kelimedir; orada mevcut kural geçerli.)
- Açıklamanın ilk satırı da kısa ve merak uyandıran olsun (yedek kanca yazısı olarak kullanılıyor).

**Kanca puanlama (yazdıktan sonra her bölüm için):** İlk seslendirilen cümleyi ve kanca_yazi'yi şu 5 türe göre 1-5 puanla, kendine sor: "Akışta kaydırırken 1,5 sn'de durur muydum?"
1. Ortak dert: izleyicinin yaşadığı ama dile getirmediği bir sıkıntı (Reels'te en güçlüsü)
2. Merak boşluğu: kapanması için izlemek gereken bir soru/boşluk
3. İddialı/ters köşe cümle: doğru ama şaşırtıcı, karşı çıkılası bir iddia
4. Kalıp kırma: beklenmedik bir giriş
5. Görsel şok: ilk karede açıklama isteyen bir görüntü
En yüksek puan 4'ün altındaysa ilk cümleyi yeniden yaz. Selamlama, giriş, "bugün size … anlatacağım", tarih/yer ile başlamak YASAK; en çarpıcı an ilk cümlede. Doğruluk kuralları aynen geçerli (abartı/uydurma yok).

**Gönderilme (DM) sebebi:** Instagram'da yeni kişilere ulaştıran en güçlü sinyal videonun DM ile birine gönderilmesi. Her bölümün SON seslendirilen cümlesi (ya da kapanış kartı alt yazısı), izleyicinin videoyu belirli birine göndermesi için doğal bir sebep versin; TEK cümle, dilenmeden: "Bunu her ay sonu batan arkadaşına gönder.", "Bunu gece yolculuğu seven birine gönder." Açıklamadaki tek çağrı kuralı aynen kalır (bu cümle videonun içinde).
