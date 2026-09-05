// ============================================================
// Worker Cloudflare — proxy léger pour l'import de recettes
// Mes Recettes, Mes Courses
// ============================================================
// Rôle : récupérer le HTML d'une page de recette ou l'image qui
// l'illustre, à la place de l'application (pour contourner la
// restriction CORS des navigateurs), et le renvoyer tel quel.
// L'analyse du contenu HTML (recherche de la recette) reste
// entièrement faite dans l'application elle-même — ce Worker ne fait
// que la transmission, ce qui le garde rapide et largement dans les
// limites du forfait gratuit de Cloudflare.
//
// Protections mises en place :
// - seules les adresses en https:// sont acceptées, sans identifiants
//   (utilisateur/mot de passe) ni port autre que 443
// - les adresses locales/privées sont refusées, y compris en IPv6 et
//   y compris après une éventuelle redirection (protection contre un
//   détournement du Worker pour sonder un réseau interne)
// - le statut HTTP de la page récupérée est vérifié (une erreur ou un
//   blocage renvoyés par le site distant n'est plus confondu avec une
//   vraie réussite)
// - un seul délai maximal couvre toute l'opération (connexion,
//   redirections, ET lecture complète du contenu), pas seulement la
//   réception des en-têtes
// - taille maximale de la réponse, différente pour le HTML et les
//   images, vérifiée à la fois avant et après téléchargement
// - en-tête CORS et vérification de l'origine limités au domaine de
//   l'application
// - seul le contenu HTML/texte ou une image JPEG/PNG/WebP est accepté

// ⚠️ À MODIFIER : remplacez par l'adresse exacte de votre application
// une fois mise en ligne (sans "/" à la fin).
const ALLOWED_ORIGIN = "https://majogari15.github.io";

const MAX_HTML_SIZE = 3 * 1024 * 1024; // 3 Mo, largement suffisant pour une page de recette
const MAX_IMAGE_SIZE = 8 * 1024 * 1024; // 8 Mo, généreux pour une photo de recette
const FETCH_TIMEOUT_MS = 25000;
const MAX_REDIRECTS = 5;
const USER_AGENT = "Mozilla/5.0 (compatible; MesRecettesBot/1.0; +https://majogari15.github.io/mes-recettes-mobile/)";
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

function isPrivateOrLocalHost(hostname) {
  // Une adresse IPv6 issue de URL().hostname garde ses crochets
  // (ex. "[::1]") : sans les retirer d'abord, aucune des comparaisons
  // ci-dessous ne pouvait jamais correspondre, laissant passer les
  // adresses IPv6 locales/privées sans être bloquées.
  const lower = hostname.toLowerCase().replace(/^\[|\]$/g, "");
  if (lower === "localhost" || lower.endsWith(".local")) return true;
  const ipv4Match = lower.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (ipv4Match) {
    const a = Number(ipv4Match[1]);
    const b = Number(ipv4Match[2]);
    if (a === 127) return true; // boucle locale
    if (a === 10) return true; // réseau privé 10.0.0.0/8
    if (a === 172 && b >= 16 && b <= 31) return true; // réseau privé 172.16.0.0/12
    if (a === 192 && b === 168) return true; // réseau privé 192.168.0.0/16
    if (a === 169 && b === 254) return true; // adresses locales-lien
    if (a === 0) return true;
  }
  if (lower === "::1" || lower.startsWith("fe80:") || lower.startsWith("fc") || lower.startsWith("fd")) return true;
  return false;
}

// Rassemble tous les contrôles à appliquer sur une adresse cible — à
// la fois pour l'adresse d'origine et pour chaque redirection
// éventuelle, afin qu'aucune étape ne puisse contourner une
// vérification appliquée seulement au tout début.
function validateTargetUrl(url) {
  if (url.protocol !== "https:") return "Only https URLs are allowed";
  if (url.username || url.password) return "Credentials in URL are not allowed";
  if (url.port && url.port !== "443") return "Port not allowed";
  if (isPrivateOrLocalHost(url.hostname)) return "Refused target host";
  return null;
}

// Petite erreur porteuse d'un statut HTTP à renvoyer, pour éviter de
// dupliquer le choix du code d'erreur à chaque endroit où une
// vérification peut échouer.
class WorkerError extends Error {
  constructor(message, httpStatus) {
    super(message);
    this.httpStatus = httpStatus;
  }
}

