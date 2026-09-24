# -----------------------------------------------------------------------------
# Project: GagaraGogo Setup Bot
# Component: bot.py
# Author: chaolcam (https://github.com/chaolcam/gagaragogo-userbot)
# License: GNU GPL v3.0
# Copyright (c) 2026 chaolcam
# -----------------------------------------------------------------------------
import os
import re
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)

from my_telegram import GgrMyTelegramClient
from session_generator import GgrSessionGenerator
from botfather import ggr_create_bot_via_botfather
from render_deployer import GgrRenderDeployer

# GagaraGogo Bot Ayarları
GGR_BOT_TOKEN = os.getenv("SETUP_BOT_TOKEN") or os.getenv("BOT_TOKEN")
GGR_API_ID = int(os.getenv("SETUP_API_ID") or os.getenv("API_ID") or 2040)
GGR_API_HASH = os.getenv("SETUP_API_HASH") or os.getenv("API_HASH") or "b18441a1ff607e10a989891a5462e627"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def ggr_get_asset_photo(filename: str) -> str:
    """Görseli yerel assets klasöründen, yoksa doğrudan GitHub raw CDN'inden döndürür."""
    local_path = os.path.join(ASSETS_DIR, filename)
    if os.path.isfile(local_path):
        return local_path
    # Hugging Face veya uzak sunucuda assets klasörü yoksa doğrudan GitHub'dan çek
    return f"https://raw.githubusercontent.com/chaolcam/gagaragogo-kurulum-bot/main/assets/{filename}"

if not GGR_BOT_TOKEN:
    logging.warning("⚠️ [GAGARAGOGO] BOT_TOKEN tanımlanmadı. Lütfen Hugging Face Secrets içerisine BOT_TOKEN giriniz.")

# Kullanıcı geçici oturum durumları (İşlem bitince anında RAM'den silinir)
ggr_user_sessions = {}
ggr_user_timers = {}

def ggr_get_user_data(user_id):
    if user_id not in ggr_user_sessions:
        ggr_user_sessions[user_id] = {}
    return ggr_user_sessions[user_id]

def ggr_wipe_user_data(user_id):
    """Kullanıcının tüm hassas verilerini RAM'den tamamen siler."""
    if user_id in ggr_user_sessions:
        data = ggr_user_sessions[user_id]
        if "my_tg" in data and data["my_tg"]:
            data["my_tg"].close()
        if "sess_gen" in data and data["sess_gen"]:
            asyncio.create_task(data["sess_gen"].disconnect())
        del ggr_user_sessions[user_id]

def ggr_cancel_user_timer(user_id):
    """Kullanıcının bekleyen temizlik görevini iptal eder."""
    if user_id in ggr_user_timers:
        try:
            ggr_user_timers[user_id].cancel()
        except Exception:
            pass
        ggr_user_timers.pop(user_id, None)

# Pyrogram Bot İstemcisi
ggr_app = Client(
    name="ggr_setup_bot",
    api_id=GGR_API_ID,
    api_hash=GGR_API_HASH,
    bot_token=GGR_BOT_TOKEN,
    in_memory=True
)

def ggr_get_lang_selection(first_name: str):
    """Dil seçim ekranını oluşturur."""
    metin = (
        f"👋 <b>Merhaba {first_name}! / Hello {first_name}!</b>\n\n"
        f"🤖 <b>GagaraGogo Userbot Kurulum Asistanı</b>\n"
        f"Lütfen devam etmek istediğiniz dili seçin:\n"
        f"Please select your preferred language:"
    )
    butonlar = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇹🇷 Türkçe", callback_data="ggr_set_lang_tr"),
            InlineKeyboardButton("🇬🇧 English", callback_data="ggr_set_lang_en")
        ]
    ])
    return metin, butonlar

