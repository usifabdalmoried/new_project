const express = require('express');
const path = require('path');
const fs = require('fs');
const helmet = require('helmet');
const compression = require('compression');
const { buildCors } = require('./config/cors');
const { apiLimiter } = require('./middleware/rateLimiter');

function createApp() {
  const app = express();

  const uploadsDir = path.join(process.cwd(), 'uploads');
  if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
  }

  app.disable('x-powered-by');
  app.use(helmet({ crossOriginResourcePolicy: { policy: 'cross-origin' } }));
  app.use(compression());
  app.use(buildCors());
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: false }));

  app.use('/uploads', express.static(uploadsDir));

  app.use(apiLimiter);

  app.get('/health', (_req, res) => {
    res.status(200).json({ success: true, data: { status: 'ok', timestamp: new Date().toISOString() } });
  });

  app.get('/', (_req, res) => {
    res.json({
      success: true,
      data: {
        name: 'REST API',
        version: '1.0.0',
        apiIndex: '/api',
      },
    });
  });

  app.use('/api', require('./routes'));

  const { notFound } = require('./middleware/notFound');
  app.use(notFound);

  const { errorHandler } = require('./middleware/errorHandler');
  app.use(errorHandler);

  return app;
}

module.exports = { createApp };
