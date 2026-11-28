const CACHE = 'quantum-leads-ai-v2';
const ASSETS = ['/', '/index.html', '/styles.css', '/app.js', '/logo.svg', '/manifest.webmanifest'];
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())));
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  const isNavigation = event.request.mode === 'navigate';
  event.respondWith((isNavigation ? fetch(event.request).then(response => {
    if (response.ok) caches.open(CACHE).then(cache => cache.put('/index.html', response.clone()));
    return response;
  }).catch(() => caches.match('/index.html')) : caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if (response.ok) caches.open(CACHE).then(cache => cache.put(event.request, response.clone()));
    return response;
  })).catch(() => caches.match('/index.html')));
});