def ggr_get_start_content(first_name: str, lang: str = "tr"):
    """Karşılama metni ve butonlarını seçilen dilde üretir."""
    if lang == "en":
        metin = (
            f"👋 <b>Hello {first_name}!</b>\n\n"
            f"🤖 Welcome to <b>GagaraGogo Userbot Automated Setup Assistant</b>.\n\n"
            f"With this assistant, without writing a single line of code:\n"
            f"1️⃣ Connect your Render account,\n"
            f"2️⃣ Retrieve API ID and HASH from <code>my.telegram.org</code>,\n"
            f"3️⃣ Generate your Pyrogram String Session,\n"
            f"4️⃣ Create an assistant bot automatically via <code>@BotFather</code>,\n"
            f"5️⃣ Deploy your userbot to Render with a 24/7 Uptime monitor!\n\n"
            f"🔒 <b>Security & Zero Storage:</b>\n"
            f"<i>Your phone numbers, passwords, and sessions are NEVER stored.</i>\n\n"
            f"⏳ <b>Privacy Protection:</b>\n"
            f"• Completed setups: <b>After 5 minutes</b>\n"
            f"• Cancelled or idle setups: <b>After 30 minutes</b>\n"
            f"all messages in this chat will be completely and automatically wiped!\n\n"
            f"⚠️ <b>Disclaimer:</b>\n"
            f"<i>Userbots carry potential risks under Telegram Terms of Service. You are solely responsible for your account actions.</i>\n\n"
            f"📁 <b>Source Code:</b>\n"
            f"<a href='https://github.com/chaolcam/gagaragogo-kurulum-bot'>github.com/chaolcam/gagaragogo-kurulum-bot</a>"
        )
        butonlar = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Start Setup", callback_data="ggr_kur_basla")],
            [InlineKeyboardButton("🗑️ Remove Bot from Account", callback_data="ggr_kaldir_basla")],
            [InlineKeyboardButton("🌐 Dil / Language (TR / EN)", callback_data="ggr_lang_change")],
            [InlineKeyboardButton("ℹ️ Privacy & Security", callback_data="ggr_bilgi")],
            [InlineKeyboardButton("📁 GitHub Repository", url="https://github.com/chaolcam/gagaragogo-kurulum-bot")]
        ])
        return metin, butonlar

    metin = (
        f"👋 <b>Merhaba {first_name}!</b>\n\n"
        f"🤖 <b>GagaraGogo Userbot Otomatik Kurulum Asistanı</b>'na hoş geldiniz.\n\n"
        f"Bu asistan ile hiçbir kodlama yapmadan:\n"
        f"1️⃣ Render hesabınıza bağlanır,\n"
        f"2️⃣ <code>my.telegram.org</code> üzerinden API ID ve HASH alınır,\n"
        f"3️⃣ String Session üretilir,\n"
        f"4️⃣ <code>@BotFather</code> üzerinden otomatik yardımcı bot açılır,\n"
        f"5️⃣ Botunuz Render'a kurulur ve 7/24 Uptime linkiniz teslim edilir!\n\n"
        f"🔒 <b>Güvenlik & Sıfır Depolama:</b>\n"
        f"<i>Girdiğiniz telefon, şifre ve kodlar sunucularımızda ASLA depolanmaz.</i>\n\n"
        f"⏳ <b>Otomatik Gizlilik Koruması:</b>\n"
        f"• Başarılı kurulumlarda: <b>5 dakika sonra</b>\n"
        f"• Yarım kalan veya iptal edilen işlemlerde: <b>30 dakika sonra</b>\n"
        f"bu sohbetteki tüm mesajlar güvenliğiniz için otomatik olarak tamamen silinir!\n\n"
        f"⚠️ <b>Sorumluluk Reddi (Disclaimer):</b>\n"
        f"<i>Userbot kullanımı Telegram şartları gereği hesabınız için risk taşıyabilir. Hesabınızdan ve yaptığınız işlemlerden bizzat kendiniz sorumlusunuz; geliştiriciler hiçbir sorumluluk kabul etmez. Kuruluma başlayarak bu şartları peşinen kabul etmiş sayılırsınız.</i>\n\n"
        f"📁 <b>Açık Kaynak Kodları:</b>\n"
        f"<a href='https://github.com/chaolcam/gagaragogo-kurulum-bot'>github.com/chaolcam/gagaragogo-kurulum-bot</a>"
    )

    butonlar = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Kuruluma Başla", callback_data="ggr_kur_basla")],
        [InlineKeyboardButton("🗑️ Botumu Hesaptan Kaldır", callback_data="ggr_kaldir_basla")],
        [InlineKeyboardButton("🌐 Dil / Language (TR / EN)", callback_data="ggr_lang_change")],
        [InlineKeyboardButton("ℹ️ Güvenlik & Gizlilik", callback_data="ggr_bilgi")],
        [InlineKeyboardButton("📁 Kaynak Kodları (GitHub)", url="https://github.com/chaolcam/gagaragogo-kurulum-bot")]
    ])
    return metin, butonlar
    metin = (
        f"👋 <b>Merhaba {first_name}!</b>\n\n"
        f"🤖 <b>GagaraGogo Userbot Otomatik Kurulum Asistanı</b>'na hoş geldiniz.\n\n"
        f"Bu asistan ile hiçbir kodlama yapmadan:\n"
        f"1️⃣ Render hesabınıza bağlanır,\n"
        f"2️⃣ <code>my.telegram.org</code> üzerinden API ID ve HASH alınır,\n"
        f"3️⃣ String Session üretilir,\n"
        f"4️⃣ <code>@BotFather</code> üzerinden otomatik yardımcı bot açılır,\n"
        f"5️⃣ Botunuz Render'a kurulur ve 7/24 Uptime linkiniz teslim edilir!\n\n"
        f"🔒 <b>Güvenlik & Sıfır Depolama:</b>\n"
        f"<i>Girdiğiniz telefon, şifre ve kodlar sunucularımızda ASLA depolanmaz.</i>\n\n"
        f"⏳ <b>Otomatik Gizlilik Koruması:</b>\n"
        f"• Başarılı kurulumlarda: <b>5 dakika sonra</b>\n"
        f"• Yarım kalan veya iptal edilen işlemlerde: <b>30 dakika sonra</b>\n"
        f"bu sohbetteki tüm mesajlar güvenliğiniz için otomatik olarak tamamen silinir!\n\n"
        f"⚠️ <b>Sorumluluk Reddi (Disclaimer):</b>\n"
        f"<i>Userbot kullanımı Telegram şartları gereği hesabınız için risk taşıyabilir. Hesabınızdan ve yaptığınız işlemlerden bizzat kendiniz sorumlusunuz; geliştiriciler hiçbir sorumluluk kabul etmez. Kuruluma başlayarak bu şartları peşinen kabul etmiş sayılırsınız.</i>\n\n"
        f"📂 <b>Açık Kaynak Kodları:</b>\n"
        f"<a href='https://github.com/chaolcam/gagaragogo-kurulum-bot'>github.com/chaolcam/gagaragogo-kurulum-bot</a>"
    )

    butonlar = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Kuruluma Başla", callback_data="ggr_kur_basla")],
        [InlineKeyboardButton("🗑️ Botumu Hesaptan Kaldır", callback_data="ggr_kaldir_basla")],
        [InlineKeyboardButton("ℹ️ Güvenlik & Gizlilik", callback_data="ggr_bilgi")],
        [InlineKeyboardButton("📂 Kaynak Kodları (GitHub)", url="https://github.com/chaolcam/gagaragogo-kurulum-bot")]
    ])
    return metin, butonlar

