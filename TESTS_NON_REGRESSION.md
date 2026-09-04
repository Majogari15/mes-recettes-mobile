# Tests de non-régression — Mes Recettes, Mes Courses

Ce document sert à vérifier, avant chaque nouvelle version publiée, que les
corrections déjà apportées n'ont pas été cassées par un changement ultérieur.

**Deux types de tests dans ce document :**
- **Simulé (Claude)** : testé automatiquement via un navigateur sans interface
  graphique (Playwright), avec un résultat réel obtenu et daté. Ne remplace pas
  un test sur un vrai appareil, mais confirme que la logique fonctionne
  correctement dans son ensemble.
- **Physique (à faire par vous)** : nécessite un vrai téléphone/tablette
  (caméra réelle, comportement Android, plusieurs appareils). Les lignes
  "Résultat obtenu" et "Appareil" sont à remplir au fur et à mesure de vos
  tests. Un modèle de tableau est fourni à la fin de chaque section physique.

Pour chaque test simulé : conditions initiales → manipulation → résultat
attendu → résultat obtenu → version testée.

---

## 1. Recettes et brouillons

### 1.1 — Modification conserve le journal de préparation *(simulé)*
- **Conditions initiales** : une recette avec `timesCooked: 2` et un journal
  de 1 entrée.
- **Manipulation** : modifier le nom de la recette et enregistrer.
- **Résultat attendu** : `timesCooked` et le journal restent inchangés après
  l'enregistrement.
- **Résultat obtenu** : ✅ Réussi — `timesCooked === 2`, journal toujours à 1
  entrée après modification.
- **Version testée** : v121

### 1.2 — Brouillon de nouvelle recette *(physique)*
- **Manipulation** : commencer une nouvelle recette, remplir plusieurs champs,
  mettre l'application en arrière-plan (pas fermer), revenir plus tard.
- **Résultat attendu** : proposition de restaurer le brouillon avec tous les
  champs remplis.
- **Résultat obtenu** : _à tester_
- **Appareil** : _à renseigner_

### 1.3 — Brouillon de modification (tous les champs) *(simulé)*
- **Conditions initiales** : recette existante, brouillon capturé pour cette
  même recette avec 15 champs modifiés (nom, catégorie, difficulté,
  personnes, temps, 3 cases à cocher, description, notes, note personnelle,
  avis famille, à améliorer, difficulté réelle).
- **Manipulation** : rouvrir la modification de cette recette.
- **Résultat attendu** : les 15 champs affichent les valeurs du brouillon, pas
  celles enregistrées.
- **Résultat obtenu** : ✅ Réussi — les 15 champs vérifiés individuellement,
  tous corrects.
- **Version testée** : v111

### 1.4 — Duplication d'une recette *(physique)*
- **Manipulation** : dupliquer une recette ayant favori/historique/notes
  personnelles remplis.
- **Résultat attendu** : la copie n'hérite ni du favori, ni de l'historique,
  ni des notes personnelles ; tout le reste (ingrédients, photo) est identique.
- **Résultat obtenu** : _à tester_
- **Appareil** : _à renseigner_

---

## 2. Sauvegarde et restauration

### 2.1 — Restauration atomique (panne en plein milieu) *(simulé)*
- **Conditions initiales** : une recette "originale" en base ; fichier de
  restauration contenant une nouvelle recette valide **et** un article de
  liste de courses invalide (sans identifiant).
- **Manipulation** : lancer `importAllData(..., "replace")`.
- **Résultat attendu** : soit tout réussit, soit rien n'est modifié (la
  recette "originale" doit rester si l'import échoue).
- **Résultat obtenu** : ✅ Réussi — après l'échec, la recette "originale" est
  toujours présente et seule, la nouvelle recette n'a jamais été écrite.
- **Version testée** : v100

### 2.2 — Validation avec rapport (éléments ignorés/corrigés) *(simulé)*
- **Conditions initiales** : fichier de sauvegarde avec 1 recette sans
  identifiant, 1 photo dangereuse (`javascript:...`), 2 nombres négatifs.
