# 🚀 دليل التشغيل - Sign Language API

---

## 📋 المتطلبات

| البرنامج | الإصدار | التحقق |
|----------|---------|--------|
| Node.js | v18+ | `node --version` |
| Python | 3.10+ | `python --version` |
| Git | أي إصدار | `git --version` |
| Postman | أي إصدار | للتجربة |

---

## 1️⃣ تشغيل الـ Backend (Node.js) - محلياً

```bash
# تثبيت المكتبات (أول مرة بس)
npm install

# تشغيل السيرفر في وضع التطوير (يعيد التشغيل تلقائياً عند أي تعديل)
npm run dev

# أو تشغيل عادي
npm start
```

> ✅ السيرفر هيشتغل على: `http://localhost:3000`
> 
> ✅ Health Check: `http://localhost:3000/health`
> 
> ✅ كل الـ Endpoints: `http://localhost:3000/api`

---

## 2️⃣ تشغيل الـ AI Service (Python Flask)

### الطريقة السريعة (start.bat):
```bash
# دوبل كليك على الملف ده
ai_service\start.bat
```

### الطريقة اليدوية:
```bash
# الدخول لفولدر الـ AI
cd ai_service

# إنشاء بيئة افتراضية (أول مرة بس)
python -m venv venv

# تفعيل البيئة الافتراضية
.\venv\Scripts\activate

# تثبيت المكتبات (أول مرة بس)
pip install -r requirements.txt

# تشغيل السيرفر
python app.py
```

> ✅ الـ AI هيشتغل على: `http://127.0.0.1:5000`
> 
> ✅ Health Check: `http://127.0.0.1:5000/health`
> 
> ✅ Predict: `POST http://127.0.0.1:5000/predict` (أرسل صورة بـ key اسمه `file`)

---

## 3️⃣ الـ Backend على Railway (Production)

الـ Backend متنشر بالفعل على Railway:

```
🌐 URL: https://newproject-production-396a.up.railway.app
```

### لدفع تعديلات جديدة لـ Railway:
```bash
# إضافة الملفات المعدلة
git add .

# عمل commit
git commit -m "وصف التعديل"

# دفع التعديلات (Railway بيعمل deploy تلقائي)
git push origin usif-1
```

> ⚡ Railway بيعمل **auto-deploy** لما تعمل push - مش محتاج تعمل حاجة تانية.

---

## 4️⃣ أوامر Prisma (قاعدة البيانات)

```bash
# توليد Prisma Client (بيحصل تلقائياً بعد npm install)
npx prisma generate

# دفع التعديلات لقاعدة البيانات
npx prisma db push

# عمل migration جديد
npx prisma migrate dev

# فتح Prisma Studio (واجهة رسومية لقاعدة البيانات)
npx prisma studio
```

---

## 5️⃣ الاختبار بـ Postman

### الخطوات:
1. افتح Postman
2. اعمل Import للملف: `SignLanguage_API.postman_collection.json`
3. ابدأ بالترتيب:
   - **Register** → إنشاء حساب
   - **Login** → التوكن بيتحفظ تلقائياً ✅
   - باقي الـ Endpoints هتشتغل بالتوكن أوتوماتيك

### المتغيرات (Variables):
| المتغير | القيمة |
|---------|--------|
| `baseUrl` | `https://newproject-production-396a.up.railway.app/api` |
| `aiBaseUrl` | `http://127.0.0.1:5000` |
| `authToken` | بيتملى تلقائياً بعد Login |

---

## 6️⃣ الربط مع Flutter

### للـ Android Emulator:
```dart
// بدل localhost استخدم:
const baseUrl = 'http://10.0.2.2:3000/api';      // Node.js Backend
const aiUrl   = 'http://10.0.2.2:5000';           // AI Service
```

### لجهاز حقيقي (على نفس الشبكة):
```dart
// استخدم IP جهازك:
const baseUrl = 'http://192.168.1.5:3000/api';    // Node.js Backend
const aiUrl   = 'http://192.168.1.5:5000';        // AI Service
```

### للـ Production (Railway):
```dart
const baseUrl = 'https://newproject-production-396a.up.railway.app/api';
```

> 💡 معرفة IP جهازك: افتح CMD واكتب `ipconfig`

---

## 7️⃣ ملخص سريع

```
┌──────────────────────────────────────────────────┐
│          الترتيب الصحيح للتشغيل المحلي           │
│                                                  │
│  1. شغل AI Service:  ai_service\start.bat        │
│  2. شغل Backend:     npm run dev                 │
│  3. جرب من Postman أو Flutter                    │
└──────────────────────────────────────────────────┘
```

---

## ❓ مشاكل شائعة

| المشكلة | الحل |
|---------|------|
| `ECONNREFUSED :5000` | الـ AI Service مش شغال → شغله الأول |
| `ECONNREFUSED :3000` | الـ Backend مش شغال → `npm run dev` |
| `502 Bad Gateway` على Railway | اعمل `git push` تاني أو اتأكد من الـ logs |
| `Model weights not found` | تأكد إن `D:\Model_weights.pth` موجود |
| Token expired | اعمل Login تاني من Postman |
