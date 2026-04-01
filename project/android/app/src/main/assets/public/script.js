// Load settings from localStorage
const savedSettings = JSON.parse(localStorage.getItem('gachaSettings') || '{}');

// API endpoint - try multiple addresses for compatibility
let API_URL;
if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
  // Web browser on same machine
  API_URL = 'http://localhost:5000/api';
} else {
  // Android app - use saved IP from settings or default
  const serverIp = savedSettings.serverIp || '172.16.0.18';
  const serverPort = savedSettings.serverPort || '5000';
  API_URL = `http://${serverIp}:${serverPort}/api`;
}

const USE_LOCAL_RANDOM = false; // ✅ Use backend (online mode)

// Generate local SVG placeholder
function createSVGPlaceholder(color, initials) {
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 400' preserveAspectRatio='xMidYMid meet'%3E%3Crect fill='${color}' width='300' height='400'/%3E%3Ctext x='150' y='210' font-size='60' fill='white' text-anchor='middle' dominant-baseline='middle' font-weight='bold'%3E${initials}%3C/text%3E%3C/svg%3E`;
}

// Sample character data - replace with backend data (FAST LOCAL PLACEHOLDERS)
const CHARACTERS = [
  {
    id: 1,
    name: 'Kafka',
    rarity: 5,
    image: createSVGPlaceholder('%23ff1493', 'K'),
    stats: { ATK: 327, DEF: 188, HP: 962 },
    description: 'A charming woman from the Antimatter Legion.',
  },
  {
    id: 2,
    name: 'Jingliu',
    rarity: 5,
    image: createSVGPlaceholder('%238b008b', 'J'),
    stats: { ATK: 340, DEF: 174, HP: 924 },
    description: 'A disciples of Jingliu, following the way of the sword.',
  },
  {
    id: 3,
    name: 'Blade',
    rarity: 5,
    image: createSVGPlaceholder('%23800000', 'B'),
    stats: { ATK: 368, DEF: 152, HP: 1010 },
    description: 'A member of the Stellaron Hunters.',
  },
  {
    id: 4,
    name: 'Dan Heng',
    rarity: 4,
    image: createSVGPlaceholder('%234169e1', 'DH'),
    stats: { ATK: 289, DEF: 176, HP: 825 },
    description: 'A reserved young man from the Xianzhou.',
  },
  {
    id: 5,
    name: 'Asta',
    rarity: 4,
    image: createSVGPlaceholder('%23ffd700', 'A'),
    stats: { ATK: 262, DEF: 154, HP: 792 },
    description: 'A talented professor of the Interastral Peace Corporation.',
  },
  {
    id: 6,
    name: 'March 7th',
    rarity: 4,
    image: createSVGPlaceholder('%2387ceeb', 'M7'),
    stats: { ATK: 241, DEF: 198, HP: 825 },
    description: 'A cheerful girl from the Nameless.',
  },
  {
    id: 7,
    name: 'Serval',
    rarity: 4,
    image: createSVGPlaceholder('%23ff69b4', 'S'),
    stats: { ATK: 268, DEF: 132, HP: 792 },
    description: 'A talented engineer and member of the Nameless.',
  },
  {
    id: 8,
    name: 'Arlan',
    rarity: 3,
    image: createSVGPlaceholder('%2332cd32', 'A'),
    stats: { ATK: 251, DEF: 120, HP: 759 },
    description: 'A soldier from the Herta Space Station.',
  },
];

// Gacha items reference
const GACHA_ITEMS = [
  { name: 'Leak', rarity: 'common', emoji: '❌', color: '#00d084' },
  { name: 'Normal', rarity: 'normal', emoji: '⭐', color: '#00d084' },
  { name: 'R', rarity: 'rare', emoji: '💫', color: '#00d084' },
  { name: 'SR', rarity: 'super_rare', emoji: '🌟', color: '#ffd700' },
  { name: 'SSR', rarity: 'ultra_rare', emoji: '👑', color: '#ff69b4' },
  { name: 'UR', rarity: 'ultra_rare', emoji: '💎', color: '#ffd700' },
];
const WEIGHTS = [10, 9, 60, 9, 9, 2.01];

// Local weighted random function (for offline support)
function weightedChoice(items, weights) {
  const cumulative = [];
  let sum = 0;
  for (let w of weights) {
    sum += w;
    cumulative.push(sum);
  }
  const total = cumulative[cumulative.length - 1];
  const random = Math.random() * total;

  for (let i = 0; i < cumulative.length; i++) {
    if (random <= cumulative[i]) {
      return items[i];
    }
  }
  return items[items.length - 1];
}

