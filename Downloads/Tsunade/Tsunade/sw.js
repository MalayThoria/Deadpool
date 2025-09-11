const CACHE_NAME = 'lp-assistant-healthcare-v1';
const urlsToCache = [
  '/Deadpool/',
  '/Deadpool/static/js/main.4b0c17ce.js',
  '/Deadpool/static/css/main.79087dfa.css',
  '/Deadpool/manifest.json',
  '/Deadpool/icon-192x192.svg',
  '/Deadpool/icon-512x512.svg'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New health update available!',
    icon: '/Deadpool/icon-192x192.svg',
    badge: '/Deadpool/icon-192x192.svg',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: '/Deadpool/icon-192x192.svg'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/Deadpool/icon-192x192.svg'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('LP Assistant Healthcare', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/Deadpool/')
    );
  }
});

// Background sync function
async function doBackgroundSync() {
  try {
    // Sync offline data when connection is restored
    const offlineData = await getOfflineData();
    if (offlineData.length > 0) {
      await syncDataToServer(offlineData);
      await clearOfflineData();
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Helper functions for offline data management
async function getOfflineData() {
  // Implementation would retrieve data from IndexedDB
  return [];
}

async function syncDataToServer(data) {
  // Implementation would send data to server
  console.log('Syncing data to server:', data);
}

async function clearOfflineData() {
  // Implementation would clear synced data from IndexedDB
  console.log('Cleared offline data');
}