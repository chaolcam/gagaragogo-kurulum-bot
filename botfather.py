# -----------------------------------------------------------------------------
# Project: GagaraGogo Setup Bot
# Component: botfather.py
# Author: chaolcam (https://github.com/chaolcam/gagaragogo-userbot)
# License: GNU GPL v3.0
# Copyright (c) 2026 chaolcam
# -----------------------------------------------------------------------------
import re
import random
import string
import asyncio
from pyrogram import Client

def ggr_get_next_bot_counter():
    """Bot sırasını (1, 2, 3...) takip eden sayaç."""
    import os
    counter_file = "bot_counter.txt"
    count = 1
    if os.path.exists(counter_file):
        try:
            with open(counter_file, "r", encoding="utf-8") as f:
                count = int(f.read().strip()) + 1
        except Exception:
            count = 1
    try:
        with open(counter_file, "w", encoding="utf-8") as f:
            f.write(str(count))
    except Exception:
        pass
    return count

async def ggr_create_bot_via_botfather(api_id: int, api_hash: str, session_str: str) -> dict:
    """
    Kullanıcının kendi hesabı üzerinden @BotFather'a bağlanarak:
    1. /newbot komutu ile yeni bot açar (Örn: GagaraGogo Bot #5).
    2. Benzersiz kullanıcı adı verir.
    3. HTTP API Token'ı çeker.
    4. /setinline komutuyla botun INLINE MODUNU otomatik etkinleştirir (Menü butonları için şart).
    """
    client = Client(
        name="ggr_bf_temp",
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_str,
        in_memory=True
    )
    await client.connect()

    try:
        bot_father = "BotFather"
        counter = ggr_get_next_bot_counter()
        bot_title = f"GagaraGogo Bot #{counter}"
        
        # 1. /cancel gönderip önceki yarım kalmış konuşmaları temizle
        await client.send_message(bot_father, "/cancel")
        await asyncio.sleep(1.5)

        # 2. /newbot gönder
        await client.send_message(bot_father, "/newbot")
        await asyncio.sleep(2)

        # 3. Bot ismini gönder
        await client.send_message(bot_father, bot_title)
        await asyncio.sleep(2)

        # 4. Benzersiz username üret ve gönder (Örn: ggr_5_x7k2_bot)
        rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        bot_username = f"ggr_{counter}_{rand_suffix}_bot"
        await client.send_message(bot_father, bot_username)
        await asyncio.sleep(3)

        # 5. BotFather'ın son mesajını oku ve token'ı ayıkla
        token = None
        async for msg in client.get_chat_history(bot_father, limit=3):
            text = msg.text or ""
            match = re.search(r'(\d{8,10}:[a-zA-Z0-9_-]{35})', text)
            if match:
                token = match.group(1)
                break

        if not token:
            # Alternatif deneme (kullanıcı adı alınmışsa sonuna random ekleyip tekrar dene)
            rand_suffix2 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            bot_username = f"ggr_bot_{counter}_{rand_suffix2}_bot"
            await client.send_message(bot_father, bot_username)
            await asyncio.sleep(3)
            async for msg in client.get_chat_history(bot_father, limit=3):
                text = msg.text or ""
                match = re.search(r'(\d{8,10}:[a-zA-Z0-9_-]{35})', text)
                if match:
                    token = match.group(1)
                    break

        if not token:
            raise Exception("BotFather'dan token alınamadı. Lütfen BotFather limitinizi kontrol edin.")

        # =======================================================
        # 6. INLINE MODU AÇMA (/setinline)
        # =======================================================
        await asyncio.sleep(2)
        await client.send_message(bot_father, "/setinline")
        await asyncio.sleep(2)

        # Hangi bot? -> bot_username gönder
        await client.send_message(bot_father, f"@{bot_username}")
        await asyncio.sleep(2)

        # Placeholder metni -> "GagaraGogo Menü"
        await client.send_message(bot_father, "GagaraGogo Menü")
        await asyncio.sleep(1.5)

        return {
            "token": token,
            "username": bot_username,
            "title": bot_title,
            "counter": counter
        }

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

# Uyumluluk aliası
create_bot_via_botfather = ggr_create_bot_via_botfather
