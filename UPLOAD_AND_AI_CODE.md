# 📸 Upload & AI Translation - Complete Code Documentation

> **Project:** Sign Language Translation API  
> **Railway URL:** https://newproject-porject-usif.up.railway.app  
> **Last Updated:** 2026-06-05

---

## 📁 Project Structure (Upload & AI Related Files)

```
new_project/
├── ai_service/                          ← 🤖 AI Service (Python Flask)
│   ├── app.py                           ← Flask server + /predict endpoint
│   ├── model.py                         ← CustomCNN model architecture
│   ├── Model_weights.pth.zip            ← Trained model weights
│   ├── requirements.txt                 ← Python dependencies
│   ├── debug_model.py                   ← Debug tool for model testing
│   ├── debug_preprocess.py              ← Debug tool for preprocessing
│   ├── test_ai.py                       ← AI test script
│   └── test_sign.jpg                    ← Test image
│
├── src/                                 ← 🟢 Node.js Backend
│   ├── app.js                           ← Express app + /predict proxy
│   ├── config/
│   │   ├── index.js                     ← AI_MODEL_URL configuration
│   │   └── upload.js                    ← Multer upload config
│   ├── routes/
│   │   └── translation.routes.js        ← /api/translation routes
│   ├── controllers/
│   │   └── translation.controller.js    ← Upload & History controllers
│   ├── services/
│   │   └── translation.service.js       ← AI call + TTS + DB save
│   └── middleware/
│       └── auth.js                      ← JWT authentication
│
├── prisma/
│   └── schema.prisma                    ← Database schema (Upload model)
│
└── uploads/                             ← 📂 Uploaded images & audio files
```

---

## 🔄 Upload Flow (How it works)

```
┌──────────┐     POST /api/translation/upload      ┌──────────────┐
│  Flutter  │ ──── image (multipart/form-data) ───→ │  Node.js API │
│   App     │                                       │  (Express)   │
└──────────┘                                        └──────┬───────┘
                                                           │
                                          1. Save image (Multer)
                                          2. Send to AI Service
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │  AI Service  │
                                                    │  (Flask)     │
                                                    │  /predict    │
                                                    └──────┬───────┘
                                                           │
                                          3. AI returns: { translation: "A", confidence: 0.98 }
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │  Node.js API │
                                                    │  - Generate  │
                                                    │    TTS audio │
                                                    │  - Save to   │
                                                    │    Database  │
                                                    └──────┬───────┘
                                                           │
                                          4. Response to Flutter:
                                             { imageUrl, translation, audioUrl }
                                                           │
                                                           ▼
                                                    ┌──────────┐
                                                    │  Flutter  │
                                                    │   App     │
                                                    └──────────┘
```

---

## 🤖 AI Service Code (Python Flask)

### 📄 `ai_service/model.py` — CNN Model Architecture

```python
import torch
import torch.nn as nn


class CustomCNN(nn.Module):
    def __init__(self, num_classes=36):
        super(CustomCNN, self).__init__()

        self.block1 = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25)
        )

        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(64),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25)
        )

        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25)
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 512),  # 64x64 -> 32x32 -> 16x16 -> 8x8
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(512),
            nn.Dropout(0.5),
            nn.Linear(512, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.classifier(x)
        return x


def load_torch_model(num_classes=36):
    return CustomCNN(num_classes=num_classes)


def load_model(saved_weights, num_classes=36):
    """Load CustomCNN with saved weights."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model  = load_torch_model(num_classes=num_classes)
    model.load_state_dict(
        torch.load(saved_weights, map_location=device, weights_only=True)
    )
    model.to(device)
    model.eval()
    return model
```

---

### 📄 `ai_service/app.py` — Flask AI Server

