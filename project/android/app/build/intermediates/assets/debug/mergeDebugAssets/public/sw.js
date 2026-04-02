// Service Worker - Cache Strategy for Performance
const CACHE_NAME = 'hsr-gacha-v2-bo-den';
const URLS_TO_CACHE = [
  '/',
  '/index.html',
  '/home.html',
  '/login.html',
  '/admin-new.html',
  '/api.js',
  '/script.js',
  '/style.css',
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Service Worker: Caching app files');
      return cache.addAll(URLS_TO_CACHE).catch(() => {
        console.log('Service Worker: Some files failed to cache (non-critical)');
      });
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip API calls (always fetch fresh)
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        // Return cached version
        return response;
      }

      // Fetch from network
      return fetch(event.request)
        .then((response) => {
          // Don't cache if not successful
          if (!response || response.status !== 200) {
            return response;
          }

          // Cache successful responses
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });

          return response;
        })
        .catch(() => {
          // Offline fallback
          return caches.match('/index.html');
        });
    })
  );
});
