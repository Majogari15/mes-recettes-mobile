# Mes Recettes — version mobile (PWA)

Première version de l'application mobile, sous forme de site web
installable ("Progressive Web App") — fonctionne sur Android et iPhone,
sans serveur ni abonnement, toutes les données restent sur l'appareil.

## Fonctionnalités incluses dans cette première version

- Ajouter / modifier / supprimer une recette (avec photo prise depuis le
  téléphone)
- Recherche et filtres rapides (Favoris, Rapide, Végétarien, Envies)
- Fiche recette avec ajustement du nombre de personnes en temps réel
- **Allergènes** : détection automatique à partir des ~1000 ingrédients
  courants (même base que la version bureau), modifiable manuellement,
  affichée sur la fiche recette
- **Valeurs nutritionnelles** : estimation automatique (calories,
  protéines, glucides, lipides) par personne, à partir des mêmes
  ingrédients reconnus
- **Recherche/autocomplétion d'ingrédient** : en tapant les premières
  lettres, en français ou dans la langue actuellement affichée, dans le
  formulaire de recette comme dans l'ajout à la liste de courses ou au
  garde-manger — les noms d'ingrédients (recettes, courses, garde-manger,
  mode cuisine) s'affichent également traduits. Tout ingrédient vraiment
  nouveau (tapé à la main, ou introduit par un import depuis un lien)
  rejoint automatiquement cette liste dès l'enregistrement de la recette
- **Substituts d'ingrédients** (base fournie **et personnalisables**
  depuis "Gérer les ingrédients"), **export PDF d'une recette**,
  **comparer deux recettes**, **sauvegarde/restauration** de toutes vos
  données en un fichier
