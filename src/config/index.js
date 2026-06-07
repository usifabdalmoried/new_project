require('dotenv').config();

const isProduction = process.env.NODE_ENV === 'production' || !!process.env.RAILWAY_STATIC_URL || !!process.env.RAILWAY_ENVIRONMENT;

if (isProduction && !process.env.JWT_SECRET) {
  console.error('[CONFIG] WARNING: JWT_SECRET is not set in production! Using fallback (INSECURE).');
}

const defaultAiUrl = 'http://127.0.0.1:5000/predict';
const aiModelUrl = process.env.AI_MODEL_URL || defaultAiUrl;

if (isProduction && !process.env.AI_MODEL_URL) {
  console.error('[CONFIG] Production requires AI_MODEL_URL. Set it to the deployed Flask AI service URL and restart the app.');
  process.exit(1);
}

console.log('[CONFIG] AI model URL:', aiModelUrl);

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  isProduction,
  jwtSecret: process.env.JWT_SECRET || 'dev-only-change-me',
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '30d',
  bcryptSaltRounds: parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10),
  corsOriginRaw: process.env.CORS_ORIGIN || '',
  aiModelUrl,
};
