const express = require('express');
const router = express.Router();
const productController = require('../controllers/product.controller');
const { protect } = require('../middleware/auth');
const { validateRequest } = require('../middleware/validateRequest');
const {
  listProductsRules,
  idParamRules,
  createProductRules,
  updateProductRules,
} = require('../validators/product.validator');

router.get('/', listProductsRules, validateRequest, productController.list);
router.get('/:id', idParamRules, validateRequest, productController.getById);
router.post('/', protect, createProductRules, validateRequest, productController.create);
router.patch('/:id', protect, updateProductRules, validateRequest, productController.update);
router.delete('/:id', protect, idParamRules, validateRequest, productController.remove);

module.exports = router;