```python
import os
import io
import torch
import torchvision.transforms as transforms
from flask import Flask, request, jsonify
from PIL import Image, ImageOps

# ── Import model from same directory ──────────────────────────────────────────
from model import load_model

# ── Configuration ──────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.environ.get(
    'MODEL_WEIGHTS_PATH',
    os.path.join(os.path.dirname(__file__), 'Model_weights.pth.zip')
)
NUM_CLASSES  = 36
DEVICE       = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 36 classes: 0-9 then A-Z (matches training data folder ordering)
CLASS_LABELS = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]

def download_weights_if_url(path_or_url):
    if path_or_url.startswith(('http://', 'https://')):
        local_filename = os.path.basename(path_or_url.split('?')[0])
        if not local_filename.endswith(('.pth', '.zip', '.bin')):
            local_filename = 'Model_weights.pth'
        
        local_path = os.path.join(os.getcwd(), local_filename)
        
        if os.path.exists(local_path):
            print(f"[AI Service] Weights already downloaded at: {local_path}")
            return local_path
            
        print(f"[AI Service] Downloading weights from {path_or_url} to {local_path}...")
        import urllib.request
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(path_or_url, local_path)
        print("[AI Service] Download complete!")
        return local_path
    return path_or_url

# ── Load model once at startup ─────────────────────────────────────────────────
resolved_weights_path = download_weights_if_url(WEIGHTS_PATH)
print(f"[AI Service] Loading model from: {resolved_weights_path}")
print(f"[AI Service] Using device: {DEVICE}")

model = load_model(resolved_weights_path)
model = model.to(DEVICE)
model.eval()

print("[AI Service] Model loaded successfully!")

# -- Image preprocessing (must match training pipeline) ────────────────────────
# NOTE: Model was trained with ToTensor() only (scales pixels to [0, 1]).
#       Do NOT apply ImageNet normalization here.
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
])

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'device': str(DEVICE)}), 200


@app.route('/predict', methods=['POST'])
def predict():
    """
    Accepts a multipart/form-data POST with key 'file' (image).
    Returns JSON: { "translation": "A", "confidence": 0.98, "result": "A" }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    try:
        # Read & preprocess image
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))
        # Fix EXIF rotation from mobile cameras
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        tensor = transform(image).unsqueeze(0).to(DEVICE)   # [1, 3, 64, 64]

        # Inference
        with torch.no_grad():
            outputs    = model(tensor)                        # [1, 36]
            probs      = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        label      = CLASS_LABELS[predicted.item()]
        confidence = round(confidence.item(), 4)

        THRESHOLD = 0.60  # Minimum Confidence

        if confidence < THRESHOLD:
            return jsonify({
                'error': "image doesn't include sign language character",
                'confidence': confidence
            }), 400

        return jsonify({
            'translation': label,
            'result'     : label,
            'confidence' : confidence,
        }), 200

    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/predict/debug', methods=['POST'])
def predict_debug():
    """
    Debug endpoint: returns top-5 predictions with BOTH possible class orderings.
    Use this to determine which ordering matches your actual sign.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use key "file".'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        original_size = image.size
        tensor = transform(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            top5 = torch.topk(probs, 5, dim=1)

        labels_0_9_AZ = [str(i) for i in range(10)] + [chr(c) for c in range(ord('A'), ord('Z') + 1)]
        labels_AZ_0_9 = [chr(c) for c in range(ord('A'), ord('Z') + 1)] + [str(i) for i in range(10)]

        results = []
        for j in range(5):
            idx = top5.indices[0][j].item()
            conf = round(top5.values[0][j].item(), 4)
            results.append({
                'rank': j + 1,
                'class_index': idx,
                'confidence': conf,
                'label_if_0to9_AtoZ': labels_0_9_AZ[idx],
                'label_if_AtoZ_0to9': labels_AZ_0_9[idx],
            })

        return jsonify({
            'image_original_size': list(original_size),
            'current_label': CLASS_LABELS[top5.indices[0][0].item()],
            'current_confidence': round(top5.values[0][0].item(), 4),
            'top5': results,
            'note': 'Compare the sign you made with both label columns to find the correct ordering',
        }), 200

    except Exception as e:
        return jsonify({'error': f'Debug prediction failed: {str(e)}'}), 500


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', os.environ.get('AI_PORT', 5000)))
    app.run(host='0.0.0.0', port=port, debug=False)
```

---

