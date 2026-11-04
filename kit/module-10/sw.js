// sw.js
// A service worker: a small script the browser keeps beside the page and runs between the page and the network.
// Course kit, module 10

// 1. ON INSTALL: save the page's own files, including Module 20's engine ###################################
const CACHE = "front-door-v1";
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(["./", "./index.html", "./app.js", "../module-20/edge.js"])));
  self.skipWaiting();
});
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

// 2. ON EVERY REQUEST: saved copy first, network second ###################################
// Only GET requests are saved. Questions to the API are POST, so they always go to the real server:
// a saved copy of an old answer would be a wrong answer.
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((hit) => hit || fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy));
      return res;
    }))
  );
});
