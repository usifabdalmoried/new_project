const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth.controller');
const { validateRequest } = require('../middleware/validateRequest');
const { authLimiter } = require('../middleware/rateLimiter');
const {
  registerRules,
  loginRules,
  forgotPasswordRules,
  verifyCodeRules,
  resetPasswordRules,
} = require('../validators/auth.validator');

router.post('/register', authLimiter, registerRules, validateRequest, authController.register);
router.post('/login', authLimiter, loginRules, validateRequest, authController.login);
router.post(
  '/forgot-password',
  authLimiter,
  forgotPasswordRules,
  validateRequest,
  authController.forgotPassword
);
router.post('/verify-code', authLimiter, verifyCodeRules, validateRequest, authController.verifyCode);
router.post(
  '/reset-password',
  authLimiter,
  resetPasswordRules,
  validateRequest,
  authController.resetPassword
);

module.exports = router;