### 📄 `ai_service/requirements.txt` — Python Dependencies

```
flask>=3.0.0
torch>=2.0.0
torchvision>=0.15.0
Pillow>=10.0.0
```

---

## 🟢 Node.js Backend Code

### 📄 `src/config/upload.js` — Multer Upload Configuration

```javascript
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const uploadsDir = path.join(process.cwd(), 'uploads');

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }
    cb(null, uploadsDir);
  },
  filename: (_req, file, cb) => {
    const uniqueSuffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    cb(null, `sign-${uniqueSuffix}${path.extname(file.originalname)}`);
  },
});

const fileFilter = (_req, file, cb) => {
  if (file.mimetype.startsWith('image/')) {
    cb(null, true);
  } else {
    cb(new Error('Only images are allowed!'), false);
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: 10 * 1024 * 1024 },  // Max 10MB
});

module.exports = { upload };
```

---

### 📄 `src/config/index.js` — App Configuration (AI URL)

```javascript
require('dotenv').config();

const isProduction = process.env.NODE_ENV === 'production' || !!process.env.RAILWAY_STATIC_URL || !!process.env.RAILWAY_ENVIRONMENT;

if (isProduction && !process.env.JWT_SECRET) {
  console.error('[CONFIG] WARNING: JWT_SECRET is not set in production! Using fallback (INSECURE).');
}

const defaultAiUrl = 'http://127.0.0.1:5000/predict';
let aiModelUrl = process.env.AI_MODEL_URL || defaultAiUrl;

if (isProduction && (aiModelUrl === defaultAiUrl || aiModelUrl.includes('127.0.0.1') || aiModelUrl.includes('localhost'))) {
  aiModelUrl = 'https://newproject-porject-usif.up.railway.app/predict';
}

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  isProduction,
  jwtSecret: process.env.JWT_SECRET || 'dev-only-change-me',
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '30d',
  bcryptSaltRounds: parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10),
  corsOriginRaw: process.env.CORS_ORIGIN || '',
  aiModelUrl,
};
```

---

### 📄 `src/routes/translation.routes.js` — Translation Routes

```javascript
const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth');
const { upload } = require('../config/upload');
const translationController = require('../controllers/translation.controller');

router.post('/upload', protect, upload.single('image'), translationController.upload);
router.get('/history', protect, translationController.getHistory);

module.exports = router;
```

---

### 📄 `src/controllers/translation.controller.js` — Translation Controller

```javascript
const translationService = require('../services/translation.service');
const { ok } = require('../utils/response');
const { asyncHandler } = require('../utils/asyncHandler');

const upload = asyncHandler(async (req, res) => {
  const result = await translationService.uploadAndTranslate(req.user.id, req.file);
  return ok(res, result);
});

const getHistory = asyncHandler(async (req, res) => {
  const page = Math.max(1, parseInt(String(req.query.page ?? '1'), 10) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(String(req.query.limit ?? '20'), 10) || 20));
  const result = await translationService.getHistory(req.user.id, { page, limit });
  return ok(res, result);
});

module.exports = { upload, getHistory };
```

---

### 📄 `src/services/translation.service.js` — Translation Service (Core Logic)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const gTTS = require('gtts');
const { prisma } = require('../lib/prisma');
const config = require('../config');
const { AppError } = require('../utils/AppError');

