// Service worker - Chrome'un PWA olarak kurması (tam ekran) için gerekli.
// Strateji: ÖNCE AĞ (network-first). PC açıkken hep en güncel dosyayı çeker;
// sadece PC erişilemezse cache'e düşer. Böylece frontend güncellemeleri
// anında tablete ulaşır (eski sürüm takılı kalmaz).
const CACHE = "dock-v4";
const ASSETS = [
  "/", "/index.html", "/style.css", "/app.js",
  "/icon-192.png", "/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/api")) return;   // API her zaman ağdan, cache'lenmez
  // Önce ağ; başarılıysa cache'i güncelle, başarısızsa cache'ten ver.
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
