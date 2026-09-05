// Service worker : met en cache tous les fichiers de l'application au premier
// chargement, pour qu'elle continue de fonctionner sans connexion internet
// ensuite (les données elles-mêmes sont stockées séparément, dans IndexedDB,
// géré directement par app.js).

const CACHE_NAME = "mes-recettes-cache-v151";
const FILES_TO_CACHE = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./i18n.js",
  "./manifest.json",
  "./manifest-loader.js",
  "./manifest-en.json",
  "./manifest-es.json",
  "./manifest-de.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./data/ingredient_allergenes.json",
  "./data/valeurs_nutritionnelles.json",
  "./data/ingredients_par_defaut.json",
  "./data/ingredient_translations_en.json",
  "./data/ingredient_translations_es.json",
  "./data/ingredient_translations_de.json",
  "./data/ingredient_substitutions.json",
  "./data/ingredient_substitutions_en.json",
  "./data/ingredient_substitutions_es.json",
  "./data/ingredient_substitutions_de.json",
  "./lib/qrcode-generator.js",
  "./lib/jsQR.js",
  "./lib/jspdf.umd.min.js",
];
// Ressources externes indispensables (ex. reconnaissance de texte par
// photo) : mises en cache elles aussi dès le premier chargement, pour
// continuer de fonctionner hors connexion ensuite malgré leur origine
// différente. jsQR et jsPDF sont désormais des fichiers locaux (voir
// FILES_TO_CACHE ci-dessus), seul Tesseract reste externe pour l'instant.
const CROSS_ORIGIN_TO_CACHE = [
  "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(FILES_TO_CACHE).then(() =>
        // Chaque ressource externe est mise en cache séparément (avec
        // "no-cors" en repli) : si l'une d'elles échoue (ex. hors ligne
        // dès le premier lancement), ça ne doit pas empêcher le reste de
        // l'application de s'installer correctement.
        Promise.all(
          CROSS_ORIGIN_TO_CACHE.map((url) =>
            fetch(url, { mode: "cors" })
              .then((res) => cache.put(url, res))
              .catch(() => {})
          )
        )
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const isCrossOriginAllowed = CROSS_ORIGIN_TO_CACHE.includes(event.request.url);
  // Ne jamais intercepter les requêtes vers un autre domaine (ex. Google
  // Fonts), sauf celles explicitement mises en liste blanche ci-dessus
  // (ex. Tesseract) : les autres suivent leur cours normalement, échec
  // inclus, sans être remplacées par une page de l'application.
  if (!isCrossOriginAllowed && new URL(event.request.url).origin !== self.location.origin) return;
  // Ignore aussi tout ce qui n'est pas une simple lecture (GET) : les
  // requêtes de mutation n'ont pas à être mises en cache.
  if (event.request.method !== "GET") return;

  const isNavigation = event.request.mode === "navigate";
  const pathname = new URL(event.request.url).pathname;
  // Ces trois fichiers contiennent la logique de l'application et sont
  // les seuls à vraiment poser problème s'ils restent périmés en cache
  // (c'est ce qui obligeait auparavant à vider le cache manuellement
  // après chaque mise à jour) — ils essaient donc toujours le réseau
  // en premier, avec le cache uniquement en repli si hors connexion.
  const isCriticalFile = isNavigation || pathname.endsWith("/app.js") || pathname.endsWith("/i18n.js") || pathname.endsWith("/index.html");

  if (isCriticalFile) {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          const resClone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
          return res;
        })
        .catch(() =>
          caches.match(event.request).then((cached) => {
            if (cached) return cached;
            return isNavigation ? caches.match("./index.html") : Response.error();
          })
        )
    );
    return;
  }

  // Pour tout le reste (images, données de référence, bibliothèques
  // externes) : cache d'abord — plus rapide, et ces fichiers changent
  // rarement d'une version à l'autre.
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).catch(() => Response.error());
    })
  );
});
