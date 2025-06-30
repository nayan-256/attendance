const CACHE_NAME = 'attendance-system-v1.0.0';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/student_login',
  '/teacher_login',
  '/register',
  '/qr_scanner',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://unpkg.com/aos@2.3.1/dist/aos.css',
  'https://unpkg.com/aos@2.3.1/dist/aos.js',
  'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap'
];

// Install Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch Event
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

// Activate Service Worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background Sync for Offline Attendance
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-attendance') {
    event.waitUntil(syncAttendance());
  }
});

async function syncAttendance() {
  try {
    const offlineData = await getOfflineAttendanceData();
    if (offlineData.length > 0) {
      for (const data of offlineData) {
        await fetch('/api/sync_attendance', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data)
        });
      }
      await clearOfflineAttendanceData();
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Push Notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New attendance notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '2'
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: '/static/icons/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icons/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Attendance System', options)
  );
});

// Notification Click Handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/dashboard')
    );
  }
});

// Helper functions for offline storage
async function getOfflineAttendanceData() {
  return new Promise((resolve) => {
    const request = indexedDB.open('AttendanceDB', 1);
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['offline_attendance'], 'readonly');
      const store = transaction.objectStore('offline_attendance');
      const getAllRequest = store.getAll();
      
      getAllRequest.onsuccess = () => {
        resolve(getAllRequest.result);
      };
    };
  });
}

async function clearOfflineAttendanceData() {
  return new Promise((resolve) => {
    const request = indexedDB.open('AttendanceDB', 1);
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['offline_attendance'], 'readwrite');
      const store = transaction.objectStore('offline_attendance');
      store.clear();
      transaction.oncomplete = () => resolve();
    };
  });
}