async function uploadAndTranslate(userId, file) {
  if (!file) {
    throw new AppError('No image uploaded', 400);
  }

  const imagePath = file.path;
  let translationResult = 'Help';

  try {
    const form = new FormData();
    form.append('file', fs.createReadStream(imagePath));
    const aiResponse = await axios.post(config.aiModelUrl, form, {
      headers: form.getHeaders(),
      timeout: 30000,
    });
    translationResult =
      aiResponse.data?.translation || aiResponse.data?.result || translationResult;
  } catch (aiError) {
    // If AI returned 400 (low confidence / not a sign language image), pass that error to user
    if (aiError.response && aiError.response.status === 400) {
      const aiMsg = aiError.response.data?.error || "image doesn't include sign language character";
      throw new AppError(aiMsg, 400);
    }
    console.warn('AI model unavailable, using fallback translation:', aiError.message);
  }

  const audioFilename = `audio-${Date.now()}-${Math.round(Math.random() * 1e9)}.mp3`;
  const audioPath = path.join('uploads', audioFilename);
  const gtts = new gTTS(translationResult, 'en');

  await new Promise((resolve, reject) => {
    gtts.save(audioPath, (err) => (err ? reject(err) : resolve()));
  });

  await prisma.upload.create({
    data: {
      user_id: userId,
      image_path: imagePath,
      translation_result: translationResult,
      audio_path: audioPath,
    },
  });

  const norm = (p) => p ? p.replace(/\\/g, '/') : null;

  return {
    message: 'Translation successful',
    imageUrl: norm(imagePath),
    translation: translationResult,
    audioUrl: norm(audioPath),
  };
}

async function getHistory(userId, { page = 1, limit = 20 }) {
  const skip = (page - 1) * limit;
  const [rows, total] = await Promise.all([
    prisma.upload.findMany({
      where: { user_id: userId },
      skip,
      take: limit,
      orderBy: { created_at: 'desc' },
    }),
    prisma.upload.count({ where: { user_id: userId } }),
  ]);

  const norm = (p) => p ? p.replace(/\\/g, '/') : null;

  return {
    items: rows.map((row) => ({
      id: row.id,
      imageUrl: norm(row.image_path),
      translation: row.translation_result,
      audioUrl: norm(row.audio_path),
      createdAt: row.created_at,
    })),
    page,
    limit,
    total,
    totalPages: Math.ceil(total / limit) || 0,
  };
}

module.exports = { uploadAndTranslate, getHistory };
```

---

### 📄 `src/app.js` — Express App (includes /predict proxy)

```javascript
const express = require('express');
const path = require('path');
const fs = require('fs');
const helmet = require('helmet');
const compression = require('compression');
const { buildCors } = require('./config/cors');
const { apiLimiter } = require('./middleware/rateLimiter');

function createApp() {
  const app = express();

  const uploadsDir = path.join(process.cwd(), 'uploads');
  if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
  }

  app.disable('x-powered-by');
  app.use(helmet({ crossOriginResourcePolicy: { policy: 'cross-origin' } }));
  app.use(compression());
  app.use(buildCors());
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: false }));

  app.use('/uploads', express.static(uploadsDir));

  app.use(apiLimiter);

  app.get('/health', (_req, res) => {
    res.status(200).json({ success: true, data: { status: 'ok', timestamp: new Date().toISOString() } });
  });

  const { upload } = require('./config/upload');
  const axios = require('axios');
  const FormData = require('form-data');
  const config = require('./config');

  // ── /predict Proxy → Forwards request to Flask AI Service ──
  app.post('/predict', upload.single('file'), async (req, res) => {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded. Use key "file".' });
    }

    try {
      const form = new FormData();
      form.append('file', fs.createReadStream(req.file.path));

      const aiResponse = await axios.post(config.aiModelUrl, form, {
        headers: form.getHeaders(),
        timeout: 30000,
      });

      // Async cleanup local temp file
      fs.unlink(req.file.path, () => {});

      return res.status(200).json(aiResponse.data);
    } catch (aiError) {
      if (req.file) {
        fs.unlink(req.file.path, () => {});
      }
      console.error('[AI Proxy Error]:', aiError.message);
      return res.status(500).json({ error: `AI Service unavailable: ${aiError.message}` });
    }
  });

  app.get('/', (_req, res) => {
    res.json({
      success: true,
      data: {
        name: 'REST API',
        version: '1.0.0',
        apiIndex: '/api',
      },
    });
  });

  app.use('/api', require('./routes'));

  const { notFound } = require('./middleware/notFound');
  app.use(notFound);

  const { errorHandler } = require('./middleware/errorHandler');
  app.use(errorHandler);

  return app;
}

module.exports = { createApp };
```

---

### 📄 `src/middleware/auth.js` — JWT Authentication Middleware

```javascript
const jwt = require('jsonwebtoken');
const config = require('../config');
const { fail } = require('../utils/response');

