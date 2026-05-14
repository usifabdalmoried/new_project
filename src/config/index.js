require('dotenv').config();

const isProduction = process.env.NODE_ENV === 'production';

if (isProduction && !process.env.JWT_SECRET) {
  console.error('[CONFIG] WARNING: JWT_SECRET is not set in production! Using fallback (INSECURE).');
}

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  isProduction,
  jwtSecret: process.env.JWT_SECRET || 'dev-only-change-me',
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '30d',
  bcryptSaltRounds: parseInt(process.env.BCRYPT_SALT_ROUNDS || '10', 10),
  corsOriginRaw: process.env.CORS_ORIGIN || '',
  aiModelUrl: process.env.AI_MODEL_URL || 'http://127.0.0.1:5000/predict',
};
