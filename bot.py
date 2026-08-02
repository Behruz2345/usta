import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import get_conn, init_db, gen_login, gen_password
import config

logging.basicConfig(level=logging.INFO)
init_db()

# Admin bilan suhbat holatini vaqtincha xotirada saqlaymiz: {chat_id: {"action": ..., **data}}
pending = {}


def is_admin(chat_id) -> bool:
    return str(chat_id) == str(config.ADMIN_CHAT_ID)


def main_menu_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📂 Bo'limlar", callback_data="admin_categories")],
            [InlineKeyboardButton("👨‍🔧 Ustalar", callback_data="admin_masters")],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        ]
    )


# ---------------- /start va /login ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if is_admin(chat_id):
        await update.message.reply_text(
            "👋 Salom, Administrator!\nBoshqaruv panelidan foydalaning:", reply_markup=main_menu_kb()
        )
    else:
        await update.message.reply_text(
            "Salom! Agar siz usta bo'lsangiz, akkauntingizni faollashtirish uchun quyidagi buyruqni yuboring:\n\n"
            "<code>/login login parol</code>",
            parse_mode="HTML",
        )


async def login_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) != 2:
        await update.message.reply_text("Foydalanish: /login login parol")
        return
    login, password = context.args
    conn = get_conn()
    master = conn.execute(
        "SELECT * FROM masters WHERE login = ? AND password = ?", (login, password)
    ).fetchone()
    if not master:
        await update.message.reply_text("❌ Login yoki parol noto'g'ri.")
        conn.close()
        return
    conn.execute("UPDATE masters SET telegram_chat_id = ? WHERE id = ?", (str(chat_id), master["id"]))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Akkaunt faollashtirildi, {master['full_name']}!\nEndi yangi klientlar haqida shu yerga xabar keladi."
    )


# ---------------- Admin: bo'limlar (kategoriyalar) ----------------

async def show_categories(chat_id, context, edit_message_id=None):
    conn = get_conn()
    cats = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    rows = [
        [
            InlineKeyboardButton(c["name"][:28], callback_data=f"noop"),
            InlineKeyboardButton("✏️", callback_data=f"cat_edit_{c['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"cat_del_{c['id']}"),
        ]
        for c in cats
    ]
    rows.append([InlineKeyboardButton("➕ Yangi bo'lim qo'shish", callback_data="cat_add")])
    rows.append([InlineKeyboardButton("« Orqaga", callback_data="admin_home")])
    kb = InlineKeyboardMarkup(rows)
    text = "📂 <b>Bo'limlar</b>\nTahrirlash yoki o'chirish uchun tugmani bosing."
    if edit_message_id:
        await context.bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message_id,
                                              reply_markup=kb, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")


# ---------------- Admin: ustalar ----------------

async def show_masters_menu(chat_id, context, edit_message_id=None):
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Usta qo'shish", callback_data="master_add")],
            [InlineKeyboardButton("📋 Ustalar ro'yxati", callback_data="master_list")],
            [InlineKeyboardButton("« Orqaga", callback_data="admin_home")],
        ]
    )
    text = "👨‍🔧 <b>Ustalar bo'limi</b>"
    if edit_message_id:
        await context.bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message_id,
                                              reply_markup=kb, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")


async def show_master_list(chat_id, context, edit_message_id=None):
    conn = get_conn()
    masters = conn.execute(
        """SELECT masters.*, categories.name as cat_name FROM masters
           JOIN categories ON masters.category_id = categories.id ORDER BY masters.id"""
    ).fetchall()
    conn.close()
    if not masters:
        text = "Hozircha ustalar yo'q."
    else:
        lines = ["👨‍🔧 <b>Ustalar ro'yxati</b>\n"]
        for m in masters:
            status = "🟢" if m["is_active"] else "🔴"
            linked = "✅ bog'langan" if m["telegram_chat_id"] else "⚠️ bog'lanmagan"
            lines.append(
                f"{status} <b>{m['full_name']}</b> — {m['cat_name']}\n"
                f"   login: <code>{m['login']}</code> | {linked}"
            )
        text = "\n".join(lines)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("« Orqaga", callback_data="admin_masters")]])
    if edit_message_id:
        await context.bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message_id,
                                              reply_markup=kb, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")


async def show_category_picker_for_master(chat_id, context, edit_message_id=None):
    conn = get_conn()
    cats = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    rows = [[InlineKeyboardButton(c["name"][:34], callback_data=f"master_cat_{c['id']}")] for c in cats]
    rows.append([InlineKeyboardButton("« Orqaga", callback_data="admin_masters")])
    kb = InlineKeyboardMarkup(rows)
    text = "Usta qaysi yo'nalishga tegishli?"
    if edit_message_id:
        await context.bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message_id, reply_markup=kb)
    else:
        await context.bot.send_message(chat_id, text, reply_markup=kb)


# ---------------- Admin: statistika ----------------

async def show_stats(chat_id, context, edit_message_id=None):
    conn = get_conn()
    visits = conn.execute("SELECT app_visits FROM stats WHERE id = 1").fetchone()["app_visits"]
    total_orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    accepted_orders = conn.execute("SELECT COUNT(*) c FROM orders WHERE status = 'accepted'").fetchone()["c"]
    total_masters = conn.execute("SELECT COUNT(*) c FROM masters WHERE is_active = 1").fetchone()["c"]
    conn.close()
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Ilovaga kirganlar: <b>{visits}</b>\n"
        f"📝 Jami buyurtmalar: <b>{total_orders}</b>\n"
        f"✅ Qabul qilinganlar: <b>{accepted_orders}</b>\n"
        f"👨‍🔧 Faol ustalar soni: <b>{total_masters}</b>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("« Orqaga", callback_data="admin_home")]])
    if edit_message_id:
        await context.bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message_id,
                                              reply_markup=kb, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")


