const { prisma } = require('../lib/prisma');
const { AppError } = require('../utils/AppError');

async function getProfile(userId) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { id: true, name: true, email: true, created_at: true },
  });
  if (!user) {
    throw new AppError('User not found', 404);
  }
  return user;
}

async function updateProfile(userId, { name, email }) {
  const data = {};
  if (name !== undefined) data.name = name;
  if (email !== undefined) data.email = email;

  try {
    const user = await prisma.user.update({
      where: { id: userId },
      data,
      select: { id: true, name: true, email: true, created_at: true },
    });
    return user;
  } catch (e) {
    if (e && e.code === 'P2002') {
      throw new AppError('Name or email already in use', 409);
    }
    throw e;
  }
}

module.exports = { getProfile, updateProfile };
