# AvtoUsta — Avto-ustalar bilan bog'lanish ilovasi

Ushbu loyiha ikkita qismdan iborat:

1. **`app.py`** — mijozlar uchun veb-ilova (Flask). Bosh menyuda usta yo'nalishlari, ariza qoldirish formasi, usta shaxsiy kabineti.
2. **`bot.py`** — sizning (administrator) va ustalar uchun Telegram bot orqali boshqaruv paneli.

Ikkalasi ham bitta `autoapp.db` (SQLite) bazasidan foydalanadi, shuning uchun ular bir xil papkada, bitta serverda ishga tushirilishi kerak.

## 1-qadam: kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

## 2-qadam: sozlash (`config.py`)

`config.py` faylini oching va quyidagilarni to'ldiring:

- **BOT_TOKEN** — Telegram'da [@BotFather](https://t.me/BotFather) orqali yangi bot yaratib, undan olingan token.
- **ADMIN_CHAT_ID** — sizning shaxsiy Telegram chat ID raqamingiz. Buni bilish uchun [@userinfobot](https://t.me/userinfobot) ga `/start` yozing, u sizga ID raqamingizni yuboradi.
- **ADMIN_TELEGRAM_USERNAME** — sizning Telegram foydalanuvchi nomingiz (@ belgisisiz). "Administrator" tugmasi bosilganda mijoz shu profilingizga o'tadi.
- **SECRET_KEY** — istalgan uzun tasodifiy matn (sessiya xavfsizligi uchun).

Muqobil variant — muhit o'zgaruvchilari orqali:

```bash
export BOT_TOKEN="123456:ABC-your-token"
export ADMIN_CHAT_ID="123456789"
export ADMIN_TELEGRAM_USERNAME="your_username"
```

## 3-qadam: ishga tushirish

Ikkita alohida terminalda:

```bash
# 1-terminal — veb-ilova
python app.py

# 2-terminal — telegram bot
python bot.py
```

Veb-ilova `http://localhost:5000` manzilida ochiladi. Uni internetga chiqarish uchun (masalan, telefon orqali kirish uchun) VPS/serverga joylashtiring yoki `ngrok` kabi vosita ishlating.

## Qanday ishlaydi

### Mijoz tomoni (veb-ilova)
- Bosh sahifada barcha usta yo'nalishlari tugma-karta shaklida chiqadi.
- Birortasini bosgach, ism, familiya, telefon va qo'shimcha ma'lumot so'raladigan forma ochiladi.
- Yuqori o'ng burchakda **☰** tugmasi bor — u orqali **Administrator** (sizning Telegram profilingiz), **Shaxsiy akkaunt** (usta uchun) va **Ilova haqida** bo'limlariga o'tiladi.
- Ariza yuborilgach, shu yo'nalishdagi barcha faol (va Telegramga bog'langan) ustalarga hamda administratorga avtomatik xabar boradi.

### Administrator (Telegram bot orqali)
Botga `/start` yozing (faqat `ADMIN_CHAT_ID` dagi akkaunt admin sifatida tanilinadi):

- **📂 Bo'limlar** — yo'nalishlarni qo'shish, tahrirlash, o'chirish.
- **👨‍🔧 Ustalar** — yangi usta qo'shish (yo'nalishni tugma orqali tanlaysiz, so'ng ism-familiyani yozasiz — bot avtomatik login va parol yaratadi), ustalar ro'yxatini ko'rish.
- **📊 Statistika** — ilovaga necha kishi kirgani, jami buyurtmalar soni, qabul qilinganlar soni, faol ustalar soni.

### Usta tomoni
Usta qo'shilgach, admin unga login va parolni beradi. Usta buni ikki xil usulda ishlata oladi:

1. **Telegram orqali:** botga `/login login parol` deb yozadi — shundan so'ng yangi klientlar haqida xabarlar to'g'ridan-to'g'ri Telegramga keladi, "✅ Qabul qilish" / "❌ Bekor qilish" tugmalari bilan.
2. **Veb-ilova orqali:** saytdagi ☰ menyu → "Shaxsiy akkaunt" bo'limiga login/parol bilan kiradi, shu yerda ham yangi klientlarni ko'rib, qabul qilishi mumkin.

Bir klientni bir usta qabul qilsa, xuddi shu yo'nalishdagi boshqa ustalarning xabari avtomatik "band qilindi" holatiga o'zgaradi (Telegramda ham, tizimda ham).

## Fayllar tuzilishi

```
autoapp/
├── app.py              # Mijozlar uchun veb-ilova
├── bot.py               # Administrator/usta uchun Telegram bot
├── database.py           # SQLite baza sxemasi va yordamchi funksiyalar
├── telegram_utils.py     # Telegram Bot API bilan ishlash
├── config.py             # Sozlamalar (token, admin ID va h.k.)
├── requirements.txt
├── templates/            # HTML sahifalar
└── static/style.css      # Uslub
```

## Eslatma

- Bu MVP (birinchi versiya) — production uchun HTTPS, kuchliroq parol xesh (hozircha oddiy matn holida saqlanadi), va PostgreSQL kabi bazaga o'tishni tavsiya qilamiz.
- Bot ishlab turishi kerak (`python bot.py` doim faol bo'lishi kerak) — aks holda ustalarga xabar bormaydi. Buni `systemd`, `pm2`, yoki `screen`/`tmux` yordamida doimiy ishlaydigan qilib qo'yish mumkin.
