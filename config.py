import os

# Telegram bot tokeningizni @BotFather orqali oling va shu yerga qo'ying
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8916769188:AAFkNdPm2xcZGjdwyUoHzDaA7j6m6ngXiAg")

# Sizning (administratorning) Telegram chat ID raqamingiz.
# Uni bilish uchun @userinfobot ga /start yozing.
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "8893508552")

# "Administrator" tugmasi bosilganda ochiladigan shaxsiy Telegram profilingiz
# (@ belgisisiz, masalan: "john_doe")
ADMIN_TELEGRAM_USERNAME = os.environ.get("ADMIN_TELEGRAM_USERNAME", "alidacru")

# Flask session uchun maxfiy kalit
SECRET_KEY = os.environ.get("SECRET_KEY", "ernfowrufh4785fg48fc")

APP_NAME = "AvtoUsta"
