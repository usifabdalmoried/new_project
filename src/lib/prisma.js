require('dotenv').config();

const { PrismaClient } = require('@prisma/client');

const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
  console.error('[Prisma] WARNING: DATABASE_URL is not set!');
}

const globalForPrisma = globalThis;

const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['error', 'warn'] : ['error'],
    datasources: dbUrl ? { db: { url: dbUrl } } : undefined,
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

module.exports = { prisma };
