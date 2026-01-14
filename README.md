# Sakai Duyuru Bot 📢

[🇬🇧 English](README_EN.md)

Sürekli Sakai'ye girip "Acaba hoca not girdi mi?", "Sınav açıklandı mı?" diye F5 atmaktan yoruldun mu?
Bırak bu nöbeti senin yerine bu bot tutsun. 🤖☕

## 🎯 Ne İşe Yarıyor?

Senin bilgisayarın kapalıyken bile arka planda çalışan bu bot:
1. Sakai hesabına gizlice giriş yapar 🕵️
2. Duyuru panosunu didik didik eder 🔍
3. **Sadece yeni bir şey bulursa** sana Telegram'dan "Bak bu önemli olabilir" der 📲
4. Eski duyurularla kafanı şişirmez, sadece tazeleri getirir 🍎

## 🎯 Nasıl Çalışır?

Bot otomatik olarak:
1. Sakai hesabına giriş yapar
2. Notification panel'ini kontrol eder
3. **Sadece yeni duyuruları gönderir** (eski olanları tekrar göndermez)
4. Duyurunun tam içeriğini çeker
5. Telegram'a düzenli formatlı mesajlar gönderir
6. Bilgisayarın kapalı olsa bile çalışır

## ⭐ Özellikler

- ✅ **Otomatik Giriş**: Sakai'ye otomatik olarak giriş yapar
- ✅ **Akıllı Duyuru Bulma**: Notification panel'inde duyuruları arar
- ✅ **Tam İçerik**: Duyurunun tüm metnini çeker
- ✅ **Telegram Bildirimi**: Yeni duyuruları anında gönderir
- ✅ **Tekrar Gönderme Engelleme**: Kaydedilen duyuruları tekrar göndermez
- ✅ **24/7 Çalışma**: GitHub sunucularında otomatik olarak çalışır
- ✅ **Profesyonel Logging**: Tüm işlemleri detaylı kaydeder
- ✅ **Hata Yönetimi**: Sorun çıktığında detaylı rapor verir

## 🚀 Hızlı Başlangıç

### Adım 1: Projeyi Fork'la ve Klonla

1. Bu sayfanın sağ üst köşesindeki **Fork** butonuna tıkla.
2. Kendi hesabına oluşturulan kopyayı klonla:

```bash
git clone https://github.com/KULLANICI_ADINIZ/debis_bot.git
cd debis_bot
```

### Adım 2: Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### Adım 3: Ayarları Yap
```bash
cp .env.example .env
# .env dosyasını düzenle ve bilgilerini gir
```

### Adım 4: Telegram Bot Oluştur

**Bot Token:**
- Telegram'da [@BotFather](https://t.me/botfather) ara
- `/newbot` yazıp bir bot oluştur
- Verilen token'ı kopyala
- `.env` dosyasında `TELEGRAM_TOKEN` kısmına yapıştır

