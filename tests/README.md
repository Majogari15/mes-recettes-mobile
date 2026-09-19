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
  dans cet environnement). Le test "remplacer tout" laisse une recette
  différente en place avant l'import et vérifie sa disparition
  ensuite (ne vide plus lui-même la base au préalable — l'ancienne
  version masquait ainsi le bug du point 101 ci-dessous).
- `test_external_audit_fixes_round2.py` — second audit externe (autre
  IA) : mode cuisine (quantités recalculées selon les convives),
  import ZIP tout-ou-rien (une entrée invalide n'applique plus rien),
  faux fichier ZIP rejeté explicitement, garde-manger ZIP (date de
  péremption conservée, articles de même nom mais unité différente non
  écrasés), service worker (erreur HTTP n'empoisonnant plus le cache,
  nettoyage à l'activation limité à cette app), fuseau horaire de la
  date de péremption, stock non augmenté après un échec d'écriture,
  glisser-déposer accessible au clavier, libellé nutrition "par
  personne" — voir TESTS_NON_REGRESSION.md point 101.
- `test_external_audit_fixes_round3.py` — troisième audit externe
  (deux autres IA) : vraie atomicité de l'import ZIP (une seule
  transaction IndexedDB multi-entrepôts couvrant toutes les sections,
  protège aussi contre un échec pendant l'écriture elle-même, pas
  seulement une donnée invalide détectée à l'avance), validation de
  forme complète (ingredients.json/personnalisations rejetés s'ils
  n'ont pas la forme attendue, même si le JSON est syntaxiquement
  valide), date de péremption restaurée invalide (ne plante plus
  l'affichage, nettoyée à l'import), date calendaire impossible (31
  février) qui ne bascule plus silencieusement sur une autre date —
  voir TESTS_NON_REGRESSION.md point 102.
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
  Émule `prefers-reduced-motion: reduce` depuis le point 110, pour
  éviter une fausse alerte "color-contrast" intermittente causée par
  l'animation d'entrée des fenêtres modales (mesure de contraste
  capturée en plein fondu selon le timing) — voir le détail au point
  110.
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
  `index.html`, sélection du bon fichier par `manifest-loader.js`,
  absence de la clé `orientation` (laisse le choix à l'utilisateur),
  présence d'au moins une capture d'écran "wide" en plus des "narrow"
  (dimensions et ratio ≤2:1 vérifiés pour toutes), favicon 32×32
  dédiée présente et aux bonnes dimensions — voir
  TESTS_NON_REGRESSION.md points 92 et 100.
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
  (`getUserMedia`, caméra factice Chromium) pour le scanner de QR code
  et le scan de code-barres, permission accordée et refusée, ainsi que
  le message d'erreur spécifique à chaque cause réelle (permission
  désactivée / aucune caméra / caméra occupée par une autre
  application) — voir TESTS_NON_REGRESSION.md points 92 et 98.
- `test_regex_dos_resilience.py` — résistance des fonctions d'analyse
  de texte maison (ingrédients, OCR) à des entrées pathologiques
  (longues répétitions ambiguës) susceptibles de provoquer un blocage
  catastrophique dans une expression régulière — voir
  TESTS_NON_REGRESSION.md point 93.
- `test_pantry_expiration.py` — date de péremption sur les articles du
  garde-manger : ajout/modification via le vrai formulaire, saisie 6
  chiffres avec "/" automatiques et validation (date incomplète ou
  calendairement invalide), statuts expiré/bientôt/lointain/sans
  date, bandeau de rappel sur l'accueil, tri par date, survie à un
  aller-retour de sauvegarde locale — voir TESTS_NON_REGRESSION.md
  points 94 et 97.
- `test_barcode_pantry.py` — ajout au garde-manger par code-barres :
  vrai chemin caméra (détection simulée), import depuis une photo déjà
  prise (détection simulée, y compris aucun code reconnu et détecteur
  natif indisponible), repli manuel, recherche du produit (Open Food
  Facts simulée, jamais le vrai réseau), aucun doublon créé grâce à la
  mémorisation du nom ET de l'unité choisis, survie de cette mémoire à
  une sauvegarde locale — voir TESTS_NON_REGRESSION.md points 95-96.
  Depuis le point 106, un rescan d'un code-barres connu ouvre bien le
  formulaire pré-rempli (nom/unité déjà connus, date de péremption
  saisissable) au lieu d'ajouter directement et silencieusement comme
  avant. Depuis le point 107 (retour de l'utilisateur : un premier
  préremplissage à "ancien total + 1" était trompeur), la case
  quantité représente combien on vient d'EN AJOUTER (préremplie à 1,
  jamais l'ancien total), additionnée au stock existant seulement à
  l'enregistrement — vérifié sur le cas exact signalé (2 déjà présents
  + 2 ajoutés = 4, jamais écrasé à 2). Depuis le point 108, un code
  saisi manuellement de longueur correcte (8/12/13 chiffres) mais de
  clé de contrôle EAN invalide est refusé avant toute requête réseau
  (vérifié en interceptant les requêtes) ; un EAN-8 et un UPC-A valides
  restent bien acceptés. Utilise `tests/fixtures/tiny_blank.png`
  (image minimale, son contenu réel n'a aucune importance puisque le
  détecteur est simulé).
- `test_barcode_rotation_retry.py` — import de code-barres depuis une
  photo qui n'est pas droite (signalé par l'utilisateur avec 4 vraies
  photos toutes prises de travers) : `decodeBarcodeImageFile()` essaie
  désormais l'image telle que prise puis 3 rotations supplémentaires
  (90/180/270°) avant d'abandonner. Détecteur simulé (le vrai
  `BarcodeDetector` n'existe pas dans ce Chromium de test — vérifié
  directement) : réussite au 1er essai sans rotation inutile, échec
  aux 2 premiers essais puis réussite au 3e (bonnes dimensions à
  chaque tentative), aucune réussite -> `null` après les 4 essais sans
  planter, une exception sur un essai n'interrompt pas les suivants —
  voir TESTS_NON_REGRESSION.md point 104. Ce test ne prouve PAS que la
  correction résout le cas réel signalé (impossible à vérifier sans le
  vrai détecteur natif) — seul un nouveau test sur téléphone le
  confirmerait. Depuis le point 108, une grande photo réelle
  (2000×1125, dimensions des photos réelles d'origine) est bien
  limitée à 1600×900 avant l'analyse (ratio 16:9 conservé), même seuil
  que `resizeImageForOcr`.
- `test_barcode_lookup_messages.py` — messages affichés après la
  recherche d'un produit scanné, suite à 2 bugs confirmés par un
  second audit externe (décodeur indépendant ZXing-C++ sur les mêmes 4
  photos) : un poids trouvé masquait silencieusement l'avertissement
  "nom non trouvé" (les deux s'affichent maintenant ensemble quand les
  deux s'appliquent) ; une panne réseau et un produit vraiment absent
  de la base étaient indiscernables (message dédié désormais pour la
  panne réseau, y compris une erreur HTTP) — voir
  TESTS_NON_REGRESSION.md point 105. Étendu au point 106 avec le cas
  d'un vrai 404 Open Food Facts (corps JSON `{status:0}` exploitable
  malgré le statut HTTP d'erreur) : bien traité comme un produit
  inconnu, pas comme une panne réseau.
- `test_drag_reorder.py` — glisser-déposer manuel (liste de courses,
  garde-manger, ingrédients d'un formulaire de recette), simulé via de
  vrais événements souris que Chromium traduit en Pointer Events :
  réordonnancement effectif sur les 3 écrans, persistance de l'ordre
  manuel (rechargement de page ET aller-retour de sauvegarde locale),
  non-régression des tris existants (alphabétique/rayon/péremption,
  jamais impactés par le tri manuel), absence de bug d'index périmé
  après un glisser-déposer dans le formulaire de recette, absence de
  débordement horizontal introduit par la nouvelle poignée — voir
  TESTS_NON_REGRESSION.md point 99.
- `test_external_audit_fixes.py` — corrections suite à un audit
  externe (autre IA) : thème suivant la préférence système au 1er
  lancement (et en direct si elle change), choix explicite jamais
  écrasé ensuite, migration sans surprise pour les utilisateurs déjà
  installés ; position de défilement restaurée au bouton "retour"
  uniquement ; cache stale-while-revalidate des fichiers JSON de
  référence (réponse immédiate + rafraîchissement en arrière-plan) ;
  avertissement non bloquant "économie de données" avant un
  téléchargement OCR ; idempotence de `init()` — voir
  TESTS_NON_REGRESSION.md point 100. Les points manifeste du même
  audit (orientation, captures "wide", favicon 32×32) sont couverts
  dans `test_pwa_manifest.py`.
- `test_pantry_expiration_photo_ocr.py` — prise/import de photo pour
  préremplir la date de péremption du garde-manger (même principe que
  le scan de code-barres, appliqué cette fois à la date elle-même) :
  heuristique d'extraction de date testée directement (formats
  ISO/européen, année à 2 chiffres, mot-clé de péremption — "DLC",
  "best before"... — préféré à une autre date sans mot-clé dans le
  même texte, date calendairement impossible comme le 31 février
  toujours ignorée, aucune date ne renvoie jamais d'erreur) ; bout en
  bout dans le formulaire du garde-manger avec le vrai OCR remplacé
  par une fonction simulée (jamais le vrai Tesseract, trop lent et non
  déterministe pour un test automatisé) : boutons caméra et galerie,
  préremplissage du champ en cas de succès, message clair si aucune
  date reconnue ou si l'OCR échoue, et surtout aucun enregistrement
  automatique — l'article n'est sauvegardé qu'après un clic explicite
  sur "Enregistrer" ; et correction d'orientation réellement vérifiée
  (pas seulement supposée en relisant le code) : `runExpirationDateOcr`
  réutilise `detectAndCorrectOrientation` (même pipeline que l'import
  photo de recette, point 16) — une vraie photo 200×100 non carrée est
  bien pivotée (dimensions inversées) avant l'OCR quand l'orientation
  est détectée avec confiance, laissée inchangée sinon (confiance
  trop faible ou détection en échec, jamais bloquant) — voir
  TESTS_NON_REGRESSION.md point 103. Utilise `tests/fixtures/tiny_blank.png`
  (contenu réel sans importance, l'OCR étant simulé) pour les scénarios
  de formulaire, et un `<canvas>` généré à la volée pour les scénarios
  d'orientation (dimensions non carrées nécessaires, contrairement à
  la fixture).
- `test_pantry_delete_undo_and_polish.py` — suite à l'examen d'un
  paquet "ui-kit" proposé par une autre IA (tabbar/FAB/icônes SVG
  présentés comme additifs, mais entrant en conflit réel avec la
  navigation et le bouton flottant déjà existants — non appliqués, voir
  TESTS_NON_REGRESSION.md point 109 pour le détail) : bug réel trouvé
  en cours d'examen (cliquer sur la poignée ☰ en tri manuel du
  garde-manger supprimait l'article au lieu de rien faire, sélecteur
  trop générique) ; bandeau "Annuler" retenu pour la suppression d'un
  article (restauration avec la totalité des champs, pas seulement le
  nom) ; disparition automatique du bandeau après son délai ; bouton
  flottant masqué pendant l'affichage du bandeau (chevauchement visuel
  repéré sur une capture d'écran réelle) ; grille à 2 colonnes de la
  liste de recettes sur écran large (appliquée sur la vraie classe
  `.recipe-list`). Son dernier cas ("colonne unique sur mobile") a été
  mis à jour au point 112 (TESTS_NON_REGRESSION.md) : la grille 2
  colonnes s'applique désormais aussi au mobile, sur demande explicite
  de l'utilisateur — le test vérifie maintenant que 2 cartes sont bien
  côte à côte à 390px, sans débordement horizontal.
- `test_ui_icon_replacement.py` — suite au "patch graphique" demandé
  explicitement par l'utilisateur (voir TESTS_NON_REGRESSION.md point
  110) : les emoji de CHROME d'interface (navigation du bas, bouton
  flottant, retour, recherche, thème, suppression) ont été remplacés
  par des icônes SVG (`icon()`/`ICONS` dans app.js), intégrées dans les
  éléments existants plutôt que dupliquées. Vérifie que chaque bouton
  concerné contient bien `svg.ui-icon`, que sa fonction (navigation,
  ouverture de fenêtre, suppression, bascule de thème) est inchangée,
  que les emoji de CONTENU (favoris, illustrations d'écran vide) ne
  sont PAS touchés, et que chaque icône est `aria-hidden="true"` avec
  l'`aria-label`/texte du bouton conservé (lecteur d'écran inchangé).
