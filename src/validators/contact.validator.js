const { body } = require('express-validator');

const submitContactRules = [
  body('name').trim().notEmpty().isLength({ max: 100 }),
  body('email').trim().isEmail().isLength({ max: 150 }),
  body('message').trim().notEmpty().isLength({ max: 10000 }),
];

module.exports = { submitContactRules };
