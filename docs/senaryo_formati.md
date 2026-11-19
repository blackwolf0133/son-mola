# SON MOLA · "Sen olsan?" — senaryo formatı (19 Kasım 2026)

Kanal 19 Kasım'da yeniden kuruldu (kullanıcı kararı). Örnek alınan hesaplar: @yasenolsaydin.tr (17 bin) ve
@kaderini.sec (10 bin). Onlardan alınan şey SADECE format: ikinci şahıs anlatım ("Kapıyı açtın…"), sonda A/B
seçimi, yorum oylarıyla devam eden mini dizi, Türk gündelik mekânları, telefon ekranı ters köşeleri.
ASLA alınmayacaklar: hikâyeleri, olay örgüleri, karakter adları (Nermin Teyze, Ramazan Efendi, Hüsnü amca…),
dizi adları (Sakın Kapıyı Açma, Sığınak, Maç Gecesi, Fener, Gece Treni, Saklan, Kara Burun…), metinleri.

## Neden tutuyor (veriler, 19 Kasım)
- yasenolsaydin en iyi: "Gece 3'te komşundan mesaj: 'Kapının önündeyim. Aç artık.' Ama telefonu sendeydi…"
  53 bin beğeni, 2.514 yorum. kaderini.sec en iyi: "Bütün sirenler çalıyor. Çarpmaya 15 dakika." 33 bin beğeni.
- HER ZAMAN dizinin 1. bölümü patlıyor; sonraki bölümler 5-10 kat düşüyor. Bu yüzden:
  * 1. gece TEK BAŞINA çarpıcı olmalı (en güçlü fikir, en güçlü ters köşe 1. gecede).
  * Diziler KISA: 3-4 gece. Sonra yeni dizi (yeni 1. bölüm = yeni patlama şansı).
- Yorum (A/B) en güçlü sinyal; seçim gerçekten zor ve ikisi de korkutucu olmalı.

## Mekân ve ton
Gece, Türkiye, sıradan hayat: gece otobüsü molası, dinlenme tesisi, benzinlik, son metro/marmaray, apartman
(site WhatsApp grubu, kapıcı, komşu), kurye, gece vardiyası (hastane, fabrika, otel resepsiyonu), taksi, köy yolu,
yayla evi, deprem çadırı değil (gerçek acılar yok). Doğaüstü ya da gerilim olabilir; tehlike asla açık gösterilmez,
ima edilir (silüet, ses, mesaj, boş koltuk). Kan, şiddet, intihar, gerçek kişi/firma/marka adı YOK.
Dinî unsurlar (cin, ezan, mezarlık) olabilir ama alay yok, hüküm/ayet yok.

## Dizi ve bölüm kimlikleri (ÇOK ÖNEMLİ — robot buna göre çalışır)
- Dizi numarası yüzler basamağı: 1. dizi 1xx, 2. dizi 2xx, 3. dizi 3xx …
- 1. gece: `N01` (tek dosya, dal yok). Sonraki her gece İKİ dosya: `N02A` ve `N02B`, `N03A`/`N03B`, `N04A`/`N04B`.
- `A` dalı = bir önceki gecenin A seçimi yapılmış hâli, `B` dalı = B seçimi yapılmış hâli.
- Dallar bir sonraki gece için AYNI noktada birleşir: N02A ile N02B farklı yaşanır ama ikisi de aynı yeni seçimle
  (aynı "secim" alanı) biter. Böylece her gece için sadece 2 dosya yazılır.
- Robot seçimli gecede bir önceki videonun yorumlarındaki A/B oylarını sayar, çoğunluk dalını paylaşır.
  Beraberlik/oy yoksa "varsayilan" (yoksa A). Öbür dal otomatik atlanır.
- Son gece (final) dosyalarında "secim" YOK; "son_kart": "SON", "son_alt": "Yeni hikâye yarın akşam".
- Dosya adı: `episodes/101_kisa_ad.json`, `episodes/102A_kisa_ad.json` …; "id" alanı dosya adının başıyla aynı.

## JSON alanları
```json
{
  "id": "102A", "slug": "lokanta", "title": "Lokanta", "dizi_adi": "Son Sefer", "gece": 2, "dal": "A",
  "seed": 51021, "kanca_yazi": "En fazla 6 kelime…",
  "scenes": [ {"text": "…", "prompt": "English, concrete…", "sis": 0.2, "sicak": false,
               "telefon": {"baslik": "Grup adı", "alt": "38 kişi",
                           "mesajlar": [{"kim": "Kişi", "metin": "…"}, {"ben": true, "metin": "…"}],
                           "bildirim": "Kimden: kısa mesaj"}} ],
  "secim": {"A": "kısa eylem (≤ 5 kelime)", "B": "kısa eylem (≤ 5 kelime)"},
  "varsayilan": "A",
  "caption": "Kanca cümlesi + 1 cümle. 😨", "hashtags": ["#…", "#…", "#…", "#…", "#sonmola"]
}
```
- "dal" sadece A/B dosyalarında. "secim" final dışındaki her bölümde.
- `caption`'a A/B satırlarını ve "yorumlara yaz" çağrısını YAZMA: robot "secim"den kendisi ekler.
- `telefon` her bölümde 1-3 sahnede olsun (grup mesajları, bilinmeyen numara, kendi numarandan mesaj, konum,
  sesli mesaj bildirimi…). Mesajlar kısa (≤ 14 kelime), en fazla 4 mesaj; "bildirim" tek satır gibi kısa.
  Telefon varken sahnenin `prompt`'u sade bir arka plan olsun (telefon ortayı kaplıyor).

## Uzunluk ve yapı
- 9-11 sahne, toplam 120-150 kelime (~60-75 sn).
- 1. sahne KANCA: sonucu ele vermeyen en ürpertici an, ≤ 14 kelime, ikinci şahıs. `kanca_yazi` ekranda büyük.
  İlk 2 saniyede soru ya da imkânsız bir durum: "Otobüs hiç yola çıkmamış. Peki sen neyin içindeydin?"
- 2. sahne: saat + yer, tek cümle ("Gece iki kırk. Issız bir dinlenme tesisi.").
- Gelişme: tuhaflık büyür, en az bir telefon ters köşesi.
- Son sahne: iki seçeneği söyleyen soru ("Sen olsan ne yapardın? Lokantaya mı girerdin, yoksa tıra mı el sallardın?").
- A/B dallarının 1. sahnesi seçimi hatırlatır: "Lokantaya girdin." / "Tıra el salladın." (kanca gibi çarpıcı).
- `text` ve `say`: sayılar ve saatler yazıyla ("gece üç kırk"), çünkü ses modeli rakamı bozabilir; telefon
  mesajlarında rakam serbest.

## Çizim
- `prompt` İngilizce, somut, karanlık; yüz yok (arkadan, silüet, uzaktan), yazı/tabela/numara yok, kan yok.
- Türkiye ayrıntısı: dinlenme tesisi, çay bardağı, apartman koridoru, kapı zili paneli, minibüs, taksi, köy evi.
- Doğaüstü varlık ASLA net çizilmez: gölge, silüet, sis, cam yansıması.

## Kopyalama kontrolü
Yazmadan önce örnek hesapların son paylaşımlarına (Rakip inceleme) bak; benzer bir öncül görürsen değiştir.
