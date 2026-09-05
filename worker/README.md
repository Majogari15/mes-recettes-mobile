# Worker Cloudflare — `cloudflare-worker.js`

Ce fichier est le code source du Worker Cloudflare utilisé pour l'import
de recettes par lien (proxy CORS personnel). Il est conservé ici pour :

- vérifier que le Worker réellement déployé correspond à cette version ;
- pouvoir restaurer son code si la configuration Cloudflare est perdue ;
- suivre ses modifications en même temps que celles de l'application.

**Ce fichier n'est pas exécuté par l'application** — il doit être déployé
manuellement sur Cloudflare Workers après chaque modification. Il n'est
jamais inclus dans le cache du service worker de la PWA (`sw.js`).

Adresse actuellement configurée dans l'application (voir
`CLOUDFLARE_WORKER_URL` dans `app.js`) :
`https://mes-recettes-proxy.fabricemoritel.workers.dev`
