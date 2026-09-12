// Service worker : met en cache tous les fichiers de l'application au premier
// chargement, pour qu'elle continue de fonctionner sans connexion internet
// ensuite (les données elles-mêmes sont stockées séparément, dans IndexedDB,
// géré directement par app.js).

const CACHE_NAME = "mes-recettes-cache-v205";
const FILES_TO_CACHE = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./i18n.js",
  "./manifest.json",
  "./sw-register-early.js",
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
  // Tesseract.js (v7.0.0, verrouillé) — désormais entièrement local,
  // plus aucune dépendance à un CDN externe. Les 6 variantes du moteur
  // WASM sont toutes mises en cache (Tesseract choisit lui-même celle
  // compatible avec l'appareil au moment de l'exécution) ; voir
  // lib/LICENSES.md pour le détail des licences.
  //
  // Les DONNÉES DE LANGUE (lib/tesseract/lang/*.traineddata.gz) ne sont
  // volontairement PAS listées ici : les précharger toutes alourdirait
  // le tout premier chargement de l'application d'environ 40 Mo, pour
  // des langues qu'une personne n'utilisera peut-être jamais. Chacune
  // n'est téléchargée qu'au premier import photo dans cette langue,
  // puis mise en cache par ce même service worker (voí l'écouteur
  // "fetch" plus bas) pour les imports suivants, y compris hors
  // connexion.
  "./lib/tesseract/tesseract.min.js",
  "./lib/tesseract/worker.min.js",
  "./lib/tesseract/core/tesseract-core.wasm.js",
  "./lib/tesseract/core/tesseract-core-simd.wasm.js",
  "./lib/tesseract/core/tesseract-core-lstm.wasm.js",
  "./lib/tesseract/core/tesseract-core-simd-lstm.wasm.js",
  "./lib/tesseract/core/tesseract-core-relaxedsimd.wasm.js",
  "./lib/tesseract/core/tesseract-core-relaxedsimd-lstm.wasm.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(FILES_TO_CACHE))
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
  const requestOrigin = new URL(event.request.url).origin;
  // Ignore aussi tout ce qui n'est pas une simple lecture (GET) : les
  // requêtes de mutation n'ont pas à être mises en cache.
  if (event.request.method !== "GET") return;

  // Cas particulier : polices Google Fonts. Contrairement aux
  // bibliothèques JS/JSON/WASM (Tesseract, jsPDF, jsQR), impossible de
  // les embarquer directement dans ce projet au moment de sa
  // construction — leurs fichiers binaires ne peuvent pas être
  // transférés de façon fiable dans l'environnement utilisé pour
  // développer cette application (risque de corruption). Repli
  // pragmatique : mise en cache à l'exécution — après un premier
  // chargement réussi (connecté), la police reste disponible hors
  // connexion pour toutes les fois suivantes. Un tout premier lancement
  // hors connexion, lui, affichera la police système par défaut le
  // temps d'une future connexion réussie.
  const isGoogleFonts = requestOrigin === "https://fonts.googleapis.com" || requestOrigin === "https://fonts.gstatic.com";
  if (isGoogleFonts) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request)
          .then((res) => {
            if (res.ok) {
              const resClone = res.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
            }
            return res;
          })
          .catch(() => Response.error());
      })
    );
    return;
  }

  // Ne jamais intercepter les autres requêtes vers un domaine externe :
  // elles suivent leur cours normalement, échec inclus, sans être
  // remplacées par une page de l'application. Tesseract étant
  // désormais entièrement local, plus aucune autre requête cross-origin
  // n'a besoin d'être mise en cache ici.
  if (requestOrigin !== self.location.origin) return;

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
  // rarement d'une version à l'autre. Si absent du cache (ex. données
  // de langue Tesseract, volontairement téléchargées à la demande
  // plutôt que préchargées — voir FILES_TO_CACHE plus haut), le
  // résultat est mis en cache après ce premier téléchargement, pour que
  // les usages suivants — y compris hors connexion — n'aient plus
  // besoin du réseau.
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((res) => {
          if (res.ok) {
            const resClone = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
          }
          return res;
        })
        .catch(() => Response.error());
    })
  );
});

// Clic sur une notification (ex. minuteur de cuisine terminé) : ramène
// au premier plan une fenêtre déjà ouverte de l'application plutôt que
// d'en ouvrir une nouvelle à chaque fois, ou en ouvre une si aucune
// n'est disponible. Si la notification indique une recette précise
// (voir showTimerNotification dans app.js), navigue vers elle avec un
// paramètre d'URL que app.js interprète au démarrage pour rouvrir
// directement le mode cuisine correspondant, plutôt que de simplement
// ramener au premier plan l'écran où l'utilisateur se trouvait avant.
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const recipeId = event.notification.data && event.notification.data.recipeId;
  const targetUrl = recipeId ? `./?openRecipe=${encodeURIComponent(recipeId)}` : "./";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ("focus" in client) {
          if (recipeId && "postMessage" in client) client.postMessage({ type: "openRecipe", recipeId });
          return client.focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(targetUrl);
    })
  );
});
