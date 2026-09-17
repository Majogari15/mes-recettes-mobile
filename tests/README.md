# Corpus OCR permanent

Ce dossier contient un corpus de sorties OCR (Tesseract.js 7), avec les
résultats attendus actuels. Objectif : mesurer objectivement si une
modification de l'analyseur OCR (`app.js`) améliore ou dégrade la
situation d'ensemble, plutôt que de corriger un cas au risque d'en
casser un autre — précisément le problème rencontré à plusieurs
reprises lors du développement de l'analyseur (versions v168 à v179).

## ⚠️ Confidentialité — à lire avant d'ajouter un cas

Un vrai incident a eu lieu pendant ce projet : une capture d'écran de
navigateur intégrée telle quelle au corpus contenait le texte OCR de la
fenêtre Chrome de l'utilisateur (onglets ouverts, favoris, nom
d'utilisateur GitHub visible), poussé par erreur dans un dépôt public.
Depuis, la structure sépare strictement :

- **`ocr-corpus/`** — cas **publiables**, versionnés dans Git. Toute
  capture d'écran de navigateur y figurant doit être une version
  **synthétique** (noms d'onglets/favoris fictifs), jamais la vraie
  capture.
- **`private-ocr-corpus/`** — vraies sorties OCR pouvant contenir des
  informations personnelles, **ignoré par Git** (voir `.gitignore` à la
  racine). Voir `private-ocr-corpus/README.md` pour la procédure
  complète avant d'y ajouter un cas.

## Contenu

- `ocr-corpus/*.json` — un fichier par cas publiable, contenant :
  - `rawText` / `layoutText` : texte OCR (réel pour une fiche recette
    sans risque, synthétique pour une capture de navigateur) ;
  - `gridText` (optionnel) : texte reconstruit par rangée puis colonne
    pour les mises en page en grille (voir `reconstructGridColumns`
    dans `app.js`) — présent seulement sur les cas de préparation en
    grille à plusieurs colonnes (fiches HelloFresh notamment) ;
  - `twoColumnIngredients` (optionnel) : liste d'ingrédients
    pré-calculée par découpage réel en 2 images verticales avec OCR
    indépendant sur chacune (voir `computeTwoColumnIngredients` dans
    `app.js`) — présent seulement sur les cas de liste d'ingrédients en
    2 colonnes (captures Marmiton à cases à cocher notamment) ;
  - `expected` : résultats attendus **actuels** — pas nécessairement
    "parfaits", mais l'état correct et connu tel qu'accepté après
    vérification (voir `notes` dans chaque fichier pour le contexte et
    les limites connues). Types de vérification disponibles :
    - `detectedSection`, `persons`, `prepTime`, `nameContains` ;
    - `ingredientCount` / `ingredientCountMax` ;
    - `keyIngredients` : ingrédients dont la présence (nom contenant
      une sous-chaîne, avec quantité et unité exactes) est vérifiée
      indépendamment de l'ordre — plus robuste qu'une égalité stricte
      de toute la liste, qui s'est révélée fragile même sur des
      données figées (l'ordre interne des mots d'un nom peut varier
      selon des détails de reconstruction sans que ce soit une vraie
      régression) ;
    - `descriptionMinLength` / `descriptionContainsAll` : vérifications
      sur le texte de préparation.
- `run_ocr_corpus.py` — démarre lui-même un serveur local temporaire
  (port libre choisi automatiquement, arrêté à la fin), fait passer
  tous les cas par le vrai code de `app.js`, et compare aux attentes.
- `test_ingredient_parsing.py` — tests unitaires ciblés sur
  `parseIngredientString` (abréviations "c. à soupe", pourcentages non
  confondus avec une quantité, détection des fractions mal reconnues
  par l'OCR) — complémentaire au corpus, adapté à des règles de format
  précises plutôt qu'à un texte de photo complet. Même fonctionnement
  autonome (serveur démarré/arrêté automatiquement).
- `test_full_merge_pipeline.py` — vérifie qu'une information de
  couverture (temps de préparation) survit jusqu'à la recette
  fusionnée finale, à travers `mergeMultiPhotoResults` — ajouté après
  un test physique où cette information semblait perdue quelque part
  entre l'OCR et le formulaire final.
- `test_section_detection.py` — tests ciblés sur `detectPhotoSection`
  et l'analyse du titre/durée dans `parseOcrRecipeText` (couverture ne
  devant pas être classée "Ingrédients" à cause d'un début de liste
  visible en bas du cadrage, durée isolée format "6h10", nettoyage du
  titre pollué par une note/nombre de commentaires) — issus de vraies
  photos Marmiton.
- `test_verification_complete.py` — 3 défauts découverts lors d'une
  vérification complète sur toutes les vraies photos du projet à la
  fois (découpage en 2 colonnes appliqué à tort à une liste à une
  seule colonne, photo d'ingrédients sans ligne d'en-tête visible,
  division silencieuse des quantités par un nombre de personnes
  deviné) — voir TESTS_NON_REGRESSION.md point 49.
- `test_shared_backup.py` — module ZIP maison (lecture/écriture, sans
  dépendance externe) et export/import au format de sauvegarde partagé
  avec l'application Windows (recettes+photos, ingrédients,
  garde-manger, personnalisations) — la compatibilité réelle avec
  l'application Windows a été vérifiée manuellement (voir
  TESTS_NON_REGRESSION.md), pas automatisable ici (tkinter indisponible
  dans cet environnement).