function protect(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return fail(res, 'Not authorized: missing bearer token', 401);
  }

  const token = auth.split(' ')[1];
  try {
    const decoded = jwt.verify(token, config.jwtSecret);
    req.user = { id: decoded.id, name: decoded.name, email: decoded.email };
    return next();
  } catch {
    return fail(res, 'Not authorized: invalid or expired token', 401);
  }
}

module.exports = { protect };
```

---

## 🗄️ Database Schema

### 📄 `prisma/schema.prisma` — Upload Model

```prisma
model Upload {
  id                 Int      @id @default(autoincrement())
  user_id            Int
  image_path         String
  translation_result String?
  audio_path         String?
  created_at         DateTime @default(now())

  user               User     @relation(fields: [user_id], references: [id], onDelete: Cascade)

  @@map("uploads")
}
```

---

## 📡 API Endpoints

### Upload & Translation

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/translation/upload` | ✅ Bearer Token | Upload image → AI translate → TTS → Save to DB |
| `GET` | `/api/translation/history` | ✅ Bearer Token | Get user's translation history |
| `POST` | `/predict` | ❌ No Auth | Direct proxy to AI Flask service |
| `GET` | `/health` | ❌ No Auth | Health check |

### Request/Response Examples

#### POST `/api/translation/upload`
**Request:**
```
Headers: Authorization: Bearer <token>
Body: form-data
  key: "image" → type: File → select image
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Translation successful",
    "imageUrl": "uploads/sign-1717545600000-123456789.jpg",
    "translation": "A",
    "audioUrl": "uploads/audio-1717545600000-987654321.mp3"
  }
}
```

**Error Response (400) — Not a sign language image:**
```json
{
  "success": false,
  "error": "image doesn't include sign language character"
}
```

#### GET `/api/translation/history?page=1&limit=20`
**Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "imageUrl": "uploads/sign-xxx.jpg",
        "translation": "A",
        "audioUrl": "uploads/audio-xxx.mp3",
        "createdAt": "2026-06-01T..."
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 5,
    "totalPages": 1
  }
}
```

---

## 🧠 AI Model Details

| Property | Value |
|----------|-------|
| **Architecture** | CustomCNN (3 Conv blocks + Classifier) |
| **Input Size** | 64×64 RGB image |
| **Output** | 36 classes (0-9 + A-Z) |
| **Weights File** | `Model_weights.pth.zip` |
| **Preprocessing** | Resize(64,64) → ToTensor() (no ImageNet normalize) |
| **Confidence Threshold** | 60% minimum |
| **Device** | CUDA if available, else CPU |

### CNN Architecture Summary
```
Input: [batch, 3, 64, 64]
  ↓
Block 1: Conv2d(3→32) → ReLU → BN → Conv2d(32→32) → ReLU → MaxPool → Dropout
  ↓ [batch, 32, 32, 32]
Block 2: Conv2d(32→64) → ReLU → BN → Conv2d(64→64) → ReLU → MaxPool → Dropout
  ↓ [batch, 64, 16, 16]
Block 3: Conv2d(64→128) → ReLU → BN → Conv2d(128→128) → ReLU → MaxPool → Dropout
  ↓ [batch, 128, 8, 8]
Classifier: Flatten → Linear(8192→512) → ReLU → BN → Dropout → Linear(512→64) → ReLU → Dropout → Linear(64→36)
  ↓
Output: [batch, 36] (class probabilities after softmax)
```

---

## 🚀 How to Run

### AI Service (Python Flask)
```bash
cd ai_service
pip install -r requirements.txt
python app.py
# Running on http://127.0.0.1:5000
```

### Node.js Backend
```bash
npm install
npx prisma generate
npm start
# Running on http://localhost:3000
```

### Test with Postman
1. Import `SignLanguage7_API.postman_collection.json`
2. Run **Register** → **Login** (token auto-saved)
3. Go to **📸 Translation → Upload & Translate Image**
4. Select an image and Send!