- `test_visual_wave_1.py` — "vague visuelle 1" (voir TESTS_NON_REGRESSION.md
  point 111) : cartes de recette à grande photo 16/9 + titre Fraunces,
  barres du haut/du bas translucides (`backdrop-filter`), pastille de
  fond sur l'onglet actif, photo de fiche recette agrandie avec
  statistiques superposées en chevauchement, cercle coloré derrière
  l'emoji des écrans vides. Vérifie aussi les 2 écarts corrigés par
  rapport aux instructions transmises (voir le point pour le détail) :
  la fenêtre de sélection de recette n'est PAS transformée en carte
  photo (bug réel trouvé en testant : `.recipe-row` seul confondait
  cette fenêtre — sans `.card` — avec les vraies listes en carte,
  rescopé en `.card.recipe-row`), et le `.stat-row` de la nutrition
  (hors fiche recette) n'a pas de marge négative. Vérifie enfin l'audit
  d'accessibilité sur l'écran diagnostic, scénario exact qui avait
  révélé une chute de contraste sous le seuil AA à cause de la
  transparence des barres (corrigée en relevant leur opacité à 95%).
- `test_weekly_plan_multi_recipe.py` — plusieurs recettes par repas dans
  le planning de la semaine (voir TESTS_NON_REGRESSION.md point 113,
  retour direct de l'utilisateur : un déjeuner/dîner se compose en
  réalité d'une entrée, un plat et un dessert, jamais d'une seule
  recette). Chaque case jour/repas contient désormais un tableau
  d'assignations (`planSlotAssignments()`, qui accepte aussi l'ancien
  format à assignation unique — aucune migration réécrivant le stockage
  n'a été nécessaire). Vérifie l'ajout/la suppression individuelle de
  plusieurs recettes sur un même créneau, qu'un ancien planning au
  format hérité s'affiche et se convertit correctement, que la
  génération de la liste de courses et l'archivage dans l'historique
  prennent bien en compte toutes les recettes d'un repas (pas
  seulement la première).