async def ggr_otomatik_sohbet_temizleyici(client, user_id, first_name, delay=300, is_success=True):
    """
    Belirtilen süre bekler:
    1. Kullanıcıya 'Süre doldu, siliniyor...' uyarısı atar.
    2. Bu uyarıdan önceki İSTİSNASIZ BÜTÜN mesajları (noktalar, kullanıcı/bot mesajları) siler.
    3. Uyarı mesajını güvenli bilgilendirme ve ana menü butonları ile günceller.
    """
    try:
        await asyncio.sleep(delay)

        durum_metni = (
            "⏳ <b>Süre Doldu!</b>\n"
            "Güvenliğiniz için kurulum mesajları ve hassas veriler temizleniyor..."
            if is_success else
            "⏳ <b>Süre Doldu!</b>\n"
            "Güvenliğiniz için yarım kalan işlem ve sohbet geçmişi temizleniyor..."
        )
        try:
            notice_msg = await client.send_message(chat_id=user_id, text=durum_metni)
            notice_id = notice_msg.id
        except Exception:
            notice_msg = None
            notice_id = 999999999

        # notice_msg'den önceki TÜM mesaj ID'lerini (aradaki noktalar dahil) topluca sil
        min_id = max(1, notice_id - 400)
        msg_ids = list(range(min_id, notice_id))

        for i in range(0, len(msg_ids), 100):
            chunk = msg_ids[i:i+100]
            try:
                await client.delete_messages(chat_id=user_id, message_ids=chunk)
            except Exception:
                pass
            await asyncio.sleep(0.2)

        # Temizlik bitince notice_msg'i kalıcı güvenli durum mesajı ve butonlar ile güncelle
        if is_success:
            final_text = (
                "🔒 <b>Güvenlik Temizliği Tamamlandı!</b>\n\n"
                "Önceki tüm kurulum mesajları, hassas anahtarlarınız ve sohbet geçmişiniz gizliliğiniz için kalıcı olarak silinmiştir.\n\n"
                "✅ <b>Botunuz 7/24 kesintisiz çalışmaya devam etmektedir.</b>\n"
                "<i>(Kurulum ve erişim bilgileriniz Telegram Kayıtlı Mesajlar sohbetinizde saklanmaktadır.)</i>\n\n"
                "Botu kaldırmak veya yeniden işlem yapmak isterseniz aşağıdaki butonları kullanabilirsiniz:"
            )
        else:
            final_text = (
                "🔒 <b>Güvenlik Temizliği Tamamlandı!</b>\n\n"
                "Yarım kalan işlem ve sohbetteki tüm önceki mesajlar güvenliğiniz için kalıcı olarak silinmiştir.\n\n"
                "Yeniden başlamak veya botu kaldırmak isterseniz aşağıdaki butonları kullanabilirsiniz:"
            )

        final_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Yeniden Kuruluma Başla", callback_data="ggr_kur_basla")],
            [InlineKeyboardButton("🗑️ Botumu Hesaptan Kaldır", callback_data="ggr_kaldir_basla")],
            [InlineKeyboardButton("ℹ️ Güvenlik & Gizlilik", callback_data="ggr_bilgi")],
            [InlineKeyboardButton("📂 Kaynak Kodları (GitHub)", url="https://github.com/chaolcam/gagaragogo-kurulum-bot")]
        ])

        if notice_msg:
            try:
                await notice_msg.edit_text(final_text, reply_markup=final_buttons)
            except Exception:
                await client.send_message(chat_id=user_id, text=final_text, reply_markup=final_buttons)
        else:
            await client.send_message(chat_id=user_id, text=final_text, reply_markup=final_buttons)

        ggr_wipe_user_data(user_id)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"Temizlik hatası ({user_id}): {e}")

def ggr_schedule_inactivity_cleanup(client, user_id, first_name, timeout_seconds=1800):
    """30 dakika boyunca işlem yapılmazsa sohbeti temizler ve güvenli menüyü gösterir."""
    ggr_cancel_user_timer(user_id)
    ggr_user_timers[user_id] = asyncio.create_task(
        ggr_otomatik_sohbet_temizleyici(client, user_id, first_name, delay=timeout_seconds, is_success=False)
    )

async def ggr_safe_edit(msg, text, reply_markup=None, disable_web_page_preview=False):
    """MessageIdInvalid ve diğer edit hatalarına karşı güvenli mesaj güncelleme/gönderme fonksiyonu."""
    try:
        return await msg.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)
    except Exception:
        try:
            return await msg.reply_text(text, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)
        except Exception:
            return msg