# ---------------- Callback query router ----------------

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    msg_id = query.message.message_id
    data = query.data
    await query.answer()

    # ---- Buyurtma qabul/bekor qilish (usta tomonidan) ----
    if data.startswith("accept_") or data.startswith("decline_"):
        order_id = int(data.split("_")[1])
        conn = get_conn()
        master = conn.execute("SELECT * FROM masters WHERE telegram_chat_id = ?", (str(chat_id),)).fetchone()
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

        if not master or not order:
            conn.close()
            return

        if data.startswith("decline_"):
            await context.bot.edit_message_text(
                "❌ Siz ushbu buyurtmadan voz kechdingiz.", chat_id=chat_id, message_id=msg_id
            )
            conn.close()
            return

        if order["status"] != "new":
            await context.bot.edit_message_text(
                "⛔ Bu buyurtma allaqachon band qilingan.", chat_id=chat_id, message_id=msg_id
            )
            conn.close()
            return

        conn.execute(
            "UPDATE orders SET status = 'accepted', accepted_by = ? WHERE id = ?", (master["id"], order_id)
        )
        conn.commit()

        notifications = conn.execute(
            "SELECT * FROM order_notifications WHERE order_id = ?", (order_id,)
        ).fetchall()
        for n in notifications:
            try:
                if n["master_id"] == master["id"]:
                    await context.bot.edit_message_text(
                        "✅ Siz ushbu buyurtmani qabul qildingiz.",
                        chat_id=n["chat_id"], message_id=n["message_id"]
                    )
                else:
                    await context.bot.edit_message_text(
                        "⛔ Bu buyurtma boshqa usta tomonidan qabul qilindi.",
                        chat_id=n["chat_id"], message_id=n["message_id"]
                    )
            except Exception:
                pass

        await context.bot.send_message(
            config.ADMIN_CHAT_ID,
            f"✅ Buyurtma #{order_id} ni <b>{master['full_name']}</b> qabul qildi.",
            parse_mode="HTML",
        )
        conn.close()
        return

    # ---- Faqat admin uchun bo'lgan bo'limlar ----
    if not is_admin(chat_id):
        return

    if data == "admin_home":
        await query.edit_message_text("👑 Boshqaruv paneli:", reply_markup=main_menu_kb())

    elif data == "admin_categories":
        await show_categories(chat_id, context, msg_id)

    elif data == "admin_masters":
        await show_masters_menu(chat_id, context, msg_id)

    elif data == "admin_stats":
        await show_stats(chat_id, context, msg_id)

    elif data == "cat_add":
        pending[chat_id] = {"action": "add_category"}
        await query.edit_message_text("Yangi bo'lim nomini yozing:")

    elif data.startswith("cat_edit_"):
        cat_id = int(data.split("_")[2])
        pending[chat_id] = {"action": "edit_category", "id": cat_id}
        await query.edit_message_text("Yangi nomni yozing:")

    elif data.startswith("cat_del_"):
        cat_id = int(data.split("_")[2])
        conn = get_conn()
        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()
        await show_categories(chat_id, context, msg_id)

    elif data == "master_add":
        await show_category_picker_for_master(chat_id, context, msg_id)

    elif data.startswith("master_cat_"):
        cat_id = int(data.split("_")[2])
        pending[chat_id] = {"action": "add_master", "category_id": cat_id}
        await query.edit_message_text("Usta ismi va familiyasini yozing (masalan: Alisher Karimov):")

    elif data == "master_list":
        await show_master_list(chat_id, context, msg_id)


# ---------------- Matnli xabarlar (admin holatlariga javob) ----------------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in pending:
        return
    state = pending.pop(chat_id)
    text = update.message.text.strip()
    conn = get_conn()

    if state["action"] == "add_category":
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (text,))
        conn.commit()
        await update.message.reply_text(f"✅ '{text}' bo'limi qo'shildi.", reply_markup=main_menu_kb())

    elif state["action"] == "edit_category":
        conn.execute("UPDATE categories SET name = ? WHERE id = ?", (text, state["id"]))
        conn.commit()
        await update.message.reply_text(f"✅ Bo'lim nomi '{text}' ga o'zgartirildi.", reply_markup=main_menu_kb())

    elif state["action"] == "add_master":
        login = gen_login(text)
        password = gen_password()
        conn.execute(
            "INSERT INTO masters (category_id, full_name, login, password) VALUES (?, ?, ?, ?)",
            (state["category_id"], text, login, password),
        )
        conn.commit()
        await update.message.reply_text(
            f"✅ Usta qo'shildi: <b>{text}</b>\n\n"
            f"🔑 Login: <code>{login}</code>\n"
            f"🔑 Parol: <code>{password}</code>\n\n"
            "Ushbu ma'lumotlarni ustaga bering. U shaxsiy akkauntga botda quyidagi buyruq bilan kirishi mumkin:\n"
            f"<code>/login {login} {password}</code>\n\n"
            "yoki ilova saytidagi 'Shaxsiy akkaunt' bo'limi orqali.",
            parse_mode="HTML",
        )

    conn.close()


def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login_cmd))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