**Chat ID (Senin ID'n):**
- Telegram'da [@userinfobot](https://t.me/userinfobot) ara
- `/my_id` yaz
- Çıkan numarayı `.env` dosyasında `TELEGRAM_CHAT_ID` kısmına yapıştır

### Adım 5: GitHub Secrets Ekle

1. GitHub repo'na gir
2. **Settings → Secrets and variables → Actions**
3. **New repository secret** tıkla
4. Şu 4 secret'ı ekle:
   - `TELEGRAM_TOKEN` = Bot token'ı
   - `TELEGRAM_CHAT_ID` = Senin Chat ID'n
   - `SAKAI_USERNAME` = Sakai kullanıcı adı
   - `SAKAI_PASSWORD` = Sakai şifresi

### Adım 6: Bitti! 🎉

Bot şimdi:
- ✅ **Her 30 dakikada bir** otomatik olarak Sakai'yi kontrol eder
  > *Not: GitHub Actions minimum 30 dakikalık aralıkları destekler. Daha sık kontrol için alternatif servis (Render, Vercel Cron) gereklidir.*
- ✅ **Yeni duyuru bulunca** anında Telegram'a haber verir
- ✅ **24/7 çalışır** (bilgisayarın açık olması gerekmez)
📁 Dosya Yapısı

```
debis_bot/
├── sakai_bot.py                 # Ana bot uygulaması (Sihrin olduğu yer ✨)
├── duyurular.json               # Kaydedilen duyurular (Git tarafından görmezden gelinir)
├── requirements.txt             # Python bağımlılıkları
├── .env.example                 # Ayarlar şablonu (geliştirme için referans)
├── .gitignore                   # Git hariç tutulacaklar
├── README.md                    # Türkçe dokümantasyon (bu dosya)
├── README_EN.md                 # English documentation
└── .github/workflows/
    └── sakai_check.yml          # GitHub Actions otomasyonu
    └── sakai_check.yml            # GitHub Actions ayarı
```

## 🔧 Yapılandırma

### Zorunlu Ortam Değişkenleri

| Değişken | Açıklama | Örnek |
|----------|----------|--------|
| `TELEGRAM_TOKEN` | @BotFather'dan alınan token | `6123456789:ABCDEfG...` |
| `TELEGRAM_CHAT_ID` | Senin Telegram user ID'n | `987654321` |
| `SAKAI_USERNAME` | Sakai kullanıcı adı | `ogrenci_no` |
| `SAKAI_PASSWORD` | Sakai şifresi | `sifre` |

### İsteğe Bağlı Değişkenler

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| `SAKAI_URL` | `https://online.deu.edu.tr/portal` | Sakai portal adresi |
| `HEADLESS` | `1` | Tarayıcı UI göster (0=görüntü, 1=gizli) |

## 📝 Yerel Test Etme

```bash
python sakai_bot.py
```

Bu komut:
- Bot'u bir kez çalıştırır
- Yeni duyuru bulursa Telegram'a gönderir
- Duyuruları `duyurular.json` içinde kaydeder

## 📅 GitHub Actions Kurulumu

Bot varsayılan olarak **her 30 dakikada bir** çalışacak şekilde ayarlanmıştır. GitHub Secrets ayarlarını yaptıktan sonra işlem tamamdır.

### Manuel Çalıştırma

GitHub'da bot'u anında çalıştırabilirsin:

1. GitHub repo'da **Actions** sekmesine gir
2. **Sakai Announcement Bot** seç
3. **Run workflow** tıkla

## 📬 Bot Nasıl Çalışır?

### 1️⃣ Başlatma
- Tüm zorunlu ayarların var olduğunu kontrol eder
- Logging sistemini açar

### 2️⃣ Tarayıcı Başlatma
- Chrome tarayıcısını açar (driver'ı otomatik indirir)
- Chrome yoksa Firefox kullanır
- GitHub Actions'da gizli modda çalışır

### 3️⃣ Sakai'ye Giriş
- Sakai portal'a gider
- Kullanıcı adı ve şifreyi girer
- Giriş tamamlanmasını bekler

### 4️⃣ Duyuru Bulma (YENİ - GELIŞTIRILMIŞ)
Notification panel'i açtıktan sonra **7 farklı yöntemle** ara:
- Çan ikonu üzerindeki sayacı bak
- Değişik HTML yapılarında ara
- Bullhorn ikonu olan öğeleri bul
- Duyuru linklerini (`/announcement/`) bul
- "duyuru" kelimesini içeren yazıları bul
- Menü öğelerini (takvim, kaynaklar, vb) otomatik filtrele

### 5️⃣ İçeriği Çek
- Her duyurunun detay sayfasını aç
- Tam içeriği oku
- Başlık ve içeriği temizle

### 6️⃣ Eski/Yeni Kontrol (ÖNEMLİ!)
- Önceki duyurularla karşılaştır
- **Sadece daha önce gönderilmemiş olanları seç**
- Listeyi `duyurular.json` dosyasına kaydet

### 7️⃣ Telegram'a Gönder
- Yeni duyuruları Telegram API'siyle gönder
- Güzel formatlı başlık ve içerik
- Başarı/başarısızlığı kaydını tut

## 💡 Deduplication (Tekrar Gönderme Engelleme)

Bu bot **sadece yeni duyuruları** gönderir. Nasıl çalışır?

```
İlk çalıştırma:
- Duyuru bulundu: "Sınav Duyurusu"
- Gönderildi ✅
- duyurular.json'a kaydedildi

İkinci çalıştırma (5 dakika sonra):
- Aynı "Sınav Duyurusu" bulundu
- duyurular.json'da var mı kontrol et → VAR ✗
- Gönderilmedi (spam önlendi)

Üçüncü çalıştırma (5 dakika sonra):
- Yeni duyuru bulundu: "Dersin Iptali"
- duyurular.json'da var mı kontrol et → YOK ✓
- Gönderildi ✅
```

**Sonuç**: Her duyuru sadece bir kez gönderilir!

## 🔐 Güvenlik

- ⚠️ **.env dosyasını GIT'e commit etme** - şifreler içeriyor
- ✅ Şifreler için GitHub Secrets kullan
- ✅ Bilgiler sadece GitHub Actions çalışma ortamında var
- ✅ `.gitignore` dosyası `.env`'i otomatik olarak korur
- ✅ Şifreler hiçbir log dosyasına yazılmaz

## 🆘 Sorun Giderme

### Duyuru Gelmiyorsa
- Sakai kullanıcı adı ve şifresi doğru mu kontrol et
- Sakai'de manuel olarak notification panel'i kontrol et (duyuru var mı?)
- GitHub Actions → **Logs** bölümünde bot çıktılarını kontrol et
- Bot neden öğeleri kabul/reddettiğini detaylı şekilde kaydediyor (debug logs)

### Telegram Mesajı Gelmiyorsa
- `TELEGRAM_TOKEN` doğru mu?
- Bot'u Telegram'da başlattın mı? (@BotName'i aç ve `/start` yaz)
- `TELEGRAM_CHAT_ID` kendi ID'n mi? (Bot ID'si değil!)
- Telegram API'ye erişim sorun var mı?

### Sakai Girişi Başarısız
- Kullanıcı adı/şifre doğru mu?
- Sakai hesabın aktif mi?
- GitHub Actions logs'ta ne yazıyor?
- Sakai sistemi bakımda mı?

### Tarayıcı Sorunları
Bot otomatik olarak:
- Chrome driver'ı indirir ve günceller
- Chrome yoksa Firefox kullanır
- Hem UI hem gizli modda çalışır

## ⚡ Performans Bilgileri

| Özellik | Değer |
|---------|-------|
| **Sayfa Yükleme Zaman Aşımı** | 10 saniye |
| **Öğe Bulma Zaman Aşımı** | 15 saniye |
| **Telegram Hız Limiti** | Mesajlar arasında 1 saniye |
| **Maksimum Duyuru** | Çalıştırma başına 20 |
| **Ortalama Çalışma Süresi** | 30-60 saniye |
| **Çalışma Sıklığı** | Her 30 dakikada (değiştirilebilir) |

## 🔄 Çalışma Sıklığını Değiştir

Bot'un kaç dakikada bir çalışmasını istersen:

1. `.github/workflows/sakai_check.yml` dosyasını aç
2. `cron: '*/30 * * * *'` satırını bulun
3. `30` yerine istediğin dakika sayısını yaz:
   - `*/15` = 15 dakikada bir
   - `*/30` = 30 dakikada bir
   - `0 * * * *` = Saatte bir
   - `0 8 * * *` = Günde bir, saat 08:00'de

4. Değişiklikleri GitHub'a yükle

## 📦 Bot'u Güncelle

Bot'un yeni versiyonunu almak istersen:

```bash
cd debis_bot
git pull origin main
pip install -r requirements.txt --upgrade
```

## 📄 Lisans

MIT

## 💬 Destek

Sorun bulursan GitHub repo'da **Issue** aç ve şunları ekle:
- Hata mesajı ve logs (GitHub Actions)
- `.env` ayarları (şifreler yazma!)
- Sakai portal adresi
- Mümkünse ekran görüntüsü

---

**ÖNEMLİ NOT**: Bu bot **sadece yeni duyuruları gönderir**. Daha önce gönderilen duyruları tekrar göndermez. Bu, spam almamak ve sadece yeni içerikler hakkında bilgi almak için tasarlanmıştır.
