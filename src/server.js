// Global crash handlers — must be registered FIRST
process.on('uncaughtException', (err) => {
  console.error('[FATAL] Uncaught exception:', err);
});
process.on('unhandledRejection', (reason) => {
  console.error('[FATAL] Unhandled rejection:', reason);
});

require('./config');

const { createApp } = require('./app');
const config = require('./config');
const { prisma } = require('./lib/prisma');

const app = createApp();

// Create tables if they don't exist (runs in background after server starts)
async function initDB() {
  try {
    // First test the connection
    await prisma.$queryRaw`SELECT 1`;
    console.log('[DB] Connected successfully.');

    await prisma.$executeRawUnsafe(`CREATE TABLE IF NOT EXISTS "users" ("id" SERIAL PRIMARY KEY,"name" VARCHAR(100) NOT NULL UNIQUE,"email" VARCHAR(150) NOT NULL UNIQUE,"password" VARCHAR(255) NOT NULL,"created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP)`);
    await prisma.$executeRawUnsafe(`CREATE TABLE IF NOT EXISTS "uploads" ("id" SERIAL PRIMARY KEY,"user_id" INTEGER NOT NULL,"image_path" TEXT NOT NULL,"translation_result" TEXT,"audio_path" TEXT,"created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,CONSTRAINT "uploads_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE)`);
    await prisma.$executeRawUnsafe(`CREATE TABLE IF NOT EXISTS "contact_messages" ("id" SERIAL PRIMARY KEY,"name" VARCHAR(100) NOT NULL,"email" VARCHAR(150) NOT NULL,"message" TEXT NOT NULL,"created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP)`);
    await prisma.$executeRawUnsafe(`CREATE TABLE IF NOT EXISTS "products" ("id" SERIAL PRIMARY KEY,"name" VARCHAR(200) NOT NULL,"description" TEXT,"price" DECIMAL(12,2) NOT NULL,"stock" INTEGER NOT NULL DEFAULT 0,"created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,"updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP)`);
    console.log('[DB] Tables ready.');
  } catch (err) {
    console.error('[DB] Init error:', err.message);
    // Don't crash the server — let it continue serving non-DB routes
  }
}

try {
  const server = app.listen(config.port, '0.0.0.0', () => {
    const port = config.port;
    console.log(`\n[Server] Running on port ${port}`);
    console.log(`[Server] Health: http://localhost:${port}/health`);
    console.log(`[Server] NODE_ENV: ${config.nodeEnv}`);
    console.log(`[Server] DATABASE_URL set: ${!!process.env.DATABASE_URL}`);
    // Init DB after server is listening (non-blocking)
    initDB();
  });

  async function shutdown() {
    await prisma.$disconnect();
    server.close(() => process.exit(0));
  }

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
} catch (err) {
  console.error('[FATAL] Failed to start server:', err);
  process.exit(1);
}