# =====================================================================
# /START & ANA MENÜ
# =====================================================================
@ggr_app.on_message(filters.command(["start", "help", "yardim"]) & filters.private)
async def ggr_start_handler(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Kullanıcı"
    ggr_wipe_user_data(user_id)
    u_data = ggr_get_user_data(user_id)
    u_data["first_name"] = first_name
    u_data["start_msg_id"] = message.id

    # Kullanıcıya ilk girişte veya /start anında dil sorulur
    metin, butonlar = ggr_get_lang_selection(first_name)
    await message.reply_text(metin, reply_markup=butonlar, disable_web_page_preview=True)
    ggr_schedule_inactivity_cleanup(client, user_id, first_name, timeout_seconds=1800)

# =====================================================================
# /KALDIR (BOTU SİLME)
# =====================================================================
@ggr_app.on_message(filters.command(["kaldir", "sil"]) & filters.private)
async def ggr_kaldir_cmd(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Kullanıcı"
    ggr_wipe_user_data(user_id)
    u_data = ggr_get_user_data(user_id)
    u_data["step"] = "KALDIR_API_KEY"
    u_data["first_name"] = first_name

    await message.reply_text(
        "🗑️ <b>GagaraGogo Userbot'u Kaldırma</b>\n\n"
        "Botunuzu Render sunucularından tamamen silmek için lütfen **Render API Anahtarınızı** (`rnd_...`) gönderin:\n\n"
        "👉 <i>İptal etmek için /cancel yazabilirsiniz.</i>"
    )
    ggr_schedule_inactivity_cleanup(client, user_id, first_name, timeout_seconds=1800)

# =====================================================================
# /CANCEL (İPTAL ETME)
# =====================================================================
@ggr_app.on_message(filters.command("cancel") & filters.private)
async def ggr_cancel_handler(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Kullanıcı"
    ggr_wipe_user_data(user_id)

    await message.reply_text(
        "❌ <b>İşlem iptal edildi.</b>\n\n"
        "Tüm geçici veriler hafızadan silindi.\n"
        "⏳ <i>Güvenliğiniz için bu sohbet 30 dakika içinde otomatik olarak temizlenecektir.</i>",
        reply_markup=ReplyKeyboardRemove()
    )
    ggr_schedule_inactivity_cleanup(client, user_id, first_name, timeout_seconds=1800)

# =====================================================================
# CALLBACK QUERY YÖNETİCİSİ
# =====================================================================
@ggr_app.on_callback_query()
async def ggr_callback_handler(client, query):
    user_id = query.from_user.id
    first_name = query.from_user.first_name or "Kullanıcı"
    data = query.data
    ggr_schedule_inactivity_cleanup(client, user_id, first_name, timeout_seconds=1800)

    if data == "ggr_set_lang_tr":
        u_data = ggr_get_user_data(user_id)
        u_data["lang"] = "tr"
        metin, butonlar = ggr_get_start_content(first_name, lang="tr")
        await query.message.edit_text(metin, reply_markup=butonlar, disable_web_page_preview=True)
        await query.answer()

    elif data == "ggr_set_lang_en":
        u_data = ggr_get_user_data(user_id)
        u_data["lang"] = "en"
        metin, butonlar = ggr_get_start_content(first_name, lang="en")
        await query.message.edit_text(metin, reply_markup=butonlar, disable_web_page_preview=True)
        await query.answer()

    elif data == "ggr_lang_change":
        metin, butonlar = ggr_get_lang_selection(first_name)
        await query.message.edit_text(metin, reply_markup=butonlar, disable_web_page_preview=True)
        await query.answer()

    elif data in ("ggr_kur_basla", "kur_basla"):
        ggr_wipe_user_data(user_id)
        u_data = ggr_get_user_data(user_id)
        u_data["step"] = "WAIT_RENDER_KEY"
        u_data["first_name"] = first_name

        await query.answer()

        # 1. Resim: Render Adım 1
        try:
            await client.send_photo(
                chat_id=user_id,
                photo=ggr_get_asset_photo("RENDERADIM1.png"),
                caption="📸 <b>Render - 1. Adım:</b>\nSağ üstteki profil simgenize (daire içindeki alana) tıklayın, ardından açılan menüden okla gösterilen <b>Account settings</b> kısmına basın."
            )
        except Exception as e:
            logging.warning(f"Render Adım 1 görsel gönderme hatası: {e}")

        # 2. Resim: Render Adım 2
        try:
            await client.send_photo(
                chat_id=user_id,
                photo=ggr_get_asset_photo("RENDERADIM2.png"),
                caption=(
                    "📸 <b>Render - 2. Adım:</b>\n"
                    "Sol menüden <b>API Keys</b> sekmesine gelin ve <b>Create API Key</b> butonuna basın. "
                    "Açılan kutuda bir isim verip onaylayın. Size verilen <code>rnd_...</code> ile başlayan API anahtarınızı kopyalayın."
                )
            )
        except Exception as e:
            logging.warning(f"Render Adım 2 görsel gönderme hatası: {e}")

        await client.send_message(
            chat_id=user_id,
            text=(
                "🌐 <b>Adım 1: Render API Anahtarı</b>\n\n"
                "Botunuzun 7/24 ücretsiz çalışacağı sunucuyu bağlamak için Render API anahtarınız gereklidir:\n\n"
                "1️⃣ <a href='https://dashboard.render.com/'>dashboard.render.com</a> adresine gidip hesabınıza giriş yapın.\n"
                "2️⃣ Yukarıdaki resimli adımlarda gösterildiği gibi <code>rnd_...</code> anahtarınızı oluşturun.\n"
                "3️⃣ Oluşturulan <code>rnd_...</code> anahtarını kopyalayıp buraya gönderin:\n\n"
                "❌ <i>İptal etmek için /cancel yazabilirsiniz.</i>"
            ),
            disable_web_page_preview=True
        )

    elif data in ("ggr_kaldir_basla", "kaldir_basla"):
        ggr_wipe_user_data(user_id)
        u_data = ggr_get_user_data(user_id)
        u_data["step"] = "KALDIR_API_KEY"
        u_data["first_name"] = first_name
        await query.message.reply_text(
            "🗑️ <b>GagaraGogo Userbot'u Kaldırma</b>\n\n"
            "Lütfen Render hesabınızdaki servisi silmek için **Render API Anahtarınızı** (`rnd_...`) mesaj olarak gönderin:"
        )
        await query.answer()

    elif data in ("ggr_bilgi", "bilgi"):
        bilgi_metin = (
            "🛡️ <b>GagaraGogo Güvenlik & Gizlilik İlkeleri</b>\n\n"
            "• <b>%100 Açık Kaynak:</b>\n"
            "Tüm kurulum ve deploy kaynak kodları GitHub üzerinde açıktır:\n"
            "👉 <a href='https://github.com/chaolcam/gagaragogo-kurulum-bot'>github.com/chaolcam/gagaragogo-kurulum-bot</a>\n\n"
            "• <b>Sıfır Depolama (Zero-Persistence):</b>\n"
            "Girdiğiniz API anahtarları, telefon numarası veya onay kodları sunucuda <b>asla</b> veritabanına veya diske kaydedilmez. Sadece o anlık RAM hafızada işlenir ve bittiğinde yok edilir.\n\n"
            "• <b>Otomatik Sohbet Temizleme:</b>\n"
            "1️⃣ Başarılı kurulumlarda: <b>5 dakika sonra</b>\n"
            "2️⃣ Yarım kalan veya iptal edilen işlemlerde: <b>30 dakika sonra</b>\n"
            "sohbetteki tüm hassas mesajlar güvenliğiniz için otomatik olarak tamamen silinir.\n\n"
            "• <b>⚠️ Sorumluluk Reddi Beyanı (Disclaimer):</b>\n"
            "Userbot kullanımı üçüncü parti bir yazılımdır ve Telegram hesabınız sınırlandırılabilir veya yasaklanabilir. Bu açık kaynaklı bir projedir; hesabınızdan ve paylaşımlarınızdan <b>bizzat kendiniz sorumlusunuz</b>. GagaraGogo geliştiricileri ve yöneticileri hiçbir sorumluluk kabul etmemektedir."
        )
        await query.message.reply_text(
            bilgi_metin,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 GitHub Kaynak Kodları", url="https://github.com/chaolcam/gagaragogo-kurulum-bot")],
                [InlineKeyboardButton("⬅️ Ana Menüye Dön", callback_data="ggr_ana_menu")]
            ])
        )
        await query.answer()

    elif data == "ggr_ana_menu":
        u_data = ggr_get_user_data(user_id)
        lang = u_data.get("lang", "tr")
        metin, butonlar = ggr_get_start_content(first_name, lang)
        await query.message.edit_text(metin, reply_markup=butonlar, disable_web_page_preview=True)
        await query.answer()

    elif data == "ggr_auto_botfather":
        u_data = ggr_get_user_data(user_id)
        await query.message.edit_text("⏳ <i>@BotFather ile konuşuluyor, yardımcı botunuz ve inline menü açılıyor...</i>")
        try:
            bf_result = await ggr_create_bot_via_botfather(
                api_id=u_data["api_id"],
                api_hash=u_data["api_hash"],
                session_str=u_data["string_session"]
            )
            u_data["bot_token"] = bf_result["token"]
            u_data["bot_username"] = bf_result["username"]

            # Artık tüm bilgiler hazır, hemen Render Deploy'u başlat!
            await ggr_deploy_to_render_and_finish(query.message, u_data, user_id)

        except Exception as e:
            await query.message.reply_text(
                f"⚠️ Otomatik bot açılırken bir sorun oluştu: `{str(e)}`\n\n"
                f"Lütfen @BotFather'dan aldığınız bir Bot Token'ı elle mesaj olarak gönderin:"
            )
            u_data["step"] = "WAIT_MANUAL_BOT_TOKEN"

    elif data in ("ggr_manual_botfather", "manual_botfather"):
        u_data = ggr_get_user_data(user_id)
        u_data["step"] = "WAIT_MANUAL_BOT_TOKEN"
        await query.message.reply_text(
            "✏️ Lütfen @BotFather'dan aldığınız bot tokenınızı yapıştırın:\n"
            "Örnek: `1234567890:ABCdef...`"
        )
        await query.answer()

    elif data == "ggr_use_official_api":
        u_data = ggr_get_user_data(user_id)
        u_data["api_id"] = 2040
        u_data["api_hash"] = "b18441a1ff607e10a989891a5462e627"

        await query.message.edit_text(
            "✅ <b>Telegram Resmi Android API Seçildi!</b>\n"
            "• API ID: <code>2040</code>\n"
            "• API HASH: <code>b18441a1ff607e10a989891a5462e627</code>\n\n"
            "⏳ <i>Giriş onay kodunuz (SMS/Telegram) gönderiliyor...</i>"
        )
        await ggr_start_pyrogram_login(query.message, u_data, user_id)

    elif data == "ggr_retry_login":
        u_data = ggr_get_user_data(user_id)
        await query.message.edit_text("⏳ <i>Giriş kodu tekrar isteniyor...</i>")
        await ggr_start_pyrogram_login(query.message, u_data, user_id)

# =====================================================================
# METİN MESAJLARI AKIŞI
# =====================================================================
@ggr_app.on_message(filters.private & ~filters.command(["start", "cancel", "kaldir", "sil"]))
async def ggr_message_flow(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Kullanıcı"
    u_data = ggr_get_user_data(user_id)
    u_data["first_name"] = first_name
    ggr_schedule_inactivity_cleanup(client, user_id, first_name, timeout_seconds=1800)

    step = u_data.get("step")
    if not step:
        await message.reply_text("Lütfen kuruluma başlamak için /start komutunu kullanın.")
        return

    # --- 1. ADIM: RENDER API KEY ALMA VE DOĞRULAMA ---
    if step == "WAIT_RENDER_KEY":
        render_key = message.text.strip()
        if not render_key.startswith("rnd_"):
            await message.reply_text("⚠️ Render API anahtarları `rnd_` ile başlar. Lütfen doğru anahtarı girdiğinizden emin olun:")
            return

        msg_wait = await message.reply_text("⏳ <i>Render API anahtarı doğrulanıyor...</i>")
        try:
            deployer = GgrRenderDeployer(render_key)
            owner_id = await deployer.get_owner_id()
            u_data["render_key"] = render_key
            u_data["owner_id"] = owner_id
            u_data["deployer"] = deployer

            u_data["step"] = "WAIT_PHONE"
            kb = ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Telefon Numaramı Paylaş", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await msg_wait.delete()
            await message.reply_text(
                "✅ <b>Render API Anahtarı Doğrulandı!</b>\n\n"
                "📱 <b>Adım 2: Telegram Telefon Numarası</b>\n\n"
                "Aşağıdaki butona basarak telefon numaranızı paylaşın veya uluslararası formatta yazın:\n"
                "Örnek: `+905551234567`\n\n"
                "🔒 <i>Numaranız sadece anlık Telegram doğrulama kodu istemek için kullanılır, ASLA kaydedilmez.</i>",
                reply_markup=kb
            )
        except Exception as e:
            await msg_wait.edit_text(f"❌ <b>Hata:</b> {str(e)}\n\nLütfen Render API anahtarınızı kontrol edip tekrar gönderin:")

    # --- 2. ADIM: TELEFON NUMARASI ALMA ---
    elif step == "WAIT_PHONE":
        if message.contact:
            phone_number = message.contact.phone_number
        else:
            phone_number = message.text.strip()

        clean_phone = re.sub(r"[^\d+]", "", phone_number)
        if not clean_phone.startswith("+"):
            clean_phone = "+" + clean_phone

        if len(clean_phone) < 10:
            await message.reply_text("❌ Geçersiz telefon numarası. Lütfen örn: `+905551234567` şeklinde yazın:")
            return

        u_data["phone"] = clean_phone
        msg_wait = await message.reply_text(
            f"⏳ <b>my.telegram.org</b> ile iletişim kuruluyor...\n"
            f"Numara: <code>{clean_phone}</code>",
            reply_markup=ReplyKeyboardRemove()
        )

        try:
            my_tg = GgrMyTelegramClient()
            u_data["my_tg"] = my_tg
            login_web_result = await my_tg.send_code(clean_phone)

            if login_web_result.get("status") == "success":
                u_data["step"] = "WAIT_MYTG_CODE"
                await msg_wait.edit_text(
                    "📨 <b>Telegram Doğrulama Kodu Gönderildi!</b>\n\n"
                    "Telegram resmi bildirimlerinden gelen web giriş kodunu buraya gönderin.\n\n"
                    "⚠️ <b>ÖNEMLİ FORMAT UYARISI:</b>\n"
                    "Telegram gelen kodların otomatik doğrulanmasını engellediği için lütfen kodu <b>aralarında boşluk bırakarak</b> yazın:\n"
                    "👉 <i>Örnek: Kod <code>93964</code> ise buraya <code>9 3 9 6 4</code> veya <code>9.3.9.6.4</code> şeklinde yazın.</i>\n\n"
                    "❌ <i>İptal etmek için /cancel yazabilirsiniz.</i>"
                )
                return

        except Exception as mytg_err:
            logging.warning(f"my.telegram.org başarısız: {mytg_err}")

        # Eğer my.telegram.org sitesi açılmazsa kullanıcıya resmi Telegram anahtar seçeneği sun
        await msg_wait.edit_text(
            "⚠️ <b>my.telegram.org Sitesine Ulaşılamadı</b>\n\n"
            "Telegram sunucularındaki yoğunluk nedeniyle web sitesi yanıt vermedi.\n"
            "Ancak endişelenmeyin! Telegram'ın resmi Android uygulamasının hazır ve lisanslı genel API anahtarlarını kullanarak devam edebilirsiniz:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Resmi Android API ile Devam Et", callback_data="ggr_use_official_api")],
                [InlineKeyboardButton("❌ İptal Et", callback_data="ggr_cancel")]
            ])
        )

    # --- 3. ADIM: my.telegram.org KODU ---
    elif step == "WAIT_MYTG_CODE":
        raw_code = message.text.strip()
        code = re.sub(r"[\s\.\-_,]", "", raw_code)

        msg_wait = await message.reply_text("⏳ <i>my.telegram.org girişi yapılıyor ve API anahtarları alınıyor...</i>")
        my_tg = u_data.get("my_tg")
        try:
            login_res = await my_tg.login(code)
            if login_res.get("status") != "success":
                raise Exception(login_res.get("message", "Giriş başarısız."))

            app_res = await my_tg.get_or_create_app()
            if app_res.get("status") == "success":
                u_data["api_id"] = app_res["api_id"]
                u_data["api_hash"] = app_res["api_hash"]

                await msg_wait.edit_text(
                    f"✅ <b>API Bilgileriniz Başarıyla Alındı!</b>\n\n"
                    f"• <b>API ID:</b> <code>{app_res['api_id']}</code>\n"
                    f"• <b>API HASH:</b> <code>{app_res['api_hash']}</code>\n\n"
                    f"⏳ <i>Şimdi String Session üretmek için Telegram uygulamanıza giriş kodu gönderiliyor...</i>"
                )
                await ggr_start_pyrogram_login(message, u_data, user_id)
            else:
                raise Exception("API ID ve HASH otomatik oluşturulamadı.")
        except Exception as e:
            await msg_wait.edit_text(
                f"❌ <b>Hata:</b> {str(e)}\n\n"
                f"Lütfen kodu doğru girdiğinizden emin olun (Örn: <code>9 3 9 6 4</code>) veya /start ile baştan deneyin."
            )

    # --- 4. ADIM: PYROGRAM TELEGRAM GİRİŞ KODU ---
    elif step == "WAIT_TG_LOGIN_CODE":
        raw_code = message.text.strip()
        code = re.sub(r"[\s\.\-_,]", "", raw_code)

        msg_wait = await message.reply_text("⏳ <i>Oturum açılıyor ve String Session üretiliyor...</i>")
        sess_gen = u_data.get("sess_gen")

        try:
            res = await sess_gen.sign_in(code)
            if res.get("status") == "success":
                u_data["string_session"] = res["session_string"]
                await ggr_ask_botfather_step(msg_wait, u_data, user_id)

            elif res.get("status") == "2fa_required":
                u_data["step"] = "WAIT_2FA_PASSWORD"
                await msg_wait.edit_text(
                    "🔐 <b>İki Adımlı Doğrulama (2FA) Şifresi Gerekli</b>\n\n"
                    "Hesabınızda 2FA şifresi aktif. Lütfen Telegram bulut şifrenizi mesaj olarak gönderin:\n\n"
                    "🔒 <i>Şifreniz hiçbir yere kaydedilmez, anlık doğrulamadan sonra hafızadan tamamen silinir.</i>"
                )
            else:
                raise Exception(res.get("message", "Giriş başarısız."))
        except Exception as e:
            await msg_wait.edit_text(f"❌ <b>Giriş Hatası:</b> {str(e)}\n\nLütfen kodu doğru girdiğinizden emin olun veya /start ile tekrar deneyin.")

    # --- 5. ADIM: 2FA ŞİFRESİ ---
    elif step == "WAIT_2FA_PASSWORD":
        password = message.text.strip()
        msg_wait = await message.reply_text("⏳ <i>2FA şifresi doğrulanıyor...</i>")
        sess_gen = u_data.get("sess_gen")

        try:
            res = await sess_gen.check_password(password)
            if res.get("status") == "success":
                u_data["string_session"] = res["session_string"]
                await ggr_ask_botfather_step(msg_wait, u_data, user_id)
            else:
                raise Exception(res.get("message", "2FA Şifresi hatalı."))
        except Exception as e:
            await msg_wait.edit_text(f"❌ <b>Hata:</b> {str(e)}\n\nLütfen şifrenizi tekrar deneyin veya /cancel yazın.")

    # --- 6. ADIM: MANUEL BOT TOKEN ---
    elif step == "WAIT_MANUAL_BOT_TOKEN":
        token = message.text.strip()
        if ":" not in token:
            await message.reply_text("❌ Geçersiz bot token formatı! Örn: `1234567890:ABCdef...`")
            return
        u_data["bot_token"] = token
        await ggr_deploy_to_render_and_finish(message, u_data, user_id)

    # --- BOT KALDIRMA ADIMI ---
    elif step == "KALDIR_API_KEY":
        render_key = message.text.strip()
        msg_wait = await message.reply_text("⏳ <i>Render hesabınızdaki 'gagaragogo-userbot' servisi aranıyor ve siliniyor...</i>")

        try:
            deployer = GgrRenderDeployer(render_key)
            silindi = await deployer.delete_userbot_service()

            if silindi:
                await msg_wait.edit_text(
                    "✅ <b>GagaraGogo Userbot Render servisiniz başarıyla silindi!</b>\n\n"
                    "Tüm sunucu işlemleri ve kaynaklar hesabınızdan tamamen kaldırılmıştır."
                )
            else:
                await msg_wait.edit_text("ℹ️ Render hesabınızda aktif bir 'gagaragogo-userbot' servisi bulunamadı.")
            ggr_wipe_user_data(user_id)
        except Exception as e:
            await msg_wait.edit_text(f"❌ Kaldırma Hatası: {str(e)}")
            ggr_wipe_user_data(user_id)

