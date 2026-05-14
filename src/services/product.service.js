const { prisma } = require('../lib/prisma');
const { AppError } = require('../utils/AppError');

function serializeProduct(row) {
  if (!row) return null;
  return {
    id: row.id,
    name: row.name,
    description: row.description,
    price: row.price != null ? String(row.price) : null,
    stock: row.stock,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

async function listProducts({ page = 1, limit = 20 }) {
  const skip = (page - 1) * limit;
  const [rows, total] = await Promise.all([
    prisma.product.findMany({
      skip,
      take: limit,
      orderBy: { created_at: 'desc' },
    }),
    prisma.product.count(),
  ]);

  return {
    items: rows.map(serializeProduct),
    page,
    limit,
    total,
    totalPages: Math.ceil(total / limit) || 0,
  };
}

async function getProductById(id) {
  const numId = parseInt(String(id), 10);
  if (isNaN(numId)) throw new AppError('Invalid product ID', 400);
  const row = await prisma.product.findUnique({ where: { id: numId } });
  if (!row) {
    throw new AppError('Product not found', 404);
  }
  return serializeProduct(row);
}

async function createProduct({ name, description, price, stock = 0 }) {
  const row = await prisma.product.create({
    data: {
      name,
      description: description ?? null,
      price,
      stock: stock ?? 0,
    },
  });
  return serializeProduct(row);
}

async function updateProduct(id, { name, description, price, stock }) {
  const numId = parseInt(String(id), 10);
  if (isNaN(numId)) throw new AppError('Invalid product ID', 400);
  const data = {};
  if (name !== undefined) data.name = name;
  if (description !== undefined) data.description = description;
  if (price !== undefined) data.price = price;
  if (stock !== undefined) data.stock = stock;

  try {
    const row = await prisma.product.update({
      where: { id: numId },
      data,
    });
    return serializeProduct(row);
  } catch (e) {
    if (e.code === 'P2025') {
      throw new AppError('Product not found', 404);
    }
    throw e;
  }
}

async function deleteProduct(id) {
  const numId = parseInt(String(id), 10);
  if (isNaN(numId)) throw new AppError('Invalid product ID', 400);
  try {
    await prisma.product.delete({ where: { id: numId } });
  } catch (e) {
    if (e.code === 'P2025') {
      throw new AppError('Product not found', 404);
    }
    throw e;
  }
}

module.exports = {
  listProducts,
  getProductById,
  createProduct,
  updateProduct,
  deleteProduct,
};
