const express = require('express');
const router = express.Router();
const contactController = require('../controllers/contact.controller');
const { validateRequest } = require('../middleware/validateRequest');
const { submitContactRules } = require('../validators/contact.validator');

router.post('/submit', submitContactRules, validateRequest, contactController.submit);

module.exports = router;
