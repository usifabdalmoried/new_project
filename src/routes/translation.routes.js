const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth');
const { upload } = require('../config/upload');
const translationController = require('../controllers/translation.controller');

router.post(
  '/upload',
  protect,
  upload.single('file'),   // 🔥 أهم سطر في المشروع كله
  translationController.upload
);

router.get('/history', protect, translationController.getHistory);

module.exports = router;
