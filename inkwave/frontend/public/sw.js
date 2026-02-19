/**
 * InkWave Service Worker
 * Provides offline caching for static assets, API responses, and audio files
 */

// Build timestamp - automatically updated during build
const BUILD_TIMESTAMP = '2025-12-20T21:34:04.580Z';
const CACHE_VERSION = BUILD_TIMESTAMP;
const CACHE_NAME = `inkwave-v${CACHE_VERSION}`;
const STATIC_CACHE = `inkwave-static-v${CACHE_VERSION}`;
const AUDIO_CACHE = 'inkwave-audio-v1'; // Versioned separately to preserve downloads

console.log(`[SW] Version: ${CACHE_VERSION} (${BUILD_TIMESTAMP})`);

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

// Maximum audio cache size (500MB)
const MAX_AUDIO_CACHE_SIZE = 500 * 1024 * 1024;

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE).then(async (cache) => {
      console.log('[SW] Caching static assets');
      // Cache each asset individually to avoid failing on any single request
      for (const asset of STATIC_ASSETS) {
        try {
          await cache.add(asset);
          console.log('[SW] Cached:', asset);
        } catch (error) {
          console.warn('[SW] Failed to cache:', asset, error.message);
          // Continue caching other assets even if one fails
        }
      }
    })
  );
  // Activate immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete old caches that don't match current version
          if (cacheName !== STATIC_CACHE &&
              cacheName !== AUDIO_CACHE &&
              cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Take control of all clients immediately
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http(s) requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Strategy based on request type
  if (isAudioRequest(request)) {
    // Audio files: Cache first, then network
    event.respondWith(cacheFirst(request, AUDIO_CACHE));
  } else if (isStaticAsset(request)) {
    // Static assets: Cache first, then network
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else if (isAPIRequest(request)) {
    // API requests: Network first, cache as fallback
    event.respondWith(networkFirst(request, CACHE_NAME));
  } else {
    // Everything else: Network first
    event.respondWith(networkFirst(request, CACHE_NAME));
  }
});

// Check if request is for audio
function isAudioRequest(request) {
  const url = new URL(request.url);
  return url.pathname.includes('/audio') ||
         request.headers.get('Accept')?.includes('audio') ||
         url.pathname.endsWith('.mp3') ||
         url.pathname.endsWith('.wav');
}

// Check if request is for static assets
function isStaticAsset(request) {
  const url = new URL(request.url);
  return url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.jpg') ||
         url.pathname.endsWith('.svg') ||
         url.pathname.endsWith('.woff2');
}

// Check if request is API call
function isAPIRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api') ||
         url.hostname.includes('api.');
}

// Cache first strategy
async function cacheFirst(request, cacheName) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    // Return cached response, but also update cache in background
    fetchAndCache(request, cacheName);
    return cachedResponse;
  }
  return fetchAndCache(request, cacheName);
}

// Network first strategy
async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // If it's a navigation request, return the cached index.html
    if (request.mode === 'navigate') {
      return caches.match('/index.html');
    }
    throw error;
  }
}

// Fetch and cache helper
async function fetchAndCache(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('[SW] Fetch failed:', error);
    throw error;
  }
}

// Listen for messages from the client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }

  // Cache audio for offline playback
  if (event.data && event.data.type === 'CACHE_AUDIO') {
    const { url, bookId } = event.data;
    event.waitUntil(cacheAudioFile(url, bookId));
  }

  // Get cache status
  if (event.data && event.data.type === 'GET_CACHE_STATUS') {
    event.waitUntil(
      getCacheStatus().then((status) => {
        event.ports[0].postMessage(status);
      })
    );
  }

  // Check if audio is cached
  if (event.data && event.data.type === 'IS_CACHED') {
    const { url } = event.data;
    event.waitUntil(
      caches.match(url).then((response) => {
        event.ports[0].postMessage({ cached: !!response });
      })
    );
  }
});

// Cache a single audio file
async function cacheAudioFile(url, bookId) {
  try {
    const cache = await caches.open(AUDIO_CACHE);
    const response = await fetch(url);

    if (response.ok) {
      // Add metadata header for cleanup
      const headers = new Headers(response.headers);
      headers.set('X-Book-Id', bookId);
      headers.set('X-Cached-At', new Date().toISOString());

      const modifiedResponse = new Response(await response.blob(), {
        status: response.status,
        statusText: response.statusText,
        headers,
      });

      await cache.put(url, modifiedResponse);
      console.log('[SW] Cached audio:', url);

      // Check cache size and cleanup if needed
      await cleanupAudioCache();
    }
  } catch (error) {
    console.error('[SW] Failed to cache audio:', error);
  }
}

// Get cache status
async function getCacheStatus() {
  const status = {
    audioFiles: 0,
    audioSize: 0,
    staticFiles: 0,
    staticSize: 0,
  };

  try {
    const audioCache = await caches.open(AUDIO_CACHE);
    const audioKeys = await audioCache.keys();
    status.audioFiles = audioKeys.length;

    for (const request of audioKeys) {
      const response = await audioCache.match(request);
      if (response) {
        const blob = await response.clone().blob();
        status.audioSize += blob.size;
      }
    }

    const staticCache = await caches.open(STATIC_CACHE);
    const staticKeys = await staticCache.keys();
    status.staticFiles = staticKeys.length;
  } catch (error) {
    console.error('[SW] Error getting cache status:', error);
  }

  return status;
}

// Cleanup old audio files if cache is too large
async function cleanupAudioCache() {
  try {
    const cache = await caches.open(AUDIO_CACHE);
    const keys = await cache.keys();

    // Calculate total size
    let totalSize = 0;
    const items = [];

    for (const request of keys) {
      const response = await cache.match(request);
      if (response) {
        const blob = await response.clone().blob();
        const cachedAt = response.headers.get('X-Cached-At') || new Date(0).toISOString();
        items.push({
          request,
          size: blob.size,
          cachedAt: new Date(cachedAt),
        });
        totalSize += blob.size;
      }
    }

    // If over limit, remove oldest items
    if (totalSize > MAX_AUDIO_CACHE_SIZE) {
      console.log('[SW] Audio cache over limit, cleaning up...');

      // Sort by date (oldest first)
      items.sort((a, b) => a.cachedAt.getTime() - b.cachedAt.getTime());

      while (totalSize > MAX_AUDIO_CACHE_SIZE * 0.8 && items.length > 0) {
        const oldest = items.shift();
        if (oldest) {
          await cache.delete(oldest.request);
          totalSize -= oldest.size;
          console.log('[SW] Removed old cached audio:', oldest.request.url);
        }
      }
    }
  } catch (error) {
    console.error('[SW] Error cleaning up audio cache:', error);
  }
}

// Notify clients about offline status changes
self.addEventListener('online', () => {
  self.clients.matchAll().then((clients) => {
    clients.forEach((client) => {
      client.postMessage({ type: 'ONLINE' });
    });
  });
});

self.addEventListener('offline', () => {
  self.clients.matchAll().then((clients) => {
    clients.forEach((client) => {
      client.postMessage({ type: 'OFFLINE' });
    });
  });
});

console.log('[SW] Service worker loaded');
