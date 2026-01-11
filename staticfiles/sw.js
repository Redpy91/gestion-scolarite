self.addEventListener("install", event => {
  event.waitUntil(
    caches.open("scolarite-v1").then(cache => {
      return cache.addAll([
        "/",
        "/admin/"
      ]);
    })
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
