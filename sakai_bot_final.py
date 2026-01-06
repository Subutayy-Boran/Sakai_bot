# -*- coding: utf-8 -*-
import json
import os
import time
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import requests
import re

# UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- TELEGRAM AYARLARI (ENV ile konfigüre edilebilir) ---
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- SAKAI AYARLARI (ENV ile konfigüre edilebilir) ---
SAKAI_URL = os.getenv("SAKAI_URL", "https://online.deu.edu.tr/portal")
SAKAI_DUYURU_URL = os.getenv("SAKAI_DUYURU_URL", "https://online.deu.edu.tr/portal/site/8661eecd-4a01-4a2a-a0ae-7722b165e914/tool/1f87c11b-7dbd-4619-b91d-a2f9c37e1e7c?panel=Main")
SAKAI_USERNAME = os.getenv("SAKAI_USERNAME", "")
SAKAI_PASSWORD = os.getenv("SAKAI_PASSWORD", "")

# Headless kontrolü (use "1" or "true")
HEADLESS = os.getenv("HEADLESS", "0").lower() in ("1", "true", "yes")

# --- DOSYALAR ---
DUYURULAR_FILE = "duyurular.json"

def telegram_bildirim_gonder(baslik, icerik):
    """Telegram'a bildirim gönder"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    mesaj = f"""
<b>📢 YENİ DUYURU</b>

<b>{baslik}</b>

{icerik}
"""
    
    veri = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=veri)
        if response.status_code == 200:
            print(f"[✓] Telegram bildirimi gönderildi: {baslik}")
        else:
            print(f"[✗] Telegram hatası: {response.text}")
    except Exception as e:
        print(f"[✗] Telegram bağlantı hatası: {e}")


def fetch_content_from_href(driver, href):
    """Verilen href'i yeni sekmede açıp içerik bulmaya çalışır, string döner."""
    icerik = ''
    try:
        driver.execute_script('window.open(arguments[0]);', href)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)

        selectors = ['.announcementBody', '.announcement-content', '.msgBody', '#main', '.portletBody', '.sakai-content', '.content', 'article', '#content']
        content_text = ''
        for selector in selectors:
            try:
                c = driver.find_element(By.CSS_SELECTOR, selector)
                content_text = c.text.strip()
                if content_text:
                    break
            except:
                continue

        if not content_text:
            try:
                candidates = driver.find_elements(By.XPATH, "//*[contains(@id,'msg') or contains(@id,'announcement') or contains(@class,'msg') or contains(@class,'announcement')]")
                for c in candidates:
                    t = c.text.strip()
                    if t and len(t) > 20:
                        content_text = t
                        break
            except:
                pass

        if not content_text:
            try:
                content_text = driver.find_element(By.TAG_NAME, 'body').text.strip()
            except:
                content_text = ''

        icerik = content_text
    except Exception:
        icerik = ''
    finally:
        try:
            driver.close()
        except:
            pass
        try:
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass

    return icerik

