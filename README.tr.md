# 🖥️ Tablet Dock

> Çekmecede eski bir tablet mi var? Onu **PC'ni kontrol eden akıllı bir duvar paneline** çevir — program aç, oyun başlat, müzik & ses kontrol et, panonu gör, sesli asistanla konuş. Sen sadece tablete dokunursun; işi PC yapar. **Bulut yok, hesap yok, API key yok.**

**🌐 [English](README.md) · [Türkçe](README.tr.md)**

---

## 📺 Tanıtım

_Video bağlantını buraya ekle._

## 🤔 Bu nedir, basitçe?

Duvardaki tablet sadece bir **web sayfası** gösterir. Asıl işi **PC'ndeki** küçük bir program (“ajan”) yapar: programları açar, Steam/Epic oyunlarını başlatır, sesi değiştirir, panoyu okur, sesine cevap verir. İkisi ev **Wi‑Fi'ı** üzerinden konuşur. Hepsi bu.

Bu yüzden **eski/zayıf tabletler** için harika — tablet neredeyse hiçbir şey yapmaz, ağır işi PC yüklenir.

## ✨ Neler yapabilir?

- 🚀 **Programlar** — dokun, program açılır (gerçek ikonuyla). Tekrar dokun, kapanır. Açık olanlar yanar.
- 🎮 **Oyunlar** — **Steam & Epic** oyunlarını otomatik bulur, kapak resimleriyle gösterir. Dokun, oyna. Oyun kurunca/silince kendini günceller.
- 📁 **Projeler** — proje klasörlerinin içindeki klasörleri gösterir; dokun, Explorer'da açılır. En yeni üstte.
- 🎵 **Medya & ses** — oynat/duraklat/ileri, ana ses, **uygulama-bazlı ses mikseri** (oyun / Discord / tarayıcı sesini ayrı ayrı ayarla), çalan şarkı ve hoparlör/kulaklık değiştirme butonu.
- 📋 **Pano** — son kopyaladığın metinler; birine dokun, PC'ye geri kopyalanır. (Parola yöneticisi parolaları atlanır.)
- 🎙️ **Sesli asistan** — dokun ve konuş. *“Sor”* PC'deki yerel yapay zekadan hızlı cevap verir. *“İnternette ara”* canlı internetle Claude'u kullanır. Cevabı sesli okur. “OBS aç”, “sesi kıs” gibi komutlar da verebilirsin.
- 🎨 Temiz **Apple‑vari koyu tasarım**, alttan yüzen menü; tablete gerçek uygulama gibi kurulur (tam ekran).

---

## 🧰 Başlamadan önce

Gerekenler:

1. Bir **Windows PC** (Windows 10 veya 11).
2. **Chrome**'lu eski bir **Android tablet** (ya da telefon).
3. İkisi de **aynı Wi‑Fi'da**.
4. Yaklaşık **20 dakika**.

Gerekmeyenler: ücretli servis, API key, kod bilgisi. Sadece adımları izle. 🙂

---

## 🖥️ Bölüm A — PC kurulumu

### Adım 1 — Python'u kur (tek sefer)

Python, bu programın çalıştığı dildir.

1. **<https://www.python.org/downloads/>** adresine git ve büyük **Download** düğmesine bas.
2. Dosyayı çalıştır. İlk ekranda **“Add Python to PATH” kutusunu işaretle** ✅ (çok önemli), sonra **Install Now**.

### Adım 2 — Projeyi indir

- **Kolay yol:** bu sayfanın üstündeki yeşil **`<> Code`** düğmesi → **Download ZIP** → kolay bir yere (mesela Masaüstü) çıkar.
- **Ya da git ile:** `git clone https://github.com/mestretero/tablet-dock.git`

### Adım 3 — Yardımcı kütüphaneleri kur

1. Proje klasörünü aç, sonra **`backend` klasörünün içine** gir.
2. O Explorer penceresinin **adres çubuğuna** tıkla, **`cmd`** yazıp **Enter**'a bas. Siyah bir terminal penceresi açılır (zaten `backend` klasöründe).
3. Şunu yazıp Enter:
   ```
   pip install -r requirements.txt
   ```
   Bitene kadar bekle. (Programın ihtiyacı olan parçaları indirir.)

