/* ==========================================================================
   Signify AI - Frontend Application Logic
   ========================================================================== */

const API_BASE = '/api';
let AUTH_TOKEN = localStorage.getItem('token') || '';
let CURRENT_USER = null;
let SELECTED_FILE = null;
let CURRENT_PAGE = 1;
const LIMIT = 5;

// DOM Elements
const authSection = document.getElementById('auth-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const tabLogin = document.getElementById('tab-login');
const tabRegister = document.getElementById('tab-register');
const authMessage = document.getElementById('auth-message');

const userProfileHeader = document.getElementById('user-profile-header');
const headerUsername = document.getElementById('header-username');
const avatarChar = document.getElementById('avatar-char');
const logoutBtn = document.getElementById('logout-btn');
const systemStatus = document.getElementById('system-status');

const dropZone = document.getElementById('drop-zone');
const imageFileInput = document.getElementById('image-file-input');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');
const clearImageBtn = document.getElementById('clear-image-btn');
const translateBtn = document.getElementById('translate-btn');

const resultCard = document.getElementById('result-card');
const resultText = document.getElementById('result-text');
const resultConfidence = document.getElementById('result-confidence');
const playAudioBtn = document.getElementById('play-audio-btn');
const globalAudioPlayer = document.getElementById('global-audio-player');

const historyListContainer = document.getElementById('history-list-container');
const historyPlaceholder = document.getElementById('history-placeholder');
const historyCount = document.getElementById('history-count');
const paginationControls = document.getElementById('pagination-controls');
const pageIndicator = document.getElementById('page-indicator');
const prevPageBtn = document.getElementById('prev-page-btn');
const nextPageBtn = document.getElementById('next-page-btn');

// Initial setup
document.addEventListener('DOMContentLoaded', () => {
  checkAPIHealth();
  if (AUTH_TOKEN) {
    fetchProfileAndInit();
  } else {
    showAuth();
  }
  setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
  // Tabs switching
  tabLogin.addEventListener('click', () => switchTab('login'));
  tabRegister.addEventListener('click', () => switchTab('register'));

  // Auth Forms
  loginForm.addEventListener('submit', handleLogin);
  registerForm.addEventListener('submit', handleRegister);
  logoutBtn.addEventListener('click', handleLogout);

  // File Upload Dropzone triggers
  dropZone.addEventListener('click', () => imageFileInput.click());
  imageFileInput.addEventListener('change', handleFileSelect);

  // Drag & drop logic
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
      imageFileInput.files = files;
      handleFileSelect();
    }
  });

  // Clear preview
  clearImageBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // prevent opening file selector
    clearPreview();
  });

  // Action Buttons
  translateBtn.addEventListener('click', performTranslation);
  playAudioBtn.addEventListener('click', playAudio);

  // Pagination buttons
  prevPageBtn.addEventListener('click', () => {
    if (CURRENT_PAGE > 1) {
      CURRENT_PAGE--;
      loadHistory();
    }
  });
  nextPageBtn.addEventListener('click', () => {
    CURRENT_PAGE++;
    loadHistory();
  });
}

// Check backend server health
async function checkAPIHealth() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    if (data.success || data.status === 'ok') {
      systemStatus.className = 'status-indicator online';
      systemStatus.querySelector('.status-text').textContent = 'API Connected';
    } else {
      throw new Error('Offline');
    }
  } catch {
    systemStatus.className = 'status-indicator offline';
    systemStatus.querySelector('.status-text').textContent = 'API Offline';
  }
}

// Switch between Login and Register tabs
function switchTab(tab) {
  hideMessage();
  if (tab === 'login') {
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
  } else {
    tabLogin.classList.remove('active');
    tabRegister.classList.add('active');
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
  }
}

// Handle login submission
async function handleLogin(e) {
  e.preventDefault();
  hideMessage();

  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Login failed');

    showMessage('Login successful! Loading dashboard...', 'success');
    AUTH_TOKEN = data.data.token;
    localStorage.setItem('token', AUTH_TOKEN);

    setTimeout(() => {
      fetchProfileAndInit();
    }, 1000);

  } catch (err) {
    showMessage(err.message, 'error');
  }
}

// Handle registration submission
async function handleRegister(e) {
  e.preventDefault();
  hideMessage();

  const name = document.getElementById('register-name').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;
  const confirmPassword = document.getElementById('register-confirm').value;

  if (password !== confirmPassword) {
    return showMessage('Passwords do not match', 'error');
  }

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, confirmPassword })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Registration failed');

    showMessage('Registration successful! Logging in...', 'success');
    
    // Automatically log user in
    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const loginData = await loginRes.json();
    AUTH_TOKEN = loginData.data.token;
    localStorage.setItem('token', AUTH_TOKEN);

    setTimeout(() => {
      fetchProfileAndInit();
    }, 1000);

  } catch (err) {
    showMessage(err.message, 'error');
  }
}

// Handle logout
function handleLogout() {
  AUTH_TOKEN = '';
  CURRENT_USER = null;
  localStorage.removeItem('token');
  showAuth();
  clearPreview();
  resultCard.classList.add('hidden');
}

