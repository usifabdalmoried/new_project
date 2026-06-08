const express = require('express');
const path = require('path');
const fs = require('fs');
const { ok } = require('../utils/response');
const { getSignImagePath } = require('../utils/signReference');

const router = express.Router();

const SIGNS_DIR = path.join(process.cwd(), 'public', 'signs');
const SIGN_ORDER = [
  ...Array.from({ length: 10 }, (_, i) => String(i)),
  ...Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i)),
];

function listSignFiles() {
  if (!fs.existsSync(SIGNS_DIR)) {
    return [];
  }

  return SIGN_ORDER.map((letter) => {
    const imageUrl = getSignImagePath(letter);
    if (!imageUrl) return null;
    return { letter, imageUrl };
  }).filter(Boolean);
}

router.get('/', (req, res) => {
  const signs = listSignFiles();
  return ok(res, {
    signs,
    total: signs.length,
    expected: SIGN_ORDER.length,
    missing: SIGN_ORDER.filter((letter) => !signs.some((s) => s.letter === letter)),
  });
});

router.get('/:letter', (req, res) => {
  const letter = String(req.params.letter || '').toUpperCase();
  if (!SIGN_ORDER.includes(letter)) {
    return res.status(404).json({ success: false, message: 'Invalid letter. Use 0-9 or A-Z.' });
  }

  const imageUrl = getSignImagePath(letter);
  if (!imageUrl) {
    return res.status(404).json({ success: false, message: `Sign image for "${letter}" not found yet.` });
  }

  return ok(res, {
    letter,
    imageUrl,
  });
});

module.exports = router;
