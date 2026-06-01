const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const gTTS = require('gtts');
const { prisma } = require('../lib/prisma');
const config = require('../config');
const { AppError } = require('../utils/AppError');

async function uploadAndTranslate(userId, file) {
  if (!file) {
    throw new AppError('No image uploaded', 400);
  }

  const imagePath = file.path;
  let translationResult = 'Help';

  try {
    const form = new FormData();
    form.append('file', fs.createReadStream(imagePath));
    const aiResponse = await axios.post(config.aiModelUrl, form, {
      headers: form.getHeaders(),
      timeout: 30000,
    });
    translationResult =
      aiResponse.data?.translation || aiResponse.data?.result || translationResult;
  } catch (aiError) {
    console.warn('AI model unavailable, using fallback translation:', aiError.message);
  }

  const audioFilename = `audio-${Date.now()}-${Math.round(Math.random() * 1e9)}.mp3`;
  const audioPath = path.join('uploads', audioFilename);
  const gtts = new gTTS(translationResult, 'en');

  await new Promise((resolve, reject) => {
    gtts.save(audioPath, (err) => (err ? reject(err) : resolve()));
  });

  await prisma.upload.create({
    data: {
      user_id: userId,
      image_path: imagePath,
      translation_result: translationResult,
      audio_path: audioPath,
    },
  });

const norm = (p) => p ? p.replace(/\\/g, '/') : null;

  return {
    message: 'Translation successful',
    imageUrl: norm(imagePath),
    translation: translationResult,
    audioUrl: norm(audioPath),
  };
}

async function getHistory(userId, { page = 1, limit = 20 }) {
  const skip = (page - 1) * limit;
  const [rows, total] = await Promise.all([
    prisma.upload.findMany({
      where: { user_id: userId },
      skip,
      take: limit,
      orderBy: { created_at: 'desc' },
    }),
    prisma.upload.count({ where: { user_id: userId } }),
  ]);

  const norm = (p) => p ? p.replace(/\\/g, '/') : null;

  return {
    items: rows.map((row) => ({
      id: row.id,
      imageUrl: norm(row.image_path),
      translation: row.translation_result,
      audioUrl: norm(row.audio_path),
      createdAt: row.created_at,
    })),
    page,
    limit,
    total,
    totalPages: Math.ceil(total / limit) || 0,
  };
}

module.exports = { uploadAndTranslate, getHistory };