- **Manipulation** : `parseBackupFile()`.
- **Résultat attendu** : rapport indiquant 1 élément ignoré, 1 photo retirée,
  2 nombres corrigés.
- **Résultat obtenu** : ✅ Réussi — `ignoredCount: 1`, `photosRemoved: 1`,
  `numbersFixed: 2`, tous exacts.
- **Version testée** : v114

### 2.3 — Ingrédients personnalisés et surcharges restaurés *(simulé)*
- **Conditions initiales** : fichier avec un ingrédient personnalisé et une
  surcharge (allergènes) — tous deux utilisent `name` comme identifiant, pas
  `id`.
- **Manipulation** : `parseBackupFile()`.
- **Résultat attendu** : les deux enregistrements survivent à la validation
  (ne sont pas filtrés à tort).
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v121

### 2.4 — Sauvegarde de sécurité même sans recette *(simulé, testé en v99)*
- **Conditions initiales** : 0 recette, mais 1 article de liste de courses.
- **Manipulation** : import en mode "Remplacer tout".
- **Résultat attendu** : sauvegarde de sécurité déclenchée malgré l'absence
  de recette.
- **Résultat obtenu** : ✅ Réussi — confirmé lors du développement (v99).
- **Version testée** : v99

### 2.5 — Partage par fichier (Android) *(physique)*
- **Manipulation** : exporter une sauvegarde, utiliser le partage natif
  Android.
- **Résultat attendu** : le fichier s'exporte sans erreur `NotAllowedError`.
- **Résultat obtenu** : _à tester_
- **Appareil** : _à renseigner_

---

## 3. Import par lien

### 3.1 — Import Marmiton via le Worker *(physique — déjà testé une fois par l'utilisateur)*
- **Résultat attendu** : titre, photo, personnes, temps, ingrédients (avec
  quantités correctement recalculées), et préparation complète tous importés.
- **Résultat obtenu** : ✅ Réussi (rapporté par l'utilisateur, cassoulet
  Marmiton, 8 personnes, 17 ingrédients, 9 étapes, description 1037/1037
  caractères).
- **Appareil** : appareil de l'utilisateur (non précisé)
- **Version testée** : v118

### 3.2 — Repli Jina conserve le nombre de personnes *(simulé)*
- **Conditions initiales** : texte façon extraction Jina contenant
  "Pour 8 personnes".
- **Manipulation** : `parseOcrRecipeText()` puis construction du résultat de
  repli.
- **Résultat attendu** : `persons: 8`, pas `4`.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v120

### 3.3 — Worker indisponible → repli Jina *(physique, nécessite coupure temporaire du Worker)*
- **Résultat attendu** : import réussi via Jina, message indiquant si un
  champ est moins précis.
- **Résultat obtenu** : _à tester_

### 3.4 — Tous les services indisponibles *(physique)*
- **Résultat attendu** : message d'erreur compréhensible, pas de plantage.
- **Résultat obtenu** : _à tester_

---

## 4. QR simple et multi-QR

### 4.1 — QR simple, encodage UTF-8 correct *(simulé)*
- **Manipulation** : générer un QR compact avec accents, le relire.
- **Résultat attendu** : nom et quantités identiques après aller-retour.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v105

