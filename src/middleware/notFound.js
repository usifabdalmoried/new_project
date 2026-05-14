const { fail } = require('../utils/response');

function notFound(req, res, next) {
  return fail(res, `Route not found: ${req.method} ${req.originalUrl}`, 404);
}

module.exports = { notFound };
