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

