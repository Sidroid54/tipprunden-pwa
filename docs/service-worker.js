const CACHE_PREFIX = "tasmania-hackentrick-";
const CACHE_NAME = `${CACHE_PREFIX}v15`;

const APP_SHELL = [
  "./index.html",
  "./styles.css",
  "./app.js",
  "./data/seasons.json",
  "./data/2026-27.json",
  "./data/2025-26.json",
  "./manifest.json",
  "./assets/logo-tasmania.png",
  "./assets/icon-tasmania-192.png",
  "./assets/icon-tasmania-512.png"
];

const INDEX_URL = new URL("./index.html", self.registration.scope).href;

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
  );

  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames
          .filter(
            name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME
          )
          .map(name => caches.delete(name))
      )
    )
  );

  self.clients.claim();
});

async function loadLatestData(request) {
  const cache = await caches.open(CACHE_NAME);
  const cacheUrl = new URL(request.url);
  cacheUrl.search = "";

  try {
    const response = await fetch(request);

    if (!response.ok) {
      throw new Error(`data.json antwortet mit ${response.status}`);
    }

    await cache.put(cacheUrl.href, response.clone());
    return response;
  } catch (error) {
    const cachedResponse = await cache.match(cacheUrl.href);

    if (cachedResponse) {
      return cachedResponse;
    }

    throw error;
  }
}

async function loadNavigation(request) {
  try {
    return await fetch(request);
  } catch (error) {
    const cachedResponse = await caches.match(INDEX_URL);

    if (cachedResponse) {
      return cachedResponse;
    }

    throw error;
  }
}

self.addEventListener("fetch", event => {
  const request = event.request;

  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);

  if (url.origin !== self.location.origin) {
    return;
  }

  if (
    url.pathname.endsWith("/data.json") ||
    url.pathname.includes("/data/")
  ) {
    event.respondWith(loadLatestData(request));
    return;
  }

  if (
    request.mode === "navigate" ||
    url.pathname.endsWith("/index.html")
  ) {
    event.respondWith(loadNavigation(request));
    return;
  }

  event.respondWith(
    caches.match(request).then(cachedResponse => {
      return cachedResponse || fetch(request);
    })
  );
});
