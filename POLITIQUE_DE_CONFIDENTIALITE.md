# Politique de confidentialité — Mes Recettes, Mes Courses

Dernière mise à jour : 2 septembre 2026

Cette politique de confidentialité décrit comment l'application « Mes
Recettes, Mes Courses » (version mobile) traite vos données personnelles.

## 1. Résumé en une phrase

L'application stocke vos données **uniquement sur votre appareil**, sans
compte ni inscription ni publicité — mais certaines fonctionnalités
optionnelles, décrites en détail ci-dessous, transmettent des informations
à des services tiers lorsque vous les utilisez explicitement (à
l'exception du chargement des polices de caractères, automatique dès le
premier chargement — voir section 4).

## 2. Où sont stockées vos données ?

Toutes les données que vous créez (recettes, ingrédients, photos, notes,
journal de cuisine, planning, menus, prix, préférences) sont enregistrées
**localement dans le stockage de votre navigateur** (technologie
IndexedDB), directement sur votre téléphone ou votre tablette. Rien n'est
envoyé vers un serveur ni stocké dans un compte en ligne géré par
l'éditeur de l'application.

## 3. Accès à la caméra

L'application peut demander l'accès à la caméra de votre appareil,
**uniquement lorsque vous ouvrez vous-même** la fonction de scan de QR
code (pour importer une recette ou une liste de courses partagée depuis
un autre appareil). Les images captées par la caméra sont analysées
**directement sur votre appareil** pour y détecter un QR code — aucune
image n'est enregistrée ni transmise où que ce soit. Vous pouvez refuser
cette autorisation sans que le reste de l'application soit affecté ; une
solution de repli (coller le texte manuellement) reste disponible.

## 4. Connexions à internet effectuées par l'application

L'application fonctionne hors connexion pour l'immense majorité de ses
fonctionnalités. Voici les connexions qu'elle effectue, la plupart à votre
initiative explicite — sauf une exception clairement indiquée ci-dessous :

- **Polices de caractères (Google Fonts)** : contrairement aux autres
  éléments listés ici, cette connexion est **automatique**, dès le
  premier chargement de l'application, sans action de votre part.
  L'application charge deux polices (Fraunces et Inter) directement
  depuis les serveurs de Google (`fonts.googleapis.com`). Cette requête
  transmet à Google les informations techniques habituelles de toute
  requête web (adresse IP, type de navigateur) — consultez la politique
  de confidentialité de Google pour plus de détails. Aucune donnée de
  l'application elle-même (recettes, listes, photos) n'est concernée.
- **Import d'une recette depuis un lien (ou de sa photo)** : les
  navigateurs empêchant une application web de récupérer directement le
  contenu d'un autre site, cette fonctionnalité transmet l'adresse que
  vous collez à l'un des services intermédiaires suivants (essayés
  automatiquement l'un après l'autre) pour contourner cette restriction
  technique : un service Cloudflare Worker propre à cette application
  (qui ne fait que transmettre la page sans en conserver de copie),
  Jina AI Reader (r.jina.ai), allorigins.win, codetabs.com, cors.lol.
  Ces services reçoivent l'adresse que vous avez collée afin de
  récupérer la page à votre place ; consultez leurs propres politiques
  de confidentialité
  pour savoir comment ils traitent ces requêtes.
- **Import de recette par photo (reconnaissance de texte)** : cette
  fonctionnalité utilise une bibliothèque technique (Tesseract.js)
  téléchargée depuis un serveur de distribution de contenu (jsDelivr) —
  et mise en cache pour un usage hors connexion ensuite. Ce
  téléchargement a lieu dès la première visite de l'application
  (installation du fonctionnement hors connexion), pas seulement au
  moment où vous utilisez réellement cette fonction. Aucune photo, aucun
  texte ni aucune donnée personnelle n'est envoyé à ce serveur : seule la
  bibliothèque elle-même est téléchargée.
  La **génération et la lecture de QR code**, ainsi que l'**export PDF**,
  fonctionnent en revanche entièrement à partir de fichiers inclus dans
  l'application elle-même, sans aucun téléchargement externe.
- **Bouton « Faire un don »** : ouvre, uniquement si vous cliquez dessus,
  la page https://buymeacoffee.com/majogari dans votre navigateur.
- **Partager la sauvegarde** (fonctionnalité optionnelle) : le bouton
  « Partager la sauvegarde » ouvre le menu de partage natif de votre
  téléphone, vous laissant choisir vous-même une application (Google
  Drive, Dropbox, email...) vers laquelle envoyer votre fichier de
  sauvegarde. L'application ne communique directement avec aucun de ces
  services : c'est l'application que vous choisissez dans ce menu qui
  reçoit le fichier, selon sa propre politique de confidentialité.

## 5. Aucune collecte, aucun suivi

L'application ne contient :
- aucun système de compte ou de connexion ;
- aucune télémétrie, aucun outil d'analyse d'utilisation ;
- aucune publicité ;
- aucun partage ou vente de vos données personnelles à des tiers.

## 6. Vos photos et vos recettes

Les photos que vous ajoutez à vos recettes ou à votre journal de cuisine
sont stockées uniquement dans le stockage local de votre navigateur. Elles
ne sont jamais transmises ailleurs, sauf si vous utilisez vous-même une
fonctionnalité d'export ou de partage (PDF, QR code, sauvegarde) et
choisissez de partager le résultat de votre propre initiative.

## 7. Maîtrise de vos données

- vous pouvez consulter, modifier ou supprimer vos données à tout moment
  directement dans l'application ;
- vous pouvez exporter l'ensemble de vos données à tout moment via la
  fonction de sauvegarde, pour les conserver ou les transférer
  vous-même où vous le souhaitez ;
- désinstaller l'application ou vider les données du site depuis les
  paramètres de votre navigateur efface l'intégralité de vos données
  locales, puisqu'aucune copie n'existe ailleurs.

## 8. Enfants

L'application ne s'adresse pas spécifiquement aux enfants et ne collecte,
comme indiqué ci-dessus, aucune donnée personnelle identifiable, quel que
soit l'âge de la personne qui l'utilise.

## 9. Modifications de cette politique

Cette politique pourra être mise à jour si de nouvelles fonctionnalités
impliquant un traitement de données étaient ajoutées à l'application. La
date de dernière mise à jour figure en haut de ce document.

## 10. Contact

Pour toute question concernant cette politique de confidentialité, vous
pouvez ouvrir une discussion (« Issue ») sur le dépôt GitHub du projet.
