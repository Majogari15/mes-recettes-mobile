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

## Tesseract.js (`tesseract/`)

- Version : 7.0.0 (`tesseract.min.js`, `worker.min.js`)
- Moteur WASM (`tesseract-core*.wasm.js`) : tesseract.js-core, version
  7.0.0 — verrouillée sur la même version majeure/mineure que
  Tesseract.js lui-même, comme recommandé par le projet
- Licence : Apache License 2.0 (bibliothèque et moteur WASM)
- Site du projet : https://github.com/naptha/tesseract.js et
  https://github.com/naptha/tesseract.js-core
- Utilisation dans l'application : reconnaissance de texte (OCR) pour
  l'import de recette par photo — entièrement sur l'appareil, aucune
  photo ni texte reconnu n'est envoyé où que ce soit
- 6 variantes du moteur WASM incluses (`tesseract-core.wasm.js`,
  `-simd.wasm.js`, `-lstm.wasm.js`, `-simd-lstm.wasm.js`, et les 2
  nouvelles variantes "Relaxed SIMD" introduites en v7,
  `-relaxedsimd.wasm.js` et `-relaxedsimd-lstm.wasm.js`) : Tesseract.js
  choisit lui-même celle compatible avec l'appareil au moment de
  l'exécution — ne fournir qu'une seule variante fixe empêcherait l'OCR
  de fonctionner sur un appareil ne supportant pas les instructions
  SIMD/Relaxed SIMD

### Données de langue (`tesseract/lang/*.traineddata.gz`)

- Format : tessdata, version 4.0.0, palier qualité "standard" (meilleure
  précision, au prix d'un fichier plus volumineux qu'un palier "rapide")
- Langues incluses : français (`fra`), anglais (`eng`), espagnol
  (`spa`), allemand (`deu`)
- Licence : Apache License 2.0, projet Tesseract OCR
  (https://github.com/tesseract-ocr/tessdata)
- Ces fichiers ne sont volontairement PAS inclus dans le
  préchargement de l'application (voir `sw.js`) : chacun n'est
  téléchargé qu'au premier import photo dans cette langue précise, puis
  mis en cache pour les usages suivants, y compris hors connexion

---

Aucune de ces bibliothèques ne collecte ni ne transmet de données —
elles s'exécutent entièrement sur l'appareil de l'utilisateur. Voir
`POLITIQUE_DE_CONFIDENTIALITE.md` pour le détail.
