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
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

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

### 1.4 — Duplication d'une recette *(testé en production, v123)*
- **Manipulation** : dupliquer une recette ayant favori/historique/notes
  personnelles remplis.
- **Résultat attendu** : la copie n'hérite ni du favori, ni de l'historique,
  ni des notes personnelles ; tout le reste (ingrédients, photo) est identique.
- **Résultat obtenu** : ⚠️ Défaut trouvé en v123 — favori, historique, note
  chiffrée, avis famille et améliorations correctement effacés, mais le
  champ "Notes personnelles" textuel restait dupliqué (oubli dans le code).
  **Corrigé** et retesté : ✅ Réussi.
- **Appareil** : testé en production (v123), correctif v124

### 1.5 — Analyse des ingrédients : unités-contenants et alternatives *(simulé)*
- **Manipulation** : analyser "1 boîte de purée de tomate", "2 sachets de
  levure", "1 pot de crème", "3 tranches de jambon", "2 gousses ail", "1 oie
  ou 1 canard", et un cas de contrôle "1 citron ou 2 citrons verts" (nombres
  différents, ne doit rien changer).
- **Résultat attendu** : unité reconnue (boîte/sachet/pot/tranche/gousse) au
  lieu de "pièce" générique ; nombre redondant après "ou" supprimé
  uniquement s'il est identique à la quantité déjà extraite.
- **Résultat obtenu** : ✅ Réussi — les 5 unités correctement reconnues ;
  "oie ou canard" nettoyé ; "1 citron ou 2 citrons verts" resté inchangé
  (nombres différents, correctement préservés).
- **Version testée** : v121
- **Complément (testé en production, v123)** : les 5 nouvelles unités
  étaient correctement enregistrées et affichées après sauvegarde, mais le
  menu déroulant du formulaire d'import/modification les affichait vides
  (absentes de la liste des options). **Corrigé** (ajoutées à
  `UNIT_OPTIONS`, source commune à tous les menus d'unité de l'app) et
  retesté : ✅ Réussi — "boîte" et "gousse" correctement sélectionnées dans
  le menu, pas vides.

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
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

---

## 3. Import par lien

### 3.1 — Import Marmiton via le Worker *(physique — déjà testé une fois par l'utilisateur)*
- **Résultat attendu** : titre, photo, personnes, temps, ingrédients (avec
  quantités correctement recalculées), et préparation complète tous importés.
- **Résultat obtenu** : ✅ Réussi (rapporté par l'utilisateur, cassoulet
  Marmiton, 8 personnes, 17 ingrédients, 9 étapes, description 1037/1037
  caractères).
- **Appareil** : appareil de l'utilisateur (non précisé)
- **Version testée** : v118, reconfirmé en v123 (8 personnes, 40 min,
  330 min, 17 ingrédients, 9 étapes)

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
- **Résultat obtenu** : Smartphone Reussi / Tablette Reussi
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour
- **Version testée** : v117

### 4.10 — Cycle physique tablette → téléphone *(physique, prioritaire)*
- **Manipulation** : afficher un multi-QR (4-5 parties) sur une tablette,
  scanner avec un téléphone.
- **Résultat attendu** : import réussi, recette complète.
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

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
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

