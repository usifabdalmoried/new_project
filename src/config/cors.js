const cors = require('cors');
const config = require('./index');

function buildCors() {
  const allowedExact = config.corsOriginRaw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  return cors({
    origin(origin, callback) {
      if (!origin) {
        return callback(null, true);
      }
      if (allowedExact.includes(origin)) {
        return callback(null, true);
      }
      if (!config.isProduction && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(origin)) {
        return callback(null, true);
      }
      return callback(null, false);
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
  });
}

module.exports = { buildCors };
