require('./config');

const { createApp } = require('./app');
const config = require('./config');
const { prisma } = require('./lib/prisma');

const app = createApp();

const server = app.listen(config.port, '0.0.0.0', () => {
  const port = config.port;
  const base = `http://localhost:${port}`;
  console.log('\n========== REST API ==========');
  console.log(`Listening on ${base} (bound to 0.0.0.0 for emulators / LAN)`);
  console.log('\n--- Localhost URLs ---');
  console.log(`${base}/health`);
  console.log(`${base}/`);
  console.log(`${base}/api`);
  console.log(`${base}/api/auth/register`);
  console.log(`${base}/api/auth/login`);
  console.log(`${base}/api/auth/forgot-password`);
  console.log(`${base}/api/auth/verify-code`);
  console.log(`${base}/api/auth/reset-password`);
  console.log(`${base}/api/users/me`);
  console.log(`${base}/api/users/me (PATCH)`);
  console.log(`${base}/api/products`);
  console.log(`${base}/api/products/:id`);
  console.log(`${base}/api/products (POST, auth)`);
  console.log(`${base}/api/products/:id (PATCH, DELETE, auth)`);
  console.log(`${base}/api/contact/submit`);
  console.log(`${base}/api/translation/upload (POST, multipart, auth)`);
  console.log(`${base}/uploads/<file>`);
  console.log('================================\n');
  console.log('Flutter: use this base URL in Dio/http — Android emulator: http://10.0.2.2:' + port);
  console.log('Flutter web: use http://localhost:' + port + ' (CORS allows localhost in development)\n');
});

async function shutdown() {
  await prisma.$disconnect();
  server.close(() => process.exit(0));
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
