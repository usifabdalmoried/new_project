const authService = require('../services/auth.service');
const { ok } = require('../utils/response');
const { asyncHandler } = require('../utils/asyncHandler');

const register = asyncHandler(async (req, res) => {
  const { name, email, password } = req.body;
  const result = await authService.register({ name, email, password });
  return ok(res, { message: result.message }, null, 201);
});

const login = asyncHandler(async (req, res) => {
  const { name, email, password } = req.body;
  const result = await authService.login({ name, email, password });
  return ok(res, {
    message: result.message,
    token: result.token,
    user: result.user,
  });
});

const forgotPassword = asyncHandler(async (req, res) => {
  const result = await authService.forgotPassword(req.body);
  return ok(res, result);
});

const verifyCode = asyncHandler(async (req, res) => {
  const result = await authService.verifyCode(req.body);
  return ok(res, result);
});

const resetPassword = asyncHandler(async (req, res) => {
  const result = await authService.resetPassword(req.body);
  return ok(res, result);
});

module.exports = {
  register,
  login,
  forgotPassword,
  verifyCode,
  resetPassword,
};