# =====================================================================
# PYROGRAM GİRİŞ VE BOTFATHER ADIMLARI
# =====================================================================
async def ggr_start_pyrogram_login(msg_target, u_data, user_id):
    """Pyrogram istemcisi ile kullanıcının hesabına giriş kodu gönderir."""
    try:
        sess_gen = GgrSessionGenerator(
            api_id=u_data["api_id"],
            api_hash=u_data["api_hash"],
            phone_number=u_data["phone"]
        )
        u_data["sess_gen"] = sess_gen
        res = await sess_gen.send_code()

        if res.get("status") == "success":
            u_data["step"] = "WAIT_TG_LOGIN_CODE"
            metin = (
                "📱 <b>Telegram Giriş Kodunuz Gönderildi!</b>\n\n"
                "Lütfen Telegram uygulamanıza gelen giriş kodunu buraya gönderin.\n\n"
                "⚠️ <b>ÖNEMLİ:</b> Kodu <b>aralarında boşluk bırakarak</b> yazın:\n"
                "👉 <i>Örnek: <code>1 2 3 4 5</code></i>"
            )
            await ggr_safe_edit(msg_target, metin)
        else:
            raise Exception(res.get("message", "Kod gönderilemedi."))
    except Exception as e:
        await ggr_safe_edit(
            msg_target,
            f"❌ Kod gönderilirken hata oluştu: `{str(e)}`\n\nLütfen tekrar deneyin:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar Dene", callback_data="ggr_retry_login")],
                [InlineKeyboardButton("❌ İptal", callback_data="ggr_cancel")]
            ])
        )