### Adım 4 — Hangi programlar görünsün, seç

1. `backend` klasöründe `apps.example.json`'u **kopyala** ve kopyanın adını **`apps.json`** yap.
2. `apps.json`'u **Not Defteri**'yle aç ve düzenle. İstediğin her program için **adını** ve `.exe` dosyasının **yolunu** yaz.
   - 💡 **Yolu nasıl bulurum:** programın kısayoluna sağ tık → **Özellikler** → **Hedef** satırını kopyala.
   - Program, klasör, hatta Projeler klasörünü ekleyebilirsin. Aşağıdaki [Kendine göre ayarla](#️-kendine-göre-ayarla) kısmına bak.

### Adım 5 — Güvenlik sertifikasını oluştur

Tabletin mikrofonu sadece güvenli (`https`) bağlantıda çalışır. Bu adım onu sağlar.

Aynı terminalde:
```
python ..\deploy\generate_cert.py
```

### Adım 6 — Başlat!

1. **`deploy`** klasörüne git ve **`start-dock.vbs`**'e **çift tıkla**.
2. Saatin yanında (ekranın sağ altı — küçük **^** okuna tıklaman gerekebilir) küçük bir ikon çıkar. Bu, **çalışıyor** demek. O ikona sağ tık → **Başlat / Durdur / Aç / Çıkış**.
3. İlk seferde Windows **güvenlik duvarını** sorabilir → **İzin Ver** (“Özel ağlar” işaretli kalsın).

### Adım 7 — PC'nin adresini bul

1. Terminalde **`ipconfig`** yazıp Enter.
2. **“IPv4 Address”** satırını bul — `192.168.1.42` gibi görünür. **Bir yere yaz** — bu PC'nin adresi. (Seninki farklı olacak.)

> 💡 İpucu: modemden PC'ne sabit IP (DHCP rezervasyonu) ver ki adres hiç değişmesin.

---

## 📱 Bölüm B — Tablet kurulumu

### Adım 1 — Sertifikaya güven (mikrofon için)

1. Tablette **Chrome**'u aç ve şuraya git:
   `https://PC-ADRESIN:8000/cert.crt`  (`PC-ADRESIN`'i yukarıdaki adresle değiştir)
2. Küçük bir dosya iner. Şimdi kur:
   **Ayarlar → Güvenlik → Şifreleme ve kimlik bilgileri → Sertifika yükle → CA sertifikası → inen dosyayı seç.**
   (Android önce ekran kilidi/PIN isterse, kur.)

### Adım 2 — Paneli uygulama olarak kur

1. Chrome'da **`https://PC-ADRESIN:8000`**'e git.
2. Chrome menüsü (**⋮**) → **Uygulamayı yükle** (ya da “Ana ekrana ekle”).
3. Ana ekrandaki yeni ikonu aç — **tam ekran** açılır, gerçek uygulama gibi.

### Adım 3 — Duvara as

Tableti duvara as (şarjda kalan bir tutucu ideal). Bitti! 🎉

> ℹ️ Fully Kiosk Browser da çalışır ama **ücretsiz** sürümü mikrofonu engeller. Sesli asistan istiyorsan **Chrome önerilir**.

---

## 🎙️ Sesli asistan (isteğe bağlı)

Ses özellikleri çoğunlukla **PC'nde** çalışır. Açmak için:

1. **[Ollama](https://ollama.com)**'yı kur (yapay zeka modellerini yerelde çalıştıran araç), sonra küçük bir model indir:
   ```
   ollama pull gemma4:e2b-it-qat
   ```
   (Hızlı çevrimdışı cevapları bu sağlar. Model adını `backend/services/llm.py`'den değiştirebilirsin.)
2. **“İnternette ara”** butonu için **`claude` CLI**'ı ([Claude Code](https://claude.com/claude-code)) kur ve giriş yap. Kendi Claude aboneliğini kullanır — **API key gerekmez**.
3. Ses‑yazı (`faster-whisper`) zaten Adım 3'te kuruldu; ilk konuştuğunda modelini indirir.

Sonra tablette **Asistan** sekmesi çalışır: **Sor** (yerel & hızlı) ya da **İnternette ara** (Claude), konuş, sesli cevap gelsin.

---

## ⚙️ Kendine göre ayarla

**Kolay yol — hiçbir dosya düzenlemeden program ekle/kaldır:**

- **Ekle:** Explorer'da bir programa/kısayola **sağ tık → Gönder → Tablet Dock'a Ekle**, ya da tepsi ikonu → **Program Ekle…**. Dosyayı seç, adını onayla — ikonu otomatik gelir.
- **Kaldır:** tepsi ikonu → **Program Kaldır…**, listeden seç (bu yalnızca panelden kaldırır, programı bilgisayardan **silmez**).

Eklediğin program tablette birkaç saniye içinde belirir — yeniden başlatma yok.

**İleri seviye — `backend/apps.json`'u elle düzenle** (otomatik okunur — yeniden başlatma yok):

```jsonc
{
  "id": "spotify",                   // benzersiz bir ad
  "name": "Spotify",                 // ikonun altında görünür
  "icon": "S",                       // gerçek ikon bulunmazsa kullanılan harf
  "path": "C:\\...\\Spotify.exe",    // .exe, .lnk kısayolu, klasör ya da web sitesi
  "args": ["--flag"],                // isteğe bağlı: ek başlatma seçenekleri
  "process": "Spotify.exe",          // isteğe bağlı: “tekrar dokun kapansın” + yanma çalışsın
  "icon_from": "C:\\...\\app.exe",   // isteğe bağlı: ikonun alınacağı .exe (.lnk için faydalı)
  "project_root": true               // isteğe bağlı: bu klasörün alt klasörleri Projeler'de görünsün
}
```

- Gerçek ikonlar programdan otomatik çıkarılır. Klasörler harf gösterir.
- Bir **klasöre** `"project_root": true` eklersen alt klasörleri **Projeler** sekmesinde listelenir.

## 🔁 Açılışta otomatik başlat (isteğe bağlı)

PC açılınca kendiliğinden başlasın diye:

1. **Win + R**'ye bas, **`shell:startup`** yazıp Enter.
2. `deploy/start-dock.vbs`'i o klasöre sağ‑tıkla‑sürükle → **Kısayol oluştur**.

## 🔒 Gizlilik & güvenlik

- Ajan yalnızca **senin `apps.json`**'undaki programları açar — başka hiçbir şey uzaktan çalıştırılamaz.
- Pano geçmişi yalnızca bellektedir (yeniden başlatınca silinir) ve parola yöneticilerinin gizli işaretlediği **parolaları atlar**.
- Bulut yok, takip yok, API key yok. Sertifikan, `apps.json`, ikonlar ve loglar **asla yüklenmez** (git‑ignore).
- Ev **Wi‑Fi'ında** tut; internete açma.

## 🆘 Sorun giderme

- **Tablet “bağlanılamıyor” diyor** → Ajan çalışıyor mu (tepsi ikonu)? Güvenlik duvarına izin verdin mi? İkisi aynı Wi‑Fi'da mı? IP doğru mu?
- **Mikrofon yok / “erişilemedi”** → Sertifikayı kurdun mu (Bölüm B, Adım 1) ve siteyi **https** ile mi açtın? **Chrome** mu kullanıyorsun (ücretsiz Fully Kiosk değil)?
- **Değiştirdikten sonra eski ikon** → ana ekran uygulamasını **tamamen kaldır** ve **yeniden kur** (Chrome ikonu önbelliyor).
- **Sunucu loglarını gör** → tepsi yerine `deploy/run.bat`'i çalıştır; mesajları gösteren bir konsol açar.

## 📄 Lisans

[MIT](LICENSE) — özgürce kullan, değiştir, paylaş.
