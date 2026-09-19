# 🚀 GagaraGogo Userbot - Otomatik Kurulum ve Deploy Botu v1.0

> **GagaraGogo Userbot**'u hiçbir teknik bilgi, konsol veya terminal kurulumu gerektirmeden Render ve Telegram altyapısına bağlayan resmi kurulum asistanı.

[![Telegram Bot](https://img.shields.io/badge/Telegram-Kurulum%20Botu-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/GagaragogoKurulumBot)

👉 **Botu Başlatmak İçin Tıklayın:** [@GagaragogoKurulumBot](https://t.me/GagaragogoKurulumBot)

---

## ⚠️ Sorumluluk Reddi Beyanı (Disclaimer)

> **Önemli Bilgilendirme:**
> - Userbot kullanımı Telegram Hizmet Şartları kapsamında hesabınızın sınırlandırılmasına veya yasaklanmasına neden olabilir.
> - Bu bir açık kaynaklı kurulum asistanıdır; yaptığınız her işlemden, paylaştığınız içeriklerden ve hesabınızdan **bizzat kendiniz sorumlusunuz**.
> - Kesinlikle **GagaraGogo geliştiricileri ve yöneticileri hiçbir sorumluluk kabul etmemektedir**.
> - GagaraGogo Userbot'u kurarak, kullanarak veya kurulum botunu çalıştırarak bu kullanım şartlarını ve sorumlulukları peşinen kabul etmiş sayılırsınız.

---

## ✨ Özellikler (v1.0)

- ⚡ **Tek Tıkla Render Entegrasyonu:** Render REST API üzerinden web servisini otomatik oluşturur, ortam değişkenlerini (`API_ID`, `API_HASH`, `STRING_SESSION`, `BOT_TOKEN`) hatasız tanımlar ve derlemeyi tetikler.
- 🌐 **7/24 Kesintisiz Çalışma Desteği:** Kurulum sonunda canlı web adresi (`https://gagaragogo-userbot-xxx.onrender.com`) ve UptimeRobot 3 adımlı rehberi sunulur.
- 🔐 **Otomatik String Session:** Telefon numarası ve Telegram doğrulama koduyla anlık RAM oturumu oluşturur.
- 🤖 **BotFather Otomasyonu:** Hesabınız üzerinden `@BotFather` ile konuşarak otomatik yardımcı bot oluşturur, tokenini alır ve `/setinline` modunu açar.
- 🛡️ **Sıfır Depolama (Zero-Persistence Gizlilik):** Girilen telefon numarası, SMS kodları, oturum dizgileri veya API anahtarları hiçbir veritabanına veya sunucu diskine **asla kaydedilmez**. İşlem tamamlandığında veya iptal edildiğinde tüm geçici RAM verileri kalıcı olarak imha edilir.
- 🧹 **Gelişmiş Otomatik Sohbet Temizliği:**
  - **Başarılı Kurulum:** Kurulum tamamlandığında 5 dakika sonra kullanıcıya bildirim gönderilir ve önceki tüm kurulum mesajları (SMS kodları, API anahtarları, sohbet kalıntıları) kalıcı olarak silinir.
  - **Yarım Kalan / İptal Edilen İşlemler:** Kullanıcı işlem yapmayı bıraktığında veya hata aldığında 30 dakika sonra tüm önceki mesajlar otomatik silinir.
  - Temizlik sonrasında bot kaldırma ve yeniden başlatma butonları güvenli bir şekilde sunulur.

---

## 📄 Lisans

Bu proje **MIT Lisansı** ile lisanslanmıştır.
