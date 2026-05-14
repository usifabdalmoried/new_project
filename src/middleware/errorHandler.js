const multer = require('multer');
const { AppError } = require('../utils/AppError');
const { fail } = require('../utils/response');
const config = require('../config');

function errorHandler(err, req, res, _next) {
  if (err instanceof multer.MulterError) {
    return fail(res, err.message, 400);
  }
  if (err.message === 'Only images are allowed!') {
    return fail(res, 'Only image uploads are allowed', 400);
  }

  if (err instanceof AppError) {
    return fail(res, err.message, err.statusCode, err.errors);
  }

  if (err.name === 'PrismaClientKnownRequestError') {
    if (err.code === 'P2002') {
      return fail(res, 'A record with this value already exists', 409);
    }
    if (err.code === 'P2025') {
      return fail(res, 'Record not found', 404);
    }
  }

  console.error(err);
  const message = config.isProduction ? 'Internal server error' : err.message || 'Internal server error';
  return fail(res, message, 500);
}

module.exports = { errorHandler };
