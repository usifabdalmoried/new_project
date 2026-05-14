const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
const { protect } = require('../middleware/auth');
const { validateRequest } = require('../middleware/validateRequest');
const { updateProfileRules } = require('../validators/user.validator');

router.get('/me', protect, userController.getMe);
router.patch('/me', protect, updateProfileRules, validateRequest, userController.updateMe);

module.exports = router;
