require('./config');

const { createApp } = require('./app');
const config = require('./config');
const { prisma } = require('./lib/prisma');

const app = createApp();

// Auto-create tables if they don't exist (PostgreSQL)
async function initDB() {
  try {
    await prisma.$executeRawUnsafe(`
      CREATE TABLE IF NOT EXISTS "users" (
        "id" SERIAL PRIMARY KEY,
        "name" VARCHAR(100) NOT NULL UNIQUE,
        "email" VARCHAR(150) NOT NULL UNIQUE,
        "password" VARCHAR(255) NOT NULL,
        "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
    await prisma.$executeRawUnsafe(`
      CREATE TABLE IF NOT EXISTS "uploads" (
        "id" SERIAL PRIMARY KEY,
        "user_id" INTEGER NOT NULL,
        "image_path" TEXT NOT NULL,
        "translation_result" TEXT,
        "audio_path" TEXT,
        "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT "uploads_user_id_fkey" FOREIGN KEY ("user_id")
          REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE
      )
    `);
    await prisma.$executeRawUnsafe(`
      CREATE TABLE IF NOT EXISTS "contact_messages" (
        "id" SERIAL PRIMARY KEY,
        "name" VARCHAR(100) NOT NULL,
        "email" VARCHAR(150) NOT NULL,
        "message" TEXT NOT NULL,
        "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
    await prisma.$executeRawUnsafe(`
      CREATE TABLE IF NOT EXISTS "products" (
        "id" SERIAL PRIMARY KEY,
        "name" VARCHAR(200) NOT NULL,
        "description" TEXT,
        "price" DECIMAL(12,2) NOT NULL,
        "stock" INTEGER NOT NULL DEFAULT 0,
        "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log('[DB] Tables ready.');
  } catch (err) {
    console.error('[DB] Init error:', err.message);
  }
}

async function start() {
  await initDB();

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
}

start();