- `test_ingredient_reference_data.py` — protège la mise à jour des
  données de référence ingrédients (allergènes, valeurs
  nutritionnelles, traductions) importées depuis l'application Windows
  v56 (source ANSES Ciqual 2025) — voir TESTS_NON_REGRESSION.md point
  53.
- `test_standalone_timers.py` — fenêtre de minuteurs autonome
  (Accueil → Outils → Minuteur) : ouverture, ajout de plusieurs
  minuteurs, persistance en arrière-plan après fermeture de la fenêtre,
  réaffichage correct du décompte à la réouverture — voir
  TESTS_NON_REGRESSION.md point 54.
- `test_backup_reminder.py` — rappel de sauvegarde de l'accueil :
  urgence progressive (3 paliers selon l'ancienneté), préparation en
  arrière-plan du fichier, partage en un clic avec repli sur l'écran
  Sauvegarde si le partage natif n'est pas disponible — voir
  TESTS_NON_REGRESSION.md point 61.
- `test_pdf_allergens.py` — section allergènes dans l'export PDF de
  recette, absente jusqu'ici bien que le champ existe et soit affiché
  à l'écran — voir TESTS_NON_REGRESSION.md point 64.
- `test_table_ingredients.py` — extraction d'ingrédients depuis un
  vrai tableau à 2 colonnes visuelles (fiches HelloFresh), reconstruit
  à partir des coordonnées réelles des mots plutôt que du texte déjà
  linéarisé — données de coordonnées synthétiques (pas une vraie
  image) ; inclut aussi la fusion protégeant un ingrédient sans
  quantité que le tableau ne peut structurellement pas capturer, voir
  TESTS_NON_REGRESSION.md points 65 et 67.
- `test_units_migration.py` — fusion des unités "sachet"/"pot" dans
  "boîte" (reconnaissance à l'import, `containerLabel` conservant le
  mot d'origine) et migration des données déjà enregistrées (prix
  personnalisés, garde-manger, courses avec fusion des doublons,
  recette, import partagé) — voir TESTS_NON_REGRESSION.md points 76
  et 77.
- `test_photo_crop_and_comparison.py` — recadrage manuel (accessibilité,
  suivi d'un redimensionnement d'écran, préservation de la photo
  originale, conservation du résultat précédent si la ré-analyse OCR
  échoue) et durée de vie des miniatures de comparaison photo
  source/résultat — voir TESTS_NON_REGRESSION.md point 77.
  L'analyse OCR y est simulée (fonction remplacée) plutôt que réelle :
  ce test vérifie la mécanique, pas la qualité de reconnaissance,
  déjà couverte par le corpus OCR.
- `test_security_hardening.py` — `escapeHtml` échappant aussi les
  guillemets (pas seulement `&`/`<`/`>`) et `isValidPhotoField`
  vérifiant tout le format base64 jusqu'au bout, pas seulement le
  préfixe — voir TESTS_NON_REGRESSION.md point 82.
- `test_data_integrity.py` — écran de secours si IndexedDB échoue au
  démarrage, atomicité de `moveRecipeToTrash`/`restoreRecipeFromTrash`
  et de `renameIngredientName`/`mergeIngredientNames` (transaction
  unique à travers tous les entrepôts concernés, aucune mutation en
  mémoire avant confirmation de la persistance), `saveRecipeForm`
  signalant un échec d'enregistrement au lieu de le masquer, et
  `storePut`/`storeDelete` gérant `tx.onabort` — voir
  TESTS_NON_REGRESSION.md points 82 et 85.
- `test_ingredient_row_layout.py` — largeur des champs quantité/unité
  de la ligne d'ingrédient (ne devenaient plus lisibles sur un écran
  étroit), puis réduction supplémentaire de la case quantité à ~5
  caractères, arrondi à 3 décimales pour l'affichage, icône de
  suppression réduite de 30 % — voir TESTS_NON_REGRESSION.md points 82
  et 84.
