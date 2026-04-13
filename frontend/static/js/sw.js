/**
 * MindfulAI — sw.js (Service Worker)
 * Caches static assets for basic offline capability.
 */

const CACHE_NAME = "mindfulai-v1";
const STATIC_ASSETS = [
  "/",
  "/static/css/main.css",
  "/static/css/chat.css",
  "/static/css/dashboard.css",
  "/static/js/api.js",
  "/static/js/auth.js",
  "/static/js/voice.js",
  "/static/js/chat.js",
  "/static/js/journal.js",
  "/static/js/habits.js",
  "/static/js/ui.js",
  "/static/js/app.js",
];

// Install: cache static assets
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate: delete old caches
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: cache-first for static, network-first for API
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);

  // Always go to network for API calls
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(
          JSON.stringify({ error: "You appear to be offline. Please check your connection." }),
          { headers: { "Content-Type": "application/json" }, status: 503 }
        )
      )
    );
    return;
  }

  // Cache-first for static assets
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
