const { body, param, query } = require('express-validator');

const listProductsRules = [
  query('page').optional().isInt({ min: 1 }).toInt(),
  query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
];

const idParamRules = [param('id').isInt({ min: 1 }).toInt().withMessage('Invalid product id')];

const createProductRules = [
  body('name').trim().notEmpty().isLength({ max: 200 }),
  body('description').optional().trim(),
  body('price').isFloat({ min: 0 }).withMessage('Price must be a non-negative number'),
  body('stock').optional().isInt({ min: 0 }).toInt(),
];

const updateProductRules = [
  ...idParamRules,
  body('name').optional().trim().notEmpty().isLength({ max: 200 }),
  body('description').optional().trim(),
  body('price').optional().isFloat({ min: 0 }),
  body('stock').optional().isInt({ min: 0 }).toInt(),
  body().custom((_, { req }) => {
    const { name, description, price, stock } = req.body;
    if (
      name === undefined &&
      description === undefined &&
      price === undefined &&
      stock === undefined
    ) {
      throw new Error('At least one field to update is required');
    }
    return true;
  }),
];

module.exports = {
  listProductsRules,
  idParamRules,
  createProductRules,
  updateProductRules,
};
