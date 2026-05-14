const express = require('express');

const router = express.Router();

router.get('/', (req, res) => {
  const base = `${req.protocol}://${req.get('host')}`;
  res.json({
    success: true,
    data: {
      message:
        'Route index: use the URLs below from your Flutter app (same machine: use 10.0.2.2 on Android emulator instead of localhost).',
      baseUrl: `${base}/api`,
      endpoints: {
        health: { method: 'GET', url: `${base}/health` },
        auth: {
          register: { method: 'POST', url: `${base}/api/auth/register` },
          login: { method: 'POST', url: `${base}/api/auth/login` },
          forgotPassword: { method: 'POST', url: `${base}/api/auth/forgot-password` },
          verifyCode: { method: 'POST', url: `${base}/api/auth/verify-code` },
          resetPassword: { method: 'POST', url: `${base}/api/auth/reset-password` },
        },
        users: {
          me: { method: 'GET', url: `${base}/api/users/me`, headers: { Authorization: 'Bearer <token>' } },
          updateMe: { method: 'PATCH', url: `${base}/api/users/me`, headers: { Authorization: 'Bearer <token>' } },
        },
        products: {
          list: { method: 'GET', url: `${base}/api/products?page=1&limit=20` },
          byId: { method: 'GET', url: `${base}/api/products/:id` },
          create: { method: 'POST', url: `${base}/api/products`, headers: { Authorization: 'Bearer <token>' } },
          update: { method: 'PATCH', url: `${base}/api/products/:id`, headers: { Authorization: 'Bearer <token>' } },
          delete: { method: 'DELETE', url: `${base}/api/products/:id`, headers: { Authorization: 'Bearer <token>' } },
        },
        contact: {
          submit: { method: 'POST', url: `${base}/api/contact/submit` },
        },
        translation: {
          upload: {
            method: 'POST',
            url: `${base}/api/translation/upload`,
            headers: { Authorization: 'Bearer <token>' },
            body: 'multipart/form-data field name: image',
          },
        },
        staticUploads: { method: 'GET', url: `${base}/uploads/<filename>` },
      },
    },
  });
});

router.use('/auth', require('./auth.routes'));
router.use('/users', require('./user.routes'));
router.use('/products', require('./product.routes'));
router.use('/contact', require('./contact.routes'));
router.use('/translation', require('./translation.routes'));

module.exports = router;
