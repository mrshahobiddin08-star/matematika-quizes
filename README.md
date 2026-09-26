# Matritsalar va Determinant — Bilim Sinovi

Universitet talabalari uchun amaliy matematika (chiziqli algebra) fanidan
**matritsalar va determinant** mavzusidagi 40 ta savoldan iborat interaktiv
veb-quiz. Har bir savolga 30 soniya vaqt beriladi, to'g'ri javobdan so'ng
tasodifiy tabriklash animatsiyasi (konfetti / sharlar / yulduzlar) chiqadi,
test oxirida esa har bir ishtirokchiga **ECO26-103** nomidan foizli
sertifikat (PNG rasm) beriladi.

## Loyiha tuzilishi

```
quiz-app/
├── app.py                # Flask serveri (bitta marshrut: "/")
├── requirements.txt      # Faqat bepul kutubxonalar: Flask, gunicorn
├── Procfile              # Bulutli platformalar uchun ishga tushirish buyrug'i
├── .gitignore
└── templates/
    └── index.html        # Butun frontend (HTML+CSS+JS) — bitta faylda,
                           # to'liq nusxa ko'chirish/ko'chirib olish qulay bo'lishi uchun
```

`templates/index.html` o'zida barcha 40 ta savol, taymer, tabriklash
animatsiyalari va sertifikat generatorini o'z ichiga oladi — kerak bo'lsa
uni boshqa loyihaga ham bitta fayl sifatida ko'chirib qo'yish mumkin.

## Ishlatilgan kutubxonalar (barchasi bepul / ochiq manbali)

- **Flask** — Python veb-serveri (BSD litsenziya, bepul)
- **gunicorn** — production server (MIT litsenziya, bepul)
- **canvas-confetti** — konfetti animatsiyasi, CDN orqali (MIT litsenziya, bepul)
- **Google Fonts** (Fraunces, Inter) — bepul shriftlar

To'lov talab qiladigan yoki litsenziya sotib olish kerak bo'lgan hech qanday
kutubxona ishlatilmagan.

## Mahalliy kompyuterda ishga tushirish

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Brauzerda `http://localhost:5000` manzilini oching.

## GitHub'ga joylash

```bash
git init
git add .
git commit -m "Matritsalar va determinant bo'yicha quiz"
git branch -M main
git remote add origin https://github.com/<FOYDALANUVCHI_NOMI>/<REPO_NOMI>.git
git push -u origin main
```

## Bulutga bepul joylash (Python asosida)

### 1-variant: Render.com (tavsiya etiladi, bepul tarif bor)

1. https://render.com saytida ro'yxatdan o'ting va GitHub akkauntingizni ulang.
2. **New +** → **Web Service** → repozitoriyangizni tanlang.
3. Sozlamalar:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
4. **Create Web Service** tugmasini bosing — bir necha daqiqadan so'ng sizga
   `https://<loyiha-nomi>.onrender.com` ko'rinishidagi bepul havola beriladi.

> Eslatma: Render'ning bepul tarifida server harakatsizlikdan so'ng "uxlab
> qoladi" va birinchi so'rovda 30-60 soniya sekinroq ochilishi mumkin — bu
> normal holat va bepul tarifning cheklovi.

### 2-variant: PythonAnywhere (bepul tarif bor)

1. https://www.pythonanywhere.com saytida bepul akkaunt oching.
2. **Files** bo'limidan loyiha fayllarini yuklang (yoki **Consoles**'dan
   `git clone <repo-havolangiz>` buyrug'ini bajaring).
3. **Web** bo'limidan **Add a new web app** → **Flask** → Python versiyasini
   tanlang, `app.py` faylini ko'rsating.
4. **Virtualenv** bo'limida `requirements.txt`'ni o'rnating:
   `pip install -r requirements.txt` (Bash konsolida).
5. **Reload** tugmasini bosing — sayt `https://<foydalanuvchi>.pythonanywhere.com`
   manzilida ishga tushadi.

### 3-variant: Railway.app

Render'dagi kabi: repozitoriyani ulang, build/start buyruqlari avtomatik
`Procfile`dan o'qib olinadi (`gunicorn app:app`), bepul kredit chegarasi
doirasida ishlaydi.

## Kim, nechta savolga to'g'ri javob berganini ko'rish ("Natijalar" sahifasi)

Har bir ishtirokchi testni yakunlaganda ismi, nechta to'g'ri javob bergani,
foizi va sanasi avtomatik ravishda serverdagi `natijalar.db` (SQLite)
faylida saqlanadi — bu uchun tashqi to'lovli xizmat kerak emas, Python'ning
o'ziga xos kutubxonasi ishlatilgan.

Natijalarni ko'rish uchun brauzerda saytingizga `/natijalar` qo'shib oching,
masalan:

```
https://<loyiha-nomi>.onrender.com/natijalar
```

Sahifa parol so'raydi. **Parol: `HUSNIDA`**. Parolni kiritgach:

- har bir ishtirokchining ismi, to'g'ri javoblari, foizi va sanasi jadvalda
  ko'rinadi;
- jami ishtirokchilar soni va o'rtacha foiz yuqorida ko'rsatiladi;
- **"CSV yuklab olish"** tugmasi orqali butun ro'yxatni Excel'da ochsa
  bo'ladigan faylga aylantirib olish mumkin.

### Parolni o'zgartirish

Standart parolni ishlab chiqarishda albatta o'zgartiring. Buning uchun
hosting platformangizda (Render → sizning servisingiz → **Environment**)
quyidagi muhit o'zgaruvchilarini qo'shing:

| Nomi          | Vazifasi                                   | Misol qiymat            |
|---------------|---------------------------------------------|--------------------------|
| `ADMIN_PAROL` | `/natijalar` sahifasiga kirish paroli       | `mening-maxfiy-parolim` |
| `SECRET_KEY`  | Flask sessiyalarini shifrlash uchun kalit   | tasodifiy uzun matn      |

Bularni qo'shmasangiz, kod ichidagi standart qiymatlar ishlatiladi — bu
faqat sinov (test) uchun yetarli, lekin haqiqiy foydalanish uchun xavfsiz
emas.

### Muhim eslatma (bepul tarif cheklovi)

Render kabi bepul platformalarda diskdagi fayllar (shu jumladan
`natijalar.db`) xizmat **qayta joylansa (redeploy qilinsa)** tozalanishi
mumkin — bu bepul tarifning cheklovi. Sayt oddiy ishlab turgan paytda
(qayta joylanmasa) natijalar yo'qolmaydi. Agar natijalarni doimiy
saqlashni istasangiz, vaqti-vaqti bilan CSV qilib yuklab olib turishni
yoki kelajakda tashqi bepul ma'lumotlar bazasiga (masalan Render'ning
bepul PostgreSQL'iga) o'tishni tavsiya qilamiz.

## Testni sozlash

- Savollar soni, matni va variantlarini o'zgartirish uchun
  `templates/index.html` faylidagi `QUESTIONS` massivini tahrirlang.
- Har bir savolga ajratilgan vaqtni o'zgartirish uchun shu fayldagi
  `TIME_PER_Q` o'zgaruvchisini tahrirlang (soniyalarda).
- Sertifikat matni/dizaynini o'zgartirish uchun `drawCertificate()`
  funksiyasini tahrirlang.
