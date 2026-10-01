# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Pas de build, pas de lint, pas de `package.json` : PWA en JavaScript vanilla pur (`app.js`, `i18n.js`, `styles.css`, `index.html`), sans étape de compilation.

Serveur local de dev :
```
python3 -m http.server 8000
```

Tests (Playwright + Python, un fichier = un scénario, chacun démarre et arrête son propre serveur local sur un port libre — pas de runner central) :
```
pip install -r tests/requirements.txt
python3 -m playwright install chromium   # une seule fois
python3 tests/test_nom_du_fichier.py     # exécute un seul test
```
Code de sortie 0 = tout passe, 1 = échec. Aucune commande "run all" : chaque fichier `tests/test_*.py` s'exécute individuellement.

## Architecture

### Fichier unique de logique
Toute la logique applicative vit dans `app.js` (~700 Ko, aucun découpage en modules). `i18n.js` contient les traductions (fr/en/es/de). Ne pas chercher de structure par dossiers/composants : tout est dans ces deux fichiers.

### Stockage : IndexedDB
`DB_NAME = "mes-recettes-db"`, `DB_VERSION = 7`, ouverture via `openDB()` (singleton `dbInstance`). Object stores créés dans `onupgradeneeded` :
`recipes`, `shopping`, `pantry`, `ingredients` (keyPath `name`), `ingredientOverrides` (keyPath `name`), `menus`, `planTemplates`, `planHistory`, `trash`, `savedShoppingLists`, `kv` (magasin générique clé/valeur).

### Catalogue d'ingrédients basé sur des id stables
Système central, construit sur plusieurs fichiers `data/*.json` liés entre eux par un `id` numérique stable (jamais recyclé, même si un ingrédient est renommé ou supprimé) :
- `data/ingredients_catalogue.json` — `[{id, fr}]`, ~10 000 entrées, source de vérité des noms français.
- `data/ingredient_translations_{en,es,de}.json` — traductions par id.
- `data/ingredient_allergenes.json` — taxonomie stricte à 14 valeurs, par id.
- `data/valeurs_nutritionnelles.json` — kcal/protéines/glucides/lipides par id (+ métadonnées de provenance optionnelles).
- `data/ingredient_substitutions.json` + 3 fichiers de langue — substitutions par id.

Chargés en globals côté app : `INGREDIENT_CATALOGUE`, `CATALOGUE_BY_ID`, `CATALOGUE_ID_BY_NAME`, `ALLERGEN_DB`, `NUTRITION_DB`, `SUBSTITUTIONS_DB`/`SUBSTITUTIONS_BY_INGREDIENT_ID`, `INGREDIENT_TRANSLATIONS`/`INGREDIENT_REVERSE_TRANSLATIONS`.

Le lien nom↔id d'un utilisateur (qui peut renommer ses ingrédients localement) est maintenu séparément dans `state.ingredientCatalogIds` (nom normalisé → id) et `state.ingredientNameByCatalogId` (id → nom actuel), reconstruit/mis à jour par les fonctions autour de la ligne ~6820 de `app.js`. Un renommage met à jour ce lien sans casser l'association aux données du catalogue (allergènes, nutrition, substitutions restent attachées au même id).

Point important pour toute évolution du catalogue : ne jamais réutiliser un id déjà attribué, même après suppression d'une entrée — le lien nom↔id d'un utilisateur existant en dépend.

Les nouvelles entrées du catalogue arrivent automatiquement chez les utilisateurs existants au démarrage (`addNewCatalogueEntries`) : la clé kv `knownCatalogueIds` mémorise les ids déjà proposés, pour ne jamais réajouter un ingrédient supprimé volontairement. Ne pas vider cette clé.

### Rendu : `render()` + `state.screen`
Un seul point d'entrée de rendu (`function render()`, ligne ~952) qui vide `app.innerHTML` puis dispatche sur `state.screen` via un `switch` (`home`, `recipes`, `recipe`, `form`, `shopping`, `pantry`, `ingredients`, `ingredientDuplicates`, `backup`, `diagnostic`, etc.), chaque cas appelant une fonction `renderXxx()` dédiée qui retourne un élément DOM. Changer d'écran = modifier `state.screen` puis rappeler `render()`. Pas de framework, pas de virtual DOM : chaque `render()` reconstruit tout le contenu de `<main>`.

Les écrans dont le calcul est coûteux (ex. `renderIngredientDuplicates`, qui lance `findSimilarIngredientPairs` sur tout le catalogue) affichent un état de chargement puis diffèrent le calcul via `setTimeout(fn, 0)` pour laisser peindre cet état avant de bloquer le thread principal — pattern à réutiliser pour tout nouvel écran manipulant le catalogue complet (~10 000 entrées).

### Détection de similarité/doublons
`findSimilarIngredientPairs` et `findClosestIngredientMatch` (recherche "vouliez-vous dire") partagent le même pipeline d'optimisation, nécessaire depuis le passage du catalogue de ~1000 à ~10 000 entrées : regroupement par première lettre, fenêtre de longueur, préfiltre par coefficient de Dice sur les bigrammes (rapide) avant le calcul exact `sequenceMatcherRatio` (coûteux, type Ratcliff/Obershelp). Tout changement à l'un de ces seuils doit être revérifié sur les cas documentés dans `tests/test_ingredient_duplicates.py` (pluriels irréguliers français, fautes de frappe en 2e lettre, doublons exacts post-normalisation).

### Service worker et cache
`sw.js` gère un cache par version : `CACHE_NAME` = `${CACHE_PREFIX}vNNN`, à incrémenter à chaque commit qui touche un fichier mis en cache (sinon les utilisateurs restent bloqués sur l'ancienne version hors ligne). Incrémenter `APP_VERSION` (app.js, numéro affiché à l'utilisateur) au même numéro — vérifié par `tests/test_version_sync.py`. Trois catégories de stratégie de cache distinctes dans le `fetch` listener : fichiers critiques (`app.js`, `i18n.js`, `index.html`, navigation) en réseau d'abord avec repli cache ; fichiers JSON de référence (`data/*.json`) en stale-while-revalidate ; tout le reste en cache d'abord.

### Proxy CORS externe
`worker/cloudflare-worker.js` (documenté dans `worker/README.md`) sert de proxy CORS pour l'import de recette depuis une URL. Déployé manuellement via Wrangler, hors du service worker de l'app, URL codée en dur dans `app.js` (`CLOUDFLARE_WORKER_URL`). Ce n'est pas exécuté ni buildé par ce dépôt.

### Corpus de tests OCR : séparation stricte public/privé
`tests/ocr-corpus/` (cas synthétiques, capture d'écran de navigateur, publiable) est strictement séparé de `tests/private-ocr-corpus/` (sorties OCR réelles pouvant contenir des données personnelles, gitignored). Ne jamais déplacer de contenu du second vers le premier sans vérification manuelle — un incident de fuite (données d'onglets/marque-pages/nom d'utilisateur GitHub réels) s'est déjà produit par le passé. Voir `tests/README.md`.
