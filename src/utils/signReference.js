const path = require('path');
const fs = require('fs');

const SIGNS_DIR = path.join(process.cwd(), 'public', 'signs');
const EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.gif'];

function normalizeLetter(label) {
  if (label == null || label === '') return null;
  const value = String(label).trim().toUpperCase();
  if (/^[0-9]$/.test(value)) return value;
  if (/^[A-Z]$/.test(value)) return value;
  return null;
}

function getSignImagePath(letter) {
  const normalized = normalizeLetter(letter);
  if (!normalized) return null;

  const found = EXTENSIONS.map((ext) => path.join(SIGNS_DIR, `${normalized}${ext}`)).find((filePath) =>
    fs.existsSync(filePath)
  );

  if (!found) return null;
  return `signs/${path.basename(found)}`;
}

function attachSignReference(payload) {
  if (!payload || typeof payload !== 'object') return payload;

  const label = payload.translation ?? payload.result;
  const signImageUrl = getSignImagePath(label);

  return {
    ...payload,
    signImageUrl,
    referenceSign: signImageUrl
      ? {
          letter: normalizeLetter(label),
          imageUrl: signImageUrl,
        }
      : null,
  };
}

module.exports = {
  getSignImagePath,
  attachSignReference,
};