// Global state
let selectedCharacter = CHARACTERS[0]; // Select first character by default
let pullCount = 0;
let gachaResults = [];
let gachaHistory = JSON.parse(localStorage.getItem('gachaHistory') || '[]');

// Load selected banner from localStorage (set by home.html)
function loadSelectedBanner() {
  const selectedBanner = JSON.parse(localStorage.getItem('selectedBanner') || 'null');

  if (selectedBanner) {
    // Use the banner name to find the character, or create a character object from banner
    const character = CHARACTERS.find(
      (c) => c.name.toLowerCase() === selectedBanner.name.toLowerCase()
    );

    if (character) {
      selectedCharacter = character;
    } else {
      // If not found in CHARACTERS array, use banner as character (convert banner to character)
      selectedCharacter = {
        id: selectedBanner.id || 999,
        name: selectedBanner.name || 'Unknown',
        rarity: selectedBanner.rarity || 5,
        image: selectedBanner.color
          ? createSVGPlaceholder(selectedBanner.color, selectedBanner.name.substring(0, 1))
          : createSVGPlaceholder('%23ff1493', 'K'),
        stats: { ATK: 300, DEF: 150, HP: 900 },
        description: selectedBanner.description || 'Banner character',
      };
    }
    console.log(`✨ Loaded banner: ${selectedCharacter.name}`);
  } else {
    console.log('⚠️ No banner selected, redirecting to home...');
    // Optional: redirect to home if no banner selected
    // window.location.href = 'home.html';
  }
}

// ========== MOBILE ORIENTATION LOCK ==========
function lockOrientation() {
  try {
    // Try Capacitor ScreenOrientation plugin (non-blocking)
    Promise.all([import('@capacitor/screen-orientation')])
      .then(([module]) => {
        const { ScreenOrientation } = module;
        if (ScreenOrientation && ScreenOrientation.lock) {
          ScreenOrientation.lock({ orientation: 'sensorLandscape' })
            .then(() => console.log('📱 Auto-landscape with sensor rotation enabled'))
            .catch((e) => console.log('⚠️ ScreenOrientation error:', e));
        }
      })
      .catch(() => console.log('⚠️ ScreenOrientation not available'));

    // Fallback Web Orientation API (W3C standard)
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation
        .lock('landscape')
        .then(() => console.log('📱 Web Orientation API locked to landscape'))
        .catch(() => console.log('⚠️ Web Orientation API not supported'));
    }
  } catch (e) {
    console.log('⚠️ Orientation lock error:', e);
  }
}

// ========== INITIALIZE ON DOM READY - ULTRA FAST ==========
function initializeUI() {
  try {
    console.log('🔧 Starting initialization...');
    lockOrientation(); // Non-blocking async call

    // Load selected banner from localStorage (set by home.html)
    loadSelectedBanner();

    // 1. Initialize character selection (DOM)
    const thumbs = document.getElementById('characterThumbs');
    if (thumbs) {
      thumbs.innerHTML = '';
      CHARACTERS.forEach((char, index) => {
        const thumb = document.createElement('div');
        thumb.className = `char-thumb ${index === 0 ? 'active' : ''}`;
        thumb.onclick = () => selectCharacter(char);

        if (char.image) {
          const img = document.createElement('img');
          img.src = char.image;
          img.alt = char.name;
          thumb.appendChild(img);
        }
        thumbs.appendChild(thumb);
      });
    }

    // 2. Update main character info
    updateCharacterImage();
    updateCharacterInfo();
    updatePullCounter();

    // 3. Setup settings button
    const settingsBtn = document.querySelector('.settings-btn');
    if (settingsBtn) {
      settingsBtn.onclick = openSettingsModal;
    }

    // 3c. Setup modal backdrop click (doesn't interfere with buttons)
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
      settingsModal.addEventListener('click', (e) => {
        // Only close if clicking on the backdrop, not on modal content
        if (e.target === settingsModal) {
          closeSettingsModal();
        }
      });
    }

    // 3d. Setup results modal backdrop click - click outside to close
    const resultsModal = document.getElementById('resultsModal');
    if (resultsModal) {
      resultsModal.addEventListener('click', (e) => {
        // Only close if clicking on the backdrop, not on modal content
        if (e.target === resultsModal) {
          resultsModal.classList.remove('active');
        }
      });
    }

    // 4. Setup tilt effect (defer to prevent blocking)
    setTimeout(() => {
      const showcase = document.querySelector('.character-showcase');
      const image = document.getElementById('characterImage');
      if (showcase && image) {
        showcase.addEventListener('mousemove', (e) => {
          const rect = showcase.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          const centerX = rect.width / 2;
          const centerY = rect.height / 2;
          const rotateY = ((x - centerX) / centerX) * 15;
          const rotateX = ((centerY - y) / centerY) * 15;
          image.style.transform = `perspective(1200px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`;
        });

        showcase.addEventListener('mouseleave', () => {
          image.style.transform = 'perspective(1200px) rotateY(0deg) rotateX(0deg)';
        });
      }
    }, 100);

    console.log('✅ UI Ready');
  } catch (err) {
    console.error('❌ Init error:', err);
  }
}

