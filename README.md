# Sakai Duyuru Bot 📢

Sakai LMS'den otomatik olarak duyuruları alıp Telegram'a gönderen bot.

## Özellikler

- ✅ Sakai LMS'ye otomatik giriş
- ✅ Duyuruları otomatik olarak kontrol et
- ✅ Yeni duyuruları Telegram'a gönder
- ✅ Duyuruları JSON dosyasına kaydet
- ✅ GitHub Actions ile periyodik çalıştırma

## Kurulum

### 1. Projeyi klonla
```bash
git clone https://github.com/YOUR_USERNAME/debis_bot.git
cd debis_bot
```

### 2. Gerekli kütüphaneleri yükle
```bash
pip install -r requirements.txt
```

### 3. Ortam değişkenlerini ayarla
```bash
# .env.example'ı kopyala
cp .env.example .env

# .env dosyasını düzenle ve kendi bilgilerini gir
```

### 4. Bot parametrelerini ayarla

#### Telegram Bot Token ve Chat ID
1. [@BotFather](https://t.me/botfather) ile Telegram bot oluştur
2. Bot token'ını al
3. [@userinfobot](https://t.me/userinfobot) ile chat ID'ni bul

#### Sakai Bilgileri
- Kullanıcı adı ve şifreni `.env` dosyasına gir

### 5. Lokal olarak test et
```bash
python sakai_bot_final.py
```

## GitHub Actions ile Otomatik Çalıştırma

Bot her gün belirli saatlerde otomatik olarak çalışacak. Bunun için:

1. GitHub repository ayarları:
   - Settings → Secrets and variables → Actions
   - Şu ortam değişkenlerini ekle:
     - `TELEGRAM_TOKEN`
     - `TELEGRAM_CHAT_ID`
     - `SAKAI_USERNAME`
     - `SAKAI_PASSWORD`

2. Workflow otomatik olarak `.github/workflows/bot.yml` dosyasından çalışır

### Çalıştırma Zamanı
- Varsayılan: **Her gün 08:00 UTC** (ayarlamak için `.github/workflows/bot.yml` dosyasını düzenle)

## Dosya Yapısı

```
debis_bot/
├── sakai_bot_final.py      # Ana bot dosyası
├── duyurular.json          # Kaydedilen duyurular (git'e yüklenmez)
├── requirements.txt        # Python dependencies
├── .env.example           # Ortam değişkenleri şablonu
├── .env                   # Gerçek ortam değişkenleri (git'e yüklenmez)
├── .gitignore            # Git'i görmezden gelecek dosyalar
├── README.md             # Bu dosya
└── .github/workflows/
    └── bot.yml          # GitHub Actions workflow
```

## Sorun Giderme

### Selenium WebDriver Hatası
- Bot otomatik olarak uygun Edge/ChromeDriver'ı indirir (Selenium Manager)

### Giriş Başarısız Olmuşsa
- Sakai kimlik bilgilerini kontrol et
- `.env` dosyasında USERNAME ve PASSWORD doğru mu?

### Telegram Bildirimi Gelmemişse
- TELEGRAM_TOKEN ve CHAT_ID'yi kontrol et
- Bot'u Telegram'da başlat (chat aç)

## Lisans

MIT

## Yardım

Sorun olursa GitHub Issues'de bildir.
