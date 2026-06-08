const multer = require('multer');
const { AppError } = require('../utils/AppError');
const { fail } = require('../utils/response');

// Express 5 detects error middleware by fn.length === 4
// All 4 parameters MUST be named (not prefixed with _)
function errorHandler(err, req, res, next) {
  // If headers already sent, delegate to Express default handler
  if (res.headersSent) {
    return next(err);
  }

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

  if (
    err.name === 'PrismaClientInitializationError' ||
    (err.message && err.message.includes('Authentication failed against database server'))
  ) {
    console.error('[DB] Connection/auth error:', err.message);
    return fail(
      res,
      'Database connection failed. Check DATABASE_URL on Railway (PostgreSQL service variables).',
      503
    );
  }

  console.error('[ERROR]', err.name, err.message, err.stack);
  const message = err.message || 'Internal server error';
  return fail(res, message, 500);
}

module.exports = { errorHandler };

