const CACHE = "wath-signal-v1";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/maskable-512.png"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.map(k => { if (k !== CACHE) return caches.delete(k); })))
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (url.pathname.endsWith("/data/latest.json")) {
    e.respondWith(networkFirst(e.request));
  } else {
    e.respondWith(cacheFirst(e.request));
  }
});

function networkFirst(req) {
  return fetch(req).then(res => {
    const clone = res.clone();
    caches.open(CACHE).then(c => c.put(req, clone));
    return res;
  }).catch(() => caches.match(req));
}

function cacheFirst(req) {
  return caches.match(req).then(res => res || fetch(req));
}
