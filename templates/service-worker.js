{% load static %}
const CACHE_NAME = "amparo-shell-v9";
const SAFE_ASSETS = [
  "{% url 'offline' %}",
  "{% static 'css/amparo.css' %}?v=9",
  "{% static 'js/amparo.js' %}?v=9",
  "{% static 'brand/logo-mark.svg' %}",
  "{% static 'icons/sprite.svg' %}"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SAFE_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (event.request.mode === "navigate") {
    event.respondWith(fetch(event.request).catch(() => caches.match("{% url 'offline' %}")));
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
  }
});