- `test_shopping_no_duplicate_missing_qty.py` — ne plus dupliquer un
  article de la liste de courses quand l'ingrédient ajouté (recette,
  menu, planning, rappel "stock bas" de l'accueil) n'a pas de quantité
  précisée (voir TESTS_NON_REGRESSION.md point 114, signalé par
  l'utilisateur avec capture d'écran). Cause : la fusion avec un article
  déjà présent n'avait lieu QUE si les deux quantités étaient non
  nulles — un ingrédient sans quantité ratait toujours cette condition
  et créait un doublon. Vérifie les 3 combinaisons (existant/ajout avec
  ou sans quantité), qu'un article déjà coché n'est toujours pas
  réutilisé, et un scénario de bout en bout reproduisant le cas exact
  signalé (recette ajoutée à une liste déjà existante).
- `test_third_audit_backup_and_shopping_bugs.py` — suite à un troisième
  audit externe (voir TESTS_NON_REGRESSION.md point 115) : 6 bugs
  confirmés et corrigés (ordre `puts`/`deletes` dans
  `storeWriteManyAcrossStores` risquant une perte de données ZIP,
  recette mal formée d'un ZIP partagé non validée, collections en
  mémoire non rechargées après une restauration JSON complète
  (menus/modèles/planning/liste sauvegardées/historique/corbeille),
  quantité fictive possible en cas d'échec d'écriture dans la liste de
  courses, accessibilité clavier/lecteur d'écran de la liste de
  courses et du garde-manger, écritures de cache du service worker non
  protégées par `event.waitUntil()`). Vérifie chaque correctif en
  appelant les vraies fonctions de l'application (restauration ZIP
  réelle, `importAllData`, `addRecipeToShoppingSilent` avec un
  `storePut` simulé en échec, rendu réel des lignes de courses/garde-
  manger, inspection du code source de `sw.js`).
- `test_shopping_partial_quantity_display.py` — suite au point 115,
  demande explicite de l'utilisateur (voir TESTS_NON_REGRESSION.md
  point 116) : affiche "... + quantité non précisée" au lieu de
  fusionner silencieusement une quantité connue et une quantité non
  précisée pour le même article de courses. Vérifie le marqueur
  `partialQuantity` posé (ou non) dans les 3 points d'ajout qui
  fusionnent un article existant (`addRecipeToShoppingSilent`,
  `addRecipeToShopping`, rappel "stock bas" de l'accueil), sa
  persistance à travers une fusion ultérieure, le suffixe réellement
  affiché à l'écran (texte et `aria-label`), et son effacement lors
  d'une modification manuelle via le formulaire d'édition.
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

