const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { prisma } = require('../lib/prisma');
const config = require('../config');
const { AppError } = require('../utils/AppError');

const verificationCodes = new Map();

function signToken(user) {
  return jwt.sign(
    { id: user.id, name: user.name, email: user.email },
    config.jwtSecret,
    { expiresIn: config.jwtExpiresIn }
  );
}

async function register({ name, email, password }) {
  const existing = await prisma.user.findFirst({
    where: { OR: [{ name }, { email }] },
  });
  if (existing) {
    throw new AppError('User with this name or email already exists', 409);
  }

  const hashedPassword = await bcrypt.hash(password, config.bcryptSaltRounds);

  await prisma.user.create({
    data: { name, email, password: hashedPassword },
  });

  return { message: 'User registered successfully' };
}

async function login({ name, email, password }) {
  const user = await prisma.user.findFirst({
    where: email ? { email } : { name },
  });

  if (!user) {
    throw new AppError('Invalid credentials', 401);
  }

  const isMatch = await bcrypt.compare(password, user.password);
  if (!isMatch) {
    throw new AppError('Invalid credentials', 401);
  }

  const token = signToken(user);

  return {
    message: 'Login successful',
    token,
    user: {
      id: user.id,
      name: user.name,
      email: user.email,
    },
  };
}

async function forgotPassword({ email }) {
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) {
    throw new AppError('User not found', 404);
  }

  const code = Math.floor(100000 + Math.random() * 900000).toString();
  verificationCodes.set(email, {
    code,
    expiresAt: Date.now() + 15 * 60 * 1000,
  });

  console.log(`[DEV] Password reset code for ${email}: ${code}`);

  return { message: 'Verification code sent (check server logs in development)' };
}

async function verifyCode({ email, code }) {
  const stored = verificationCodes.get(email);
  if (!stored) {
    throw new AppError('No verification code requested or it expired', 400);
  }
  if (Date.now() > stored.expiresAt) {
    verificationCodes.delete(email);
    throw new AppError('Verification code expired', 400);
  }
  if (stored.code !== code) {
    throw new AppError('Invalid verification code', 400);
  }

  return { message: 'Code verified. You may now reset your password.' };
}

async function resetPassword({ email, code, newPassword }) {
  const stored = verificationCodes.get(email);
  if (!stored || stored.code !== code) {
    throw new AppError('Invalid or expired verification process', 400);
  }

  const hashedPassword = await bcrypt.hash(newPassword, config.bcryptSaltRounds);

  await prisma.user.update({
    where: { email },
    data: { password: hashedPassword },
  });

  verificationCodes.delete(email);

  return { message: 'Password reset successful' };
}

module.exports = {
  register,
  login,
  forgotPassword,
  verifyCode,
  resetPassword,
};