def sakai_duyurlari_al():
    """Sakai'ye giriş yap ve Duyuru panelini oku"""
    
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

    # Selenium Manager will find appropriate driver/browser
    driver = webdriver.Edge(options=options)
    duyurular = []
    
    try:
        # Portal ana sayfasını aç
        driver.get(SAKAI_URL)
        time.sleep(5)

        # Otomatik giriş: eğer bullhorn görünmüyorsa kullanıcı bilgileriyle giriş dene
        logged_in = False
        try:
            driver.find_element(By.ID, 'Mrphs-bullhorn')
            logged_in = True
        except:
            logged_in = False

        if not logged_in and SAKAI_USERNAME and SAKAI_PASSWORD:
            print("[→] Otomatik giriş denemesi yapılıyor...")

            def try_fill_and_submit(context_driver):
                try:
                    u = None
                    p = None
                    # username selectors
                    for sel in [('name','eid'),('name','username'),('id','eid'),('id','username'),('name','j_username'),('id','j_username')]:
                        try:
                            u = context_driver.find_element(getattr(By, sel[0].upper()), sel[1])
                            break
                        except:
                            u = None
                    # password selectors
                    for sel in [('name','pw'),('name','password'),('id','pw'),('id','password'),('name','j_password'),('id','j_password')]:
                        try:
                            p = context_driver.find_element(getattr(By, sel[0].upper()), sel[1])
                            break
                        except:
                            p = None

                    if u and p:
                        try:
                            u.clear()
                        except:
                            pass
                        u.send_keys(SAKAI_USERNAME)
                        try:
                            p.clear()
                        except:
                            pass
                        p.send_keys(SAKAI_PASSWORD)

                        submitted = False
                        # submit button candidates
                        for bsel in [(By.CSS_SELECTOR, "input[type='submit']"), (By.CSS_SELECTOR, "button[type='submit']"), (By.XPATH, "//button[contains(., 'Giriş') or contains(., 'Login')]") , (By.XPATH, "//input[@type='submit']")]:
                            try:
                                btn = context_driver.find_element(bsel[0], bsel[1])
                                try:
                                    btn.click()
                                except:
                                    context_driver.execute_script('arguments[0].click();', btn)
                                submitted = True
                                break
                            except:
                                continue

                        if not submitted:
                            try:
                                p.submit()
                                submitted = True
                            except:
                                pass

                        return submitted
                except:
                    return False

            submitted = False
            try:
                submitted = try_fill_and_submit(driver)
            except:
                submitted = False

            if not submitted:
                # try inside iframes
                try:
                    frames = driver.find_elements(By.TAG_NAME, 'iframe')
                except:
                    frames = []
                for frame in frames:
                    try:
                        driver.switch_to.frame(frame)
                        if try_fill_and_submit(driver):
                            submitted = True
                            driver.switch_to.default_content()
                            break
                        driver.switch_to.default_content()
                    except:
                        try:
                            driver.switch_to.default_content()
                        except:
                            pass

            if submitted:
                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'Mrphs-bullhorn')))
                    print("[✓] Otomatik giriş başarılı")
                except:
                    print("[!] Otomatik giriş denendi ama bullhorn bulunamadı; bekleniyor...")
                    time.sleep(3)

        # Eğer bildirim (bullhorn) varsa, tıklayıp oradaki linkleri al
        try:
            bull = driver.find_element(By.ID, 'Mrphs-bullhorn')
            counter = 0
            try:
                cnt = bull.find_element(By.ID, 'bullhorn-counter')
                counter = int(re.sub(r"\D", "", cnt.text.strip() or "0"))
            except:
                try:
                    cnt2 = bull.find_element(By.CLASS_NAME, 'bullhorn-counter-red')
                    counter = int(re.sub(r"\D", "", cnt2.text.strip() or "0"))
                except:
                    counter = 0

            if counter > 0:
                print(f"[→] {counter} yeni bildirim var, bildirim paneli açılıyor...")
                try:
                    driver.execute_script('arguments[0].click();', bull)
                except:
                    try:
                        bull.click()
                    except:
                        pass
                time.sleep(2)

                # Bildirim panelindeki announcement linklerini bul
                links = driver.find_elements(By.XPATH, "//a[contains(@href, '/announcement/msg/') or contains(@href, '/announcement') or contains(@href, 'directtool')]")
                found = 0
                for a in links:
                    try:
                        href = a.get_attribute('href')
                        link_text = a.text.strip() or ''
                        # varsa author span'ını al
                        author = None
                        try:
                            author_span = a.find_element(By.CSS_SELECTOR, '.portal-bullhorn-display-name')
                            author = author_span.text.strip()
                        except:
                            author = None

                        # Başlık tahmini: author mevcutsa metinden ayıkla, değilse link_text kullan
                        baslik_guess = link_text
                        if author and author in link_text:
                            try:
                                after = link_text.split(author, 1)[1].strip()
                                baslik_guess = after if after else link_text
                            except:
                                baslik_guess = link_text

                        if href:
                            content = fetch_content_from_href(driver, href)
                            duyurular.append({
                                'baslik': baslik_guess or href,
                                'icerik': content,
                                'tarih': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            found += 1
                    except:
                        pass

                if found:
                    print(f"[✓] {found} bildirim içeriği okundu")
                    return duyurular
        except Exception:
            pass

        # Duyuru panelini ara
        print("[→] Duyuru paneli aranıyor...")

        # Çeşitli XPath'ler dene
        duyuru_elements = []

        # XPath 1: Duyuru başlığı içerenler
        try:
            duyuru_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Duyuru') or contains(text(), 'Announcement')]")
            print(f"[!] Duyuru elementi bulundu (XPath 1): {len(duyuru_elements)}")
        except:
            pass

        # Eğer bulunamazsa, panel container'ı ara
        if not duyuru_elements:
            try:
                panel = driver.find_element(By.XPATH, "//div[contains(@class, 'announcement') or contains(@class, 'news') or contains(@class, 'duyuru')]")
                duyuru_elements = panel.find_elements(By.XPATH, ".//*[contains(@class, 'item') or contains(@class, 'entry')]")
                print(f"[!] Panel container'ından öğeler bulundu: {len(duyuru_elements)}")
            except:
                pass

        # Tüm divleri listele ve duyuru araştır
        if not duyuru_elements:
            print("[!] Standart selectors çalışmadı, sayfadaki tüm öğeler kontrol ediliyor...")
            
            # Sayfadaki tüm öğeleri al ve kontrol et
            all_divs = driver.find_elements(By.XPATH, "//div | //li | //article")
            
            for elem in all_divs[:120]:  # Daha fazla kontrol
                try:
                    text = elem.text
                    if text and len(text) > 10:  # En az 10 karakter
                        # "Duyuru" kelimesini içeriyor mu kontrol et
                        if any(word in text.lower() for word in ['duyuru', 'announcement', 'başlık', 'title', 'subject']):
                            duyuru_elements.append(elem)
                except:
                    pass

        # Duyurular'ı parse et (daha iyi içerik yakalamak için link varsa aç)
        print(f"[→] {len(duyuru_elements)} potansiyel duyuru öğesi kontrol ediliyor...")
        
        for elem in duyuru_elements[:20]:  # Max 20
            try:
                text = elem.text.strip()
                if not text or len(text) < 5:
                    continue

                # Deneyecek: başlık için heading veya ilk satır
                baslik = None
                for tag in ['h1','h2','h3','h4','h5','strong','b','a']:
                    try:
                        el = elem.find_element(By.TAG_NAME, tag)
                        val = el.text.strip()
                        if val:
                            baslik = val
                            break
                    except:
                        pass

                if not baslik:
                    satirlar = text.split('\n')
                    baslik = satirlar[0]

                icerik = ''

                # Eğer içinde link varsa, takip et ve detay sayfasından içeriği al
                try:
                    a = elem.find_element(By.TAG_NAME, 'a')
                    href = a.get_attribute('href')
                    if href:
                        # open link in new tab and switch
                        driver.execute_script('window.open(arguments[0]);', href)
                        driver.switch_to.window(driver.window_handles[-1])
                        # wait for page
                        time.sleep(2)
                        content_text = ''

                        # If URL pattern indicates announcement detail, try specific selectors
                        try:
                            url_lower = href.lower()
                        except:
                            url_lower = ''

                        selectors = []
                        if '/announcement/msg/' in url_lower or 'directtool' in url_lower:
                            selectors = ['.announcementBody', '.announcement-content', '.msgBody', '#main', '.portletBody', '.sakai-content']
                        else:
                            selectors = ['.announcementBody', '.announcement-content', '.content', 'article', '#content', '#main']

                        for selector in selectors:
                            try:
                                c = driver.find_element(By.CSS_SELECTOR, selector)
                                content_text = c.text.strip()
                                if content_text:
                                    break
                            except:
                                continue

                        # As a fallback, try to find element with id or class containing 'msg' or 'announcement'
                        if not content_text:
                            try:
                                candidates = driver.find_elements(By.XPATH, "//*[contains(@id,'msg') or contains(@id,'announcement') or contains(@class,'msg') or contains(@class,'announcement')]")
                                for c in candidates:
                                    t = c.text.strip()
                                    if t and len(t) > 20:
                                        content_text = t
                                        break
                            except:
                                pass

                        if not content_text:
                            # fallback to whole body
                            try:
                                content_text = driver.find_element(By.TAG_NAME, 'body').text.strip()
                            except:
                                content_text = ''

                        icerik = content_text
                        # close tab and switch back
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    # fallback: use element's remaining text
                    satirlar = text.split('\n')
                    icerik = '\n'.join(satirlar[1:]).strip() if len(satirlar) > 1 else ''

                duyurular.append({
                    "baslik": baslik.strip(),
                    "icerik": icerik.strip(),
                    "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception:
                pass
        # Duyuru panelini ara
        print("[→] Duyuru paneli aranıyor...")
        
        # Çeşitli XPath'ler dene
        duyuru_elements = []
        
        # XPath 1: Duyuru başlığı içerenler
        try:
            duyuru_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Duyuru') or contains(text(), 'Announcement')]")
            print(f"[!] Duyuru elementi bulundu (XPath 1): {len(duyuru_elements)}")
        except:
            pass
        
        # Eğer bulunamazsa, panel container'ı ara
        if not duyuru_elements:
            try:
                panel = driver.find_element(By.XPATH, "//div[contains(@class, 'announcement') or contains(@class, 'news') or contains(@class, 'duyuru')]")
                duyuru_elements = panel.find_elements(By.XPATH, ".//*[contains(@class, 'item') or contains(@class, 'entry')]")
                print(f"[!] Panel container'ından öğeler bulundu: {len(duyuru_elements)}")
            except:
                pass
        
        # Tüm divleri listele ve duyuru araştır
        if not duyuru_elements:
            print("[!] Standart selectors çalışmadı, sayfadaki tüm öğeler kontrol ediliyor...")
            
            # Sayfadaki tüm öğeleri al ve kontrol et
            all_divs = driver.find_elements(By.XPATH, "//div | //li | //article")
            
            for elem in all_divs[:50]:  # İlk 50'yi kontrol et
                try:
                    text = elem.text
                    if text and len(text) > 10:  # En az 10 karakter
                        # "Duyuru" kelimesini içeriyor mu kontrol et
                        if any(word in text.lower() for word in ['duyuru', 'announcement', 'başlık', 'title', 'subject']):
                            duyuru_elements.append(elem)
                except:
                    pass
        
        # Duyurular'ı parse et
        print(f"[→] {len(duyuru_elements)} potansiyel duyuru öğesi kontrol ediliyor...")
        
        for elem in duyuru_elements[:10]:  # Max 10
            try:
                text = elem.text.strip()
                if text and len(text) > 5:
                    # Başlık ve içerik olarak böl (ilk satır başlık, rest içerik)
                    satırlar = text.split('\n')
                    baslik = satırlar[0]
                    icerik = '\n'.join(satırlar[1:]) if len(satırlar) > 1 else ""
                    
                    duyurular.append({
                        "baslik": baslik.strip(),
                        "icerik": icerik.strip(),
                        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            except:
                pass
        
        print(f"[✓] {len(duyurular)} duyuru başarıyla okundu")
        
        # Sayfayı görüntüle (debug için)
        print("\n[!] Sayfadaki Duyuru Paneli: ")
        print("=" * 50)
        for i, d in enumerate(duyurular, 1):
            print(f"\n{i}. Başlık: {d['baslik']}")
            print(f"   İçerik: {d['icerik'][:100]}...")
        print("=" * 50)
        
        return duyurular
        
    except Exception as e:
        print(f"[✗] Hata: {e}")
        import traceback
        traceback.print_exc()
        telegram_bildirim_gonder("BOT HATASI", f"Sakai botunda hata oluştu:\n{str(e)}")
        return []
    
    finally:
        time.sleep(2)
        driver.quit()

def duyurlari_kaydet(duyurular):
    """Duyuruları JSON dosyasına kaydet"""
    if os.path.exists(DUYURULAR_FILE):
        with open(DUYURULAR_FILE, 'r', encoding='utf-8') as f:
            eski_duyurular = json.load(f)
    else:
        eski_duyurular = []
    
    with open(DUYURULAR_FILE, 'w', encoding='utf-8') as f:
        json.dump(duyurular, f, ensure_ascii=False, indent=2)
    
    return eski_duyurular

def yeni_duyurulari_bul(yeni_duyurular, eski_duyurular):
    """Yeni duyuruları tespit et"""
    yeni = []
    eski_basliklari = {d["baslik"] for d in eski_duyurular}
    
    for duyuru in yeni_duyurular:
        if duyuru["baslik"] not in eski_basliklari:
            yeni.append(duyuru)
    
    return yeni

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print(f"SAKAI DUYURU BOT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Duyuruları al
    yeni_duyurular = sakai_duyurlari_al()
    
    if not yeni_duyurular:
        print("[!] Duyuru bulunamadı")
        return
    
    # Eski duyuruları al
    eski_duyurular = duyurlari_kaydet(yeni_duyurular)
    
    # Yeni olanları tespit et
    yeni = yeni_duyurulari_bul(yeni_duyurular, eski_duyurular)
    
    if yeni:
        print(f"\n[✓] {len(yeni)} YENİ DUYURU BULUNDU!")
        for duyuru in yeni:
            telegram_bildirim_gonder(duyuru["baslik"], duyuru["icerik"])
            time.sleep(1)  # Rate limiting
    else:
        print("[✓] Yeni duyuru yok, hepsi zaten okundu")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
