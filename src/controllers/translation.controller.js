const translationService = require('../services/translation.service');
const { ok } = require('../utils/response');
const { asyncHandler } = require('../utils/asyncHandler');

const upload = asyncHandler(async (req, res) => {
  const result = await translationService.uploadAndTranslate(req.user.id, req.file);
  return ok(res, result);
});

const getHistory = asyncHandler(async (req, res) => {
  const page = Math.max(1, parseInt(String(req.query.page ?? '1'), 10) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(String(req.query.limit ?? '20'), 10) || 20));
  const result = await translationService.getHistory(req.user.id, { page, limit });
  return ok(res, result);
});

module.exports = { upload, getHistory };
