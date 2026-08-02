import os

# Telegram bot tokeningizni @BotFather orqali oling va shu yerga qo'ying
BOT_TOKEN = os.environ.get("BOT_TOKEN", "TOKEN_NI_BU_YERGA_QOYING")

# Sizning (administratorning) Telegram chat ID raqamingiz.
# Uni bilish uchun @userinfobot ga /start yozing.
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "123456789")

# "Administrator" tugmasi bosilganda ochiladigan shaxsiy Telegram profilingiz
# (@ belgisisiz, masalan: "john_doe")
ADMIN_TELEGRAM_USERNAME = os.environ.get("ADMIN_TELEGRAM_USERNAME", "your_username")

# Flask session uchun maxfiy kalit
SECRET_KEY = os.environ.get("SECRET_KEY", "juda-maxfiy-kalit-buni-ozgartiring")

# Ilova haqida matn
APP_NAME = "AvtoUsta"
