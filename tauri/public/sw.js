const CACHE_VERSION = 'v2';
const CACHE_NAME = `pdf-resizer-${CACHE_VERSION}`;
const BASE_PATH = '/';

// В массиве оставляем только те файлы, которые РЕАЛЬНО лежат в твоей папке Tauri/public
const FILES_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/icon.png',
];

// Install - кеширует необходимые файлы
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(FILES_TO_CACHE))
      .then(() => self.skipWaiting())
      .catch((err) => {
        console.warn('Cache.addAll error (проверь, все ли файлы существуют в public):', err);
      })
  );
});

// Activate - полностью очищает старое хранилище
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => caches.delete(cacheName))
        )
      )
      .then(() => self.clients.claim())
  );
});

// Fetch - для страницы сначала сеть (network-first), для остального - stale-while-revalidate
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Обрабатываем только запросы в рамках приложения
  if (!url.pathname.startsWith(BASE_PATH)) {
    return;
  }

  // Навигационные запросы (открытие страницы): всегда сначала сеть,
  // чтобы пользователь получал свежий index.html. Кэш - только fallback оффлайн.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (!response || response.status !== 200) {
            return response;
          }

          // Обновляем закешированную страницу свежим ответом
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put('/', responseToCache);
            cache.put('/index.html', responseToCache);
          });

          return response;
        })
        .catch(() =>
          caches.match(request).then((response) => {
            if (response) {
              return response;
            }
            return caches.match('/');
          })
        )
    );
    return;
  }

  // Остальные запросы: отдаём кэш сразу, а в фоне обновляем из сети
  event.respondWith(
    caches.match(request).then((cached) => {
      const networkFetch = fetch(request)
        .then((response) => {
          if (!response || response.status !== 200) {
            return response;
          }

          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });

          return response;
        })
        .catch(() => cached);

      return cached || networkFetch;
    })
  );
});
