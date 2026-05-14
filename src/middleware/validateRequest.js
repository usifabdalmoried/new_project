const { validationResult } = require('express-validator');
const { fail } = require('../utils/response');

function validateRequest(req, res, next) {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return fail(res, 'Validation failed', 422, errors.array({ onlyFirstError: false }));
  }
  next();
}

module.exports = { validateRequest };
