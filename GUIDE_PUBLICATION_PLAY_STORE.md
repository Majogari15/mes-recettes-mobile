# Publier "Mes Recettes, Mes Courses" sur le Google Play Store

Guide complet, étape par étape. Je ne peux pas soumettre l'application
à votre place (ça nécessite votre propre compte Google et un paiement),
mais tout ce qui est vérifiable et préparable à l'avance l'a été.

## Vue d'ensemble de la méthode

Une PWA (comme celle-ci) se publie sur le Play Store via une **TWA**
(Trusted Web Activity) : une coquille Android très fine qui affiche
votre site web déjà en ligne en plein écran, sans barre de navigateur.
L'outil **PWABuilder** (gratuit, par Microsoft, toujours d'actualité en
2026) automatise presque tout ce travail.

## Prérequis avant de commencer

- [ ] L'application doit être **déjà en ligne** à une adresse HTTPS
      stable (c'est le cas : votre dépôt GitHub Pages)
- [ ] Un **compte développeur Google Play** (25 $, paiement unique,
      valable à vie) — à créer sur https://play.google.com/console
      si ce n'est pas déjà fait
- [ ] La politique de confidentialité (`POLITIQUE_CONFIDENTIALITE.md`
      fournie) **hébergée en ligne** avant de commencer — par exemple
      comme nouvelle page sur votre GitHub Pages
      (`https://majogari15.github.io/mes-recettes-mobile/confidentialite.html`)

## Étape 1 — Générer le paquet Android avec PWABuilder

1. Allez sur **https://www.pwabuilder.com**
2. Entrez l'adresse de votre application déployée, cliquez sur
   **Start**
3. PWABuilder analyse votre manifeste et votre service worker, et
   affiche un score — devrait maintenant afficher 0 erreur
   obligatoire, 0 recommandation en échec (déjà confirmé sur la
   version actuelle)
4. Cliquez sur **Package for stores**, puis choisissez **Android**
5. Dans les options qui s'affichent, réglez précisément :
   - **Package ID** : proposé automatiquement (ex.
     `io.github.majogari15.twa`) — **choisissez maintenant une valeur
     définitive** plutôt que de garder cette proposition automatique,
     par exemple `io.github.majogari15.mesrecettes`. ⚠️ **Cet
     identifiant devient permanent après publication** — impossible
     d'en changer pour une mise à jour future, il faudrait recréer une
     toute nouvelle fiche Play Store. Prenez un moment pour choisir
     une valeur dont vous serez satisfait durablement.
   - **Signing key** : choisissez "Create new signing key" — c'est
     votre première publication

     ⚠️ **Le point le plus important de toute cette étape** : une fois
     le paquet généré, vous allez recevoir un fichier de clé
     (`.keystore` ou `.pem`) et un mot de passe. **Sauvegardez-les
     immédiatement dans un endroit sûr** (gestionnaire de mots de
     passe, ou au moins 2 copies différentes) — sans cette clé exacte,
     vous ne pourrez plus jamais publier de mise à jour de
     l'application, il faudrait recommencer avec une toute nouvelle
     fiche Play Store.
   - **Pays** (dans les informations de la clé de signature) :
     renseignez `FR`, pas la valeur par défaut `US`
   - Le reste des options par défaut (affichage "Standalone", repli
     "Custom Tabs"...) peut rester tel quel
6. Cliquez sur **Generate**, patientez le temps de la génération
   (peut prendre 1 à 2 minutes)
7. Téléchargez le fichier `.zip` généré — il contient le fichier
   `.aab` à soumettre, votre clé de signature, et un fichier
   `assetlinks.json`

### Vérifier `targetSdkVersion 36` (exigence Google Play depuis fin août 2026)

Vous n'avez pas besoin d'outil spécial pour vérifier ce point vous-même
— **Play Console le vérifie automatiquement à l'étape de
téléversement** (Étape 4 ci-dessous) et refusera clairement le fichier
avec un message explicite si ce n'est pas le cas. Si ce message
apparaît, la cause la plus probable est une version de PWABuilder pas
encore à jour sur ce point précis — revenez me voir avec le message
exact affiché, je regarderai la marche à suivre.

## Étape 2 — Prouver que vous possédez le site (Digital Asset Links)

⚠️ **Point technique important, corrigé après un second avis** : ce
fichier doit être placé à la **racine de votre domaine**
(`majogari15.github.io`), pas dans le sous-dossier de ce projet
(`mes-recettes-mobile/`) — c'est une exigence du format Digital Asset
Links lui-même : la vérification se fait sur l'origine complète du
domaine, pas sur un chemin particulier à l'intérieur.

1. Dans le `.zip` téléchargé, trouvez le fichier `assetlinks.json`
2. Placez-le à l'adresse exacte :
   `https://majogari15.github.io/.well-known/assetlinks.json`

   Concrètement, cela signifie un **second dépôt GitHub**, séparé de
   `mes-recettes-mobile` : un dépôt nommé exactement
   `majogari15.github.io` (le dépôt "utilisateur" GitHub Pages,
   different d'un dépôt "projet"). Si vous n'en avez pas encore un,
   créez-en un avec ce nom exact, puis ajoutez-y juste un dossier
   `.well-known/` contenant ce fichier `assetlinks.json` — il n'a pas
   besoin de contenir quoi que ce soit d'autre.
3. Vérifiez que ce fichier est bien accessible en ouvrant cette URL
   dans un navigateur après publication — sans ça, l'application
   n'affichera pas d'erreur visible mais s'ouvrira avec une barre de
   navigateur visible en haut de l'écran, au lieu de l'apparence plein
   écran attendue d'une vraie application installée

## Étape 3 — Créer la fiche dans Play Console

1. Dans Play Console, créez une nouvelle application
2. Remplissez les informations avec le contenu de
   `FICHE_PLAY_STORE.md` fourni (titre, descriptions)
3. Ajoutez les captures d'écran fournies dans le dossier
   `screenshots/` (minimum 2 requises, les 4 fournies conviennent) —
   Play Store peut demander un format légèrement différent selon les
   sections (icône 512×512 déjà disponible dans `icons/`)
4. Renseignez l'URL de votre politique de confidentialité (étape
   préalable ci-dessus)
5. Remplissez le formulaire **Sécurité des données** en suivant
   `GUIDE_SECURITE_DONNEES_PLAY_STORE.md` fourni, question par
   question
6. Remplissez le questionnaire de classification du contenu
   (IARC) — pour cette application, les réponses seront presque
   toutes "non" (pas de violence, pas de contenu choquant...),
   aboutissant à une classification "Tout public"

## Étape 4 — Soumettre le paquet

1. Dans la section "Production" (ou "Test fermé" si vous préférez
   tester avant une sortie publique), téléversez le fichier `.aab`
   généré à l'étape 1
2. Complétez les derniers champs obligatoires que Play Console vous
   signale s'il en manque
3. Soumettez pour vérification

## Étape 5 — Attendre la vérification

Google vérifie chaque nouvelle application avant publication —
généralement de quelques heures à quelques jours. Vous recevrez un
email en cas de refus, avec le motif précis ; la plupart des refus à
ce stade concernent des informations manquantes dans la fiche, pas le
code de l'application lui-même.

## Pour les mises à jour futures

À chaque nouvelle version de l'application (nouveau numéro de
version dans `app.js`) :
1. Redéployez le site sur GitHub Pages comme d'habitude
2. Repassez par PWABuilder pour régénérer un `.aab` — réutilisez
   impérativement la **même clé de signature** que la première fois
   (PWABuilder permet de l'importer plutôt que d'en générer une
   nouvelle)
3. Téléversez le nouveau `.aab` dans Play Console

## Fichiers fournis avec ce guide

- `FICHE_PLAY_STORE.md` — textes prêts à copier-coller
- `POLITIQUE_CONFIDENTIALITE.md` — à héberger en ligne avant de commencer
- `GUIDE_SECURITE_DONNEES_PLAY_STORE.md` — pour remplir ce formulaire précis
- `screenshots/` — 4 captures d'écran réelles de l'application
- `manifest.json` mis à jour avec ces captures (installation enrichie)