// Check token validity and show dashboard
async function fetchProfileAndInit() {
  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
    });
    const data = await res.json();
    
    if (!res.ok) {
      handleLogout();
      return;
    }

    CURRENT_USER = data.data;
    initDashboard();
  } catch {
    handleLogout();
  }
}

// Render user dashboard info
function initDashboard() {
  authSection.classList.add('hidden');
  dashboardSection.classList.remove('hidden');
  userProfileHeader.classList.remove('hidden');

  headerUsername.textContent = CURRENT_USER.name;
  avatarChar.textContent = CURRENT_USER.name.charAt(0).toUpperCase();

  CURRENT_PAGE = 1;
  loadHistory();
}

// Show auth form
function showAuth() {
  authSection.classList.remove('hidden');
  dashboardSection.classList.add('hidden');
  userProfileHeader.classList.add('hidden');
}

// Display messages inside auth card
function showMessage(msg, type) {
  authMessage.textContent = msg;
  authMessage.className = `alert-box ${type}`;
}

function hideMessage() {
  authMessage.classList.add('hidden');
}

// Image File Selection handlers
function handleFileSelect() {
  const file = imageFileInput.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    alert('Please upload an image file');
    return;
  }

  SELECTED_FILE = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreview.src = e.target.result;
    previewContainer.classList.remove('hidden');
    translateBtn.disabled = false;
  };
  reader.readAsDataURL(file);
}

// Clear selected image preview
function clearPreview() {
  SELECTED_FILE = null;
  imageFileInput.value = '';
  imagePreview.src = '';
  previewContainer.classList.add('hidden');
  translateBtn.disabled = true;
}

// API Call: upload image to translate gesture
async function performTranslation() {
  if (!SELECTED_FILE) return;

  // Set visual loading state
  translateBtn.disabled = true;
  translateBtn.querySelector('span').textContent = 'Translating...';
  translateBtn.querySelector('i').setAttribute('data-lucide', 'loader-2');
  translateBtn.querySelector('i').classList.add('spin-animation');
  lucide.createIcons();

  const formData = new FormData();
  formData.append('image', SELECTED_FILE);

  try {
    const res = await fetch(`${API_BASE}/translation/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` },
      body: formData
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.message || data.error || 'Translation failed');

    // Display translation outputs
    resultText.textContent = data.data.translation;
    resultConfidence.textContent = 'Translation Match OK';
    
    // Setup audio path
    globalAudioPlayer.src = `/${data.data.audioUrl}`;
    
    resultCard.classList.remove('hidden');
    resultCard.scrollIntoView({ behavior: 'smooth' });

    // Reload history list
    CURRENT_PAGE = 1;
    loadHistory();

  } catch (err) {
    alert(`Translation Error: ${err.message}`);
  } finally {
    // Reset button design
    translateBtn.disabled = false;
    translateBtn.querySelector('span').textContent = 'Translate Image';
    translateBtn.querySelector('i').setAttribute('data-lucide', 'cpu');
    translateBtn.querySelector('i').classList.remove('spin-animation');
    lucide.createIcons();
  }
}

// Listen Translation audio playback
function playAudio() {
  if (globalAudioPlayer.src) {
    globalAudioPlayer.play().catch(err => {
      console.error('Audio play failed:', err);
    });
  }
}

// Fetch history list
async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/translation/history?page=${CURRENT_PAGE}&limit=${LIMIT}`, {
      headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Failed to load history');

    renderHistory(data.data);
  } catch (err) {
    console.error('History load error:', err);
  }
}

// Render history items in sidebar list
function renderHistory(historyData) {
  const items = historyData.items || [];
  historyCount.textContent = `${historyData.total} items`;

  if (items.length === 0) {
    historyListContainer.innerHTML = '';
    historyListContainer.appendChild(historyPlaceholder);
    paginationControls.classList.add('hidden');
    return;
  }

  // Generate list layout
  let html = '';
  items.forEach(item => {
    const dateStr = new Date(item.createdAt).toLocaleString();
    html += `
      <div class="history-item" data-id="${item.id}">
        <div class="item-left">
          <img class="item-thumb" src="/${item.imageUrl}" alt="Gesture preview" onerror="this.src='https://placehold.co/50x50?text=Sign'">
          <div class="item-info">
            <span class="item-translation">${item.translation}</span>
            <span class="item-date">${dateStr}</span>
          </div>
        </div>
        <div class="item-actions">
          <button class="icon-btn item-play-btn" onclick="playHistoryAudio('/${item.audioUrl}')" title="Play Speech">
            <i data-lucide="volume-2"></i>
          </button>
        </div>
      </div>
    `;
  });

  historyListContainer.innerHTML = html;
  lucide.createIcons();

  // Handle pagination visibility
  if (historyData.totalPages > 1) {
    pageIndicator.textContent = `Page ${CURRENT_PAGE} of ${historyData.totalPages}`;
    prevPageBtn.disabled = CURRENT_PAGE === 1;
    nextPageBtn.disabled = CURRENT_PAGE === historyData.totalPages;
    paginationControls.classList.remove('hidden');
  } else {
    paginationControls.classList.add('hidden');
  }
}

// Play speech audio from list item
window.playHistoryAudio = function(audioUrl) {
  const player = new Audio(audioUrl);
  player.play().catch(err => console.error('Audio play failed:', err));
};
