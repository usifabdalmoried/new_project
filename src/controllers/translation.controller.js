const translationService = require('../services/translation.service');
const { ok } = require('../utils/response');
const { asyncHandler } = require('../utils/asyncHandler');

const upload = asyncHandler(async (req, res) => {
  const result = await translationService.uploadAndTranslate(req.user.id, req.file);
  return ok(res, result);
});

module.exports = { upload };
