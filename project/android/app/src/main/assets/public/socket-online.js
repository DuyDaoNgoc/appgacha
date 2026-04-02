/**
 * 🎮 Socket.io Client for Real-time Online Status
 * Handles WebSocket connections, online/offline events, and real-time player list
 */

// Socket.io connection
let socket = null;
const API_URL = window.location.origin || 'http://172.16.0.18:5000';

// ============ Socket.io Setup ============
function initializeSocket() {
  try {
    // Load Socket.io library
    const script = document.createElement('script');
    script.src = '/socket.io/socket.io.js';
    script.onload = function () {
      console.log('✅ Socket.io library loaded');
      connectSocket();
    };
    script.onerror = function () {
      console.warn('⚠️  Socket.io library not found, using polling fallback');
      setupPolling();
    };
    document.head.appendChild(script);
  } catch (e) {
    console.error('❌ Socket.io init error:', e);
    setupPolling();
  }
}

function connectSocket() {
  try {
    socket = io(API_URL, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      transports: ['websocket', 'polling'],
    });

    // Connection events
    socket.on('connect', () => {
      console.log('✅ Connected to server (Socket.io)');
      const userId = localStorage.getItem('user_id');
      const username = localStorage.getItem('username');

      if (userId && username) {
        // Tell server user is online
        socket.emit('user:login', { user_id: userId, username });
      }
    });

    socket.on('disconnect', () => {
      console.log('❌ Disconnected from server');
      setupPolling(); // Fallback to polling
    });

    socket.on('error', (error) => {
      console.error('⚠️  Socket error:', error);
    });

    // Online status events
    socket.on('user:online', (data) => {
      console.log(`✅ ${data.username} came online`);
      updateOnlineUsersList();
      showNotification(`${data.username} is online`);
    });

    socket.on('user:offline', (data) => {
      console.log(`❌ ${data.username} went offline`);
      updateOnlineUsersList();
      showNotification(`${data.username} went offline`);
    });

    socket.on('online-users:list', (data) => {
      console.log('👥 Received online users list:', data.users);
      displayOnlineUsers(data.users);
    });
  } catch (e) {
    console.error('❌ Socket connection error:', e);
    setupPolling();
  }
}

// ============ Polling Fallback ============
let pollingInterval = null;

function setupPolling() {
  if (pollingInterval) clearInterval(pollingInterval);

  console.log('📡 Starting polling fallback (5s interval)');

  // Get initial list
  fetchOnlineUsers();

  // Poll every 5 seconds
  pollingInterval = setInterval(() => {
    fetchOnlineUsers();
  }, 5000);
}

async function fetchOnlineUsers() {
  try {
    const response = await fetch(`${API_URL}/api/online-users`);
    const data = await response.json();
    displayOnlineUsers(data.online_users || []);
  } catch (e) {
    console.error('❌ Polling error:', e);
  }
}

// ============ Online Users Display ============
function displayOnlineUsers(users) {
  const container = document.getElementById('online-users-container');
  if (!container) return;

  if (users.length === 0) {
    container.innerHTML = '<p style="color: #999; text-align: center;">No users online</p>';
    return;
  }

  let html = '<div class="online-users-list">';
  html += `<h3>Online Players (${users.length})</h3>`;

  users.forEach((user) => {
    html += `
      <div class="online-user-item">
        <span class="online-indicator">🟢</span>
        <span class="username">${user.username || 'Unknown'}</span>
      </div>
    `;
  });

  html += '</div>';
  container.innerHTML = html;
}

function updateOnlineUsersList() {
  if (socket && socket.connected) {
    socket.emit('online-users:request');
  } else {
    fetchOnlineUsers();
  }
}

// ============ Notifications ============
function showNotification(message) {
  // Create notification element
  const notif = document.createElement('div');
  notif.className = 'online-notification';
  notif.textContent = message;
  notif.style.cssText = `
    position: fixed;
    top: 60px;
    right: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 9999;
    animation: slideIn 0.3s ease-out;
  `;

  document.body.appendChild(notif);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    notif.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => notif.remove(), 300);
  }, 3000);
}

// ============ User Login/Logout ============
async function broadcastUserOnline() {
  const userId = localStorage.getItem('user_id');
  const username = localStorage.getItem('username');

  if (!userId || !username) return;

  if (socket && socket.connected) {
    socket.emit('user:login', { user_id: userId, username });
  } else {
    // Fallback: Just use API
    try {
      await fetch(`${API_URL}/api/user/online`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (e) {
      console.error('❌ Failed to set user online:', e);
    }
  }

  updateOnlineUsersList();
}

async function broadcastUserOffline() {
  const userId = localStorage.getItem('user_id');
  const username = localStorage.getItem('username');

  if (!userId || !username) return;

  if (socket && socket.connected) {
    socket.emit('user:logout', { user_id: userId, username });
    socket.disconnect();
  } else {
    // Fallback: Just use API
    try {
      await fetch(`${API_URL}/api/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        keepalive: true,
      });
    } catch (e) {
      console.log('Logout API error (non-critical):', e);
    }
  }
}

// ============ Page Lifecycle ============
document.addEventListener('DOMContentLoaded', () => {
  console.log('🎮 Initializing online status system...');
  initializeSocket();

  // Broadcast current status if user is logged in
  if (localStorage.getItem('user_id')) {
    broadcastUserOnline();
  }
});

// Handle page unload
window.addEventListener('beforeunload', broadcastUserOffline);
window.addEventListener('unload', broadcastUserOffline);

// Handle app close (Capacitor)
if (typeof cordova !== 'undefined' || window.location.href.includes('ionic')) {
  document.addEventListener('pause', broadcastUserOffline);
  document.addEventListener('deviceready', () => {
    if (navigator.app) {
      document.addEventListener('backbutton', broadcastUserOffline, false);
    }
  });
}

// ============ Styling ============
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }

  .online-users-list {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .online-users-list h3 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
    font-weight: 600;
  }

  .online-user-item {
    display: flex;
    align-items: center;
    padding: 8px;
    margin-bottom: 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 8px;
    font-size: 13px;
  }

  .online-user-item:last-child {
    margin-bottom: 0;
  }

  .online-indicator {
    margin-right: 8px;
    font-size: 16px;
  }

  .username {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
`;
document.head.appendChild(style);

console.log('✅ Online status system initialized!');