// Récupère le contenu d'une adresse (page HTML ou image), en suivant
// les redirections manuellement (pour revalider chaque nouvelle
// destination) et sous un seul délai global qui couvre toute
// l'opération — y compris la lecture complète du contenu, pas
// seulement la réception des en-têtes de réponse. Sans ça, un serveur
// distant pourrait répondre rapidement puis ralentir volontairement
// l'envoi du corps de la réponse pour dépasser le délai prévu sans
// jamais être interrompu.
//
// Renvoie soit { kind: "text", data, contentType }, soit
// { kind: "binary", data, contentType } — la distinction est
// importante : convertir une image en texte la corromprait, il faut
// la lire comme des données binaires brutes (ArrayBuffer).
async function fetchRecipeContent(targetUrl) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    let currentUrl = targetUrl;
    let response = null;
    for (let hop = 0; hop <= MAX_REDIRECTS; hop++) {
      response = await fetch(currentUrl.toString(), {
        signal: controller.signal,
        redirect: "manual",
        headers: { "User-Agent": USER_AGENT },
      });

      if (response.status >= 300 && response.status < 400) {
        const location = response.headers.get("location");
        if (!location) throw new WorkerError("Redirect without location", 502);
        let nextUrl;
        try {
          nextUrl = new URL(location, currentUrl);
        } catch (e) {
          throw new WorkerError("Invalid redirect location", 502);
        }
        const validationError = validateTargetUrl(nextUrl);
        if (validationError) throw new WorkerError(validationError, 400);
        currentUrl = nextUrl;
        response = null;
        continue;
      }
      break;
    }
    if (!response) throw new WorkerError("Too many redirects", 502);

    if (!response.ok) {
      throw new WorkerError("Upstream HTTP " + response.status, 502);
    }

    const contentType = response.headers.get("content-type") || "";
    const isHtmlLike = contentType.includes("text/html") || contentType.includes("text/plain");
    const isAllowedImage = ALLOWED_IMAGE_TYPES.some((t) => contentType.includes(t));

    if (!isHtmlLike && !isAllowedImage) {
      throw new WorkerError("Unsupported content type", 415);
    }

    const maxSize = isAllowedImage ? MAX_IMAGE_SIZE : MAX_HTML_SIZE;
    const contentLength = Number(response.headers.get("content-length") || 0);
    if (contentLength > maxSize) {
      throw new WorkerError("Response too large", 413);
    }

    if (isAllowedImage) {
      const buffer = await response.arrayBuffer();
      if (buffer.byteLength > maxSize) {
        throw new WorkerError("Response too large", 413);
      }
      return { kind: "binary", data: buffer, contentType };
    }

    const html = await response.text();
    if (html.length > maxSize) {
      throw new WorkerError("Response too large", 413);
    }
    return { kind: "text", data: html, contentType: "text/html; charset=utf-8" };
  } finally {
    clearTimeout(timeoutId);
  }
}

export default {
  async fetch(request) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
      "Access-Control-Allow-Methods": "GET, OPTIONS",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }
    if (request.method !== "GET") {
      return new Response("Method not allowed", { status: 405, headers: corsHeaders });
    }

    // Vérifie l'origine de la requête entrante quand elle est fournie
    // — une protection raisonnable contre une utilisation détournée
    // depuis un autre site web, même si elle ne protège pas contre un
    // script qui n'envoie simplement pas cet en-tête (ce qui demande
    // plutôt une limitation du nombre de requêtes, à ajouter avant une
    // diffusion publique importante).
    const requestOrigin = request.headers.get("Origin");
    if (requestOrigin && requestOrigin !== ALLOWED_ORIGIN) {
      return new Response("Origin not allowed", { status: 403, headers: corsHeaders });
    }

    const reqUrl = new URL(request.url);
    const target = reqUrl.searchParams.get("url");
    if (!target) {
      return new Response("Missing url parameter", { status: 400, headers: corsHeaders });
    }
    // Mesurée sur l'adresse cible déjà décodée (searchParams.get() la
    // décode automatiquement) — mesurer l'URL complète du Worker
    // gonflerait artificiellement la longueur à cause de l'encodage
    // (%3A, %2F...). 2048 caractères reste largement suffisant pour une
    // vraie page de recette, tout en empêchant un abus trivial.
    if (target.length > 2048) {
      return new Response("URL too long", { status: 414, headers: corsHeaders });
    }

    let targetUrl;
    try {
      targetUrl = new URL(target);
    } catch (e) {
      // Message enrichi avec le détail technique exact et la longueur
      // reçue — un simple "Invalid url" ne permettait pas de comprendre
      // pourquoi une adresse par ailleurs valide pouvait être refusée.
      return new Response(`Invalid url (${e.message}, length=${target.length})`, { status: 400, headers: corsHeaders });
    }
    const validationError = validateTargetUrl(targetUrl);
    if (validationError) {
      return new Response(validationError, { status: 400, headers: corsHeaders });
    }

    try {
      const content = await fetchRecipeContent(targetUrl);
      return new Response(content.data, {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": content.contentType },
      });
    } catch (e) {
      const status = e instanceof WorkerError ? e.httpStatus : 502;
      return new Response(e.message || "Fetch failed", { status, headers: corsHeaders });
    }
  },
};
