# 🚀 دليل التشغيل وشرح المكتبات - Sign Language API

---

## 📋 المتطلبات الأساسية

| البرنامج | الإصدار | التحقق |
|----------|---------|--------|
| Node.js | v18+ | `node --version` |
| Python | 3.10+ | `python --version` |
| Git | أي إصدار | `git --version` |
| Postman | أي إصدار | للتجربة |

---

## 📦 أولاً: مكتبات الـ Backend (Node.js) وشرحها

هذه هي المكتبات المستخدمة في سيرفر Node.js (الموجودة في `package.json`):

| المكتبة | دورها في المشروع | أمر التثبيت المنفرد (اختياري) |
|---------|-----------------|-----------------------------|
| **express** | الإطار الأساسي لبناء السيرفر والـ APIs والتحكم في الـ Routes. | `npm install express` |
| **prisma** & **@prisma/client** | الـ ORM للتعامل مع قاعدة البيانات (إنشاء الجداول، الاستعلامات، والربط). | `npm install prisma @prisma/client` |
| **bcrypt** | لتشفير كلمات مرور المستخدمين (Hashing) قبل حفظها في قاعدة البيانات لحمايتها. | `npm install bcrypt` |
| **jsonwebtoken (JWT)** | لإنشاء وفحص توكن الأمان (Token) للتحقق من هوية المستخدم وحماية الـ Endpoints. | `npm install jsonwebtoken` |
| **multer** | لاستقبال ورفع الملفات والصور (مثل صور لغة الإشارة المرسلة للترجمة). | `npm install multer` |
| **axios** | لإرسال طلبات HTTP من سيرفر الـ Node.js إلى سيرفر الـ AI Service. | `npm install axios` |
| **dotenv** | لقراءة متغيرات البيئة السرية مثل (رابط قاعدة البيانات، الـ JWT Secret) من ملف `.env`. | `npm install dotenv` |
| **cors** | للسماح للتطبيقات الخارجية (مثل تطبيق Flutter أو الويب) بالاتصال بالـ API دون قيود الحماية الافتراضية للـ Browser. | `npm install cors` |
| **helmet** | لتأمين التطبيق وحمايته من الثغرات الأمنية الشائعة عبر إضافة HTTP headers أمنية. | `npm install helmet` |
| **compression** | لضغط حجم البيانات المرسلة من السيرفر لتسريع استجابة الـ API. | `npm install compression` |
| **express-rate-limit** | لتحديد عدد الطلبات المسموح بها لكل مستخدم في دقيقة معينة لحماية السيرفر من هجمات الإغراق (DDOS). | `npm install express-rate-limit` |
| **express-validator** | للتحقق من صحة البيانات المرسلة من المستخدم (مثل التأكد من كتابة إيميل صحيح أو كلمة مرور قوية). | `npm install express-validator` |
| **form-data** | لتجهيز وإرسال الملفات والصور بصيغة Multipart/Form-Data إلى سيرفر الـ AI. | `npm install form-data` |
| **gtts** | مكتبة تحويل النصوص إلى صوت (Google Text-to-Speech) لتحويل النص المترجم لصوت مسموع. | `npm install gtts` |

### 🛠️ كيفية تثبيت وتشغيل الـ Backend:
```bash
# 1. تثبيت كل المكتبات المذكورة أعلاه بضغطة واحدة:
npm install

# 2. إنشاء وتوليد جداول قاعدة البيانات:
npx prisma db push

# 3. تشغيل السيرفر في وضع التطوير (يعيد التشغيل تلقائياً عند أي تعديل):
npm run dev
```
> 🌐 السيرفر هيشتغل محلياً على: `http://localhost:3000`

---

## 🐍 ثانياً: مكتبات الـ AI Service (Python Flask) وشرحها

هذه هي المكتبات المستخدمة في سيرفر الذكاء الاصطناعي (الموجودة في `ai_service/requirements.txt`):

| المكتبة | دورها في المشروع |
|---------|-----------------|
| **flask** | الإطار البرمجي الخفيف لبناء سيرفر الـ API الخاص بنموذج الذكاء الاصطناعي لاستقبال الصور وإرجاع التوقعات. |
| **torch (PyTorch CPU)** | المكتبة الأساسية لتشغيل نموذج الذكاء الاصطناعي وعمل (Inference) لملف الأوزان `Model_weights.pth` (نسخة الـ CPU لتناسب الاستضافة المجانية). |
| **torchvision** | مكتبة مساعدة لـ PyTorch تحتوي على نماذج جاهزة وأدوات لمعالجة وتحويل الصور قبل إدخالها للنموذج. |
| **Pillow (PIL)** | لفتح وقراءة ومعالجة الصور المستقبلة من السيرفر. |
| **gunicorn** | سيرفر ويب احترافي لتشغيل تطبيق Flask في بيئة الإنتاج (Production) مثل Railway. |

