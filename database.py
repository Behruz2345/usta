import sqlite3
import secrets
import string
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "autoapp.db")

CATEGORIES = [
    "Motorist (Dvigatel ustasi)",
    "Hodovik (Xodovoy / Podveska ustasi)",
    "Avtoelektrik (Elektromexanik)",
    "Kompyuter diagnostikasi ustasi",
    "Kuzov ustasi (Kuzovshchik)",
    "Malyar (Bo'yoqchi)",
    "Injektor / Karbyurator ustasi",
    "Razval-shoxqal ustasi",
    "Konditsioner ustasi",
    "Glushitel (Chiqindi gazlar tizimi) ustasi",
    "Oddiy plyonka ustasi (Tonirovshchik)",
    "Athermal (Atermik) plyonka ustasi",
    "Bronirovka (Himoya plyonkasi) ustasi",
    "Elyustratsiya va reklama ustasi",
    "Eksteryer tuning ustasi (Tashqi ko'rinish)",
    "Vinil va Wrapping ustasi (Plyonka va dizayn)",
    "Interyer tuning ustasi (Salon ichini yangilovchi)",
    "Chiptuning ustasi (Dasturiy tuning)",
    "Exhaust tuning ustasi (Chiqindi gaz / Ovoz sozlovchi)",
    "Avtozvuk (Audio tuning) ustasi",
    "Optika tuning ustasi (Chiroq sozlovchi)",
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS masters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            telegram_chat_id TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            extra_info TEXT,
            status TEXT DEFAULT 'new',
            accepted_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES categories(id),
            FOREIGN KEY(accepted_by) REFERENCES masters(id)
        );

        CREATE TABLE IF NOT EXISTS order_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            master_id INTEGER NOT NULL,
            chat_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );

        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            app_visits INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS admin_state (
            chat_id TEXT PRIMARY KEY,
            state TEXT,
            data TEXT
        );
        """
    )
    cur.execute("INSERT OR IGNORE INTO stats (id, app_visits) VALUES (1, 0)")
    for name in CATEGORIES:
        cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def gen_login(full_name: str) -> str:
    base = "".join(ch for ch in full_name.lower().replace(" ", "") if ch.isalnum())[:6] or "usta"
    conn = get_conn()
    while True:
        candidate = f"{base}{secrets.randbelow(9000) + 1000}"
        exists = conn.execute("SELECT 1 FROM masters WHERE login = ?", (candidate,)).fetchone()
        if not exists:
            conn.close()
            return candidate


def gen_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def increment_visits():
    conn = get_conn()
    conn.execute("UPDATE stats SET app_visits = app_visits + 1 WHERE id = 1")
    conn.commit()
    conn.close()
