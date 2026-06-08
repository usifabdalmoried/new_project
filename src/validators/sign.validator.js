const { body, param } = require('express-validator');

const VALID_LETTER = /^[0-9A-Z]$/;

function normalizeLetter(value) {
  return String(value).trim().toUpperCase();
}

const letterParamRules = [
  param('letter')
    .trim()
    .customSanitizer(normalizeLetter)
    .matches(VALID_LETTER)
    .withMessage('Letter must be a single digit (0-9) or uppercase letter (A-Z)'),
];

const upsertSignRules = [
  body('letter')
    .trim()
    .customSanitizer(normalizeLetter)
    .matches(VALID_LETTER)
    .withMessage('Letter must be a single digit (0-9) or uppercase letter (A-Z)'),
  body('description').optional().trim().isLength({ max: 500 }),
];

module.exports = {
  letterParamRules,
  upsertSignRules,
};