### 6.2 — Fonctions indisponibles hors connexion *(corrigé v124)*
- **Manipulation** : tenter un import par lien hors connexion.
- **Résultat attendu** : message clair, pas de plantage silencieux.
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel — pas
  de plantage, mais le message affiché ("Le site n'est peut-être pas
  compatible, ou le lien est incorrect") était trompeur, ne mentionnant pas
  l'absence de connexion pourtant la cause la plus probable. **Corrigé** :
  message spécifique affiché quand `navigator.onLine` est faux, testé et
  confirmé.
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

---

## 7. Mise à jour de la PWA *(entièrement physique)*

### 7.1 — Mise à jour v118/v119 → v121 sans perte de données
- **Manipulation** : avoir des données sur une ancienne version installée,
  mettre à jour vers la dernière version.
- **Résultat attendu** : toutes les recettes/courses/garde-manger présentes
  après la mise à jour.
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

### 7.2 — Numéro de version affiché correspond
- **Manipulation** : ouvrir l'écran Sauvegarde après mise à jour.
- **Résultat attendu** : le numéro affiché correspond à la version
  effectivement installée.
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

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
- **Résultat obtenu** : Smartphone fonctionnel / Tablette fonctionnel
- **Appareil** : Smartphone Samsung A06 (a jour) / Tablete Lenovo android 11 chrome pas a jour

### 8.6 — Étoiles : groupe radio complet (une seule tabulable, flèches) *(simulé + confirmé en production)*
- **Manipulation** : vérifier qu'une seule étoile a `tabindex="0"` ; depuis
  l'étoile 1, appuyer 2× flèche droite (doit arriver à 3) ; 5× flèche gauche
  depuis 3 (doit s'arrêter à 1, jamais en dessous) ; 10× flèche droite
  (doit s'arrêter à 5, jamais au-dessus).
- **Résultat attendu** : navigation correcte aux flèches, limites
  respectées, clic toujours fonctionnel (non-régression).
- **Résultat obtenu** : ✅ Réussi — une seule étoile tabulable confirmée ;
  flèche droite ×2 → 3 (focus suit) ; flèche gauche ×5 → arrêt à 1 ; flèche
  droite ×10 → arrêt à 5 ; clic sur étoile 2 → 2 (non-régression confirmée).
  Reconfirmé sur la v123 publiée (une seule étoile tabulable, 2× flèche
  droite → étoile 3).
- **Version testée** : v123

---

## 9. Partage et export Android *(entièrement physique)*

### 9.1 — Sauvegarde automatique vers Google Drive *(clarifié v124)*
- **Manipulation** : exporter une sauvegarde avec la fonction "backup
  automatique" Android activée.
- **Résultat attendu** : le fichier apparaît ensuite dans Drive.
- **Résultat obtenu** : ⚠️ Pas un bug de l'app, mais une incompréhension du
  texte d'astuce affiché. Le fichier apparaît bien dans le dossier
  Téléchargements de l'appareil, mais **cette sauvegarde Android est
  propre à chaque appareil** (utile pour restaurer ce même appareil après
  une réinitialisation), **pas une synchronisation entre appareils** — le
  fichier n'apparaît donc pas automatiquement sur un autre appareil.
  **Corrigé** : texte de l'astuce clarifié dans les 4 langues, orientant
  vers le bouton "Partager" (déjà testé avec succès, test 2.5) pour un
  vrai transfert entre appareils.
- **Appareil** : appareil de test de l'utilisateur

### 9.2 — Enregistrement d'un QR en image *(cause racine trouvée et corrigée, v126)*
- **Résultat attendu** : image PNG valide dans la galerie, nommée
  correctement (avec suffixe `-1sur3` etc. si multi-QR), relisible ensuite
  via "Choisir une image".
- **Résultat obtenu** : ✅ Enregistrement et suffixes corrects sur les deux
  appareils. ⚠️ Défaut réel trouvé : rescanner l'image ainsi enregistrée
  échouait avec "[object Event]" sur les deux appareils. **Vraie cause**
  identifiée (pas seulement le message d'erreur) : le fichier enregistré
  portait l'extension `.png` mais contenait en réalité un **GIF**
  (confirmé : `lib/qrcode-generator.js` produit
  `data:image/gif;base64,...`) — un fichier dont le contenu ne correspond
  pas à son extension, refusé par certains décodeurs. **Corrigé en
  profondeur** :
  1. Le bouton "Enregistrer" redessine désormais l'image sur un canvas et
     exporte un **vrai PNG** (`canvas.toBlob(..., "image/png")`) — testé :
     signature de fichier `\x89PNG...` confirmée, plus jamais `GIF8`.
  2. Le nouveau PNG reste correctement décodable (vérifié avec OpenCV,
     décodeur indépendant).
  3. Repli ajouté pour les **anciens fichiers déjà enregistrés** avant ce
     correctif (toujours des GIF nommés `.png`) : détection par signature
     réelle des octets, pas par extension — testé, un ancien fichier GIF
     se charge maintenant correctement.
  4. Découverte additionnelle en testant : le chargement d'image via
     `Blob` + `URL.createObjectURL()` s'est révélé peu fiable (échec
     constaté même pour un PNG parfaitement valide dans certains
     contextes) — remplacé par une URL `data:` construite directement à
     partir des octets réels du fichier, avec détection du type par
     signature plutôt que par extension. Plus robuste pour tous les cas
     (PNG, GIF, ancien ou nouveau).
- **Appareil** : Smartphone Samsung A06 / Tablette Lenovo (défaut
  original) — correctifs testés en simulation, **redemande une
  vérification physique** pour confirmer sur les deux appareils réels.

---

## 10. Diagnostic, Worker et manifeste

### 10.1 — Panneau de diagnostic *(simulé)*
- **Manipulation** : ouvrir Sauvegarde → Diagnostic, vérifier les 12 lignes,
  tester le bouton "Copier le diagnostic".
- **Résultat attendu** : version app et cache correctes, navigateur/système
  détectés, service d'import et dernière sauvegarde affichés, copie
  fonctionnelle — jamais de recette, nom, adresse ou photo.
- **Résultat obtenu** : ✅ Réussi — les 12 lignes correctement remplies
  (ex. "App version : v121", "Cache version : v121"), bouton copier
  confirmé (contenu du presse-papiers vérifié).
- **Version testée** : v122

### 10.2 — Worker : limite de longueur d'URL cible *(simulé + confirmé en production)*
- **Manipulation** : simuler la vérification sur une URL normale (75
  caractères), une URL abusive (3000+ caractères), et une URL à caractères
  spéciaux (50 caractères réels mais 122 une fois encodée dans la requête).
- **Résultat attendu** : la limite de 2048 caractères s'applique à l'adresse
  cible **décodée**, jamais à la longueur artificiellement gonflée par
  l'encodage.
- **Résultat obtenu** : ✅ Réussi — URL normale acceptée, URL abusive
  rejetée, URL à caractères spéciaux correctement mesurée sur sa longueur
  décodée (50), pas la longueur encodée (122). **Confirmé en production
  sur le vrai Worker déployé** : URL normale → HTTP 200 ; URL de plus de
  2048 caractères → HTTP 414 "URL too long" ; en-têtes CORS limités à
  `https://majogari15.github.io`.
- **Version testée** : worker.js (non versionné avec l'app — à redéployer
  manuellement sur Cloudflare)
- **Note** : la vraie limitation du nombre de requêtes par IP reste en
  attente (nécessite Wrangler + binding Rate Limiting, ou un domaine
  personnalisé + règle WAF — voir échanges du 04/09/2026).

### 10.3 — Manifeste externalisé (`manifest-loader.js`) *(simulé + confirmé en production)*
- **Manipulation** : vérifier la sélection du bon manifeste après
  externalisation du script (déplacé hors de `index.html`, chargé après la
  CSP).
- **Résultat attendu** : aucune régression — même comportement qu'avant
  l'externalisation.
- **Résultat obtenu** : ✅ Réussi — navigateur en français sans langue
  enregistrée → `manifest.json` ; langue "de" enregistrée →
  `manifest-de.json`. **Confirmé en production** : fichier présent dans le
  cache du service worker, changement FR→EN reflété correctement
  (`manifest.json` → `manifest-en.json` après rechargement).
- **Version testée** : v123

---

## Modèle de tableau pour les tests physiques

| Test | Appareil | Android | Chrome | PWA installée ? | Résultat | Remarque |
|---|---|---|---|---|---|---|
| | | | | | Réussi / Échoué | |

---

## Résumé — état au 04/09/2026 (v126)

- **Tests simulés réussis** : 32
- **Campagne de tests physiques réalisée par l'utilisateur** (2 appareils :
  Smartphone Samsung A06 à jour, Tablette Lenovo Android 11 non à jour) —
  quasi-totalité des tests physiques du document effectués
- **6 défauts réels trouvés en conditions réelles, tous corrigés** :
  1. Notes personnelles dupliquées (v124)
  2. Nouvelles unités absentes du menu déroulant du formulaire, données
     bien enregistrées (v124)
  3. Message trompeur lors d'un import hors connexion (v125)
  4. Message "[object Event]" lors du choix d'une image invalide —
     symptôme d'une cause plus profonde trouvée ensuite : le QR
     enregistré était en réalité un GIF portant l'extension `.png`.
     Corrigé en profondeur : vrai PNG exporté désormais, repli pour les
     anciens fichiers, chargement d'image rendu plus robuste (v125→v126)
  5. Astuce Google Drive trompeuse — clarifiée, pas un bug de code (v125)
  6. Phrase coupée dans la documentation du test 8.5 (v126)
- **Tests physiques restants** : 3 — 3.3 et 3.4 (pas urgent), et **9.2 à
  revérifier sur les deux appareils réels** pour confirmer que la vraie
  cause racine (GIF nommé .png) est bien résolue en conditions réelles,
  le correctif v126 n'ayant pu être testé qu'en simulation

Aucune régression détectée dans les tests simulables. La quasi-totalité des
tests physiques a maintenant été réalisée par l'utilisateur sur deux
appareils réels, avec des résultats globalement très positifs — les
défauts trouvés étaient tous des problèmes d'affichage ou de message,
jamais de perte de données.
