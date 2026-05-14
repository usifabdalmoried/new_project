const contactService = require('../services/contact.service');
const { ok } = require('../utils/response');
const { asyncHandler } = require('../utils/asyncHandler');

const submit = asyncHandler(async (req, res) => {
  const result = await contactService.submitContact(req.body);
  return ok(res, result, null, 201);
});

module.exports = { submit };
