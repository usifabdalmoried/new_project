const productService = require('../services/product.service');
const { ok } = require('../utils/response');
const { asyncHandler } = require('../utils/asyncHandler');

const list = asyncHandler(async (req, res) => {
  const page = Math.max(1, parseInt(String(req.query.page ?? '1'), 10) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(String(req.query.limit ?? '20'), 10) || 20));
  const result = await productService.listProducts({ page, limit });
  return ok(res, result);
});

const getById = asyncHandler(async (req, res) => {
  const product = await productService.getProductById(req.params.id);
  return ok(res, { product });
});

const create = asyncHandler(async (req, res) => {
  const { name, description, price, stock } = req.body;
  const product = await productService.createProduct({
    name,
    description,
    price,
    stock,
  });
  return ok(res, { product }, 'Product created', 201);
});

const update = asyncHandler(async (req, res) => {
  const { name, description, price, stock } = req.body;
  const product = await productService.updateProduct(req.params.id, {
    name,
    description,
    price,
    stock,
  });
  return ok(res, { product }, 'Product updated');
});

const remove = asyncHandler(async (req, res) => {
  await productService.deleteProduct(req.params.id);
  return ok(res, { deleted: true }, 'Product deleted');
});

module.exports = { list, getById, create, update, remove };