async def ggr_ask_botfather_step(msg_target, u_data, user_id):
    """Yardımcı botun otomatik açılmasını veya manuel girilmesini sorar."""
    u_data["step"] = "CHOOSE_BOTFATHER_MODE"
    metin = (
        "🔐 <b>String Session Başarıyla Üretildi!</b>\n\n"
        "🤖 <b>Son Adım: Yardımcı Bot Kurulumu</b>\n\n"
        "GagaraGogo Userbot'un inline buton menüleri ve ayar paneli için bir yardımcı bota ihtiyacı vardır.\n\n"
        "Ne yapmak istersiniz?\n"
        "• <b>Otomatik Oluştur:</b> Botunuz @BotFather ile konuşup saniyeler içinde yeni bot açar ve inline modunu ayarlar.\n"
        "• <b>Manuel Giriş:</b> Daha önceden aldığınız bir Bot Token'ı kendiniz yapıştırabilirsiniz."
    )
    butonlar = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Otomatik Bot Aç (Önerilen)", callback_data="ggr_auto_botfather")],
        [InlineKeyboardButton("✏️ Bot Token'ı Kendim Gireceğim", callback_data="ggr_manual_botfather")]
    ])
    await ggr_safe_edit(msg_target, metin, reply_markup=butonlar)

