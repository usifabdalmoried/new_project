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
  limits: { fileSize: 10 * 1024 * 1024 },
});

const signsDir = path.join(uploadsDir, 'signs');

const signRefStorage = multer.diskStorage({
  destination: (req, _file, cb) => {
    if (!fs.existsSync(signsDir)) {
      fs.mkdirSync(signsDir, { recursive: true });
    }
    cb(null, signsDir);
  },
  filename: (req, file, cb) => {
    const letter = String(req.body.letter || req.params.letter || 'X')
      .trim()
      .toUpperCase();
    cb(null, `${letter}${path.extname(file.originalname) || '.jpg'}`);
  },
});

const signRefUpload = multer({
  storage: signRefStorage,
  fileFilter,
  limits: { fileSize: 10 * 1024 * 1024 },
});

module.exports = { upload, signRefUpload };
