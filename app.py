from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_conn, init_db, increment_visits
from telegram_utils import send_message, order_keyboard
from telegram_utils import edit_message
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

init_db()


@app.context_processor
def inject_globals():
    return {"admin_username": config.ADMIN_TELEGRAM_USERNAME}


@app.before_request
def _count_visit():
    # Faqat asosiy sahifaga birinchi marta kirganda hisoblaymiz (juda oddiy usul)
    if request.endpoint == "index" and not session.get("visited"):
        increment_visits()
        session["visited"] = True


@app.route("/")
def index():
    conn = get_conn()
    categories = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    return render_template("index.html", categories=categories, app_name=config.APP_NAME)


@app.route("/buyurtma/<int:category_id>", methods=["GET", "POST"])
def order_form(category_id):
    conn = get_conn()
    category = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not category:
        conn.close()
        return redirect(url_for("index"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        phone = request.form.get("phone", "").strip()
        extra_info = request.form.get("extra_info", "").strip()

        if not first_name or not last_name or not phone:
            flash("Iltimos, barcha majburiy maydonlarni to'ldiring.")
            conn.close()
            return render_template("order_form.html", category=category, app_name=config.APP_NAME)

        cur = conn.execute(
            """INSERT INTO orders (category_id, first_name, last_name, phone, extra_info, status)
               VALUES (?, ?, ?, ?, ?, 'new')""",
            (category_id, first_name, last_name, phone, extra_info),
        )
        order_id = cur.lastrowid
        conn.commit()

        # Ushbu yo'nalishdagi faol ustalarni topamiz
        masters = conn.execute(
            "SELECT * FROM masters WHERE category_id = ? AND is_active = 1 AND telegram_chat_id IS NOT NULL",
            (category_id,),
        ).fetchall()

        text = (
            f"🆕 <b>Yangi klient!</b>\n\n"
            f"📂 Yo'nalish: {category['name']}\n"
            f"👤 Ism familiya: {first_name} {last_name}\n"
            f"📞 Telefon: {phone}\n"
            f"📝 Qo'shimcha: {extra_info or '-'}"
        )

        for m in masters:
            msg_id = send_message(m["telegram_chat_id"], text, order_keyboard(order_id))
            if msg_id:
                conn.execute(
                    "INSERT INTO order_notifications (order_id, master_id, chat_id, message_id) VALUES (?, ?, ?, ?)",
                    (order_id, m["id"], m["telegram_chat_id"], msg_id),
                )

        # Adminga ham xabar boradi
        send_message(config.ADMIN_CHAT_ID, text + "\n\n(Barcha tegishli ustalarga yuborildi)")

        conn.commit()
        conn.close()
        return render_template("order_success.html", app_name=config.APP_NAME)

    conn.close()
    return render_template("order_form.html", category=category, app_name=config.APP_NAME)


@app.route("/haqida")
def about():
    return render_template("about.html", app_name=config.APP_NAME)


# ---------------- USTA SHAXSIY AKKAUNTI ----------------

@app.route("/kirish", methods=["GET", "POST"])
def master_login():
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "").strip()
        conn = get_conn()
        master = conn.execute(
            "SELECT * FROM masters WHERE login = ? AND password = ? AND is_active = 1", (login, password)
        ).fetchone()
        conn.close()
        if master:
            session["master_id"] = master["id"]
            return redirect(url_for("master_dashboard"))
        flash("Login yoki parol noto'g'ri.")
    return render_template("master_login.html", app_name=config.APP_NAME)


@app.route("/kabinet")
def master_dashboard():
    master_id = session.get("master_id")
    if not master_id:
        return redirect(url_for("master_login"))

    conn = get_conn()
    master = conn.execute(
        """SELECT masters.*, categories.name AS category_name
           FROM masters JOIN categories ON masters.category_id = categories.id
           WHERE masters.id = ?""",
        (master_id,),
    ).fetchone()
    if not master:
        session.pop("master_id", None)
        conn.close()
        return redirect(url_for("master_login"))

    new_orders = conn.execute(
        "SELECT * FROM orders WHERE category_id = ? AND status = 'new' ORDER BY created_at DESC",
        (master["category_id"],),
    ).fetchall()
    my_orders = conn.execute(
        "SELECT * FROM orders WHERE accepted_by = ? ORDER BY created_at DESC", (master_id,)
    ).fetchall()
    conn.close()
    return render_template(
        "master_dashboard.html",
        master=master,
        new_orders=new_orders,
        my_orders=my_orders,
        app_name=config.APP_NAME,
    )


@app.route("/kabinet/qabul/<int:order_id>", methods=["POST"])
def master_accept(order_id):
    master_id = session.get("master_id")
    if not master_id:
        return redirect(url_for("master_login"))

    conn = get_conn()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order and order["status"] == "new":
        conn.execute(
            "UPDATE orders SET status = 'accepted', accepted_by = ? WHERE id = ?", (master_id, order_id)
        )
        conn.commit()

        # Boshqa ustalarga yuborilgan xabarlarni yangilaymiz ("chatdek" - o'chirilgandek ko'rinadi)
        notifications = conn.execute(
            "SELECT * FROM order_notifications WHERE order_id = ?", (order_id,)
        ).fetchall()
        for n in notifications:
            if n["master_id"] == master_id:
                edit_message(n["chat_id"], n["message_id"], "✅ Siz ushbu buyurtmani qabul qildingiz.")
            else:
                edit_message(n["chat_id"], n["message_id"], "⛔ Bu buyurtma boshqa usta tomonidan qabul qilindi.")
        conn.close()
        flash("Buyurtma qabul qilindi.")
    else:
        conn.close()
        flash("Bu buyurtma allaqachon band qilingan.")
    return redirect(url_for("master_dashboard"))


@app.route("/kabinet/bekor/<int:order_id>", methods=["POST"])
def master_decline(order_id):
    master_id = session.get("master_id")
    if not master_id:
        return redirect(url_for("master_login"))
    flash("Buyurtmadan voz kechdingiz.")
    return redirect(url_for("master_dashboard"))


@app.route("/kabinet/chiqish")
def master_logout():
    session.pop("master_id", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
