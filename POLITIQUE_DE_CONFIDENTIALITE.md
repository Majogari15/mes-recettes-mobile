# Politique de confidentialité — Mes Recettes, Mes Courses

Dernière mise à jour : 2 septembre 2026

Cette politique de confidentialité décrit comment l'application « Mes
Recettes, Mes Courses » (version mobile) traite vos données personnelles.

## 1. Résumé en une phrase

L'application stocke vos données **uniquement sur votre appareil**, sans
compte ni inscription ni publicité — mais certaines fonctionnalités
optionnelles, décrites en détail ci-dessous, transmettent des informations
à des services tiers lorsque vous les utilisez explicitement.

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
fonctionnalités. Elle se connecte à internet dans les cas suivants,
toujours à votre initiative explicite :

- **Import d'une recette depuis un lien** : les navigateurs empêchant une
  application web de récupérer directement le contenu d'un autre site,
  cette fonctionnalité transmet l'adresse que vous collez à l'un des
  services intermédiaires suivants (essayés automatiquement l'un après
  l'autre) pour contourner cette restriction technique : Jina AI Reader
  (r.jina.ai), allorigins.win, codetabs.com, cors.x2u.in, cors.lol,
  corsfix.com. Ces services reçoivent l'adresse que vous avez collée afin
  de récupérer la page à votre place ; consultez leurs propres politiques
  de confidentialité pour savoir comment ils traitent ces requêtes.
- **Import de recette par photo (reconnaissance de texte)** : cette
  fonctionnalité s'exécute directement sur votre appareil, via une
  bibliothèque (Tesseract.js) téléchargée une seule fois depuis un serveur
  de distribution de contenu (jsDelivr) lors de la première utilisation.
  Aucune photo ni aucun texte n'est envoyé à un serveur externe : seule la
  bibliothèque elle-même est téléchargée, pas vos données.
- **Génération et lecture de QR code, export PDF** : ces fonctionnalités
  utilisent des bibliothèques techniques également téléchargées depuis des
  serveurs de distribution de contenu (cdnjs, jsDelivr) lors de la première
  utilisation. Vos données (recettes, listes) ne sont jamais transmises à
  ces serveurs, qui ne font que fournir le code nécessaire au
  fonctionnement de ces outils sur votre appareil.
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
