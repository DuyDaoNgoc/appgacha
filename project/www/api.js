// ============ API Configuration ============
const API_URL = 'http://172.16.0.18:5000';

// ============ Auth & User Management ============
function getToken() {
  return localStorage.getItem('token');
}

function getAuthHeader() {
  return {
    Authorization: `Bearer ${getToken()}`,
    'Content-Type': 'application/json',
  };
}

function checkAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

async function getUserProfile() {
  try {
    const response = await fetch(`${API_URL}/api/user/profile`, {
      method: 'GET',
      headers: getAuthHeader(),
    });

    if (response.status === 401) {
      localStorage.clear();
      window.location.href = 'login.html';
      return null;
    }

    const data = await response.json();
    if (response.ok) {
      localStorage.setItem('xu', data.xu);
      localStorage.setItem('stars', data.stars);
      return data;
    }
  } catch (e) {
    console.log('Profile fetch error:', e);
  }
  return null;
}

// ============ Gacha System ============
async function performGacha(rolls = 1) {
  const token = getToken();
  if (!token) {
    showNotification('❌ Please login first', 'error');
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/api/gacha/roll`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: JSON.stringify({ rolls: rolls }),
    });

    const data = await response.json();

    if (response.ok) {
      localStorage.setItem('xu', data.xu_remaining);
      return {
        success: true,
        results: data.results,
        xu_remaining: data.xu_remaining,
      };
    } else {
      showNotification(`❌ ${data.error}`, 'error');
      return { success: false };
    }
  } catch (e) {
    showNotification('❌ Gacha failed: Connection error', 'error');
    console.log('Gacha error:', e);
    return { success: false };
  }
}

// ============ Mailbox System ============
async function loadMailbox() {
  const token = getToken();
  if (!token) return [];

  try {
    const response = await fetch(`${API_URL}/api/mailbox/messages`, {
      method: 'GET',
      headers: getAuthHeader(),
    });

    const data = await response.json();
    return data.messages || [];
  } catch (e) {
    console.log('Mailbox load error:', e);
    return [];
  }
}

async function claimReward(messageId) {
  const token = getToken();
  if (!token) return false;

  try {
    const response = await fetch(`${API_URL}/api/mailbox/claim/${messageId}`, {
      method: 'POST',
      headers: getAuthHeader(),
    });

    const data = await response.json();

    if (response.ok) {
      showNotification(`✅ Claimed! +${data.xu_gained} Xu, +${data.stars_gained} Stars`, 'success');
      // Refresh profile
      await getUserProfile();
      return true;
    } else {
      showNotification(`❌ ${data.error}`, 'error');
      return false;
    }
  } catch (e) {
    showNotification('❌ Claim failed', 'error');
    return false;
  }
}

// ============ Notification System ============
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = message;
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? 'rgba(244,67,54,0.9)' : type === 'success' ? 'rgba(76,175,80,0.9)' : 'rgba(33,150,243,0.9)'};
        color: white;
        border-radius: 8px;
        font-weight: bold;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// ============ Logout ============
async function logout() {
  if (confirm('Are you sure you want to logout?')) {
    try {
      const token = getToken();
      if (token) {
        // Call backend to set offline status
        await fetch(`${API_URL}/api/logout`, {
          method: 'POST',
          headers: getAuthHeader(),
        }).catch((e) => console.log('Logout API call failed (non-critical):', e));
      }
    } catch (e) {
      console.log('Logout error:', e);
    } finally {
      // Clear local data
      localStorage.clear();
      window.location.href = 'login.html';
    }
  }
}

// ============ Auto Logout on App Close ============
async function logoutOnAppClose() {
  const token = getToken();
  if (token) {
    try {
      // Use keepalive for reliable delivery on page unload
      fetch(`${API_URL}/api/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        keepalive: true,
      }).catch((e) => console.log('Auto logout failed (non-critical):', e));
    } catch (e) {
      console.log('Auto logout error:', e);
    }
  }
}

// Set up auto-logout on page unload
window.addEventListener('beforeunload', logoutOnAppClose);
window.addEventListener('unload', logoutOnAppClose);

