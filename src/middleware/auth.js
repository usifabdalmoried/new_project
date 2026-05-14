const jwt = require('jsonwebtoken');
const config = require('../config');
const { fail } = require('../utils/response');

function protect(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return fail(res, 'Not authorized: missing bearer token', 401);
  }

  const token = auth.split(' ')[1];
  try {
    const decoded = jwt.verify(token, config.jwtSecret);
    req.user = { id: decoded.id, name: decoded.name, email: decoded.email };
    return next();
  } catch {
    return fail(res, 'Not authorized: invalid or expired token', 401);
  }
}

module.exports = { protect };