- `test_ingredient_autocomplete.py` — le menu de suggestions d'un champ
  ingrédient s'affiche dès le clic dans un champ vide, pas seulement
  après avoir tapé une première lettre — voir TESTS_NON_REGRESSION.md
  point 83.
- `test_recipe_category_filter.py` — filtre par catégorie sur l'écran
  Recettes, à gauche du contrôle de tri — voir TESTS_NON_REGRESSION.md
  point 84.
- `test_recipe_form_photo_gallery.py` — le formulaire de recette et le
  journal de cuisine ("J'ai cuisiné ça !") permettent d'importer une
  photo déjà présente sur le téléphone (bouton Galerie), pas seulement
  d'en prendre une nouvelle avec l'appareil photo, et le champ associé
  se réinitialise bien après lecture pour permettre de resélectionner
  la même photo — voir TESTS_NON_REGRESSION.md points 86 et 87.
- `test_accessibility_audit.py` — audit automatisé (axe-core, fourni
  uniquement pour les tests dans `vendor/`, jamais chargé par
  l'application) des écrans principaux en thèmes clair et sombre :
  contraste des couleurs, landmarks (`<main>`/`<header>`/`<nav>`),
  titre de niveau 1 par écran — voir TESTS_NON_REGRESSION.md point 90.
- `test_performance_basic.py` — démarrage à froid, rendu et filtrage
  avec un grand volume de données (300 recettes, 500 ingrédients),
  mémoire JS utilisée — seuils larges destinés à détecter une
  régression franche, pas une certification de performance absolue —
  voir TESTS_NON_REGRESSION.md point 90.
- `test_responsive_large_screens.py` — absence de débordement
  horizontal sur des écrans plus grands qu'un téléphone (tablette
  portrait/paysage, pliable dépliée) — complète les tests existants
  limités à 390px/320px — voir TESTS_NON_REGRESSION.md point 90.
- `test_network_interruption.py` — coupure réseau simulée en cours
  d'import de recette par lien : message d'échec clair en temps
  raisonnable, pas de blocage ni d'erreur JS, application réutilisable
  après le retour du réseau — voir TESTS_NON_REGRESSION.md point 90.
- `test_pdf_exports_full.py` — les 3 exports PDF (recette seule, liste
  de courses, livre de cuisine multi-recettes) aboutissent vraiment à
  un fichier PDF valide via `doc.save()`, pas seulement au bon texte
  "dessiné" (déjà couvert par `test_pdf_allergens.py` pour la recette
  seule) — ajouté lors de l'audit de régression suivant la mise à jour
  de jsPDF, voir TESTS_NON_REGRESSION.md points 90-91.
- `test_pwa_manifest.py` — validité des 4 manifestes (fr/en/es/de) :
  icônes existantes aux bonnes dimensions, `display:"standalone"`,
  cohérence de la couleur de thème entre les manifestes et
  `index.html`, sélection du bon fichier par `manifest-loader.js` —
  voir TESTS_NON_REGRESSION.md point 92.
- `test_pwa_install_flow.py` — logique JS du bandeau d'installation
  (événement `beforeinstallprompt` simulé, clic Installer appelant
  `prompt()`, clic Non merci mémorisé et jamais réaffiché, détection du
  mode déjà installé) — voir TESTS_NON_REGRESSION.md point 92.
