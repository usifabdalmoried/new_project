const { body } = require('express-validator');

const registerRules = [
  body('name').trim().notEmpty().withMessage('Name is required').isLength({ max: 100 }),
  body('email').trim().isEmail().withMessage('Valid email is required').isLength({ max: 150 }),
  body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
  body('confirmPassword')
    .notEmpty()
    .withMessage('Confirm password is required')
    .custom((value, { req }) => {
      if (value !== req.body.password) {
        throw new Error('Passwords must match');
      }
      return true;
    }),
];

const loginRules = [
  body('password').notEmpty().withMessage('Password is required'),
  body('name').optional().trim().isLength({ max: 100 }),
  body('email').optional().trim().isEmail(),
  body().custom((_, { req }) => {
    if (!req.body.name && !req.body.email) {
      throw new Error('Either name or email is required');
    }
    return true;
  }),
];

const forgotPasswordRules = [body('email').trim().isEmail().withMessage('Valid email is required')];

const verifyCodeRules = [
  body('email').trim().isEmail(),
  body('code').trim().notEmpty().isLength({ min: 4, max: 12 }),
];

const resetPasswordRules = [
  body('email').trim().isEmail(),
  body('code').trim().notEmpty(),
  body('newPassword').isLength({ min: 8 }).withMessage('New password must be at least 8 characters'),
];

module.exports = {
  registerRules,
  loginRules,
  forgotPasswordRules,
  verifyCodeRules,
  resetPasswordRules,
};
