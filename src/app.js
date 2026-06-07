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
  app.use(helmet({ 
    crossOriginResourcePolicy: { policy: 'cross-origin' },
    contentSecurityPolicy: false
  }));
  app.use(compression());
  app.use(buildCors());
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: false }));

  app.use(express.static(path.join(process.cwd(), 'public')));
  app.use('/uploads', express.static(uploadsDir));

  app.use(apiLimiter);

  app.get('/health', (_req, res) => {
    res.status(200).json({ success: true, data: { status: 'ok', timestamp: new Date().toISOString() } });
  });



  const { upload } = require('./config/upload');
  const axios = require('axios');
  const FormData = require('form-data');
  const config = require('./config');

  app.post('/predict', upload.single('file'), async (req, res) => {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded. Use key "file".' });
    }

    try {
      const form = new FormData();
      form.append('file', fs.createReadStream(req.file.path));

      const aiResponse = await axios.post(config.aiModelUrl, form, {
        headers: form.getHeaders(),
        timeout: 30000,
      });

      // Async cleanup local temp file
      fs.unlink(req.file.path, () => { });

      return res.status(200).json(aiResponse.data);
    } catch (aiError) {
      if (req.file) {
        fs.unlink(req.file.path, () => { });
      }
      console.error('[AI Proxy Error]:', aiError.message, 'AI URL:', config.aiModelUrl);

      if (aiError.response) {
        if (aiError.response.status === 400) {
          return res.status(400).json(aiError.response.data);
        }

        return res.status(502).json({
          error: `AI Service returned ${aiError.response.status}`,
          details: aiError.response.data || aiError.response.statusText || aiError.message,
          aiModelUrl: config.aiModelUrl,
        });
      }

      return res.status(502).json({
        error: `AI Service unavailable at ${config.aiModelUrl}`,
        details: aiError.message,
        aiModelUrl: config.aiModelUrl,
      });
    }
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
