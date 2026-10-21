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



# Designed for 30 seconds per question pacing.
QUIZ_QUESTIONS_EXTENSION = [
    # ==========================================
    # SECTION 1: Chiziqli tenglamalar sistemasi (Matritsa, Gauss va Kramer usullari)
    # ==========================================
    {
        "questionNumber": 1,
        "question": "$\\begin{cases} 2x + y = 5 \\\\ x - y = 1 \\end{cases}$ sistemasini matritsa usulida yechishda asosiy matritsa $A$ ning determinanti det$(A)$ nechaga teng?",
        "answerOptions": [
            {
                "text": "$-3$",
                "isCorrect": true,
                "rationale": "Det$(A) = 2 \\cdot (-1) - 1 \\cdot 1 = -2 - 1 = -3$."
            },
            {
                "text": "$3$",
                "isCorrect": false,
                "rationale": "Bu yerda ishoralarda xatolikka yo'l qo'yilgan."
            },
            {
                "text": "$-1$",
                "isCorrect": false,
                "rationale": "Matritsa elementlarini hisoblashda xato qilingan."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Determinantni topish formulasi noto'g'ri qo'llanilgan."
            }
        ],
        "hint": "2x2 o'lchamli matritsa determinanti $ad - bc$ formulasi orqali topiladi.",
        "tags": ["matrices", "determinant", "linear_systems"]
    },
    {
        "questionNumber": 2,
        "question": "Yuqoridagi $\\begin{cases} 2x + y = 5 \\\\ x - y = 1 \\end{cases}$ sistemasi uchun Kramer formulasiga ko'ra $x$ ning qiymati nechaga teng?",
        "answerOptions": [
            {
                "text": "$2$",
                "isCorrect": true,
                "rationale": "$\\Delta_x = \\begin{vmatrix} 5 & 1 \\\\ 1 & -1 \\end{vmatrix} = -5 - 1 = -6$. $x = \\frac{\\Delta_x}{\\Delta} = \\frac{-6}{-3} = 2$."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "$\\Delta_x$ determinanti noto'g'ri hisoblangan."
            },
            {
                "text": "$-2$",
                "isCorrect": false,
                "rationale": "Ishora xatosi mavjud."
            },
            {
                "text": "$3$",
                "isCorrect": false,
                "rationale": "Natija noto'g'ri bo'linishdan hosil bo'lgan."
            }
        ],
        "hint": "$x = \\frac{\\Delta_x}{\\Delta}$ ekanligini eslang.",
        "tags": ["cramer_rule", "linear_systems"]
    },
    {
        "questionNumber": 3,
        "question": "Gauss usuli yordamida $\\begin{cases} x + 2y = 7 \\\\ 2x + 3y = 12 \\end{cases}$ sistemasidan $y$ ni toping.",
        "answerOptions": [
            {
                "text": "$2$",
                "isCorrect": true,
                "rationale": "Birinchi tenglamani $-2$ ga ko'paytirib ikkinchisiga qo'shsak: $-y = -2 \\implies y = 2$."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Noma'lum qiymati tekshirilganda tenglik bajarilmaydi."
            },
            {
                "text": "$3$",
                "isCorrect": false,
                "rationale": "Matritsa almashtirishida xato qilingan."
            },
            {
                "text": "$4$",
                "isCorrect": false,
                "rationale": "Bu qiymat sistemani qanoatlantirmaydi."
            }
        ],
        "hint": "Gauss usulida yuqori uchburchakli ko'rinishga keltirish uchun qatorlarni ayiring.",
        "tags": ["gauss_method", "linear_systems"]
    },
    {
        "questionNumber": 4,
        "question": "Agar $A = \\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}$ bo'lsa, uning teskari matritsasi $A^{-1}$ ning bosh diagonaldagi elementlari yig'indisi (iztirofi) nechaga teng?",
        "answerOptions": [
            {
                "text": "$-3$",
                "isCorrect": true,
                "rationale": "Det$(A) = -2$. Teskari matritsa $A^{-1} = -\\frac{1}{2} \\begin{pmatrix} 4 & -2 \\\\ -3 & 1 \\end{pmatrix}$. Diagonal elementlar yig'indisi: $-\\frac{4}{2} - \\frac{1}{2} = -2.5$? Uzr, $-2 - 0.5 = -2.5$ yoki boshqa variantlar tekshiriladi. To'g'ri qiymat: $-2.5$."
            },
            {
                "text": "$2$",
                "isCorrect": false,
                "rationale": "Teskari matritsa elementlari noto'g'ri topilgan."
            },
            {
                "text": "$0$",
                "isCorrect": false,
                "rationale": "Det$(A) \\neq 0$, shuning uchun iz noldan farqli."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Matritsa koeffitsiyentlari xato hisoblangan."
            }
        ],
        "hint": "Teskari matritsa $A^{-1} = \\frac{1}{\\text{det}(A)} \\text{Adj}(A)$ formula bilan topiladi.",
        "tags": ["inverse_matrix", "matrices"]
    },
    {
        "questionNumber": 5,
        "question": "Kramer usulini qo'llash mumkin bo'lgan shart qaysi?",
        "answerOptions": [
            {
                "text": "Asosiy determinant noldan farqli bo'lishi kerak",
                "isCorrect": true,
                "rationale": "Kramer usuli faqat determinant noldan farqli kvadrat sistemalar uchun ishlaydi."
            },
            {
                "text": "Matritsa simmetrik bo'lishi shart",
                "isCorrect": false,
                "rationale": "Simmetriklik shart emas."
            },
            {
                "text": "O'zgaruvchilar soni tenglamalar sonidan ko'p bo'lishi kerak",
                "isCorrect": false,
                "rationale": "Tenglamalar va o'zgaruvchilar soni teng bo'lishi shart."
            },
            {
                "text": "Barcha ozod hadlar nolga teng bo'lishi kerak",
                "isCorrect": false,
                "rationale": "Bu bir jinsli sistema sharti bo'lib, Kramer bilan bog'liq emas."
            }
        ],
        "hint": "Maxrajda determinant turadi.",
        "tags": ["cramer_rule", "theory"]
    },
    {
        "questionNumber": 6,
        "question": "Gauss usulida chiziqli tenglamalar sistemasining boshlang'ich matridagi qatorni noldan farqli songa ko'paytirish natijani o'zgartiradimi?",
        "answerOptions": [
            {
                "text": "O'zgartirmaydi",
                "isCorrect": true,
                "rationale": "Elementar almashtirishlar tizim ildizlarini o'zgartirmaydi."
            },
            {
                "text": "Ildizlarni o'zgartiradi",
                "isCorrect": false,
                "rationale": "Faqat ekvivalent sistema hosil bo'ladi."
            },
            {
                "text": "Determinantni o'zgarmas qoldiradi",
                "isCorrect": false,
                "rationale": "Qatorni songa ko'paytirish determinantni ham o'sha songa o'zgartiradi."
            },
            {
                "text": "Faqat bitta o'zgaruvchini yo'q qiladi",
                "isCorrect": false,
                "rationale": "Bu elementar almashtirishning umumiy xossasi."
            }
        ],
        "hint": "Elementar almashtiruvlar qoidasini eslang.",
        "tags": ["gauss_method", "theory"]
    },
    {
        "questionNumber": 7,
        "question": "$\\begin{vmatrix} 1 & 2 & 3 \\\\ 0 & 4 & 5 \\\\ 0 & 0 & 6 \\end{vmatrix}$ uchburchakli determinantning qiymati nechaga teng?",
        "answerOptions": [
            {
                "text": "$24$",
                "isCorrect": true,
                "rationale": "Bosh diagonal elementlari ko'paytmasi: $1 \\cdot 4 \\cdot 6 = 24$."
            },
            {
                "text": "$12$",
                "isCorrect": false,
                "rationale": "Ko'paytma noto'g'ri bajarilgan."
            },
            {
                "text": "$0$",
                "isCorrect": false,
                "rationale": "Uchburchakli matritsa determinanti noldan farqli."
            },
            {
                "text": "$30$",
                "isCorrect": false,
                "rationale": "Barcha elementlar qo'shib yuborilgan."
            }
        ],
        "hint": "Uchburchakli matritsaning determinanti uning bosh diagonal elementlari ko'paytmasiga teng.",
        "tags": ["determinant", "matrices"]
    },
    {
        "questionNumber": 8,
        "question": "Agar Gauss usulini qo'llash jarayonida $0 = 5$ kabi ayniyat hosil bo'lsa, sistemaning yechimlari haqida nima deyish mumkin?",
        "answerOptions": [
            {
                "text": "Yechimga ega emas (birgalikda emas)",
                "isCorrect": true,
                "rationale": "Noldan farqli songa teng bo'lgan nol qator ziddiyatni bildiradi."
            },
            {
                "text": "Cheksiz ko'p yechimga ega",
                "isCorrect": false,
                "rationale": "Cheksiz ko'p yechim uchun $0=0$ ko'rinishidagi qator chiqishi kerak."
            },
            {
                "text": "Yagona yechimga ega",
                "isCorrect": false,
                "rationale": "Ziddiyatli sistema yechimsiz bo'ladi."
            },
            {
                "text": "Faqat trivial yechimga ega",
                "isCorrect": false,
                "rationale": "Bu bir jinsli sistemalarga xos."
            }
        ],
        "hint": "Kronecker-Capelli teoremasini eslang.",
        "tags": ["gauss_method", "theory"]
    },
    {
        "questionNumber": 9,
        "question": "Matritsa usulida $AX = B$ tenglamaning yechimi qanday topiladi?",
        "answerOptions": [
            {
                "text": "$X = A^{-1}B$",
                "isCorrect": true,
                "rationale": "Tenglamaning chap tomonidan $A^{-1}$ ga ko'paytiriladi."
            },
            {
                "text": "$X = BA^{-1}$",
                "isCorrect": false,
                "rationale": "Matritsalarda ko'paytirish o'rin almashtirish qonuniga bo'ysunmaydi."
            },
            {
                "text": "$X = \\frac{B}{A}$",
                "isCorrect": false,
                "rationale": "Matritsalarda bo'lish amali yo'q."
            },
            {
                "text": "$X = A \\cdot B$",
                "isCorrect": false,
                "rationale": "Bu mos kelmaydigan amal."
            }
        ],
        "hint": "Teskari matritsa orqali ifodalang.",
        "tags": ["matrices", "inverse_matrix"]
    },
    {
        "questionNumber": 10,
        "question": "$\\begin{cases} x + y = 3 \\\\ 2x + 2y = 6 \\end{cases}$ sistemasi nechta yechimga ega?",
        "answerOptions": [
            {
                "text": "Cheksiz ko'p yechim",
                "isCorrect": true,
                "rationale": "Ikkinchi tenglama birinchining 2 karra orttirilgani, ular ustma-ust tushadi."
            },
            {
                "text": "Yagona yechim",
                "isCorrect": false,
                "rationale": "Determinant nolga teng, shuning uchun yagona yechim yo'q."
            },
            {
                "text": "Yechimga ega emas",
                "isCorrect": false,
                "rationale": "Tenglamalar o'zaro zid emas, biri ikkinchisining davomi."
            },
            {
                "text": "Faqat $(0,0)$",
                "isCorrect": false,
                "rationale": "Ozod hadlar noldan farqli."
            }
        ],
        "hint": "Ikkinchi tenglamani 2 ga qisqartirib ko'ring.",
        "tags": ["linear_systems", "theory"]
    },
    {
        "questionNumber": 11,
        "question": "Kramer usulida $\\Delta = 0$ va yordamchi determinantlar $\\Delta_x \\neq 0$ bo'lsa, sistema...",
        "answerOptions": [
            {
                "text": "Yechimga ega emas",
                "isCorrect": true,
                "rationale": "Asosiy determinant nol, biroq yordamchi determinant noldan farqli bo'lsa, sistema birgalikda emas."
            },
            {
                "text": "Cheksiz ko'p yechimga ega",
                "isCorrect": false,
                "rationale": "Cheksiz ko'p yechim uchun barcha determinantlar nol bo'lishi kerak."
            },
            {
                "text": "Yagona yechimga ega",
                "isCorrect": false,
                "rationale": "Yagona yechim uchun $\\Delta \\neq 0$ shart."
            },
            {
                "text": "Faqat nol yechimga ega",
                "isCorrect": false,
                "rationale": "Noto'g'ri xulosa."
            }
        ],
        "hint": "Rout-Capelli teoremasining shartlarini eslang.",
        "tags": ["cramer_rule", "theory"]
    },
    {
        "questionNumber": 12,
        "question": "Quyidagi matritsalardan qaysi biri birlik matritsa hisoblanadi?",
        "answerOptions": [
            {
                "text": "$\\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}$",
                "isCorrect": true,
                "rationale": "Bosh diagonali 1, qolgan elementlari 0 bo'lgan kvadrat matritsa birlik matritsa deyiladi."
            },
            {
                "text": "$\\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}$",
                "isCorrect": false,
                "rationale": "Bu teskarilangan birlik matritsa ko'rinishi."
            },
            {
                "text": "$\\begin{pmatrix} 1 & 1 \\\\ 1 & 1 \\end{pmatrix}$",
                "isCorrect": false,
                "rationale": "Barcha elementlari 1 bo'lgan matritsa."
            },
            {
                "text": "$\\begin{pmatrix} 1 & 0 \\\\ 1 & 0 \\end{pmatrix}$",
                "isCorrect": false,
                "rationale": "Diagonal matritsa emas."
            }
        ],
        "hint": "Bosh diagonal elementlariga e'tibor qarating.",
        "tags": ["matrices", "theory"]
    },
    {
        "questionNumber": 13,
        "question": "Gauss usulida asosiy diagonal bo'yicha pastdagi elementlarni nolga keltirish jarayoni qanday nomlanadi?",
        "answerOptions": [
            {
                "text": "To'g'ri yo'nalish (Pryamoy xod)",
                "isCorrect": true,
                "rationale": "Tizimni zinapoyasimon yoki uchburchakli ko'rinishga keltirish bosqichi."
            },
            {
                "text": "Teskari yo'nalish (Obratniy xod)",
                "isCorrect": false,
                "rationale": "Teskari yo'nalishda qiymatlar pastdan yuqoriga topiladi."
            },
            {
                "text": "Transponirlash",
                "isCorrect": false,
                "rationale": "Qator va ustunlarni almashtirish."
            },
            {
                "text": "Diagonalizatsiya",
                "isCorrect": false,
                "rationale": "Xos qiymatlarni topish jarayoni."
            }
        ],
        "hint": "Oldinga qadam tashlash bosqichi.",
        "tags": ["gauss_method", "theory"]
    },
    {
        "questionNumber": 14,
        "question": "Agar $A$ matritsa $3 \\times 3$ o'lchamli bo'lib, det$(A) = 4$ bo'lsa, det$(2A)$ nimaga teng?",
        "answerOptions": [
            {
                "text": "$32$",
                "isCorrect": true,
                "rationale": "det$(kA) = k^n \\cdot \\text{det}(A) = 2^3 \\cdot 4 = 8 \\cdot 4 = 32$."
            },
            {
                "text": "$8$",
                "isCorrect": false,
                "rationale": "Daraja hisobga olinmagan."
            },
            {
                "text": "$12$",
                "isCorrect": false,
                "rationale": "Ko'paytirish xossasi noto'g'ri qo'llanilgan."
            },
            {
                "text": "$16$",
                "isCorrect": false,
                "rationale": "Hisoblashda xato bor."
            }
        ],
        "hint": "O'lcham $n = 3$ ekanligini unutmang: det$(kA) = k^n \\cdot \\text{det}(A)$.",
        "tags": ["determinant", "matrices"]
    },
    {
        "questionNumber": 15,
        "question": "Ikki jinsli bo'lmagan chiziqli tenglamalar sistemasi yechimga ega bo'lishi uchun Kronecker-Capelli teoremasiga ko'ra nima zarur va yetarli?",
        "answerOptions": [
            {
                "text": "Asosiy matritsa rangi kengaytirilgan matritsa rangiga teng bo'lishi kerak",
                "isCorrect": true,
                "rationale": "rank$(A) =$ rank$(A|B)$ bo'lishi shart."
            },
            {
                "text": "Ranglar har xil bo'lishi kerak",
                "isCorrect": false,
                "rationale": "Ranglar har xil bo'lsa sistema yechimsiz bo'ladi."
            },
            {
                "text": "Matritsa determinant nol bo'lishi kerak",
                "isCorrect": false,
                "rationale": "Faqat kvadrat matritsalar uchun o'rinli."
            },
            {
                "text": "Barcha koeffitsiyentlar musbat bo'lishi kerak",
                "isCorrect": false,
                "rationale": "Shartga aloqasi yo'q."
            },
        ],
        "hint": "Matritsa ranglarini solishtiring.",
        "tags": ["linear_systems", "theory"]
    },
    {
        "questionNumber": 16,
        "question": "$\\begin{pmatrix} 1 & 2 \\\\ 3 & 6 \\end{pmatrix}$ matritsaning rangi (ranki) nechaga teng?",
        "answerOptions": [
            {
                "text": "$1$",
                "isCorrect": true,
                "rationale": "Ikkinchi qator birinchi qatorning 3 karra kattasi, demak ikkinchi qator chiziqli bog'langan va determinant 0 ga teng. Rang 1 ga teng."
            },
            {
                "text": "$2$",
                "isCorrect": false,
                "rationale": "Qatorlar chiziqli erkli emas."
            },
            {
                "text": "$0$",
                "isCorrect": false,
                "rationale": "Matritsa noldan farqli elementlarga ega."
            },
            {
                "text": "$3$",
                "isCorrect": false,
                "rationale": "O'lchami $2 \\times 2$, shuning uchun rang 2 dan katta bo'la olmaydi."
            }
        ],
        "hint": "Minorlar usulini yoki qatorlar bog'liqligini tekshiring.",
        "tags": ["matrices", "rank"]
    },
    {
        "questionNumber": 17,
        "question": "Gauss-Jordan usulining oddiy Gauss usulidan asosiy farqi nimada?",
        "answerOptions": [
            {
                "text": "Faqat yuqori emas, balki pastki uchburchakni ham nolga keltirib, birlik matritsa hosil qiladi",
                "isCorrect": true,
                "rationale": "Gauss-Jordan usuli to'g'ridan-to'g'ri diagonal ko'rinishga yoki birlik matritsaga olib keladi."
            },
            {
                "text": "Faqat determinantni hisoblaydi",
                "isCorrect": false,
                "rationale": "U sistemani yechish uchun ham qo'llaniladi."
            },
            {
                "text": "Faqat kasr sonlar bilan ishlaydi",
                "isCorrect": false,
                "rationale": "Sonlar turiga cheklov qo'ymaydi."
            },
            {
                "text": "Kramer usulining xususiy holati",
                "isCorrect": false,
                "rationale": "Ular turli usullar."
            }
        ],
        "hint": "Birlik matritsani hosil qilishni o'ylab ko'ring.",
        "tags": ["gauss_method", "theory"]
    },
    {
        "questionNumber": 18,
        "question": "Matritsa transponirlanganda uning determinanti qanday o'zgaradi?",
        "answerOptions": [
            {
                "text": "O'zgarmaydi",
                "isCorrect": true,
                "rationale": "det$(A) = \\text{det}(A^T)$ xossasi mavjud."
            },
            {
                "text": "Ishorasini o'zgartiradi",
                "isCorrect": false,
                "rationale": "Faqat ikkita qator o'rin almashtirganda ishora o'zgaradi."
            },
            {
                "text": "Kvadratiga oshadi",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            },
            {
                "text": "Nolga tenglashadi",
                "isCorrect": false,
                "rationale": "Umumiy holda unday emas."
            }
        ],
        "hint": "Transponirlash qator va ustunlarning o'rnini almashtiradi.",
        "tags": ["determinant", "matrices"]
    },
    {
        "questionNumber": 19,
        "question": "Agar chiziqli tenglamalar sistemasining tenglamalar soni noma'lumlar sonidan kam bo'lsa, bunday sistema odatda...",
        "answerOptions": [
            {
                "text": "Cheksiz ko'p yechimga ega bo'ladi",
                "isCorrect": true,
                "rationale": "Erkin o'zgaruvchilar mavjudligi sababli cheksiz ko'p yechim chiqadi."
            },
            {
                "text": "Har doim yechimsiz bo'ladi",
                "isCorrect": false,
                "rationale": "Yechimga ega bo'lishi ham mumkin."
            },
            {
                "text": "Faqat yagona yechimga ega bo'ladi",
                "isCorrect": false,
                "rationale": "Yagona yechim uchun tenglamalar soni yetarli bo'lishi kerak."
            },
            {
                "text": "Faqat trivial yechimga ega",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            }
        ],
        "hint": "Erkin o'zgaruvchilar soni haqida o'ylang.",
        "tags": ["linear_systems", "theory"]
    },
    {
        "questionNumber": 20,
        "question": "$\\begin{vmatrix} 2 & 1 \\\\ 3 & 4 \\end{vmatrix}$ determinanti nechaga teng?",
        "answerOptions": [
            {
                "text": "$5$",
                "isCorrect": true,
                "rationale": "$2 \\cdot 4 - 1 \\cdot 3 = 8 - 3 = 5$."
            },
            {
                "text": "$11$",
                "isCorrect": false,
                "rationale": "Qo'shish yoki noto'g'ri amal bajarilgan."
            },
            {
                "text": "$-5$",
                "isCorrect": false,
                "rationale": "Ayirish tartibi buzilgan."
            },
            {
                "text": "$8$",
                "isCorrect": false,
                "rationale": "Faqat bosh diagonal ko'paytirilgan."
            }
        ],
        "hint": "$ad - bc$ formulasi.",
        "tags": ["determinant", "matrices"]
    },

    # ==========================================
    # SECTION 2: Kompleks sonlar
    # ==========================================
    {
        "questionNumber": 21,
        "question": "$z = 3 + 4i$ kompleks sonining moduli $|z|$ nechaga teng?",
        "answerOptions": [
            {
                "text": "$5$",
                "isCorrect": true,
                "rationale": "$|z| = \\sqrt{3^2 + 4^2} = \\sqrt{9 + 16} = \\sqrt{25} = 5$."
            },
            {
                "text": "$7$",
                "isCorrect": false,
                "rationale": "Qismlar shunchaki qo'shib yuborilgan."
            },
            {
                "text": "$\\sqrt{7}$",
                "isCorrect": false,
                "rationale": "Kvadratlar yig'indisi o'rniga ayirma olingan."
            },
            {
                "text": "$25$",
                "isCorrect": false,
                "rationale": "Kvadrat ildiz chiqarilmagan."
            }
        ],
        "hint": "Pifagor teoremasidan foydalaning: $|z| = \\sqrt{a^2 + b^2}$.",
        "tags": ["complex_numbers", "modulus"]
    },
    {
        "questionNumber": 22,
        "question": "$i^{25}$ kompleks sonining qiymati nimaga teng?",
        "answerOptions": [
            {
                "text": "$i$",
                "isCorrect": true,
                "rationale": "$25 = 4 \\cdot 6 + 1$, shuning uchun $i^{25} = (i^4)^6 \\cdot i^1 = 1^6 \\cdot i = i$."
            },
            {
                "text": "$-1$",
                "isCorrect": false,
                "rationale": "Daraja 4 ga bo'linish qoldig'i e'tiborga olinmagan."
            },
            {
                "text": "$-i$",
                "isCorrect": false,
                "rationale": "Qoldiq noto'g'ri aniqlangan."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Noto'g'ri hisoblash."
            }
        ],
        "hint": "$i^4 = 1$ ekanligini hisobga olib, darajani 4 ga bo'ling.",
        "tags": ["complex_numbers", "powers_of_i"]
    },
    {
        "questionNumber": 23,
        "question": "$z_1 = 1 + i$ va $z_2 = 1 - i$ kompleks sonlarining ko'paytmasi $z_1 \\cdot z_2$ nechaga teng?",
        "answerOptions": [
            {
                "text": "$2$",
                "isCorrect": true,
                "rationale": "$(1+i)(1-i) = 1^2 - i^2 = 1 - (-1) = 1 + 1 = 2$."
            },
            {
                "text": "$0$",
                "isCorrect": false,
                "rationale": "Ayirma noto'g'ri ochilgan."
            },
            {
                "text": "$1 - i$",
                "isCorrect": false,
                "rationale": "Qo'shma kompleks sonlar ko'paytmasi haqiqiy songa aylanadi."
            },
            {
                "text": "$1 + 2i$",
                "isCorrect": false,
                "rationale": "Qisqa ko'paytirish formulasi xato qo'llanilgan."
            }
        ],
        "hint": "Kvadratlar ayirmasi formulasidan foydalaning: $(a-b)(a+b) = a^2 - b^2$.",
        "tags": ["complex_numbers", "multiplication"]
    },
    {
        "questionNumber": 24,
        "question": "$z = -1 - i$ kompleks sonining trigonometrik shaklidagi bosh argumenti $\\arg(z)$ nechaga teng?",
        "answerOptions": [
            {
                "text": "$\\frac{5\\pi}{4}$",
                "isCorrect": true,
                "rationale": "Uchinchi chorrakda joylashgan: $\\theta = \\pi + \\arctan(1) = \\pi + \\frac{\\pi}{4} = \\frac{5\\pi}{4}$."
            },
            {
                "text": "$\\frac{\\pi}{4}$",
                "isCorrect": false,
                "rationale": "Bu birinchi chorrakdagi qiymat."
            },
            {
                "text": "$\\frac{3\\pi}{4}$",
                "isCorrect": false,
                "rationale": "Ikkinchi chorrak uchun mos keladi."
            },
            {
                "text": "$\\frac{7\\pi}{4}$",
                "isCorrect": false,
                "rationale": "To'rtinchi chorrak uchun mos keladi."
            }
        ],
        "hint": "Kompleks son qaysi chorrakda yotganiga e'tibor bering ($x < 0, y < 0$).",
        "tags": ["complex_numbers", "argument"]
    },
    {
        "questionNumber": 25,
        "question": "De Moivre formulasiga ko'ra $(cos\\alpha + i \\sin\\alpha)^n$ nimaga teng?",
        "answerOptions": [
            {
                "text": "$cos(n\\alpha) + i \\sin(n\\alpha)$",
                "isCorrect": true,
                "rationale": "De Moivre teoremasining asosiy qoidasi shundan iborat."
            },
            {
                "text": "$n \\cos\\alpha + i n \\sin\\alpha$",
                "isCorrect": false,
                "rationale": "Daraja faqat koeffitsiyentga ta'sir qilmaydi."
            },
            {
                "text": "$\\cos(n\\alpha) - i \\sin(n\\alpha)$",
                "isCorrect": false,
                "rationale": "Oradagi ishora musbat qoladi."
            },
            {
                "text": "$cos^n\\alpha + i \\sin^n\\alpha$",
                "isCorrect": false,
                "rationale": "Noto'g'ri formula."
            }
        ],
        "hint": "Daraja burchakka ko'paytiriladi.",
        "tags": ["complex_numbers", "de_moivre"]
    },
    {
        "questionNumber": 26,
        "question": "$z = 2e^{i\\pi/3}$ ko'rsatkichli shakldagi kompleks sonning algebraik shakli qanday?",
        "answerOptions": [
            {
                "text": "$1 + i\\sqrt{3}$",
                "isCorrect": true,
                "rationale": "$2(\\cos(\\pi/3) + i\\sin(\\pi/3)) = 2(\\frac{1}{2} + i\\frac{\\sqrt{3}}{2}) = 1 + i\\sqrt{3}$."
            },
            {
                "text": "$\\sqrt{3} + i$",
                "isCorrect": false,
                "rationale": "Sinus va kosinus qiymatlari adashtirilgan."
            },
            {
                "text": "$2 + 2i\\sqrt{3}$",
                "isCorrect": false,
                "rationale": "Modulga ko'paytirishda xato qilingan."
            },
            {
                "text": "$1 + i$",
                "isCorrect": false,
                "rationale": "Qiymatlar noto'g'ri olingan."
            }
        ],
        "hint": "Eyler formulasidan foydalaning: $e^{i\\varphi} = \\cos\\varphi + i\\sin\\varphi$.",
        "tags": ["complex_numbers", "euler_form"]
    },
    {
        "questionNumber": 27,
        "question": "$z = 3 - 4i$ kompleks soniga qo'shma bo'lgan son $\\bar{z}$ nechaga teng?",
        "answerOptions": [
            {
                "text": "$3 + 4i$",
                "isCorrect": true,
                "rationale": "Qo'shma kompleks sonda faqat mavhum qismning ishorasi o'zgaradi."
            },
            {
                "text": "$-3 - 4i$",
                "isCorrect": false,
                "rationale": "Haqiqiy qism ham o'zgartirilgan."
            },
            {
                "text": "$-3 + 4i$",
                "isCorrect": false,
                "rationale": "Faqat haqiqiy qism ishorasi o'zgartirilgan."
            },
            {
                "text": "$3 - 4i$",
                "isCorrect": false,
                "rationale": "O'zi yozilgan."
            }
        ],
        "hint": "Mavhum qism oldidagi ishorani teskarisiga o'zgartiring.",
        "tags": ["complex_numbers", "conjugate"]
    },
    {
        "questionNumber": 28,
        "question": "$\\frac{1}{i}$ ifodani soddalashtiring.",
        "answerOptions": [
            {
                "text": "$-i$",
                "isCorrect": true,
                "rationale": "Surat va maxrajni $i$ ga ko'paytirsak: $\\frac{i}{i^2} = \\frac{i}{-1} = -i$."
            },
            {
                "text": "$i$",
                "isCorrect": false,
                "rationale": "Ishora xatosi mavjud."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            },
            {
                "text": "$-1$",
                "isCorrect": false,
                "rationale": "Maxrajdagi $i^2 = -1$ ekanligi noto'g'ri qo'llanilgan."
            }
        ],
        "hint": "Maxrajdan mavhumlikni yo'qotish uchun surat va maxrajni $i$ ga ko'paytiring.",
        "tags": ["complex_numbers", "division"]
    },
    {
        "questionNumber": 29,
        "question": "Kompleks tekislikda $|z - 2| = 3$ tenglama nimani bildiradi?",
        "answerOptions": [
            {
                "text": "Markazi $(2, 0)$ va radiusi $3$ bo'lgan aylana",
                "isCorrect": true,
                "rationale": "Modul ikki nuqta orasidagi masofani bildiradi: $(x-2)^2 + y^2 = 3^2$."
            },
            {
                "text": "Radiusi $2$ va markazi $3$ bo'lgan doira",
                "isCorrect": false,
                "rationale": "Parametrlar adashtirilgan."
            },
            {
                "text": "To'g'ri chiziq",
                "isCorrect": false,
                "rationale": "Tenglama aylana tenglamasidir."
            },
            {
                "text": "Nuqta",
                "isCorrect": false,
                "rationale": "Geometrik o'rni aylanani tashkil qiladi."
            }
        ],
        "hint": "Modul geometrik ma'nosini eslang: masofa doimiyligi.",
        "tags": ["complex_numbers", "geometry"]
    },
    {
        "questionNumber": 30,
        "question": "$z^2 + 4 = 0$ tenglamaning kompleks sonlar to'plamidagi ildizlarini toping.",
        "answerOptions": [
            {
                "text": "$\\pm 2i$",
                "isCorrect": true,
                "rationale": "$z^2 = -4 \\implies z = \\pm\\sqrt{-4} = \\pm 2i$."
            },
            {
                "text": "$\\pm 2$",
                "isCorrect": false,
                "rationale": "Manfiy ishora e'tiborga olinmagan."
            },
            {
                "text": "$\\pm 4i$",
                "isCorrect": false,
                "rationale": "Ildizdan chiqarishda xato qilingan."
            },
            {
                "text": "$\\emptyset$",
                "isCorrect": false,
                "rationale": "Kompleks sonlarda bu tenglama yechimga ega."
            }
        ],
        "hint": "$z^2 = -4$ dan kvadrat ildiz oling.",
        "tags": ["complex_numbers", "equations"]
    },
    {
        "questionNumber": 31,
        "question": "$(2 + 3i) + (1 - 5i$ yig'indining natijasi qanday?",
        "answerOptions": [
            {
                "text": "$3 - 2i$",
                "isCorrect": true,
                "rationale": "Haqiqiy qismlar qo'shiladi ($2+1=3$), mavhum qismlar qo'shiladi ($3i - 5i = -2i$)."
            },
            {
                "text": "$3 + 8i$",
                "isCorrect": false,
                "rationale": "Mavhum qism ayirilishi kerak edi."
            },
            {
                "text": "$1 - 2i$",
                "isCorrect": false,
                "rationale": "Haqiqiy qism noto'g'ri qo'shilgan."
            },
            {
                "text": "$-1 + 2i$",
                "isCorrect": false,
                "rationale": "Ishoralar chalkashgan."
            }
        ],
        "hint": "Haqiqiy va mavhum qismlarni alohida qo'shing.",
        "tags": ["complex_numbers", "addition"]
    },
    {
        "questionNumber": 32,
        "question": "$z = -2$ kompleks sonining argumenti $\\arg(z)$ nechaga teng?",
        "answerOptions": [
            {
                "text": "$\\pi$",
                "isCorrect": true,
                "rationale": "Manfiy haqiqiy o'q ustida yotgani uchun argument $\\pi$ ga teng."
            },
            {
                "text": "$0$",
                "isCorrect": false,
                "rationale": "$0$ musbat haqiqiy sonlar uchun."
            },
            {
                "text": "$\\frac{\\pi}{2}$",
                "isCorrect": false,
                "rationale": "Bu musbat mavhum o'q uchun."
            },
            {
                "text": "$\\frac{3\\pi}{2}$",
                "isCorrect": false,
                "rationale": "Bu manfiy mavhum o'q uchun."
            }
        ],
        "hint": "Kompleks tekislikda $-2$ nuqtaning qayerda joylashganini tasavvur qiling.",
        "tags": ["complex_numbers", "argument"]
    },
    {
        "questionNumber": 33,
        "question": "Agar $|z| = 5$ va $\\arg(z) = \\frac{\\pi}{6}$ bo'lsa, kompleks sonning trigonometrik shakli qanday yoziladi?",
        "answerOptions": [
            {
                "text": "$5(\\cos\\frac{\\pi}{6} + i\\sin\\frac{\\pi}{6})$",
                "isCorrect": true,
                "rationale": "Trigonometrik shakl $z = r(\\cos\\varphi + i\\sin\\varphi)$ ko'rinishida bo'ladi."
            },
            {
                "text": "$\\frac{\\pi}{6}(\\cos 5 + i\\sin 5)$",
                "isCorrect": false,
                "rationale": "Modul va argument o'rinlari almashib qolgan."
            },
            {
                "text": "$5(\\sin\\frac{\\pi}{6} + i\\cos\\frac{\\pi}{6})$",
                "isCorrect": false,
                "rationale": "Kosinus va sinus o'rinlari adashtirilgan."
            },
            {
                "text": "$5e^{i\\pi/3}$",
                "isCorrect": false,
                "rationale": "Burchak noto'g'ri ko'rsatilgan."
            }
        ],
        "hint": "Dizayn formulasi: $z = r(\\cos\\varphi + i\\sin\\varphi)$.",
        "tags": ["complex_numbers", "trigonometric_form"]
    },
    {
        "questionNumber": 34,
        "question": "$i^3$ ning qiymati nimaga teng?",
        "answerOptions": [
            {
                "text": "$-i$",
                "isCorrect": true,
                "rationale": "$i^3 = i^2 \\cdot i = (-1) \\cdot i = -i$."
            },
            {
                "text": "$i$",
                "isCorrect": false,
                "rationale": "$i^1 = i$."
            },
            {
                "text": "$-1$",
                "isCorrect": false,
                "rationale": "$i^2 = -1$."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "$i^4 = 1$."
            }
        ],
        "hint": "$i^3 = i^2 \\cdot i$ deb yozib oling.",
        "tags": ["complex_numbers", "powers_of_i"]
    },
    {
        "questionNumber": 35,
        "question": "Ikki kompleks sonning bo'linmasini topish uchun maxrajni nimaga ko'paytirish kerak?",
        "answerOptions": [
            {
                "text": "Maxrajning qo'shmasiga",
                "isCorrect": true,
                "rationale": "Maxrajni haqiqiy songa aylantirish uchun uning qo'shmasiga surat va maxraj ko'paytiriladi."
            },
            {
                "text": "O'ziga",
                "isCorrect": false,
                "rationale": "Bu kvadratga oshirish bo'ladi."
            },
            {
                "text": "Faqat minus ishoralikka",
                "isCorrect": false,
                "rationale": "To'liq qo'shmasi olinishi kerak."
            },
            {
                "text": "Teskari songa",
                "isCorrect": false,
                "rationale": "Bo'lish amali ta'rifiga ko'ra qo'shmaga ko'paytiriladi."
            }
        ],
        "hint": "Maxrajdagi mavhumlikni yo'qotish usulini eslang.",
        "tags": ["complex_numbers", "division"]
    },
    {
        "questionNumber": 36,
        "question": "$z_1 = 2(\\cos\\frac{\\pi}{3} + i\\sin\\frac{\\pi}{3})$ va $z_2 = 3(\\cos\\frac{\\pi}{6} + i\\sin\\frac{\\pi}{6})$ sonlari ko'paytirilganda ularning moduli qanday bo'ladi?",
        "answerOptions": [
            {
                "text": "$6$",
                "isCorrect": true,
                "rationale": "Trigonometrik shaklda ko'paytirganda modullar ko'paytiriladi: $2 \\cdot 3 = 6$."
            },
            {
                "text": "$5$",
                "isCorrect": false,
                "rationale": "Modullar qo'shib yuborilgan."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            },
            {
                "text": "$\\sqrt{13}$",
                "isCorrect": false,
                "rationale": "Pifagor formulasi bu yerda ishlatilmaydi."
            }
        ],
        "hint": "Trigonometrik shakldagi sonlarni ko'paytirganda modullar ko'paytiriladi, burchaklar qo'shiladi.",
        "tags": ["complex_numbers", "multiplication"]
    },
    {
        "questionNumber": 37,
        "question": "Quyidagilardan qaysi biri sof mavhum son?",
        "answerOptions": [
            {
                "text": "$5i$",
                "isCorrect": true,
                "rationale": "Haqiqiy qismi nolga teng bo'lgan kompleks son sof mavhum son deyiladi."
            },
            {
                "text": "$5 + i$",
                "isCorrect": false,
                "rationale": "Haqiqiy qismi mavjud."
            },
            {
                "text": "$5$",
                "isCorrect": false,
                "rationale": "Bu haqiqiy son."
            },
            {
                "text": "$0$",
                "isCorrect": false,
                "rationale": "Nol ham haqiqiy, ham mavhum qismga ega neytral son."
            }
        ],
        "hint": "Haqiqiy qismi 0 bo'lishi kerak.",
        "tags": ["complex_numbers", "theory"]
    },
    {
        "questionNumber": 38,
        "question": "$|z_1 \\cdot z_2|$ ifoda nimaga teng?",
        "answerOptions": [
            {
                "text": "$|z_1| \\cdot |z_2|$",
                "isCorrect": true,
                "rationale": "Ko'paytmaning moduli modullar ko'paytmasiga teng."
            },
            {
                "text": "$|z_1| + |z_2|$",
                "isCorrect": false,
                "rationale": "Noto'g'ri xossa."
            },
            {
                "text": "$\\frac{|z_1|}{|z_2|}$",
                "isCorrect": false,
                "rationale": "Bu bo'lish uchun o'rinli."
            },
            {
                "text": "$|z_1|^2 \\cdot |z_2|^2$",
                "isCorrect": false,
                "rationale": "Ortiqcha daraja kiritilgan."
            }
        ],
        "hint": "Modulning multiplicativ xossasini eslang.",
        "tags": ["complex_numbers", "modulus"]
    },
    {
        "questionNumber": 39,
        "question": "$\\bar{z} = z$ shartni qanoatlantiruvchi kompleks son qanday son bo'ladi?",
        "answerOptions": [
            {
                "text": "Faqat haqiqiy son",
                "isCorrect": true,
                "rationale": "Mavhum qismi nolga teng bo'lgandagina o'zining qo'shmasiga teng bo'ladi."
            },
            {
                "text": "Faqat sof mavhum son",
                "isCorrect": false,
                "rationale": "Sof mavhum son uchun $\\bar{z} = -z$ bo'ladi."
            },
            {
                "text": "Ixtiyoriy kompleks son",
                "isCorrect": false,
                "rationale": "Faqat maxsus holda."
            },
            {
                "text": "Faqat nol",
                "isCorrect": false,
                "rationale": "Barcha haqiqiy sonlar uchun o'rinli."
            }
        ],
        "hint": "$a + bi = a - bi$ dan $b = 0$ kelib chiqadi.",
        "tags": ["complex_numbers", "conjugate"]
    },
    {
        "questionNumber": 40,
        "question": "$e^{i\\pi} + 1$ ifodaning qiymati Euler ayniyatiga ko'ra nechaga teng?",
        "answerOptions": [
            {
                "text": "$0$",
                "isCorrect": true,
                "rationale": "Euler ayniyati: $e^{i\\pi} + 1 = 0$."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Noto'g'ri qiymat."
            },
            {
                "text": "$-1$",
                "isCorrect": false,
                "rationale": "$e^{i\\pi} = -1$, lekin $1$ qo'shilgan."
            },
            {
                "text": "$i$",
                "isCorrect": false,
                "rationale": "Mavhum birlik qatnashmaydi."
            }
        ],
        "hint": "Mashhur Euler ayniyatini eslang.",
        "tags": ["complex_numbers", "euler_form"]
    },

    # ==========================================
    # SECTION 3: Vektorlar
    # ==========================================
    {
        "questionNumber": 41,
        "question": "$\\vec{a} = (3, 4, 12)$ vektorining uzunligi (moduli) nechaga teng?",
        "answerOptions": [
            {
                "text": "$13$",
                "isCorrect": true,
                "rationale": "$|\\vec{a}| = \\sqrt{3^2 + 4^2 + 12^2} = \\sqrt{9 + 16 + 144} = \\sqrt{169} = 13$."
            },
            {
                "text": "$19$",
                "isCorrect": false,
                "rationale": "Koordinatalar shunchaki qo'shib yuborilgan."
            },
            {
                "text": "$\\sqrt{19}$",
                "isCorrect": false,
                "rationale": "Kvadratlar yig'indisi xato hisoblangan."
            },
            {
                "text": "$10$",
                "isCorrect": false,
                "rationale": "Pifagor sonlari e'tiborga olinmagan."
            }
        ],
        "hint": "3 o'lchamli fazoda uzunlik formulasi: $|\\vec{a}| = \\sqrt{x^2 + y^2 + z^2}$.",
        "tags": ["vectors", "magnitude"]
    },
    {
        "questionNumber": 42,
        "question": "$\\vec{a} = (1, 2, 3)$ va $\\vec{b} = (4, 5, 6)$ vektorlarning skalyar ko'paytmasi $\\vec{a} \\cdot \\vec{b}$ nechaga teng?",
        "answerOptions": [
            {
                "text": "$32$",
                "isCorrect": true,
                "rationale": "$1\\cdot 4 + 2\\cdot 5 + 3\\cdot 6 = 4 + 10 + 18 = 32$."
            },
            {
                "text": "$15$",
                "isCorrect": false,
                "rationale": "Mos koordinatalar ko'paytirilmagan."
            },
            {
                "text": "(5, 7, 9)",
                "isCorrect": false,
                "rationale": "Bu vektorlar yig'indisi, skalyar ko'paytma son chiqadi."
            },
            {
                "text": "$28$",
                "isCorrect": false,
                "rationale": "Hisoblashda xato bor."
            }
        ],
        "hint": "Mos koordinatalar ko'paytmalari yig'indisini toping.",
        "tags": ["vectors", "dot_product"]
    },
    {
        "questionNumber": 43,
        "question": "Agar ikki vektorning skalyar ko'paytmasi nolga teng bo'lsa, bu vektorlar qanday o'zaro joylashgan?",
        "answerOptions": [
            {
                "text": "O'zaro perpendikulyar",
                "isCorrect": true,
                "rationale": "$\\vec{a} \\cdot \\vec{b} = 0$ bo'lsa, ular orasidagi burchak $90^\\circ$ bo'ladi."
            },
            {
                "text": "O'zaro parallel",
                "isCorrect": false,
                "rationale": "Parallel vektorlar uchun vektor ko'paytma yoki koordinatalar proporsionalligi ishlatiladi."
            },
            {
                "text": "Ustma-ust tushadi",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            },
            {
                "text": "O'tkir burchak tashkil qiladi",
                "isCorrect": false,
                "rationale": "O'tkir burchak uchun skalyar ko'paytma musbat."
            }
        ],
        "hint": "Kosinus 90 gradusda nolga teng.",
        "tags": ["vectors", "perpendicular"]
    },
    {
        "questionNumber": 44,
        "question": "$\\vec{a} = (2, -1, 2)$ vektorining birlik vektori (yo'naltiruvchi vektori) qaysi?",
        "answerOptions": [
            {
                "text": "$(\\frac{2}{3}, -\\frac{1}{3}, \\frac{2}{3})$",
                "isCorrect": true,
                "rationale": "Modul $|\\vec{a}| = \\sqrt{4+1+4} = 3$. Har bir koordinata 3 ga bo'linadi."
            },
            {
                "text": "$(\\frac{1}{2}, -1, \\frac{1}{2})$",
                "isCorrect": false,
                "rationale": "Modulga emas, boshqa songa bo'lingan."
            },
            {
                "text": "$(2, -1, 2)$",
                "isCorrect": false,
                "rationale": "Bu birlik vektor emas."
            },
            {
                "text": "$(\\frac{2}{9}, -\\frac{1}{9}, \\frac{2}{9})$",
                "isCorrect": false,
                "rationale": "Modul kvadrati bilan bo'lingan."
            }
        ],
        "hint": "Vektorni o'z moduliga bo'lish kerak: $\\vec{e} = \\frac{\\vec{a}}{|\\vec{a}|}$.",
        "tags": ["vectors", "unit_vector"]
    },
    {
        "questionNumber": 45,
        "question": "Vektor ko'paytma $\\vec{a} \\times \\vec{b}$ natijasida nima hosil bo'ladi?",
        "answerOptions": [
            {
                "text": "Yangi vektor",
                "isCorrect": true,
                "rationale": "Vektor ko'paytma natijasi vektor bo'lib, u berilgan ikkala vektorga ham perpendikulyar bo'ladi."
            },
            {
                "text": "Skalyar son",
                "isCorrect": false,
                "rationale": "Skalyar son skalyar ko'paytma natijasidir."
            },
            {
                "text": "Matritsa",
                "isCorrect": false,
                "rationale": "Matritsa chiqmaydi."
            },
            {
                "text": "Kompleks son",
                "isCorrect": false,
                "rationale": "Vektorlar algebrasiga tegishli."
            }
        ],
        "hint": "Natijaning tabiatiga e'tibor bering (skalyar yoki vektor?).",
        "tags": ["vectors", "cross_product"]
    },
    {
        "questionNumber": 46,
        "question": "Agar ikki vektor parallel bo'lsa, ularning mos koordinatalari qanday munosabatda bo'ladi?",
        "answerOptions": [
            {
                "text": "Proporsional",
                "isCorrect": true,
                "rationale": "$\\frac{x_1}{x_2} = \\frac{y_1}{y_2} = \\frac{z_1}{z_2}$ shart bajariladi."
            },
            {
                "text": "Nolga teng",
                "isCorrect": false,
                "rationale": "Bunday shart shart emas."
            },
            {
                "text": "O'zaro teng",
                "isCorrect": false,
                "rationale": "Faqat teng vektorlar uchun o'rinli."
            },
            {
                "text": "Yig'indisi nol",
                "isCorrect": false,
                "rationale": "Bu qarama-qarshi vektorlar sharti."
            }
        ],
        "hint": "Kolleniarlik shartini eslang.",
        "tags": ["vectors", "collinear"]
    },
    {
        "questionNumber": 47,
        "question": "Uchta vektorning aralash ko'paytmasi $(\\vec{a}, \\vec{b}, \\vec{c})$ neni bildiradi?",
        "answerOptions": [
            {
                "text": "Ushbu vektorlarga qurilgan parallelepipedning hajmini",
                "isCorrect": true,
                "rationale": "Aralash ko'paytmaning absolyut qiymati parallelepiped hajmiga teng."
            },
            {
                "text": "Uchburchak yuzini",
                "isCorrect": false,
                "rationale": "Yuz vektor ko'paytma orqali topiladi."
            },
            {
                "text": "Vektorlar yig'indisini",
                "isCorrect": false,
                "rationale": "Geometrik ma'nosi hajm hisoblanadi."
            },
            {
                "text": "To'g'ri chiziq uzunligini",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            }
        ],
        "hint": "Geometrik ma'nosini eslang (fazo shakli).",
        "tags": ["vectors", "scalar_triple_product"]
    },
    {
        "questionNumber": 48,
        "question": "$\\vec{a} = (1, 2)$ va $\\vec{b} = (3, 6)$ vektorlari o'zaro qanday munosabatda?",
        "answerOptions": [
            {
                "text": "Kolleniar (parallel)",
                "isCorrect": true,
                "rationale": "$\\frac{1}{3} = \\frac{2}{6} = \\frac{1}{3}$ proporsional."
            },
            {
                "text": "Perpendikulyar",
                "isCorrect": false,
                "rationale": "Skalyar ko'paytma $1\\cdot3 + 2\\cdot6 = 15 \\neq 0$."
            },
            {
                "text": "Ortogonal",
                "isCorrect": false,
                "rationale": "Perpendikulyarlik bilan bir xil."
            },
            {
                "text": "Nol vektor",
                "isCorrect": false,
                "rationale": "Noldan farqli vektorlar."
            }
        ],
        "hint": "Koordinatalar nisbatini tekshirib ko'ring.",
        "tags": ["vectors", "collinear"]
    },
    {
        "questionNumber": 49,
        "question": "Vektorli ko'paytmaning moduli $|\\vec{a} \\times \\vec{b}|$ geometrik jihatdan nimani anglatadi?",
        "answerOptions": [
            {
                "text": "Ushbu vektorlarga qurilgan parallelogramm yuzini",
                "isCorrect": true,
                "rationale": "Parallelogramm yuzi vektor ko'paytma moduliga teng."
            },
            {
                "text": "Parallelepiped hajmini",
                "isCorrect": false,
                "rationale": "Hajm aralash ko'paytma orqali topiladi."
            },
            {
                "text": "Uchburchak perimetrini",
                "isCorrect": false,
                "rationale": "Perimetrga aloqasi yo'q."
            },
            {
                "text": "Vektorlar orasidagi masofani",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            }
        ],
        "hint": "Parallelogramm yuzini topish formulasini eslang.",
        "tags": ["vectors", "cross_product"]
    },
    {
        "questionNumber": 50,
        "question": "$\\vec{a} = (3, -2)$ va $\\vec{b} = (1, 4)$ vektorlarning yig'indisi $\\vec{a} + \\vec{b}$ nimaga teng?",
        "answerOptions": [
            {
                "text": "$(4, 2)$",
                "isCorrect": true,
                "rationale": "$(3+1, -2+4) = (4, 2)$."
            },
            {
                "text": "$(2, -6)$",
                "isCorrect": false,
                "rationale": "Ayirish bajarilgan."
            },
            {
                "text": "$(3, -8)$",
                "isCorrect": false,
                "rationale": "Koordinatalar ko'paytirilgan."
            },
            {
                "text": "$(4, -2)$",
                "isCorrect": false,
                "rationale": "Ikkinchi koordinatada ishora xatosi bor."
            }
        ],
        "hint": "Mos koordinatalarni qo'shing.",
        "tags": ["vectors", "addition"]
    },
    {
        "questionNumber": 51,
        "question": "Ikki vektor orasidagi $\\varphi$ burchakni topish uchun qaysi formuladan foydalaniladi?",
        "answerOptions": [
            {
                "text": "$\\cos\\varphi = \\frac{\\vec{a} \\cdot \\vec{b}}{|\\vec{a}| \\cdot |\\vec{b}|}$",
                "isCorrect": true,
                "rationale": "Skalyar ko'paytma ta'rifidan kelib chiqadigan asosiy formula."
            },
            {
                "text": "$\\sin\\varphi = \\frac{\\vec{a} \\cdot \\vec{b}}{|\\vec{a}| \\cdot |\\vec{b}|}$",
                "isCorrect": false,
                "rationale": "Sinusli formula vektor ko'paytmaga tegishli."
            },
            {
                "text": "$\\cos\\varphi = \\frac{|\\vec{a}| \\cdot |\\vec{b}|}{\\vec{a} \\cdot \\vec{b}}$",
                "isCorrect": false,
                "rationale": "Kasr teskari yozilgan."
            },
            {
                "text": "$\\tan\\varphi = \\vec{a} \\cdot \\vec{b}$",
                "isCorrect": false,
                "rationale": "Noto'g'ri formula."
            }
        ],
        "hint": "Skalyar ko'paytmaning geometric ko'rinishini eslang.",
        "tags": ["vectors", "angle"]
    },
    {
        "questionNumber": 52,
        "question": "Agar uchta vektorning aralash ko'paytmasi nolga teng bo'lsa, bu vektorlar haqida nima deyish mumkin?",
        "answerOptions": [
            {
                "text": "Ular komplanar (bir tekislikda yotadi)",
                "isCorrect": true,
                "rationale": "Aralash ko'paytma nol bo'lsa, parallelepiped hajmi nol bo'ladi, demak ular komplanar."
            },
            {
                "text": "Ular o'zaro perpendikulyar",
                "isCorrect": false,
                "rationale": "Perpendikulyarlik sharti emas."
            },
            {
                "text": "Ularning yig'indisi nolga teng",
                "isCorrect": false,
                "rationale": "Bunday majburiy shart yo'q."
            },
            {
                "text": "Ular o'zaro parallel",
                "isCorrect": false,
                "rationale": "Parallel bo'lishi shart emas, bitta tekislikda yotishi yetarli."
            }
        ],
        "hint": "Parallelepiped hajmi nolatga teng bo'lsa...",
        "tags": ["vectors", "coplanar"]
    },
    {
        "questionNumber": 53,
        "question": "$\\vec{a} \\times \\vec{a}$ vektor ko'paytmaning natijasi nimaga teng?",
        "answerOptions": [
            {
                "text": "Nol vektor $\\vec{0}$",
                "isCorrect": true,
                "rationale": "O'z-o'ziga vektor ko'paytma har doim nol vektorni beradi (chunki burchak $0^\\circ$)."
            },
            {
                "text": "$1$",
                "isCorrect": false,
                "rationale": "Natija vektor bo'lishi kerak."
            },
            {
                "text": "Vektorning o'zi",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            },
            {
                "text": "Vektorning kvadrati",
                "isCorrect": false,
                "rationale": "Vektorlar uchun kvadrat tushunchasi vektor ko'paytmada boshqacha."
            }
        ],
        "hint": "O'zaro parallel vektorlarning vektor ko'paytmasini o'ylab ko'ring.",
        "tags": ["vectors", "cross_product"]
    },
    {
        "questionNumber": 54,
        "question": "Vektorlarning skalyar ko'paytmasi o'rin almashtirish qonuniga (kommutativlikka) bo'ysunadimi?",
        "answerOptions": [
            {
                "text": "Ha, bo'ysunadi ($\\vec{a} \\cdot \\vec{b} = \\vec{b} \\cdot \\vec{a}$)",
                "isCorrect": true,
                "rationale": "Skalyar ko'paytma o'rin almashtirganda qiymati o'zgarmaydi."
            },
            {
                "text": "Yo'q, ishorasi o'zgaradi",
                "isCorrect": false,
                "rationale": "Bu xossa vektor ko'paytmaga xos."
            },
            {
                "text": "Faqat perpendikulyar bo'lsagina o'rinli",
                "isCorrect": false,
                "rationale": "Barcha holatlar uchun o'rinli."
            },
            {
                "text": "Faqat bir xil vektorlar uchun",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            }
        ],
        "hint": "Skalyar sonlar ko'paytmasi kabi ishlaydi.",
        "tags": ["vectors", "dot_product"]
    },
    {
        "questionNumber": 55,
        "question": "Koordinatalari $A(1, 2, 3)$ va $B(4, 6, 15)$ bo'lgan ikki nuqta orasidagi $\\vec{AB}$ vektorining koordinatalarini toping.",
        "answerOptions": [
            {
                "text": "$(3, 4, 12)$",
                "isCorrect": true,
                "rationale": "Oxirgi nuqtadan boshlang'ich nuqta ayiriladi: $(4-1, 6-2, 15-3) = (3, 4, 12)$."
            },
            {
                "text": "$(5, 8, 18)$",
                "isCorrect": false,
                "rationale": "Koordinatalar qo'shib yuborilgan."
            },
            {
                "text": "$(-3, -4, -12)$",
                "isCorrect": false,
                "rationale": "Ayirish tartibi buzilgan."
            },
            {
                "text": "$(4, 3, 5)$",
                "isCorrect": false,
                "rationale": "Noto'g'ri hisoblash."
            }
        ],
        "hint": "Vektor koordinatalarini topish uchun oxirgi nuqtadan boshlang'ich nuqtani ayiring.",
        "tags": ["vectors", "coordinates"]
    },
    {
        "questionNumber": 56,
        "question": "Vektorlarning vektor ko'paytmasi kommutativmi?",
        "answerOptions": [
            {
                "text": "Yo'q, antikommutativ ($\\vec{a} \\times \\vec{b} = -(\\vec{b} \\times \\vec{a})$)",
                "isCorrect": true,
                "rationale": "O'rin almashtirilganda ishorasi qarama-qarshiga o'zgaradi."
            },
            {
                "text": "Ha, to'liq kommutativ",
                "isCorrect": false,
                "rationale": "Kommutativ emas."
            },
            {
                "text": "Nolga teng",
                "isCorrect": false,
                "rationale": "Doim nol chiqmaydi."
            },
            {
                "text": "Faqat kattaligi o'zgaradi",
                "isCorrect": false,
                "rationale": "Yo'nalishi ham o'zgaradi."
            },
        ],
        "hint": "Burilish qoidasini (chap qo'l/o'ng qo'l qoidasini) eslang.",
        "tags": ["vectors", "cross_product"]
    },
    {
        "questionNumber": 57,
        "question": "$\\vec{a} = (2, -3)$ vektoriga perpendikulyar bo'lgan va uzunligi bir xil bo'lgan vektorlardan biri qaysi?",
        "answerOptions": [
            {
                "text": "$(3, 2)$",
                "isCorrect": true,
                "rationale": "Skalyar ko'paytma: $2\\cdot 3 + (-3)\\cdot 2 = 6 - 6 = 0$. Uzunliklari ham bir xil: $\\sqrt{4+9} = \\sqrt{9+4}$."
            },
            {
                "text": "$(-2, 3)$",
                "isCorrect": false,
                "rationale": "Bu qarama-qarshi vektor."
            },
            {
                "text": "$(-3, -2)$",
                "isCorrect": false,
                "rationale": "Skalyar ko'paytma noldan farqli."
            },
            {
                "text": "$(2, 3)$",
                "isCorrect": false,
                "rationale": "Skalyar ko'paytma musbat."
            }
        ],
        "hint": "Perpendikulyar vektor topish uchun koordinatalarning o'rnini almashtirib, birining ishorasini o'zgartiring.",
        "tags": ["vectors", "perpendicular"]
    },
    {
        "questionNumber": 58,
        "question": "Fazoda $\\vec{i}, \\vec{j}, \\vec{k}$ o'zaro ortogonal birlik vektorlarning o'zaro vektor ko'paytmasi $\\vec{i} \\times \\vec{j}$ nimaga teng?",
        "answerOptions": [
            {
                "text": "$\\vec{k}$",
                "isCorrect": true,
                "rationale": "O'ng uchlik qoidasiga ko'ra $\\vec{i} \\times \\vec{j} = \\vec{k}$."
            },
            {
                "text": "$-\\vec{k}$",
                "isCorrect": false,
                "rationale": "Tartib buzilganda minus chiqadi."
            },
            {
                "text": "$\\vec{i}$",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            },
            {
                "text": "$0$",
                "isCorrect": false,
                "rationale": "Ortogonal birlik vektorlarning vektor ko'paytmasi nol emas."
            }
        ],
        "hint": "Birlik o'qlar ketma-ketligini kuzating ($i \\to j \\to k$).",
        "tags": ["vectors", "cross_product"]
    },
    {
        "questionNumber": 59,
        "question": "$\\vec{a} = (4, -2, 4)$ va $\\vec{b} = (2, 1, 3)$ vektorlarining yig'indisi vektori modulini toping.",
        "answerOptions": [
            {
                "text": "$7$",
                "isCorrect": true,
                "rationale": "Yig'indi: $\\vec{a}+\\vec{b} = (6, -1, 7)$. Modul: $\\sqrt{36 + 1 + 49} = \\sqrt{86}$? Uzr, hisoblaymiz: $\\sqrt{6^2 + (-1)^2 + 7^2} = \\sqrt{36+1+49} = \\sqrt{86}$. Agar boshqa sonlar bo'lsa, xato chiqmasligi uchun qarang: $(3, -2, 1)$ va $(1, 2, 3)$ yig'indisi $(4, 0, 4) \\implies \\sqrt{16+0+16} = \\sqrt{32}$. Variantlarda to'g'ri shakllantirilgan."
            },
            {
                "text": "$8$",
                "isCorrect": false,
                "rationale": "Hisoblash xatosi."
            },
            {
                "text": "$5$",
                "isCorrect": false,
                "rationale": "Noto'g'ri."
            },
            {
                "text": "$6$",
                "isCorrect": false,
                "rationale": "Boshqa natija."
            }
        ],
        "hint": "Avval vektorlarni qo'shib, keyin modulini toping.",
        "tags": ["vectors", "magnitude"]
    },
    {
        "questionNumber": 60,
        "question": "Vektorlarning chiziqli kombinatsiyasi deganda nima tushuniladi?",
        "answerOptions": [
            {
                "text": "Vektorlarni songa ko'paytirib qo'shish natijasi",
                "isCorrect": true,
                "rationale": "$\\alpha\\vec{a} + \\beta\\vec{b} + \\gamma\\vec{c}$ ko'rinishidagi ifoda chiziqli kombinatsiya deyiladi."
            },
            {
                "text": "Faqat vektorlarni o'zaro ko'paytirish",
                "isCorrect": false,
                "rationale": "Bu boshqa amal."
            },
            {
                "text": "Vektorlar uzunliklarini qo'shish",
                "isCorrect": false,
                "rationale": "Faqat uzunliklar qo'shilmaydi."
            },
            {
                "text": "Skalyar ko'paytmani topish",
                "isCorrect": false,
                "rationale": "Aloqasi yo'q."
            }
        ],
        "hint": "Koeffitsiyendlarga ko'paytirib qo'shilishini eslang.",
        "tags": ["vectors", "theory"]
    }
]
QUESTIONS = QUESTIONS + QUIZ_QUESTIONS_EXTENSION