// ============ Characters Data ============
const CHARACTERS = [
  {
    id: 1,
    name: 'Kafka',
    initial: 'K',
    rarity: 5,
    description: 'A charming woman from the Antimatter Legion.',
    color: '#ff1493',
  },
  {
    id: 2,
    name: 'Jingliu',
    initial: 'J',
    rarity: 5,
    description: 'The Master Swordsman.',
    color: '#8b008b',
  },
  {
    id: 3,
    name: 'Blade',
    initial: 'B',
    rarity: 5,
    description: 'The Cursed Warrior.',
    color: '#800000',
  },
  {
    id: 4,
    name: 'Dan Heng',
    initial: 'D',
    rarity: 5,
    description: 'The Nameless.',
    color: '#4169e1',
  },
  {
    id: 5,
    name: 'Asta',
    initial: 'A',
    rarity: 4,
    description: 'The Optimist.',
    color: '#00bfff',
  },
  {
    id: 6,
    name: 'March 7th',
    initial: 'M',
    rarity: 4,
    description: 'The Cheerful Wanderer.',
    color: '#ff69b4',
  },
  {
    id: 7,
    name: 'Serval',
    initial: 'S',
    rarity: 4,
    description: 'The Engineer.',
    color: '#ff8c00',
  },
  {
    id: 8,
    name: 'Arlan',
    initial: 'A',
    rarity: 4,
    description: 'The Guard.',
    color: '#32cd32',
  },
];

// ============ SVG Generator ============
function generateSVG(character, size = 300) {
  const fontSize = Math.round(size * 0.2);
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${size} ${size}' style='background:${character.color}20'%3E%3Ccircle cx='${size / 2}' cy='${size / 2}' r='${size * 0.4}' fill='${character.color}'/%3E%3Ctext x='50%25' y='50%25' font-size='${fontSize}' font-weight='bold' fill='white' text-anchor='middle' dy='0.3em'%3E${character.initial}%3C/text%3E%3C/svg%3E`;
}

// ============ Tilt Effect ============
function setupTiltEffect() {
  const showcase = document.querySelector('.character-showcase');
  if (!showcase) return;

  let mouseX = 0,
    mouseY = 0;

  showcase.addEventListener('mousemove', (e) => {
    const rect = showcase.getBoundingClientRect();
    mouseX = (e.clientX - rect.left) / rect.width;
    mouseY = (e.clientY - rect.top) / rect.height;

    const rotateX = (mouseY - 0.5) * 30;
    const rotateY = -(mouseX - 0.5) * 30;

    showcase.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.05)`;
  });

  showcase.addEventListener('mouseleave', () => {
    showcase.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
  });
}

// ============ Orientation Lock ============
async function lockLandscapeOrientation() {
  try {
    if (typeof ScreenOrientation !== 'undefined' && screen.orientation && screen.orientation.lock) {
      await screen.orientation.lock('sensorLandscape');
      console.log('🔒 Landscape locked');
    } else if (typeof AndroidScreenOrientation !== 'undefined') {
      // Fallback for Cordova
      window.cordova.plugins.ScreenOrientation.lockOrientation('landscape');
    }
  } catch (e) {
    console.log('Orientation lock not available');
  }
}

// ============ Initialize Game ============
async function initializeGame() {
  console.log('🔧 Initializing Game...');

  // Check auth
  if (!checkAuth()) return;

  // Load user profile
  const profile = await getUserProfile();
  if (profile) {
    updateUI(profile);
  }

  // Setup UI
  setupTiltEffect();
  lockLandscapeOrientation();
  loadMailbox().then((messages) => {
    if (messages.length > 0) {
      showNotification(`📬 You have ${messages.length} new messages!`, 'info');
    }
  });

  console.log('✅ Game initialized');
}

function updateUI(profile) {
  const xuDisplay = document.querySelector('.xu-display');
  const starsDisplay = document.querySelector('.stars-display');
  const usernameDisplay = document.querySelector('.username-display');

  if (xuDisplay) xuDisplay.textContent = profile.xu;
  if (starsDisplay) starsDisplay.textContent = profile.stars;
  if (usernameDisplay) usernameDisplay.textContent = profile.username;
}

// ============ Add CSS Animations ============
document.head.insertAdjacentHTML(
  'beforeend',
  `
<style>
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
</style>
`
);

// ============ Initialize on Load ============
document.addEventListener('DOMContentLoaded', initializeGame);
