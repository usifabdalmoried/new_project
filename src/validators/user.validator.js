const { body } = require('express-validator');

const updateProfileRules = [
  body('name').optional().trim().notEmpty().isLength({ max: 100 }),
  body('email').optional().trim().isEmail().isLength({ max: 150 }),
  body().custom((_, { req }) => {
    if (!req.body.name && !req.body.email) {
      throw new Error('At least one of name or email must be provided');
    }
    return true;
  }),
];

module.exports = { updateProfileRules };
