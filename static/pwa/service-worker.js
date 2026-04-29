const CACHE_NAME = 'podarguard-pwa-v1';
const APP_ASSETS = [
  '/manifest.json',
  '/static/pwa/icon.svg'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(APP_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (key) {
            return key !== CACHE_NAME;
          })
          .map(function (key) {
            return caches.delete(key);
          })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (event) {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET') {
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(function () {
        return new Response(
          '<!doctype html><title>PodarGuard Offline</title><meta name="viewport" content="width=device-width,initial-scale=1"><body style="font-family:Arial,sans-serif;margin:24px;background:#f6f7fb;color:#172033"><h1>PodarGuard</h1><p>You are offline. Reconnect to view live child device details.</p></body>',
          {
            headers: {
              'Content-Type': 'text/html; charset=utf-8'
            }
          }
        );
      })
    );
    return;
  }

  if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(function (cachedResponse) {
        return cachedResponse || fetch(request).then(function (networkResponse) {
          const responseCopy = networkResponse.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(request, responseCopy);
          });
          return networkResponse;
        });
      })
    );
  }
});