- **Corbeille** pour les recettes supprimées (récupérables avant
  suppression définitive), **convertisseur d'unités** indépendant,
  **listes de courses enregistrées** (à recharger plus tard), **export
  PDF de la liste de courses**, **partage de la liste de courses par QR
  code** (à scanner depuis un autre appareil pour l'importer — le scan
  nécessite une connexion sécurisée HTTPS, donc indisponible tant que
  l'app n'est pas mise en ligne), **recherche rapide globale** (icône 🔍
  en haut de l'accueil/recettes/courses/garde-manger), **QR code d'une
  recette** (nom + ingrédients, à scanner ou enregistrer en image), et
  **"Que puis-je cuisiner ?"** (repéré depuis le garde-manger, indique
  les recettes réalisables ou presque avec ce que vous avez déjà),
  **export "livre de cuisine"** (plusieurs recettes choisies, réunies en
  un seul PDF avec sommaire et numéros de page), **gestion
  centralisée des substituts** (retrouvez d'un coup d'œil tous les
  ingrédients ayant déjà un substitut enregistré), des **statistiques**
  (répartition par catégorie/difficulté, recettes les plus cuisinées,
  jamais cuisinées ou délaissées depuis 90+ jours, coût et calories
  moyens, graphique mensuel), et l'**import de recette depuis une
  photo** (reconnaissance de texte entièrement sur l'appareil, rien
  n'est envoyé où que ce soit — mais bien moins fiable qu'un import par
  lien, à toujours vérifier avant d'enregistrer)
- **Menus** (collections de recettes réutilisables) et **planning de la
  semaine** avec **modèles** réutilisables et **historique automatique**
  des semaines passées (jusqu'à 26 semaines, archivées avant chaque
  effacement ou application d'un modèle)
- **Journal de cuisine** : notez une impression et une photo à chaque
  fois que vous cuisinez une recette, avec compteur du nombre de fois
- **Lecture à voix haute** des étapes en mode cuisine
- **Import de recette depuis un lien internet** (voir la limitation
  ci-dessous), avec récupération automatique de la **photo**, des
  **vraies étapes de préparation** (pas juste un résumé), des **temps de
  préparation/cuisson**, d'une **catégorie devinée**, compatible avec le
  format "microdonnées" en plus du format JSON-LD le plus courant, et
  qui rattache les ingrédients importés à ceux déjà connus (variantes
  plurielles, fautes de frappe) plutôt que de systématiquement en créer
  de nouveaux
- **Gestion des ingrédients** : ajouter, renommer ou supprimer un
  ingrédient, et corriger/compléter ses allergènes, valeurs
  nutritionnelles et **prix** individuellement (accessible depuis
  l'accueil) — la liste de courses affiche alors un **total estimé**,
  avec un indicateur du nombre d'ingrédients sans prix connu, et peut se
  **trier par rayon de magasin** (Fruits & Légumes, Crèmerie...) en plus
  du tri par nom
- **Détection des doublons d'ingrédients** ("Tomate"/"Tomates",
  fautes de frappe...) avec fusion en un clic, accessible depuis
  "Gérer les ingrédients" — et suggérée **en temps réel** pendant la
  saisie d'un ingrédient ("Vouliez-vous dire...") pour éviter d'en créer
  un nouveau par erreur
- **Bouton d'installation** en haut de l'accueil (en plus de la
  suggestion automatique du navigateur), avec instructions dédiées sur
  iPhone/iPad
- **Corbeille** : une recette supprimée est récupérable avant
  suppression définitive
- **Convertisseur d'unités** indépendant de toute recette (tasses,
  onces, livres, cuillères...)
- **Listes de courses enregistrées** : sauvegardez la liste actuelle
  sous un nom pour la recharger plus tard
- **Export PDF de la liste de courses**
- **Recherche rapide** globale (icône 🔍 en haut, accessible depuis les
  4 écrans principaux)
- **QR code d'une recette** (nom + ingrédients), à scanner et à
  enregistrer en image
- **Scanner un QR code** pour importer une liste de courses **ou une
  recette** partagée depuis un autre appareil — compatible avec les QR
  codes générés par la version bureau, pas seulement par mobile
  (nécessite HTTPS pour la caméra, donc utilisable seulement une fois
  l'application mise en ligne). Utilise en priorité la détection de QR
  code intégrée au système (le même moteur que les applications de scan
  classiques, disponible sur Chrome Android), avec une bibliothèque de
  repli si l'appareil ne la propose pas. Si la lecture par caméra ne
  fonctionne toujours pas bien sur votre appareil, **"Coller le texte
  d'un QR code"** propose la même reconnaissance à partir du texte
  obtenu via une autre application de scan
- **"Que puis-je cuisiner ?"** : indiquez vos ingrédients disponibles
  (repris du garde-manger), voir quelles recettes sont réalisables ou
  presque
- Ajout d'une recette à la liste de courses (quantités fusionnées
  automatiquement)
- Mode courses avec cases à cocher
- Garde-manger (ajout/modification/suppression d'articles), avec **seuil
  d'alerte optionnel** par article : un rappel apparaît sur l'accueil
  dès que la quantité passe en dessous, touchez-le pour ajouter
  directement ces articles à la liste de courses (avec le seuil comme
  quantité suggérée)
- Mode cuisine avec **plusieurs minuteurs** réglables (décompte,
  sonnerie **et vibration**, clignotement à zéro)
- Multilingue : français, anglais, espagnol, allemand
- Thème clair / sombre
- Fonctionne hors connexion une fois ouverte une première fois
- Installable sur l'écran d'accueil comme une vraie application

## Fonctionnalités pas encore incluses (prévues pour plus tard)

Aucune connue à ce jour — la comparaison avec la version bureau ne
laisse plus que des différences mineures ou volontaires (voir plus
haut).

## ⚠️ À savoir sur l'import de recette depuis un lien

Contrairement aux autres fonctionnalités, celle-ci dépend de services
tiers pour contourner une restriction de sécurité des navigateurs
(CORS) — sans eux, il serait impossible de récupérer le contenu d'un
autre site directement depuis le téléphone. Un **Worker Cloudflare**
propre à cette application est essayé en premier : il ne fait que
transmettre la page (et sa photo) sans en garder de copie, et permet en
plus une récupération automatique et précise de la photo de la recette.
S'il échoue ou n'est pas configuré, **Jina AI Reader** prend le relais :
il ne transmet pas le HTML brut mais une version déjà nettoyée en texte
de la page, analysée ensuite avec la même méthode que l'import par
photo (repérage des mots "Ingrédients"/"Préparation") — moins précis
qu'une extraction de données structurées, et sans récupération de photo
automatique, mais nettement plus fiable en pratique que les services
suivants. Si Jina échoue aussi, trois services CORS publics classiques
sont essayés automatiquement l'un après l'autre (`allorigins.win`,
`codetabs.com`, `cors.lol`) en tout dernier recours ; chaque réponse est
vérifiée pour confirmer qu'elle contient réellement une recette avant
d'être acceptée (une page d'erreur ou de blocage renvoyée par l'un de
ces services ne fait donc plus stopper la recherche à tort). Deux
conséquences à connaître :
- L'adresse que vous collez est transmise à ces services intermédiaires
- Si tous deviennent indisponibles un jour, cette fonctionnalité
  cesserait de fonctionner jusqu'à ce qu'on la fasse pointer vers
  d'autres services équivalents

La reconnaissance des quantités et unités reste approximative (comme sur
la version bureau) : vérifiez toujours le résultat avant d'enregistrer.

## Tester en local sur votre tablette Android

1. Sur l'ordinateur, dans ce dossier, lancez un petit serveur local :
   ```
   python3 -m http.server 8000
   ```
   (ou toute autre méthode pour servir des fichiers statiques)
2. Trouvez l'adresse IP locale de l'ordinateur (Windows : `ipconfig`,
   cherchez "Adresse IPv4", ex. `192.168.1.42`)
3. Assurez-vous que la tablette est sur le **même réseau Wi-Fi**
4. Sur la tablette, ouvrez Chrome et allez sur :
   ```
   http://192.168.1.42:8000
   ```
   (remplacez par votre propre adresse IP)
5. Pour l'installer comme une vraie app : menu ⋮ de Chrome → **"Installer
   l'application"** ou **"Ajouter à l'écran d'accueil"**

## Mise en ligne gratuite (pour y accéder de partout, pas seulement en Wi-Fi local)

Le moyen le plus simple et gratuit : **GitHub Pages**, puisque vous avez
déjà un dépôt GitHub pour ce projet.

1. Créez un nouveau dépôt (ou un nouveau dossier `mobile/` dans le dépôt
   existant)
2. Poussez tout le contenu de ce dossier dedans
3. Dans les paramètres du dépôt GitHub, section "Pages", activez GitHub
   Pages sur la branche principale
4. L'application sera accessible à une adresse du type
   `https://majogari15.github.io/nom-du-depot/`

## Structure des fichiers

- `index.html` — page principale
- `app.js` — toute la logique de l'application
- `i18n.js` — traductions (4 langues)
- `styles.css` — apparence
- `manifest.json` — configuration de l'installation en tant qu'app
- `sw.js` — fonctionnement hors connexion
- `icons/` — icônes de l'application
- `data/` — bases d'allergènes et de valeurs nutritionnelles (référence
  uniquement, jamais modifiées par l'application)
