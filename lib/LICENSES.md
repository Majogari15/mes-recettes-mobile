# Licences des bibliothèques embarquées (dossier `lib/`)

Ce dossier contient des bibliothèques tierces embarquées localement,
pour un fonctionnement hors connexion fiable, sans dépendre d'un CDN
externe. Chacune conserve sa licence d'origine.

## jsQR (`jsQR.js`)

- Version : 1.4.0
- Licence : Apache License 2.0
- Site du projet : https://github.com/cozmo/jsQR
- Utilisation dans l'application : lecture de QR code (scan par caméra,
  choix d'une image, ou coller un texte de QR)

## jsPDF (`jspdf.umd.min.js`)

- Version : 2.5.1
- Licence : MIT
- Copyright (c) 2010-2021 James Hall et contributeurs (voir l'en-tête du
  fichier lui-même pour la liste complète)
- Site du projet : https://github.com/parallax/jsPDF
- Utilisation dans l'application : export de recettes et de listes de
  courses au format PDF

## qrcode-generator (`qrcode-generator.js`)

- Version : 1.0.3
- Licence : MIT
- Site du projet : https://github.com/kazuhikoarase/qrcode-generator
- Utilisation dans l'application : génération de QR code (partage d'une
  recette ou d'une liste de courses)

---

Aucune de ces bibliothèques ne collecte ni ne transmet de données —
elles s'exécutent entièrement sur l'appareil de l'utilisateur. Voir
`POLITIQUE_DE_CONFIDENTIALITE.md` pour le détail.
