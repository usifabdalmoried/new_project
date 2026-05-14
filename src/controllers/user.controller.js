const userService = require('../services/user.service');
const { ok } = require('../utils/response');
const { asyncHandler } = require('../utils/asyncHandler');

const getMe = asyncHandler(async (req, res) => {
  const user = await userService.getProfile(req.user.id);
  return ok(res, { user });
});

const updateMe = asyncHandler(async (req, res) => {
  const { name, email } = req.body;
  const user = await userService.updateProfile(req.user.id, { name, email });
  return ok(res, { user }, 'Profile updated');
});

module.exports = { getMe, updateMe };
