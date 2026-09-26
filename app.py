"""
Matritsalar va Determinant — Bilim Sinovi
Flask serveri:
  "/"              — quiz sahifasi (test + sertifikat generatori)
  "/api/natija"    — test tugagach JS shu yerga natijani yuboradi (JSON)
  "/natijalar"     — parol bilan himoyalangan sahifa: kim, qachon, nechta
                      to'g'ri javob berganini ko'rish uchun
  "/natijalar/csv" — natijalarni CSV fayl qilib yuklab olish

Faqat bepul narsalar ishlatilgan: Flask, gunicorn va Python'ning o'ziga
xos "sqlite3" moduli (alohida o'rnatish shart emas, ma'lumotlar bazasi
uchun tashqi to'lovli xizmat kerak emas).
"""
import csv
import io
import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)

# Ishlab chiqarishda bularni albatta o'zgartiring — Render/PythonAnywhere kabi
# platformalarda "Environment Variables" bo'limiga qo'ying, kodga yozmang.
app.secret_key = os.environ.get("SECRET_KEY", "iltimos-shu-qatorni-ozgartiring")
ADMIN_PAROL = os.environ.get("ADMIN_PAROL", "HUSNIDA")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "natijalar.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS natijalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ism TEXT NOT NULL,
            togri INTEGER NOT NULL,
            jami INTEGER NOT NULL,
            foiz INTEGER NOT NULL,
            sana TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/natija", methods=["POST"])
def api_natija():
    """Quiz tugagach frontend shu yerga {ism, togri, jami, foiz} yuboradi."""
    data = request.get_json(silent=True) or {}

    ism = str(data.get("ism", "")).strip()[:60] or "Ishtirokchi"
    try:
        togri = max(0, int(data.get("togri", 0)))
        jami = max(0, int(data.get("jami", 0)))
        foiz = max(0, min(100, int(data.get("foiz", 0))))
    except (TypeError, ValueError):
        return jsonify({"status": "xato", "xabar": "Noto'g'ri ma'lumot"}), 400

    sana = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    conn.execute(
        "INSERT INTO natijalar (ism, togri, jami, foiz, sana) VALUES (?, ?, ?, ?, ?)",
        (ism, togri, jami, foiz, sana),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


def fetch_all_natijalar():
    conn = get_db()
    rows = conn.execute("SELECT * FROM natijalar ORDER BY id DESC").fetchall()
    conn.close()
    return rows


@app.route("/natijalar", methods=["GET", "POST"])
def natijalar():
    """Parol bilan himoyalangan: kim, qachon, nechta to'g'ri javob bergani."""
    xato = False
    if request.method == "POST":
        if request.form.get("parol") == ADMIN_PAROL:
            session["admin_ok"] = True
        else:
            xato = True

    if not session.get("admin_ok"):
        return render_template("login.html", xato=xato)

    rows = fetch_all_natijalar()
    jami_kishi = len(rows)
    ortacha_foiz = round(sum(r["foiz"] for r in rows) / jami_kishi) if jami_kishi else 0
    return render_template(
        "natijalar.html", rows=rows, jami_kishi=jami_kishi, ortacha_foiz=ortacha_foiz
    )


@app.route("/natijalar/csv")
def natijalar_csv():
    if not session.get("admin_ok"):
        return redirect(url_for("natijalar"))

    rows = fetch_all_natijalar()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Ism", "To'g'ri", "Jami savol", "Foiz", "Sana"])
    for r in rows:
        writer.writerow([r["ism"], r["togri"], r["jami"], r["foiz"], r["sana"]])

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=natijalar.csv"},
    )


@app.route("/chiqish")
def chiqish():
    session.pop("admin_ok", None)
    return redirect(url_for("natijalar"))


# Bulutli platformalar (Render, Railway, PythonAnywhere va h.k.) uchun
# ular beradigan PORT muhit o'zgaruvchisini o'qiymiz, bo'lmasa 5000-portda ishga tushamiz.
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
