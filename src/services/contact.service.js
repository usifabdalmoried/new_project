const { prisma } = require('../lib/prisma');

async function submitContact({ name, email, message }) {
  await prisma.contactMessage.create({
    data: { name, email, message },
  });
  return { message: 'Message submitted successfully' };
}

module.exports = { submitContact };
