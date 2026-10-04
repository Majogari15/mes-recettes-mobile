# Politique de confidentialité — Mes Recettes, Mes Courses

*Dernière mise à jour : 4 octobre 2026 — version anglaise : `privacy.html`*

## Résumé en une phrase

Cette application stocke toutes vos données uniquement sur votre
téléphone ; rien n'est envoyé à un serveur, sauf lorsque vous
choisissez vous-même d'importer une recette depuis un lien internet,
de rechercher un produit à partir d'un code-barres scanné, ou de
chercher une recette sur Internet.

## Quelles données sont stockées, et où

Vos recettes, votre garde-manger, vos listes de courses, votre
planning et vos préférences sont enregistrés **uniquement sur votre
appareil** (stockage local du navigateur, technologie IndexedDB),
ainsi que quelques réglages et messages techniques (langue, thème,
date de la dernière sauvegarde, acceptation de la clause de
responsabilité, derniers messages d'erreur affichés dans l'écran
Diagnostic). Aucun compte n'est requis. Personne d'autre que vous — ni le
développeur, ni un tiers — n'a accès à ces données.

Si vous désinstallez l'application ou effacez les données de votre
navigateur, ces informations sont supprimées définitivement, à moins
que vous n'ayez exporté une sauvegarde vous-même au préalable.

## Accès à la caméra

L'application utilise la caméra de deux façons différentes :

- **Scan de QR code** (pour importer une recette ou une liste de
  courses partagée depuis un autre appareil) : l'application ouvre un
  flux vidéo en direct de la caméra, analysé **entièrement sur votre
  appareil** pour y détecter un QR code. Aucune image n'est
  enregistrée ni transmise où que ce soit. Vous pouvez refuser cette
  autorisation sans que le reste de l'application soit affecté ; une
  solution de repli (coller le texte manuellement) reste disponible.
