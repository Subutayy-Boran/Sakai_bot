# Sakai Duyuru Bot 📢

Sakai LMS'den otomatik olarak yeni duyuruları alıp Telegram'a gönderen bot.

## Özellikler

- ✅ Sakai'ye otomatik giriş
- ✅ Her 30 dakikada bir duyuruları kontrol et
- ✅ Yeni duyuruları Telegram'a gönder
- ✅ Bilgisayar kapalı olsa bile çalış (GitHub sunucularında)
- ✅ Gereksiz menü/ders listesi gönderme
- ✅ Profesyonel hata yönetimi ve logging

## Hızlı Başlangıç

### 1. Projeyi Klonla
```bash
git clone https://github.com/YOUR_USERNAME/debis_bot.git
cd debis_bot
```

### 2. Gereksinimleri Yükle
```bash
pip install -r requirements.txt
```

### 3. Ayarları Yapılandır
```bash
cp .env.example .env
# .env dosyasını düzenle ve kendi bilgilerini gir
```

### 4. Telegram Bilgileri Al

**Bot Token:**
- Telegram'da [@BotFather](https://t.me/botfather) ara
- `/newbot` yazıp bir bot oluştur
- Token'ı kopyala

**Chat ID (Senin ID'n):**
- Telegram'da [@userinfobot](https://t.me/userinfobot) ara
- `/my_id` yaz
- Çıkan numara senin Chat ID'n

### 5. GitHub Secrets Ekle

GitHub repo'na gir:
1. **Settings → Secrets and variables → Actions**
2. **New repository secret** tıkla
3. Şu 4 secret'ı ekle:
   - `TELEGRAM_TOKEN` = Bot token'ı
   - `TELEGRAM_CHAT_ID` = Senin Chat ID'n
   - `SAKAI_USERNAME` = Sakai kullanıcı adı
   - `SAKAI_PASSWORD` = Sakai şifresi

### 6. Bitti! 🎉

Bot şimdi:
- ✅ **Her 30 dakikada bir** otomatik olarak Sakai'yi kontrol eder
- ✅ **Yeni duyuru bulunca** Telegram'a anında haber verir
- ✅ **24/7 çalışır** (bilgisayarın açık olması gerekmez)

## Nasıl Çalışır?

1. Bot Sakai'ye giriş yapar
2. Notification panel'inde duyuru var mı kontrol eder
3. Duyuru bulursa içeriğini okur
4. Telegram'a gönderir
5. Duyuruyu kaydeder (tekrar gönderme engelle)

## Sorun Giderme

### Telegram bildirimi gelmiyorsa
- ✅ Chat ID'nin **insan ID'si** olduğundan emin ol (bot ID'si değil)
- ✅ TELEGRAM_TOKEN ve TELEGRAM_CHAT_ID doğru mu kontrol et
- ✅ Bot'u Telegram'da başlat (@BotName'i aç)

### Sakai'ye giriş başarısız oluyorsa
- ✅ Kullanıcı adı ve şifresi doğru mu?
- ✅ Sakai hesabın aktif mi?

### Duyuru gelmiyorsa
- ✅ GitHub Actions → Logs'ta hata var mı bak
- ✅ Sakai'de gerçekten yeni duyuru var mı?
- ✅ 30 dakika bekle (otomatik çalışma süresi)

## Dosya Yapısı

```
debis_bot/
├── sakai_bot_final.py          # Ana bot
├── requirements.txt            # Bağımlılıklar
├── .env.example               # Ayarlar şablonu
├── README.md                  # İngilizce dokümantasyon
├── README.tr.md              # Türkçe dokümantasyon (bu)
└── .github/workflows/
    └── sakai_check.yml       # GitHub Actions ayarı
```

## Lisans

MIT

## Sorular?

Sorun olursa GitHub Issues'de bildir! 🚀
