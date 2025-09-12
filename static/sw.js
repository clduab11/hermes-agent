/**
 * HERMES Legal AI Dashboard - Service Worker
 * Provides offline functionality and PWA capabilities
 */

const CACHE_NAME = 'hermes-v1.0.0';
const STATIC_CACHE_NAME = 'hermes-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'hermes-dynamic-v1.0.0';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/dashboard',
  '/static/assets/legal-theme/styles.css',
  '/static/dashboard/app.js',
  '/static/dashboard/voice-interface.js',
  '/static/dashboard/analytics.js',
  '/static/manifest.json',
  '/templates/dashboard.html',
  // Font files will be cached dynamically
  'https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=Source+Sans+Pro:wght@300;400;500;600;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Cache strategies for different types of requests
const CACHE_STRATEGIES = {
  // Cache first for static assets
  STATIC: 'cache-first',
  // Network first for API calls
  API: 'network-first',
  // Stale while revalidate for dynamic content
  DYNAMIC: 'stale-while-revalidate'
};

self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Pre-caching static assets...');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Failed to cache static assets:', error);
      })
  );
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName.startsWith('hermes-')) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        return self.clients.claim();
      })
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http(s) requests
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // Determine cache strategy based on request type
  if (isApiRequest(url)) {
    event.respondWith(networkFirstStrategy(request));
  } else if (isStaticAsset(url)) {
    event.respondWith(cacheFirstStrategy(request));
  } else {
    event.respondWith(staleWhileRevalidateStrategy(request));
  }
});

// Cache strategies implementation

async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Cache first strategy failed:', error);
    return createOfflineFallback(request);
  }
}

async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network failed, trying cache for:', request.url);
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    return createOfflineFallback(request);
  }
}

async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const cachedResponse = await caches.match(request);
  
  const fetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => {
    return cachedResponse;
  });
  
  return cachedResponse || fetchPromise;
}

// Helper functions

function isApiRequest(url) {
  return url.pathname.startsWith('/api/') || 
         url.pathname.startsWith('/auth/') ||
         url.pathname.startsWith('/ws/');
}

function isStaticAsset(url) {
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.woff', '.woff2', '.ttf'];
  const pathname = url.pathname.toLowerCase();
  
  return staticExtensions.some(ext => pathname.endsWith(ext)) ||
         url.pathname.startsWith('/static/') ||
         url.hostname.includes('fonts.googleapis.com') ||
         url.hostname.includes('cdnjs.cloudflare.com');
}

function createOfflineFallback(request) {
  const url = new URL(request.url);
  
  if (request.headers.get('accept')?.includes('text/html')) {
    return caches.match('/dashboard').then(response => {
      return response || new Response(
        getOfflineHTML(),
        { headers: { 'Content-Type': 'text/html' } }
      );
    });
  }
  
  if (request.headers.get('accept')?.includes('application/json')) {
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'This feature requires an internet connection'
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
  
  return new Response('Offline', { status: 503 });
}

function getOfflineHTML() {
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HERMES - Offline</title>
        <style>
            body {
                font-family: 'Source Sans Pro', sans-serif;
                background: linear-gradient(135deg, #1a365d, #2d5a87);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }
            .offline-container {
                max-width: 400px;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }
            .offline-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
                opacity: 0.8;
            }
            .offline-title {
                font-size: 2rem;
                margin-bottom: 1rem;
                font-family: 'Crimson Text', serif;
            }
            .offline-message {
                font-size: 1.1rem;
                margin-bottom: 2rem;
                opacity: 0.9;
                line-height: 1.6;
            }
            .offline-button {
                background: #d69e2e;
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .offline-button:hover {
                background: #b7791f;
                transform: translateY(-2px);
            }
            .pulse {
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        </style>
    </head>
    <body>
        <div class="offline-container">
            <div class="offline-icon pulse">📡</div>
            <h1 class="offline-title">You're Offline</h1>
            <p class="offline-message">
                HERMES Legal AI requires an internet connection to function. 
                Please check your connection and try again.
            </p>
            <button class="offline-button" onclick="window.location.reload()">
                Try Again
            </button>
        </div>
    </body>
    </html>
  `;
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'offline-voice-data') {
    event.waitUntil(syncOfflineVoiceData());
  } else if (event.tag === 'offline-analytics') {
    event.waitUntil(syncOfflineAnalytics());
  }
});

async function syncOfflineVoiceData() {
  try {
    // Retrieve offline voice data from IndexedDB
    const offlineData = await getOfflineVoiceData();
    
    if (offlineData.length > 0) {
      // Send to server
      for (const data of offlineData) {
        await fetch('/api/voice/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data)
        });
      }
      
      // Clear synced data
      await clearOfflineVoiceData();
      console.log('Offline voice data synced successfully');
    }
  } catch (error) {
    console.error('Failed to sync offline voice data:', error);
  }
}

async function syncOfflineAnalytics() {
  try {
    // Sync offline analytics data
    const offlineAnalytics = await getOfflineAnalytics();
    
    if (offlineAnalytics.length > 0) {
      await fetch('/api/analytics/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(offlineAnalytics)
      });
      
      await clearOfflineAnalytics();
      console.log('Offline analytics synced successfully');
    }
  } catch (error) {
    console.error('Failed to sync offline analytics:', error);
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  if (!event.data) {
    return;
  }
  
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/static/assets/icons/icon-192x192.png',
    badge: '/static/assets/icons/badge-72x72.png',
    tag: data.tag || 'hermes-notification',
    requireInteraction: data.requireInteraction || false,
    data: data.data || {},
    actions: data.actions || []
  };
  
  if (data.urgency === 'high') {
    options.requireInteraction = true;
    options.silent = false;
  }
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const notificationData = event.notification.data;
  let targetUrl = '/dashboard';
  
  if (event.action) {
    // Handle notification action clicks
    switch (event.action) {
      case 'view-session':
        targetUrl = '/dashboard#voice-interface';
        break;
      case 'view-analytics':
        targetUrl = '/dashboard#analytics';
        break;
      case 'view-matters':
        targetUrl = '/dashboard#matters';
        break;
    }
  } else if (notificationData.url) {
    targetUrl = notificationData.url;
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      // Check if dashboard is already open
      for (const client of clientList) {
        if (client.url.includes('/dashboard') && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});

// Placeholder functions for IndexedDB operations
// These would be implemented with proper IndexedDB operations
async function getOfflineVoiceData() {
  // Implementation would retrieve data from IndexedDB
  return [];
}

async function clearOfflineVoiceData() {
  // Implementation would clear data from IndexedDB
}

async function getOfflineAnalytics() {
  // Implementation would retrieve analytics from IndexedDB
  return [];
}

async function clearOfflineAnalytics() {
  // Implementation would clear analytics from IndexedDB
}

console.log('HERMES Service Worker loaded successfully');