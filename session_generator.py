# -----------------------------------------------------------------------------
# Project: GagaraGogo Userbot
# Author: chaolcam (https://github.com/chaolcam/gagaragogo-userbot)
# License: MIT License
# Copyright (c) 2026 chaolcam
#
# Module: GagaraGogo In-Memory Session Generator (session_generator.py)
# Security: SIFIR LOGLAMA VE KAYIT. Diske hiçbir .session dosyası yazılmaz.
# -----------------------------------------------------------------------------

import asyncio
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, PasswordHashInvalid

class GgrSessionGenerator:
    """Tamamen RAM bellekte çalışan Pyrogram V2 String Session üreticisi."""

    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = None
        self.phone_code_hash = None
        self.client = None

    async def initialize(self):
        # In-memory client oluştur
        self.client = Client(
            name="ggr_temp_session",
            api_id=self.api_id,
            api_hash=self.api_hash,
            in_memory=True
        )
        await self.client.connect()

    async def send_code(self, phone: str) -> dict:
        """Kullanıcının Telegram hesabına MTProto onay kodunu gönderir."""
        self.phone = phone.strip()
        if not self.client:
            await self.initialize()

        sent = await self.client.send_code(self.phone)
        self.phone_code_hash = sent.phone_code_hash
        return {
            "status": True,
            "phone_code_hash": self.phone_code_hash,
            "type": str(sent.type)
        }

    async def sign_in_code(self, code: str) -> dict:
        """Gelen 5 haneli SMS/Telegram kodunu onaylar. 2FA gerekirse bildirir."""
        if not self.client or not self.phone_code_hash:
            raise Exception("Önce onay kodu gönderilmelidir.")

        try:
            signed_user = await self.client.sign_in(
                phone_number=self.phone,
                phone_code_hash=self.phone_code_hash,
                phone_code=code.strip()
            )
            session_str = await self.client.export_session_string()
            return {
                "status": "success",
                "session": session_str,
                "user": signed_user
            }
        except SessionPasswordNeeded:
            return {
                "status": "2fa_needed"
            }
        except PhoneCodeInvalid:
            raise Exception("Girdiğiniz onay kodu hatalı!")
        except PhoneCodeExpired:
            raise Exception("Onay kodunun süresi dolmuş! Lütfen işlemi baştan başlatın.")

    async def sign_in_2fa(self, password: str) -> dict:
        """2 Adımlı Doğrulama (2FA) bulut şifresini onaylayıp session üretir."""
        if not self.client:
            raise Exception("Oturum başlatılamadı.")

        try:
            await self.client.check_password(password=password.strip())
            session_str = await self.client.export_session_string()
            signed_user = await self.client.get_me()
            return {
                "status": "success",
                "session": session_str,
                "user": signed_user
            }
        except PasswordHashInvalid:
            raise Exception("İki Adımlı Doğrulama (2FA) şifreniz hatalı!")

    async def disconnect(self):
        """İstemciyi kapat ve hafızayı temizle."""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
            self.client = None
        self.phone = None
        self.phone_code_hash = None

# Uyumluluk aliası
SessionGenerator = GgrSessionGenerator
