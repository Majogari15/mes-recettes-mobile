// Service worker : met en cache tous les fichiers de l'application au premier
// chargement, pour qu'elle continue de fonctionner sans connexion internet
// ensuite (les données elles-mêmes sont stockées séparément, dans IndexedDB,
// géré directement par app.js).

const CACHE_NAME = "mes-recettes-cache-v45";
const FILES_TO_CACHE = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./i18n.js",
  "./manifest.json",
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
];
// Ressources externes indispensables (ex. génération de PDF) : mises en
// cache elles aussi dès le premier chargement, pour continuer de
// fonctionner hors connexion ensuite malgré leur origine différente.
const CROSS_ORIGIN_TO_CACHE = [
  "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.0.3/qrcode.min.js",
  "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js",
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
  // (ex. jsPDF) : les autres suivent leur cours normalement, échec
  // inclus, sans être remplacées par une page de l'application.
  if (!isCrossOriginAllowed && new URL(event.request.url).origin !== self.location.origin) return;
  // Ignore aussi tout ce qui n'est pas une simple lecture (GET) : les
  // requêtes de mutation n'ont pas à être mises en cache.
  if (event.request.method !== "GET") return;

  // Stratégie "cache d'abord, réseau en repli" : rapide, et fonctionne
  // même hors connexion une fois le premier chargement effectué. Pour une
  // navigation (ouverture de page), on retombe sur index.html si tout
  // échoue ; pour les autres ressources, on laisse l'échec se produire
  // normalement plutôt que de le masquer avec un mauvais contenu.
  const isNavigation = event.request.mode === "navigate";
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).catch(() => {
        if (isNavigation) return caches.match("./index.html");
        return Response.error();
      });
    })
  );
});
