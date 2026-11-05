// sw.js: a service worker, a small script the browser keeps beside the page.
// It saves every file the page fetches (page, code, runtime, model) the first time,
// then serves the saved copy when the network is gone. That is what makes the page work offline.
const CACHE = "field-assistant-v3";   // v3: the matcher moved to match.js
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(["./", "./index.html", "./app.js", "../module-10/edge.js", "./notes.json", "./match.js"])));
  self.skipWaiting();
});
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
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
