# Politique de confidentialité — Mes Recettes, Mes Courses

*Dernière mise à jour : 14 septembre 2026*

## Résumé en une phrase

Cette application stocke toutes vos données uniquement sur votre
téléphone ; rien n'est envoyé à un serveur, sauf lorsque vous
choisissez vous-même d'importer une recette depuis un lien internet
(à l'exception du chargement des polices de caractères, automatique
dès le premier chargement — voir plus bas).

## Quelles données sont stockées, et où

Vos recettes, votre garde-manger, vos listes de courses, votre
planning et vos préférences sont enregistrés **uniquement sur votre
appareil** (stockage local du navigateur, technologie IndexedDB).
Aucun compte n'est requis. Personne d'autre que vous — ni le
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
- **Photo d'une recette, du journal de cuisine, ou import de recette
  depuis une photo** : l'application ouvre l'appareil photo natif de
  votre téléphone (comme le ferait n'importe quelle autre application)
  pour prendre un cliché, ou vous laisse en choisir un déjà existant
  dans votre galerie. La photo obtenue reste stockée uniquement dans
  le stockage local de l'application.

## Connexions à internet effectuées par l'application

L'application fonctionne hors connexion pour l'immense majorité de ses
fonctionnalités. Voici les connexions qu'elle effectue, la plupart à
votre initiative explicite — sauf une exception clairement indiquée
ci-dessous :

- **Polices de caractères (Google Fonts)** : contrairement aux autres
  éléments listés ici, cette connexion est **automatique**, dès le
  premier chargement de l'application, sans action de votre part.
  L'application charge deux polices (Fraunces et Inter) directement
  depuis les serveurs de Google (`fonts.googleapis.com`). Cette requête
  transmet à Google les informations techniques habituelles de toute
  requête web (adresse IP, type de navigateur) — consultez la
  [politique de confidentialité de Google](https://policies.google.com/privacy)
  pour plus de détails. Aucune donnée de l'application elle-même
  (recettes, listes, photos) n'est concernée.
- **Import d'une recette depuis un lien internet** : les navigateurs
  empêchant une application web de récupérer directement le contenu
  d'un autre site, cette fonctionnalité transmet l'adresse que vous
  collez à l'un des services intermédiaires suivants (essayés
  automatiquement l'un après l'autre en cas d'échec) pour contourner
  cette restriction technique :
  1. Un serveur (Cloudflare Worker) exploité par le développeur, en
     premier — il ne fait que transmettre la page (et sa photo) sans
     en garder de copie
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
  espagnol, allemand), téléchargé une seule fois lors du tout premier
  import photo dans cette langue précise, puis mis en cache pour un
  usage hors connexion ensuite. Aucune photo, aucun texte ni aucune
  donnée personnelle n'est envoyé où que ce soit : le fichier
  téléchargé contient uniquement les données nécessaires à la
  reconnaissance de texte, indépendamment de vos photos. La
  **génération et la lecture de QR code**, ainsi que l'**export PDF**,
  fonctionnent entièrement à partir de fichiers inclus dans
  l'application elle-même, sans aucun téléchargement externe.
- **Bouton « Faire un don »** : ouvre, uniquement si vous cliquez
  dessus, la page https://buymeacoffee.com/majogari dans votre
  navigateur.
- **Partager la sauvegarde** (fonctionnalité optionnelle) : le bouton
  « Partager la sauvegarde » ouvre le menu de partage natif de votre
  téléphone, vous laissant choisir vous-même une application (Google
  Drive, Dropbox, email...) vers laquelle envoyer votre fichier de
  sauvegarde. L'application ne communique directement avec aucun de
  ces services : c'est l'application que vous choisissez dans ce menu
  qui reçoit le fichier, selon sa propre politique de confidentialité.

## Ce que l'application ne fait pas

- Le développeur ne collecte aucune donnée personnelle (nom, email,
  localisation...) — voir cependant la section précédente : votre
  adresse IP est techniquement visible des quelques services réseau
  sollicités (import par lien, polices), comme pour n'importe quelle
  requête sur internet
- Elle n'utilise aucun outil d'analyse d'audience ou de suivi
  publicitaire
- Elle n'affiche aucune publicité
- Elle ne partage, ne vend, ni ne transmet vos recettes ou vos données
  à qui que ce soit
- Elle ne nécessite aucun compte ni inscription

## Permissions de l'appareil utilisées

- **Appareil photo** : voir la section « Accès à la caméra »
  ci-dessus — utilisée uniquement lorsque vous ouvrez vous-même le
  scan de QR code, l'ajout d'une photo à une recette/au journal de
  cuisine, ou l'import de recette depuis une photo.
- **Notifications** : uniquement pour vous prévenir qu'un minuteur de
  cuisine est terminé.

## Vos photos et vos recettes

Les photos que vous ajoutez à vos recettes ou à votre journal de
cuisine sont stockées uniquement dans le stockage local de votre
navigateur. Elles ne sont jamais transmises ailleurs, sauf si vous
utilisez vous-même une fonctionnalité d'export ou de partage (PDF, QR
code, sauvegarde) et choisissez de partager le résultat de votre
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

## Contact

Pour toute question sur cette politique de confidentialité :
fabrice.moritel15@gmail.com (vous pouvez aussi ouvrir une discussion
« Issue » sur le dépôt GitHub du projet).