function updateCharacterImage() {
  const img = document.getElementById('characterImage');
  if (img) {
    img.src = selectedCharacter.image || createSVGPlaceholder('%23666666', '?');
  }
}

function selectCharacter(character) {
  selectedCharacter = character;
  document.querySelectorAll('.char-thumb').forEach((thumb, index) => {
    thumb.classList.toggle('active', CHARACTERS[index].id === character.id);
  });
  updateCharacterInfo();
}

function updateCharacterInfo() {
  // Update name
  const nameEl = document.getElementById('charName');
  if (nameEl) nameEl.textContent = selectedCharacter.name;

  // Update rarity (stars)
  const rarityEl = document.getElementById('rarityDisplay');
  if (rarityEl) {
    rarityEl.innerHTML = '';
    for (let i = 0; i < selectedCharacter.rarity; i++) {
      const star = document.createElement('div');
      star.className = 'star';
      rarityEl.appendChild(star);
    }
  }

  // Update stats
  const statsEl = document.getElementById('statsContainer');
  if (statsEl) {
    statsEl.innerHTML = '';
    Object.entries(selectedCharacter.stats).forEach(([stat, value]) => {
      const row = document.createElement('div');
      row.className = 'stat-row';
      row.innerHTML = `<span class="stat-label">${stat}</span><span class="stat-value">${value}</span>`;
      statsEl.appendChild(row);
    });
  }

  // Update description
  const descEl = document.getElementById('charDescription');
  if (descEl) descEl.textContent = selectedCharacter.description;

  // Update banner name
  const bannerEl = document.getElementById('bannerName');
  if (bannerEl) bannerEl.textContent = `${selectedCharacter.name} Banner`;

  updateCharacterImage();
}

// ========== PULL COUNTER ==========
function updatePullCounter() {
  const counter = document.getElementById('pullCount');
  if (counter) counter.textContent = pullCount;
}

// ========== GACHA FUNCTIONS ==========
async function startGacha(count) {
  console.log(`🎮 Starting Gacha x${count}`);

  // Add spinning animation to button
  const button = event?.target;
  if (button) {
    button.classList.add('rolling');
    button.disabled = true;
  }

  gachaResults = [];

  try {
    if (USE_LOCAL_RANDOM) {
      // Use local random
      gachaResults = [];
      for (let i = 0; i < count; i++) {
        const item = weightedChoice(GACHA_ITEMS, WEIGHTS);
        gachaResults.push({
          name: item.name,
          emoji: item.emoji,
          rarity: item.rarity,
          isWin: item.rarity === 'super_rare' || item.rarity === 'ultra_rare',
        });
      }
    } else {
      // Call backend API
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);

      try {
        const response = await fetch(`${API_URL}/gacha`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ count }),
          signal: controller.signal,
        });

        clearTimeout(timeout);

        if (!response.ok) throw new Error(`API error: ${response.status}`);

        const data = await response.json();
        gachaResults = data.results;
      } catch (err) {
        clearTimeout(timeout);
        console.warn('Backend failed, using local random:', err.message);

        gachaResults = [];
        for (let i = 0; i < count; i++) {
          const item = weightedChoice(GACHA_ITEMS, WEIGHTS);
          gachaResults.push({
            name: item.name,
            emoji: item.emoji,
            rarity: item.rarity,
            isWin: item.rarity === 'super_rare' || item.rarity === 'ultra_rare',
          });
        }
      }
    }

    // Display results with animation delay
    setTimeout(() => {
      displayResults();
      pullCount += count;
      updatePullCounter();

      // Remove spinning animation after results show
      if (button) {
        button.classList.remove('rolling');
        button.disabled = false;
      }
    }, 800);
  } catch (error) {
    console.error('Gacha error:', error);
    showNotification('❌ Gacha failed: ' + error.message, 'error');
  }
}