### 🛠️ كيفية تثبيت وتشغيل الـ AI Service:

#### الطريقة السريعة (Windows):
دوبل كليك على الملف: `ai_service\start.bat`

#### الطريقة اليدوية:
```bash
# 1. الدخول لفولدر الـ AI
cd ai_service

# 2. إنشاء بيئة افتراضية (أول مرة فقط)
python -m venv venv

# 3. تفعيل البيئة الافتراضية
.\venv\Scripts\activate

# 4. تثبيت المكتبات المذكورة أعلاه
pip install -r requirements.txt

# 5. تشغيل السيرفر
python app.py
```
> 🌐 الـ AI هيشتغل محلياً على: `http://127.0.0.1:5000`

---

## 🚀 ثالثاً: النشر على Railway (Production)

الـ Backend والـ AI مربوطين ومنشورين بالفعل على Railway:
* **رابط الـ API الأساسي (Node.js):** `https://backend-porject-usif.up.railway.app`

### لدفع أي تعديلات جديدة للـ Production:
```bash
git add .
git commit -m "update: add library docs"
git push origin usif-1
```
(المنصة هتعمل Deploy تلقائياً للتعديلات الجديدة 🚀)

### ربط PostgreSQL على Railway (مهم جداً)

إذا ظهر خطأ مثل `Authentication failed against database server at postgres.railway.internal`:

1. افتح مشروعك على [Railway Dashboard](https://railway.app/dashboard).
2. تأكد أن عندك **خدمتين** في نفس المشروع:
   - **PostgreSQL** (قاعدة البيانات)
   - **Backend** (Node.js API)
3. ادخل على خدمة **PostgreSQL** → تبويب **Variables** → انسخ قيمة `DATABASE_URL`.
4. ادخل على خدمة **Backend** → **Variables**:
   - احذف أي `DATABASE_URL` قديم مكتوب يدوياً بكلمة مرور خاطئة.
   - أضف متغير جديد:
     - **الاسم:** `DATABASE_URL`
     - **القيمة:** `${{Postgres.DATABASE_URL}}`  
       (استبدل `Postgres` باسم خدمة PostgreSQL عندك إن كان مختلفاً)
   - أو الصق نفس `DATABASE_URL` المنسوخ من خطوة 3.
5. تأكد أيضاً من وجود `JWT_SECRET` و `AI_MODEL_URL` في متغيرات الـ Backend.
6. اعمل **Redeploy** لخدمة الـ Backend.
7. اختبر الاتصال:
   ```
   GET https://backend-porject-usif.up.railway.app/health
   ```
   يجب أن ترى `"database": "connected"`.

> **ملاحظة:** إذا أعدت إنشاء خدمة PostgreSQL، كلمة المرور تتغير — يجب تحديث `DATABASE_URL` في الـ Backend فوراً.

---

## 📱 رابعاً: الربط مع تطبيق الـ Flutter

### في بيئة التطوير (Development):
* **لو شغال بـ Android Emulator:** استخدم `http://10.0.2.2:5000/api` للاتصال بالـ Backend.
* **لو شغال بجهاز حقيقي:** استخدم الـ IP الخاص بجهازك (مثال: `http://192.168.1.5:5000/api`) بشرط أن يكون اللابتوب والموبايل على نفس شبكة الـ Wi-Fi.

### في بيئة الإنتاج (Production):
استخدم رابط الـ Railway مباشرة:
`https://backend-porject-usif.up.railway.app/api`

---

## ❓ حل المشاكل الشائعة

| المشكلة | السبب | الحل |
|---------|------|------|
| `ECONNREFUSED :5000` | سيرفر الـ AI مغلق | شغل سيرفر الـ Python أولاً |
| `ECONNREFUSED :3000` | سيرفر الـ Backend مغلق | تأكد من عمل `npm run dev` |
| `Model weights not found` | ملف الأوزان غير موجود | تأكد من وجود ملف الأوزان في مكانه الصحيح في الـ AI service |
| `Token expired` | توكن الأمان انتهت صلاحيته | قم بعمل تسجيل دخول (Login) جديد للحصول على توكن جديد |
| `Authentication failed against database server` | `DATABASE_URL` على Railway غير صحيح أو قديم | اتبع خطوات ربط PostgreSQL أدناه |

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
