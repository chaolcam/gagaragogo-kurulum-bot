# -----------------------------------------------------------------------------
# Project: GagaraGogo Setup Bot
# Component: my_telegram.py
# Author: chaolcam (https://github.com/chaolcam/gagaragogo-userbot)
# License: GNU GPL v3.0
# Copyright (c) 2026 chaolcam
# -----------------------------------------------------------------------------
import re
import requests
from bs4 import BeautifulSoup

GGR_MYTG_BASE = "https://my.telegram.org"

class GgrMyTelegramClient:
    """my.telegram.org web portalı üzerinden API_ID ve API_HASH alan/oluşturan otomasyon sınıfı."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": GGR_MYTG_BASE,
            "Referer": f"{GGR_MYTG_BASE}/auth"
        })
        self.random_hash = None
        self.phone = None

    def send_password(self, phone: str) -> dict:
        """Kullanıcının telefonuna Telegram resmi servisinden web giriş kodunu gönderir."""
        # Numarayı sadece rakam ve baştaki + içerecek şekilde temizle (boşlukları sil)
        temiz_numara = re.sub(r'[^0-9+]', '', phone.strip())
        if not temiz_numara.startswith("+"):
            temiz_numara = "+" + temiz_numara
        self.phone = temiz_numara

        url = f"{GGR_MYTG_BASE}/auth/send_password"
        payload = {"phone": self.phone}
        
        resp = self.session.post(url, data=payload, timeout=15)
        if resp.status_code != 200:
            raise Exception(f"Telegram web servisi yanıt vermedi (Hata Kodu: {resp.status_code}).")
            
        try:
            data = resp.json()
        except Exception:
            text_resp = resp.text.strip()
            if "too many" in text_resp.lower() or "flood" in text_resp.lower():
                raise Exception("Telegram web servisi geçici istek sınırı koydu (Too many requests). Lütfen birkaç dakika bekleyin veya resmi API seçeneğini kullanın.")
            elif "invalid" in text_resp.lower():
                raise Exception("Geçersiz telefon numarası formatı! Numaranızı +905xxxxxxxxx şeklinde yazınız.")
            raise Exception(f"Telegram web servisi yanıtı: {text_resp[:120]}")
            
        if "random_hash" not in data:
            raise Exception("Telegram web onay kodu gönderilemedi. Numaranızı kontrol edin (+905xxxxxxxxx).")
            
        self.random_hash = data["random_hash"]
        return {"status": True, "random_hash": self.random_hash}

    def login(self, password: str) -> bool:
        """Kullanıcının Telegram'a gelen harfli/sayılı web kodunu kullanarak my.telegram.org'a giriş yapar."""
        if not self.phone or not self.random_hash:
            raise Exception("Önce telefon numarası girilmeli ve onay kodu istenmelidir.")
            
        url = f"{GGR_MYTG_BASE}/auth/login"
        payload = {
            "phone": self.phone,
            "random_hash": self.random_hash,
            "password": password.strip()
        }
        
        resp = self.session.post(url, data=payload, timeout=15)
        if resp.status_code != 200 or resp.text.strip() != "true":
            raise Exception("Girdiğiniz web onay kodu hatalı veya süresi dolmuş!")
            
        return True

    def get_or_create_app(self) -> dict:
        """
        Giriş yapılmış oturumdan kullanıcının API_ID ve API_HASH değerlerini çeker.
        Kullanıcının henüz bir uygulaması yoksa 'GagaraGogo Userbot' adıyla otomatik oluşturur.
        """
        apps_url = f"{GGR_MYTG_BASE}/apps"
        resp = self.session.get(apps_url, timeout=15)
        html = resp.text

        # 1. Mevcut uygulamayı doğrudan regex ile tara (my.telegram.org HTML yapısı)
        # my.telegram.org örneği:
        # <label for="app_api_id">App api_id:</label> ... <strong>123456</strong>
        # <label for="app_api_hash">App api_hash:</label> ... <span ...>0123456789abcdef0123456789abcdef</span>
        id_match = re.search(r'app_api_id.*?(\d{5,12})', html, re.DOTALL | re.IGNORECASE) or \
                   re.search(r'<strong>\s*(\d{5,12})\s*</strong>', html)
                   
        hash_match = re.search(r'app_api_hash.*?([0-9a-f]{32})', html, re.DOTALL | re.IGNORECASE) or \
                     re.search(r'([0-9a-f]{32})', html)

        if id_match and hash_match:
            return {
                "api_id": int(id_match.group(1)),
                "api_hash": str(hash_match.group(1))
            }

        # 2. Uygulama henüz yoksa, oluşturma formunu gönder
        hash_match_csrf = re.search(r'name="hash"\s+value="([a-zA-Z0-9_-]+)"', html)
        if not hash_match_csrf:
            if "login" in resp.url.lower():
                raise Exception("my.telegram.org oturumu kapandı. Lütfen /start ile tekrar deneyin.")
            raise Exception("Telegram uygulama oluşturma formu CSRF anahtarı alınamadı.")
            
        csrf_hash = hash_match_csrf.group(1)

        create_payload = {
            "hash": csrf_hash,
            "app_title": "GagaraGogo Userbot",
            "app_short_name": "gagaragogo",
            "app_url": "https://github.com/chaolcam/gagaragogo-userbot",
            "app_platform": "android",
            "app_desc": "GagaraGogo Modular Telegram Userbot"
        }

        self.session.post(f"{GGR_MYTG_BASE}/apps/create", data=create_payload, timeout=15)
        
        # Yeniden /apps sayfasına git ve değerleri çek
        resp_after = self.session.get(apps_url, timeout=15)
        html_after = resp_after.text

        id_match_after = re.search(r'app_api_id.*?(\d{5,12})', html_after, re.DOTALL | re.IGNORECASE) or \
                         re.search(r'<strong>\s*(\d{5,12})\s*</strong>', html_after)
                         
        hash_match_after = re.search(r'app_api_hash.*?([0-9a-f]{32})', html_after, re.DOTALL | re.IGNORECASE) or \
                           re.search(r'([0-9a-f]{32})', html_after)
        
        if id_match_after and hash_match_after:
            return {
                "api_id": int(id_match_after.group(1)),
                "api_hash": str(hash_match_after.group(1))
            }

        raise Exception("API ID ve API HASH my.telegram.org üzerinden çekilemedi. Lütfen my.telegram.org sayfasını kontrol edin.")

    def close(self):
        """Oturumu temizle ve hafızadan düşür."""
        try:
            self.session.close()
        except Exception:
            pass
        self.session = None
        self.phone = None
        self.random_hash = None

# Uyumluluk aliası
MyTelegramClient = GgrMyTelegramClient