- `test_pwa_cold_offline.py` — vraie navigation hors-ligne "à froid"
  (service worker + cache déjà en place, puis rechargement complet
  hors connexion, y compris vers une URL avec paramètre jamais visitée
  avant), au-delà de la coupure réseau en cours d'action déjà couverte
  par `test_network_interruption.py` — voir TESTS_NON_REGRESSION.md
  point 92.
- `test_pwa_camera_permission.py` — accès réel à la caméra
  (`getUserMedia`, caméra factice Chromium) pour le scanner de QR code,
  permission accordée et refusée — voir TESTS_NON_REGRESSION.md
  point 92.
- `test_regex_dos_resilience.py` — résistance des fonctions d'analyse
  de texte maison (ingrédients, OCR) à des entrées pathologiques
  (longues répétitions ambiguës) susceptibles de provoquer un blocage
  catastrophique dans une expression régulière — voir
  TESTS_NON_REGRESSION.md point 93.
- `test_pantry_expiration.py` — date de péremption sur les articles du
  garde-manger : ajout/modification via le vrai formulaire, statuts
  expiré/bientôt/lointain/sans date, bandeau de rappel sur l'accueil,
  tri par date, survie à un aller-retour de sauvegarde locale — voir
  TESTS_NON_REGRESSION.md point 94.
- `test_barcode_pantry.py` — ajout au garde-manger par scan de
  code-barres : vrai chemin caméra (détection simulée), repli manuel,
  recherche du produit (Open Food Facts simulée, jamais le vrai
  réseau), aucun doublon créé grâce à la mémorisation du nom ET de
  l'unité choisis, survie de cette mémoire à une sauvegarde locale —
  voir TESTS_NON_REGRESSION.md point 95.
- `vendor/axe.min.js` — bibliothèque axe-core (MIT, Deque Systems),
  utilisée uniquement par `test_accessibility_audit.py` — jamais
  chargée par l'application elle-même.
- `requirements.txt` — version verrouillée de Playwright.

## Utilisation

Une seule commande, après installation initiale :

```bash
cd recipe_pwa
pip install -r tests/requirements.txt
python3 -m playwright install chromium  # une seule fois
python3 tests/run_ocr_corpus.py
```

Code de sortie 0 si tous les cas passent, 1 sinon — utilisable dans un
script ou une vérification automatisée avant chaque livraison.

## Ajouter un nouveau cas au corpus

1. **Vérifier la confidentialité** : le texte OCR contient-il autre
   chose que du contenu de recette (onglets, favoris, identifiants) ?
   Si oui, voir `private-ocr-corpus/README.md` avant toute chose.
2. Récupérer le texte OCR réel (`rawText`) et reconstruit
   (`layoutText`) — ne jamais inventer un texte approximatif pour une
   fiche recette, l'intérêt du corpus est de refléter fidèlement ce que
   Tesseract produit réellement.
3. Créer `ocr-corpus/nom_descriptif.json` avec `id`,
   `sourceDescription`, `rawText`, `layoutText`.
4. Déterminer les résultats **actuellement corrects** en exécutant le
   pipeline dessus, et les inscrire dans `expected` — de préférence
   avec des `keyIngredients`/`descriptionContainsAll` plutôt que de
   simples comptages, qui masquent facilement une vraie régression sur
   le contenu (quantité, unité) tout en laissant le compte inchangé.
5. Ajouter des `notes` expliquant le contexte et les limites connues.
6. Relancer `run_ocr_corpus.py` pour confirmer que ce nouveau cas passe,
   puis committer le fichier avec le reste des changements.

## Limites connues

- Ce corpus fige le texte OCR à un instant donné — il ne re-teste
  jamais Tesseract lui-même (dont la reconnaissance peut varier
  légèrement selon l'appareil et la variante WASM utilisée, comme
  observé à plusieurs reprises pendant ce projet). Il vérifie
  uniquement que l'**analyseur** (`app.js`) traite correctement un
  texte OCR donné, connu et stable — le test physique sur un vrai
  appareil reste nécessaire pour valider la chaîne complète, OCR
  compris.
- Les assertions `keyIngredients`/`descriptionContainsAll` sont plus
  robustes qu'un simple comptage, mais ne remplacent pas une relecture
  humaine complète du résultat — elles détectent une classe de
  régressions (quantité/unité perdue, mot-clé de contenu absent), pas
  toutes les erreurs possibles.