### 4.2 — QR simple, décodage réel avec un décodeur indépendant *(simulé)*
- **Manipulation** : générer un QR, le décoder avec OpenCV (décodeur
  professionnel indépendant de l'application).
- **Résultat attendu** : contenu décodé identique à l'original.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v106

### 4.3 — Multi-QR : découpage et réassemblage exacts *(simulé)*
- **Conditions initiales** : texte de 973 caractères (recette de cassoulet
  réaliste, 9 étapes).
- **Résultat attendu** : réassemblage identique caractère pour caractère.
- **Résultat obtenu** : ✅ Réussi — 973/973 caractères.
- **Version testée** : v116

### 4.4 — Multi-QR : lecture dans le désordre *(simulé)*
- **Manipulation** : générer 4 QR, les "scanner" dans un ordre aléatoire
  (3, 2, 0, 1).
- **Résultat attendu** : import réussi uniquement après la 4e partie, quel
  que soit l'ordre.
- **Résultat obtenu** : ✅ Réussi — description finale 2120/2120 caractères
  exacts, accents compris.
- **Version testée** : v119

### 4.5 — Multi-QR : fragment dupliqué ignoré *(simulé)*
- **Résultat attendu** : rescanner la même partie ne la compte pas deux fois.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v118

### 4.6 — Multi-QR : fragment incohérent rejeté *(simulé)*
- **Conditions initiales** : un fragment annonce 2 parties, un second (même
  lot) en annonce 3.
- **Résultat attendu** : le second fragment est rejeté, pas silencieusement
  accepté.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v121

### 4.7 — Multi-QR : somme de contrôle détecte une corruption *(simulé)*
- **Manipulation** : corrompre le contenu d'un fragment après découpage,
  avant reconstitution.
- **Résultat attendu** : import refusé, message d'erreur explicite.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v121

### 4.8 — Multi-QR : identifiants de lot uniques *(simulé)*
- **Manipulation** : générer 200 lots à la suite rapidement.
- **Résultat attendu** : 200 identifiants distincts, aucune collision.
- **Résultat obtenu** : ✅ Réussi — 200/200 uniques (testé aussi à 1000/1000
  lors du développement).
- **Version testée** : v121

### 4.9 — Caméra arrêtée à la fermeture (Échap) *(simulé + physique à confirmer)*
- **Résultat attendu** : `stop()` appelé sur le flux caméra même en cas de
  fermeture par Échap.
- **Résultat obtenu (simulé)** : ✅ Réussi (testé isolément, sans dépendre du
  chargement de jsQR qui échoue dans l'environnement de simulation).
- **Résultat obtenu (physique)** : _à tester — vérifier que le voyant caméra
  s'éteint immédiatement après Échap/Retour Android_
- **Version testée** : v117

### 4.10 — Cycle physique tablette → téléphone *(physique, prioritaire)*
- **Manipulation** : afficher un multi-QR (4-5 parties) sur une tablette,
  scanner avec un téléphone.
- **Résultat attendu** : import réussi, recette complète.
- **Résultat obtenu** : _à tester_
- **Appareil** : _à renseigner_

---

## 5. Courses et garde-manger

### 5.1 — Réduction garde-manger, calcul cumulé sur 2 recettes *(simulé)*
- **Conditions initiales** : 1 kg de farine en stock ; 2 recettes ayant
  chacune besoin de 800 g.
- **Résultat attendu** : après les deux ajouts, 600 g de farine sur la liste
  (le vrai manque), pas 0.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v102

### 5.2 — Réservation annulée = rien appliqué *(simulé)*
- **Manipulation** : ajouter une recette avec réduction du garde-manger, puis
  cliquer "Annuler" sur la confirmation.
- **Résultat attendu** : aucune réservation appliquée.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v121

### 5.3 — Édition et suppression individuelle d'un article *(simulé)*
- **Résultat attendu** : toucher un article ouvre la modification ; le bouton
  "×" le supprime avec confirmation.
- **Résultat obtenu** : ✅ Réussi (modification 1L→2L confirmée, suppression
  avec bon nom affiché confirmée).
- **Version testée** : v103

### 5.4 — Renommage d'ingrédient propagé partout *(simulé)*
- **Conditions initiales** : même ingrédient dans une recette et sur la liste
  de courses.
- **Résultat attendu** : renommer met à jour les deux emplacements.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v104 (retesté v121)

---

## 6. Mode hors connexion *(entièrement physique)*

### 6.1 — Chargement après mise en cache
- **Manipulation** : ouvrir l'application une première fois (en ligne), puis
  couper le réseau et relancer.
- **Résultat attendu** : l'application se charge normalement.
- **Résultat obtenu** : _à tester_

### 6.2 — Fonctions indisponibles hors connexion
- **Manipulation** : tenter un import par lien hors connexion.
- **Résultat attendu** : message clair, pas de plantage silencieux.
- **Résultat obtenu** : _à tester_

---

## 7. Mise à jour de la PWA *(entièrement physique)*

### 7.1 — Mise à jour v118/v119 → v121 sans perte de données
- **Manipulation** : avoir des données sur une ancienne version installée,
  mettre à jour vers la dernière version.
- **Résultat attendu** : toutes les recettes/courses/garde-manger présentes
  après la mise à jour.
- **Résultat obtenu** : _à tester_

### 7.2 — Numéro de version affiché correspond
- **Manipulation** : ouvrir l'écran Sauvegarde après mise à jour.
- **Résultat attendu** : le numéro affiché correspond à la version
  effectivement installée.
- **Résultat obtenu** : _à tester_

---

## 8. Accessibilité

### 8.1 — Fenêtres modales : Échap, piège de focus, restauration *(simulé)*
- **Résultat attendu** : `role="dialog"`, `aria-modal="true"`, Échap ferme et
  déclenche le nettoyage éventuel, le focus revient à l'élément déclencheur.
- **Résultat obtenu** : ✅ Réussi — les 4 vérifications passent.
- **Version testée** : v121 (fonctionnalité de base v108, généralisée v112,
  caméra v117)

### 8.2 — Étoiles accessibles au clavier *(simulé)*
- **Résultat attendu** : Tab atteint chaque étoile, Entrée/Espace la
  sélectionne.
- **Résultat obtenu** : ✅ Réussi (testé lors du développement, v108).
- **Version testée** : v108

### 8.3 — Autocomplétion ingrédients au clavier *(simulé)*
- **Résultat attendu** : flèches pour naviguer, Entrée pour sélectionner,
  Échap pour fermer.
- **Résultat obtenu** : ✅ Réussi (testé lors du développement, v110).
- **Version testée** : v110

### 8.4 — Contraste du texte atténué (mode clair) *(simulé, calcul)*
- **Résultat attendu** : ratio ≥ 4,5:1 sur fond crème (norme WCAG).
- **Résultat obtenu** : ✅ Réussi — 4,64:1 sur crème, 4,99:1 sur blanc.
- **Version testée** : v108

### 8.5 — Lecteur d'écran réel (TalkBack) *(physique)*
- **Manipulation** : activer TalkBack, naviguer dans l'application.
- **Résultat attendu** : titres des fenêtres annoncés correctement (pas
  seulement "dialogue").
- **Résultat obtenu** : _à tester_

---

## 9. Partage et export Android *(entièrement physique)*

### 9.1 — Sauvegarde automatique vers Google Drive
- **Manipulation** : exporter une sauvegarde avec la fonction "backup
  automatique" Android activée.
- **Résultat attendu** : le fichier apparaît ensuite dans Drive.
- **Résultat obtenu** : _à tester_

### 9.2 — Enregistrement d'un QR en image
- **Résultat attendu** : image PNG valide dans la galerie, nommée
  correctement (avec suffixe `-1sur3` etc. si multi-QR).
- **Résultat obtenu** : _à tester_

---

## Modèle de tableau pour les tests physiques

| Test | Appareil | Android | Chrome | PWA installée ? | Résultat | Remarque |
|---|---|---|---|---|---|---|
| | | | | | Réussi / Échoué | |

---

## Résumé — état au 04/09/2026 (v121)

- **Tests simulés réalisés** : 25
- **Tests simulés réussis** : 25 / 25
- **Tests physiques restants** : 13, dont 1 déjà rapporté réussi par
  l'utilisateur (import Marmiton complet)

Aucune régression détectée dans les tests simulables à ce jour. Les tests
physiques (caméra réelle, comportement Android, plusieurs appareils, mode
hors connexion, mise à jour PWA) restent à la charge de l'utilisateur — ce
sont des conditions que Claude ne peut pas reproduire fidèlement dans son
environnement de simulation.
