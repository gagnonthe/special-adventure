const CACHE_NAME = 'playscore-pwa-v1';
const ASSETS = [
  '/',
  '/static/app.js',
  '/static/style.css',
  '/static/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener('fetch', (e) => {
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