# =====================================================================
# RENDER DEPLOY VE REHBER SUNUMU
# =====================================================================
async def ggr_deploy_to_render_and_finish(msg_target, u_data, user_id):
    """Render servisini kurar, UptimeRobot rehberini sunar ve 5 dk otomatik temizleyiciyi başlatır."""
    msg_wait = await msg_target.reply_text(
        "🚀 <b>GagaraGogo Kurulumu Başlatılıyor...</b>\n\n"
        "Render hesabınızda <code>gagaragogo-userbot</code> servisi oluşturuluyor ve değişkenler yükleniyor..."
    )

    try:
        deployer = u_data.get("deployer") or GgrRenderDeployer(u_data["render_key"])
        env_vars = {
            "API_ID": u_data["api_id"],
            "API_HASH": u_data["api_hash"],
            "STRING_SESSION": u_data["string_session"],
            "BOT_TOKEN": u_data["bot_token"],
            "OWNER_ID": user_id
        }

        deploy_result = await deployer.deploy_service(env_vars)
        service_id = deploy_result.get("id")
        app_live_url = deploy_result.get("service_url")
        dashboard_url = deploy_result.get("dashboard_url") or f"https://dashboard.render.com/web/{service_id}"

        basari_metni = (
            f"🎉 <b>TEBRİKLER! GAGARAGOGO USERBOT KURULDU!</b>\n\n"
            f"🚀 <b>Render Web Servisiniz Başlatıldı:</b>\n"
            f"• <b>Servis Adı:</b> <code>{deploy_result['name']}</code>\n"
            f"• <b>Size Özel Canlı Web Adresi:</b> <code>{app_live_url}</code>\n"
            f"• <b>Panel Linki:</b> <a href='{dashboard_url}'>Render Dashboard</a>\n\n"
            f"🔑 <b>Hesap Anahtarlarınız:</b>\n"
            f"• API ID: <code>{u_data['api_id']}</code>\n"
            f"• API HASH: <code>{u_data['api_hash']}</code>\n"
            f"• YARDIMCI BOT: <code>{u_data.get('bot_username', 'Aktif')}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <b>BOTUN 7/24 SÜRESİZ VE KESİNTİSİZ ÇALIŞMASI İÇİN:</b>\n\n"
            f"Render ücretsiz planları 15 dakika istek almadığında uyku moduna geçer. Botunuzun <b>hiç uyumaması ve 7/24 kesintisiz çalışması için</b> aşağıdaki 2 resimli UptimeRobot adımını tamamlayın:\n\n"
            f"🔗 <b>Size Özel Canlı Web Adresiniz:</b>\n👉 <code>{app_live_url}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <b>Gizlilik & Güvenlik Koruması:</b>\n"
            f"<i>Güvenliğiniz için bu sohbetteki tüm kurulum mesajları ve anahtarlar <b>5 dakika sonra otomatik olarak silinecektir</b>. Kurulum bilgileriniz Kayıtlı Mesajlar (Saved Messages) kutunuza güvenle yedeklenmiştir!</i>\n\n"
            f"📂 <b>Açık Kaynak Kodları:</b> <a href='https://github.com/chaolcam/gagaragogo-kurulum-bot'>GitHub Depomuz</a>\n\n"
            f"Telegram'da herhangi bir sohbete <code>.alive</code> yazarak botunuzu test edebilirsiniz!"
        )

        await msg_wait.edit_text(basari_metni, disable_web_page_preview=True)

        # 1. Resim: UptimeRobot Adım 1
        try:
            await ggr_app.send_photo(
                chat_id=user_id,
                photo=ggr_get_asset_photo("UPTIMEADIM1.png"),
                caption=(
                    "📸 <b>UptimeRobot - 1. Adım:</b>\n"
                    "<a href='https://uptimerobot.com/'>uptimerobot.com</a> adresine gidin. "
                    "Daire içindeki <b>+ New</b> butonunun yanındaki oka basarak açılan menüden <b>Single monitor</b> seçeneğine tıklayın."
                )
            )
        except Exception as e:
            logging.warning(f"UptimeRobot Adım 1 görsel gönderme hatası: {e}")

        # 2. Resim: UptimeRobot Adım 2
        try:
            await ggr_app.send_photo(
                chat_id=user_id,
                photo=ggr_get_asset_photo("UPTIMEADIM2.png"),
                caption=(
                    f"📸 <b>UptimeRobot - 2. Adım:</b>\n"
                    f"URL kutusuna botun size verdiği canlı linkin tamamını yapıştırın:\n"
                    f"👉 <code>{app_live_url}</code>\n\n"
                    f"Ardından en alttaki <b>Create monitor</b> butonuna basın. Başka hiçbir şey yapmanıza gerek yoktur, botunuz 7/24 aktif kalacaktır!"
                )
            )
        except Exception as e:
            logging.warning(f"UptimeRobot Adım 2 görsel gönderme hatası: {e}")

        # Kullanıcının Telegram Kayıtlı Mesajlar sohbetine güvenli yedek gönder
        try:
            temp_client = Client(
                "ggr_temp_export",
                api_id=u_data["api_id"],
                api_hash=u_data["api_hash"],
                session_string=u_data["string_session"],
                in_memory=True
            )
            await temp_client.connect()
            await temp_client.send_message("me", f"🔐 <b>GagaraGogo Userbot Yedek ve Uptime Bilgileriniz:</b>\n\n{basari_metni}", disable_web_page_preview=True)
            try:
                await temp_client.join_chat("gagaragogouserbot")
            except Exception:
                pass
            await temp_client.disconnect()
        except Exception:
            pass

        # Başarılı olduğunda 30 dakikalık boşta kalma sayacını iptal et
        ggr_cancel_user_timer(user_id)
        first_name = u_data.get("first_name", "Kullanıcı")

        # 5 dakika sonra önce bildirim atıp önceki tüm mesajları silen temizlik görevini başlat
        asyncio.create_task(
            ggr_otomatik_sohbet_temizleyici(ggr_app, user_id, first_name, delay=300, is_success=True)
        )

    except Exception as e:
        await msg_wait.edit_text(f"❌ Render Deploy Hatası:\n`{str(e)}`")
    finally:
        ggr_wipe_user_data(user_id)

# Uyumluluk aliasları
app = ggr_app
get_user_data = ggr_get_user_data
wipe_user_data = ggr_wipe_user_data