function displayResults() {
  const modal = document.getElementById('resultsModal');
  const list = document.getElementById('resultsList');

  if (!modal || !list) return;

  list.innerHTML = '';

  gachaResults.forEach((result, index) => {
    setTimeout(() => {
      const item = document.createElement('div');
      item.className = 'result-item';

      const rarityColor = {
        common: '#888',
        normal: '#888',
        rare: '#00d084',
        super_rare: '#ffd700',
        ultra_rare: '#ff69b4',
      };

      const rarityClass = {
        common: '3-Star',
        normal: '3-Star',
        rare: '3-Star',
        super_rare: '4-Star',
        ultra_rare: '5-Star',
      };

      item.style.borderLeftColor = rarityColor[result.rarity] || '#888';
      item.style.animationDelay = `${index * 0.08}s`;

      item.innerHTML = `
        <div class="result-image" style="background: ${rarityColor[result.rarity]}/0.3;">${result.emoji}</div>
        <div class="result-info">
          <div class="result-name">${result.name}</div>
          <div class="result-rarity">${rarityClass[result.rarity] || result.rarity}</div>
        </div>
      `;

      list.appendChild(item);
    }, index * 50); // Faster stagger
  });

  modal.classList.add('active');
}

function confirmResults() {
  const modal = document.getElementById('resultsModal');
  if (modal) modal.classList.remove('active');

  // Add to history
  gachaResults.forEach((result) => {
    gachaHistory.unshift({
      item: result.name,
      emoji: result.emoji,
      rarity: result.rarity,
      timestamp: new Date().toLocaleString('vi-VN'),
      isWin: result.isWin,
    });
  });

  // Keep last 50
  if (gachaHistory.length > 50) {
    gachaHistory = gachaHistory.slice(0, 50);
  }

  localStorage.setItem('gachaHistory', JSON.stringify(gachaHistory));
  gachaResults = [];
}

// ========== MODAL HANDLERS ==========
function openSettingsModal() {
  console.log('🔧 Opening settings modal...');
  const modal = document.getElementById('settingsModal');
  if (modal) {
    modal.classList.add('active');
    const ip = document.getElementById('serverIp');
    const port = document.getElementById('serverPort');
    if (ip) ip.value = savedSettings.serverIp || '172.16.0.18';
    if (port) port.value = savedSettings.serverPort || '5000';
    console.log('✅ Modal opened');
  }
}

function closeSettingsModal() {
  console.log('🔧 Closing settings modal...');
  const modal = document.getElementById('settingsModal');
  if (modal) {
    modal.classList.remove('active');
    console.log('✅ Modal closed - class removed');
  } else {
    console.error('❌ Modal element not found!');
  }
}

function saveServerSettings() {
  const ip = document.getElementById('serverIp')?.value?.trim();
  const port = document.getElementById('serverPort')?.value?.trim() || '5000';

  if (!ip) {
    showNotification('⚠️ Please enter Server IP', 'error');
    return;
  }

  savedSettings.serverIp = ip;
  savedSettings.serverPort = port;
  localStorage.setItem('gachaSettings', JSON.stringify(savedSettings));

  API_URL = `http://${ip}:${port}/api`;

  showNotification(`✅ Saved!\nServer: ${ip}:${port}`, 'success');
  setTimeout(() => closeSettingsModal(), 500);
}

function closeGacha() {
  if (confirm('Return to home page?')) {
    window.location.href = 'home.html';
  }
}

// ========== TOAST NOTIFICATIONS ==========
function showNotification(message, type = 'info') {
  let existing = document.getElementById('notification-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'notification-toast';
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#00d084' : '#a86cff'};
    color: white;
    padding: 16px 24px;
    border-radius: 8px;
    z-index: 10000;
    font-weight: 600;
    max-width: 90%;
    text-align: center;
  `;

  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, 3000);
}

// ========== ANIMATIONS ==========
const style = document.createElement('style');
style.textContent = `
  @keyframes slideDown {
    from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
    to { transform: translateX(-50%) translateY(0); opacity: 1; }
  }

  @keyframes slideUp {
    from { transform: translateX(-50%) translateY(0); opacity: 1; }
    to { transform: translateX(-50%) translateY(-100%); opacity: 0; }
  }
`;
document.head.appendChild(style);

// ========== INITIALIZE ==========
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeUI);
} else {
  initializeUI();
}

console.log('✨ HSR Gacha UI loaded!');
