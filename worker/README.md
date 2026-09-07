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

## Limitation de débit (Rate Limiting)

Le Worker limite maintenant le nombre de requêtes par adresse IP (30
par minute par défaut) — une protection contre un usage automatisé
abusif, en plus de la vérification d'origine déjà en place.

**Tant que cette configuration n'est pas faite, le Worker continue de
fonctionner normalement, sans aucune limitation** — ce n'est donc pas
urgent, mais recommandé avant une diffusion publique importante.

### Wrangler — seule méthode qui fonctionne réellement

⚠️ Une version précédente de ce document suggérait une configuration
possible depuis le tableau de bord Cloudflare (Settings → Bindings).
**C'était une erreur** : la documentation officielle de Cloudflare
indique explicitement que les liaisons Rate Limiting ne sont
actuellement pas visibles dans le tableau de bord, quelle que soit sa
langue. Wrangler est la seule méthode qui fonctionne.

Depuis ce dossier (`worker/`), avec Node.js installé :

```
npx wrangler login
```

(la première fois uniquement — ouvre votre navigateur pour autoriser
l'accès à votre compte Cloudflare)

```
npx wrangler deploy
```

Ceci lit `wrangler.toml`, crée la liaison `RATE_LIMITER`, et met à jour
le Worker déjà en ligne avec le code qui l'utilise. Si l'identifiant
`namespace_id = "1001"` du fichier est déjà utilisé par un autre Worker
sur votre compte, changez-le pour n'importe quel autre nombre entier.

### Vérifier que ça fonctionne

Une fois configuré, importer normalement quelques recettes doit
continuer à fonctionner sans rien changer côté application — la
limitation ne se déclenche qu'en cas d'usage largement anormal (plus
de 30 requêtes en une minute depuis la même adresse IP).

