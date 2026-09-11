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