- **Scan de code-barres** (pour ajouter un article au garde-manger) :
  comme le scan de QR code, l'application analyse le flux vidéo
  **entièrement sur votre appareil** pour y détecter un code-barres —
  aucune image n'est enregistrée ni transmise où que ce soit. Le
  numéro du code-barres détecté (jamais l'image) est ensuite envoyé à
  Open Food Facts pour retrouver le nom du produit — voir la section
  suivante. Vous pouvez refuser cette autorisation ou taper le
  code-barres vous-même ; le reste de l'application n'est pas affecté.
- **Photo d'une recette, du journal de cuisine, ou import de recette
  depuis une photo** : l'application ouvre l'appareil photo natif de
  votre téléphone (comme le ferait n'importe quelle autre application)
  pour prendre un cliché, ou vous laisse en choisir un déjà existant
  dans votre galerie. La photo obtenue reste stockée uniquement dans
  le stockage local de l'application.

## Connexions à internet effectuées par l'application

L'application fonctionne hors connexion pour l'immense majorité de ses
fonctionnalités — y compris les polices de caractères utilisées pour
son apparence (Fraunces et Inter), incluses directement dans
l'application plutôt que chargées depuis un service externe. Voici les
connexions qu'elle effectue, toutes à votre initiative explicite :

- **Import d'une recette depuis un lien internet** : les navigateurs
  empêchant une application web de récupérer directement le contenu
  d'un autre site, cette fonctionnalité transmet l'adresse que vous
  collez à l'un des services intermédiaires suivants (essayés
  automatiquement l'un après l'autre en cas d'échec) pour contourner
  cette restriction technique :
  1. Un serveur (Cloudflare Worker) exploité par le développeur, en
     premier — il ne fait que transmettre la page (et sa photo) sans
     en garder de copie. Il est hébergé par **Cloudflare**, qui voit
     passer la requête (adresse de la page et votre adresse IP) selon
     sa propre politique de confidentialité
  2. Si celui-ci échoue : **Jina AI Reader** (r.jina.ai)
  3. Si celui-ci échoue aussi : l'un des trois services publics
     **AllOrigins** (allorigins.win), **CodeTabs** (codetabs.com) ou
     **cors.lol**, en dernier recours

  Dans tous les cas, seule l'adresse de la page que vous voulez
  importer (et, séparément, l'adresse de la photo de la recette qui en
  est extraite) est transmise — jamais vos recettes, votre
  garde-manger ou toute autre donnée personnelle. Ces services ne sont
  pas exploités par le développeur (à l'exception du premier) et
  peuvent avoir leurs propres règles de conservation, sur lesquelles le
  développeur n'a pas de contrôle direct. Cette action ne se produit
  que si vous choisissez explicitement d'importer une recette par lien
  — ce n'est jamais un comportement automatique ou en arrière-plan.
- **Import de recette par photo (reconnaissance de texte)** : cette
  fonctionnalité utilise une bibliothèque technique (Tesseract.js),
  incluse directement dans l'application elle-même, comme la
  génération de QR code et l'export PDF — aucun serveur externe pour
  cette partie. Reconnaître le texte d'une photo nécessite en revanche
  un fichier de données propre à chaque langue (français, anglais,
  espagnol, allemand, indonésien, portugais, italien, suédois,
  norvégien), ainsi qu'un petit fichier supplémentaire servant
  uniquement à détecter et corriger automatiquement une photo prise à
  l'envers ou de côté, chacun téléchargé une seule fois **depuis le
  site de l'application elle-même** (aucun service tiers) lors du tout
  premier import photo concerné, puis mis en cache pour un usage hors
  connexion ensuite. Aucune photo, aucun texte ni aucune
  donnée personnelle n'est envoyé où que ce soit : le fichier
  téléchargé contient uniquement les données nécessaires à la
  reconnaissance de texte, indépendamment de vos photos. La
  **génération et la lecture de QR code**, ainsi que l'**export PDF**,
  fonctionnent entièrement à partir de fichiers inclus dans
  l'application elle-même, sans aucun téléchargement externe.
- **Scan de code-barres (garde-manger)** : le numéro détecté (ou tapé
  manuellement) est envoyé à **Open Food Facts**
  (world.openfoodfacts.org), une base de données ouverte et gratuite,
  pour retrouver le nom du produit et son poids/volume net si
  disponibles. Aucune autre donnée n'est transmise avec cette requête
  — ni vos recettes, ni votre garde-manger, ni aucune information
  personnelle. Le nom trouvé est toujours à confirmer ou modifier
  avant d'être ajouté ; il n'est jamais appliqué automatiquement, et si
  le produit n'est pas trouvé (ou en l'absence de réseau), vous pouvez
  toujours continuer en tapant le nom vous-même. Cette action ne se
  produit que si vous scannez ou saisissez vous-même un code-barres —
  jamais en arrière-plan. Ce service n'est pas exploité par le
  développeur et peut avoir ses propres règles de conservation, sur
  lesquelles le développeur n'a pas de contrôle direct.
- **Recherche d'une recette sur Internet** (écran « Importer depuis un
  lien ») : ouvre, uniquement si vous lancez la recherche, une page de
  résultats **Google** dans votre navigateur avec les mots que vous
  avez saisis (et des noms de sites de recettes ajoutés
  automatiquement). Google reçoit cette recherche selon sa propre
  politique de confidentialité ; l'application ne lit pas les
  résultats.
- **Bouton « Faire un don »** : ouvre, uniquement si vous cliquez
  dessus, la page https://buymeacoffee.com/majogari dans votre
  navigateur.
- **Partager la sauvegarde ou le fichier agenda du planning**
  (fonctionnalités optionnelles) : les boutons « Partager la
  sauvegarde » et « Exporter vers l'agenda (.ics) » ouvrent le menu de
  partage natif de votre téléphone (ou téléchargent le fichier), vous
  laissant choisir vous-même une application (Google Drive, Dropbox,
  agenda, email...) vers laquelle envoyer le fichier. L'application ne
  communique directement avec aucun de ces services : c'est
  l'application que vous choisissez dans ce menu qui reçoit le
  fichier, selon sa propre politique de confidentialité.
- **Rapport de diagnostic** (écran Diagnostic) : il contient la
  version de l'application, le navigateur et le système, l'espace de
  stockage utilisé et les derniers messages d'erreur techniques — ni
  vos recettes, ni les adresses des pages importées. Il n'est envoyé
  que si vous le partagez ou le copiez vous-même, par le moyen de
  votre choix.
- **Lecture à voix haute** (mode cuisine) : elle utilise le moteur de
  synthèse vocale de votre téléphone, selon ses propres réglages ;
  l'application n'envoie elle-même aucun texte à un service externe.

## Ce que l'application ne fait pas

- Le développeur ne collecte aucune donnée personnelle (nom, email,
  localisation...) — voir cependant la section précédente : votre
  adresse IP est techniquement visible des services réseau sollicités
  (import par lien, code-barres, recherche web), comme pour n'importe
  quelle requête sur internet
- Elle n'utilise aucun outil d'analyse d'audience ou de suivi
  publicitaire
- Elle n'affiche aucune publicité
- Elle ne partage, ne vend, ni ne transmet vos recettes ou vos données
  à qui que ce soit
- Elle ne nécessite aucun compte ni inscription

## Permissions de l'appareil utilisées

- **Appareil photo** : voir la section « Accès à la caméra »
  ci-dessus — utilisée uniquement lorsque vous ouvrez vous-même le
  scan de QR code ou de code-barres, l'ajout d'une photo à une
  recette/au journal de cuisine, ou l'import de recette depuis une
  photo.
- **Notifications** : uniquement pour vous prévenir qu'un minuteur de
  cuisine est terminé.
- **Presse-papiers** : lu uniquement quand vous touchez « Coller le
  lien copié » (écran « Importer depuis un lien ») ; votre téléphone
  peut vous demander l'autorisation. Le diagnostic peut aussi y copier
  son rapport, à votre demande.
- **Vibration** : uniquement quand un minuteur de cuisine sonne
  (aucune autorisation n'est demandée pour cela).

## Vos photos et vos recettes

Les photos que vous ajoutez à vos recettes ou à votre journal de
cuisine sont stockées uniquement dans le stockage local de votre
navigateur. Elles ne sont jamais transmises ailleurs, sauf si vous
utilisez vous-même une fonctionnalité d'export ou de partage (PDF, QR
code, sauvegarde, fichier agenda) et choisissez de partager le résultat de votre
propre initiative.

## Vos droits / maîtrise de vos données

Puisqu'aucune donnée n'est collectée par le développeur, il n'y a rien
à demander de supprimer, corriger ou exporter auprès de lui — vos
données vous appartiennent et restent sous votre contrôle direct sur
votre appareil, à tout moment :

- vous pouvez consulter, modifier ou supprimer vos données à tout
  moment directement dans l'application ;
- vous pouvez exporter l'ensemble de vos données à tout moment via la
  fonction de sauvegarde, pour les conserver ou les transférer
  vous-même où vous le souhaitez ;
- désinstaller l'application ou vider les données du site depuis les
  paramètres de votre navigateur efface l'intégralité de vos données
  locales, puisqu'aucune copie n'existe ailleurs.

## Enfants

L'application ne s'adresse pas spécifiquement aux enfants et ne
collecte, comme indiqué ci-dessus, aucune donnée personnelle
identifiable, quel que soit l'âge de la personne qui l'utilise.

## Modifications de cette politique

Cette politique pourra être mise à jour si de nouvelles
fonctionnalités impliquant un traitement de données étaient ajoutées à
l'application. La date de dernière mise à jour figure en haut de ce
document.

Les conditions d'utilisation de l'application (allergènes, données
indicatives, services tiers) figurent dans sa **clause de
responsabilité**, affichée au premier lancement et consultable à tout
moment depuis l'écran Sauvegarde.

## Contact

Pour toute question sur cette politique de confidentialité :
majogari81@gmail.com (vous pouvez aussi ouvrir une discussion
« Issue » sur le dépôt GitHub du projet).
