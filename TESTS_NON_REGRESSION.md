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

### 2.3bis — Validation structurelle renforcée *(cause racine trouvée et corrigée, v150)*
- **Contexte** : la restauration ne validait pas encore la structure
  interne des recettes — un nom absent, une note personnelle hors de
  0-5, un ingrédient malformé, une catégorie/unité/difficulté inconnue,
  ou une entrée de journal de préparation corrompue pouvaient passer la
  validation et provoquer des erreurs à l'affichage ensuite (tri par
  `localeCompare`, widget d'étoiles).
- **Corrigé** : nom de recette non textuel remplacé par une chaîne
  vide ; note personnelle plafonnée à 0-5 ; catégorie/difficulté
  inconnues normalisées ; ingrédients non-objets retirés du tableau,
  nom non textuel et unité inconnue corrigés individuellement ;
  entrées de journal non-objets retirées. Nouveau compteur
  `structuralFixes` dans le rapport affiché à l'utilisateur.
- **Résultat obtenu** : ✅ Réussi — testé avec un fichier combinant
  tous ces défauts simultanément : nom devenu chaîne vide, note
  plafonnée à 5, catégorie/difficulté corrigées, 2 ingrédients
  malformés retirés (null et chaîne simple) sur 4, les 2 valides
  correctement conservés et corrigés (nom/unité), entrée de journal
  malformée retirée, `structuralFixes: 8` confirmé dans le rapport.
- **Version testée** : v150

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
- **Doute résolu en v131** : l'utilisateur s'est demandé si c'était
  vraiment le Worker qui fonctionnait ou si Jina faisait le travail en
  coulisse. Un champ de diagnostic ("Dernière erreur du Worker") a été
  ajouté pour clarifier ce genre de doute à l'avenir. **Confirmé via le
  panneau Diagnostic** : le Worker Cloudflare fonctionne réellement (5
  imports d'affilée réussis, "Dernier service d'import utilisé" affiche
  bien "Worker Cloudflare", pas "Jina AI Reader").

### 3.1bis — Lien collé sans protocole (https://) *(cause racine trouvée et corrigée, v133)*
- **Contexte** : l'utilisateur a rencontré `worker_http_400 (Invalid
  url)` en réimportant la même recette Marmiton qui avait pourtant
  fonctionné plus tôt. Message du Worker enrichi (v132) pour inclure le
  détail technique exact : `Invalid URL string., length=63`.
- **Enquête** : la vraie URL fait 75 caractères ; 63 caractères
  correspond exactement à la même adresse **sans le préfixe
  "https://www."** — confirmé en testant : `new URL()` échoue
  effectivement sur cette version tronquée. L'utilisateur avait
  vraisemblablement collé le lien depuis un endroit qui l'affiche sans
  protocole (comme cela s'est produit dans son propre message de test).
- **Corrigé** : le champ d'import ajoute désormais automatiquement
  "https://" si l'adresse collée n'a pas de protocole, au lieu de la
  rejeter froidement.
- **Résultat obtenu** : ✅ Réussi — testé avec le cas exact rencontré
  (URL sans protocole → corrigée → valide) et 3 cas de non-régression
  (http://, https://, HTTPS:// en majuscules → tous inchangés,
  correctement reconnus comme ayant déjà un protocole).
- **Version testée** : v133
- **Cause confirmée par l'utilisateur** : le copier-coller via Google
  Lens (recherche visuelle depuis l'écran) extrait le texte affiché du
  lien, pas l'adresse réelle — le protocole "http://www." disparaît
  systématiquement dans ce cas précis. Le correctif v133 gère
  correctement ce scénario (avec ou sans le "www." manquant en plus du
  protocole).

### 3.1ter — Repli Jina : conversion "Xh YY" en minutes *(cause racine trouvée et corrigée, v134)*
- **Contexte** : l'utilisateur a rapporté qu'un temps de cuisson affiché
  comme "5h30" sur le site importait "5 min" au lieu de 330 minutes.
- **Cause** : la recherche ne capturait qu'un seul nombre après
  "Cuisson :", ignorant complètement le "h" et tout ce qui suivait.
- **Corrigé** : nouvelle fonction de conversion gérant "Xh YY" (heures +
  minutes), "Xh" seul, et le format simple en minutes.
- **Résultat obtenu** : ✅ Réussi — testé avec "5h30" → 330 minutes
  (cas exact rapporté), et non-régression confirmée sur le format
  simple "35 min" → 35 minutes (inchangé).
- **Version testée** : v134

### 3.1quater — Repli Jina : contenu hors-sujet dans la description *(cause racine trouvée et corrigée, v134)*
- **Contexte** : l'utilisateur a rapporté que la description importée
  incluait des sections sans rapport avec la recette (commentaires,
  "Qu'est-ce qu'on mange ce soir ?" et suggestions diverses du site).
- **Cause** : la liste des marqueurs de fin de description ne couvrait
  pas tous les intitulés utilisés par les sites de recettes.
- **Corrigé** : liste élargie (découvrir aussi, recettes similaires,
  publicité, newsletter, partager/imprimer la recette, etc.).
- **Résultat obtenu** : ✅ Réussi — testé avec un texte contenant "Qu'est-
  ce qu'on mange ce soir ?" et "Commentaires" après les vraies étapes :
  les deux sont maintenant exclues, seules les étapes réelles restent
  dans la description.
- **Version testée** : v134

### 3.2 — Repli Jina conserve le nombre de personnes *(simulé)*
- **Conditions initiales** : texte façon extraction Jina contenant
  "Pour 8 personnes".
- **Manipulation** : `parseOcrRecipeText()` puis construction du résultat de
  repli.
- **Résultat attendu** : `persons: 8`, pas `4`.
- **Résultat obtenu** : ✅ Réussi.
- **Version testée** : v120

### 3.3 — Worker indisponible → repli Jina *(testé via le mode de test v130)*
- **Résultat attendu** : import réussi via Jina, message indiquant si un
  champ est moins précis.
- **Résultat obtenu** : ✅ Réussi — testé avec `?importtest=jina` (Worker
  volontairement contourné), import réussi via Jina, confirmé dans le
  diagnostic ("Jina AI Reader (test)").
- **Appareil** : appareil de l'utilisateur

### 3.4 — Tous les services indisponibles *(testé via le mode de test v130)*
- **Résultat attendu** : message d'erreur compréhensible, pas de plantage.
- **Résultat obtenu** : ✅ Réussi — testé avec `?importtest=fail` (tous les
  services volontairement contournés), message d'erreur clair affiché,
  aucun plantage.
- **Appareil** : appareil de l'utilisateur

### 3.4bis — Mode de test restreint à localhost *(cause racine trouvée et corrigée, v137)*
- **Contexte** : `?importtest=...` restait exploitable par n'importe qui
  sur le site public déployé, pouvant perturber volontairement l'import
  d'un autre utilisateur.
- **Corrigé** : le paramètre n'est désormais pris en compte que si
  `location.hostname` correspond à localhost/127.0.0.1 — ignoré
  silencieusement partout ailleurs, y compris sur le site public.
- **Résultat obtenu** : ✅ Réussi — testé sur un vrai serveur local
  (`127.0.0.1`, mode pris en compte) et avec un nom d'hôte simulé de
  production (`majogari15.github.io`, mode correctement ignoré).
- **Note** : les futurs tests 3.3/3.4 nécessiteront un serveur local
  plutôt que le site public déployé.
- **Version testée** : v137

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

### 5.0bis — Fusion d'ingrédients propagée partout *(cause racine trouvée et corrigée, v150)*
- **Contexte** : fusionner deux ingrédients en double remplaçait bien
  l'ancien nom dans les recettes, mais jamais dans la liste de
  courses, le garde-manger, ni les listes de courses enregistrées —
  l'ancien ingrédient pouvait donc rester visible à ces endroits après
  une fusion.
- **Corrigé** : `mergeIngredientNames()` propage désormais le
  renommage aux 3 emplacements manquants, chacun persisté
  individuellement.
- **Résultat obtenu** : ✅ Réussi — testé avec une recette, un article
  de courses, un article de garde-manger et une liste enregistrée
  portant tous le même ancien nom : les 4 emplacements confirmés
  correctement renommés après la fusion.
- **Version testée** : v150

### 5.0ter — Unités non convertibles enfin distinctes *(cause racine trouvée et corrigée, v150)*
- **Contexte** : pièce, boîte, sachet, pot, tranche, gousse et autre
  étaient toutes regroupées sous une seule catégorie "comptable"
  générique — une boîte au garde-manger pouvait donc à tort couvrir
  une pièce demandée par une recette, et un prix fixé au sachet
  pouvait s'appliquer à tort à une quantité en boîte.
- **Corrigé** : chaque unité non convertible devient son propre
  groupe distinct ("count:unité") — seuls le poids (g/kg) et le
  volume (cl/L) restent de vrais groupes convertibles entre eux.
- **Résultat obtenu** : ✅ Réussi — testé sur le garde-manger (boîte ne
  couvre plus une pièce, mais boîte contre boîte fonctionne toujours,
  et kg/g reste convertible) et sur le calcul de prix (prix au sachet
  ne s'applique plus à une quantité en boîte, mais sachet contre
  sachet fonctionne toujours).
- **Version testée** : v150

### 5.0 — Multi-QR pour la liste de courses *(cause racine trouvée et corrigée, v136)*
- **Contexte** : contrairement aux recettes, la liste de courses ne
  bénéficiait pas du multi-QR — au-delà de 900 caractères, les derniers
  articles étaient silencieusement retirés (avec un avertissement
  visible, mais un transfert incomplet quand même).
- **Corrigé** : réutilisation complète du système multi-QR partagé avec
  les recettes (découpage, navigation, somme de contrôle, réassemblage
  dans n'importe quel ordre) — plus aucun article n'est jamais retiré.
  Fonction de troncature devenue inutile retirée, ainsi que sa
  traduction associée dans les 4 langues.
- **Résultat obtenu** : ✅ Réussi — testé avec 30 articles (largement
  au-delà de l'ancienne limite), génération en 2 QR confirmée, scan dans
  le désordre, **30 articles sur 30 retrouvés après import, premier et
  dernier article présents**, aucune perte.
- **Version testée** : v136

### 5.0bis — Rappel de sauvegarde pour toutes les données importantes *(cause racine trouvée et corrigée, v138)*
- **Contexte** : le rappel après 14 jours ne vérifiait que
  `state.recipes.length > 0`, ne s'affichant donc jamais pour quelqu'un
  n'ayant que des courses, un garde-manger, des menus ou des plannings.
- **Corrigé** : vérifie désormais recettes, courses, garde-manger,
  menus, modèles de planning, historique de planning, listes de courses
  enregistrées, et le planning hebdomadaire actif.
- **Résultat obtenu** : ✅ Réussi — testé avec 5 scénarios : rien du tout
  (pas de rappel, correct), seulement des courses (rappel affiché),
  seulement un garde-manger (rappel affiché), seulement un planning
  hebdomadaire (rappel affiché), et avec des recettes (non-régression,
  toujours affiché). Un premier test avait échoué à tort à cause d'une
  détection cherchant le mot français alors que l'app tournait en
  anglais — corrigé avec une détection par l'emoji 💾, indépendante de
  la langue, confirmant que le vrai correctif fonctionnait déjà.
- **Limite connue** : les ingrédients personnalisés seuls (sans aucune
  autre donnée) ne déclenchent pas le rappel, n'étant pas chargés en
  mémoire de façon permanente — cas très marginal, non couvert par ce
  correctif.
- **Version testée** : v138

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

### 8.5bis — Langue HTML synchronisée *(cause racine trouvée et corrigée, v139)*
- **Contexte** : l'interface changeait correctement de langue, mais
  `<html lang="fr">` restait figé — un lecteur d'écran pouvait donc
  prononcer l'anglais, l'espagnol ou l'allemand comme si c'était du
  français.
- **Corrigé** : `setLang()` met maintenant à jour `document.
  documentElement.lang` et `document.title` à chaque changement ; la
  langue détectée au premier chargement (avant tout choix manuel) est
  également synchronisée dès le départ.
- **Résultat obtenu** : ✅ Réussi — testé avec une langue "de" déjà
  enregistrée au chargement (`html lang="de"` confirmé, titre "Meine
  Rezepte") et un changement manuel vers l'espagnol en cours de session
  (`html lang="es"` confirmé, titre "Mis Recetas"). Confirmé aussi que
  le chargement initial correspond bien à la langue du navigateur quand
  rien n'est encore enregistré (testé avec le navigateur réglé en
  français : `html lang="fr"` correct).
- **Version testée** : v139

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

### 9.1 — Sauvegarde automatique vers Google Drive *(clarifié v124, approfondi v127, cause racine du partage trouvée v129)*
- **Manipulation** : exporter une sauvegarde avec la fonction "backup
  automatique" Android activée.
- **Résultat attendu** : le fichier apparaît ensuite dans Drive.
- **Résultat obtenu** : ⚠️ Pas un bug de l'app, mais une incompréhension du
  texte d'astuce affiché — approfondi une seconde fois après une remarque
  externe. Recherche effectuée : il existe en réalité **deux mécanismes
  Android différents** — l'ancienne "sauvegarde automatique des
  applications" (ne couvre pas Téléchargements) et une **nouvelle**
  fonction de sauvegarde spécifique du dossier Téléchargements vers
  Drive, déployée progressivement depuis février 2026 (stable depuis
  fin juillet 2026), **désactivée par défaut**. Plutôt que de continuer à
  décrire un comportement Android qui varie selon la version/le
  déploiement, le texte a été **simplifié pour ne plus faire aucune
  affirmation sur le fonctionnement interne d'Android** — il se
  concentre uniquement sur ce que l'app garantit elle-même (le bouton
  "Exporter" reste local à l'appareil ; "Partager" est la vraie solution
  pour un autre appareil).
  **Défaut additionnel trouvé et corrigé** : si le partage échoue
  réellement (pas juste annulé par l'utilisateur), le code téléchargeait
  silencieusement le fichier en affichant "export réussi" — donnant
  l'impression trompeuse que le partage avait fonctionné. **Corrigé** :
  message explicite désormais affiché ("le partage direct n'est pas
  disponible... enregistré dans Téléchargements à la place"), testé et
  confirmé avec un échec de partage simulé.
- **Appareil** : appareil de test de l'utilisateur

  - **Défaut additionnel trouvé grâce au diagnostic v128** : l'utilisateur
    a rapporté l'erreur exacte via le nouveau panneau de diagnostic —
    `NotAllowedError — Permission denied`. Recherche menée sur la
    documentation officielle MDN du Web Share API, **deux causes
    confirmées et corrigées ensemble en v129** :
    1. **Extension incohérente avec le type MIME** : le fichier partagé
       utilisait déjà `text/plain` (bon choix) mais gardait l'extension
       `.json` — or la liste officielle des types de fichiers
       partageables (vérifiée directement sur MDN) associe `.txt` à
       `text/plain`, jamais `.json`. **Corrigé** : nom de fichier dédié
       au partage avec extension `.txt`, testé — fichier transmis à
       `navigator.share()` confirmé `nom.txt` / `text/plain` exacts.
    2. **Activation utilisateur potentiellement perdue** : le fichier
       était préchargé via une promesse, mais un `await` restait entre
       le clic et l'appel à `navigator.share()`. **Corrigé** : le bouton
       reste désactivé ("Préparation...") jusqu'à ce que le fichier soit
       entièrement résolu, puis le clic appelle `navigator.share()`
       sans aucun délai. Testé : bouton désactivé puis activé
       correctement, aucun `await` avant l'appel.
    3. Restauration élargie pour accepter `.txt` en plus de `.json`
       (par contenu, comme avant, mais aussi par sélecteur de fichier).
       **Testé** : cycle complet partage (.txt) → restauration → recette
       intacte, confirmé.
  - **Redemande une vérification physique** sur l'appareil Samsung pour
    confirmer que le partage fonctionne enfin réellement (impossible à
    tester avec certitude en simulation, `navigator.share()` n'étant pas
    disponible dans l'environnement de test).

### 9.2 — Enregistrement d'un QR en image *(cause racine trouvée, corrigée et confirmée physiquement, v126)*
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
- **Appareil** : Smartphone Samsung A06 / Tablette Lenovo — **✅ Confirmé
  fonctionnel sur les deux appareils réels après le correctif v126.**

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

## 11. Bibliothèques embarquées localement

### 11.1 — jsQR et jsPDF en local *(fourni par l'utilisateur, testé et intégré, v141)*
- **Contexte** : Claude ne pouvait pas récupérer ces deux fichiers
  complets avec ses outils (fichiers trop volumineux pour son outil de
  récupération web). L'utilisateur les a téléchargés lui-même et
  transmis directement.
- **Intégré** : `lib/jsQR.js` (257 Ko, Apache-2.0) et
  `lib/jspdf.umd.min.js` (364 Ko, MIT) — adresses CDN remplacées dans
  `app.js`, `index.html` et `sw.js` ; CSP resserrée (retrait de
  `cdnjs.cloudflare.com`, plus utilisé par rien) ; fichier
  `lib/LICENSES.md` créé pour conserver les mentions de licence ;
  politique de confidentialité mise à jour (seul Tesseract reste
  externe désormais).
- **Résultat obtenu** : ✅ Réussi — testé fonctionnellement (pas
  seulement un chargement) : jsPDF génère un vrai PDF valide
  (signature `data:application/pdf` confirmée) ; jsQR décode
  correctement un QR généré par la bibliothèque locale de génération,
  contenu exact retrouvé caractère pour caractère. Confirmé par
  surveillance réseau qu'aucune requête ne part plus vers
  `cdnjs.cloudflare.com` ni vers `jsdelivr.net` pour jsqr, y compris
  lors de l'ouverture réelle du scanner.
- **Version testée** : v141

## 12. Import par photo (OCR)

### 12.1 — CSP bloquait le Worker Tesseract *(cause racine trouvée et corrigée, v143)*
- **Contexte** : l'import par photo échouait systématiquement (4 échecs
  rapportés) avec un message "undefined" peu informatif.
- **Cause confirmée** par plusieurs sources indépendantes (AWS IVS,
  Mapbox, Apryse, exemple CSP spécifique à Tesseract.js) : la CSP
  n'autorisait pas les Web Workers créés via `blob:` (utilisés par
  Tesseract.js), ni la compilation WebAssembly.
- **Corrigé** : ajout de `worker-src 'self' blob: https://cdn.jsdelivr.net;`
  et de `'wasm-unsafe-eval'` à `script-src`.
- **Version testée** : v143 — **redemande une vérification physique**
  pour confirmer que l'OCR démarre enfin réellement (impossible à
  tester avec certitude en simulation, Tesseract nécessitant un vrai
  appareil pour la reconnaissance).

### 12.2 — Message "undefined" en cas d'échec *(cause racine trouvée et corrigée, v143)*
- **Cause confirmée** : un rejet de promesse sans valeur (`undefined`)
  faisait passer par `String(undefined)`, produisant littéralement le
  texte "undefined" à l'écran. Ce même motif fragile existait à 7
  endroits différents dans le code, pas seulement pour l'OCR.
- **Corrigé** : nouvelle fonction `formatCaughtError()` réutilisée
  partout, gérant explicitement les cas `undefined`/`null`, les objets
  sans `.name`/`.message`, les `Event` DOM, et les valeurs simples.
- **Résultat obtenu** : ✅ Réussi — testé avec 8 formes d'erreur
  différentes (dont `undefined` et `null`), aucune ne produit plus la
  chaîne "undefined".
- **Version testée** : v143

### 12.3 — Analyse : en-tête "Ingrédients pour X personnes" *(cause racine trouvée et corrigée, v143)*
- **Contexte** : des photos HelloFresh contenant "Ingrédients pour 2
  personnes" n'étaient pas reconnues comme le début de la section
  ingrédients (seul le mot seul "Ingrédients" était reconnu).
- **Corrigé** : la détection accepte désormais un texte de personnes
  après le mot-clé, dans les 4 langues.
- **Résultat obtenu** : ✅ Réussi — testé avec le texte exact "Ingrédients
  pour 2 personnes" suivi de 3 ingrédients : les 3 correctement
  détectés, et le nombre de personnes (2) correctement extrait pour
  normaliser les quantités par personne.
- **Version testée** : v143

### 12.4 — Analyse : ordre inversé "Nom Quantité Unité" *(cause racine trouvée et corrigée, v143)*
- **Contexte** : le format HelloFresh place la quantité et l'unité
  après le nom ("Grenailles 500 g"), jamais géré jusqu'ici — toute la
  ligne devenait le nom, avec quantité nulle.
- **Corrigé** : repli sur l'ordre inversé quand aucun chiffre n'est
  trouvé en tête de ligne, en réutilisant toute la logique de
  reconnaissance d'unité déjà existante.
- **Résultat obtenu** : ✅ Réussi — testé avec "Grenailles 500 g",
  "Haricots verts 1 sachet", "Thon au naturel 1 boîte" : tous
  correctement reconnus (nom, quantité et unité exacts). Non-régression
  confirmée sur l'ordre normal ("500 g Farine") et sur un ingrédient
  sans quantité ("Sel").
- **Version testée** : v143

### 12.5 — Import HelloFresh réel, cas complet *(cause racine trouvée et corrigée, v144)*
- **Contexte** : après un vrai test physique, l'OCR démarrait
  correctement (v143), mais le classement échouait — Tesseract avait lu
  "ingrédients pour £ personnes" (confusion "2"/"£"), non reconnu par la
  détection stricte alors en place.
- **Corrigé, plusieurs points ensemble** :
  1. Détection du titre assouplie (accepte tout préfixe "Ingrédients",
     peu importe ce qui suit — insensible aux erreurs OCR sur le nombre
     de personnes)
  2. "Valeurs nutritionnelles"/"Allergènes" ajoutés comme fins de liste
     d'ingrédients (4 langues)
  3. Fractions unicode (½, ⅔, ¼, ¾...) converties en décimal
  4. Suffixe "(s)" ignoré ("sachet(s)" → "sachet")
  5. Abréviations HelloFresh "cs"/"cc" reconnues (cuillère à soupe/café)
  6. **Bug additionnel trouvé en testant** : "cs" perdait son "s" à
     cause de la règle générique de singulier/pluriel, devenant "c"
     (jamais reconnu) — corrigé en vérifiant "cs"/"cc" sur le mot brut,
     avant cette normalisation
  7. **Second bug trouvé** : "pièce" n'était pas reconnu comme unité à
     part entière (seulement comme repli par défaut), faisant échouer
     le réassemblage de l'ordre inversé pour les fractions — corrigé
- **Résultat obtenu** : ✅ Réussi — testé avec le texte exact rapporté
  (6 ingrédients dont fractions et abréviations, plus "Valeurs
  nutritionnelles" après) : les 6 ingrédients correctement reconnus
  (nom, quantité, unité exacts), "Valeurs nutritionnelles" correctement
  exclue de la liste. Non-régression confirmée sur les tests 12.3/12.4
  précédents.
- **Version testée** : v144
- **Limite structurelle non résolue** (signalée par les deux audits) :
  une photo complète d'une fiche HelloFresh multi-colonnes peut faire
  lire par Tesseract plusieurs colonnes fusionnées sur une même ligne
  (ingrédient + étape mélangés) — aucune expression régulière ne peut
  fiablement séparer ça après coup. Voir la discussion sur l'import à
  plusieurs photos.

## 13. Import par plusieurs photos

### 13.1 — Deux boutons distincts (caméra / galerie) *(simulé)*
- **Résultat attendu** : deux boutons explicites, pas de dépendance au
  comportement variable du navigateur avec `capture="environment"`
  seul (peu fiable sur iPhone notamment).
- **Résultat obtenu** : ✅ Réussi — les deux boutons "Prendre une photo"
  et "Choisir depuis la galerie" confirmés présents, chacun relié à son
  propre champ de fichier.
- **Version testée** : v145

### 13.2 — Détection automatique de la section par photo *(simulé)*
- **Manipulation** : 4 photos avec un texte OCR simulé différent —
  ingrédients seuls, étapes seules, les deux à la fois, et un texte
  sans rapport (ambigu).
- **Résultat attendu** : détection correcte pour les 3 premiers cas ;
  repli sur "Autre" avec sélection manuelle requise pour le 4e.
- **Résultat obtenu** : ✅ Réussi — les 4 cas exactement comme attendu
  (`ingredients`/`preparation`/`mixed` détectés automatiquement, `other`
  sans détection automatique pour le cas ambigu).
- **Version testée** : v145

### 13.3 — Fusion de plusieurs photos en une seule recette *(simulé)*
- **Manipulation** : une photo "ingrédients" (nom + 2 ingrédients) et
  une photo "étapes" (2 étapes), fusionnées.
- **Résultat attendu** : nom repris de la première photo, ingrédients
  et étapes combinés, formulaire ouvert prérempli, état de l'import
  vidé après la fusion.
- **Résultat obtenu** : ✅ Réussi — nom exact, les 2 étapes des deux
  photos bien présentes dans la description, 2 ingrédients dans le
  formulaire, aucune photo restante en mémoire après la fusion.
- **Version testée** : v145

### 13.4 — Suppression d'une photo et limite maximale *(simulé)*
- **Résultat attendu** : le bouton "×" retire bien la photo choisie ;
  au-delà de 8 photos, les tentatives suivantes sont ignorées.
- **Résultat obtenu** : ✅ Réussi — suppression confirmée (1 → 0), et
  limite de 8 respectée même en tentant d'en ajouter 9.
- **Version testée** : v145
- **Reste à tester physiquement** : le cycle complet avec de vraies
  photos et le vrai OCR Tesseract (impossible à simuler entièrement
  dans l'environnement de test).

### 13.5 — Choix manuel réellement fonctionnel *(cause racine trouvée et corrigée, v146)*
- **Contexte** : après un vrai test avec des photos HelloFresh, l'autre
  IA a confirmé que le sélecteur manuel ne faisait que changer
  l'étiquette affichée — il ne réanalysait jamais le texte brut. Une
  photo mal classée automatiquement restait donc mal analysée même
  après correction manuelle.
- **Corrigé** : le texte OCR brut est désormais conservé pour chaque
  photo, et 4 analyseurs dédiés par section réinterprètent vraiment ce
  texte selon le choix (fait automatiquement ou manuellement) —
  "Ingrédients" traite chaque ligne comme un ingrédient potentiel sans
  exiger de mot-clé, "Préparation" garde tout comme étapes, "Recette
  complète" utilise l'analyse habituelle, "Infos générales" ne cherche
  que nom/personnes/temps.
- **Résultat obtenu** : ✅ Réussi — testé avec un vrai clic utilisateur
  sur le menu déroulant (`select_option`, pas un appel direct à une
  fonction) : un texte mal classé automatiquement en "Préparation" (0
  ingrédient trouvé) donne bien les 3 ingrédients corrects une fois
  reclassé manuellement en "Ingrédients".
- **Version testée** : v146

### 13.6 — Fusion : nom et personnes ne dépendent plus de l'ordre *(cause racine trouvée et corrigée, v146)*
- **Contexte** : deux bugs trouvés lors du test réel : (1) le nom
  pouvait venir de n'importe quelle photo, y compris une photo
  "Ingrédients" dont la première ligne n'a aucune raison d'être un nom
  de recette ; (2) chaque photo sans portion détectée recevait
  automatiquement 4, et la fusion gardait la valeur de la première
  photo traitée — une photo d'étapes traitée avant une photo
  d'ingrédients avec la vraie portion (2) pouvait donc imposer 4 à
  tort, doublant certaines quantités à l'affichage.
- **Corrigé** : `parseOcrRecipeText()` renvoie maintenant `null` quand
  aucune portion n'est réellement détectée (au lieu de supposer 4
  immédiatement) ; le repli à 4 ne s'applique qu'une fois toutes les
  photos fusionnées. Le nom ne peut plus provenir des sections
  "Ingrédients"/"Préparation" (les analyseurs dédiés ne le renseignent
  jamais pour ces sections).
- **Résultat obtenu** : ✅ Réussi — testé avec le vrai pipeline complet
  (`deriveSectionDataForPhoto` puis `mergeMultiPhotoResults`, pas des
  données fabriquées à la main) : le nom vient bien de la photo "Infos
  générales", jamais de la photo "Ingrédients" même quand sa première
  ligne ressemble à un titre. Personnes confirmées identiques (2) peu
  importe l'ordre des deux photos testées.
- **Version testée** : v146

### 13.7 — Un seul Worker Tesseract réutilisé *(cause racine trouvée et corrigée, v146)*
- **Contexte** : un nouveau Worker Tesseract était créé et détruit à
  chaque photo — avec huit images, cela représente huit initialisations
  complètes du moteur, lent et gourmand en mémoire sur les appareils
  d'entrée de gamme (signalé pour le Samsung A06).
- **Corrigé** : un seul Worker partagé pour toute la série de photos,
  recréé seulement si la langue change, terminé une fois la fusion
  effectuée.
- **Résultat obtenu** : ✅ Réussi — testé avec 2 photos : une seule
  création de Worker confirmée (au lieu de 2).
- **Version testée** : v146

### 13.8 — Unité "paquet" non reconnue *(cause racine trouvée et corrigée, v146)*
- **Contexte** : "1paquet Chips" ne reconnaissait pas "paquet" comme
  unité, le mot entier finissant dans le nom de l'ingrédient.
- **Corrigé** : "paquet"/"paquets" reconnus, fusionnés avec l'unité
  "sachet" déjà existante dans le formulaire.
- **Résultat obtenu** : ✅ Réussi — testé au singulier et au pluriel.
- **Version testée** : v146
- **Limite structurelle non résolue** : une photo complète
  multi-colonnes (HelloFresh notamment) peut toujours faire lire par
  Tesseract plusieurs colonnes fusionnées sur une même ligne — aucune
  de ces corrections ne peut séparer un ingrédient et une étape
  mélangés sur la même ligne reconnue. Une photo bien rapprochée d'une
  seule section reste nécessaire pour un résultat fiable.

### 13.9 — Doublement des quantités après reclassement manuel *(cause racine trouvée et corrigée, v147)*
- **Contexte** : après un vrai test avec des photos HelloFresh, l'autre
  IA a trouvé que les quantités d'une photo "Recette complète" étaient
  divisées par le nombre de personnes détecté, mais celles d'une photo
  reclassée manuellement en "Ingrédients" ne l'étaient jamais — la
  fusion pouvait donc appliquer un nombre de personnes détecté sur une
  AUTRE photo à des quantités jamais divisées, doublant l'affichage
  final (500 g → 1000 g pour 2 personnes).
- **Corrigé** : `parseOcrRecipeText()` ne divise plus du tout en
  interne ; la division par le nombre de personnes final se fait une
  seule fois, après la fusion complète de toutes les photos
  (`mergeMultiPhotoResults`), avec le diviseur toujours identique à la
  valeur enregistrée comme nombre de personnes. Le repli Jina (import
  par lien) applique désormais cette division lui-même, puisqu'il n'a
  pas d'étape de fusion.
- **Résultat obtenu** : ✅ Réussi — testé avec le scénario exact
  rapporté (Grenailles 500 g, 2 personnes détectées sur une photo
  séparée) dans les deux ordres de photos : 250 g/personne stocké dans
  les deux cas, 500 g correctement réaffiché pour 2 personnes, jamais
  1000 g.
- **Version testée** : v147

### 13.10 — Traitements simultanés et nettoyage du Worker *(cause racine trouvée et corrigée, v147)*
- **Contexte** : le bouton "Fusionner" restait actif même si une autre
  photo était encore en cours d'analyse, risquant de terminer le
  Worker Tesseract pendant qu'il était utilisé.
- **Corrigé** : "Fusionner" et les boutons d'ajout de photo sont
  désormais désactivés tant qu'une photo est en cours ; la terminaison
  du Worker est protégée par try/catch ; le Worker est aussi nettoyé
  automatiquement si l'utilisateur quitte l'écran sans fusionner.
- **Résultat obtenu** : ✅ Réussi — testé avec une reconnaissance
  volontairement bloquée : les deux boutons confirmés désactivés
  pendant le traitement, réactivés une fois terminé ; un seul appel à
  `terminate()` confirmé après avoir quitté l'écran sans fusionner.
- **Version testée** : v147

### 13.11 — Unités espagnoles/allemandes et filtre "personnes" multilingue *(cause racine trouvée et corrigée, v147)*
- **Contexte** : l'analyseur manuel d'ingrédients ne reconnaissait que
  les unités françaises/anglaises ; le filtre retirant les lignes de
  comptage de personnes ne cherchait que le mot français "personnes".
- **Corrigé** : ajout de "pieza", "paquete", "lata", "cucharada"
  (espagnol) et "Stück", "Packung", "Dose", "EL", "TL" (allemand) ;
  filtre élargi à "people"/"persons"/"personas"/"personen", avec ou
  sans nombre devant (ex. "4 people").
- **Résultat obtenu** : ✅ Réussi — les 9 unités testées individuellement
  toutes correctes ; "4 people" confirmé exclu des ingrédients (seul
  "Flour" reste).
- **Version testée** : v147
- **Limite connue** : les unités catalanes, portugaises ou italiennes
  ne sont pas couvertes ; à ajouter si des photos dans ces langues
  posent problème.

### 13.12 — Titres complets non retirés en section manuelle *(cause racine trouvée et corrigée, v148)*
- **Contexte** : après un vrai test avec des photos HelloFresh, l'autre
  IA a trouvé que le filtre ne retirait que les compteurs isolés
  ("4 people", "pour 2 personnes"), pas les vrais titres complets des
  fiches ("Ingrédients pour 2 personnes", "Ingredientes para 4
  personas", "Zutaten für 4 Personen") — ces titres devenaient donc de
  faux ingrédients après un reclassement manuel en "Ingrédients". Même
  problème, moins grave, pour "Étapes" restant dans la description.
- **Corrigé** : les marqueurs de titre déjà utilisés par
  `parseOcrRecipeText()` sont désormais remontés au niveau du module et
  réutilisés dans `deriveSectionDataForPhoto()` — les titres complets
  sont retirés avant de traiter chaque ligne comme un ingrédient
  potentiel, et le nombre de personnes est extrait du titre avant sa
  suppression (pas perdu).
- **Résultat obtenu** : ✅ Réussi — testé avec les 3 titres exacts
  rapportés (français, espagnol, allemand) : plus aucun faux
  ingrédient, personnes correctement extraites (2, 4, 4) dans les 3
  cas. Testé aussi que "Étapes" ne reste plus dans la description.
- **Version testée** : v148

### 13.13 — Nombre de personnes supposé silencieusement *(cause racine trouvée et corrigée, v148)*
- **Contexte** : si aucune photo ne contenait de nombre de personnes
  détectable, la fusion supposait 4 immédiatement et divisait toutes
  les quantités avec cette valeur — si l'utilisateur corrigeait
  ensuite le nombre de personnes dans le formulaire final, les
  quantités restaient basées sur la mauvaise division.
- **Corrigé** : un champ "Nombre de personnes" visible et modifiable a
  été ajouté à l'écran d'import — préremplit avec la valeur détectée
  si disponible (avec confirmation "✓ détecté"), sinon 4 avec un
  avertissement explicite ("non détecté — valeur supposée, à
  vérifier"). La fusion utilise toujours cette valeur confirmée par
  l'utilisateur pour diviser les quantités, jamais une supposition
  silencieuse.
- **Résultat obtenu** : ✅ Réussi — testé le cycle complet : valeur par
  défaut 4 avec avertissement affiché avant toute photo ; correction
  manuelle à 2 par l'utilisateur ; fusion confirmée utilisant bien 2
  (250 g stocké pour 500 g déclaré), pas 4 (ce qui aurait donné 125 g
  à tort).
- **Version testée** : v148

## 14. Tests physiques d'ensemble (session du 05/09/2026)

### 14.1 — OCR réel avec plusieurs photos HelloFresh *(physique)*
- **Résultat obtenu** : ⚠️ Peu fiable, souvent des erreurs — **mis en
  attente**, chantier séparé (voir section 12-13, corrections en
  cours mais résultat réel encore instable sur les vraies fiches
  HelloFresh).

### 14.2 — TalkBack sur les formulaires et fenêtres *(physique)*
- **Résultat obtenu** : ✅ Réussi — fonctionne correctement.

### 14.3 — Affichage allemand sur un écran étroit *(physique)*
- **Résultat obtenu** : ✅ Réussi — fonctionne correctement.

### 14.4 — Installation et mise à jour PWA sur les deux appareils *(physique)*
- **Résultat obtenu** : ✅ Réussi — fonctionne correctement.

### 14.5 — Fonctionnement hors connexion après installation neuve *(physique)*
- **Résultat obtenu** : ✅ Réussi — fonctionne correctement.

### 14.6 — Import QR par caméra et galerie sur les deux appareils *(physique)*
- **Résultat obtenu** : ⚠️ Peu fiable, souvent des erreurs — **mis en
  attente**, à investiguer séparément (cause non encore identifiée,
  contrairement au scanner de recette/liste qui avait été testé
  fonctionnel plus tôt — écart à clarifier).

### 14.7 — Notification et vibration Android *(physique — terminé)*
- **Résultat obtenu** : ✅ Fiable au premier plan (sonnerie, vibration,
  répétition, arrêt) ; ⚠️ non fiable en arrière-plan (vibration
  différée) ; ❌ non fiable écran verrouillé (rien à l'heure prévue,
  déclenché seulement au réveil de l'écran) ; ❌ aucune notification
  système dans aucun cas. Voir le détail complet en section 19.1.

### 14.8 — Manifestes/raccourcis après changement de langue et redémarrage *(physique)*
- **Résultat obtenu** : ✅ Réussi, avec une nuance mineure et attendue :
  - Langue interne conservée après redémarrage : réussi.
  - Les 4 manifestes contiennent les bonnes traductions : réussi.
  - Les raccourcis ouvrent les bons écrans : réussi.
  - Après réinstallation, les raccourcis correspondent à la langue
    choisie : réussi.
  - ⚠️ Les raccourcis d'une PWA **déjà installée** ne changent pas
    immédiatement de langue sans réinstallation — comportement normal
    de Chrome/Android (les raccourcis sont figés à l'installation),
    pas un bug de l'application. Non bloquant, pas de correctif prévu :
    il ne serait pas raisonnable de demander une réinstallation
    seulement pour deux raccourcis.
- **Appareil** : Samsung Galaxy A06, Android 16 — One UI 8.0, Chrome
  152.0.7977.75

---

## 15. Accessibilité, langues et ergonomie (session du 05/09/2026)

### 15.1 — `maximum-scale=1` retiré *(cause racine trouvée et corrigée, v151)*
- **Contexte** : empêchait l'utilisateur de zoomer, un vrai problème
  d'accessibilité.
- **Corrigé** : retiré de la balise viewport.
- **Version testée** : v151

### 15.2 — Contrastes de couleurs insuffisants *(cause racine trouvée et corrigée, v151)*
- **Contexte** : `--accent` sur `--accent-light` à 2,51:1 et `--danger`
  sur `--danger-light` à 4,05:1, tous deux sous le seuil WCAG AA (4,5:1
  pour du texte normal) — confirmé par calcul précis contre les vrais
  fonds utilisés.
- **Corrigé** : `--accent` assombri (#C08A2E → #886120, 4,59:1) et
  `--danger` assombri (#B54B3A → #A84535, 4,58:1) en mode clair. Mode
  sombre déjà correct (6,5:1 et 5,37:1), non modifié.
- **Version testée** : v151

### 15.3 — Étoiles illisibles dans l'export PDF *(cause racine trouvée et corrigée, v151)*
- **Contexte** : les caractères ★/☆ ne sont pas correctement pris en
  charge par la police PDF actuelle.
- **Corrigé** : remplacés par un texte simple "X / 5".
- **Version testée** : v151

### 15.4 — Anciennes fenêtres `prompt()` remplacées *(cause racine trouvée et corrigée, v151)*
- **Contexte** : deux `prompt()` natifs subsistaient (nommer une liste
  de courses enregistrée, nommer un modèle de planning), incohérents
  avec le reste de l'application.
- **Corrigé** : nouvelle fonction `customPrompt()` suivant le même
  modèle que `customConfirm()`/`customAlert()`, utilisée aux deux
  endroits.
- **Résultat obtenu** : ✅ Réussi — testé avec une valeur par défaut et
  une saisie utilisateur, les deux correctement retournées.
- **Version testée** : v151

### 15.5 — "Coller le texte d'un QR code" déplacé *(amélioration ergonomique, v151)*
- **Contexte** : fonction technique rarement utilisée, en place directe
  sur l'accueil.
- **Corrigé** : retiré de l'accueil, déplacé en option secondaire
  discrète ("Le scan ne fonctionne pas ? Coller le contenu du QR code")
  à l'intérieur de la fenêtre de scan — reste disponible comme solution
  de secours, sans occuper une place directe sur l'accueil.
- **Résultat obtenu** : ✅ Réussi — testé : accueil ne contient plus le
  bouton, fenêtre de scan contient bien le lien, le clic ouvre
  correctement la fenêtre de collage.
- **Version testée** : v151

### 15.6 — Limite de sauvegarde réduite *(v151)*
- **Corrigé** : 200 Mo → 50 Mo, plus prudent pour un appareil d'entrée
  de gamme.
- **Version testée** : v151

### 15.7 — Connexion automatique à Google Fonts documentée *(v151)*
- **Contexte** : la politique de confidentialité laissait entendre que
  toutes les connexions étaient déclenchées explicitement, alors que le
  chargement des polices est automatique dès le premier chargement.
- **Corrigé** : section dédiée ajoutée, résumé ajusté pour ne plus
  sur-affirmer.
- **Version testée** : v151

### 15.8 — Dates selon la langue de l'application, pas du téléphone *(cause racine trouvée et corrigée, v151)*
- **Contexte** : toutes les dates utilisaient `toLocaleDateString()`/
  `toLocaleString()` sans locale explicite, suivant donc la langue du
  téléphone plutôt que celle choisie dans l'application.
- **Corrigé** : nouvelles fonctions `localeDateStr()`/
  `localeDateTimeStr()` utilisant `CURRENT_LANG` explicitement,
  appliquées aux 7 usages trouvés (PDF, journal de cuisine, corbeille,
  diagnostic, statistiques mensuelles).
- **Résultat obtenu** : ✅ Réussi — testé avec navigateur en français
  et application réglée en allemand : date correctement au format
  allemand (5.3.2026), différente du format français par défaut du
  navigateur (05/03/2026).
- **Version testée** : v151

### 15.9 — Tri des ingrédients par traduction affichée *(cause racine trouvée et corrigée, v151)*
- **Contexte** : le tri utilisait le nom français interne
  (`localeCompare(b, "fr")`), pas la traduction visible à l'écran —
  l'ordre alphabétique pouvait donc paraître incohérent dans les
  autres langues.
- **Corrigé** : nouveau comparateur `compareIngredientNamesForDisplay()`
  triant par traduction affichée, appliqué aux 5 tris trouvés (y
  compris un second écran, la gestion des substituts, touché par le
  même défaut).
- **Résultat obtenu** : ✅ Réussi — testé avec deux traductions
  inversant l'ordre alphabétique français : le tri suit bien l'ordre
  de la traduction affichée.
- **Version testée** : v151

### 15.10 — Collisions de traduction désambiguïsées *(cause racine trouvée et corrigée, v151)*
- **Contexte** : 23 à 27 traductions (selon la langue) correspondent à
  plusieurs noms français différents, souvent de vrais synonymes (ex.
  "Arachide"/"Cacahuète" → "Peanut" en anglais), produisant deux
  suggestions visuellement identiques.
- **Corrigé** : les traductions en collision affichent désormais le nom
  français d'origine entre parenthèses, uniquement à l'affichage (les
  données sous-jacentes ne sont pas modifiées, pour éviter tout risque
  sur les allergènes/nutrition/substitutions déjà liés aux noms
  français existants).
- **Résultat obtenu** : ✅ Réussi — testé : "Arachide" → "Peanut
  (Arachide)", "Cacahuète" → "Peanut (Cacahuète)", désormais
  distinguables ; un ingrédient sans collision ("Sel") reste inchangé.
- **Version testée** : v151

### 15.11 — Noms de fichiers PDF traduits *(v151)*
- **Corrigé** : "liste-de-courses"/"mon-livre-de-recettes" traduits
  dans les 4 langues.
- **Version testée** : v151

### 15.12 — Réservations du garde-manger persistées *(cause racine trouvée et corrigée, v151)*
- **Contexte** : les réservations de la session (évite de compter deux
  fois le même stock entre plusieurs ajouts à la liste de courses)
  étaient perdues à chaque redémarrage de l'application.
- **Corrigé** : persistées dans localStorage, chargées au démarrage.
  Le recalcul automatique des réservations après modification/
  suppression d'un article reste différé, comme convenu (refonte plus
  large, pas prioritaire).
- **Résultat obtenu** : ✅ Réussi — testé avec un vrai rechargement
  complet de la page : la réservation survit exactement.
- **Version testée** : v151

### 15.13 — Noms accessibles manquants *(cause racine trouvée et corrigée, v151)*
- **Contexte** : plusieurs champs (4 barres de recherche, la ligne
  d'ingrédient du formulaire — nom/quantité/unité —, les champs de
  substitution) n'avaient qu'un placeholder, insuffisant pour un
  lecteur d'écran (TalkBack peut alors annoncer seulement "champ de
  saisie").
- **Corrigé** : `aria-label` ajouté à tous ces champs. Vérifié que les
  6 autres champs à placeholder de l'application ont déjà un vrai
  `<label>` associé (recette, avis famille, notes d'amélioration,
  modale d'ingrédient, nom de menu, import par lien) — rien à corriger
  pour ceux-là.
- **Résultat obtenu** : ✅ Réussi — testé sur la ligne d'ingrédient du
  formulaire (les 3 champs) et la recherche de recettes.
- **Version testée** : v151

### 15.14 — Texte alternatif des miniatures OCR *(cause racine trouvée et corrigée, v151)*
- **Contexte** : les miniatures de l'import multi-photos n'avaient
  aucun attribut `alt`.
- **Corrigé** : texte alternatif ajouté. Vérifié qu'aucune autre image
  de l'application n'en manque.
- **Version testée** : v151

---

## 16. Corrections suite à l'audit de la v151 (session du 05/09/2026)

### 16.1 — Régression scanner/collage QR *(régression trouvée et corrigée, v152)*
- **Contexte** : le déplacement du bouton "Coller le texte d'un QR
  code" vers l'écran de scan (v151, point 15.5) avait introduit une
  régression : le lien de secours ouvrait la fenêtre de collage sans
  arrêter la caméra ni fermer la fenêtre de scan — caméra active
  derrière, deux fenêtres modales empilées.
- **Corrigé** : `cleanup()` et `overlay.remove()` appelés avant
  d'ouvrir la fenêtre de collage.
- **Résultat obtenu** : ✅ Réussi — testé avec un flux caméra simulé :
  caméra bien arrêtée, une seule fenêtre modale présente après le clic
  (celle du collage), plus de superposition.
- **Version testée** : v152

### 16.2 — Réservations du garde-manger recalculées *(cause racine trouvée et corrigée, v152)*
- **Contexte** : les réservations, désormais persistantes (v151),
  n'étaient toujours pas remises à zéro après suppression/modification
  d'un article de courses ou de garde-manger, ni après restauration
  d'une sauvegarde différente — une ancienne réservation incorrecte
  pouvait donc survivre indéfiniment.
- **Corrigé** (solution minimale, comme recommandé — la refonte
  complète avec rattachement précis reste différée) : remise à zéro
  après modification d'un article de courses/garde-manger, suppression
  d'un article de courses/garde-manger, et après toute restauration de
  sauvegarde.
- **Résultat obtenu** : ✅ Réussi — testé sur la suppression d'article
  et la restauration de sauvegarde, les deux confirmées à `{}`.
- **Version testée** : v152

### 16.3 — Résolution de "Peanut (Arachide)" *(cause racine trouvée et corrigée, v152)*
- **Contexte** : la désambiguïsation des collisions de traduction
  (v151, point 15.10) affiche "Peanut (Arachide)", mais
  `resolveIngredientInput()` ne reconnaissait pas cette forme complète
  — la resaisir aurait créé un nouvel ingrédient personnalisé au lieu
  de retrouver l'original.
- **Corrigé** : la partie entre parenthèses est désormais extraite et
  reconnue si elle correspond à un ingrédient existant.
- **Résultat obtenu** : ✅ Réussi — testé : "Peanut (Arachide)" résolu
  vers "Arachide" ; un texte avec parenthèses ne correspondant à rien
  reste inchangé (pas de faux positif).
- **Version testée** : v152

### 16.4 — Tri des ingrédients retrié après changement de langue *(cause racine trouvée et corrigée, v152)*
- **Contexte** : le tri par traduction (v151, point 15.9) ne
  s'appliquait qu'au chargement initial — changer de langue en cours
  d'utilisation ne retriait pas immédiatement la liste, seulement au
  prochain redémarrage.
- **Corrigé** : `setLang()` retrie désormais immédiatement.
- **Résultat obtenu** : ✅ Réussi — testé avec des traductions
  inversant l'ordre alphabétique français : le tri suit bien le nouvel
  ordre immédiatement après l'appel, sans redémarrage nécessaire.
- **Version testée** : v152

### 16.5 — Petits points *(v152)*
- **`customPrompt()`** : `aria-labelledby` ajouté au champ de saisie
  (pointant vers le message de la fenêtre) — TalkBack n'annonçait
  auparavant que le titre général, pas ce qui est précisément demandé.
- **Validation des sauvegardes** : `ingredients`/`cookLog` remis à `[]`
  s'ils existent mais ne sont pas des tableaux du tout (chaîne, nombre,
  objet) — auparavant conservés tels quels. Testé et confirmé.
- **Résumé du document de tests** : corrigé pour ne plus prétendre à
  tort qu'aucun test ne reste en attente — les 3 points authentiquement
  non résolus (OCR, scan QR caméra/galerie, notification/vibration)
  sont désormais explicitement cités dans le résumé final.

## 17. Réservations du garde-manger, ciblage précis (session du 05/09/2026)

### 17.1 — Remise à zéro globale trop large *(régression confirmée et corrigée, v153)*
- **Contexte** : la remise à zéro globale ajoutée en v152 (point 16.2)
  réglait le problème des réservations obsolètes, mais en introduisait
  un nouveau : modifier ou supprimer N'IMPORTE QUEL article effaçait
  TOUTES les réservations, y compris celles d'ingrédients sans aucun
  rapport. Scénario concret confirmé : farine réservée par une recette
  A (800 g sur 1000 g disponibles), puis modification d'un article
  totalement différent efface la réservation de farine — une recette B
  ayant aussi besoin de farine croit alors disposer des 1000 g complets
  alors que 800 g sont déjà utilisés, ne proposant plus d'en acheter
  alors qu'il en manque réellement 600 g.
- **Corrigé** : remise à zéro ciblée sur l'ingrédient concerné
  uniquement (ancien et nouveau nom si renommé), pas sur l'ensemble des
  réservations — pour les 3 cas d'un seul article (suppression et
  modification d'un article de courses, suppression d'un article de
  garde-manger). Les 3 cas d'opération groupée (vider toute la liste,
  charger une autre liste enregistrée, restaurer une sauvegarde)
  gardent à raison la remise à zéro complète, puisque tout change
  réellement dans ces cas-là.
- **Résultat obtenu** : ✅ Réussi — testé avec le scénario exact de
  l'audit : la réservation de farine (800g) survit bien à la
  suppression d'un article sans rapport ("Sel") ; et, cas
  complémentaire, supprimer la farine elle-même efface bien
  correctement sa propre réservation.
- **Limite reconnue en v153, résolue en v154** : restait approximatif
  si le MÊME ingrédient était concerné par plusieurs recettes/articles
  à la fois — voir section 18 pour la refonte complète qui corrige
  précisément ce cas.
- **Version testée** : v153

### 17.2 — `null` non normalisé dans la validation des sauvegardes *(cause racine trouvée et corrigée, v153)*
- **Contexte** : `ingredients: null` et `cookLog: null` n'étaient pas
  transformés en tableau vide, contrairement aux chaînes, nombres et
  objets (la condition excluait explicitement les valeurs `null`).
- **Corrigé** : condition simplifiée pour couvrir aussi `null`/
  `undefined`.
- **Résultat obtenu** : ✅ Réussi — testé avec les deux champs
  explicitement à `null` : tous deux correctement normalisés en `[]`.
- **Version testée** : v153

### 17.3 — Nature réelle de cette suite de tests *(précision honnête, sans changement de code)*
- **Point soulevé** : ce document ne constitue pas une suite
  automatisée exécutable (pas de CI, pas de protection automatique des
  futures versions) — les tests dits "simulés" sont des vérifications
  ponctuelles effectuées manuellement à chaque session de
  développement, puis documentées ici. Les tests "physiques" sont
  réalisés par l'utilisateur sur ses propres appareils.
- **Décision** : ce document reste donc une **trace de vérifications
  ponctuelles**, utile pour suivre l'historique des défauts trouvés et
  corrigés, mais ne remplace pas une vraie suite automatisée qui
  s'exécuterait seule avant chaque publication. Construire une telle
  suite serait un chantier à part entière, non entrepris ici faute
  d'avoir été demandé en priorité.

## 18. Refonte complète du registre de réservations (session du 05/09/2026)

### 18.1 — Registre précis par source *(refonte complète, v154)*
- **Contexte** : la v153 corrigeait le cas "ingrédient sans rapport",
  mais restait imprécise pour le MÊME ingrédient réservé par plusieurs
  sources — scénario confirmé par l'audit : deux recettes réservant
  séparément 400 g de farine chacune (800 g au total), puis la
  suppression d'un seul article "Farine" effaçait les 800 g au lieu de
  seulement la part concernée.
- **Corrigé, refonte complète** : `state.pantryClaimedThisSession`
  devient un tableau d'entrées individuelles `{id, ingredientKey,
  amount, sourceType, sourceId}`, chacune attachée précisément à ce qui
  l'a créée :
  - un article de courses (`sourceType: "shopping"`, son propre
    identifiant) pour un ingrédient partiellement couvert ;
  - un identifiant d'opération d'ajout de recette
    (`sourceType: "recipe"`) pour un ingrédient **entièrement** couvert
    par le garde-manger, qui n'a donc aucun article de courses
    correspondant.
  - `releasePantryClaimsForSource()` libère uniquement les entrées
    d'une source précise ; `releasePantryClaimsForIngredient()` libère
    toutes les entrées d'un ingrédient donné (utilisé uniquement pour
    la suppression/modification d'un article de **garde-manger**, où
    le stock physique lui-même change ou disparaît, invalidant toute
    réservation contre lui quelle que soit sa source).
- **Résultat obtenu** : ✅ Réussi — testé avec le scénario exact de
  l'audit : deux "recettes" réservant chacune 400 g de farine (stock
  limité à 600 g, l'une entièrement couverte, l'autre partiellement)
  donnent deux entrées distinctes ; supprimer l'article de courses
  résultant de la seconde libère précisément ses 200 g, la réservation
  de 400 g de la première **survit intacte**. Testé aussi : ajout
  unitaire via la fenêtre modale, suppression d'un article de
  garde-manger (libère bien toutes les sources pour cet ingrédient,
  sans toucher aux autres ingrédients), et persistance dans
  localStorage avec le nouveau format (survit à un rechargement complet
  de la page).
- **Compatibilité** : l'ancien format (objet) éventuellement encore en
  localStorage chez un utilisateur est simplement ignoré au chargement
  plutôt que de planter dessus — ces anciennes réservations n'ont de
  toute façon plus d'origine identifiable pour les convertir fidèlement.
- **Version testée** : v154

## 19. Minuteur Android et mode cuisine (session du 05/09/2026)

### 19.1 — Test physique du minuteur *(physique — terminé)*
- **Application visible** : ✅ « Terminé ! » affiché, ✅ sonnerie, ✅
  vibration, ✅ répétition, ✅ le bouton arrête correctement l'alarme.
- **Application en arrière-plan** : ⚠️ sonnerie fonctionnelle ; ⚠️
  vibration différée jusqu'au retour dans l'application ; ❌ aucune
  notification système.
- **Écran verrouillé** : ❌ aucune sonnerie à l'heure prévue ; ❌ aucune
  vibration à l'heure prévue ; ⚠️ la sonnerie commence au réveil de
  l'écran, même avant la saisie du code PIN ; ⚠️ la vibration ne
  commence qu'au retour dans l'application ; ❌ aucune notification
  système.
- **Conclusion** : le minuteur est fiable lorsque l'application reste
  visible. Son fonctionnement n'est pas fiable en arrière-plan ou écran
  verrouillé.
- **Cause identifiée** : le minuteur repose sur `setInterval()`, que
  Android ralentit ou suspend quand l'application n'est plus visible,
  particulièrement écran verrouillé. Aucune notification système n'est
  implémentée dans le code actuel (absence de `Notification`/
  `showNotification()`).
- **Appareil** : Samsung Galaxy A06

### 19.2 — Bug critique trouvé en marge : mode cuisine plantait systématiquement *(cause racine trouvée et corrigée, v155)*
- **Contexte** : en vérifiant le code pour implémenter le Wake Lock,
  `openCookingMode()` s'est révélé planter à chaque appel
  (`ReferenceError: sheet is not defined` — une variable jamais
  déclarée, la fonction ne possède pas d'élément nommé "sheet").
- **Corrigé** : `initModalA11y(overlay, sheet)` → `initModalA11y(overlay,
  overlay)`.
- **Résultat obtenu** : ✅ Réussi — testé : plus aucune erreur JS à
  l'ouverture du mode cuisine, la fenêtre s'affiche correctement.
- **Version testée** : v155

### 19.3 — Maintien de l'écran allumé pendant la cuisine (Wake Lock) *(implémenté v155, validé physiquement v155)*
- **Contexte** : recommandation de priorité haute pour rendre le
  minuteur fiable dans le scénario normal de cuisine (écran resté
  allumé, visible en permanence) — ne résout pas le cas écran
  verrouillé, qui nécessiterait une vraie application native (prévu
  pour la conversion Play Store, en toute fin de projet).
- **Implémenté** : Wake Lock demandé à l'ouverture du mode cuisine,
  relâché à la fermeture, redemandé automatiquement si la visibilité de
  la page revient (le verrou est autrement relâché par le navigateur
  dès que l'onglet devient invisible). Indicateur visible affiché
  ("🔆 Écran maintenu allumé pendant la cuisine"), avec message clair si
  refusé ou non disponible (économie d'énergie, appareil non
  compatible).
- **Résultat obtenu (simulé)** : ✅ Réussi — cycle complet testé : une
  seule demande à l'ouverture, redemande confirmée après un changement
  de visibilité simulé, relâchement confirmé à la fermeture ; message
  de repli confirmé quand l'API n'est pas disponible.
- **Résultat obtenu (physique) — validation complète** : ✅ message
  affiché ; ✅ écran encore allumé après 2 minutes (mise en veille
  automatique réglée à 15 secondes) ; ✅ minuteur déclenché à l'heure
  prévue ; ✅ sonnerie ; ✅ vibration ; ✅ répétition ; ✅ arrêt par le
  bouton ; ✅ Wake Lock libéré après fermeture, écran s'éteignant
  ensuite normalement ; ✅ Wake Lock repris après un changement
  d'application ; ✅ fonctionnel même avec le mode économie d'énergie
  activé.
- **Limite confirmée, inchangée** : ne rend pas le minuteur fiable si
  l'utilisateur verrouille volontairement l'écran ou laisse
  l'application en arrière-plan — seul le cas "application visible,
  écran non verrouillé" est concerné par cette amélioration.
- **Appareil** : Samsung Galaxy A06, Android 16, Chrome 152.0.7977.75
- **Non traité pour l'instant** (comme convenu, priorité moyenne/basse) :
  notification système classique, et alarme fiable écran verrouillé
  (nécessiterait une vraie application native).
- **Version testée** : v155/v156

### 19.4 — Fermeture par Échap contournait le nettoyage *(cause racine trouvée et corrigée, v156)*
- **Contexte** : la fermeture par le bouton dédié nettoyait bien tout
  (minuteurs, lecture à voix haute, Wake Lock, écouteur de visibilité),
  mais une fermeture par la touche Échap (clavier externe) passait par
  un chemin différent qui contournait entièrement ce nettoyage —
  laissant potentiellement le Wake Lock jamais relâché.
- **Corrigé** : le nettoyage a été extrait dans une fonction nommée
  (`cleanupCookingMode`), réutilisée à la fois par le bouton ET passée
  comme `beforeClose` à `initModalA11y()` (déjà conçu pour ce cas, déjà
  utilisé pour la caméra du scanner QR).
- **Résultat obtenu** : ✅ Réussi — testé : Échap déclenche maintenant
  bien le relâchement du Wake Lock (confirmé une seule fois) et ferme
  la fenêtre ; non-régression confirmée sur la fermeture par bouton
  (toujours fonctionnelle, sans double relâchement).
- **Portée** : cas rare sur téléphone (nécessite un clavier externe),
  mais désormais couvert.
- **Version testée** : v156

### 19.5 — Deux cas limites du Wake Lock *(causes racines trouvées et corrigées, v157)*
- **Contexte** : après la validation physique complète (section 19.3),
  une relecture attentive de la séquence asynchrone a révélé deux
  défauts potentiels, non visibles lors des tests normaux mais réels :
  1. **Course fermeture/octroi** : la demande de Wake Lock est
     asynchrone (`await navigator.wakeLock.request(...)`) — si le mode
     cuisine est fermé avant qu'Android ne réponde, `releaseWakeLock()`
     ne trouve encore rien à relâcher ; si Android accorde ensuite le
     verrou (après la fermeture), il restait actif indéfiniment. Même
     risque lors d'une redemande après un retour de visibilité.
  2. **Nettoyage non idempotent** : `cleanupCookingMode()` peut être
     appelé une première fois par le bouton, puis une seconde fois par
     le `MutationObserver` de `initModalA11y()` (son propre drapeau
     interne "closed" ne voit pas un appel direct au nettoyage
     contournant `closeModal`) — pas dangereux en pratique dans ce cas
     précis, mais fragile.
- **Corrigé** : l'état `cookingModeOpen` est revérifié après chaque
  demande de Wake Lock (à l'ouverture et après un retour de
  visibilité), relâchant immédiatement si fermé entre-temps.
  `cleanupCookingMode()` protégée par un drapeau (`cookingModeCleaned`),
  ne s'exécutant réellement qu'une seule fois quel que soit le nombre
  d'appels.
- **Résultat obtenu** : ✅ Réussi — testé la course exacte décrite :
  fermeture immédiate simulée AVANT la résolution de la demande de
  Wake Lock (0 relâchement à cet instant, confirmé), puis Android
  "accorde" le verrou après coup (1 relâchement correctement déclenché
  à ce moment). Testé aussi le vrai scénario de double appel (bouton
  puis `MutationObserver` réel, pas un appel direct répété) : un seul
  relâchement au total. Non-régression confirmée sur Échap et la
  fermeture par bouton (toujours fonctionnels).
- **Version testée** : v157

### 19.6 — Demandes de Wake Lock simultanées *(cause racine trouvée et corrigée, v158)*
- **Contexte** : deux demandes de Wake Lock pouvaient s'exécuter en
  parallèle (une à l'ouverture, une autre lors d'un retour de
  visibilité) — celle qui se terminait en second écrasait la référence
  de l'autre, "perdant" le premier verrou (jamais relâché). Un risque
  additionnel existait dans `releaseWakeLock()` elle-même : la variable
  n'était remise à `null` qu'après avoir attendu `release()`, ce qui
  pouvait effacer un NOUVEAU verrou assigné entre-temps par une demande
  différente survenue pendant cette attente.
- **Corrigé** : une promesse partagée empêche désormais deux vraies
  demandes simultanées — un second appel pendant qu'une demande est
  déjà en cours attend simplement le résultat de la première plutôt
  que d'en lancer une nouvelle. `releaseWakeLock()` capture le verrou
  localement et remet la variable globale à `null` immédiatement,
  avant d'attendre `release()`.
- **Résultat obtenu** : ✅ Réussi — testé les deux scénarios exacts :
  deux appels "simultanés" à `requestWakeLock()` ne déclenchent qu'un
  seul vrai appel à `navigator.wakeLock.request()`, les deux appelants
  recevant correctement le même résultat ; et, pour la course au
  relâchement, un nouveau verrou assigné pendant qu'un ancien
  relâchement est encore en attente **survit** correctement — vérifié
  en confirmant que ce nouveau verrou est bien relâché lors de la
  fermeture réelle qui suit, pas perdu silencieusement.
- **Non-régression** : Échap, fermeture par bouton, octroi tardif après
  fermeture simple, et idempotence du nettoyage — tous revérifiés,
  toujours fonctionnels.
- **Version testée** : v158

### 19.7 — Minuteur basé sur une échéance absolue *(amélioration recommandée, implémentée et testée, v159)*
- **Contexte** : le minuteur reposait sur un simple `remaining--` à
  chaque `tick()` — si Android retarde ou saute un tick (l'app passe
  brièvement en arrière-plan, le moteur JS est occupé...), ce retard
  s'accumule silencieusement, faisant sonner l'alarme plus tard que
  prévu même à l'écran visible, indépendamment du Wake Lock.
- **Corrigé** : le temps restant est désormais recalculé à chaque tick
  à partir d'une échéance absolue (`endAt = Date.now() + durée`,
  calculée une fois au démarrage/reprise), pas par simple
  décrémentation — `remaining = Math.max(0, Math.round((endAt -
  Date.now()) / 1000))`.
- **Résultat obtenu** : ✅ Réussi — testé avec un bond d'horloge simulé
  de 3,5 secondes sur un minuteur de 3 secondes (représentant un
  retard Android) : l'alarme se déclenche correctement dès le premier
  tick suivant, sans attendre les tick manqués. Comportement normal
  (sans retard) confirmé inchangé : décompte correct seconde par
  seconde, alarme à l'heure exacte. Pause/reprise testée : le temps
  reste bien figé pendant la pause, une nouvelle échéance est
  correctement recalculée à la reprise à partir du temps restant.
- **Version testée** : v159

### 19.8 — Registre de réservations du garde-manger finalisé *(6 sous-points implémentés et testés, v160)*
- **Contexte** : le registre par source (v154) fonctionnait
  correctement en interne, mais restait invisible et non géré pour
  l'utilisateur — plusieurs points concrets manquaient.
- **Implémenté et testé, chaque sous-point individuellement** :
  1. **Affichage des réservations entièrement couvertes** (celles qui
     ne produisent aucun article de courses) — nouvelle section
     "Réservations en cours" dans l'écran garde-manger, affichée même
     si le garde-manger est vide.
  2. **Annulation individuelle** — testé, une réservation précise se
     retire sans toucher aux autres.
  3. **Réinitialisation même liste vide** — testée, le bouton reste
     disponible et fonctionne même sans aucun article de garde-manger
     ni de courses.
  4. **Inclusion dans les sauvegardes** — migré de localStorage vers
     le store `kv` (IndexedDB), déjà couvert par le mécanisme de
     sauvegarde existant. Testé le cycle complet : sauvegarde puis
     restauration, les réservations survivent correctement (au lieu
     d'être systématiquement effacées comme avant ce correctif).
  5. **Validation des entrées chargées** — nouvelle fonction
     `sanitizePantryClaims()`, testée avec 8 cas dont 6 malformés
     (null, quantité négative, type de source invalide, clé vide,
     champ manquant, valeur non-objet) : seules les 2 entrées
     réellement valides sont conservées.
  6. **Ancien format v153** — testé explicitement : un objet (ancien
     format) donné à `sanitizePantryClaims()` renvoie correctement un
     tableau vide, sans planter.
- **Défaut trouvé en testant l'affichage** : le nom d'ingrédient
  affiché utilisait la clé normalisée (minuscules, ex. "sucre") au lieu
  du vrai nom, faisant échouer silencieusement la traduction. Corrigé
  en retrouvant le nom correctement casé dans `state.ingredientNames`
  avant de traduire — testé, "Sucre"/"Farine" s'affichent maintenant
  correctement traduits.
- **Non-régression** : tests précédents du registre (fusion précise,
  suppression garde-manger, ajout unitaire) tous relancés avec succès.
  Un ancien test (`test_pantry_reset`) a été retiré : il utilisait un
  format d'API obsolète (v150) et testait un comportement
  intentionnellement changé par ce correctif (la restauration de
  sauvegarde restaure désormais les réservations au lieu de les
  effacer) — les cas qu'il couvrait restent testés par les tests plus
  récents avec la bonne API.
- **Version testée** : v160

### 19.9 — Notification système du minuteur *(implémentée et testée, v161)*
- **Contexte** : le minuteur sonne et vibre correctement quand l'app
  est visible, mais rien n'était affiché quand l'app tourne encore en
  arrière-plan sans être au premier plan — améliore ce cas précis, sans
  prétendre résoudre l'écran verrouillé (voir section 19.1/19.3).
- **Implémenté** :
  1. Demande d'autorisation au premier démarrage effectif d'un
     minuteur (moment naturel, jamais proactive au chargement de la
     page), une seule fois par session.
  2. Notification affichée via `registration.showNotification()` (le
     service worker) plutôt que le constructeur direct — meilleure
     prise en charge Android — quand le minuteur atteint zéro, en plus
     de la sonnerie/vibration existantes.
  3. Gestion du clic sur la notification (`notificationclick` dans
     `sw.js`) : ramène au premier plan une fenêtre déjà ouverte de
     l'application, ou en ouvre une si aucune n'est disponible.
- **Résultat obtenu** : ✅ Réussi — testé : une seule vraie demande
  d'autorisation même après plusieurs appels ; permission déjà refusée
  correctement gérée sans redemander ; notification affichée avec le
  bon titre/texte/icône quand accordée. **Intégration complète testée**
  avec le vrai minuteur : démarrage → expiration → notification
  affichée automatiquement, confirmé de bout en bout.
- **Non-régression** : tests précédents du minuteur (échéance absolue,
  pause/reprise) et du mode cuisine (Wake Lock, nettoyage) tous
  relancés avec succès.
- **Version testée** : v161

### 19.10 — Six défauts confirmés et corrigés sur le minuteur/notifications/réservations *(v162)*
- **1. Minuteur déclenché ~0,5s trop tôt** *(cause racine confirmée et corrigée)* :
  `Math.round((endAt-Date.now())/1000)` donnait 0 dès 400ms restant,
  déclenchant l'alarme prématurément. Corrigé : le déclenchement se
  décide désormais sur `msLeft <= 0` (millisecondes brutes), l'affichage
  utilise `Math.ceil` (jamais "0" tant qu'il reste vraiment du temps).
  Testé avec le vrai `tick()` et une échéance à 400ms exactement : ne se
  déclenche plus avant l'échéance réelle.
- **2. Pause ne recalculait pas le temps exact** *(cause racine confirmée et corrigée)* :
  testé avec une manipulation directe de l'horloge (isolant le vrai
  défaut, mon premier essai avait une attente erronée) : la pause
  recalcule bien depuis l'heure réelle, pas la valeur figée du dernier
  tick.
- **3. Notifications de minuteurs qui s'écrasaient** *(cause racine confirmée et corrigée)* :
  identifiant unique par minuteur (`cooking-timer-{id}`) au lieu du même
  pour tous, durée d'origine incluse dans le texte. Testé avec deux
  minuteurs terminés simultanément : deux notifications distinctes
  confirmées (tags différents).
- **4. Réservations sans unité affichée** *(cause racine confirmée et corrigée)* :
  `claimKind` (poids/volume/unité de comptage précise) propagé depuis
  `computePantryReduction()` jusqu'à l'affichage via une nouvelle
  fonction `kindToDisplayUnit()`, avec validation renforcée pour ce
  nouveau champ optionnel.
- **5. Cas limite Wake Lock (fermeture/réouverture rapide)** *(cause racine confirmée, corrigée en 2 temps)* :
  un identifiant de session partagé remplace le simple booléen par
  fermeture — mais un premier correctif s'est révélé encore incomplet
  à l'test : le callback d'une session fermée (A) pouvait relâcher à
  tort le verrou qu'une session rouverte immédiatement (B) recevait via
  la même demande partagée. Corrigé en ne relâchant que si vraiment
  plus aucune session n'est active (`activeCookingSessionId === null`),
  pas seulement si CETTE session précise ne l'est plus. Testé le
  scénario exact : B conserve bien son verrou actif, 0 relâchement
  erroné ; testé aussi que la fermeture simple sans réouverture continue
  de relâcher correctement.
- **6. Refus des notifications jamais affiché** *(corrigé)* : message
  affiché à l'ouverture du mode cuisine si déjà refusé, et après une
  demande refusée au démarrage d'un minuteur.
- **Non traité, consciemment différé** (classés "moins urgents" par
  l'audit) : écritures IndexedDB des réservations non explicitement
  attendues ; migration de l'ancien format v153 (toujours ignoré plutôt
  que converti, aucune origine identifiable pour le faire fidèlement) ;
  clic sur une notification ne cible pas la recette/minuteur précis ;
  arrêter l'alarme dans l'app ne retire pas la notification déjà
  affichée.
- **Non-régression** : 17 tests relancés (minuteur, mode cuisine,
  Wake Lock, notifications, registre de réservations), tous réussis.
- **Test physique encore indispensable** : comme le note l'audit, rien
  ne remplace une confirmation réelle sur le Samsung A06 — permission
  au premier minuteur, notification visible app ouverte/arrière-plan,
  comportement écran verrouillé, deux minuteurs successifs, clic sur
  la notification, présence après arrêt de l'alarme.
- **Version testée** : v162

### 19.11 — Les 4 points "moins urgents" traités *(v163)*
- **1. Écritures IndexedDB non attendues** : `commitPantryClaim()`,
  `releasePantryClaimsForIngredient()` et `releasePantryClaimsForSource()`
  sont désormais `async`, tous leurs appelants (8 au total, dont 2
  boucles converties de `.forEach` à `for...of`) attendent correctement
  leur exécution avant de continuer.
- **2. Migration de l'ancien format v153** : plutôt que d'être
  silencieusement ignoré, chaque ancienne réservation `{ingrédient:
  total}` devient une entrée `sourceType: "legacy"` — visible et
  annulable individuellement via l'écran garde-manger (libellé "ancienne
  réservation, origine non conservée"), plutôt que perdue sans que
  l'utilisateur ne s'en rende compte. Testé : migration confirmée,
  persistée en nouveau format (ne se reproduit qu'une fois), libellé
  correctement affiché.
- **3. Clic sur la notification ne ciblait pas la recette précise** :
  corrigé pour les deux cas — aucune fenêtre déjà ouverte (navigation
  avec `?openRecipe=<id>`, lu et retiré de l'URL au démarrage, suivant
  le même modèle que le paramètre `?screen=` existant pour les
  raccourcis PWA) et une fenêtre déjà ouverte (message envoyé via
  `postMessage`, écouté par l'application). Testé les deux chemins
  séparément avec un vrai chargement de page (paramètre d'URL) et un
  vrai événement `message` (postMessage) : les deux ouvrent
  correctement le mode cuisine de la bonne recette.
- **4. Arrêter l'alarme ne retirait pas la notification** : nouvelle
  fonction `closeTimerNotification()`, appelée à la fois lors de l'arrêt
  individuel d'une alarme et lors de la fermeture complète du mode
  cuisine (cohérence). Testé : la notification du minuteur concerné est
  bien fermée après arrêt de son alarme.
- **Non-régression** : 21 tests relancés (minuteur, mode cuisine, Wake
  Lock, notifications, registre de réservations), tous réussis.
- **Version testée** : v163

### 19.12 — Régression critique et 2 corrections incomplètes de la v163 *(v164)*
- **Priorité critique — double mode cuisine au clic sur notification**
  *(régression confirmée exactement et corrigée)* : le gestionnaire de
  message rappelait `openCookingMode()` sans jamais vérifier si une
  session était déjà active. Confirmé exactement : `openCookingMode()`
  réinitialise `state.cookingTimers = []` à chaque appel, orphelinant
  les minuteurs d'une session précédente encore active — leur sonnerie
  aurait continué indéfiniment, sans plus aucun moyen de l'arrêter
  depuis l'écran. Corrigé : nouvelle référence `closeActiveCookingMode`
  exposée par chaque session, appelée pour fermer proprement l'ancienne
  avant d'en ouvrir une autre ; si la même recette est déjà ouverte, ne
  rien faire de plus (le `focus()` du service worker suffit). **Testé
  le scénario exact de l'audit** : clic sur la même recette déjà ouverte
  (aucun doublon, minuteur original intact) ; clic sur une AUTRE recette
  pendant qu'un minuteur de la première sonne (ancienne session
  proprement fermée et nettoyée, une seule fenêtre au final).
- **Priorité haute — IndexedDB toujours non attendu** *(cause racine
  confirmée exactement et corrigée)* : `persistPantryClaims()` n'avait
  toujours pas de `return` devant `kvSet(...)`, résolvant immédiatement
  sans jamais attendre la vraie écriture — les 8 `await` ajoutés en
  v163 n'apportaient donc aucune protection réelle. Corrigé avec
  `return kvSet(...)`. **Testé en reproduisant la vérification de
  l'audit** : avec une écriture artificiellement ralentie à 300ms,
  `await persistPantryClaims()` prend maintenant bien ~300ms (au lieu de
  résoudre immédiatement).
- **Priorité moyenne — bouton poubelle ne fermait pas la notification**
  *(confirmé exactement et corrigé)* : `closeTimerNotification(timer)`
  ajouté au gestionnaire du bouton poubelle, comme déjà fait pour
  `dismissAlarm()`. Testé et confirmé.
- **Commentaire obsolète corrigé** : `persistPantryClaims()` mentionnait
  encore "localStorage" alors que le stockage est IndexedDB depuis la
  v160.
- **Non-régression** : 23 tests relancés (minuteur, mode cuisine, Wake
  Lock, notifications, registre de réservations), tous réussis.
- **Précision honnête sur la suite de tests** : comme le note l'audit,
  ces "N tests" ne sont pas une suite automatisée présente dans le
  dépôt — ce sont des scripts Playwright ponctuels que je conserve et
  relance manuellement à chaque session, documentés ici au fur et à
  mesure. Voir aussi le point 17.3 du même sujet.
- **Test physique Android avec deux minuteurs** : ✅ confirmé réussi par
  l'utilisateur — le scénario décisif recommandé par l'audit (deux
  minuteurs lancés, application en arrière-plan, deux notifications
  reçues, clic sur une notification) fonctionne correctement : le mode
  cuisine existant revient au premier plan sans doublon ni sonnerie
  impossible à arrêter.
- **Version testée** : v164

### 19.13 — Confirmation physique finale du système minuteur/notifications *(physique — réussi)*
- **Résultat obtenu** : ✅ le test physique décisif (deux minuteurs,
  arrière-plan, notifications, clic ciblant la bonne recette) est
  confirmé réussi par l'utilisateur sur son appareil réel.
- **Portée** : clôture la série de corrections apportées entre les
  v155 et v164 sur le Wake Lock, le minuteur basé sur une échéance
  absolue, le registre de réservations et les notifications système —
  l'ensemble est désormais validé à la fois par simulation (tests
  Playwright ponctuels) et par un usage réel sur Samsung Galaxy A06.
- **Limites toujours valables, non concernées par cette confirmation** :
  écran verrouillé (le minuteur reste suspendu tant que l'écran est
  verrouillé — nécessiterait une vraie application native, prévu pour
  la conversion Play Store) ; l'alarme sonne dès le réveil de l'écran,
  même avant la saisie du code PIN (comportement du navigateur, pas de
  l'application).

### 20 — Tesseract.js en local : implémentation complète *(v165)*

**Contexte** : l'OCR dépendait jusqu'ici entièrement du CDN jsDelivr —
premier chargement parfois impossible, aucun fonctionnement hors
connexion tant que ce chargement n'avait pas eu lieu au moins une fois,
risque de changement imprévu d'une version distante.

**Difficulté rencontrée et résolue** : mes premières tentatives de
récupérer moi-même les fichiers (via `web_fetch`) ont échoué de façon
silencieuse — même un fichier de taille modérée (`worker.min.js`,
~130 Ko) revenait tronqué en fin de contenu. Plutôt que de livrer des
fichiers corrompus sans m'en rendre compte, l'utilisateur a téléchargé
et fourni les 10 fichiers nécessaires directement.

**Fichiers intégrés** (`lib/tesseract/`, ~48 Mo au total, largement
sous la limite de 100 Mo convenue) :
- `tesseract.min.js` + `worker.min.js` — v5.1.1, verrouillée
- `core/tesseract-core*.wasm.js` — les 4 variantes (SIMD/non-SIMD,
  legacy/non-legacy), v5.1.1 assortie — Tesseract choisit lui-même
  celle compatible avec l'appareil ; une seule variante fixe aurait pu
  empêcher l'OCR de fonctionner sur un appareil plus ancien
- `lang/{fra,eng,spa,deu}.traineddata.gz` — palier qualité "standard"
  (meilleure précision qu'un palier "rapide"), format tessdata 4.0.0

**Stratégie de chargement à la demande** : contrairement aux fichiers
fixes ci-dessus, les données de langue ne sont volontairement PAS
préchargées à l'installation (`sw.js`) — chacune n'est téléchargée
qu'au premier import photo dans cette langue précise, pour ne pas
alourdir le tout premier chargement de l'application d'environ 40 Mo
pour des langues qu'une personne n'utilisera peut-être jamais.

**Découverte importante en testant** : Tesseract.js gère lui-même la
persistance hors connexion des données de langue via sa propre base
IndexedDB (`keyval-store`), entièrement indépendante du service worker
de l'application. Mon premier test de vérification (cherchant le
fichier dans le cache du service worker) donnait donc un faux négatif
— corrigé en vérifiant plutôt la présence de cette base IndexedDB, puis
confirmé par un vrai test en conditions hors connexion simulées
(`context.set_offline(True)`).

**Autres changements** :
- `sw.js` : le mécanisme `CROSS_ORIGIN_TO_CACHE` supprimé (plus aucune
  ressource externe, Tesseract étant désormais entièrement local) ;
  corrigé au passage un manque réel — les fichiers non préchargés
  n'étaient jamais mis en cache après leur premier téléchargement, ce
  qui aurait empêché le fonctionnement hors connexion des données de
  langue même via le service worker
- `index.html` : CSP resserrée, `cdn.jsdelivr.net` retiré de
  `script-src` et `worker-src`
- `POLITIQUE_DE_CONFIDENTIALITE.md` et `lib/LICENSES.md` mis à jour

**Tests réels effectués** (pas seulement de la syntaxe) :
- Les 10 fichiers servis correctement avec les tailles attendues
- Intégrité gzip des 4 fichiers de langue vérifiée (décompression
  réussie)
- Worker Tesseract initialisé avec succès avec les chemins locaux
- **OCR réel réussi** : texte généré sur un canvas ("Bonjour Monde")
  correctement reconnu à 95 % de confiance
- **OCR confirmé fonctionnel entièrement hors connexion** après ce
  premier téléchargement, testé avec une vraie simulation de
  déconnexion réseau
- 23 tests de régression existants relancés, tous toujours corrects

**Ce que ce changement ne corrige pas** (rappel) : la fiabilité de
l'OCR lui-même sur de vraies photos HelloFresh (colonnes mélangées,
tableaux mal interprétés, photos inclinées) reste un chantier séparé,
non traité ici — reste un chantier séparé, mentionné comme tel dans le
suivi du projet.

**Version testée** : v165

### 21 — Vérification de la v165 réelle sur GitHub, corrections *(v166)*

**Contrôles confirmés par l'audit** : empreintes SHA-256 des 10 fichiers
Tesseract exactement conformes aux paquets npm officiels (aucune
troncature ni altération) ; reconnaissance indépendante réussie sur une
vraie photo HelloFresh (confiance 83, plusieurs lignes correctement
lues) ; limitation Cloudflare confirmée active en conditions réelles
(30 requêtes acceptées puis 429, exactement comme testé par
l'utilisateur lui-même juste avant).

**Priorité 1 — limite de sauvegarde à 2 paliers, corrigée** : la
décision prise plus tôt dans le projet (avertissement à 50 Mo, refus
seulement au-delà de 100 Mo) n'avait jamais été réellement implémentée
— `MAX_BACKUP_FILE_SIZE` était toujours à 50 Mo dans le code livré.
Corrigé : `BACKUP_WARNING_SIZE` (50 Mo, avertissement avec confirmation)
et `MAX_BACKUP_FILE_SIZE` (100 Mo, refus définitif) séparés. Testé
directement : un fichier de 60 Mo est accepté par `parseBackupFile()`
(la confirmation intermédiaire est gérée par l'appelant), un fichier de
110 Mo est bien refusé.

**Priorité 2 — cache Tesseract lié à la version de l'app : désaccord
argumenté, aucun changement fait**. L'audit recommandait un nom de
cache séparé et stable pour Tesseract, pour éviter que les données de
langue ne soient perdues à chaque changement de version. **Vérifié
directement par deux tests dédiés, et le problème ne se produit pas** :
- Les données de langue sont persistées par Tesseract.js lui-même dans
  sa propre base IndexedDB (`keyval-store`), entièrement indépendante
  du cache du service worker de l'application — supprimer le cache du
  service worker (simulant un changement de version) puis tester l'OCR
  hors connexion fonctionne toujours correctement, la langue n'ayant
  jamais été perdue.
- Le moteur WASM, lui, passe bien par le cache du service worker, mais
  une vraie migration de version précache TOUJOURS le nouveau nom
  AVANT de supprimer l'ancien (comportement standard de l'événement
  "install" survenant avant "activate") — testé en simulant cette
  migration exacte (v165 → v166) puis un usage hors connexion : la
  création d'un nouveau worker Tesseract réussit toujours.

Ce point de l'audit repose sur un raisonnement statique plausible mais
non vérifié empiriquement — les deux tests réels contredisent le risque
décrit. Introduire un second nom de cache aurait ajouté de la
complexité (logique de nettoyage supplémentaire à maintenir) pour un
problème qui ne se manifeste pas dans les faits.

**Priorité 3 — fiabilité de l'OCR sur fiches complexes** : confirmée
comme limite connue et déjà documentée, aucune action nouvelle
attendue à ce stade (voir les tests OCR mis en pause plus haut dans ce
document).

**Corrections documentaires** : les deux commentaires (`app.js`,
`sw.js`) pointant vers `lib/tesseract/LICENSES.md` (chemin inexistant)
corrigés vers le vrai chemin `lib/LICENSES.md`. Le `worker/README.md`
mentionnant encore une configuration possible depuis le tableau de bord
Cloudflare avait déjà été corrigé en conversation (Wrangler présenté
comme seule méthode réellement validée) mais n'avait jamais été inclus
dans une livraison — inclus cette fois.

**Non-régression** : 29 tests relancés (minuteur, mode cuisine, Wake
Lock, notifications, registre de réservations, Tesseract local, OCR
réel, limites de sauvegarde, survie du cache aux migrations de
version), tous corrects.

**Version testée** : v166

### 22 — Trois corrections mineures de message et de documentation *(v167)*

**Contrôles confirmés par ce second audit** : tous les seuils de
sauvegarde (0-50 Mo sans avertissement, 50-100 Mo avec confirmation,
au-delà refusé), les 519 clés de traduction identiques dans les 4
langues, tous les fichiers préchargés existants, les 4 fichiers de
langue Tesseract valides et inchangés depuis la v165. **Accord obtenu
sur le point du cache Tesseract** : plus de risque fonctionnel
justifiant un cache séparé, confirmé par les deux audits indépendants
en plus de mes propres tests.

**Priorité moyenne — message trompeur pour fichier >100 Mo, corrigé** :
confirmé exactement — un fichier dépassant la limite dure affichait le
même message générique qu'un fichier simplement invalide ("Ce fichier
n'est pas un fichier de sauvegarde valide"), sans indiquer la vraie
raison. Corrigé avec un message dédié précisant la limite exacte
dépassée. **Testé directement** : un fichier de 110 Mo affiche
maintenant bien "This file exceeds the 100 MB limit and cannot be
imported" (et l'équivalent dans les 3 autres langues) plutôt que le
message générique.

**Priorité faible — résumé périmé sur Tesseract, corrigé** : un point
du résumé final, jamais mis à jour depuis la v141 (bien avant le
passage en local de la v165), affirmait encore que Tesseract restait
chargé depuis un CDN. Corrigé pour refléter l'état réel.

**Priorité faible — contradiction sur la configuration Rate Limiting,
corrigée** : `worker/cloudflare-worker.js` et `worker/wrangler.toml`
mentionnaient encore une configuration possible depuis le tableau de
bord Cloudflare, en contradiction avec le `README.md` déjà corrigé
(Wrangler étant la seule méthode qui fonctionne réellement, confirmé
par la documentation officielle Cloudflare et par un déploiement réel
réussi). Les deux fichiers corrigés pour rester cohérents avec le
README.

**Limite de vérification reconnue par l'audit lui-même** : les tests
ne sont pas une suite automatisée intégrée au dépôt — précision déjà
documentée au point 19.12, toujours valable.

**Non-régression** : 30 tests relancés (les 29 précédents plus un
nouveau test dédié au message d'erreur de taille), tous corrects.

**Version testée** : v167

### 23 — Analyseur OCR : les 5 défauts prioritaires corrigés et testés sur textes réels *(v168)*

**Contexte** : test réel sur 8 vraies photos (fiches HelloFresh salade
grecque et barramundi, captures Marmiton financiers) confirmant que
l'OCR brut et Tesseract local fonctionnent bien, mais que l'analyseur
classait mal les sections et transformait trop facilement du texte
parasite en ingrédients. Toutes les causes précises ont été confirmées
en examinant le code, puis corrigées et testées avec des textes
reconstitués fidèlement à partir des vraies photos fournies.

**Priorité 1 — découpage réel de la zone ingrédients, corrigé** :
`deriveSectionDataForPhoto()` ne faisait auparavant que retirer les
lignes de titre où qu'elles apparaissent, sans jamais couper la liste
à la première limite de section suivante — une "Valeurs
nutritionnelles" au milieu laissait passer toutes les lignes
numériques qui la suivent. Corrigé avec un vrai découpage
(`slice()` entre le titre et la limite suivante, comme le fait déjà
`parseOcrRecipeText()` pour les photos "recette complète"). **Testé
avec un texte reconstitué depuis la vraie fiche salade grecque** : 35
"ingrédients" fantômes de l'audit → 12, correspondant exactement aux
12 vraies lignes de la fiche (aucune ligne de nutrition/allergène
n'ayant fuité).

**Priorité 2 — tolérance aux symboles OCR avant les titres, corrigée** :
les motifs de reconnaissance de section exigeaient auparavant que le
mot-clé soit exactement en tout début de ligne — un OCR produisant
"= Ingrédients" ou "« Préparation" ne reconnaissait plus la section du
tout. Corrigé en tolérant un petit nombre de symboles parasites
courants avant le mot-clé. **Testé avec les artefacts exacts remontés
par l'audit** ("= Ingrédients", "« Préparation", "• Étapes") : tous
correctement reconnus, sans casser la reconnaissance normale.

**Priorité 3 — découpage réel de la zone préparation, corrigé** : même
défaut que le point 1, côté préparation — une photo classée
"Préparation" conservait aussi tout ce qui précédait le titre (barre
de navigateur, navigation Marmiton) et tout ce qui suivait les vraies
étapes (commentaires, "Note de l'auteur"). Corrigé avec le même
découpage réel, complété par l'ajout de "Anonyme" (pseudonyme de
commentaire très courant sur Marmiton) à la liste des marqueurs de fin
de contenu. **Testé avec un texte reconstitué depuis les captures
Marmiton fournies** : ni le bruit de navigateur ni le commentaire de
fin ne contaminent plus la description, les 5 étapes réelles étant
parfaitement conservées.

**Priorité 4 — vraie détection "Informations générales", corrigée** :
`detectPhotoSection()` ne pouvait auparavant jamais choisir "general"
— une couverture (nom + durée, sans ingrédients ni vraies étapes)
tombait systématiquement dans "Préparation" dès que son texte dépassait
20 caractères. Cause racine trouvée en creusant : le format de durée
"À table dans : 35-45 Min" (courant chez HelloFresh) n'était reconnu
par aucun motif existant, empêchant tout signal de temps d'être détecté
pour alimenter une distinction. Corrigé en ajoutant la reconnaissance
de ce format, et en distinguant une vraie section d'étapes (présence
d'une numérotation d'étapes, ou plusieurs lignes) d'une simple
accroche de couverture. **Testé avec la vraie couverture barramundi
fournie** : correctement classée "general" plutôt que "preparation".
**Régression détectée et corrigée en cours de route** : un premier
seuil basé uniquement sur le nombre de lignes cassait deux cas déjà
couverts par `test_multiphoto.py` (une recette courte de seulement 1-2
étapes numérotées) — corrigé en priorisant la détection d'une
numérotation d'étapes sur le simple comptage de lignes, confirmé par
une relecture complète de la suite existante.

**Priorité 5 — rejet des lignes non-ingrédients, corrigée** : toute
ligne non vide devenait auparavant un "ingrédient" valide (avec unité
générique "pièce"), sans aucun filtre de vraisemblance. Corrigé avec
`looksLikeIngredientLine()` : rejette les mots-clés parasites connus
(ustensiles, valeurs nutritionnelles, allergènes, "À ajouter
vous-même"...), les lignes purement numériques (lignes de tableau de
valeurs), et les phrases trop longues pour être un simple ingrédient.
**Attention portée à un risque identifié pendant les tests** : un
premier motif de rejet pour "sel" était trop large et aurait rejeté à
tort un vrai ingrédient "Sel 1 pincée" — corrigé pour ne cibler que la
ligne du tableau nutritionnel "Sel (g)". Testé séparément pour
confirmer les deux cas distingués correctement.

**Résidu signalé non reproduit** : le texte d'avertissement en double
dans `renderImportPhoto()` n'a pas été retrouvé dans le code actuel —
une seule occurrence existe, et un test réel en conditions de
navigateur confirme qu'il ne s'affiche qu'une fois. Possible faux
positif de l'audit, ou déjà corrigé lors d'une session précédente.

**Priorité moyenne — unité "barquette" ajoutée** : reconnue comme
nouvelle unité de comptage (même famille que boîte/sachet/pot, non
convertible avec les autres), avec ses traductions dans les 4 langues.
Testée avec l'exemple exact de l'audit ("Tomates cerises 1
barquette(s)") : correctement séparée en nom + quantité + unité,
plutôt que d'être absorbée dans le nom sous l'unité générique "pièce".
L'unité "filet" n'a pas été ajoutée : en examinant la vraie photo,
"Filet de barramundi" est le NOM de l'ingrédient (l'unité réelle étant
déjà "pièce", correctement reconnue), pas une unité de mesure
distincte à ajouter.

**Ce que cette session ne corrige pas, comme prévu** : le
prétraitement d'image (redressement, contraste, recadrage) reste hors
scope — un chantier de reconnaissance d'image, pas d'analyse de texte.
Les fractions mal reconnues par l'OCR lui-même (½ → %) restent une
limite du moteur, pas de l'analyseur.

**Non-régression** : 23 tests relancés, dont 2 régressions repérées et
corrigées en cours de route (voir priorité 4) avant validation finale
— tous corrects.

**Version testée** : v168

### 24 — Migration Tesseract.js 5.1.1 → 7.0.0 *(v169)*

**Contexte** : avant d'entreprendre le chantier de reconstruction des
colonnes par coordonnées (recommandé par un second avis externe),
l'utilisateur a choisi de migrer d'abord vers Tesseract.js 7 — pour ne
pas risquer de refaire ce travail si la version change quoi que ce
soit à l'import, même de façon infime. **Cette prudence s'est avérée
justifiée** : la migration a révélé un changement réel, repéré et
corrigé avant qu'il ne cause de problème.

**Fichiers mis à jour** (`lib/tesseract/`) : `tesseract.min.js` et
`worker.min.js` remplacés par la version 7.0.0 exacte. Moteur WASM
(`tesseract.js-core@7.0.0`) : les 4 variantes historiques remplacées,
**plus 2 nouvelles variantes "Relaxed SIMD"** introduites par cette
version (`tesseract-core-relaxedsimd.wasm.js` et
`-relaxedsimd-lstm.wasm.js`), portant le total à 6 fichiers. **Données
de langue non retéléchargées** : le format tessdata (4.0.0) est resté
identique depuis la v5, confirmé par recherche avant de demander quoi
que ce soit à l'utilisateur — les 4 fichiers de langue existants
restent valides tels quels.

**Problème réel rencontré et résolu** : la première tentative
d'initialisation échouait (`NetworkError` sur
`tesseract-core-relaxedsimd-lstm.wasm.js`) — la v7 détecte désormais le
support "Relaxed SIMD" du navigateur et tente de charger une variante
non anticipée, absente des 4 fichiers initialement fournis. Cause
racine confirmée en retrouvant le code source réel de la fonction de
sélection du moteur (`getCore.js` de tesseract.js) : la détection
`relaxedSimd()` prime désormais sur `simd()`. Corrigé en récupérant les
2 fichiers manquants — testé à nouveau, l'initialisation et l'OCR réel
fonctionnent alors correctement.

**Changement de structure confirmé et documenté** (celui redouté par
l'utilisateur) : `blocks`, `lines`, `words` et `paragraphs` ne sont plus
retournés par défaut par `worker.recognize()` en v7 (contrairement à la
v5.1.1, qui les incluait automatiquement) — confirmé par un test direct
comparant les deux versions. **Sans impact sur les fonctionnalités
actuelles** (l'application n'utilise que `data.text`), mais **information
cruciale pour le futur chantier des colonnes** : il faudra explicitement
demander `{ blocks: true }` à l'appel de `recognize()`. Vérifié que
cette réactivation explicite fonctionne bien : structure `blocks →
paragraphs → { text, bbox }` correctement retournée une fois demandée.

**Tests réels effectués** :
- OCR réel toujours fonctionnel après migration (95 % de confiance,
  identique à la v5.1.1)
- Fonctionnement hors connexion confirmé après un vrai changement de
  version de cache (v168 → v169), avec les 2 nouveaux fichiers
  correctement précachés
- Les 5 corrections de l'analyseur OCR (v168) et toute la suite de
  régression existante relancées sans aucune régression

**Documentation mise à jour** : `lib/LICENSES.md`, commentaires dans
`app.js` et `sw.js` reflétant la version 7.0.0 et les 6 variantes.

**Prochaine étape, non commencée ici** : exploitation des coordonnées
(`blocks`/`paragraphs`/`bbox`) pour reconstruire les colonnes avant
analyse — le vrai chantier structurel, désormais possible à construire
sur une base stable.

**Version testée** : v169

### 25 — Reconstruction des colonnes par coordonnées OCR *(v170)*

**Contexte** : suite à l'audit détaillé testant l'analyseur v169 sur les
8 vraies photos du projet avec Tesseract 7, confirmant que le vrai
défaut restant est la perte de la mise en page (colonnes mélangées)
avant même que l'analyseur ne reçoive le texte. Cette session a
exécuté de l'OCR réel (pas simulé) sur les photos, avec les
coordonnées explicitement demandées, pour concevoir et valider une
vraie correction géométrique.

**Priorité 1 — reconstruction des colonnes, implémentée et validée sur
photos réelles** : `runOcrOnImage()` demande maintenant `{ blocks: true
}` (nécessaire depuis la migration v7, qui ne renvoie plus cette
donnée par défaut) et reconstruit chaque ligne à partir des
coordonnées des mots (`reconstructTextFromBlocks()`), plutôt que
d'utiliser le texte brut tel quel.

Principe validé empiriquement sur les vraies photos HelloFresh (pas de
supposition théorique) : une ligne d'ingrédient contient déjà
normalement un grand espace horizontal entre le nom et sa quantité
(mise en page en tableau, quantités alignées à droite) — ce premier
grand espace est normal et ne doit jamais servir à couper la ligne. Un
DEUXIÈME grand espace qui suit correspond presque toujours au passage
vers la colonne voisine (étapes) : c'est là qu'il faut couper. Une
première tentative se basant sur la position horizontale absolue
(pourcentage de la largeur de l'image) s'est révélée incorrecte —
testée contre la vraie photo Barramundi, elle coupait aussi des
quantités légitimes quand le nom de l'ingrédient était court (donc la
quantité naturellement plus à droite). Corrigée en se basant sur le
RANG du grand espace (1er ignoré, 2ème et suivants coupés), pas sa
position absolue.

**Résultats concrets, mesurés avec du vrai OCR sur les vraies
photos** :
- Salade grecque : la contamination de la colonne "Quelques découpes"
  a quasiment disparu des lignes d'ingrédients
- Barramundi : passage de 18 "ingrédients" contaminés (constatés par
  l'audit) à 10-12 selon l'exécution, tous les ingrédients réels
  correctement séparés de leur quantité, sans texte de la colonne
  voisine

**Variabilité de l'OCR constatée et documentée honnêtement** : au cours
des tests, la même photo a occasionnellement produit un ordre de mots
légèrement différent selon les circonstances exactes du traitement
(résolution de redimensionnement, appels précédents sur le worker
partagé). Ce n'est pas un défaut de la fonction de reconstruction
elle-même (vérifiée correcte sur les données stables), mais une
caractéristique de Tesseract sur des mises en page ambiguës aux
limites de sa segmentation automatique — non totalement résolue, à
surveiller lors des prochains tests physiques.

**Priorité 2 — classification de la couverture Barramundi, cause
racine trouvée et corrigée** : `detectPhotoSection()` classait à tort
une photo de couverture (nom + durée, sans vraies étapes) en
"Préparation" dès que le bruit OCR d'une grande photo du plat
produisait plus de 3 lignes — la photo du plat lui-même étant
"lue" par erreur comme du texte. Cause racine confirmée avec le vrai
texte OCR de la vraie photo (des dizaines de lignes de charabia). Deux
tentatives de correction rejetées avant la bonne :
- Un filtre par ratio de lettres était trop permissif (du charabia
  contenant par hasard plus de 50% de lettres passait quand même)
- Un filtre par mots-outils français a été abandonné : trop
  spécifique à une seule langue (l'app en supporte 4), et les mots de 2
  lettres (ce, et, la, ou...) correspondaient par pur hasard dans du
  bruit aléatoire

Corrigé avec un critère indépendant de la langue : la longueur moyenne
des mots d'une ligne, calibrée empiriquement sur les vraies données
(bruit ≤ 2,4 caractères/mot, vrai texte ≥ 3,8) — séparation nette.
Seuil de lignes plausibles également relevé (3 → 6), du texte réel
mais hors-recette (mentions légales, instruction de pliage) pouvant
légitimement apparaître sur une couverture sans qu'il s'agisse de
vraies étapes. **Testé avec le vrai texte OCR de la vraie couverture
Barramundi** : correctement classée "general" après correction (contre
"preparation" avant).

**Point mineur — nom de recette = barre du navigateur, partiellement
corrigé** : sur une capture d'écran de navigateur, la première ligne
(barre d'adresse ou onglets) devenait le nom de la recette. Corrigé
pour ignorer une première ligne ressemblant à du bruit d'interface
(motif de domaine, plusieurs barres verticales de menu concaténé,
longueur moyenne de mot très faible), passant à la ligne suivante plus
plausible. **Limite honnête** : testé avec la vraie capture Marmiton la
plus chargée en interface (adresse + onglets + menu + bouton, 4 lignes
de bruit consécutives de natures différentes) — 3 des 4 lignes de
bruit sont désormais correctement ignorées, la 4ème (texte de bouton
mal reconnu) passe encore le filtre. Amélioration réelle mais
incomplète sur ce cas extrême ; non poursuivi davantage pour éviter
d'empiler des règles de plus en plus spécifiques à un seul exemple
(risque de sur-ajustement).

**Non traité dans cette session, chantier séparé confirmé plus
complexe** : la priorité 3 de l'audit (reconstruction d'une grille à 3
colonnes pour les photos de préparation HelloFresh, où chaque "ligne"
du texte brut mélange 3 étapes côte à côte) — vérifié avec du vrai OCR
sur la vraie photo, confirmé comme un problème géométriquement
différent (regroupement de blocs en colonnes distinctes, pas
simplement couper une ligne au bon endroit), nécessitant son propre
chantier dédié.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement de seuil, aucune régression.

**Version testée** : v170

### 26 — Fragilité du remplacement de texte corrigée, redimensionnement ajouté *(v171)*

**Contexte** : après le test physique sur Samsung montrant les 3 photos
Barramundi classées à tort en "Préparation" avec 4 personnes (au lieu
de 2), un second avis a mené sa propre vérification indépendante et
identifié la cause probable dans le code : `runOcrOnImage()` (v170)
remplaçait entièrement le texte brut par le texte reconstruit
(`reconstructTextFromBlocks(data) || data.text`), utilisé ensuite pour
TOUT — nom, personnes, section. Si la reconstruction géométrique
abîmait la ligne "Ingrédients pour X personnes" (segmentation
différente selon l'appareil/variante WASM), le marqueur de section ET
le nombre de personnes disparaissaient simultanément.

**Corrigé exactement comme suggéré** : `runOcrOnImage()` retourne
désormais `{ rawText, layoutText }` séparément, plus jamais un
remplacement. Le texte BRUT sert toujours à la détection de section,
du nom, des personnes et des temps (`parseOcrRecipeText`, appelé sur
`rawText`) ; le texte reconstruit ne sert qu'au nettoyage des lignes
d'ingrédients, via une nouvelle fonction commune
`extractIngredientsFromLines()` appliquée séparément aux deux textes.
Le résultat du texte reconstruit n'est retenu que s'il a LUI-MÊME
retrouvé son propre marqueur de section ; sinon, repli entier sur le
texte brut plutôt qu'un mélange risqué des deux. Le nombre de
personnes préfère toujours le texte brut quand les deux l'ont trouvé,
conformément à l'ordre de priorité suggéré.

**Testé avec le scénario exact rapporté** : simulé un texte reconstruit
endommagé (ligne titre disparue) à côté d'un texte brut intact —
confirmé que la section et les personnes restent correctement
détectées depuis le texte brut, et que l'extraction d'ingrédients
retombe bien sur le texte brut plutôt que d'échouer. Testé aussi le
cas où le texte reconstruit fonctionne bien : le nettoyage de
contamination continue de s'appliquer normalement dans ce cas.

**Découverte complémentaire en testant sur les vraies photos à pleine
résolution** : le second avis n'avait pas reproduit exactement les 3
classements "Préparation" du Samsung (chez lui : couverture et
préparation correctement classées) — en creusant avec du vrai OCR sur
les vraies photos à leur PLEINE résolution (jusqu'à 4080×3060,
correspondant à ce que fait réellement l'application, sans
redimensionnement jusqu'ici), confirmé que Tesseract segmente parfois
différemment à cette échelle par rapport à une image redimensionnée,
pouvant produire un ordre de lecture différent voire, sur la photo de
couverture la plus chargée visuellement, une perte quasi complète du
titre au profit du sous-titre. Ceci explique probablement pourquoi le
second avis (ayant peut-être traité les photos différemment) et le
test Samsung ne concordaient pas exactement.

**Amélioration ajoutée en conséquence** : `runOcrOnImage()` redimensionne
maintenant l'image (1600 px maximum) avant reconnaissance, avec repli
sur le fichier original en cas d'échec du redimensionnement lui-même.
**Testé sur les vraies photos** : le nombre de lignes conservées pour
les ingrédients Barramundi passe de 15 à 12 (plus proche des 10 réels)
avec ce redimensionnement. La salade grecque reste à 15 malgré le
redimensionnement — le nettoyage des limites de section déformées par
l'OCR (ex. "Val triti" pour "Valeurs nutritionnelles") reste un
chantier séparé, non résolu ici.

**Limite honnête restant sur la photo de couverture Barramundi** : même
avec le redimensionnement, le nom extrait de cette photo précise reste
parfois un fragment du sous-titre plutôt que le vrai titre — la photo
contient une grande image du plat qui semble perturber l'ordre de
lecture déterminé par Tesseract lui-même, indépendamment de la
résolution. Non résolu dans cette session ; la classification et la
durée détectée restent cependant correctes malgré ce nom imparfait.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement (y compris la mise à jour du mock de
`runOcrOnImage` dans `test_multiphoto.py` pour refléter le nouveau
contrat `{rawText, layoutText}`), tous corrects.

**Version testée** : v171

### 27 — Test physique Samsung : 3 défauts corrigés et testés *(v172)*

**Contexte** : après confirmation du bug principal corrigé (texte brut
protégé), le test physique sur Samsung a montré 3 nouveaux défauts
précis, confirmés indépendamment par un second avis avec ses propres
observations chiffrées.

**Point 1 — classement "Préparation" au lieu d'"Ingrédients" avec des
ustensiles au-dessus, corrigé** : le marqueur de titre exigeait
pratiquement que "Ingrédients" soit en tout début de ligne — avec des
ustensiles précédents, une segmentation différente pouvait empêcher
toute détection. Corrigé avec `matchesIngredientTitle()` : recherche
le mot dans les 15 premiers caractères d'une ligne d'au plus 6 mots
(tolère un petit fragment collé devant par l'OCR, jamais une phrase
entière). **Première tentative trop permissive, corrigée après
régression détectée** : une recherche "n'importe où dans une ligne
courte" attrapait aussi de vraies phrases d'étape mentionnant le mot
"ingrédients" en son sein (ex. "Mélanger les ingrédients pendant
longtemps", cassant `test_multiphoto.py`) — resserré avec la
contrainte de position ET de nombre de mots ci-dessus. **Testé avec le
scénario exact rapporté** (ustensiles + description + "Ingrédients
pour 2 personnes") : correctement classé "ingredients" avec 2
personnes détectées, contenu des ustensiles bien exclu.

**Point 2 — valeurs nutritionnelles transformées en ingrédients,
corrigé** : deux causes précises trouvées et corrigées.
- Le retrait des puces (`*`, `•`, `-`) intervenait APRÈS le filtrage
  par mots-clés parasites, permettant à `* Conserver au réfrigérateur`
  de contourner le rejet (qui exige que la ligne commence exactement
  par le mot-clé, pas par un symbole suivi de lui). Corrigé en
  retirant les puces dès le départ, avant tout filtrage.
- Limites fortes supplémentaires ajoutées ("Par portion", "Pour 100
  g", "Conserver au réfrigérateur", "Énergie"/kJ-kcal) qui arrêtent
  désormais complètement l'extraction, pas seulement un rejet ligne
  par ligne — utile si le vrai titre "Valeurs nutritionnelles" a été
  mal reconnu par l'OCR.
- Tolérance légère ajoutée pour "à ajouter vous-même" collé sans
  espace par l'OCR. Une déformation extrême au niveau des lettres
  (ex. "Aejoutervoustréte", rapportée par un second avis) reste un cas
  limite non résolu — une correction fiable demanderait une
  correspondance floue au niveau des caractères, hors de portée d'une
  simple expression régulière sans risquer de sur-ajustement.

**Testé avec les scénarios exacts et les décomptes précis rapportés
par le second avis** : salade grecque 13 → **12** ingrédients exacts ;
Barramundi 12 → **10** ingrédients exacts, correspondant précisément
aux vraies fiches. "Conserver au réfrigérateur" et "À ajouter
vous-même" n'apparaissent plus dans aucune des deux listes.

**Point 3 — description encombrée de bruit et grille à 3 colonnes,
non traité dans cette session** : confirmé par les deux avis comme le
chantier le plus complexe (nettoyage du bruit + reconstruction
géométrique de la grille), volontairement reporté après stabilisation
complète des deux points précédents, conformément à l'ordre recommandé
par l'audit lui-même.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, y compris une régression détectée et corrigée en
cours de route (voir point 1) avant validation finale.

**Version testée** : v172

### 28 — Régression PNG corrigée, variantes "Étape"/"Préparation" tolérées *(v173)*

**Contexte** : test sur les 8 vraies photos avec la v172 exacte,
révélant une régression critique introduite par le redimensionnement
systématique ajouté en v171, plus deux défauts précis dans la
reconnaissance des titres de préparation sur les captures Marmiton.

**Régression critique — redimensionnement des captures PNG, corrigée** :
confirmée par comparaison directe sur la vraie capture Marmiton
ingrédients (3839×2075) : 775 caractères reconnus après
redimensionnement à 1600px, contre 1758 sans aucun redimensionnement —
plus de la moitié du texte perdu. Une tentative intermédiaire à 2600px
n'a récupéré que partiellement la qualité (1474 caractères). Corrigé
en ne redimensionnant JAMAIS les captures d'écran PNG (détectées via
`file.type` ou l'extension), en ne conservant le redimensionnement à
1600px que pour les photos JPEG classiques (qui en bénéficient,
confirmé lors du travail précédent). **Testé et confirmé** : la
capture PNG retrouve exactement ses 1758 caractères d'origine ; une
photo JPEG continue d'être normalement redimensionnée (1200×1600 pour
une photo 4080×3060).

**"/ Préparation" non reconnu, corrigé** : le slash n'était pas inclus
dans les symboles tolérés avant un titre. Ajouté à
`OCR_LEADING_NOISE`.

**Variantes singulier/numérotées d'"Étape" non reconnues, corrigées** :
seul "Étapes" au pluriel était reconnu — avec "ÉTapE2" ou "étape #320"
(numéro collé sans espace), aucune détection, faisant retenir
uniquement une occurrence beaucoup plus tardive du pluriel exact et
supprimant ainsi toutes les étapes précédentes. Corrigé pour reconnaître
"Étape"/"Étapes" avec un numéro optionnel collé ou séparé (`#`, espace,
ou directement accolé). **Testé avec toutes les variantes exactes
rapportées** ("/ Préparation", "ÉTapE2", "étape #320", "Etape1"...) :
toutes désormais reconnues. **Testé avec un texte reproduisant la
structure Marmiton complète** (bruit de navigateur, 5 étapes numérotées
de façons différentes, commentaire de fin) : les 5 étapes sont
maintenant conservées depuis la première, plus seulement la fin.

**Non traité dans cette session, confirmé comme cas limites plus
complexes** : la déformation extrême de "À ajouter vous-même"
("'Ajoutervous-rréne so"), les fractions transformées en "%", l'unité
"filet", le pluriel OCR incomplet "(s" — chacun nécessiterait une
correspondance floue au niveau des caractères ou un traitement dédié,
hors de portée d'un simple ajustement d'expression régulière sans
risquer de sur-ajustement à un seul exemple. La reconstruction des
préparations en grille à 3 colonnes reste également hors scope,
confirmée comme le chantier séparé le plus complexe.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v173

### 29 — 3 défauts confirmés par le test complet des 8 photos, corrigés *(v174)*

**Contexte** : la correction PNG de la v173 confirmée fonctionner
nettement (préparation Marmiton : 5 lignes finales seulement → 19
lignes, étapes 1 à 5 complètes) sur un nouveau test des 8 vraies
photos. Trois nouveaux défauts précis identifiés et corrigés.

**Point 1 — nombre de personnes perdu si sur une ligne séparée,
corrigé** : l'analyseur "Ingrédients" ne cherchait le nombre de
personnes que sur la ligne du titre lui-même — avec "Ingrédients" et
"2 personnes" sur deux lignes distinctes (capture d'écran), la valeur
était perdue au profit du repli à 4. Corrigé avec une recherche sur
tout le texte en repli si absent du titre. **Testé avec le scénario
exact rapporté** ("| 2 personnes | +" sur sa propre ligne) : 2
personnes correctement détectées.

**Point 2 — lignes parasites d'interface prises pour des ingrédients,
corrigé en deux temps** :
- Le filtre de rejet des lignes "X personnes" exigeait un début de
  ligne exact, sans tolérer les symboles d'interface ("|", "+")
  entourant le nombre — corrigé en élargissant `OCR_LEADING_NOISE`
  (ajout de `|` et `+`) et en appliquant cette tolérance aussi en fin
  de ligne pour ce filtre précis.
- Ajout d'un rejet complet de l'extraction quand très peu de lignes
  (≤3) survivent au filtrage ET qu'aucune n'a de quantité reconnue —
  évite qu'une capture ne montrant que le titre et quelques fragments
  de bruit produise de faux ingrédients, sans risquer de rejeter une
  vraie liste plus longue. **Testé avec le scénario exact rapporté**
  ("Marmiton, haut de page" : titre + bruit seul, aucun vrai
  ingrédient) : liste correctement vidée plutôt que de garder les
  fragments parasites.

**Point 3 — "(A) anonyme" et "Capture d'écran" non reconnus comme fin
de contenu, corrigés** : le préfixe "(A)" (initiale d'avatar de
commentaire) empêchait la reconnaissance du marqueur "anonyme".
Ajoutée une tolérance pour ce préfixe précis. Ajouté aussi "capture
d'écran" comme marqueur de fin, avec tolérance totale de préfixe
(garbling imprévisible du texte de l'outil de capture Windows,
ex. "BB Out Capture d'écran"). **Testé avec les variantes exactes
rapportées** : toutes désormais reconnues.

**Non traité, confirmé comme cas limites plus complexes** : la
déformation extrême de "À ajouter vous-même", les fractions en "%",
l'unité "filet", le pluriel OCR incomplet "(s", les 12 lignes
incohérentes de la capture Marmiton ingrédients illustrés, et la
reconstruction en grille à 3 colonnes pour les préparations HelloFresh
et Barramundi — tous confirmés comme nécessitant un traitement dédié
plutôt qu'un ajustement ponctuel supplémentaire, qui risquerait un
sur-ajustement à des exemples isolés sans traiter la cause structurelle.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v174

### 30 — Capture Marmiton en grille d'icônes : liste incohérente rejetée *(v175)*

**Contexte** : la v174 confirmée corriger ses 3 points ciblés (personnes
sur ligne séparée, faux ingrédients sur capture vide, fin de
préparation Marmiton), mais un nouveau défaut identifié sur la capture
"Marmiton, ingrédients illustrés" (présentation en grille d'icônes,
chaque case scindée entre une ligne de quantités et une ligne de noms
mélangés) : 2 lignes de bruit contenant accidentellement des chiffres
contournaient la protection existante, laissant passer 12 lignes
incohérentes.

**Vérifié avec une nouvelle exécution OCR réelle sur la vraie
capture** avant toute correction, confirmant le texte brut exact et le
mécanisme précis de la fuite.

**Corrections apportées, par ordre d'impact** :
- Ajout du symbole `@` aux symboles tolérés avant un titre — "@
  Ustensiles" n'était pas reconnu comme limite de section, laissant
  passer tout le bruit qui suit (bouton "Capture d'écran", "Voir
  plus", "Balisage et partage"). **Ce seul correctif a réduit les 12
  lignes à 8.**
- Rejet de la mention légale récurrente sur Marmiton ("En cliquant sur
  les liens...", "d'autres pages de notre site" — apostrophe rendue
  optionnelle, l'OCR l'ayant parfois entièrement supprimée).
- **Règle de rejet élargie** : si moins de 40 % des lignes survivantes
  ont une vraie quantité reconnue (et qu'il y en a un nombre
  raisonnable, 4 à 10), la liste entière est rejetée plutôt que de
  conserver des fragments de grille mal reconstruite — une vraie liste
  HelloFresh/Marmiton classique ayant presque toujours une nette
  majorité de lignes avec quantité, ce seuil ne la pénalise pas.

**Testé avec le vrai texte OCR de la capture** : la liste est
désormais entièrement vide plutôt que de contenir 12 fragments
incohérents. **Confirmé que les vraies listes salade grecque (12) et
Barramundi (10) restent intactes**, la grande majorité de leurs lignes
ayant une quantité réelle (bien au-dessus du seuil de 40 %).

**Point cosmétique connu, non corrigé** : comme relevé par l'audit, la
photo reste étiquetée "Ingrédients" même quand la liste finale est
vide (plutôt que "Autre"), car la classification automatique
(`detectPhotoSection`, via `parseOcrRecipeText`) utilise encore sa
propre extraction plus ancienne, distincte de celle utilisée pour
l'affichage final (`extractIngredientsFromLines`, qui bénéficie des
nouvelles règles de rejet). Sans danger pour les données (liste
réellement vide, pas de faux ingrédients enregistrés), mais un choix
manuel serait plus cohérent. Non corrigé par prudence : unifier les
deux chemins d'extraction risquerait d'affecter aussi la
classification des photos "mixed" (recette complète sur une seule
photo), un chantier plus risqué que la valeur de ce simple ajustement
cosmétique.

**Non traité, confirmé comme cas limites plus complexes** :
"À ajouter vous-même" trop déformé, fractions en "%", "1 sachet(s"
incomplet, "Beurre 1 cs"→"ac", "Lait 1 filet", grille à 3 colonnes des
préparations HelloFresh, page complète de salade trop chargée.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v175

### 31 — 6 corrections précises confirmées par vérification indépendante *(v176)*

**Contexte** : la v175 confirmée fonctionner pour la salade grecque
(12), mais Barramundi restait à 11 et la capture Marmiton illustrée
produisait encore 12 lignes incohérentes malgré la correction
précédente. Une nouvelle exécution OCR réelle a révélé la cause
précise : le glyphe reconnu par Tesseract pour ce symbole varie d'une
exécution à l'autre ("@" dans mon propre test, "©" dans celui de
l'audit) — confirmant une variabilité réelle de l'OCR sur ce glyphe
ambigu, pas une erreur de l'un ou l'autre test.

**Point 1 — "©"/"®" non tolérés, corrigé** : ajoutés à
`OCR_LEADING_NOISE`, en plus de "@" déjà présent — couvre maintenant
les deux variantes possibles produites par Tesseract sur ce glyphe.

**Point 2 — "Ustensites" (l/t confondu) non reconnu, corrigé** :
`ustensiles?` remplacé par `ustensi[lt]es?`, reconnaissant les deux
graphies.

**Point 3 — seuil de qualité contourné au-delà de 10 lignes, corrigé** :
la limite supérieure arbitraire de 10 permettait à une liste de 12
lignes de contourner entièrement la vérification des 40 %. Retirée —
seule la limite inférieure (≥4) subsiste, pour ne pas interférer avec
la règle séparée déjà en place pour les listes plus courtes.
**Confirmé que les vraies listes salade (12) et Barramundi (10)
restent intactes** après ce retrait, leur proportion de lignes
quantifiées restant largement au-dessus du seuil.

**Point 4 — ligne "N personnes" non retirée avec caractères parasites
en fin, corrigé** : l'exigence de correspondance exacte sur toute la
ligne échouait dès qu'un fragment résiduel apparaissait après (ex.
"| 2 personnes | + es"). Corrigé pour rejeter dès que le motif "N
personnes" apparaît près du début de la ligne, quels que soient les
caractères qui suivent.

**Point 5 — texte OCR réel ajouté comme test permanent** : le texte
exact reconstitué d'après les lignes rapportées (variante "©"/
"Ustensites"/"es" parasite) conservé comme test dédié, distinct de la
variante "@"/"Ustensiles" testée précédemment — couvre maintenant les
deux variantes possibles de cette même capture.

**Point 6 — séparateur "À ajouter vous-même" sévèrement déformé sur
Barramundi, corrigé** : la correspondance de phrase complète échouait
sur la déformation extrême rapportée ("'Ajoutervous-rréne so").
Corrigé avec une détection ciblée et plus permissive : le mot-racine
"ajouter" apparaissant n'importe où dans une ligne courte (≤30
caractères) suffit désormais à la rejeter, ce mot n'apparaissant
normalement jamais dans un vrai nom d'ingrédient.

**Tous les 6 points testés avec les formes exactes rapportées par
l'audit** (nouvelle exécution OCR réelle sur la capture, plus
scénarios reconstitués fidèlement pour Barramundi) : la capture
Marmiton illustrée est maintenant rejetée à liste vide dans les deux
variantes de glyphe possibles ; Barramundi confirmé à exactement 10
ingrédients ; salade grecque toujours à 12.

**Non traité, confirmé comme cas limites plus complexes** : fractions
en "%", "1 sachet(s" incomplet, "Beurre 1 cs"→"ac", grille à 3
colonnes des préparations, page complète de salade trop chargée.

**Non-régression** : toute la suite de tests existante (26 tests)
relancée après chaque changement, aucune régression.

**Version testée** : v176

### 32 — 2 risques de faux rejet identifiés et corrigés *(v177)*

**Contexte** : la v176 confirmée reproduire les 3 résultats annoncés
(Marmiton 0, Barramundi 10, salade 12) par une vérification
indépendante avec une nouvelle exécution OCR réelle. Deux risques de
faux rejet identifiés dans les protections ajoutées, tous deux
vérifiés puis corrigés avant de les considérer acceptables.

**Risque 1 — filtre "ajouter" trop large, confirmé et corrigé** :
`/ajouter/i` seul rejetait à tort de vrais ingrédients contenant ce mot
en fin de ligne ("Eau à ajouter", "Sucre à ajouter", "2 c. à soupe
d'eau à ajouter"). **Testé et confirmé exactement comme rapporté**
avant correction. Corrigé en ciblant la vraie signature du séparateur
déformé : "ajouter" suivi de près par "vous" (`/ajouter\s{0,3}vous/i`)
plutôt que le mot seul — un vrai ingrédient contenant "ajouter" ne
l'a jamais suivi de "vous". **Retesté après correction** : les 3
ingrédients légitimes désormais acceptés, le séparateur déformé
toujours rejeté.

**Risque 2 — règle des 40 % pouvant vider une vraie liste sans
quantités, confirmé et la règle retirée entièrement** : vérifié avec
le scénario exact rapporté ("Sel selon votre goût, Poivre, Herbes
fraîches, Huile selon besoin", 0 % de lignes quantifiées) — la liste
était effectivement entièrement vidée à tort. **Analyse plus poussée
révélant un problème plus profond** : cette liste légitime (0 % de
quantité) a en réalité un taux PLUS BAS que la grille Marmiton
réellement incohérente (~29 % dans le cas réel constaté), rendant ce
critère par nature incapable de les distinguer de façon fiable, quel
que soit le seuil choisi. La règle des 40 % a donc été retirée
entièrement plutôt qu'ajustée. **Remplacée par un critère plus sûr et
ciblé** : rejet d'une ligne contenant la préposition isolée "de"/"d'"
à deux reprises ou plus — signe fort de plusieurs noms d'ingrédients
fusionnés sur une seule ligne (grille scindée), qu'un vrai nom
d'ingrédient ne présente presque jamais. **Testé soigneusement contre
7 cas** (vrais ingrédients avec apostrophe comme "Gousse d'ail" ou
"Huile d'olive", contre les fragments fusionnés réels de la capture
Marmiton) : tous corrects. **Retesté la liste légitime** : désormais
bien conservée (4 ingrédients, pas vide).

**Compromis assumé et documenté honnêtement** : ce nouveau critère,
plus sûr, ne parvient plus à vider entièrement la capture Marmiton
illustrée (4 fragments incohérents restent, contre 0 avec l'ancienne
règle des 40 % retirée) — un recul partiel sur ce cas précis, mais
délibéré : préférable à risquer de vider silencieusement une vraie
recette dans d'autres cas, conformément à la recommandation de
l'audit. Cette capture reste un cas connu difficile, pas encore
totalement résolu.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression (une unique exécution isolée de
`test_resolve_paren` a affiché un échec ponctuel dû à un problème de
délai du serveur de test déjà rencontré précédemment dans ce projet —
confirmé non reproductible en relançant ce test seul).

**Version testée** : v177

### 33 — Risque "de/d'" trop agressif, confirmé et corrigé *(v178)*

**Contexte** : la v177 confirmée fonctionner correctement pour le
filtre "ajouter vous" et le retrait de la règle des 40 %. Un troisième
risque identifié dans la règle "de/d'" ajoutée en v177 pour remplacer
celle des 40 %.

**Vérifié exactement comme rapporté** : `looksLikeIngredientLine`
rejetait bien à tort "Filet de poulet et crème de coco", "Jus de
citron et huile d'olive" et "2 c. à soupe de crème de noix de coco" —
trois vrais ingrédients légitimes contenant deux occurrences ou plus
de cette préposition.

**Corrigé en combinant avec l'absence de quantité, comme recommandé** :
la règle "de/d'" a été retirée de `looksLikeIngredientLine` (qui
l'appliquait seule, avant même de connaître la quantité) et déplacée
après l'analyse complète de la ligne (`parseIngredientString`), où
elle n'est désormais appliquée que si AUCUNE quantité n'a été
reconnue pour cette ligne — un vrai ingrédient portant une quantité
n'est ainsi plus jamais pénalisé par sa préposition, quel que soit son
nombre d'occurrences.

**Testé à deux niveaux** :
- Appel direct à `looksLikeIngredientLine` (comme dans le rapport) :
  les 5 exemples (dont les 3 précédemment rejetés à tort) sont
  désormais tous acceptés.
- Pipeline complet (`extractIngredientsFromLines`) avec des lignes
  réalistes portant une quantité ("200g Filet de poulet et crème de
  coco", "2 c. à soupe de crème de noix de coco"...) : les 5 lignes
  correctement conservées, confirmant que la correction protège aussi
  bien l'appel isolé que l'usage réel en contexte de recette.

**Compromis toujours assumé sur la capture Marmiton illustrée** :
cette version plus prudente de la règle ne parvient toujours pas à
vider entièrement cette capture précise (4 fragments incohérents
restent, inchangé depuis la v177) — accepté comme limite connue, la
sécurité des vraies recettes primant sur ce cas isolé difficile,
conformément aux deux audits successifs sur ce point.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v178

### 34 — Retrait complet des règles de rejet textuelles risquées *(v179)*

**Contexte** : après trois rounds successifs de correctifs sur les
règles de rejet des ingrédients (règle des 40 %, puis "de/d'" combinée
à l'absence de quantité), une nouvelle vérification indépendante a
confirmé que le risque de suppression de vrais ingrédients n'était
**toujours pas résolu** : dès que l'OCR ne reconnaît simplement pas la
quantité d'un ingrédient (un cas courant, pas une exception), les deux
règles combinées continuaient de vider des listes parfaitement
légitimes.

**Vérifié exactement comme rapporté** avant toute correction :
- 4 ingrédients légitimes sans quantité reconnue ("Filet de poulet et
  crème de coco", "Jus de citron et huile d'olive", "Crème de noix de
  coco", "Sel") : **0 conservé** — liste entièrement vidée.
- 3 ingrédients courts légitimes sans quantité ("Sel", "Poivre",
  "Herbes fraîches") : **0 conservé** — même problème via l'autre
  règle.

**Décision** : suivant la recommandation explicite de l'audit, les
deux règles ont été retirées **entièrement** plutôt que d'être encore
ajustées — après trois tentatives successives de les rendre plus
sûres sans y parvenir complètement, la conclusion est qu'une
distinction fiable entre une liste légitime sans quantités lisibles et
une grille d'icônes mal reconstruite demanderait de vraies coordonnées
géométriques (plusieurs colonnes détectées), pas une heuristique
reposant sur le texte final. **La sécurité des vraies recettes de
l'utilisateur prime sur la détection du cas Marmiton précis.**

**Testé après retrait** : les deux scénarios exacts rapportés
retrouvent bien leurs ingrédients (4/4 et 3/3 conservés). Salade
grecque et Barramundi confirmés toujours à 12 et 10 respectivement
(inchangés). Trois scripts de test existants, dont le but vérifiait
précisément les règles désormais retirées, mis à jour pour refléter
ce nouveau comportement intentionnel plutôt que supprimés.

**Conséquence assumée** : la capture Marmiton en grille d'icônes ne
sera désormais plus vidée automatiquement — quelques fragments
incohérents pourront à nouveau y apparaître, comme avant la v175. Ce
recul est délibéré : la relecture manuelle avant enregistrement (déjà
systématiquement proposée pour tout import photo) reste le filet de
sécurité approprié pour ce cas difficile, plutôt qu'une suppression
automatique côté analyseur qui s'est révélée, à trois reprises
consécutives, incapable de cibler ce cas sans risquer d'en toucher
d'autres.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression sur les protections qui
restent en place (limite de section tolérante à `@`/`©`/`®` et
"Ustensites", rejet des mentions légales Marmiton, rejet du séparateur
"À ajouter vous-même" même déformé, nombre de personnes sur ligne
séparée).

**Version testée** : v179

### 35 — Corpus OCR permanent créé *(v180)*

**Contexte** : suite à une recherche sur les alternatives OCR/analyse
de recettes (aucun modèle spécialisé mûr trouvé, mais confirmation que
le vrai gain vient de la structure — segmentation, ordre des colonnes,
score plutôt que rejet binaire), premier chantier engagé dans l'ordre
convenu : **le corpus de test permanent**, préalable aux chantiers
suivants (score de confiance, reconstruction géométrique des
colonnes).

**Ce qui a été créé** (`tests/`) :
- `ocr-corpus/*.json` — 5 cas construits à partir de **vraies sorties
  OCR sauvegardées** lors des sessions de vérification précédentes
  (jamais un texte inventé) : salade grecque ingrédients, couverture
  Barramundi, ingrédients Barramundi, préparation Barramundi (grille 3
  colonnes), captures Marmiton ingrédients illustrées. Chaque fichier
  contient le texte brut réel, le texte reconstruit, et les résultats
  actuellement attendus avec leurs limites documentées en note (ex.
  "séparateur déformé non filtré depuis la v179, priorité à la
  sécurité des données").
- `run_ocr_corpus.py` — script exécutant tout le corpus contre le vrai
  code de `app.js` (`parseOcrRecipeText`, `detectPhotoSection`,
  `deriveSectionDataForPhoto`), rapportant un résumé pass/fail avec
  code de sortie utilisable en vérification automatisée.
- `README.md` — documente l'usage et la procédure pour ajouter un
  nouveau cas au corpus.

**Un cas particulier rafraîchi avant intégration** : la capture
Marmiton ingrédients illustrées avait été sauvegardée très tôt dans le
projet, avant la correction du redimensionnement systématique des PNG
(v173) — son texte OCR sauvegardé était donc celui de l'ancien
comportement (775 caractères), pas représentatif du code actuel.
Régénéré avec une vraie exécution OCR fraîche sur l'image source
(1758 caractères, cohérent avec les résultats v173+ déjà validés)
avant de l'intégrer au corpus.

**Validé comme outil de détection réel, pas seulement décoratif** :
un bug connu (désactivation temporaire du repli "personnes sur ligne
séparée") introduit délibérément dans une copie de travail, confirmé
détecté par le corpus (échec sur le cas Marmiton concerné, les autres
cas non affectés restant corrects) avant d'être annulé.

**Non-régression** : toute la suite de tests existante relancée en
parallèle du nouveau corpus, aucune régression.

**Prochaines étapes convenues, dans cet ordre** : système de score de
confiance (ligne "sûre" vs "à vérifier" plutôt que rejet binaire),
puis reconstruction géométrique des colonnes pour les préparations en
grille, puis comparaison avec une bibliothèque d'analyse de quantités
plus mature avant de remplacer `parseIngredientString`.

**Version testée** : v180

### 36 — Fuite de données personnelles corrigée, corpus renforcé *(v181)*

**Contexte** : audit confirmant un incident sérieux — le fichier corpus
Marmiton (v180) contenait le texte OCR réel d'une capture d'écran de
navigateur, incluant les onglets ouverts, le contenu de la barre de
favoris, et le nom d'utilisateur GitHub de l'utilisateur, visibles
dans un dépôt destiné à être public. L'utilisateur a immédiatement
rendu son dépôt privé pendant le traitement de ce problème.

**Priorité 1 — fuite de données, corrigée** : le fichier concerné
déplacé vers un nouveau dossier `tests/private-ocr-corpus/`, ajouté au
`.gitignore` créé à cet effet. Remplacé dans le corpus public par une
version **synthétique** — mêmes propriétés de bruit OCR (onglets et
favoris garblés de façon similaire), mais noms entièrement fictifs.
**Vérifié avant remplacement** que la version synthétique produit
exactement les mêmes résultats de test que l'original (section,
personnes, nombre de fragments identiques) pour ne perdre aucune
valeur de test. Les 4 autres fichiers du corpus vérifiés : provenant
tous de photos de fiches recette (pas de captures de navigateur), ne
contiennent aucune information personnelle.

**Priorité 2 — incohérence de version, reconfirmée cohérente** :
`APP_VERSION` et `CACHE_NAME` vérifiés synchronisés à 180 dans la copie
de travail locale au moment de l'audit ; la cause exacte de l'écart
constaté sur GitHub n'a pas pu être déterminée avec certitude, mais la
version est de nouveau incrémentée (181) pour cette livraison, afin de
ne laisser aucune ambiguïté sur l'état livré.

**Priorité 3 — corpus renforcé au-delà des simples comptages** :
ajout d'assertions `keyIngredients` (nom contenant une sous-chaîne,
avec quantité et unité exactes, vérifié indépendamment de l'ordre) sur
les cas salade grecque et Barramundi, et `descriptionContainsAll` (mots-clés
attendus dans le texte de préparation) sur le cas Barramundi
préparation. **Testé que ces nouvelles assertions détectent bien une
régression invisible à l'ancien comptage seul** : une régression
simulée (quantité de "Grenailles" forcée à `null`) laissait le nombre
total d'ingrédients inchangé (12) mais était correctement détectée en
échec par la nouvelle vérification `keyIngredients`, avant confirmation
que la restauration du code redonnait un résultat entièrement correct.

**Découverte notable en construisant les assertions exactes** :
une tentative de valider position par position toute la liste
d'ingrédients de Barramundi a révélé qu'un ordre interne des mots dans
un nom pouvait varier de façon stable et reproductible selon les
circonstances exactes de reconstruction, sans refléter une vraie
régression de contenu — confirmé en relançant le même test trois fois
de suite sur des données figées (résultat identique à chaque fois,
donc un artefact déterministe de cette exécution précise, pas un
problème d'instabilité). D'où le choix d'assertions par présence
(indépendantes de l'ordre) plutôt que d'égalité stricte de toute la
liste.

**Priorité 4 — reproductibilité en une seule commande** : script
réécrit pour démarrer et arrêter lui-même un serveur local temporaire
(port libre choisi automatiquement) plutôt que d'exiger une étape
manuelle préalable. `tests/requirements.txt` ajouté avec la version
exacte de Playwright installée et vérifiée dans l'environnement.
**Testé sans aucun serveur préexistant** : la commande unique
`python3 tests/run_ocr_corpus.py` fonctionne de bout en bout.

**Non traité dans cette session** : le remplacement complet de
`ingredientCount`/`ingredientCountMax` par des attentes exactes sur
*tous* les cas (fait seulement sur les 2 cas où c'était le plus
significatif) ; le système de score de confiance ligne par ligne
(prochain chantier convenu, non commencé).

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v181

### 37 — Système de score de confiance par ingrédient *(v182)*

**Contexte** : chantier convenu suite à la recherche sur les
alternatives OCR/analyse de recettes — remplacer le principe des rejets
binaires (accepté ou supprimé), qui a fait perdre plusieurs manches
successives sur de faux rejets d'ingrédients légitimes (points 30 à 34
de ce document), par un système de score conservant toujours la ligne
mais la signalant "à vérifier" quand la confiance est faible.

**Conception** : `scoreIngredientConfidence()` calcule un score à
partir de plusieurs signaux déjà utilisés ailleurs dans l'analyseur
(quantité reconnue, longueur moyenne des mots, répétition de la
préposition "de"/"d'", longueur du nom) — mais comme composantes d'un
score cumulé plutôt que comme motifs de rejet individuels et
définitifs. **Calibrée et testée contre 9 cas connus avant intégration**
(ingrédients légitimes complexes ayant fait l'objet de faux rejets
lors des sessions précédentes — "Filet de poulet et crème de coco",
"Herbes fraîches" — et fragments réels de la grille Marmiton — "Nes Q
L 3)", "de beurre de sucre semoule de farine") : les 9 cas
correctement classés dès la première calibration.

**Intégration** : le score est attaché à chaque ingrédient
(`confidence: "reliable" | "uncertain"`) dans les deux chemins
d'extraction existants (`extractIngredientsFromLines` pour les photos
"Ingrédients" seules, `parseOcrRecipeText` pour les photos "recette
complète"). **Vérifié que le champ survit à la fusion multi-photos**
(`mergeMultiPhotoResults`, qui divise les quantités par le nombre de
personnes) grâce à l'opérateur de décomposition déjà utilisé, sans
modification nécessaire à cette fonction.

**Interface** : un badge ⚠️ discret (fond ambre, jamais rouge —
signal d'attention, pas d'alarme) apparaît sur la ligne du formulaire
pour tout ingrédient "uncertain", avec une infobulle expliquant la
raison. **Jamais de suppression automatique** : la ligne reste
toujours modifiable normalement, le badge n'étant qu'une indication
visuelle pour orienter la relecture déjà systématiquement proposée
avant enregistrement. **Testé le rendu réel** : le badge apparaît
exactement sur la bonne ligne, aucune fausse position constatée.

**Corpus enrichi en conséquence** : `run_ocr_corpus.py` vérifie
désormais aussi le champ `confidence` des ingrédients-clés attendus.
Ingrédients fiables de la salade grecque et du Barramundi confirmés
`reliable`. **Sur la capture Marmiton en grille** : confirmé que le
score signale correctement 4 des 6 fragments comme "à vérifier" — une
amélioration réelle documentée honnêtement comme imparfaite (2
fragments passent encore comme "reliable" à tort, l'un ayant
accidentellement une quantité extraite d'une cellule de grille
voisine) plutôt que présentée comme une résolution complète du cas.

**Non-régression** : toute la suite de tests existante et le corpus
complet relancés après chaque changement, aucune régression.

**Prochaine étape convenue, non commencée** : la reconstruction
géométrique des colonnes pour les préparations en grille à 3 colonnes
(HelloFresh, Barramundi), puis la comparaison avec une bibliothèque
d'analyse de quantités plus mature.

**Version testée** : v182

### 38 — Reconstruction géométrique des colonnes en grille *(v183)*

**Contexte** : chantier convenu après le système de score de confiance
— le morceau le plus conséquent restant, confirmé par plusieurs audits
et par la recherche externe comme nécessitant une vraie reconstruction
de mise en page, pas un simple ajustement de filtre textuel.

**Analyse géométrique préalable, sur les vraies coordonnées** : examen
direct des blocs/lignes/mots produits par Tesseract sur la vraie photo
Barramundi préparation. Découverte que Tesseract fusionne déjà les 3
colonnes HelloFresh en une seule "ligne" de lecture au niveau bloc et
ligne (un seul bloc, un seul paragraphe, des lignes s'étendant sur
la quasi-totalité de la largeur de l'image). Découverte plus
préoccupante en examinant le niveau mot : certaines coordonnées de
mots se chevauchent horizontalement de façon incohérente avec un ordre
de lecture simple, signe d'une imprécision de Tesseract lui-même sur
cette photo précise (probablement liée à un léger flou ou une légère
rotation) — une limite de la source que la reconstruction en aval ne
peut pas réparer, quelle que soit sa sophistication.

**Solution conçue et validée avant intégration** : reconstruction à 2
niveaux plutôt qu'une simple coupure par ligne :
1. **Séparation par rangée** : détection des grands sauts verticaux
   entre groupes de mots (typiquement les photos illustrant chaque
   étape, créant un vide d'environ 90 à 190 px sur la vraie photo) ;
2. **Séparation par colonne au sein de chaque rangée** : tiers fixes
   de la largeur de l'image, correspondant à la mise en page HelloFresh
   connue (3 colonnes égales) ;
3. Dans chaque cellule rangée × colonne, regroupement des mots en
   lignes par proximité verticale, puis tri horizontal.

**Testé directement contre les vraies coordonnées avant toute
intégration au code** : les 6 étapes obtenues correspondent exactement
à la vraie fiche (rangée 1/colonne 1 = "Veillez à bien respecter...",
rangée 1/colonne 2 = "Épluchez les pommes de terre...", rangée
2/colonne 1 = "Répartissez les tomates cerises...", etc.) — contre un
seul bloc de texte mélangeant indistinctement les 3 colonnes
auparavant.

**Détection déclenchant la reconstruction, calibrée avec prudence après
un faux positif repéré** : une première tentative basée sur la largeur
des lignes déclenchait à tort sur la vraie capture Marmiton (simple
liste à une colonne, aucune grille). Remplacée par un signal plus
spécifique — le chevauchement de mots au sein d'une même ligne
reconnue par Tesseract — **vérifié à 0 % sur la vraie capture Marmiton
contre 39 % sur la vraie photo Barramundi en grille**, une séparation
nette. Revérifié aussi sur les 3 autres photos déjà validées
(couverture Barramundi, ingrédients salade et Barramundi) : aucun
faux positif.

**Intégration au pipeline réel** : `runOcrOnImage()` calcule
désormais une troisième variante de texte, `gridText`, uniquement
quand la détection déclenche. `deriveSectionDataForPhoto()` l'utilise
pour la section "preparation" quand disponible et substantielle (plus
de 200 caractères), avec repli sûr sur le comportement précédent
(texte brut, découpage simple par titre) sinon — **vérifié que
Marmiton reste inchangé** après cette intégration (les 5 étapes
toujours correctement extraites depuis la première).

**Limite honnête documentée** : l'ordre exact des mots *au sein* de
chaque étape reste imparfait sur cette photo précise, à cause de
l'imprécision des coordonnées de mots produites par Tesseract lui-même
(pas un défaut de la reconstruction) — mais la séparation des 6 étapes
individuelles, qui était le vrai problème bloquant depuis le début de
ce chantier, fonctionne correctement. Une photo mieux cadrée/moins
floue produirait vraisemblablement un résultat plus propre à l'intérieur
de chaque étape, cette limite étant spécifique à la qualité de la
photo source testée, pas structurelle à l'approche.

**Corpus enrichi** : `gridText` pré-calculé ajouté au cas Barramundi
préparation existant, avec de nouvelles vérifications
`descriptionContainsAll` confirmant la présence des 4 phrases-clés
attendues (une par étape déterminante) dans le texte reconstruit.
`run_ocr_corpus.py` mis à jour pour propager ce troisième champ,
optionnel, aux cas qui en disposent.

**Non-régression** : toute la suite de tests existante et le corpus
complet relancés après chaque changement, aucune régression.

**Prochaine étape convenue, non commencée** : comparaison avec une
bibliothèque d'analyse de quantités plus mature
(`parse-ingredient` de jakeboone02) avant d'envisager de remplacer
`parseIngredientString`.

**Version testée** : v183

### 39 — Signalement des fractions Unicode mal reconnues par l'OCR *(v184)*

**Contexte** : chantier ciblé convenu après la comparaison avec
`parse-ingredient` (jakeboone02) — comparer sa gestion des fractions à
la nôtre.

**Découverte importante ayant réorienté le chantier** : en vérifiant
précisément le comportement actuel sur les vrais cas du corpus
("Echalote % piece(s)", "Origan séché % sachet"), confirmé que le vrai
problème n'était **pas** une lacune de notre analyseur de texte (une
fonction `normalizeUnicodeFractions` existait déjà et gère bien les
vrais caractères ½/⅔ quand ils sont présents), mais que **Tesseract lui
-même lit le symbole "%" à la place du vrai caractère de fraction**,
avant même que notre code ne voie le texte. Emprunter la logique de
fractions de `parse-ingredient`/`numeric-quantity` n'aurait donc rien
changé : ces bibliothèques attendent aussi un vrai caractère de
fraction en entrée, pas un "%" déjà corrompu par l'OCR.

**Chantier réajusté en conséquence** : plutôt que d'essayer de deviner
la valeur exacte de la fraction perdue (risqué — aucun moyen fiable de
distinguer ½, ⅓ ou ⅔ à partir d'un simple "%"), détection du motif
précis ("%" isolé, sans chiffre juste avant, suivi d'un mot) comme
signature d'une fraction probablement mal reconnue, puis **connexion
avec le système de score de confiance déjà en place** (chantier
précédent) : la ligne est marquée "à vérifier" plutôt que silencieusement
acceptée avec une quantité vide sans aucun indice.

**Implémenté proprement, sans dupliquer la détection** : la fonction
`parseIngredientString` d'origine renommée en fonction interne
(`parseIngredientStringInner`), enveloppée dans une nouvelle
`parseIngredientString` qui calcule le signal une seule fois et
l'attache au résultat final (`likelyMisreadFraction: true`) —
`scoreIngredientConfidence` le vérifie en tout premier, avant même de
calculer le reste du score.

**Testé avec précision contre les faux positifs** : un vrai pourcentage
authentique dans un contexte de recette ("200 g crème fraîche 20% MG",
"1 pot crème fraîche à 30%", "Lait demi-écrémé 1,5%") n'est jamais
signalé à tort — le motif exige que le "%" soit isolé, sans chiffre
immédiatement devant, ce qu'un vrai pourcentage a toujours.

**Testé sur les vrais cas du corpus** : "Echalote % piece(s)" et
"Origan séché % sachet" (fiche salade grecque réelle) tous deux
correctement marqués "uncertain" avec le signal attaché. Corpus mis à
jour avec ces deux vérifications permanentes.

**Correction apportée en cours de route sur une confusion de la session
précédente** : clarifié que `parse-ingredient` (jakeboone02, sans "s")
n'est **pas** nativement multilingue contrairement à ce qui avait été
avancé — son "support" français/allemand/espagnol se limite à des
options de configuration manuelle (séparateurs de plage, préfixes à
retirer), sans reconnaissance native des unités françaises. Le vrai
paquet avec support français intégré (`parse-ingredients` de magrinj,
avec un "s") est un projet différent et plus petit.

**Non-régression** : toute la suite de tests existante et le corpus
complet relancés après chaque changement, aucune régression.

**Version testée** : v184

### 40 — Abréviations de cuillères, pourcentages non confondus avec une quantité, incohérence de version *(v185)*

**Contexte** : la v184 confirmée fonctionner sur ses nouveautés
principales (fractions, corpus, grille), mais 3 défauts trouvés par
vérification indépendante.

**Point 1 — incohérence de version `sw.js` v183 / `app.js` v184,
investiguée** : la copie de travail locale montrait déjà les deux
fichiers correctement synchronisés à v184 au moment de la
vérification, et le contenu du zip livré (vérifié directement via
`unzip -p` après l'incident) montrait également v184 des deux côtés —
la cause exacte de l'écart constaté par l'utilisateur n'a pas pu être
déterminée avec certitude (possible aléa du système de fichiers en
réseau utilisé pour la livraison, qui avait déjà produit une erreur
d'E/S lors de cette même opération). Version de nouveau incrémentée
(185) et livraison entièrement reconstruite avec des vérifications
supplémentaires (comparaison directe du nombre de fichiers
source/livraison, contenu du zip vérifié par extraction directe) pour
ne laisser aucune ambiguïté.

**Point 2 — abréviations "c. à soupe"/"c à café" non reconnues,
corrigé** : seule la forme complète "cuillère(s) à..." était reconnue.
`spoonMatch` étendu pour accepter aussi "c."/"c" comme abréviation.
**Testé avec le cas exact rapporté** ("2 c. à soupe de crème de noix
de coco") et 5 autres variantes (formes abrégées et complètes,
café/soupe, avec/sans point) : toutes correctement reconnues
désormais, sans régression sur les formes déjà fonctionnelles.

**Point 3 — un nombre suivi de "%" pouvait être pris pour une quantité
d'ingrédient, corrigé** : "20% MG crème fraîche" extrayait à tort 20
comme quantité. Un nombre immédiatement suivi de "%" (avec ou sans
espace) n'est désormais jamais traité comme une quantité d'ingrédient
— c'est un descripteur de pourcentage (matière grasse, alcool...), pas
un compte d'unités, même en tête de ligne. **Testé avec 4 variantes**
(pourcentage en tête, en fin, avec une vraie quantité+unité présente
par ailleurs, décimale avec virgule) : toutes correctes. **Test
permanent prévu pour surveiller ce cas à l'avenir — voir le point 41
ci-dessous, où ce test a été effectivement créé sous le nom
`test_ingredient_parsing.py` après un premier oubli.

**Non-régression** : toute la suite de tests existante et le corpus
complet relancés après chaque changement, aucune régression.

**Version testée** : v185

### 41 — Correction d'une promesse non tenue : vrai fichier de test permanent ajouté *(v186)*

**Contexte** : la v185 mentionnait dans ce document l'ajout d'un test
permanent `test_percent_not_quantity.py`, mais ce fichier n'existait en
réalité que dans l'espace de travail temporaire — jamais réellement
livré ni versionné dans `tests/`. Repéré par vérification indépendante
sur le dépôt public.

**Corrigé** : un vrai fichier permanent créé,
`tests/test_ingredient_parsing.py` — autonome comme
`run_ocr_corpus.py` (démarre et arrête lui-même un serveur local),
couvrant :
- les 4 cas de pourcentages non confondus avec une quantité (point 40) ;
- les 6 cas d'abréviations de cuillères, demandées en complément par
  le même retour (point 40) ;
- 3 cas de détection des fractions mal reconnues par l'OCR (point 39),
  ajoutés pour la même raison — cette vérification n'était protégée
  que par le corpus OCR jusqu'ici, pas par un test ciblé sur la
  fonction elle-même.

**Exécuté et confirmé** : les 13 cas passent
(`python3 tests/test_ingredient_parsing.py`).

**README des tests mis à jour** pour documenter ce nouveau fichier.

**Non-régression** : toute la suite de tests existante et le corpus
complet relancés après ce changement, aucune régression.

**Version testée** : v186

### 42 — 3 corrections issues du premier test réel avec PDF Samsung *(v187)*

**Contexte** : premier test utilisant le **vrai PDF produit par
l'application sur le Samsung** (pas une simulation), pour la recette
Barramundi complète (couverture + ingrédients + préparation). Confirme
que les corrections précédentes (abréviations de cuillères, v186)
fonctionnent bien en conditions réelles — "Beurre : 1 cuillère à
soupe" correctement reconnu sur l'appareil. Trois nouveaux défauts
identifiés et corrigés.

**Point 1 — catégorie "Petit-déjeuner" par défaut, corrigé** : cause
trouvée — `CATEGORY_OPTIONS` liste "Petit-déjeuner" en premier, et le
formulaire ne définissait jamais explicitement de catégorie par défaut
pour une nouvelle recette importée par photo (`mergeMultiPhotoResults`
ne renvoie aucun champ catégorie), laissant le navigateur choisir
silencieusement le premier élément de la liste. Corrigé avec un repli
explicite sur "Plat". **Testé** : import photo → "Plat" ; modification
d'une recette existante avec sa propre catégorie → toujours respectée,
aucune régression.

**Point 2 — titre tronqué sur les couvertures à deux lignes, corrigé** :
"Barramundi en croûte persillée" au lieu du titre complet avec
sous-titre. La ligne suivant le titre est désormais fusionnée si elle
ressemble à un sous-titre (courte, ne correspond à aucun marqueur de
temps/personnes/section). **Testé avec le texte réel de la couverture**
(titre complet récupéré) et 4 cas de non-régression (titre simple,
titre suivi directement d'ingrédients/personnes/préparation) : tous
corrects. Corpus mis à jour en conséquence.

**Point 3 — "Lait 1 filet(s)" perdait sa quantité et mélangeait l'ordre
des mots ("filet Lait"), corrigé** : cause trouvée — "filet" n'était
reconnu comme unité nulle part, faisant échouer la ré-analyse du
format inversé et produisant un nom scindé de façon incohérente.
"filet" ajouté comme unité reconnue (`UNIT_OPTIONS`, chaîne de
reconnaissance, traductions dans les 4 langues). **Testé avec
précision contre la confusion redoutée** : "Filet de barramundi 2
pièce(s)" continue de traiter "Filet de barramundi" comme le nom de
l'ingrédient, jamais comme l'unité — le format inversé ne capture
qu'un seul mot isolé en position d'unité, jamais un mot en tête de nom
composé.

**Non traité dans cette session, discussion nécessaire avant de
lancer ce chantier** : la recommandation principale de l'audit — découper
la photo de préparation en 6 images séparées (grille 3×2) et lancer un
OCR indépendant sur chacune — représente un changement d'architecture
substantiel (manipulation de canvas, 6 passages OCR au lieu d'un seul,
temps de traitement nettement plus long) plutôt qu'un ajustement
ciblé comme les 3 points ci-dessus.

**Non-régression** : toute la suite de tests existante, le corpus
complet et les tests unitaires d'ingrédients relancés après chaque
changement, aucune régression.

**Version testée** : v187

### 43 — Découpage réel en 6 images avec OCR indépendant sur chacune *(v188)*

**Contexte** : chantier substantiel convenu avec l'utilisateur avant de
le lancer, vu son ampleur — la recommandation principale de l'audit
sur le vrai PDF Samsung (point 42) : plutôt que de reconstruire le
texte d'une seule passe OCR par coordonnées, découper réellement la
photo en 6 images (2 rangées x 3 colonnes) et lancer un OCR
indépendant sur chacune.

**Analyse préalable sur la vraie photo, avant toute intégration** :
examen direct des coordonnées de mots produites par un premier passage
OCR pour déterminer les limites de chaque case. Difficulté trouvée et
résolue en 3 itérations :
1. Un simple regroupement par saut vertical (seuil 60px, réutilisant
   la logique de l'ancienne reconstruction textuelle) donnait 5
   groupes séparés (titre et contenu de chaque rangée scindés par le
   petit espace dû à l'image entre les deux), pas les 2 vraies rangées
   de grille attendues.
2. Un seuil élargi (150px) fusionnait bien titre+contenu, mais
   fusionnait aussi à tort le pied de page (astuces de fin) dans la
   deuxième rangée.
3. Corrigé avec un regroupement fin (seuil 60px) suivi d'une fusion
   ciblée des 4 premiers groupes seulement (2 titres + 2 contenus,
   structure connue d'une fiche à 6 étapes), excluant explicitement
   tout ce qui suit — **vérifié sur la vraie photo** : exactement 2
   rangées propres obtenues (y=259-627 et y=810-1272), pied de page
   correctement exclu.

**Résultat, testé directement contre la vraie photo avant
intégration** : chaque case, une fois découpée et réanalysée
séparément, produit un texte **parfaitement ordonné** correspondant
exactement à la vraie recette — comparé à l'ancienne reconstruction
par coordonnées sur un seul passage (qui séparait déjà correctement
les 6 étapes, mais avec un ordre interne des mots encore imparfait à
cause de l'imprécision des coordonnées Tesseract sur cette photo
précise, un problème que le découpage en images résout à la racine en
donnant à Tesseract une image bien plus simple à lire pour chaque
passage). Temps mesuré : environ 7 à 8 secondes pour les 6 passages
OCR supplémentaires sur cette photo — l'indicateur de chargement
générique existant ("peut prendre une minute la première fois") reste
suffisamment informatif, aucun ajustement d'interface nécessaire.

**Implémenté** (`runOcrOnImage`) :
- `detectGridRowBounds(allWords)` : détermine les limites verticales
  des rangées de grille à partir des mots déjà obtenus lors du premier
  passage OCR (pas de nouveau passage nécessaire pour cette étape).
- `runGridCellOcr(worker, input, data, numColumns)` : découpe l'image
  source en cases (rangées x colonnes, avec une marge de 10px pour ne
  pas couper le texte aux bords) et relance l'OCR indépendamment sur
  chacune, combinant les textes obtenus.
- `gridText` n'est calculé que si une mise en page en grille est
  effectivement détectée — aucun coût supplémentaire pour les photos
  qui n'en ont pas besoin (ingrédients, listes simples type Marmiton).

**Ancienne fonction retirée** : `reconstructGridColumns` (reconstruction
textuelle par coordonnées sur un seul passage) devenue obsolète et
retirée proprement, plus aucun appelant après ce changement.

**Testé de bout en bout** : le pipeline complet
(`runOcrOnImage` → `deriveSectionDataForPhoto`) confirmé produire la
description améliorée sur la vraie photo. Corpus régénéré avec les
vraies données actuelles (`rawText`, `layoutText`, `gridText`
recalculés depuis la vraie photo avec le code v188), assertions
renforcées (5 phrases-clés au lieu de 4, couvrant désormais aussi la
dernière étape). Toute la suite de tests existante et le corpus complet
relancés après chaque changement, y compris une vérification
spécifique que les photos sans grille (Marmiton, ingrédients) ne
déclenchent jamais ce traitement plus coûteux.

**Version testée** : v188

### 44 — Détection de rangées rendue robuste, limite nutritionnelle renforcée *(v189)*

**Contexte** : nouveau test physique complet avec 3 nouvelles vraies
photos (couverture, ingrédients, préparation) sur une recette
Barramundi déjà connue, mais dans un cadrage différent (format paysage
plutôt que portrait) et une netteté légèrement inférieure. A révélé
une régression sérieuse sur la reconstruction en grille (v188), avec
un diagnostic précis et exploitable.

**Cause racine confirmée par examen direct des données réelles** :
la détection de rangées par coordonnées de mots (v188) regroupait les
mots par proximité verticale, mais sur cette nouvelle photo, du texte
de **faible confiance** produit par les photos de plat au sein de la
grille (mots comme "BE", "ONES", confiance 8 à 30) comblait
artificiellement l'espace entre les deux vraies rangées. Un filtrage
naïf par confiance a ensuite révélé un problème plus profond : du
**vrai texte** de la deuxième rangée avait aussi, sur cette photo
précise, une confiance individuelle par mot étonnamment basse
(ex. "les tomates dans les" à confiance 91-95, mais d'autres mots
adjacents de la même phrase à confiance 20-40) — un simple seuil de
confiance ne pouvait donc pas distinguer fiablement bruit et vrai
texte de façon généralisable à toute photo.

**Corrigé en abandonnant la détection par texte au profit d'une
division proportionnelle fixe** : `detectGridRowBounds` ne dépend plus
des coordonnées de mots ni de leur confiance, mais divise simplement
la hauteur de l'image en deux (moitié haute / moitié basse, léger
chevauchement pour ne pas couper le texte à la frontière). **Testé
directement sur les deux vraies photos disponibles, aux orientations
différentes** (nouvelle photo 1600×1200 paysage, ancienne photo
1200×1600 portrait) : les 6 étapes parfaitement séparées et dans le
bon ordre dans les deux cas — une robustesse que l'ancienne approche
par coordonnées n'atteignait pas de façon fiable d'une photo à
l'autre. Temps de traitement inchangé (5 à 8 secondes selon la
photo).

**Limite de fin de liste d'ingrédients renforcée** : ajout d'une
limite de secours reconnaissant le motif "nombre/nombre" (ex.
"2745/656"), signature quasi certaine d'une valeur d'énergie kJ/kcal —
robuste même quand le titre "Valeurs nutritionnelles" est si déformé
par l'OCR qu'aucun mot-clé ne correspond (constaté sur la vraie photo :
"(kifkeal)" au lieu de "kJ/kcal"). Sans changer le résultat observable
sur cette photo précise (les filtres ligne par ligne existants
rattrapaient déjà la plupart des lignes parasites), ce filet de
sécurité supplémentaire reste une protection plus directe et robuste
pour d'autres appareils ou photos où ces filtres seraient moins
efficaces.

**Test permanent ajouté** (`tests/test_full_merge_pipeline.py`),
comme recommandé, vérifiant que le temps de préparation détecté sur la
couverture survit jusqu'à la recette fusionnée finale, via le vrai
texte OCR du corpus. **Non reproduit avec le code actuel** : le
signalement d'un "35 min" disparu sur l'exécution physique réelle n'a
pas pu être reproduit avec les mêmes photos dans cet environnement
(la valeur survit correctement à chaque étape testée) — possible
variabilité OCR propre à l'appareil, comme observée à plusieurs
reprises pendant ce projet, plutôt qu'un défaut du code identifiable.
Le nouveau test reste en place pour détecter toute régression future
sur ce point précis, même sans avoir pu confirmer la cause exacte de
cet incident particulier.

**Non traité, confirmé comme limite de l'OCR plutôt que du code** :
"Beurre" absent et "Lait" non reconnu sur les ingrédients de cette
nouvelle photo — vérifié que ces deux mots n'apparaissent nulle part
dans le texte OCR brut lui-même, confirmant une limite de
reconnaissance de Tesseract sur cette photo précise (probablement liée
à sa netteté), pas un défaut de l'analyseur.

**Non-régression** : toute la suite de tests existante, le corpus
complet et les tests unitaires d'ingrédients relancés après chaque
changement, aucune régression — y compris une vérification spécifique
que les photos sans grille (Marmiton, ingrédients seuls) ne
déclenchent toujours pas ce traitement.

**Version testée** : v189

### 45 — Parenthèse fermante manquante corrigée, confirmation des corrections précédentes *(v190)*

**Contexte** : nouveau test physique complet sur la v189, avec un
cadrage encore différent des précédents. Confirme d'abord que
plusieurs corrections antérieures tiennent bien en conditions
réelles : **"Beurre" et "Lait" tous deux correctement reconnus avec
leur quantité et leur unité** (corrections des points 40 et 42),
"Pommes de terre" et "Filet de barramundi" toujours corrects.

**Vrai bug trouvé et corrigé** : "Persil plat et ciboulette*"
apparaissait sans aucune quantité ni unité dans le PDF réel. Isolé
précisément : le retrait du marqueur de pluriel `"(s)"` n'acceptait
que la forme AVEC la parenthèse fermante — or l'OCR l'omet
fréquemment ("sachet(s" sans le ")" final, un motif déjà rencontré à
plusieurs reprises dans ce projet). Sans cette parenthèse, le "("
résiduel cassait la fin du format inversé "Nom Quantité Unité",
faisant échouer toute reconnaissance de la ligne. Corrigé en rendant
la parenthèse fermante optionnelle dans les deux endroits où ce motif
était dupliqué (fonction interne et enveloppe de
`parseIngredientString`). **Testé avec le cas réel exact** ("Persil
plat et ciboulette* 1 sachet(s") et 2 cas de non-régression (même
motif avec une autre unité, et le cas normal AVEC la parenthèse
présente) : tous corrects. **Test permanent ajouté** à
`test_ingredient_parsing.py`.

**Limite honnête découverte en investiguant le séparateur "À ajouter
vous-même"** : sur cette nouvelle photo, ce séparateur était
tellement déformé ("LrrereP SiOiter vous-tree") qu'aucun motif textuel
raisonnable ne peut le reconnaître — confirmé ne contenir aucune
sous-chaîne "ajouter" reconnaissable. **Découverte complémentaire** en
vérifiant si au moins le score de confiance le signalait "à
vérifier" : non, car ses mots ont une longueur moyenne élevée malgré
leur non-sens complet (le score actuel ne vérifie que la longueur des
mots, pas leur plausibilité en tant que vrais mots) — un vrai angle
mort du système de score, documenté ici honnêtement plutôt que
corrigé dans l'urgence par une règle supplémentaire risquant, comme à
plusieurs reprises dans ce projet, un sur-ajustement à ce seul
exemple.

**Non-régression** : toute la suite de tests existante, le corpus
complet et les tests unitaires relancés après chaque changement,
aucune régression.

**Version testée** : v190

### 46 — Fiabilité du déclenchement de grille et corrections issues d'une nouvelle recette réelle (Marmiton Cassoulet) *(v191)*

**Contexte** : nouveau test physique avec une recette de type très
différent (Marmiton "Cassoulet à l'ancienne", 8 personnes, liste
d'ingrédients en 2 colonnes) en complément du Barramundi déjà connu.
Confirme que la correction `sachet(s` (v190) fonctionne bien en
conditions réelles. Révèle un problème critique de fiabilité et
plusieurs nouveaux défauts précis sur ce type de recette.

**Point 1 — déclenchement de la grille de préparation non fiable
d'un appareil à l'autre, corrigé** : sur la nouvelle photo Barramundi
(pourtant en grille), le découpage en 6 cases ne s'est pas déclenché
sur le Samsung alors qu'il fonctionnait dans l'environnement de test —
confirmant que le signal de chevauchement de mots
(`looksLikeMergedGridLayout`), bien que fiable dans cet environnement,
dépend trop de la reconnaissance OCR elle-même (variante WASM,
netteté...) pour être fiable partout. Corrigé en **combinant** ce
signal avec un critère géométrique simple et indépendant de
l'appareil : l'orientation paysage de la photo (rapport largeur/hauteur
> 1,15), qu'une photo de préparation HelloFresh présente presque
toujours. Le coût d'un déclenchement superflu sur une photo qui
n'est pas réellement en grille reste limité au temps de traitement
(`gridText` n'étant utilisé que pour la section "preparation").
Vérifié sans régression sur les photos existantes (portrait,
signal de chevauchement toujours actif quand pertinent).

**Point 2 — couverture Marmiton classée à tort "Ingrédients", corrigé** :
la couverture affiche déjà les 3-4 premières lignes de la vraie liste
d'ingrédients au bas du cadrage (avant que l'utilisateur ne fasse
défiler), faisant basculer la classification à tort et perdant le nom,
la durée et la difficulté. **Vérifié sur nos vraies données existantes**
qu'aucune vraie photo d'ingrédients (Barramundi, salade) n'affiche
jamais À LA FOIS les personnes ET une durée (la durée étant une
information de couverture, presque jamais présente sur une photo
recadrée sur les seuls ingrédients) — signal retenu pour distinguer
les deux cas : personnes ET durée présentes ensemble, combiné à un
petit nombre d'ingrédients trouvés (≤5), fait désormais préférer
"Informations générales". **Testé avec le cas réel exact** et un cas
de non-régression (vraie photo d'ingrédients sans durée, reste bien
classée normalement).

**Point 3 — durée isolée au format "6h10" non reconnue, corrigé** :
Marmiton affiche souvent la durée sans aucun préfixe explicite
("6h10 • Facile • Assez cher"), un format qu'aucun motif existant ne
capturait (tous exigeaient un préfixe comme "Préparation :"). Ajoutée
une reconnaissance de ce format isolé, limitée aux lignes courtes pour
éviter un faux positif sur un motif "XhXX" apparaissant au milieu d'un
texte plus long sans rapport. Testé avec le cas réel et un cas de
non-régression.

**Point 4 — titre pollué par la note et le nombre de commentaires,
corrigé** : "Cassoulet à l'ancienne 4.7/5 3 commentaires" au lieu du
titre seul — la note était déjà collée au titre par l'OCR lui-même, et
la fusion de sous-titre (v187) absorbait en plus la ligne de
durée/difficulté suivante. Corrigé à deux niveaux : retrait du motif
note/commentaires du nom quelle que soit son origine, et nouvelle
limite empêchant la fusion de sous-titre d'absorber une ligne de
durée isolée ou de difficulté ("Facile", "Moyen", "Difficile", prix).
Testé avec le cas réel et confirmé que la fusion de sous-titre
HelloFresh (2 lignes légitimes) continue de fonctionner normalement.

**4 tests permanents ajoutés** dans un nouveau fichier
`tests/test_section_detection.py`, chacun avec un cas réel et au
moins un cas de non-régression.

**Non traité dans cette session, chantier séparé à discuter** :
la liste d'ingrédients en 2 colonnes de cette recette Cassoulet
(structurellement différente de la table quantité/unité HelloFresh —
ici, 2 colonnes indépendantes d'ingrédients côte à côte) fait encore
fusionner à tort les deux ingrédients d'une même rangée en une seule
ligne. Ce chantier représente un nouveau type de mise en page à
traiter, distinct de la grille de préparation déjà résolue, et
mériterait sa propre analyse dédiée avant implémentation plutôt qu'un
ajustement à la volée dans cette même session.

**Non-régression** : toute la suite de tests existante, le corpus
complet et tous les tests unitaires relancés après chaque changement,
aucune régression.

**Version testée** : v191

### 47 — Découpage réel en 2 colonnes pour les listes d'ingrédients Marmiton *(v192)*

**Contexte** : chantier convenu avec l'utilisateur, volontairement
reporté au tour précédent (v191) pour analyse dédiée — la liste
d'ingrédients de la recette Cassoulet (Marmiton, 2 colonnes de cases à
cocher) faisait fusionner à tort les deux ingrédients d'une même
rangée, produisant 32 lignes incohérentes pour 17 ingrédients réels.

**Analyse préalable sur la vraie capture, avant toute intégration** :
examen direct du texte OCR brut confirmant la structure exacte —
chaque case à cocher affiche sa quantité sur une ligne et son nom sur
la ligne suivante ("1\noignon"), et les DEUX colonnes se retrouvent
mélangées sur la MÊME ligne reconnue par Tesseract ("[sel [ poivre",
"oignon oignons"...), un phénomène structurellement analogue à celui
déjà résolu pour la grille de préparation à 3 colonnes, mais avec une
mise en page différente (2 colonnes seulement, nombre de rangées
variable, chaque ingrédient sur 2 lignes plutôt qu'une seule).

**Solution conçue et testée directement sur la vraie capture avant
intégration** : découpage réel de l'image en 2 moitiés verticales
(gauche/droite, pleine hauteur chacune, léger chevauchement pour ne
pas couper le texte à la frontière) avec OCR indépendant sur chacune —
**chaque colonne ressort parfaitement séparée**, quantité et nom
correctement associés (validé avant tout code : "sel", "1 oignon",
"2 clous de girofle"... pour la colonne gauche, "poivre", "2 oignons",
"1 carotte"... pour la colonne droite, correspondant exactement à la
vraie fiche). Temps mesuré : 2,9 secondes pour les 2 passages
supplémentaires.

**Bug latent découvert et corrigé au passage** : `runGridCellOcr` (le
chantier précédent, v188) aurait échoué sur une entrée PNG — jamais
testée avec ce cas précis jusqu'ici, l'entrée pouvant être un `File`
brut non redimensionné (voir `resizeImageForOcr`) plutôt qu'un canvas,
que `drawImage()` n'accepte pas directement. Corrigé avec une
normalisation systématique en bitmap dessinable, appliquée aux deux
fonctions de découpage d'image.

**Analyseur dédié conçu et affiné en 2 itérations** — `parseStackedIngredientColumn`,
pour le format "quantité sur une ligne, nom sur la suivante" :
1. Une première version nettoyait trop agressivement les préfixes de
   case à cocher parasites, mangeant parfois une vraie lettre de début
   de mot ("el" au lieu de "sel").
2. Corrigée avec une détection plus prudente (préfixe court suivi d'un
   espace, uniquement si ce préfixe contient un symbole ou fait 1-2
   caractères) et une reconnaissance de quantité plus permissive
   (tolère un court préfixe générique parasite avant le chiffre,
   plutôt qu'une liste fixe de symboles).

**Intégration prudente, sans détection préalable devinée** : contrairement
à la grille de préparation (où l'orientation paysage sert de signal
géométrique fiable), aucun signal fiable n'a été trouvé pour détecter
à l'avance une liste d'ingrédients en 2 colonnes — le signal de
chevauchement de mots existant, testé directement sur cette capture,
ne se déclenche pas pour ce type de mise en page. Le découpage en 2
colonnes n'est donc tenté qu'**après confirmation** que la section a
été classée "ingredients", évitant de deviner à l'avance et le coût de
ce traitement sur des photos où il ne serait jamais utilisé. **Résultat
retenu uniquement s'il produit plus d'ingrédients que l'extraction
standard** — signe qu'une vraie mise en page à 2 colonnes a été
démêlée avec succès, plutôt qu'une liste à une seule colonne où ce
découpage n'aurait rien apporté. Mis en cache sur l'entrée pour être
réutilisé sans recalcul si l'utilisateur change ensuite manuellement
la section.

**Résultat final, testé de bout en bout sur la vraie capture** :
19 ingrédients correctement entrelacés dans l'ordre de lecture naturel
(gauche puis droite, ligne par ligne) sur les 17 réels — contre 32
lignes incohérentes initialement. **Limite honnête documentée** : 2
ingrédients restent imparfaits ("1kg" lu "like", "3" lu "Os" par
Tesseract lui-même) — le chiffre de quantité est mal reconnu comme des
lettres, une limite de reconnaissance OCR que l'analyse en aval ne
peut pas corriger ; ces lignes restent correctement signalées "à
vérifier" ou visibles pour correction manuelle plutôt que
silencieusement fausses.

**Vérifié sans régression** sur les vraies photos à une seule colonne
déjà validées (salade grecque toujours 12, Barramundi toujours 11).

**Corpus enrichi** : nouveau cas `photo_cassoulet_ingredients_2colonnes.json`
avec les vraies données de la capture, `twoColumnIngredients`
pré-calculé, assertions sur 4 ingrédients-clés. `run_ocr_corpus.py` mis
à jour pour propager ce nouveau champ optionnel.

**Non-régression** : toute la suite de tests existante, le corpus
complet (6 cas) et tous les tests unitaires relancés après chaque
changement, aucune régression.

**Version testée** : v192

### 48 — Personnes non devinées silencieusement, nouveau variant de parenthèse isolée *(v193)*

**Contexte** : nouveau test physique avec 2 recettes inédites (Marmiton
"Retour des fameuses pâtes carbo à la française" et "La Chèvre Chaud :
betterave & bacon"). Le PDF final de la recette Carbonara affichait
"4 personnes" au lieu des 2 réelles — investigué directement.

**Point 1 — cause trouvée : "4" deviné silencieusement, corrigé** :
ni la couverture ni la photo d'ingrédients de cette recette précise ne
contenaient de motif "N personnes" lisible par l'OCR (probablement un
problème d'éclairage sur cette capture, signalé par l'utilisateur
lui-même). Le formulaire retombait alors sur une valeur par défaut
codée en dur ("4"), au lieu de laisser le champ vide comme le font déjà
correctement les champs temps de préparation/cuisson dans la même
situation — masquant ainsi le fait que la vraie valeur n'avait pas pu
être détectée, plutôt que d'inviter l'utilisateur à la vérifier.
Corrigé en alignant le champ personnes sur le même comportement :
laissé vide en contexte d'import (photo ou URL) quand rien n'a été
détecté, le "4" par défaut restant réservé à la création manuelle
d'une toute nouvelle recette depuis zéro. **Testé avec 3 scénarios**
(import sans détection → vide, import avec 2 détecté → conservé,
nouvelle recette vierge → 4 inchangé) : tous corrects.

**Point 2 — nouveau variant de parenthèse isolée sans "s)" du tout,
corrigé** : "Persil* 1 sachet (" (juste "(" en fin de ligne, sans même
un "s" résiduel) faisait complètement échouer la reconnaissance de la
quantité — un variant encore plus dégradé que celui corrigé au point
45 ("sachet(s" sans la fermeture). Corrigé en généralisant le motif de
retrait en un seul motif ancré en fin de chaîne, couvrant les 3
variantes observées à ce jour ("(s)" complet, "(s" sans fermeture, "("
isolé). Testé avec le cas réel exact, sans régression sur les 3 cas
déjà couverts.

**Non reproduit avec le code actuel** : "Spaghetti 180" perdant son
unité "g" dans le PDF final n'a pas pu être reproduit — testé
directement avec le vrai texte OCR de cette photo (qui contient bien
"180 g"), la quantité et l'unité sont correctement extraites à travers
tout le pipeline. Cause exacte non déterminée (peut-être un état du
code antérieur aux corrections déjà livrées, ou un artefact propre à
l'export PDF plutôt qu'à l'analyse elle-même).

**Autres lignes fortement dégradées observées sur cette recette**
(noms tronqués à une lettre isolée, unités méconnaissables) **non
investiguées individuellement** : probablement des limites de
reconnaissance OCR liées à l'éclairage de la capture, comme
l'utilisateur l'a lui-même anticipé, plutôt que des défauts de
l'analyse — cohérent avec le principe déjà établi dans ce projet de ne
pas sur-ajuster à des cas de dégradation extrême au cas par cas.

**2 tests permanents ajoutés** (un dans `test_ingredient_parsing.py`
pour le nouveau variant de parenthèse, un dans
`test_section_detection.py` pour le champ personnes).

**Non-régression** : toute la suite de tests existante, le corpus
complet et tous les tests unitaires relancés après chaque changement,
aucune régression.

**Version testée** : v193

### 49 — Vérification complète sur toutes les vraies photos du projet : 3 défauts sérieux trouvés et corrigés *(v194)*

**Contexte** : à la demande de l'utilisateur, vérification systématique
du code v193 en repassant **toutes** les vraies photos collectées
depuis le début du projet (Salade grecque, 2 sessions Barramundi,
Cassoulet, Carbonara, Chèvre Chaud) à travers le pipeline complet
(OCR → détection de section → extraction → fusion), plutôt que de se
limiter aux cas déjà couverts par le corpus. A révélé 3 défauts
sérieux qu'aucun test individuel n'avait détectés.

**Point 1 — régression critique du chantier 2 colonnes (v192),
corrigée** : le découpage en 2 colonnes s'appliquait à tort à des
photos d'ingrédients à une seule colonne, fragmentant chaque ligne en
deux morceaux incohérents. Une vraie photo Barramundi (10 ingrédients
réels) produisait 40 "ingrédients" absurdes ; une vraie photo Salade
grecque (12 réels) en produisait 62. Cause : le critère de sélection
"plus d'ingrédients = meilleur résultat" (v192) ne suffisait pas à
distinguer une vraie mise en page à 2 colonnes correctement démêlée
d'une liste à une seule colonne fragmentée à tort, qui produit
mécaniquement PLUS de "lignes" mais de bien moins bonne qualité.
Corrigé en ajoutant un garde-fou de qualité, calibré sur des données
réelles : la proportion d'ingrédients avec une quantité reconnue est de
68 % sur le vrai cas à 2 colonnes (Cassoulet) contre seulement 18 % sur
le cas cassé (Barramundi) — 40 % retenu comme seuil de sécurité. Testé
sur les vraies photos Barramundi (retour à 8-11 ingrédients raisonnables)
et Cassoulet (toujours 19 ingrédients, aucune régression sur le corpus).

**Point 2 — photo d'ingrédients sans ligne d'en-tête visible, corrigée** :
une vraie photo Carbonara cadrée sans "Ingrédients pour N personnes"
visible (probablement coupée hors du cadre) se retrouvait classée à
tort "Préparation", avec zéro ingrédient extrait. Cause : la
classification automatique (`detectPhotoSection`) dépend entièrement
de `parseOcrRecipeText`, dont le comportement conservateur (délibéré
et raisonnable pour son propre usage : "mieux vaut des ingrédients
vides qu'un découpage hasardeux") laisse les ingrédients vides quand
aucun marqueur n'est trouvé — mais cette prudence empêchait aussi la
CLASSIFICATION de reconnaître une vraie photo d'ingrédients dans ce
cas précis. Corrigé en ajoutant un signal de repli dédié,
`looksLikeIngredientTableWithoutMarker`, qui estime la probabilité
d'une table d'ingrédients à partir de la densité de lignes se
terminant par une unité reconnue (`\d+\s*(g|kg|sachet|pièce...)`),
utilisé uniquement pour la CLASSIFICATION (pas pour l'extraction
elle-même, qui continue d'utiliser `extractIngredientsFromLines`,
déjà capable de traiter tout le texte sans marqueur). Seuil calibré
sur le cas réel (29,6 % de lignes correspondantes, seuil retenu à
25 % avec une marge de sécurité). Testé sans aucun faux positif sur
les 8 autres vraies photos de préparation et de couverture du projet.

**Point 3 — division silencieuse des quantités par un nombre de
personnes deviné, corrigée** : en investiguant le "4 personnes" déjà
signalé (point 48, uniquement corrigé côté affichage du formulaire),
découvert que `mergeMultiPhotoResults` divisait aussi silencieusement
les quantités par 4 quand le nombre de personnes était réellement
inconnu — un défaut plus grave que le simple affichage, puisqu'il
fausse durablement les quantités STOCKÉES. Corrigé : les quantités
restent désormais à leur valeur brute (non divisées) quand ni
l'utilisateur ni aucune photo n'a permis de déterminer le nombre de
personnes, cohérent avec le champ du formulaire déjà laissé vide dans
ce cas plutôt que rempli d'une valeur inventée. **Vérifié explicitement
sans régression** : la division normale par un nombre de personnes
réellement connu continue de fonctionner correctement (testé avec 2
personnes, quantité 500 g → 250 g par personne, inchangé).

**5 tests permanents ajoutés** dans un nouveau fichier
`tests/test_verification_complete.py`, couvrant les 3 points
ci-dessus avec des cas réels et des vérifications de non-régression,
dont un garde-fou testant explicitement qu'un faux résultat 2 colonnes
de mauvaise qualité (30 fragments sans quantité) est bien rejeté.

**Non-régression** : toute la suite de tests existante, le corpus
complet et tous les tests unitaires relancés après chaque changement,
aucune régression.

**Version testée** : v194

### 50 — Compatibilité des sauvegardes entre l'app mobile et l'app Windows *(v195, + modifications sur `main.py`)*

**Contexte** : demande explicite de l'utilisateur — faire fonctionner
les sauvegardes indifféremment entre l'application mobile (PWA, ce
dépôt) et une application de bureau distincte ("MonLivreDeRecettes",
Python/tkinter), avec des tailles de fichiers gérées de façon
cohérente entre les deux.

**Analyse préalable, avant tout code** : comparaison détaillée des deux
architectures de sauvegarde. Différences trouvées :
- Format : JSON plat unique (mobile, photos en base64 intégrées) contre
  archive ZIP avec fichiers JSON séparés + dossier `images/` (Windows,
  module Python `zipfile`).
- **Aucun identifiant stable côté Windows** — les recettes y étaient
  identifiées par leur nom uniquement.
- **Aucune limite de taille côté Windows**, contre 50 Mo
  (avertissement) / 100 Mo (refus) côté mobile.
- Noms de champs différents (camelCase contre snake_case) mais très
  proches conceptuellement pour la plupart.
- Différences de conception plus profondes pour le planning
  hebdomadaire (Windows : un seul créneau par jour référencé par nom de
  recette ; mobile : trois créneaux par jour référencés par
  identifiant), les menus et les listes de courses enregistrées.

**Périmètre volontairement recentré en cours de route** : plutôt que de
forcer une correspondance approximative pour le planning/menus/listes
de courses (risquant de mélanger des données incohérentes entre les
deux applications), le format partagé se limite aux données les plus
utiles à faire circuler entre les deux appareils : **recettes (avec
leurs photos), ingrédients connus, garde-manger, personnalisations**
(allergènes, prix, substituts). Documenté clairement des deux côtés.

**Bibliothèque ZIP maison, après un premier échec instructif** : une
première tentative avec la bibliothèque JSZip (récupérée via le web,
~100 Ko sur une seule ligne minifiée) a échoué — le fichier s'est
corrompu pendant la sauvegarde locale (`Cannot find module
'./stream/StreamHelper'` à l'exécution). Plutôt que de retenter le
transfert, implémenté un lecteur/écrivain ZIP minimal en s'appuyant sur
les API de compression natives du navigateur
(`CompressionStream`/`DecompressionStream`, format "deflate-raw",
disponibles depuis Chrome/Edge 80+, Firefox 113+, Safari 16.4+) —
aucune dépendance externe, donc aucun risque de corruption au
transfert. **Compatibilité avec le module Python `zipfile` (utilisé
côté Windows) vérifiée dans les deux sens avec de vraies commandes** :
un zip généré par le nouveau code JS s'ouvre et se vérifie
correctement avec `zipfile.testzip()` côté Python ; un zip généré par
Python (compression DEFLATE) se relit correctement côté JS.

**Deux erreurs d'étourderie corrigées en cours de route** : lors de
l'ajout du nouveau module ZIP puis des fonctions de conversion, la
ligne de déclaration de la fonction/constante suivante a été
accidentellement effacée à deux reprises par un remplacement de texte
mal délimité (`BACKUP_STORES`, puis `buildBackupData`) — chaque fois
repéré immédiatement par la vérification de syntaxe systématique après
chaque modification, et corrigé sur-le-champ.

**Identifiant stable ajouté côté Windows, avec migration automatique** :
chaque recette reçoit désormais un identifiant (`uuid4`) à sa création.
Une recette déjà existante sans identifiant (créée avant cette version)
en reçoit un nouveau silencieusement au premier chargement, sauvegardé
immédiatement pour que la migration ne s'exécute qu'une seule fois par
recette. **Testé directement** (voir plus bas la méthode de test) :
l'identifiant reste stable d'un chargement à l'autre après migration,
et une recette ayant déjà un identifiant n'est jamais modifiée.

**Méthode de test pour le code Windows, sans interface graphique
disponible** : cet environnement ne dispose pas de tkinter ni d'écran,
rendant impossible l'exécution normale de l'application Windows.
Contournement mis en place : des modules `tkinter`/`tkinter.ttk` factices
minimalistes (une classe générique répondant à n'importe quel attribut
ou appel par un objet inerte) permettent d'importer le vrai fichier
`main.py` et d'exécuter directement ses fonctions de couche de données
(chargement/sauvegarde des recettes, ingrédients, garde-manger...) sans
jamais déclencher de code d'interface graphique — la partie testée
correspond exactement au code qui sera réellement exécuté par
l'application, contrairement à une réécriture séparée à des fins de
test.

**Résultat le plus important, vérifié avec du vrai code des deux côtés,
dans les deux sens** :
- Une vraie archive produite par le vrai code JavaScript (recette avec
  photo, ingrédients) importée avec succès par le vrai code Python —
  tous les champs corrects, **photo vérifiée identique octet pour
  octet**.
- Une vraie archive produite par le vrai code Python importée avec
  succès par le vrai code JavaScript — même vérification, résultat
  identique.

**Fonctions ajoutées côté application mobile** (`app.js`) :
`buildZipFile`/`parseZipFile` (module ZIP générique), `crc32`,
`deflateRawBytes`/`inflateRawBytes` (API natives), `recipeToSharedFormat`/
`recipeFromSharedFormat`, `pantryToSharedFormat`/`pantryFromSharedFormat`,
`buildSharedBackupZip`, `restoreFromSharedZip`. Interface ajoutée dans
l'écran Sauvegarde (nouvelle section dédiée, avec sélecteur de mode
fusion/remplacement identique à l'import classique).

**Fonctions ajoutées côté application Windows** (`main.py`) :
`build_shared_backup_zip`, `restore_from_shared_zip`, migration
d'identifiant dans `load_recipes`. Interface ajoutée dans la fenêtre
d'import/export existante (deux nouveaux boutons, sous un séparateur
dédié) — **le câblage de l'interface elle-même (dialogues tkinter) n'a
pas pu être testé visuellement**, faute d'environnement graphique
disponible ; la logique sous-jacente (les deux fonctions ci-dessus) a
en revanche été testée en profondeur comme décrit plus haut.

**Limites de taille alignées** : 50 Mo (avertissement) / 100 Mo (refus)
désormais appliquées des deux côtés, sur les deux fonctions de
restauration Windows (format partagé et format complet existant) —
totalement absentes côté Windows auparavant.

**Test permanent ajouté** (`tests/test_shared_backup.py`), couvrant le
module ZIP maison et l'aller-retour export/import complet côté
application mobile. La compatibilité réelle avec l'application Windows,
elle, a été vérifiée manuellement comme décrit ci-dessus mais ne peut
pas être automatisée dans ce dépôt (tkinter indisponible dans cet
environnement).

**Non-régression** : toute la suite de tests existante côté application
mobile relancée après chaque changement, aucune régression.

**Version testée** : v195 (mobile), modifications non versionnées côté
application Windows (pas de système de version dans ce projet distinct).

### 51 — Bouton de partage pour l'export au format partagé *(v196)*

**Contexte** : l'export au format partagé (voir point 50) ne
proposait que le téléchargement direct dans le dossier Téléchargements
— demande explicite de l'utilisateur d'ajouter aussi le partage natif
(Drive, Gmail, Dropbox...), comme c'est déjà le cas pour l'export
classique.

**Corrigé en réutilisant le mécanisme déjà en place** : `shareBackupData`
étant générique (accepte n'importe quel `File`, sans dépendre du
format de sauvegarde), directement réutilisée pour le fichier ZIP
partagé — même précaution que pour l'export classique (fichier
entièrement préparé avant que le bouton ne devienne cliquable, pour
qu'aucun `await` ne s'intercale entre le clic et l'appel à
`navigator.share()`), même repli sur le téléchargement classique en
cas d'échec du partage.

**Testé** : rendu de l'interface sans capacité de partage (bouton de
partage absent, téléchargement seul proposé, comportement inchangé) et
avec capacité de partage simulée (bouton présent, désactivé puis
activé une fois le fichier prêt, texte correct) — aucune erreur JS
dans les deux cas.

**Non-régression** : suite de tests existante et corpus complet
relancés, aucune régression.

**✅ Confirmé fonctionnel en conditions réelles par l'utilisateur** :
export et import de sauvegarde testés dans les deux sens entre l'app
mobile réelle et l'app Windows réelle — ça fonctionne. Il s'agit du
premier test physique de tout le chantier de compatibilité (points 50
et 51), jusqu'ici seulement vérifié par du code exécuté directement
sans interface graphique (voir point 50) faute d'environnement adapté
pour ce faire. Confirme que le câblage des boutons Windows
(jusque-là jamais vu à l'écran) fonctionne correctement, en plus de la
logique sous-jacente déjà testée en profondeur.

**Version testée** : v196

### 52 — Audit complet de l'application, corrections design/UI *(v197)*

**Contexte** : audit complet demandé par l'utilisateur, couvrant
fonctionnement et design/interface. Méthode : captures d'écran réelles
de 17 écrans (mode clair, sombre, mobile et écran large), calcul des
ratios de contraste WCAG sur toute la palette, vérification de code
ciblée — pas de simulation, tout vu ou mesuré concrètement.

**Piège méthodologique repéré et corrigé en cours d'audit** : chaque
script Playwright démarre un navigateur neuf, donc IndexedDB ne
persiste pas entre deux scripts séparés — les toutes premières captures
montraient des écrans vides malgré des données insérées juste avant,
et une bannière "restaurer une sauvegarde" affichée à tort. Corrigé en
regroupant insertion des données et captures dans une seule session ;
confirmé ensuite que le code lui-même était correct
(`state.recipes.length === 0` avant correction, `4` après — la logique
d'affichage de la bannière était juste, c'est la donnée de test qui
manquait).

**Fausse alerte écartée après vérification** : chevauchement apparent
entre le bouton flottant "+" et les boutons de suppression en bas de
liste. Vérifié par un vrai test de défilement jusqu'en bas d'une
longue liste (700+ ingrédients) : le dernier élément reste pleinement
atteignable, padding-bas correct. Comportement normal d'un bouton
flottant, pas un bug.

**Contraste des couleurs vérifié par calcul** (pas à l'œil) : les 10
combinaisons principales de la palette (texte/fond, boutons, mode
sombre) passent toutes WCAG AA (4,5:1 minimum) — de 4,64:1 à 14,5:1
selon les paires.

**3 corrections appliquées, chacune testée visuellement avant/après** :

1. **Puces de filtre coupées sans indice de défilement** (écran
   Recettes) : la 4ᵉ puce ("Envies") était coupée net, barre de
   défilement volontairement masquée sans aucun signal alternatif.
   Corrigé en enveloppant `.chip-row` dans un conteneur
   `.chip-row-wrap` avec un dégradé sur le bord droit
   (`pointer-events:none` pour ne jamais bloquer un appui sur la
   dernière puce partiellement visible). Confirmé visuellement : la
   puce se fond maintenant proprement au bord plutôt que d'être
   coupée à l'aveugle.

2. **Bouton "Choisir un fichier" non stylisé** (écran Sauvegarde, 2
   emplacements : import classique et import au format partagé).
   Corrigé avec le motif déjà utilisé pour la photo de recette (entrée
   native rendue invisible, `<label>` stylisé en bouton à la place) —
   plus l'ajout d'un affichage du nom de fichier choisi, absent du
   nouveau style puisque le rendu natif du navigateur ne l'affiche
   plus. **Conflit de spécificité CSS trouvé et corrigé en cours de
   route** : la couleur du texte du bouton ne correspondait pas à
   celle voulue (`.field label` existant, plus spécifique, l'emportait
   sur la nouvelle classe) — détecté en vérifiant précisément la
   couleur calculée (`rgb(121,110,94)` au lieu de `rgb(43,36,32)`
   attendu), pas seulement à l'œil où la différence était trop subtile
   pour être fiable. Corrigé en renforçant la spécificité du
   sélecteur. Fonctionnalité de sélection de fichier retestée après
   coup : toujours opérationnelle.

3. **Cibles tactiles sous 44px** : boutons +/- personnes (32→44px),
   crayon/poubelle de la gestion des ingrédients (34→44px), et un 3ᵉ
   cas trouvé en vérifiant plus largement pendant la correction
   (bouton de suppression d'ingrédient dans le formulaire de recette,
   38→44px, non listé dans l'audit initial mais suivant le même motif).

**Point 4 de l'audit initial (mise en page desktop non peaufinée)**
volontairement laissé tel quel à la demande de l'utilisateur — l'app
étant clairement conçue mobile-first (navigation du bas, import
photo/QR), jugé non prioritaire.

**Non-régression** : toute la suite de tests existante et le corpus
complet relancés après chaque correction, aucune régression.

**Version testée** : v197

**✅ Confirmé fonctionnel en conditions réelles par l'utilisateur** —
sur les deux appareils : bouton de partage de l'export partagé (menu
de partage natif Android), les 3 corrections visuelles (dégradé sur
les puces de filtre, bouton de fichier stylisé, cibles tactiles
agrandies) côté mobile ; numéro de version dans le titre de fenêtre,
position des 2 nouveaux boutons, comportement en conditions réelles
côté Windows. Clôture la série de vérifications physiques ouverte
depuis le chantier de compatibilité des sauvegardes (points 50 à 52).

### 53 — Import des données de référence ingrédients depuis l'app Windows v56 *(v198)*

**Contexte** : l'utilisateur a fourni la dernière version de
l'application Windows (v56), dans laquelle un audit indépendant avait
mis à jour les données de référence des 1 030 ingrédients — allergènes,
valeurs nutritionnelles et traductions — avec une source officielle
(ANSES, Table Ciqual 2025, licence ouverte Etalab 2.0) plutôt que des
estimations. Demande : réutiliser ce travail déjà fait pour améliorer
les mêmes données côté application mobile, sans repartir d'une
recherche web.

**Compatibilité de structure confirmée avant tout changement** :
l'application mobile charge déjà, depuis son propre dossier `data/`,
exactement les mêmes fichiers que l'application Windows (mêmes noms,
même format JSON) — `ingredients_par_defaut.json`,
`ingredient_allergenes.json`, `valeurs_nutritionnelles.json`,
`ingredient_translations_{en,es,de}.json`. Un import direct par simple
remplacement de fichier était donc possible, sans conversion.

**Ampleur des changements vérifiée précisément avant l'import** (pas
seulement en confiance sur l'annonce du fichier `AUDIT_INGREDIENTS_v56.md`
fourni) :
- Liste des 1 030 noms d'ingrédients : identique (aucun ajout ni
  suppression), confirmé par comparaison d'ensembles.
- **60 corrections d'allergènes** trouvées par comparaison ligne à
  ligne — nombre exactement égal à celui annoncé dans l'audit fourni.
  Exemples réels vérifiés : "Beurre" passe de `[]` à `["Lactose"]`
  (allergène manquant, potentiellement dangereux à l'oubli) ; "Courge
  spaghetti" perd à tort l'étiquette "Gluten" (faux positif retiré).
- **289 fiches nutritionnelles avec des valeurs différentes** sur les
  290 annoncées (écart d'une seule fiche, négligeable — sans doute une
  estimation déjà correcte par coïncidence). 290 fiches disposent
  désormais d'une provenance Ciqual explicite (code, nom précis de
  l'aliment, URL source) dans un champ `_ciqual`, absent des fiches
  encore estimées.
- **26 corrections de traduction** au total sur les 3 langues (9 en
  anglais, 7 en espagnol, 10 en allemand) — somme exactement égale à
  celle annoncée dans l'audit fourni.
- Substitutions d'ingrédients : confirmées identiques (non concernées
  par cet audit), donc non touchées.

**Compatibilité du nouveau champ `_ciqual` avec le code existant
vérifiée avant l'import** : `getIngredientNutrition`/
`computeRecipeNutrition` ne lisent que les champs `kcal`, `protein_g`,
`carbs_g`, `fat_g` par accès direct — jamais d'itération sur toutes
les clés d'un enregistrement. Le nouveau champ de provenance est donc
ignoré sans risque par le code existant, aucune adaptation nécessaire.

**Fichiers remplacés** dans `data/` : les 6 fichiers listés ci-dessus.
**Sauvegarde de sécurité** des anciennes versions conservée
séparément avant tout remplacement.

**Testé de bout en bout après l'import** : `getIngredientAllergens`,
`getIngredientNutrition`, `computeRecipeAllergens`,
`computeRecipeNutrition` — tous confirmés fonctionner avec les
nouvelles données, y compris le cas "Beurre" (allergène désormais
détecté au niveau recette) et "Ail en poudre" (346 kcal, exemple cité
tel quel dans l'audit fourni). Aucune erreur JS.

**Service worker** : ces 6 fichiers étaient déjà dans la liste de
préchargement (`FILES_TO_CACHE`) — la version a donc été incrémentée
pour que les installations existantes récupèrent bien les fichiers mis
à jour, plutôt que de continuer à servir indéfiniment les anciennes
données déjà en cache.

**Test permanent ajouté** (`tests/test_ingredient_reference_data.py`),
avec un échantillon représentatif des corrections (pas une
vérification exhaustive des 390 corrections) — protège contre une
régression accidentelle qui effacerait ce travail déjà fait, sans
revalider l'exactitude scientifique des valeurs elle-même (hors de
portée d'un test automatisé).

**Non-régression** : toute la suite de tests existante et le corpus
complet relancés après le remplacement, aucune régression.

**Limite honnête** : 740 fiches nutritionnelles restent des
estimations non vérifiées côté source (précisé explicitement dans
l'audit fourni) — cet import améliore la base existante, ne la
certifie pas intégralement.

**Version testée** : v198

**✅ Confirmé fonctionnel en conditions réelles par l'utilisateur** —
tous les points de vérification passés : mise à jour bien déclenchée,
"Beurre" affiche désormais l'allergène Lactose, valeurs nutritionnelles
changées comme attendu, aucun ingrédient manquant (toujours 1030).
Temps de premier chargement mesuré à 2-3 secondes (fichier nutrition
+60% plus lourd), quasi instantané ensuite grâce à la mise en cache —
jugé tout à fait acceptable par l'utilisateur.

### 54 — Audit complet de l'application, mise en cache des polices hors-ligne, fenêtre de minuteurs autonome *(v199)*

**Contexte** : audit complet demandé par l'utilisateur (résidus de
code, erreurs, problèmes graphiques, fonctionnalités incorrectes),
suivi de deux demandes concrètes issues de cet audit — corriger le
point trouvé sur les polices non disponibles hors-ligne, et ajouter un
bouton "Minuteur" autonome dans Accueil → Outils.

**Audit lui-même** : suite de tests existante (7 fichiers) entièrement
relancée, aucune régression. Analyse statique (`console.log` résiduels,
TODO, `alert()` natifs, blocs `catch` vides) : rien trouvé. Cohérence
des 5 fichiers de données ingrédients ↔ les 1030 noms de référence :
parfaite. 25 écrans testés avec de vraies données, y compris cas
limites (recette à champs vides, comparaison, doublons) : aucune
erreur. Un test XSS basique (injection `<script>` dans la recherche) :
correctement neutralisé. Premier lancement avec base de données
entièrement vide : aucun crash.

**Fausse piste creusée puis écartée** : 51 clés de traduction
semblaient inutilisées (catégories, unités, difficultés...) — en
réalité toutes utilisées via un mécanisme d'indirection
(`CATEGORY_KEYS`, `UNIT_KEYS`, `DIFFICULTY_KEYS`) que la recherche
automatique par expression régulière ne pouvait pas tracer. Aucun code
mort réel trouvé dans le système de traduction.

**Vraie trouvaille de l'audit, maintenant corrigée** : les polices
(Fraunces/Inter) étaient chargées depuis Google Fonts en ligne
(`@import` dans `styles.css`), contrairement à Tesseract/jsPDF/jsQR,
tous délibérément embarqués localement dans ce projet pour la
fiabilité hors-ligne. Tentative d'embarquer directement les fichiers
de police : **échec technique constaté**, pas de raccourci pris —
récupération d'un fichier de police variable via GitHub explicitement
refusée (`ROBOTS_DISALLOWED`), et le risque de corruption au transfert
d'un fichier binaire dans cet environnement (déjà vécu avec JSZip lors
du chantier de compatibilité des sauvegardes, voir point 50) rendait
toute tentative alternative trop risquée pour être poursuivie sans
garantie de fiabilité.

**Solution de repli retenue, honnête sur sa portée** : mise en cache à
l'exécution dans le service worker, spécifiquement pour les domaines
`fonts.googleapis.com` et `fonts.gstatic.com` (cas particulier ajouté
avant l'exclusion générale des domaines externes, qui reste inchangée
pour tout le reste). Une fois chargée avec succès une première fois
(connecté), la police reste disponible hors connexion ensuite ; seul
un tout premier lancement hors-ligne, avant toute connexion réussie,
affiche encore la police système par défaut. Testé : la logique de
branchement par domaine fonctionne correctement (vérifiée
explicitement pour les deux domaines concernés et pour deux domaines
qui ne doivent pas être affectés), toute la suite de tests existante
relancée sans régression.

**Fenêtre de minuteurs autonome, réutilisant la logique déjà mature du
mode cuisine** (`createCookingTimer`, `renderTimerRow`,
notifications) plutôt que de la réécrire. Nouvelle fonction
`openStandaloneTimers()`, bouton "⏱️ Minuteur" ajouté dans
Accueil → Outils.

**Différence de comportement volontaire par rapport au mode cuisine** :
fermer cette fenêtre ne stoppe PAS les minuteurs en cours — ils
continuent de tourner (l'utilisateur peut naviguer ailleurs dans
l'app), la notification prévient le moment venu, plutôt que d'être
annulés comme à la fermeture d'une session de cuisine.

**Point technique résolu pour permettre cette persistance** :
`renderTimerRow` modifiée pour se reconnecter proprement à un minuteur
déjà en cours ou déjà en train de sonner (fenêtre refermée puis
rouverte) — sans ce correctif, le nouvel affichage serait resté figé
sur l'ancienne valeur, l'intervalle précédent continuant de mettre à
jour une ligne devenue invisible plutôt que celle-ci. **Testé
concrètement** : un minuteur démarré à 05:00, fenêtre fermée, 1,5
seconde d'attente en arrière-plan, fenêtre rouverte — affiche
correctement "04:59" et `running: true`, pas figé ni remis à zéro.

**Bonus trouvé en réutilisant l'en-tête du mode cuisine** : le bouton
"✕ Fermer" débordait visuellement de son cercle fixe de 40px (prévu
pour un seul caractère, pas pour icône + mot) — **bug préexistant du
mode cuisine, indépendant de cette nouvelle fonctionnalité**, découvert
par ricochet et corrigé pour les deux écrans (largeur automatique
adaptée au contenu plutôt que cercle fixe).

**Test permanent ajouté** (`tests/test_standalone_timers.py`, 5 cas :
ouverture depuis le bouton, ajout d'un second minuteur, dimensionnement
correct du bouton fermer, persistance après fermeture, réaffichage
correct du décompte à la réouverture).

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v199

### 55 — Préparation à la publication sur le Google Play Store

**Contexte** : demande de l'utilisateur d'entamer le chantier de mise
sur le Play Store, après avoir écarté iOS (pas dans le foyer, pas la
cible visée).

**Recherche préalable** : méthode confirmée toujours d'actualité en
2026 — PWABuilder (gratuit, Microsoft), génère un paquet Android via
Trusted Web Activity (TWA). Score Lighthouse ≥80 recommandé, Digital
Asset Links requis pour prouver la propriété du domaine.

**Manifeste amélioré** : ajout d'un champ `screenshots` (4 images,
recommandé par PWABuilder pour une installation enrichie et une fiche
Play Store plus complète) — uniquement sur le manifeste principal
(français), pas sur les 3 manifestes de langue alternatifs (utilisés
pour la localisation de l'invite d'installation dans le navigateur,
sujet distinct de la soumission Play Store).

**4 vraies captures d'écran générées** (1080×2400, résolution
standard téléphone) avec de vraies données de démonstration
réalistes (recette avec photo, allergènes, notes, liste de courses
avec prix) — pas des captures vides ou avec des données de test
minimales.

**Point de vigilance identifié et documenté honnêtement** : le worker
Cloudflare du développeur (`mes-recettes-proxy...workers.dev`, déjà en
HTTPS, vérifié dans le code) traite l'URL saisie par l'utilisateur
lors d'un import de recette par lien — la seule donnée quittant
l'appareil dans toute l'application. Documenté précisément dans la
politique de confidentialité et le guide de déclaration "Sécurité des
données", pour une déclaration Play Console honnête plutôt qu'un
"aucune donnée collectée" trop optimiste ou une déclaration excessive
par excès de prudence.

**4 documents rédigés** :
- `GUIDE_PUBLICATION_PLAY_STORE.md` — guide principal étape par étape
- `FICHE_PLAY_STORE.md` — textes prêts à l'emploi (titre, descriptions),
  comptages de caractères vérifiés précisément par calcul plutôt
  qu'estimés (deux erreurs d'estimation initiales corrigées après
  vérification)
- `POLITIQUE_CONFIDENTIALITE.md` — à héberger en ligne (obligatoire
  pour toute application Play Store, même sans collecte de données)
- `GUIDE_SECURITE_DONNEES_PLAY_STORE.md` — remplissage du formulaire
  Play Console question par question

**Non-régression** : toute la suite de tests existante relancée après
l'ajout des captures au manifeste, aucune régression.

**Ce qui reste à faire par l'utilisateur lui-même** (nécessite un
compte Google et un paiement, hors de portée de cette session) :
création du compte développeur Play Console, passage par PWABuilder
pour générer le paquet signé, hébergement de la politique de
confidentialité en ligne, remplissage final et soumission.

**Version testée** : v199 (pas de changement de code applicatif,
uniquement le manifeste — pas de bump de version nécessaire)

### 56 — Corrections suite à un second audit externe, préparation Play Store *(v200)*

**Contexte** : un second audit indépendant (autre assistant IA,
vérification de la version réellement déployée sur GitHub) a trouvé
plusieurs défauts avant la soumission au Play Store. Chaque point a
été vérifié moi-même avant correction plutôt qu'accepté tel quel — un
point s'est avéré incorrect dans l'audit lui-même (voir plus bas).

**Confirmé et corrigé** :
- **Icônes sans canal alpha** : les 3 icônes étaient en RGB, Google
  Play exige un PNG 32 bits avec alpha pour l'icône 512×512 — converties
  en RGBA (canal alpha entièrement opaque, aucun changement visuel).
- **Ratio des captures d'écran invalide** : 1080×2400 donnait un ratio
  de 2,22:1, au-dessus du maximum autorisé de 2:1 — régénérées à
  1080×1920 (ratio 1,78:1).
- **Image promotionnelle (feature graphic) manquante** : obligatoire
  pour toute fiche Play Store, créée aux dimensions exactes (1024×500,
  RGB sans alpha — exigence inverse de celle de l'icône).
- **Digital Asset Links au mauvais endroit** : mon guide indiquait
  `majogari15.github.io/mes-recettes-mobile/.well-known/`, alors que ce
  fichier doit être à la racine du domaine
  (`majogari15.github.io/.well-known/`) — la vérification se fait sur
  l'origine complète, pas sur un chemin particulier. Nécessite un
  second dépôt GitHub ("dépôt utilisateur", différent d'un "dépôt
  projet"). Guide corrigé en conséquence.
- **Politique de confidentialité et guide "Sécurité des données"
  incomplets** : ne mentionnaient que le Worker Cloudflare du
  développeur pour l'import de recette par lien, alors que le code
  utilise aussi, en repli successif, Jina AI Reader puis trois services
  publics (AllOrigins, CodeTabs, cors.lol) — vérifié directement dans
  le code (`fetchViaJinaReader`, `fetchRecipeDataViaProxies`), confirmé
  exact. Les deux documents corrigés pour mentionner les 5 services au
  total (le Worker et les 4 autres).
- **Politique de confidentialité inaccessible depuis l'application** :
  n'existait qu'en ligne (page GitHub Pages), jamais liée depuis
  l'interface — pourtant exigée par Google Play. Lien ajouté dans le
  pied de page de l'écran Sauvegarde, avec sa propre clé de traduction
  dans les 4 langues.

**Recherché puis considéré à tort par le premier audit** :
- **`icone_application.ico`** (usage interne à l'app Windows, sans
  rapport avec ce projet mobile) : non concerné.
- **Vulnérabilité jsPDF 2.5.1** (CVSS 9,6, GHSA-wfv2-pwc8-crg5) :
  recherche confirmant la vulnérabilité réelle, mais **vérifiée non
  exploitable dans ce projet** — le code n'utilise jamais
  `doc.output()` avec les surcharges concernées (`pdfobjectnewwindow`,
  `pdfjsnewwindow`, `dataurlnewwindow`), uniquement `doc.save()`,
  confirmé par recherche exhaustive dans `app.js` (`grep -n
  "\.output("` : aucun résultat). **Tentative de mise à jour vers
  4.2.1 abandonnée** après un problème de transfert de fichier
  (nouvelle tentative accidentellement tronquée, non fonctionnelle) —
  plutôt que de risquer de livrer une bibliothèque PDF cassée, la
  version 2.5.1 fonctionnelle a été restaurée depuis une sauvegarde de
  livraison antérieure, puis retestée avec succès (export PDF réel
  confirmé). **Reste un point ouvert**, sans risque pratique avéré
  compte tenu de l'usage réel du code, à reprendre dans une session
  future avec un moyen de transfert de fichier plus fiable.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression. Export PDF spécifiquement
retesté après la restauration de la version 2.5.1.

**Fichiers ajoutés/modifiés** : `icons/*.png` (canal alpha),
`screenshots/*.png` (ratio corrigé), `feature-graphic.png` (nouveau),
`confidentialite.html` et `POLITIQUE_CONFIDENTIALITE.md` (5 services
mentionnés), `GUIDE_SECURITE_DONNEES_PLAY_STORE.md` (5 services),
`GUIDE_PUBLICATION_PLAY_STORE.md` (emplacement Digital Asset Links
corrigé), `app.js`/`i18n.js` (lien politique de confidentialité).

**Version testée** : v200

### 57 — Lien manifeste rendu visible dans le HTML statique, suite au vrai rapport PWABuilder *(v201)*

**Contexte** : premier passage réel par PWABuilder (v200 déployée) —
2 avertissements remontés : "Add a service worker" et "Add
screenshots", alors que les deux existent bel et bien dans le projet.

**Cause trouvée et corrigée** : le lien `<link rel="manifest">`
n'existait jusqu'ici que créé dynamiquement en JavaScript
(`manifest-loader.js`, pour choisir le bon fichier selon la langue déjà
enregistrée) — absent du HTML brut. Un outil d'analyse qui ne lit pas
le JavaScript exécuté (ou l'exécute trop rapidement) pouvait donc ne
jamais voir de manifeste du tout, expliquant plausiblement pourquoi
son contenu (dont le tableau `screenshots`) n'était pas détecté.

**Corrigé sans casser le multilingue** : un lien manifeste statique
(`id="app-manifest"`, pointant par défaut sur `manifest.json`) ajouté
directement dans `index.html`. `manifest-loader.js` modifié pour
**mettre à jour ce lien existant** plutôt que d'en créer un second —
important, puisque les navigateurs n'utilisent que le premier lien
manifeste rencontré ; en créer un second aurait laissé le lien
statique (toujours en français) prendre le dessus, cassant le
changement de manifeste selon la langue.

**Testé** : lien manifeste bien présent dans le HTML brut avant toute
exécution JS (récupéré directement, sans navigateur) ; un seul lien
au total après exécution (jamais deux) ; mise à jour correcte selon la
langue (français par défaut, anglais si `navigator.language` ou
`localStorage` l'indique).

**Second avertissement ("service worker) analysé mais non modifié** :
code vérifié correct et rapide (enregistrement dès les toutes
premières lignes de `init()`, appelée immédiatement à la fin de
`app.js`, aucune attente longue avant). Recherche confirmant un
problème de détection **documenté et connu** côté PWABuilder lui-même
(plusieurs utilisateurs rapportent exactement ce comportement
incohérent, y compris "fonctionne" puis "ne fonctionne plus" sur le
même site sans changement). Aucune modification de code apportée pour
ce second point — recommandé de relancer l'analyse PWABuilder après
le correctif du manifeste, plutôt que de modifier un code déjà correct
sans certitude que ça change quoi que ce soit.

**Non-régression** : suite de tests existante relancée, aucune
régression.

**Version testée** : v201

### 58 — Corrections suite au rapport PWABuilder complet (paquet Android testé) *(v202)*

**Contexte** : un second audit a réellement testé la v201 déployée dans
PWABuilder (pas seulement une analyse de manifeste) — "Your PWA is
store ready" affiché, mais 2 points bloquants trouvés, plus 3 points
annexes à ne pas négliger avant soumission réelle.

**Confirmé et corrigé** :
- **Dimensions des captures erronées dans le manifeste** : déclarées
  `1080x2400` alors que les 4 fichiers réels font `1080x1920` depuis la
  correction du ratio (point 55) — **oubli de synchronisation de ma
  part**, confirmé en vérifiant les dimensions réelles des 4 fichiers
  avant correction. Les 4 occurrences corrigées.
- **Enregistrement du service worker rendu indépendant du reste de
  l'initialisation** : jusqu'ici enregistré dans `init()` (app.js),
  après `await loadPantryClaims()` — un délai qui, sur un premier
  chargement sans base IndexedDB existante, pourrait dépasser la
  fenêtre de détection d'un outil d'analyse automatisé. Nouveau
  fichier dédié `sw-register-early.js`, chargé en tout premier dans
  `index.html` (avant même le lien manifeste), qui n'enregistre le
  service worker sans rien faire d'autre. La logique existante dans
  `app.js` (détection de mise à jour, forçage de vérification) reste
  inchangée : un second appel à `register()` avec la même URL renvoie
  simplement l'enregistrement déjà en cours, sans conflit ni doublon —
  testé explicitement (enregistrement détecté en 0,05s après
  chargement, aucune erreur).
- **Formulation trop absolue sur la collecte de données** : "elle ne
  collecte aucune donnée personnelle" reformulé pour préciser que
  l'adresse IP reste techniquement visible des services réseau
  sollicités (import par lien, Google Fonts) — une nuance réelle,
  distincte de la collecte active par le développeur.

**Non applicable directement (nécessite une action de l'utilisateur,
pas du code)** :
- Politique de confidentialité déployée encore avec `[complétez la
  date]` et `[votre adresse email]` non remplacés — rappelé à
  l'utilisateur, hors de portée du code puisque ces informations lui
  appartiennent.
- Digital Asset Links toujours en 404 : attendu à ce stade, ce fichier
  ne peut être généré qu'après avoir finalisé l'identifiant de paquet
  Android et la clé de signature dans PWABuilder.
- Réglages de l'assistant Android PWABuilder (pays de la clé, choix
  définitif du Package ID) : réglages de l'outil externe, pas du
  projet.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v202

### 59 — Bouton "Partager" retiré pour la sauvegarde partagée (zip), signalement utilisateur *(v203)*

**Contexte** : l'utilisateur signale que le bouton "Partager" de la
sauvegarde (format compatible Windows, `.zip`) n'ouvre jamais le menu
Android — le fichier part directement dans Téléchargements, sans
passer par le choix d'application.

**Cause confirmée par recherche officielle** : le Web Share API de
Chromium n'autorise que certaines extensions de fichiers (audio,
image, PDF, vidéo, texte) — **les fichiers `.zip` en sont
explicitement exclus**, une restriction de sécurité volontaire
documentée directement dans un commit du code source de Chromium
("we allow only common audio, image, text and video file extensions
[...] this blocks executable files from being shared"). Ce n'est pas
spécifique à un appareil : `navigator.canShare({files:[zipFile]})`
renvoie systématiquement `false` sur Chromium, quel que soit
l'appareil.

**Asymétrie découverte en creusant** : la sauvegarde **classique**
(JSON) contourne déjà ce problème depuis une session précédente — le
fichier est nommé `.txt` avec le type MIME `text/plain` plutôt que
`.json`/`application/json`, `.txt` étant explicitement autorisé.
Cette astuce ne peut pas s'appliquer à la sauvegarde **partagée**
(zip) : un fichier zip ne peut pas être déguisé en texte brut sans
perdre son sens.

**Bug de conception trouvé en creusant** : les deux boutons
"Partager" (classique et partagé) utilisaient la **même** vérification
`canShareFiles`, basée sur un fichier `.txt` de test — jamais sur le
véritable type de fichier partagé. Le bouton de la sauvegarde partagée
s'affichait donc à tort, avec la promesse d'un partage qui échouait
alors systématiquement.

**Corrigé** : vérification séparée `canShareZip` (test avec un fichier
`.zip` réel), utilisée uniquement pour le bouton de la sauvegarde
partagée. Le bouton "Partager" classique reste inchangé (fonctionne
correctement, aucune régression). Le bouton de la sauvegarde partagée
**n'apparaît désormais plus du tout** puisqu'il échouerait toujours —
plus honnête qu'un bouton visible mais systématiquement en échec.
L'utilisateur garde le bouton "Exporter (.zip)" (téléchargement
classique), qui fonctionne normalement.

**Testé** : `navigator.canShare` simulé pour refléter le vrai
comportement Android (accepte `.txt`, refuse `.zip`) — confirmé que le
bouton classique reste affiché et que le bouton partagé disparaît
correctement. Suite de tests existante relancée, aucune régression.

**Version testée** : v203

### 60 — Verrou d'écran (Wake Lock) pour la fenêtre de minuteurs autonome, demande utilisateur *(v204)*

**Contexte** : l'utilisateur signale que le téléphone peut se mettre
en veille et éteindre l'écran pendant qu'un minuteur autonome (Accueil
→ Outils → Minuteur) est actif — contrairement au mode cuisine, qui
empêche déjà ça avec un message d'avertissement.

**Réutilisation complète du système existant** :
`requestWakeLock()`/`releaseWakeLock()` étaient déjà des fonctions
génériques au niveau du module (pas spécifiques au mode cuisine),
directement réutilisables sans modification. Mêmes clés de traduction
que le mode cuisine (`cooking_wake_lock_active`/
`cooking_wake_lock_unavailable`) pour le message affiché — c'est
littéralement la même fonctionnalité, pas la peine d'en dupliquer le
texte.

**Identifiant de session séparé** (`activeStandaloneTimersSessionId`,
distinct de `activeCookingSessionId` du mode cuisine) — par
prudence, pour éviter toute interférence si les deux étaient ouverts
simultanément (cas rare), même mécanisme de "session la plus
récente l'emporte" que le mode cuisine pour gérer les demandes
asynchrones qui se chevauchent.

**Différence assumée avec le mode cuisine** : fermer la fenêtre de
minuteurs autonome continue de NE PAS arrêter les minuteurs (comportement
existant, inchangé — voir point 54), mais **relâche bien le verrou
d'écran**, contrairement aux minuteurs eux-mêmes qui continuent en
arrière-plan. Raisonnement : le rôle du verrou est d'empêcher l'écran
de s'éteindre PENDANT que l'utilisateur regarde activement le
décompte, pas de le maintenir indéfiniment après qu'il soit parti
faire autre chose dans l'app — le minuteur sonnera de toute façon via
la notification, qui fonctionne écran éteint.

**Testé** : ouverture (session activée), fermeture par le bouton
(session désactivée, verrou relâché), réouverture propre (pas de
blocage résiduel), fermeture par la touche Échap (même nettoyage que
le bouton). Message "verrou indisponible" correctement affiché en
environnement de test (l'implémentation native du navigateur refuse
la permission en contexte automatisé — comportement attendu, pas une
erreur du code testé, confirmé en isolant l'appel directement).

**Non-régression** : suite de tests existante relancée, aucune
régression.

**Version testée** : v204

### 61 — Rappel de sauvegarde amélioré : urgence progressive et partage en un clic *(v205)*

**Contexte** : après une recherche approfondie sur la sauvegarde cloud
(Google Drive, Dropbox, sauvegarde automatique Android — voir échanges
avec l'utilisateur, aucune conclusion de code à ce stade, sujet mis de
côté pour l'instant), l'utilisateur a demandé 3 améliorations concrètes
du mécanisme de rappel existant plutôt qu'une nouvelle intégration
cloud.

**1. Urgence progressive** : le rappel de l'accueil reste neutre de 14
à 30 jours (comportement inchangé), devient plus visible avec une
bordure de 30 à 60 jours, puis franchement insistant (couleurs
"danger", message différent) au-delà de 60 jours — sans jamais bloquer
l'usage de l'app, juste une attention croissante. 6 nouvelles clés de
traduction (2 nouveaux paliers × 4 langues... en réalité 2 clés × 4
langues, le palier neutre réutilisant le texte déjà existant).

**2. Partage en un clic depuis le rappel** : auparavant, cliquer sur le
rappel menait seulement à l'écran Sauvegarde, d'où il fallait encore
cliquer sur "Partager". Le fichier de sauvegarde est maintenant
préparé en arrière-plan dès l'affichage du rappel (mis en cache 2
minutes pour éviter de le reconstruire à chaque réaffichage de
l'accueil) — le temps que l'utilisateur remarque le rappel et clique
dessus suffit largement à cette préparation, permettant d'appeler
`navigator.share()` directement au clic, sans `await` entre les deux
(condition nécessaire pour que le geste soit reconnu comme "actif").
Repli sur l'écran Sauvegarde classique si le partage natif n'est pas
disponible sur l'appareil.

**3. Vérification de la complétude du partage classique** : déjà
satisfaite avant toute modification — `BACKUP_STORES` (utilisé par le
bouton "Partager" existant, celui qui fonctionne réellement,
contrairement à celui de la sauvegarde partagée en zip) inclut déjà
`kv`, qui contient le planning actif de la semaine
(`state.weeklyPlan`, stocké via `kvSet("weeklyPlan", ...)`) — confirmé
en remontant la chaîne de chargement/sauvegarde dans le code. Le
partage classique JSON est donc déjà plus complet que le format zip
partagé (qui exclut volontairement planning/menus/listes enregistrées
pour la compatibilité Windows) : aucune modification nécessaire pour
ce point.

**Testé** : les 3 paliers d'urgence (aucun rappel avant 14 jours, texte
et bordure corrects à chaque palier) ; fichier bien préparé en
arrière-plan avant tout clic ; clic avec `canShare` simulé absent
(repli sur l'écran Sauvegarde, confirmé) et simulé présent (partage
direct sans quitter l'accueil, fichier correctement transmis, date de
dernière sauvegarde mise à jour) — testé dans les deux scénarios
séparément pour bien isoler chaque chemin.

**Test permanent ajouté** (`tests/test_backup_reminder.py`, 6 cas).

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v205

### 62 — Quatre corrections OCR, signalées avec preuve à l'appui (photo + PDF généré) *(v206)*

**Contexte** : l'utilisateur a fourni à la fois la photo prise (fiche
recette imprimée, issue d'un précédent export PDF de l'app elle-même)
ET le PDF regénéré après import — permettant de comparer exactement
attendu contre obtenu, plutôt que de deviner. Reproduit fidèlement en
faisant tourner le vrai pipeline OCR (`runOcrOnImage` puis
`parseOcrRecipeText`) sur la photo réelle fournie, pas une simulation.

**1. Nombre de personnes incorrect (1 au lieu de 2)** : la regex de
détection ne gérait pas les nombres décimaux — "2.0 personne(s)"
faisait matcher le "0" isolé après le point plutôt que le "2" avant,
donnant `Math.max(1, 0)` = 1. Corrigée pour capturer la partie entière
avant un éventuel point/virgule décimal.

**2. Contamination de la liste d'ingrédients + description amputée de
ses 2 premières étapes** — la cause la plus subtile trouvée dans cette
session : le mot "préparation" apparaît naturellement au milieu de
l'étape 2 ("Ajouter les zestes blanchis à la préparation."), et l'OCR
l'a isolé sur sa propre ligne à cause d'un retour à la ligne. Ce mot
isolé, se terminant par un point, était pris à tort pour un véritable
en-tête de section ("Préparation :"), au même titre qu'un authentique
en-tête. Conséquence en cascade : la liste d'ingrédients continuait
jusqu'à cette fausse frontière (avalant la ligne de nutrition,
l'en-tête "Description :" et les 2 premières étapes), tandis que la
description ne démarrait qu'après ce même point (amputée des mêmes 2
étapes). Nouvelle fonction `looksLikeGenuineSectionMarker` : une ligne
ne compte comme véritable en-tête que si elle est courte (≤6 mots,
même principe déjà éprouvé par `matchesIngredientTitle`) ET se termine
par ":" plutôt que par un point — sauf exception pour les lignes
contenant "kcal" (valeurs nutritionnelles avec leurs propres données
sur la même ligne que l'en-tête, cas structurellement différent).
"description" et "nutrition estimée" ajoutés aux marqueurs reconnus
(absents jusqu'ici, alors qu'il s'agit précisément du format utilisé
par les propres PDF générés par cette application — donc pertinent
pour la réimportation par photo de ses propres exports).

**3. Allergènes jamais extraits en import photo** : fonctionnalité
manquante (pas un bug) — `parseOcrRecipeText` ne renvoyait aucun champ
`allergens`, contrairement à la fonction équivalente déjà existante
pour l'import par lien (`allerg(?:[eè]ne|en)s?`, dans une fonction
séparée). Ajoutée : recherche d'une ligne "Allergènes :", découpage
par virgule, correspondance par inclusion (normalisée, sans
accents/casse) contre `ALLERGEN_OPTIONS` — "Lait (dont lactose)"
reconnu comme correspondant à l'option "Lactose" de l'application, pas
seulement une égalité stricte du libellé complet. Propagée à travers
`deriveSectionDataForPhoto` (déjà correcte pour le cas "mixed" via
`parseOcrRecipeText` directement) et surtout `mergeMultiPhotoResults`,
qui ne la propageait pas du tout jusqu'ici.

**Piège rencontré en testant ce point précis** : l'OCR a lu
"Allerg**é**nes" (accent aigu) au lieu de "Allerg**è**nes" (accent
grave, orthographe correcte) — ma première regex `[èe]` n'incluait pas
la variante é, laissant passer silencieusement aucun allergène détecté
sur cette relecture précise, alors qu'un test antérieur (OCR non
déterministe d'un run à l'autre) avait fonctionné. Élargie à `[èeé]` —
même correction appliquée aux 2 autres occurrences du même motif
limité trouvées dans le fichier (`OCR_SECTION_BOUNDARY_MARKER`,
`OCR_NON_INGREDIENT_KEYWORDS`), pour cohérence. Un motif similaire mais
symétrique (`[eè]` sans é) existe dans la fonction d'import par URL,
non concerné par ce risque précis (texte web propre, jamais issu d'une
reconnaissance optique) — volontairement laissé inchangé.

**Défaut du script de test lui-même trouvé en cours de route** :
`tests/run_ocr_corpus.py` appelait `detectPhotoSection(parsed)` avec un
seul argument, alors que l'usage réel de l'application en passe
toujours deux (`detectPhotoSection(parsed, rawText)`, voir
`handleNewPhoto`) — écart qui aurait pu masquer d'autres régressions
que celle des allergènes, pas seulement l'affecter elle. Corrigé pour
refléter fidèlement l'usage réel.

**Point non corrigé, expliqué** : la valeur nutritionnelle affichée
tantôt "16g prot.", tantôt "169 prot." selon les essais — confusion
possible entre "g" et "9" par l'OCR lui-même (paire de caractères
connue pour se ressembler), pas un problème de l'analyse de texte.
Sans conséquence pratique désormais : cette ligne entière est
maintenant exclue des ingrédients (voir point 2 ci-dessus), son
contenu n'étant jamais stocké ni réaffiché nulle part dans la recette
finale.

**Nouveau cas de corpus ajouté**
(`tests/ocr-corpus/photo_financiers_recette_complete.json`) — vraie
photo (pas de donnée personnelle, simple fiche recette imprimée),
directement dans le corpus public. Nouveau champ `hasAllergen` ajouté
au lanceur de tests (`run_ocr_corpus.py`) pour vérifier spécifiquement
la détection d'un allergène donné — absent jusqu'ici de ce qui était
vérifiable.

**Testé** : le pipeline complet (OCR réel → analyse → détection de
section → dérivation → fusion multi-photos) sur la vraie photo
fournie, confirmant les 4 corrections ensemble. Tout le corpus OCR
existant (7 cas au total désormais) relancé, aucune régression — y
compris après la correction du défaut du script de test lui-même.

**Non-régression** : toute la suite de tests existante relancée après
chaque changement, aucune régression.

**Version testée** : v206

### 63 — Second test approfondi (4 recettes), en-tête "Recette :" et seuil de détection *(v207)*

**Contexte** : l'utilisateur signale que la v206 n'était pas encore
redéployée (toujours v205 affichée dans l'app) au moment de tester —
le PDF "Financiers" fourni montre donc encore les anciens symptômes
déjà corrigés au point 62, pas une régression. Fournit en plus 3
nouvelles recettes réelles (Riz cantonnais, Pâtes à la carbonara,
Mijoté de dinde au curry HelloFresh), certaines testées deux fois
(détection automatique, puis sélection manuelle de section).

**1. En-tête "Recette :" jamais reconnu, confirmé et corrigé** :
courant sur les fiches du site "de simples recettes" (Riz cantonnais,
Pâtes à la carbonara) — absent de `OCR_INSTRUCTION_MARKER` et
`OCR_SECTION_BOUNDARY_MARKER`, qui ne reconnaissaient que
"préparation/description/étapes/instructions...". Toute la
préparation se retrouvait donc avalée dans la liste d'ingrédients (le
même mécanisme de contamination déjà résolu au point 62, mais
déclenché ici par un mot-clé manquant plutôt que par un faux
positif), la description restant entièrement vide. "recette" ajouté
aux deux marqueurs.

**2. Seuil de détection de section trop strict pour une préparation
courte** — trouvé en testant : même après la correction ci-dessus, la
recette Pâtes carbonara restait classée "ingredients" plutôt que
"mixed" (recette complète), sa préparation ne comptant que 6 lignes
sans étapes numérotées ("1.", "2."...), sous l'ancien seuil de
détection (`> 6 lignes`). **Tentative risquée évitée** : abaisser
directement ce seuil (essayé à titre de test à `> 4`) casse un cas
déjà validé du corpus (`photo3_barramundi_couverture`, dont le bruit
de couverture dépasse alors à tort ce seuil plus bas) — confirmé
empiriquement en relançant tout le corpus avant de considérer ce
changement, pas supposé. **Solution retenue** : nouveau champ
`hasExplicitInstructionMarker` exposé par `parseOcrRecipeText`
(`instrIdx >= 0`), utilisé comme signal supplémentaire et
indépendant — un marqueur explicitement trouvé (pas une simple
estimation par comptage) l'emporte dès 3 lignes de préparation,
sans toucher au seuil existant pour les cas où aucun marqueur n'a
été trouvé.

**3. Cas plus complexe non résolu dans cette session, honnêtement
signalé** : la recette HelloFresh "Mijoté de dinde au curry" (mise en
page à colonnes multiples pour les ingrédients, préparation répartie
sur une grille 2×2 de sous-recettes avec leurs propres sous-titres)
reste mal analysée y compris avec sélection manuelle de section —
nécessite une investigation séparée, plus approfondie, que le temps de
cette session ne permettait pas de mener correctement plutôt que de
risquer une correction précipitée.

**Testé** : les 2 corrections confirmées sur les vraies photos
fournies (Riz cantonnais, Pâtes carbonara) — ingrédients et
description désormais exacts et complets pour les deux, section
correctement détectée "mixed" pour les deux. Tout le corpus existant
(7 cas) relancé après CHAQUE changement, y compris la tentative de
seuil abandonnée — aucune régression sur la version finale retenue.

**Nouveau cas de corpus ajouté**
(`tests/ocr-corpus/photo_riz_cantonnais_recette_header.json`).

**Non-régression** : toute la suite de tests existante relancée,
aucune régression. 8 cas au total dans le corpus désormais.

**Version testée** : v207

### 64 — Section allergènes manquante dans l'export PDF de recette *(v208)*

**Contexte** : après confirmation par l'utilisateur d'avoir bien
réimporté la recette Financiers avec la v207 (extraction des
allergènes fonctionnelle depuis le point 62), les allergènes
n'apparaissaient toujours pas dans le PDF généré. Distinction
importante trouvée : ce n'était pas un problème d'**extraction**
(déjà corrigée), mais d'**export** — deux maillons séparés de la même
chaîne.

**Confirmé** : `drawRecipeContent` (fonction commune à
`exportRecipePdf` et à l'export du livre de cuisine complet)
n'affichait jamais `recipe.allergens`, quelle que soit son origine
(import photo, import par lien, ou saisie manuelle dans le
formulaire) — un champ pourtant déjà affiché à l'écran sur la fiche
recette elle-même (badges colorés), simplement oublié lors de la
construction du PDF. Vérifié par recherche exhaustive dans la
fonction entière (aucune occurrence de "allerg" trouvée).

**Corrigé** : section "Allergènes" ajoutée juste après les
ingrédients (même ordre que sur la fiche recette à l'écran), avant la
description — uniquement si la recette a au moins un allergène
renseigné, pas de section vide sinon. Réutilise `translateAllergen`
et la clé de traduction `recipe_allergens` déjà existantes.

**Testé** : espionnage direct des appels à `doc.text()` (pas seulement
"le PDF se génère sans erreur", qui ne prouve rien sur son contenu)
pour confirmer que "Allergènes" et "Gluten, Lactose" apparaissent bien
dans les commandes de dessin réelles ; confirmé aussi qu'une recette
sans allergène n'affiche aucune section vide ou parasite.

**Test permanent ajouté** (`tests/test_pdf_allergens.py`, 2 cas : avec
et sans allergènes).

**Non-régression** : toute la suite de tests existante relancée,
aucune régression.

**Version testée** : v208

### 65 — Extraction d'ingrédients par coordonnées réelles pour les tableaux à 2 colonnes (fiches HelloFresh) *(v209)*

**Contexte** : reprise du cas HelloFresh "Mijoté de dinde au curry"
mis de côté au point précédent — ses ingrédients sont présentés dans
un vrai **tableau à 2 colonnes visuelles** (nom à gauche, quantité à
droite), pas une liste à puces, ce qu'aucune analyse existante ne
savait interpréter correctement.

**Première tentative, abandonnée après test** : séparer le texte
linéarisé par l'OCR en deux blocs successifs (tous les noms, puis
toutes les quantités) et les apparier par position. Fonctionnait sur
un passage, échouait sur le suivant, **sur la même photo** — l'OCR
perd parfois le chiffre en tête de quantité ("1 pièce(s)" devient
"pièce(s)") de façon non reproductible, décalant alors tout
l'appariement suivant. Retirée entièrement avant toute intégration
(vérifié : aucun résidu, tout le corpus repassait comme avant) plutôt
que de livrer quelque chose de fiable un coup sur deux.

**Seconde approche, retenue** : reconstruction par les **coordonnées
géométriques réelles** de chaque mot (`bbox.x0`/`x1`, déjà utilisées
par `reconstructTextFromBlocks` pour un autre usage). Chaque ligne
(regroupée verticalement par Tesseract lui-même) est traitée
**indépendamment** — contrairement à la tentative précédente, un
problème sur une ligne ne peut plus jamais décaler les autres.
Principe : la dernière grande coupure horizontale d'une ligne sépare
le nom (avant) de la quantité (après) — la dernière plutôt que la
première, un résidu d'icône en tête de ligne créant parfois sa propre
petite coupure avant le vrai nom.

**Nouvelles fonctions** :
- `reconstructTableRowsFromBlocks(data)` — produit un texte "nom |
  quantité" par ligne, exposé comme nouveau champ `tableText` au même
  niveau que `rawText`/`layoutText`/`gridText`
- `parseTableRowsIngredients(tableText)` — transforme ce texte en
  ingrédients ; la partie quantité est analysée isolément (réutilise
  la reconnaissance d'unité déjà éprouvée de `parseIngredientString`
  via un nom factice, plutôt que de la dupliquer) ; arrêt dès qu'une
  ligne évoque nutrition/nutrition/allergènes (le tableau nutritionnel
  suit toujours les ingrédients sur ce type de fiche — sans cet
  arrêt, ses lignes seraient prises pour de faux ingrédients)

**Intégration prudente dans `deriveSectionDataForPhoto`** : critère de
comparaison différent de celui déjà existant pour `twoColumnIngredients`
— cette extraction vise délibérément MOINS d'éléments mais bien plus
propres (rejette le bruit plutôt que de le compter), un simple
comptage brut la pénaliserait donc à tort face à une liste plus
longue mais pleine de fragments incohérents. Comparaison basée sur le
nombre d'éléments avec une quantité effectivement reconnue,
préférée même à égalité si elle produit moins d'éléments au total
(meilleure proportion, moins de bruit).

**Résultat concret sur la vraie photo** : 11 ingrédients propres et
correctement nommés (contre une liste de 14 entrées largement
incohérentes auparavant — "0 pièce 7 VE VOS EE ER ORNE PE)" et
similaires) ; nombre de personnes désormais correctement détecté (2,
au lieu du repli par défaut à 4) grâce à l'en-tête "Ingrédients pour 2
personnes" correctement isolé. Reste 2 ingrédients sur 14 non
récupérés (Oignon, Gousse d'ail — perdus dans un chevauchement de
bruit particulièrement mauvais en tout début de tableau) et quelques
unités approximatives (sachet/paquet, pièce/cs) — imperfections
mineures assumées plutôt qu'une régression vers l'ancien
comportement pour les poursuivre.

**Testé** : pipeline complet (OCR réel → détection de section
→ dérivation → fusion multi-photos) sur la vraie photo fournie,
confirmant les 11 ingrédients propres et persons=2 dans le résultat
final fusionné. Tout le corpus OCR existant (8 cas) relancé après
chaque étape, aucune régression. Nouveau test unitaire à données de
coordonnées synthétiques (`tests/test_table_ingredients.py`, 4 cas) —
cette extraction dépend de données géométriques qui ne peuvent pas
être rejouées depuis du texte déjà extrait comme le fait le corpus
OCR habituel, un test unitaire direct sur la structure de données est
donc plus adapté ici.

**Non-régression** : toute la suite de tests existante relancée,
aucune régression.

**Version testée** : v209

### 66 — Vérification élargie sur photos réelles, régression trouvée et corrigée *(v210)*

**Contexte** : demande explicite de l'utilisateur de vérifier plus
largement qu'une amélioration pour un cas ne dégrade pas les autres,
étant donné le nombre et la diversité des utilisateurs réels visés.
Point de méthode important trouvé en y répondant : le corpus de test
habituel (`tests/run_ocr_corpus.py`) rejoue du texte déjà extrait
(`rawText`/`layoutText`), jamais de vraies coordonnées — il n'appelait
donc **jamais** `deriveSectionDataForPhoto` avec un `tableText`, et ne
pouvait donc pas exercer ni protéger le nouveau chemin ajouté au point
65, même en "passant". Un corpus qui passe ne prouve rien sur du code
qu'il n'exerce jamais.

**Vérification menée** : comparaison automatisée, avec et sans le
nouveau chemin d'extraction par tableau, sur les **15 vraies photos**
encore accessibles dans cette session (bien au-delà des 8 cas du
corpus officiel) — measurant précisément si le résultat change, pas
seulement s'il "a l'air correct".

**Régression réelle trouvée** : sur la photo Barramundi (déjà dans le
corpus), une valeur du tableau nutritionnel ("(kifkeal) 2745 /656",
lecture déformée de "(kJ/kcal)") remplaçait à tort un ingrédient réel
en fin de liste — l'arrêt de sécurité ajouté au point 65 ne
reconnaissait pas ce mot-clé nutrition trop déformé par l'OCR pour
matcher littéralement. **Corrigée** en ajoutant la signature
numérique "nombre/nombre" (ex. "2745/656") déjà éprouvée ailleurs dans
le fichier (`extractIngredientsFromLines`, pour cette même raison)
comme signal complémentaire, indépendant du texte de l'en-tête.

**Différence restante, vérifiée comme une amélioration et non une
régression** : sur cette même photo Barramundi, un fragment "1
filet(s)" disparaît de la liste — inspection directe du texte source
confirmant qu'il s'agit d'un résidu isolé n'ayant jamais formé de
vraie paire nom/quantité dans le tableau (pas un ingrédient réel
perdu), contrairement à l'ancienne extraction qui le comptait à tort
comme un 8ᵉ ingrédient.

**Résultat de la vérification élargie, après correction** : sur les 15
photos testées, 14 montrent un résultat **rigoureusement identique**
avec et sans le nouveau chemin (celui-ci ne s'active tout simplement
pas pour elles, laissant le comportement existant totalement
inchangé) ; la seule différence restante (Barramundi) est une
amélioration confirmée, pas une dégradation.

**Nouveau cas de test ajouté** à `tests/test_table_ingredients.py`
(5 cas désormais) — protège spécifiquement cette régression précise
(en-tête nutritionnel trop déformé pour être reconnu littéralement).

**Non-régression** : tout le corpus officiel (8 cas) et le cas Mijoté
du point 65 relancés après la correction, aucune régression.

**Version testée** : v210

### 67 — Amélioration générale de la qualité d'extraction sur 19 vraies photos *(v211)*

**Contexte** : demande explicite de rendre l'extraction aussi complète
et correcte que possible (nom, description, ingrédients, quantités,
personnes) sur les 19 vraies photos identifiées dans l'historique de
la session — pas seulement corriger un cas isolé.

**Filtrage des faux ingrédients "unité seule"** : nouveau filtre
`isUnitOnlyOrTooShortName`, réutilisant la liste d'unités déjà
officielle de l'app (`UNIT_KEYS`) — rejette un "ingrédient" dont le
nom final n'est en réalité que le mot d'unité lui-même ("sachet",
"piéce" seuls, avec ou sans chiffre isolé accolé comme "1 sachet"), ou
un fragment de 1-2 lettres ("E", "ur"). Volontairement limité à ces
cas précis et sans ambiguïté — un nom de 3 lettres reste accepté (riz,
ail, sel, thé sont des ingrédients bien réels). Rejet aussi de "selon
votre goût" isolé (reliquat récurrent de "Poivre et sel selon votre
goût" scindé, jamais un vrai ingrédient à lui seul). Appliqué aux 3
chemins d'extraction photo (`extractIngredientsFromLines`,
`parseTableRowsIngredients`, `parseStackedIngredientColumn`).

**Point-virgule ajouté au bruit toléré en début de ligne**
(`OCR_LEADING_NOISE`) — trouvé sur une vraie photo ("; Par portion
Pour 100g") où ce caractère, absent de la liste jusqu'ici, empêchait
la reconnaissance de "Par portion" comme frontière de section, laissant
une ligne de tableau nutritionnel se glisser parmi les ingrédients.

**Régression trouvée et corrigée pendant ce travail lui-même** : le
correctif du point-virgule ci-dessus, en changeant légèrement le
résultat de l'extraction par tableau sur une autre vraie photo, a fait
disparaître un ingrédient réel ("Gousse d'ail", sans quantité indiquée
sur cette photo précise) — l'extraction par tableau ne peut
structurellement jamais capturer un ingrédient "juste un nom, sans
quantité", puisqu'elle exige une paire nom/quantité par ligne.
Remplacer purement la liste par le résultat du tableau, comme c'était
fait jusqu'ici, risquait donc de perdre silencieusement de vrais
ingrédients dès que l'un d'eux n'a pas de quantité affichée. **Corrigé
par une fusion plutôt qu'un remplacement** : les ingrédients propres
du tableau sont complétés par les ingrédients sans quantité de
l'extraction alternative, absents du tableau (déduplication par
inclusion de sous-chaîne, pas seulement égalité stricte, pour
reconnaître "Chapelure panko" et "Chapelure panko % sachet" comme le
même ingrédient) et dont le nom a une longueur moyenne de mots
plausible (signal déjà utilisé ailleurs dans ce fichier), pour ne pas
réintroduire les fragments de bruit que le tableau avait justement
correctement exclus.

**Testé** : suite de tests existante relancée après chaque changement
(y compris après la régression trouvée puis corrigée), aucune
régression. Nouveau cas de test ajouté à `tests/test_table_ingredients.py`
(6 cas désormais) protégeant spécifiquement ce comportement de
fusion.

**Limites restantes, assumées plutôt que poursuivies indéfiniment** :
quelques fragments de bruit isolés subsistent sur certaines photos
(ex. "nell", "portion" seul) — un filtrage plus agressif risquerait de
rejeter à tort de vrais ingrédients courts sur d'autres recettes, un
compromis jugé plus sûr que de chasser une perfection totale au prix
de nouvelles régressions. Un format "2 ingrédients par ligne"
(rencontré sur une nouvelle recette, "Butternut farcies") reste non
géré — structurellement différent de tout ce qui est actuellement
traité, à considérer comme un chantier séparé.

**Non-régression** : toute la suite de tests existante et le corpus
officiel (8 cas) relancés à plusieurs reprises au cours de ce travail,
aucune régression au résultat final.

**Version testée** : v211

### 68 — Motif "2 ingrédients par ligne" résolu (photo Butternut) *(v212)*

**Contexte** : reprise du cas mis de côté au point 67 — certaines
fiches présentent 2 ingrédients complets (nom+quantité chacun) sur une
même ligne visuelle (ex. "Persil 1/2 bouquet Pois chiches (conserve)
200g"), un motif différent du tableau HelloFresh à 2 colonnes déjà
géré (une seule paire nom/quantité par ligne).

**Géométrie réelle vérifiée avant tout code** : récupération directe
des coordonnées de mots (`bbox`) sur la vraie photo plutôt que
deviner — confirmant 3 grandes coupures horizontales par ligne (pas
1), donnant 4 segments qui s'apparient naturellement 2 à 2 (nom1,
qté1, nom2, qté2).

**`reconstructTableRowsFromBlocks` étendue** : un nombre IMPAIR de
grandes coupures (≥3) donne un nombre PAIR de segments, appariés 2 à 2
comme autant de lignes "nom | quantité" distinctes. Le comportement
existant (1 coupure, ou coupures paires avec repli sur la dernière
pour tolérer un résidu d'icône) reste rigoureusement inchangé —
vérifié explicitement contre le corpus et le test Barramundi déjà en
place avant de continuer.

**Deux ajustements supplémentaires nécessaires, trouvés en testant
contre la vraie photo (pas supposés à l'avance)** :

1. **Arrêt par mot-clé transformé en simple saut de ligne** : cette
   photo mentionne "Valeurs nutritionnelles pour 100g" dans son
   **en-tête**, avant même les ingrédients (contrairement aux fiches
   HelloFresh déjà gérées, où cette mention suit toujours les
   ingrédients) — un arrêt complet à ce stade empêchait d'atteindre les
   vrais ingrédients plus loin dans le texte. Remplacé par un simple
   passage de cette ligne précise (`continue` plutôt que `break`),
   sans arrêter la recherche des lignes suivantes. La signature
   numérique précise (kJ/kcal, "2745/656") reste, elle, un arrêt
   complet — sans ambiguïté possible, contrairement à une simple
   mention de mot-clé.
2. **Démarrage optionnel après un sélecteur de portions** (motif
   "(- 4 personnes | (+)", courant sur les fiches avec réglage +/- du
   nombre de personnes) : sans ce point de départ, les badges/temps de
   préparation précédant les ingrédients étaient pris à tort pour des
   "ingrédients" par l'extraction par tableau. Repli sur un traitement
   dès le début si ce motif précis est absent, pour ne jamais bloquer
   les fiches qui ne l'utilisent pas.

**Résultat concret sur la vraie photo** : les 6 ingrédients désormais
tous correctement extraits avec leurs bonnes quantités (Persil 1/2
bouquet, Pois chiches 200g, Quinoa 100g, Huile d'olive 1 filet, Courge
butternut 2, Cranberry séchée 1 poignée) et le nombre de personnes
correctement détecté (4) — contre seulement 3 ingrédients
incohérents auparavant.

**Testé** : chaque modification vérifiée immédiatement contre le
corpus officiel (8 cas) et le test Barramundi déjà en place avant de
passer à la suivante — aucune étape appliquée à l'aveugle. Toutes les
19 vraies photos de la session relancées après l'ensemble des
changements : les 18 autres montrent un résultat rigoureusement
identique à avant, seule la photo Butternut change (en bien). 3
nouveaux cas de test ajoutés à `tests/test_table_ingredients.py`
(8 cas désormais).

**Non-régression** : toute la suite de tests existante et le corpus
officiel relancés à plusieurs reprises au cours de ce travail, aucune
régression au résultat final.

**Version testée** : v212

### 69 — Sécurité, bugs de quantités, et import par partage *(v213)*

- Faille SSRF corrigée dans le Worker Cloudflare (adresses IPv4
  mappées IPv6 non filtrées par le contrôle anti-réseau-local).
- Les deux fichiers de politique de confidentialité, jusque-là
  divergents, unifiés en un seul, fidèle au code réel.
- Quantités négatives bloquées partout (ingrédients, garde-manger,
  seuils, nutrition, prix), en préservant explicitement le champ vide
  et le 0 (ex. sel/poivre sans quantité précise) — corrige aussi
  l'affichage d'une quantité à 0 sur la fiche recette, jusque-là
  traité comme "aucune quantité".
- `defaultPersons` ne peut plus tomber à 0/négatif.
- Minuteur autonome qui pouvait sonner indéfiniment sans bouton pour
  l'arrêter après ouverture du Mode cuisine, corrigé.
- Renommage/fusion d'ingrédients harmonisés (comparaison normalisée
  dans les deux cas).
- Ajout du Web Share Target : partager un lien de recette depuis une
  autre application ouvre directement l'import, adresse préremplie.

**Vérifié** : les 10 scripts de tests + les 8 cas du corpus OCR (tous
verts), et par des tests manuels en navigateur mobile.

**Version testée** : v213

### 70 — Auto-hébergement des polices Fraunces/Inter *(v214)*

Dernière dépendance réseau externe de l'application supprimée :
Fraunces et Inter (licence SIL OFL) téléchargées et incluses
localement (`lib/fonts/`), remplaçant l'appel à fonts.googleapis.com.
CSP resserrée en conséquence, politique de confidentialité mise à
jour (plus aucune connexion automatique au chargement).

**Vérifié** : zéro requête externe au chargement, rendu visuel
identique, suite de tests complète toujours verte (10 scripts +
corpus OCR).

**Version testée** : v214

### 71 — 5 bugs corrigés dans l'analyseur d'import photo *(v215)*

Trouvés via test réel de l'import photo sur 5 vraies recettes
(Butternut farcies quinoa, Mijoté dinde au curry, Financiers, Pâtes
carbonara, Riz cantonnais) : unités françaises absentes de la liste
reconnue (bouquet, poignée, cm) ; format "Nom Quantité" sans mot
d'unité perdant la quantité ; ":" resté collé en fin de nom
d'ingrédient ; temps combiné "préparation / cuisson" attribué en
entier à la cuisson ; badge de préparation précis écrasé par un temps
total vague de couverture.

**Vérifié sans régression** : les 8 cas du corpus OCR et les 13
suites de tests du projet.

**Version testée** : v215

### 72 — Correction automatique d'orientation pour l'import par photo *(v216)*

Une photo prise à l'envers ou de côté (90°/180°/270°) était jusque-là
illisible par l'OCR. Détection d'orientation dédiée ajoutée (OSD
Tesseract, worker et fichier de données séparés de la reconnaissance
de texte) : la rotation détectée est appliquée avant l'analyse
principale, sans jamais bloquer l'import si la détection échoue.
Mapping degrés vérifié empiriquement avant implémentation, puis testé
de bout en bout sur 4 photos synthétiques à 0/90/180/270°.

**Vérifié sans régression** : corpus OCR et 13 suites de tests.

**Version testée** : v216

### 73 — Tri des recettes + bouton "Signaler un problème" *(v217)*

Tri de la liste de recettes (alphabétique, plus récentes, temps de
préparation, favoris d'abord) — une recette sans temps renseigné
n'est jamais confondue avec "0 minute", poussée en fin de liste sur
le tri par temps. Bouton "Signaler un problème" sur l'écran
Diagnostic : la description saisie est jointe aux informations
techniques puis envoyée via `navigator.share()` (repli sur la copie
presse-papiers si indisponible).

**Vérifié sans régression** : corpus OCR et 13 suites de tests.

**Version testée** : v217

### 74 — Comparaison photo source / résultat après import photo *(v218)*

Bande de miniatures des photos sources en haut du formulaire, visible
juste après un import photo — chaque miniature ouvre une visionneuse
plein écran pour comparer avec le résultat extrait. Bug trouvé et
corrigé pendant le test réel : un sélecteur CSS ambigu plaçait la
miniature dans le texte du label au lieu de la bande dédiée.

**Vérifié sans régression** : corpus OCR et 13 suites de tests.

**Version testée** : v218

### 75 — Recadrage manuel optionnel avant l'OCR (import photo) *(v219)*

Bouton "✂️ Recadrer" optionnel sur chaque carte de la liste de review
d'import photo : cadre à 4 coins glissables, puis nouvelle analyse
OCR sur la zone recadrée, sur la même carte. Vérifié de bout en bout
avec une vraie image à deux zones de texte distinctes et un vrai
glisser-déposer simulé : le texte de la zone exclue disparaît du
résultat, celui de la zone gardée reste.

**Vérifié sans régression** : corpus OCR, 13 suites de tests,
détection d'orientation et comparaison photo source/résultat.

**Version testée** : v219

### 76 — Fusion des unités "sachet"/"pot" dans "boîte" *(v220)*

Ces trois unités-contenants désignaient déjà la même chose en
pratique. Fusionnées en une seule, affichée "boîte/pot/sachet" dans
le menu déroulant et à l'affichage — les variantes reconnues à
l'import (sachet, pot, boîte, conserve, paquet, dose/dosen, lata...)
restent inchangées, seule l'unité résultante change. Migration
automatique des recettes, du garde-manger, de la liste de courses et
des listes enregistrées déjà sauvegardées avec les anciennes unités
séparées.

**Version testée** : v220

### 77 — 9 défauts corrigés suite à un second avis sur la v220 *(v221)*

Un second avis détaillé (autre IA), ayant testé la v220 sur une copie
isolée du dépôt, a trouvé 9 défauts réels dans la fusion des unités
et le recadrage manuel — chacun vérifié ici par exécution réelle
avant correction, pas seulement à la lecture du rapport :

1. Prix personnalisés par ingrédient (`ingredientOverrides`) non
   migrés : le coût redevenait "inconnu" après la fusion des unités.
2. Restauration de sauvegarde incomplète : seules les recettes
   étaient migrées, pas le garde-manger/courses/corbeille/listes
   enregistrées, et seulement au prochain démarrage.
3. Import partagé (QR recette/courses, lien ZIP bureau) conservant
   encore les anciennes unités — menu déroulant d'unité vide dans le
   formulaire pour ces ingrédients.
4. Brouillon de recette non migré à la reprise (même symptôme).
5. Doublons non fusionnés après la conversion des unités (ex.
   "Yaourt/pot" + "Yaourt/sachet" restaient deux lignes séparées au
   lieu d'une seule, quantités additionnées).
6. Miniatures de comparaison photo disparaissant dès le second rendu
   du formulaire (ex. changement de langue en cours d'édition).
7. Cadre de recadrage figé en pixels absolus, ne suivant pas une
   rotation d'écran pendant le recadrage (zone réellement découpée
   différente de la sélection visuelle).
8. Photo originale écrasée par un recadrage, sans retour possible, et
   un échec de la nouvelle analyse OCR bloquait la carte en erreur
   sans conserver le résultat précédent.
9. Fenêtre de recadrage sans les mécanismes d'accessibilité des
   autres fenêtres de l'application (rôle dialogue, touche Échap,
   focus piégé, poignées inutilisables au clavier).

**Vérifié** : chacun des 9 points reproduit puis corrigé
individuellement, avec un script de test dédié par point (avant/après
correction). Suite de régression complète repassée au vert (10
scripts + corpus OCR) après chaque lot de corrections.

**Version testée** : v221

## Résumé — état au 06/09/2026 (v212)

- **jsQR, jsPDF et Tesseract.js désormais tous embarqués localement**
  (jsQR/jsPDF depuis la v141, Tesseract depuis la v165) — plus aucune
  bibliothèque de l'application ne dépend d'un CDN externe. Seules les
  données de langue Tesseract restent téléchargées, mais à la demande
  (au premier import photo dans cette langue), pas au chargement de
  l'application.
- **Tests simulés réussis** : 33
- **Campagne de tests physiques réalisée par l'utilisateur** (2 appareils :
  Smartphone Samsung A06 à jour, Tablette Lenovo Android 11 non à jour)
  — tous les tests du document sont résolus, aucun restant marqué "à
  tester"
- **7 défauts réels trouvés en conditions réelles avant la v131, tous
  corrigés et confirmés** : notes personnelles dupliquées, unités
  absentes du menu déroulant, message trompeur hors connexion, QR
  enregistré en réalité un GIF (cause racine, corrigé en profondeur),
  astuce Google Drive trompeuse, phrase coupée en documentation, partage
  Drive échouant silencieusement (deux causes trouvées et corrigées)
- **Audit complémentaire (v132-v139)**, dix points corrigés et testés :
  1. Diagnostics anciens désormais effacés après une réussite (import,
     partage, Worker)
  2. Code source du Worker Cloudflare versionné dans le dépôt
     (`worker/cloudflare-worker.js`)
  3. Multi-QR réutilisé pour la liste de courses — testé avec 30
     articles, aucune perte
  4. `?importtest=...` restreint à localhost, inoffensif sur le site
     public
  5. Rappel de sauvegarde vérifiant désormais toutes les données
     importantes, pas seulement les recettes
  6. Langue HTML (`<html lang>`) et titre de la page synchronisés à
     chaque changement, y compris au premier chargement
  7. Test physique de l'import par photo (OCR) — laissé à l'utilisateur
  8. 5 traductions mortes retirées (20 entrées, 4 langues)
  9. 2 commentaires obsolètes corrigés (nombre réel d'entrepôts
     IndexedDB, extension du fichier de partage)
  10. Documentation mise à jour (`LISEZ-MOI.md`, politique de
      confidentialité, ce résumé)
- **Cause racine du "Worker qui ne marchait pas"** : un problème
  temporaire côté Cloudflare (cause exacte inconnue, non liée à une
  modification du code) s'est résorbé de lui-même — confirmé via le
  diagnostic que le Worker fonctionne réellement, pas seulement Jina en
  coulisse
- **Mode de test disponible** (`?importtest=jina/proxy/fail`, localhost
  uniquement) pour vérifier les chemins de repli d'import sans jamais
  couper le Worker en production
- **Tests physiques restants** : 2 points confirmés non résolus par
  l'utilisateur (voir section 14) — OCR réel par photo (encore peu
  fiable), import QR par caméra/galerie (encore peu fiable).
  Notification/vibration Android désormais testée (section 19.1) :
  fiable au premier plan uniquement, pas en arrière-plan ni écran
  verrouillé — un correctif partiel (Wake Lock) a été apporté en v155.
  Aucun autre test du document lui-même n'est en attente.
- **Régression trouvée et corrigée après coup** (v152) : le déplacement
  du bouton "Coller le texte d'un QR code" (point 15.5) avait introduit
  une régression — la caméra restait active et deux fenêtres modales
  s'empilaient au clic sur ce lien de secours. Corrigé : caméra arrêtée
  et fenêtre de scan fermée avant d'ouvrir celle de collage.

Aucune régression détectée dans les points explicitement retestés après
chaque correctif. Les 3 points OCR/scan QR/notification ci-dessus restent
authentiquement non résolus ou non testés — ce résumé ne prétend pas le
contraire. Tous les autres défauts trouvés au fil de cette longue
campagne ont été corrigés puis reconfirmés fonctionnels, jamais de perte
de données. L'application est dans un état solide, largement testée en
conditions réelles sur deux appareils, à l'exception des 3 points cités.

## Résumé — état au 16/09/2026 (v222)

Suite directe du résumé v212 ci-dessus (toujours valable pour tout ce
qui précède) — dix versions plus loin (points 69 à 78) :

- **Sécurité et robustesse** : faille SSRF corrigée, quantités
  négatives bloquées partout, dernière dépendance réseau externe
  supprimée (polices auto-hébergées).
- **Import photo nettement amélioré** : 5 bugs d'extraction corrigés
  sur des cas réels, correction automatique d'orientation (photo à
  l'envers/de côté), comparaison photo source/résultat, et recadrage
  manuel optionnel avant l'OCR.
- **Fusion des unités "sachet"/"pot"/"boîte"** en une seule unité
  affichée "boîte/pot/sachet" (v220), suivie de 9 défauts trouvés par
  un second avis externe et corrigés (v221) — voir point 77 pour le
  détail : prix personnalisés, restauration de sauvegarde, import
  partagé, brouillons, fusion des doublons, durée de vie des
  miniatures de comparaison, suivi de rotation d'écran pendant le
  recadrage, préservation de la photo originale, accessibilité de la
  fenêtre de recadrage.
- **Tri des recettes** et **bouton "Signaler un problème"** ajoutés.

**Mise à jour (v222, correctifs supplémentaires)** — voir point 78
ci-dessous : débordement horizontal du formulaire de recette, libellé
erroné du bouton retour du Diagnostic, tests permanents ajoutés pour
la fusion des unités et le recadrage, préservation de l'unité
d'origine (`containerLabel`), hygiène du dépôt (`.gitignore`).

**Réserves encore ouvertes, honnêtement signalées** :
- Les 3 points physiques du résumé v212 (OCR réel par photo, import
  QR par caméra/galerie, notification en arrière-plan) n'ont pas été
  réévalués depuis — ce résumé ne prétend pas qu'ils sont résolus,
  seulement que les points 69-78 ci-dessous ont bien été vérifiés.
- Les captures d'écran de la fiche Play Store (`screenshots/`,
  `feature-graphic.png`) datent de la v200 et n'ont pas été
  régénérées — laissé de côté à la demande explicite.

### 78 — 6 correctifs supplémentaires suite au propre audit du projet *(v222)*

En plus des 9 défauts du point 77 (trouvés par un second avis externe),
un audit du projet lui-même (résidus de code, cohérence i18n, fichiers
de données, écrans testés en direct) avait trouvé 6 autres points,
corrigés ici :

1. **Débordement horizontal du formulaire de recette** : sur un écran
   de téléphone réaliste (390px), la ligne nom/quantité/unité/bouton-
   suppression d'un ingrédient dépassait la largeur de l'écran d'environ 280px
   (`docWidth: 715` vs `viewport: 390`), rendant le bouton de
   suppression hors champ. Cause : un `<select>` refuse de rétrécir
   sous la largeur de son contenu même en `flex-basis: 0`, sans
   `min-width: 0` explicite. Préexistait déjà avant la fusion des
   unités (`docWidth: 669` en v219), seulement aggravé par le nouveau
   libellé plus long ("boîte/pot/sachet").
2. **Libellé erroné du bouton retour du Diagnostic** : affichait
   "← ✕ Fermer" (clé i18n `cooking_close`, prévue pour le mode
   cuisine, réutilisée par erreur) au lieu de "← Retour"
   (`common_back`).
3. **Tests permanents ajoutés** : `test_units_migration.py` (fusion
   des unités, migration des prix/garde-manger/courses/recettes/
   import partagé, fusion des doublons) et
   `test_photo_crop_and_comparison.py` (accessibilité et suivi de
   redimensionnement du recadrage, préservation de l'original,
   conservation du résultat précédent en cas d'échec OCR, durée de
   vie des miniatures de comparaison) — comblent la réserve du point
   77.
4. **Préservation de l'unité d'origine** : un nouveau champ
   `containerLabel` (sur les ingrédients de RECETTE uniquement, pas
   sur les articles de courses/garde-manger) conserve lequel des
   trois mots fusionnés ("boîte"/"sachet"/"pot") était réellement
   utilisé à l'origine — purement informatif, sans influence sur
   l'unité affichée, le menu déroulant ni aucun calcul. Effacé si
   l'utilisateur choisit ensuite une autre unité manuellement (ce
   n'est alors plus "l'unité d'origine ambiguë" mais une décision
   actuelle assumée).
5. **`.gitignore`** complété (`__pycache__/`, `*.pyc`,
   `.pytest_cache/`) — un risque réel constaté : ces fichiers ont
   presque été commités par erreur en lançant les tests Python
   pendant l'audit.
6. **Ce document mis à jour** (points 69 à 78) — s'arrêtait jusqu'ici
   à la v212, huit versions non consignées.

**Vérifié** : chaque point testé en direct (débordement mesuré avant/
après via `getBoundingClientRect`, libellé du bouton lu dans le DOM,
`containerLabel` vérifié sur la reconnaissance à l'import, la
migration de données existantes, l'enregistrement réel via le
formulaire, et l'effacement après changement manuel de l'unité).
Suite de régression complète repassée au vert (12 scripts + corpus
OCR, les 2 nouveaux inclus).

**Version testée** : v222

### 79 — 5 défauts de la fusion des doublons + fabrication évitée sur containerLabel *(v223)*

Un second avis externe, faute d'accès à jour à GitHub, a listé 5
défauts déjà signalés sur la v221 comme "à retester" sur la v222, et a
soulevé deux points supplémentaires sur `containerLabel` (ajouté au
point 78). Les 5 défauts de fusion, vérifiés ici sur le code réel de
la v222 (pas seulement sur le compte rendu), étaient bien encore
présents :

1. **Doublons non fusionnés après restauration** : `sanitizeBackupItem`
   convertit déjà l'unité avant l'écriture — `migrateMergedContainerUnits`
   ne détectait alors plus aucun changement d'unité et sautait la
   fusion, qui était conditionnée à tort à "une unité vient d'être
   convertie DANS CET APPEL". Corrigé : la fusion est désormais
   toujours tentée, jamais conditionnée à ce déclencheur précis.
2. **Fusion mélangeant articles cochés et non cochés** : deux lignes
   "Yaourt/pot coché" et "Yaourt/sachet non coché" fusionnaient en une
   seule ligne, faisant redevenir "à acheter" un article déjà acheté
   (ou l'inverse). Corrigé : le regroupement se fait maintenant aussi
   par état coché/non coché — jamais mélangés.
3. **Quantité inconnue devenant 0** : deux lignes sans quantité
   renseignée (`null`) fusionnaient en une ligne à quantité 0, une
   information fausse ("quantité inconnue" ≠ "aucun besoin"). Corrigé :
   si au moins une des lignes fusionnées a une quantité inconnue, le
   résultat reste `null`, jamais une somme partielle ou 0.
4. **Réservations de garde-manger orphelines** : la fusion supprimait
   des lignes de courses sans réattribuer les réservations
   (`pantryClaimedThisSession`) qui les référençaient encore par leur
   id — une réservation liée à une ligne supprimée continuait à
   réduire à tort le stock disponible pour un article qui n'existait
   plus. Corrigé : chaque réservation est réattribuée à l'id de la
   ligne conservée au moment de la fusion.
5. **Double comptage possible en cas d'interruption** : la mise à jour
   de la ligne conservée et la suppression des doublons se faisaient
   en appels séparés (`storePut` puis `storeDelete`), chacun sa propre
   transaction IndexedDB — une interruption entre les deux pouvait
   laisser la quantité déjà additionnée ET l'original pas encore
   supprimé coexister. Corrigé : nouvelle fonction
   `storePutAndDeleteMany`, une seule transaction IndexedDB pour
   l'ensemble de la fusion (mise à jour et suppressions ensemble,
   jamais l'une sans l'autre).

Deux points supplémentaires sur `containerLabel` (ajouté au point 78),
également corrigés :

6. **Fabrication d'une origine inconnue** : plusieurs points d'entrée
   (import partagé, reprise de brouillon, QR) déduisaient
   `containerLabel` à partir de l'unité courante même quand celle-ci
   était déjà "boîte" — incapable de distinguer un ingrédient qui a
   toujours dit "boîte" d'un autre dont l'origine ("sachet"/"pot") a
   été perdue par une migration antérieure (v220/v221, avant
   l'existence de ce champ). `legacyContainerLabel` ne retourne
   désormais plus jamais "boîte" : seuls "sachet"/"pot" sont des faits
   sûrs (l'unité ne peut valoir l'un des deux QUE s'il s'agit
   réellement, à l'instant de l'appel, de la valeur d'origine pas
   encore convertie) ; une origine réellement irrécupérable reste
   `null`, jamais devinée.
7. **Perte au réexport QR** : le format QR compact n'encodait que
   `[nom, quantité, unité]`, sans `containerLabel` — le réexporter
   vers un autre appareil perdait le souvenir "sachet"/"pot" à
   nouveau. Un 4e élément optionnel transporte maintenant
   `containerLabel` ; les QR déjà en circulation (sans ce 4e élément)
   restent lisibles normalement.

**Vérifié** : chacun des 5 défauts de fusion reproduit puis corrigé
individuellement (dédup après restauration, mélange coché/non coché,
quantité null, réservation orpheline, transaction atomique — cette
dernière en avortant délibérément une transaction pour confirmer que
IndexedDB annule bien la totalité, pas seulement une partie), ainsi
que l'absence de fabrication de `containerLabel` et sa survie à un
aller-retour QR complet. Les 7 cas ont été ajoutés à
`test_units_migration.py` (permanent, pas seulement ponctuel — comblait
une réserve explicitement signalée). Suite de régression complète
repassée au vert (12 scripts + corpus OCR).

**Version testée** : v223

### 80 — Atomicité réservations, mutation différée, `tx.onabort`, tests réels, capture fraîche de "boîte" *(v224)*

Un troisième avis externe, portant cette fois sur la v223 elle-même
(les 5 défauts du point 79 confirmés corrigés), a identifié 5 défauts
plus profonds dans le même mécanisme de fusion :

1. **Réservations encore orphelines en cas d'échec isolé** : la
   réattribution des réservations (`persistPantryClaims()`) était un
   appel séparé de la transaction de fusion des courses — un échec du
   second sans échec du premier laissait la fusion des courses
   appliquée mais les réservations non réattribuées. Corrigé :
   nouvelle fonction `persistShoppingMergeWithClaims`, une seule
   transaction IndexedDB couvrant à la fois l'entrepôt "shopping" et
   l'entrepôt "kv" (où vivent les réservations) — les deux réussissent
   ou échouent ensemble, jamais l'un sans l'autre.
2. **Mutation en mémoire avant confirmation de la persistance** :
   `mergeQuantityGroups` modifiait directement les objets de la liste
   fournie, et `dedupeQuantityListAfterUnitMigration` mettait à jour
   `state.pantryClaimedThisSession` avant même d'avoir écrit en base —
   un échec de persistance laissait alors l'état en mémoire
   désynchronisé de ce qui est réellement stocké. Corrigé :
   `mergeQuantityGroups` retourne désormais des copies (jamais les
   objets d'origine modifiés en place) et `list` /
   `state.pantryClaimedThisSession` ne sont mutés qu'après confirmation
   que la transaction a bien réussi.
3. **`storePutAndDeleteMany` ignorait `tx.onabort`** : si la
   transaction était abandonnée après que toutes ses requêtes aient
   déjà individuellement réussi (aucune erreur de requête à faire
   remonter à `onerror`), ni `oncomplete` ni `onerror` ne se
   déclenchaient — la promesse restait bloquée pour toujours. Reproduit
   précisément (abandon déclenché depuis l'intérieur du gestionnaire
   `onsuccess` d'une requête déjà réussie, pour n'activer QUE
   `onabort`) puis corrigé en ajoutant ce gestionnaire manquant.
4. **Tests ne couvrant pas les fonctions réelles** : le test
   d'atomicité construisait sa propre transaction manuelle au lieu
   d'appeler `storePutAndDeleteMany`, et le test d'aller-retour QR
   reconstruisait lui-même le format compact au lieu d'appeler le code
   d'export réel de l'application — les deux pouvaient donc rester au
   vert même si le vrai code de production régressait. Corrigé : le
   test d'atomicité appelle maintenant `storePutAndDeleteMany` (en
   interceptant temporairement `IDBTransaction.prototype.objectStore`
   pour provoquer un abandon après succès de la requête, sans avoir
   besoin d'une référence à la transaction interne) ; le contenu QR est
   désormais construit par la nouvelle fonction extraite
   `buildCompactRecipeQrPayload` (utilisée aussi bien par
   `openQrCodeModal` que par le test), jamais reconstruit séparément.
5. **"boîte" plus conservé pour un texte source frais** : le correctif
   du point 79 (item 6), en rendant `legacyContainerLabel` plus
   prudent, avait par erreur aussi supprimé la capture de
   `containerLabel="boîte"` lors de l'analyse d'un texte source qui dit
   littéralement "boîte" (ex. "1 boîte de tomates") — un fait observé
   directement dans le texte en cours d'analyse, jamais reconstruit à
   partir d'une valeur déjà stockée et potentiellement déjà fusionnée.
   Corrigé : `parseIngredientStringInner` capture de nouveau
   directement "boîte"/"sachet"/"pot" comme `containerLabel` dans sa
   branche d'analyse de texte frais, tandis que `legacyContainerLabel`
   reste volontairement plus conservateur pour l'autre cas, réellement
   ambigu, de reconstruction depuis une donnée déjà stockée.

**Vérifié** : chacun des 5 défauts reproduit puis corrigé
individuellement, y compris par interception de
`IDBTransaction.prototype.objectStore` pour provoquer un abandon de
transaction précisément après le succès d'une requête (le seul
scénario où `onabort` se déclenche sans jamais déclencher `onerror`),
et par vérification explicite qu'aucune mutation de `state.shopping` /
`state.pantryClaimedThisSession` ne survient avant confirmation de la
persistance. Les 2 tests visés par le point 4 ont été réécrits pour
appeler le code de production réel plutôt que de le reconstruire, et 3
nouveaux cas ont été ajoutés à `test_units_migration.py` (fusion +
réservation avec échec simulé, atomicité réelle de
`storePutAndDeleteMany`, aller-retour QR via le vrai encodeur). Suite
de régression complète repassée au vert (12 scripts + corpus OCR).

**Version testée** : v224

### 81 — Écriture partielle possible sur une erreur SYNCHRONE de préparation de requête *(v225)*

Un quatrième avis externe, portant sur `storePutAndDeleteMany` et
`persistShoppingMergeWithClaims` livrées en v224, a signalé qu'aucune
des deux ne protège ses appels `put()`/`delete()` par un `try/catch`
annulant explicitement la transaction. Une erreur SYNCHRONE pendant la
mise en file d'une requête (ex. `put()` sur un enregistrement sans
identifiant, qui lève immédiatement une `DataError` avant même
qu'IndexedDB ne traite quoi que ce soit) survient avant que
`tx.oncomplete` / `tx.onerror` / `tx.onabort` ne puissent l'annuler :
les requêtes déjà mises en file avant l'erreur n'étaient pas
abandonnées automatiquement et continuaient à s'appliquer normalement,
alors même que la promesse de la fonction rejetait — un « tout ou
rien » rompu sur ce chemin d'erreur précis, distinct du cas déjà
couvert par `tx.onabort` (point 80, item 3).

Reproduit en direct : `storePutAndDeleteMany('shopping', [{id:
'se-1', ...valide}, {...sans id}], [])` rejetait bien avec la
`DataError` attendue, mais l'enregistrement valide `se-1`, mis en file
juste avant l'élément malformé, se retrouvait quand même écrit en
base. Même constat pour `persistShoppingMergeWithClaims` entre les
entrepôts "shopping" et "kv".

Corrigé dans les deux fonctions : les gestionnaires de transaction
(`oncomplete`/`onerror`/`onabort`) sont désormais installés AVANT les
appels `put()`/`delete()`, qui sont eux-mêmes entourés d'un
`try/catch` appelant explicitement `tx.abort()` puis rejetant avec
l'erreur d'origine dès qu'une exception synchrone survient — empêchant
les requêtes déjà en file de s'appliquer malgré tout.

**Vérifié** : les deux fonctions rejettent toujours avec la même
erreur qu'avant le correctif, mais plus aucune écriture partielle
n'est appliquée ni sur l'entrepôt "shopping" ni sur "kv". 4 nouveaux
cas ajoutés à `test_units_migration.py`. Suite de régression complète
repassée au vert (12 scripts + corpus OCR).

**Version testée** : v225

### 82 — Audit complet (code, fonctionnalités, interface, i18n) : 9 défauts corrigés *(v226)*

Un audit complet demandé explicitement (code, fonctionnalités,
interface, erreurs, améliorations), croisant lecture directe du code,
exécution réelle (Playwright) et deux revues indépendantes vérifiées
avant d'être retenues. 9 défauts confirmés et corrigés :

1. **Injection HTML via le champ photo (XSS), atténuée par la CSP** :
   `isValidPhotoField` ne vérifiait que le PRÉFIXE d'une data URL
   ("data:image/...;base64,"), laissant passer n'importe quelle suite
   de caractères ensuite. Combiné à `escapeHtml` (voir point 2), une
   photo de recette (sauvegarde restaurée, import « format partagé »,
   recette reçue) pouvait injecter un attribut HTML arbitraire
   (`onload="..."`) dans `<img src="${recipe.photo}">`, affiché sans
   échappement à 9 endroits. Vérifié en direct : l'attribut injecté
   apparaît bien comme un attribut DOM distinct contrôlé par
   l'attaquant — mais la CSP déclarée dans `index.html`
   (`script-src 'self' 'wasm-unsafe-eval'`, sans `unsafe-inline`)
   bloque déjà son exécution (confirmé par le message d'erreur CSP dans
   la console). Corrigé quand même en profondeur (défense en couches,
   la CSP n'étant qu'une des deux protections) : le regex de
   `isValidPhotoField` est maintenant ancré jusqu'à la fin et limité à
   l'alphabet base64 ; les 9 interpolations de `recipe.photo`/`r.photo`/
   `entry.photo`/`state.formPhoto`/`photoData`/`photoDataUrl` passent
   maintenant par `escapeHtml`.
2. **`escapeHtml` n'échappait jamais les guillemets** : l'ancienne
   implémentation (`div.textContent` → `div.innerHTML`) échappe
   correctement `&`, `<` et `>`, mais PAS les guillemets — alors que
   cette fonction est très souvent appelée À L'INTÉRIEUR d'attributs
   HTML entre guillemets dans tout le fichier (217 appels). Un texte
   contenant un guillemet double (nom de recette, d'ingrédient,
   note...) pouvait donc terminer prématurément l'attribut et injecter
   du HTML arbitraire juste après — vérifié en direct avec un nom
   contenant `" onmouseover="..."`. Corrigé en réécrivant `escapeHtml`
   avec un échappement explicite de `&`, `<`, `>`, `"` et `'`, sûr dans
   les deux contextes (texte ou attribut) et sans effet visible à
   l'affichage (le navigateur les dé-échappe de façon transparente).
3. **`init()` sans aucun `try/catch`** : si `openDB()`/toute opération
   IndexedDB échoue au démarrage (navigation privée stricte, quota
   dépassé, juste après une mise à jour de navigateur), l'écran restait
   totalement blanc, sans texte ni bouton — vérifié en direct en
   simulant cet échec. Corrigé : `init()` délègue maintenant tout son
   travail à `initInner()` sous un `try/catch`, avec un écran de
   secours minimal (`renderStartupError`, volontairement indépendant du
   reste de l'app) affichant un message clair, un bouton "Réessayer" et
   les détails techniques dépliables.
4. **`moveRecipeToTrash`/`restoreRecipeFromTrash` non atomiques** :
   deux écritures séparées (deux transactions distinctes) sans lien —
   un échec entre les deux pouvait dupliquer une recette dans
   "recipes" ET "trash", ou la faire disparaître des deux. Corrigé avec
   une nouvelle fonction générique `moveRecordBetweenStores` (transaction
   unique couvrant les deux entrepôts), sur le même principe que
   `persistShoppingMergeWithClaims` (point 80).
5. **`renameIngredientName`/`mergeIngredientNames` non atomiques et
   mutation prématurée** : propagation d'un renommage à travers jusqu'à
   6 entrepôts (ingredients, recipes, shopping, pantry,
   savedShoppingLists, ingredientOverrides) par écritures séquentielles
   sans lien, avec mutation de `state`/`INGREDIENT_OVERRIDES` avant même
   la persistance. Corrigé avec une nouvelle fonction générique
   `storeWriteManyAcrossStores` (transaction unique quel que soit le
   nombre d'entrepôts) ; les deux fonctions calculent maintenant tous
   les changements SANS toucher à `state`, les écrivent en une seule
   transaction, et ne mutent l'état en mémoire qu'après confirmation.
6. **`saveRecipeForm` sans `try/catch`** : un échec d'écriture (quota
   IndexedDB dépassé, plausible avec une photo en base64) laissait
   croire à tort que la recette avait été enregistrée, l'écran
   naviguant quand même vers la fiche recette. Corrigé : un échec
   affiche maintenant un message d'erreur clair et n'avance ni l'état
   ni l'écran.
7. **Champs quantité/unité illisibles dans le formulaire de recette** :
   sur la ligne d'ingrédient (`.ing-form-row`), le champ nom prenait
   242px sur 358px disponibles (67 %) alors que quantité et unité se
   retrouvaient à 25px et 23px — juste assez pour la flèche du menu
   déroulant, la valeur et l'unité choisies devenant invisibles (bien
   qu'effectivement enregistrées). Cause : `.autocomplete-wrap` (qui
   enveloppe le champ nom) n'avait pas `min-width: 0` contrairement aux
   autres champs de la ligne (corrigés au point 7 initial, v222) — son
   minimum automatique, piloté par la taille intrinsèque du `<input>`
   qu'il contient, écrasait les voisins. Corrigé (`min-width: 0` +
   `width: 100%` sur l'input à l'intérieur) ; vérifié à 390px ET 320px.
8. **"Mo" figé dans l'écran Diagnostic** : `${usedMb} Mo` toujours en
   français quelle que soit la langue affichée. Corrigé avec une
   nouvelle clé `diagnostic_storage_used_value` traduite ("Mo"/"MB").
9. **Tri des recettes par nom incohérent selon l'écran** : 5 endroits
   triaient par nom avec `.localeCompare(b.name, "fr")` figé ou sans
   aucun paramètre de locale, contrairement au tri des ingrédients
   (déjà corrigé pour suivre `CURRENT_LANG`). Corrigé : les 5 sites
   suivent maintenant `CURRENT_LANG`.

Deux pistes signalées mais NON retenues, avec justification : la
traduction espagnole `nav_planning: "Planning"` a été examinée en
détail (16 occurrences de "planning" dans le bloc es, contre une seule
de "planificación" dans un contexte différent) — c'est un choix
délibéré et cohérent dans tout le bloc, pas un oubli, donc laissé tel
quel. Les messages d'erreur d'import bruts en français
(`diagnostic_last_import_error` et apparentés) sont un journal
technique de diagnostic destiné au signalement de bug (mélangé à des
messages d'erreur JS eux-mêmes non traduits, ex. `TypeError:` en
anglais), pas du texte d'interface traduit par conception — laissés
tels quels pour ne pas casser cette cohérence interne.

**Vérifié** : chacun des 9 défauts reproduit puis corrigé
individuellement, y compris par interception de
`IDBTransaction.prototype.objectStore` pour provoquer un abandon de
transaction précis (mêmes techniques que les points 80-81), par
simulation d'un `openDB()` en échec pour le point 3, et par mesure
directe des largeurs de champs pour le point 7. 3 nouveaux fichiers de
test permanents ajoutés (`test_security_hardening.py`,
`test_data_integrity.py`, `test_ingredient_row_layout.py`). Suite de
régression complète repassée au vert (16 scripts + corpus OCR).

**Version testée** : v226

### 83 — Le menu d'autocomplétion d'ingrédient n'apparaissait qu'après la première lettre tapée *(v227)*

Demande explicite de l'utilisateur : dans le formulaire de recette, le
menu de suggestions d'un champ ingrédient (nom) ne s'affichait qu'après
avoir tapé au moins un caractère, alors qu'un simple clic dans le champ
appelait déjà `open()` (géré depuis longtemps via l'événement
"focus"). Cause : `searchIngredientNames("")` renvoie toujours un
tableau vide par construction (une recherche vide n'a pas de sens), donc
`open()` n'avait rien à afficher tant que le champ était vide.

Corrigé dans `attachIngredientAutocomplete` : quand le champ est vide,
`open()` affiche maintenant les 8 premiers noms d'ingrédients connus
(`state.ingredientNames`, déjà maintenu trié par ordre alphabétique
d'affichage partout ailleurs dans l'app) au lieu d'appeler
`searchIngredientNames`. Dès qu'un caractère est tapé, la recherche
normale reprend le relais sans changement de comportement.

**Vérifié** : un clic dans un champ vide affiche désormais 8
suggestions triées alphabétiquement ; taper un texte filtre toujours
correctement (`test_ingredient_autocomplete.py`, nouveau fichier
permanent) ; effacer le texte fait revenir à la liste par défaut au
lieu de rester bloqué sur un menu vide. Suite de régression complète
repassée au vert (17 scripts + corpus OCR).

**Version testée** : v227

### 84 — Ligne d'ingrédient réorganisée + filtre par catégorie sur l'écran Recettes *(v228)*

Deux demandes explicites de l'utilisateur.

**1. Ligne d'ingrédient du formulaire de recette** : la case quantité
pouvait afficher ~7 caractères, l'icône de suppression faisait 44px.
Demandé : réduire la quantité à ~5 caractères, limiter l'affichage à 3
décimales, réduire l'icône de suppression de 30 %, et donner l'espace
ainsi libéré au champ nom.

- `.ing-form-row input.qty` : largeur fixée à `calc(5ch + 10px)`
  (`flex-grow: 0` désormais, ne vole plus d'espace au champ nom) plutôt
  que `flex: 1`.
- Nouvelle fonction `roundQtyForInput` (distincte de `fmtQty`, qui
  utilise la virgule française invalide pour un `<input type="number">`)
  appliquée à la valeur affichée dans ce champ : `0.333333333` devient
  `0.333`.
- `.ing-form-row .remove-ing` : 44px → 31px (icône : 17px → 12px),
  soit -30 % comme demandé.
- `.ing-form-row select` (unité) : passe aussi en largeur fixe
  (`flex: 0 1 82px`, sa taille actuelle) plutôt que `flex: 1.2`, pour
  qu'il ne capte plus une part de l'espace libéré.
- `.autocomplete-wrap` (champ nom) : `flex: 2` → `flex: 1`, devenant le
  seul élément encore extensible de la ligne — il capte donc
  automatiquement 100 % de l'espace libéré par les trois réductions
  ci-dessus.
- Effet de bord découvert et corrigé en vérifiant en direct : les
  flèches natives d'incrémentation d'un `<input type="number">`
  réservent leur propre espace indépendamment de la largeur CSS —
  sur une case déjà réduite à 5 caractères, elles tronquaient
  visuellement le dernier chiffre malgré une largeur par ailleurs
  suffisante (confirmé par mesure : largeur du texte 45px pour une
  case de 56px de contenu, pourtant coupée à l'écran). Corrigé en
  masquant ces flèches sur ce champ précis (`::-webkit-inner/outer-spin-button`),
  inutiles sur un écran tactile.

**2. Filtre par catégorie sur l'écran Recettes**, à gauche du contrôle
de tri existant : nouveau `<select>` (`recipe-category-select`)
listant `CATEGORY_OPTIONS` ("Apéro", "Dessert", "Plat"...) plus une
option "Toutes". Nouvel état `state.recipeCategoryFilter`, appliqué
dans `filteredRecipes()` (une recette sans catégorie renseignée est
traitée comme "Autre", jamais exclue silencieusement — même
convention que l'écran Statistiques) et réinitialisé au changement
d'onglet dans la barre de navigation, comme les autres filtres.

**Vérifié** : mesures directes des largeurs/valeurs à 390px ET 320px
en français ET en allemand (langue la plus longue) — aucun
débordement, aucun retour à la ligne intempestif, arrondi à 3
décimales confirmé, réduction de l'icône confirmée (≤32px), filtre par
catégorie confirmé (y compris le cas "sans catégorie" → "Autre") et sa
réinitialisation au changement d'onglet. 2 nouveaux fichiers de test
permanents (les cas de largeur ont été ajoutés à
`test_ingredient_row_layout.py` existant, plus un nouveau
`test_recipe_category_filter.py`). Suite de régression complète
repassée au vert (18 scripts + corpus OCR).

**Version testée** : v228

### 85 — `storePut`/`storeDelete` ignoraient aussi `tx.onabort` *(v229)*

Dernier point identifié lors de l'audit complet (point 82) mais
volontairement laissé de côté à l'époque comme pré-existant et de
priorité moindre : `storePut`/`storeDelete`, les deux fonctions de base
utilisées à des dizaines d'endroits dans tout le fichier, n'écoutaient
que `oncomplete`/`onerror` — exactement le même défaut déjà corrigé sur
`storePutAndDeleteMany` et les autres fonctions d'écriture multi-entrepôt
(points 80-81, 82). Si la transaction est abandonnée APRÈS que sa seule
requête (le `put`/`delete` unique) a déjà réussi, aucun des deux
gestionnaires ne se déclenche — la promesse restait bloquée pour
toujours dans ce cas précis.

Corrigé en ajoutant `tx.onabort = () => reject(tx.error || new
Error("transaction_aborted"));` aux deux fonctions, à l'identique des
fonctions déjà corrigées.

**Vérifié** : reproduit le même scénario qu'aux points 80-81
(interception de `IDBTransaction.prototype.objectStore` pour abandonner
la transaction depuis l'intérieur du gestionnaire `onsuccess` d'une
requête déjà réussie) sur `storePut` ET `storeDelete` séparément — les
deux promesses restaient bloquées avant le correctif, se
résolvent/rejettent désormais normalement. Cas ajoutés à
`test_data_integrity.py`. Suite de régression complète repassée au
vert (18 scripts + corpus OCR).

**Version testée** : v229

### 86 — Le formulaire de recette ne permettait pas d'importer une photo depuis la galerie *(v230)*

Demande explicite de l'utilisateur : le champ photo du formulaire de
recette n'avait qu'un seul champ de fichier portant l'attribut
`capture="environment"`, qui force les navigateurs mobiles à ouvrir
directement l'appareil photo — impossible de choisir une image déjà
présente sur le téléphone. L'écran d'import photo (OCR) avait déjà
résolu ce même problème avec deux boutons distincts.

Corrigé en appliquant le même motif au formulaire de recette : la zone
d'aperçu (`.photo-upload`) ne contient plus de champ de fichier, deux
boutons apparaissent juste en dessous — "Prendre une photo" (avec
`capture`) et "Choisir depuis la galerie" (sans `capture`, réutilise
les clés i18n déjà existantes `import_photo_add_camera`/
`import_photo_add_gallery`). Les deux déclenchent le même traitement
qu'avant (redimensionnement via canvas, max 800px de large). Les deux
boutons restent disponibles après un premier choix, pour changer la
photo à tout moment.

**Vérifié** : structure du DOM (aucun champ de fichier dans la zone
d'aperçu, exactement 2 champs — un avec `capture`, un sans), sélection
réelle d'un fichier via le bouton Galerie confirmée (`state.formPhoto`
mis à jour, aperçu affiché), boutons toujours visibles après un
premier choix. Nouveau fichier de test permanent
`test_recipe_form_photo_gallery.py`. Suite de régression complète
repassée au vert (19 scripts + corpus OCR).

**Version testée** : v230

### 87 — Même correctif étendu au journal de cuisine ("J'ai cuisiné ça !") *(v231)*

Suite au point 86 : la photo du journal de cuisine avait exactement le
même défaut (`capture="environment"` empêchant l'accès à la galerie),
repéré en même temps mais volontairement laissé de côté (hors du
périmètre demandé), puis confirmé à corriger aussi. Même correctif
appliqué : la zone d'aperçu (`.photo-upload`, `#cooklog-photo-preview`)
ne contient plus de champ de fichier, deux boutons "Prendre une photo"/
"Choisir depuis la galerie" apparaissent juste en dessous, réutilisant
les mêmes clés i18n et le même traitement (redimensionnement canvas,
max 800px) qu'avant.

**Vérifié** : structure du DOM scopée à la fenêtre modale du journal de
cuisine (2 champs de fichier — un avec `capture`, un sans —, aucun à
l'intérieur de la zone d'aperçu), sélection réelle d'un fichier via le
bouton Galerie confirmée (aperçu mis à jour). Cas ajoutés à
`test_recipe_form_photo_gallery.py`. Suite de régression complète
repassée au vert (19 scripts + corpus OCR).

**Version testée** : v231

### 88 — Audit complet (code depuis v226, i18n, fichiers .md/.txt) : 1 bug corrigé, 3 fichiers documentaires mis à jour *(v232)*

Audit complet explicitement demandé, portant cette fois aussi sur les
fichiers `.md`/`.txt` du dépôt (jamais passés en revue jusqu'ici), en
plus du code (points 83-87) et de l'i18n. Trois volets menés en
parallèle et vérifiés avant d'être retenus :

**Code** : un bug réel confirmé — les 4 champs de fichier du nouveau
sélecteur photo (formulaire de recette + journal de cuisine, points
86-87) ne remettaient jamais leur valeur à vide après lecture,
contrairement à l'écran d'import photo/OCR dont ils sont la copie
(`app.js:9886-9887`). Un navigateur ne redéclenche "change" que si la
valeur du champ change réellement : sélectionner de nouveau EXACTEMENT
la même photo via le même bouton ne faisait donc plus rien,
silencieusement. Vérifié en direct (y compris que Playwright reproduit
fidèlement ce comportement natif, permettant un vrai test de
non-régression) puis corrigé en ajoutant `e.target.value = "";` aux 4
gestionnaires. Un second point, théorique (fenêtre de course très
étroite sur `renameIngredientName`/`mergeIngredientNames` si une
action concurrente sur la même recette survient pendant la transaction
en cours), a été signalé mais laissé de côté — la probabilité de le
déclencher via l'interface réelle (modale, donc actions
nécessairement sérialisées) est jugée trop faible pour justifier une
refonte sans décision explicite.

**i18n** : entièrement propre (566/566 clés dans les 4 langues, 680
appels `t()` tous résolus, 8 nouvelles clés bien traduites).

**Fichiers `.md`/`.txt`** (premier audit de ce type sur ce projet) :
`tests/README.md` ne mentionnait aucun des 6 fichiers de test les plus
récents (`test_data_integrity.py`, `test_security_hardening.py`,
`test_ingredient_row_layout.py`, `test_ingredient_autocomplete.py`,
`test_recipe_category_filter.py`, `test_recipe_form_photo_gallery.py`)
— corrigé, une entrée ajoutée pour chacun. `LISEZ-MOI.md` et
`FICHE_PLAY_STORE.md` ne mentionnaient ni l'import de photo depuis la
galerie (v230/v231) ni le filtre par catégorie (v228), et la
description de l'autocomplétion ne mentionnait pas l'ouverture au
clic (v227) — les trois mis à jour. Rien à corriger sur
`POLITIQUE_CONFIDENTIALITE.md`/`confidentialite.html` (identiques et
fidèles aux 5 services externes réellement contactés),
`GUIDE_SECURITE_DONNEES_PLAY_STORE.md`, `lib/LICENSES.md`,
`worker/README.md`, ni sur la cohérence interne de ce présent fichier.

**Vérifié** : le bug du sélecteur photo reproduit puis corrigé (cas
ajouté à `test_recipe_form_photo_gallery.py`, confirmé que Playwright
reproduit fidèlement le comportement natif des navigateurs sur ce
point précis). Suite de régression complète repassée au vert (19
scripts + corpus OCR).

**Version testée** : v232

### 89 — Limite connue et acceptée : fenêtre de course sur renommage/fusion d'ingrédient *(non corrigée, décision explicite)*

Signalé lors de l'audit du point 88 : `renameIngredientName` et
`mergeIngredientNames` calculent d'abord tous les changements à partir
de l'état en mémoire, puis écrivent en une seule transaction
atomique, et ne mettent à jour l'état en mémoire qu'après confirmation
(voir point 82). Entre le calcul et la confirmation, un `await` cède
la main à la boucle d'événements : si une AUTRE opération (mise à la
corbeille, modification d'une personnalisation d'ingrédient...) touche
exactement la même recette/le même ingrédient pendant cette fenêtre,
la transaction du renommage/de la fusion peut réécrire en base une
version désormais périmée — l'état en mémoire de la session en cours
reste correct (grâce aux vérifications `findIndex(...) >= 0`), mais
IndexedDB peut se retrouver avec un enregistrement orphelin ou
resurgi, qui réapparaîtrait au prochain rechargement complet.

**Décision explicite de l'utilisateur : ne pas corriger.** Le vrai
correctif demanderait un verrou global sérialisant toutes les
opérations multi-entrepôt de l'application entre elles (renommage,
fusion, corbeille, courses...) — une refonte touchant 4-5 fonctions
différentes. Le scénario n'est concrètement déclenchable que si
**deux onglets du même navigateur, sur le même appareil**, modifient
la même donnée à la milliseconde près (IndexedDB n'est jamais partagé
entre appareils différents) — quasiment inatteignable en usage normal
d'une application personnelle utilisée sur un seul téléphone. La
complexité et le risque d'un tel verrou dépassent largement le
bénéfice pour ce cas précis.

À reconsidérer seulement si l'application venait à être utilisée
habituellement sur plusieurs onglets/appareils simultanément sur les
mêmes données.

**Version testée** : v232 (non modifiée par ce point)

### 90 — Audit étendu : manques identifiés par rapport à une checklist QA générique (accessibilité, performance, compatibilité, réseau, dépendances)

Suite au point 88 (audit complet code+i18n+docs), l'utilisateur a fourni
une checklist QA générique en 6 catégories (fonctionnel ; interface et
utilisabilité ; technique et compatibilité ; performance et charge ;
sécurité et conformité ; bêta/stores) et demandé une comparaison
honnête avec ce qui avait réellement été couvert. Les manques
identifiés ont ensuite été traités, dans la mesure du possible dans cet
environnement (pas d'appareil réel, pas de vrai lecteur d'écran, pas
d'accès aux stores) :

**1. Accessibilité — jamais testée jusqu'ici.** Audit automatisé avec
axe-core (bibliothèque tierce, ajoutée uniquement pour les tests dans
`tests/vendor/axe.min.js`, jamais chargée par l'application) sur 13
écrans principaux, en thèmes clair et sombre. Deux défauts réels
confirmés et corrigés :
- **Contraste insuffisant en thème sombre** sur tous les boutons/puces
  à texte blanc (`.btn-primary`, `.chip.active`, bouton flottant, bandeau
  d'installation) : 2,4:1 mesuré, minimum WCAG AA 4,5:1. `--primary` en
  thème sombre (`#7BB489`) est volontairement clair pour rester lisible
  comme COULEUR DE TEXTE sur fond sombre (onglet actif...), mais ne
  passait plus le contraste utilisé comme fond avec du texte blanc par-
  dessus. Corrigé en séparant les deux usages : nouvelle variable
  `--primary-strong` (`#3F7A4C` en sombre, identique à `--primary` en
  clair où le problème ne se posait pas) réservée aux fonds à texte
  blanc, `--primary` restant pour le texte (`styles.css`).
- **Contraste limite (4,45:1, sous le seuil 4,5:1) sur les `<select>`
  de filtre/tri de l'écran Recettes** : ces deux `<select>` (ajoutés au
  point 84) n'ont, contrairement à tous les autres champs de
  formulaire, ni `background` ni `color` explicites — ils héritaient
  donc du rendu natif sombre du navigateur (`color-scheme: dark`,
  fond gris ~`#6b6b6b`) au lieu du couple `var(--card)`/`var(--text)`
  déjà utilisé par tous les autres `<select>` de l'application (règle
  `.field select`). Corrigé en ajoutant les mêmes `background`/`color`
  explicites (`app.js`).
- Deux manques structurels supplémentaires (gravité "moderate", sous le
  seuil WCAG AA mais réels) : aucun `<main>`/`<header>` (tout le
  contenu était dans de simples `<div>`, hors de tout repère de
  structure — 292 occurrences relevées par axe-core sur l'ensemble des
  écrans) et 7 écrans secondaires sans titre de niveau 1 (le titre
  était un `<span>`, jamais un `<h1>`, sauf sur l'écran de détail
  recette). Corrigés : le conteneur d'écran (`screenEl`) devient un
  `<main>`, la barre du haut un `<header>`, et le `<span class="subtitle">`
  du titre des écrans secondaires devient un `<h1 class="subtitle">`
  (classe conservée, donc aucun changement visuel — seulement la
  balise). La barre de navigation du bas était déjà un `<nav>`.
- Après ces deux séries de corrections : 0 violation critique/sérieuse
  ni modérée sur les 13 écrans × 2 thèmes ; il reste 2 constats
  "minor" (bruit de fond fréquent avec axe-core sur des composants
  dynamiques, non identifiés précisément, non bloquants).
- **Non fait, limite reconnue** : ceci reste un test AUTOMATISÉ, pas un
  vrai passage avec VoiceOver/TalkBack sur un appareil réel — seul un
  test physique peut confirmer l'expérience réelle au clavier/lecteur
  d'écran. Test permanent : `tests/test_accessibility_audit.py`.

**2. Performance/charge — jamais testée jusqu'ici.** Démarrage à froid
mesuré (~1s), rendu de la liste de recettes avec 300 recettes et 500
ingrédients (~10 ms), filtrage par catégorie sur ce volume (~4 ms),
mémoire JS utilisée (~4 Mo) : aucun problème constaté, seuils larges
volontairement choisis pour détecter une régression franche (ex. un
rendu devenu accidentellement O(n²)), pas pour certifier une
performance absolue. **Non fait, limite reconnue** : pas de mesure
réelle de batterie/RAM sur un vrai appareil, pas de test de charge
"utilisateurs multiples" (non applicable ici, aucun serveur/backend
partagé). Test permanent : `tests/test_performance_basic.py`.

**3. Compatibilité multi-appareils — partiellement testée (390px/320px
téléphone uniquement jusqu'ici).** Ajout de 3 tailles d'écran plus
grandes (tablette portrait 768×1024, tablette paysage 1024×768,
pliable dépliée 673×841) : aucun débordement horizontal ni élément hors
champ constaté (le conteneur `.screen` est déjà centré avec une largeur
maximale de 640px, absorbant naturellement les écrans plus grands).
**Non fait, limite reconnue** : seul le moteur Chromium est disponible
dans cet environnement de test (ni Firefox ni la vraie moteur Safari/
WebKit d'iOS) — la compatibilité multi-navigateurs réelle repose
toujours sur les tests physiques déjà faits par l'utilisateur sur son
smartphone. Test permanent : `tests/test_responsive_large_screens.py`.

**4. Réseau/interruption — jamais testée jusqu'ici.** Coupure réseau
simulée pendant un import de recette par lien (`page.context.
set_offline`) : l'application affiche en quelques secondes un message
d'échec clair et spécifique ("internet semble indisponible..."), sans
rester bloquée sur "en cours" ni lever d'erreur JS, et reste
utilisable normalement une fois le réseau revenu — aucun défaut
trouvé, comportement déjà correct. Test permanent :
`tests/test_network_interruption.py`.

**5. Sécurité/dépendances — audit des bibliothèques tierces embarquées,
jamais fait jusqu'ici.** Recherche de CVE connues sur les 4
bibliothèques vendues localement (`lib/`) :
- **jsPDF 2.5.1 → 4.2.1** : plusieurs CVE réelles affectent 2.5.1,
  notamment CVE-2025-29907 (déni de service par expression régulière
  dans le parsing d'URL de données de `addImage`). Vérifié que
  l'application n'appelle `addImage` qu'avec une image toujours
  regénérée par son propre canvas (`resizeBlobToDataUrl`/
  `canvas.toDataURL`), jamais avec une donnée brute externe : la faille
  n'était donc pas concrètement exploitable ici. Mise à jour effectuée
  quand même par hygiène (aucune API utilisée par l'application —
  `addImage`, `addPage`, `text`, `setFont(Size)`, `setPage`,
  `setTextColor`, `splitTextToSize`, `getImageProperties` — n'a changé
  de comportement ; suite de tests PDF repassée au vert).
- **tesseract.js 7.0.0** : aucune vulnérabilité connue trouvée (à ne
  pas confondre avec le paquet distinct `node-tesseract-ocr`, non
  utilisé ici, concerné par CVE-2026-26832).
- **jsQR** et **qrcode-generator 1.0.3** : aucune CVE connue trouvée.
- **Non fait, limite reconnue** : ceci n'est pas un scan automatisé
  reproductible (pas d'outil `npm audit` utilisable, ces bibliothèques
  étant vendues en fichiers statiques plutôt que via un
  gestionnaire de paquets) — recherche ponctuelle à refaire
  manuellement en cas de doute futur.

**6. Bêta/stores — non fait, hors de portée de cet environnement.**
Aucun accès à TestFlight/Play Console/soumission réelle en store
possible depuis ici. Les captures d'écran Play Store restent, comme
déjà décidé par l'utilisateur, sous sa propre responsabilité.

**Vérifié** : suite de régression complète (22 scripts) au vert après
chaque changement de code, y compris après le remplacement de jsPDF et
les changements de balises (`<main>`/`<header>`/`<h1>`).

**Version testée** : v233

### 91 — Audit de régression fonctionnelle suite au point 90 : 2 bugs de contraste supplémentaires trouvés et corrigés, exports PDF vérifiés de bout en bout

Demande explicite de l'utilisateur après le point 90 : vérifier que les
changements venant d'être faits n'ont pas fait régresser une
fonctionnalité existante. Deux volets :

**1. Deux bugs de contraste réels, de la même famille que ceux du point
90, avaient été manqués** — parce qu'ils n'apparaissent que dans des
états transitoires que le premier audit (13 écrans, mais toujours en
régime "normal") ne déclenchait jamais :
- **Bandeau "mise à jour disponible"** (`state.updateAvailable`,
  affiché quand une nouvelle version est détectée) : son bouton
  utilisait encore `background:#fff; color:var(--primary)`, avec le
  même défaut que `.btn-install` ci-dessous. Corrigé en même temps que
  le fond du bandeau (`var(--primary)` → `var(--primary-strong)`,
  `app.js`).
- **Bandeau d'installation** (proposition d'ajout à l'écran d'accueil,
  déclenché par l'événement natif `beforeinstallprompt`, donc invisible
  dans l'environnement de test automatisé sans le simuler
  explicitement) : deux défauts distincts sur `.install-banner` dans
  `styles.css` —
  - `.btn-install` utilisait `background:#fff; color:var(--primary)`,
    exactement le même problème que ci-dessus (le fond blanc de ce
    bouton est volontairement fixe, indépendant du thème — le texte
    doit donc aussi l'être plutôt que suivre `--primary`, devenu trop
    clair sur blanc en thème sombre). Corrigé en fixant sa couleur à
    `#2F5233` (la valeur de `--primary` en thème clair, jamais
    concernée par le défaut).
  - Le sous-titre (`.text span`) et `.btn-dismiss` atténuaient le blanc
    à 85 % d'opacité pour un effet visuel plus discret — sur le
    nouveau fond `--primary-strong` (thème sombre), ce blanc atténué
    retombait à 4,2:1, sous le minimum 4,5:1. Corrigé en repassant à
    pleine opacité (perte cosmétique minime, contraste garanti).
  - Ces deux bandeaux sont maintenant déclenchés et vérifiés à chaque
    exécution de `tests/test_accessibility_audit.py` (précédemment
    absents de sa boucle d'écrans), pour ne plus jamais les manquer.

**2. Vérification de bout en bout des 3 exports PDF** (recette seule,
liste de courses, livre de cuisine multi-recettes) suite à la mise à
jour de jsPDF au point 90 : jusqu'ici, seul le contenu texte "dessiné"
de la recette seule était vérifié (`test_pdf_allergens.py`) — jamais le
résultat réel de `doc.save()` pour aucun des 3 exports. Nouveau test
`tests/test_pdf_exports_full.py` : les 3 génèrent chacun un vrai
fichier PDF valide (en-tête `%PDF-`, taille non nulle), et le livre de
cuisine (page de garde + sommaire + 3 recettes) est bien nettement plus
gros qu'une recette seule. Aucune régression trouvée.

**Non refait dans ce point** (déjà couvert par les vérifications
existantes, grep de code confirmant qu'aucun autre endroit ne dépend
des anciennes balises `div.screen`/`div.topbar`/`span.subtitle`
remplacées au point 90) : parcours clic réel (thème, création de
recette, navigation) — fait une fois manuellement pendant l'audit,
aucune anomalie, confirmé que la validation existante ("au moins un
ingrédient nommé" avant enregistrement) fonctionne toujours normalement.

**Vérifié** : suite de régression complète (23 scripts + corpus OCR) au
vert.

**Version testée** : v234

### 92 — Checklist PWA spécifique : vérification des points jamais couverts jusqu'ici (installation, hors-ligne à froid, caméra, Lighthouse) — 1 vraie régression de performance trouvée et corrigée

Demande explicite de l'utilisateur : une checklist PWA spécifique (5
catégories : installation/intégration, hors-ligne/service worker,
cross-browser, accès aux fonctionnalités du téléphone, performance
Lighthouse) a été comparée point par point à ce qui avait déjà été
vérifié. Les manques réellement testables dans cet environnement ont
ensuite été vérifiés :

**1. Manifeste PWA** (`tests/test_pwa_manifest.py`) : les 4 manifestes
(fr/en/es/de) sont valides, `display:"standalone"` partout, les 3
icônes existent et font bien les dimensions déclarées (192×192,
512×512, 512×512 maskable), la couleur de thème est identique entre
les 4 manifestes et `index.html`, `manifest-loader.js` sélectionne
bien le fichier selon la langue. Aucun défaut trouvé.

**2. Logique de l'invite d'installation** (`tests/
test_pwa_install_flow.py`) : le vrai événement natif
`beforeinstallprompt` ne se déclenche jamais dans un navigateur
headless (heuristiques d'engagement hors de notre contrôle) — simulé
en le dispatchant nous-mêmes. Vérifié : le bandeau s'affiche à la
réception de l'événement, le clic "Installer" appelle bien `prompt()`
sur l'événement différé, le clic "Non merci" est mémorisé dans
`localStorage` et empêche le bandeau de revenir même après un
rechargement avec un nouvel événement, `isRunningStandalone()` détecte
correctement le mode déjà installé. Aucun défaut trouvé.

**3. Navigation hors-ligne "à froid"** (`tests/
test_pwa_cold_offline.py`) : au-delà de la coupure réseau EN COURS
d'action déjà testée au point 90, ce test attend que le service worker
soit actif et que le cache contienne bien `app.js`, puis coupe le
réseau et **recharge complètement la page** (simulant une fermeture/
réouverture) — y compris via une URL avec un paramètre jamais visitée
avant (proche d'un lien profond ouvert hors-ligne). Vérifié : l'app se
recharge depuis le cache (pas d'erreur navigateur), les données
IndexedDB créées avant la coupure sont toujours là. Aucun défaut
trouvé.

**4. Accès réel à la caméra** (`tests/test_pwa_camera_permission.py`) :
seul `openQrScanModal` (scanner de QR code) appelle vraiment
`getUserMedia` — le sélecteur de photo de recette utilise un simple
`<input type="file" capture>` qui délègue à l'application caméra du
système, sans permission navigateur à tester. Avec une caméra factice
Chromium (`--use-fake-device-for-media-stream`) et la permission
accordée : un vrai flux vidéo s'affiche et débloque la saisie manuelle.
Permission refusée (simulée via un rejet `NotAllowedError`) : message
d'erreur clair affiché, repli "choisir une image" toujours disponible,
pas de plantage. Aucun défaut trouvé.

**5. Audit Lighthouse** : Google a retiré la catégorie notée "PWA" de
Lighthouse à partir de la version 12 (les audits dédiés — manifeste,
service worker, écran de démarrage, icône maskable — n'existent même
plus dans le rapport de la version 13.4.1 installée ici ; seule une
vérification générique de viewport mobile subsiste). Catégories encore
notées vérifiées : **accessibilité 100/100**, **bonnes pratiques
100/100** (cohérent avec l'audit axe-core du point 90).
**Performance : 58/100 — 1 régression de performance réelle trouvée et
corrigée.** `lib/jspdf.umd.min.js` (420 Ko depuis la mise à jour du
point 90, 364 Ko avant) était chargé sans condition via une balise
`<script>` statique dans `index.html`, sur CHAQUE écran de
l'application — y compris tous ceux qui n'exportent jamais de PDF.
Corrigé en le chargeant à la demande (nouvelle fonction
`loadJsPdfLib()`, `app.js`, appelée par les 3 fonctions d'export PDF
avant leur premier usage), exactement sur le modèle déjà utilisé par
`loadJsQrLib()` pour la bibliothèque de scan de QR code. Toujours mis
en cache par le service worker pour un usage hors connexion (inchangé
dans `FILES_TO_CACHE`, `sw.js`). Effet mesuré : premier affichage
utile 7,3s → 5,2s, plus grand affichage de contenu 9,7s → 8,0s,
JavaScript inutilisé au premier chargement 775 Ko → 427 Ko (sous
throttling Lighthouse mobile — ces temps ne reflètent pas les
conditions réelles d'usage, seule l'AMÉLIORATION relative entre avant/
après est significative). Score final : 62/100 — le reste (JS non
minifié, JS inutilisé restant) reflète un choix d'architecture
délibéré et assumé depuis le début du projet (un seul fichier
`app.js` lisible, sans étape de build/minification) plutôt qu'un
défaut ; non modifié sans décision explicite de l'utilisateur.

**Non fait, reste impossible dans cet environnement** (aucune
tentative de simulation trompeuse) :
- **Safari/iOS** : seul le moteur Chromium est disponible ici (déjà
  documenté au point 90) — aucune plateforme Apple n'a jamais été
  testée, ni par moi ni, à ma connaissance, par l'utilisateur.
- **Persistance du stockage après inactivité prolongée sur iOS** :
  comportement réel du système sur plusieurs semaines, impossible à
  simuler fidèlement.
- **Rendu visuel réel une fois l'app installée** (icône sur l'écran
  d'accueil, écran de démarrage) : les DONNÉES qui le déterminent sont
  validées (point 1 ci-dessus), mais le rendu final dépend du système
  d'exploitation réel, jamais vérifié visuellement dans cet
  environnement.
- **Notifications Push** (au sens strict, serveur → navigateur) :
  l'application n'en a pas — seulement des notifications locales
  (minuteurs de cuisine), déjà testées bien avant cette session. Non
  applicable.
- **Background Sync** : aucune action distante à synchroniser dans
  cette architecture 100% locale (IndexedDB). Non applicable.

**Vérifié** : suite de régression complète (27 scripts + corpus OCR)
au vert après le passage en chargement différé de jsPDF, y compris
`test_pdf_allergens.py` et `test_pdf_exports_full.py` adaptés pour
charger explicitement la bibliothèque avant de l'utiliser directement.

**Version testée** : v235

### 93 — Suite au référentiel PWA étendu de l'utilisateur (45 rubriques) : 2 corrections ciblées à coût faible, 1 vrai bug de performance trouvé et corrigé dans les regex maison

Après comparaison de ce référentiel très complet (fourni par l'utilisateur, construit en partie à partir des points 90-92 puis largement enrichi) aux audits déjà menés, 2 corrections immédiates à coût quasi nul ont été appliquées, et une vérification ciblée sur un risque jusque-là jamais testé a révélé un vrai bug de performance :

**1. `rel="noopener noreferrer"` sur le lien externe** (bouton ☕,
`app.js`) : sans ce paramètre, la page ouverte (buymeacoffee.com)
pourrait théoriquement accéder à `window.opener` et rediriger l'onglet
d'origine à l'insu de l'utilisateur ("reverse tabnabbing"). Risque réel
faible ici (destination connue et de confiance) mais corrigé par
principe.

**2. Balise `<noscript>`** ajoutée à `index.html` : filet de sécurité
minimal si un déploiement défectueux venait à casser complètement le
JavaScript avant même l'enregistrement du service worker — message
bilingue (fr/en) explicite plutôt qu'une page blanche silencieuse.

**3. Résistance des fonctions d'analyse de texte MAISON à des entrées
pathologiques (ReDoS)** — jamais testée jusqu'ici, distincte de
l'audit des bibliothèques tierces (point 90/92). Nouveau test boîte
noire (`tests/test_regex_dos_resilience.py`) : plusieurs fonctions
d'analyse (`parseIngredientString`, `parseOcrRecipeText`,
`parseIsoDurationToMinutes`, `parseRecipeFromQrText`,
`parseTableRowsIngredients`, `parseStackedIngredientColumn`) reçoivent
des textes de forme classique pour provoquer un retour arrière
catastrophique (longues répétitions ambiguës suivies d'un caractère ne
correspondant à rien).

**Un vrai bug confirmé et corrigé** : `normalizeUnicodeFractions`
(appelée en tout premier dans `parseIngredientStringInner`, donc à
chaque analyse d'ingrédient) faisait un remplacement global
(`/(\d+\s*)?([½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])/g`) avec un groupe de chiffres
optionnel NON ANCRÉ scanné à chaque position de la chaîne — sur un
texte long sans aucune fraction unicode (ex. une longue suite de
chiffres, plausible depuis un OCR bruité ou un QR corrompu), ce motif
devient quadratique : 20 000 caractères prenaient 3,5 secondes
(mesuré), un temps qui aurait continué à croître avec le carré de la
longueur. Corrigé en ajoutant un test de présence rapide
(`UNICODE_FRACTION_CHARS.test(str)`) avant de lancer le remplacement
coûteux — strictement aucune fraction unicode dans l'immense majorité
des textes réels, donc gain de performance général, pas seulement une
protection contre un cas pathologique. Effet mesuré : 20 000 caractères
adversariaux, 3543ms → 0-1ms sur `parseIngredientString`.

**Amélioration partielle, non totalement corrigée** :
`parseStackedIngredientColumn` reste quadratique sur le même type
d'entrée (4067ms → 530ms à 20 000 caractères après la correction
ci-dessus, qui bénéficie indirectement à son appel interne de
`parseIngredientString` — mais un second motif non ancré,
`/\d+\s*(personnes?|people|persons?|personas?|personen)/i`, répété à
l'identique à plusieurs autres endroits du fichier (détection du
nombre de personnes), reste quadratique sur ce même type d'entrée
pathologique. Reste sous le budget de test (2000ms) à 20 000
caractères et resterait acceptable pour toute taille de texte
réaliste (une ligne de texte OCR ou un fragment de QR n'atteint
jamais cette longueur en usage normal) — corrigé partiellement plutôt
que réécrit intégralement, le gain marginal de traiter chaque
occurrence ne justifiant pas, à ce stade, de revoir une bonne
douzaine d'endroits du fichier pour un vecteur d'entrée aussi extrême.
À revisiter si un jour une vraie voie d'entrée légitime pouvait
produire un texte de cette taille sans retour à la ligne.

**Décision explicite de l'utilisateur, sur ma recommandation** : ne
pas poursuivre l'élargissement du référentiel PWA lui-même (déjà à 45
rubriques, largement suffisant pour la nature de ce projet) ni chasser
les points restants qui nécessitent un vrai appareil iOS, de vrais
utilisateurs non familiers, ou plusieurs semaines d'observation réelle
— ces limites sont déjà documentées aux points 90 et 92 et ne seront
plus reformulées à chaque audit futur. Les points suivants restent
volontairement non testés dans cet environnement, marqués [NA] au sens
du référentiel plutôt que poursuivis artificiellement :
- Glisser-déposer un fichier sur la fenêtre (absent du code, jamais
  demandé, l'app utilise uniquement des boutons de sélection).
- Auto-limitation des appels vers les services tiers publics
  (Jina/proxys CORS) pour éviter un bannissement de l'app elle-même.
- Combinaison précise "même origine ouverte en PWA installée ET en
  onglet navigateur classique simultanément".
- Safari/iOS, appareils physiques, utilisateurs réels non familiers
  (déjà documentés aux points 90/92).

**Vérifié** : suite de régression complète (28 scripts + corpus OCR)
au vert.

**Version testée** : v236

### 94 — Nouvelle fonctionnalité : date de péremption sur le garde-manger

Demande explicite de l'utilisateur (première des 3 étapes proposées —
les deux autres, import par photo et lecture de code-barres, restent
à étudier séparément, non commencées) :

- Champ date de péremption optionnel sur chaque article du
  garde-manger (`item.expirationDate`, format ISO `YYYY-MM-DD`,
  `<input type="date">` dans le formulaire d'ajout/modification déjà
  existant — même endroit que le seuil d'alerte).
- Statut calculé (`getPantryExpirationStatus`) : "expired" (date
  dépassée), "soon" (dans les `PANTRY_EXPIRATION_WARNING_DAYS` = 3
  prochains jours, inclut les expirés), ou aucun (date lointaine ou
  absente).
- Bandeau de rappel sur l'accueil (`getExpiringPantryItems`), même
  principe que le rappel de seuil de stock bas déjà existant mais
  distinct (couleur danger plutôt qu'accent, clic → écran garde-manger
  plutôt qu'ajout direct à la liste de courses, puisqu'ici l'action
  utile est de vérifier/utiliser l'article, pas d'en racheter).
- Affichage dans la liste du garde-manger : suffixe coloré selon
  l'urgence (rouge "expiré le...", orange "expire le...", neutre "à
  consommer avant le..."), rien si aucune date renseignée.
- Nouveau tri "Date de péremption" (sélecteur ajouté sur l'écran
  garde-manger, absent jusqu'ici — seul le tri alphabétique existait) :
  articles les plus urgents en tête, ceux sans date toujours en
  dernier.
- Sauvegarde locale (JSON) : le champ survit automatiquement à un
  export/import, `BACKUP_STORES` copiant chaque entrepôt IndexedDB
  intégralement plutôt que champ par champ — vérifié par un aller-retour
  réel dans le test.
- **Exclusion volontaire, documentée** : le format de partage compatible
  avec l'application Windows (`pantryToSharedFormat`/
  `pantryFromSharedFormat`, utilisé pour le QR code et la sauvegarde
  partagée) ne transporte PAS ce champ — l'application Windows n'a pas
  cette fonctionnalité et ne saurait pas quoi en faire. Un aller-retour
  mobile → partage → bureau → mobile perd donc la date de péremption
  (mais rien d'autre) ; seule la sauvegarde locale (.json, propre à
  l'app mobile) la conserve. Non corrigé sans décision explicite de
  l'utilisateur, puisque cela nécessiterait de faire évoluer aussi
  l'application Windows. Décision volontairement laissée de côté ici.
- Vérifié via axe-core que ni le nouveau bandeau ni le nouveau
  sélecteur de tri n'introduisent de défaut de contraste en thème
  sombre (repéré une fois déjà aux points 90-91 sur des éléments
  similaires) — corrigé d'emblée en reprenant le motif déjà
  contrasté (`background:var(--card);color:var(--text)`) plutôt que
  de le découvrir après coup. Les deux nouveaux écrans/bandeaux sont
  désormais aussi seedés avec de vraies données dans
  `test_accessibility_audit.py`, pas seulement testés vides.

**Non fait dans cette étape** (explicitement reporté par l'utilisateur
à plus tard, après étude d'autres idées) : ajout d'un article et de sa
date par photo (OCR), lecture de code-barres.

**Vérifié** : nouveau test `tests/test_pantry_expiration.py` (ajout
réel via formulaire, 4 statuts, bandeau, clic, affichage coloré, tri,
modification/effacement de la date, aller-retour de sauvegarde) +
suite de régression complète (29 scripts + corpus OCR) au vert.

**Version testée** : v237

### 95 — Nouvelle fonctionnalité : ajout au garde-manger par scan de code-barres

Étape 3 de la demande utilisateur (après la date de péremption,
étape 1) : scanner le code-barres d'un produit pour l'ajouter au
garde-manger, sans créer de doublon avec un ingrédient déjà connu.

**Conception retenue, discutée et validée avec l'utilisateur avant
codage** :
- Le nom trouvé n'est **jamais appliqué automatiquement** : il
  pré-remplit le champ nom du formulaire d'ajout habituel, avec
  l'autocomplétion déjà existante permettant de le rattacher à un
  ingrédient déjà connu plutôt que d'en créer un nouveau.
- Le poids/volume net (si trouvé) est affiché à titre indicatif
  seulement — la quantité réellement suivie reste un nombre de boîtes
  (ou l'unité choisie), cohérent avec le reste de l'app.
- Une fois le nom (et l'unité) choisis pour un code-barres donné,
  l'app s'en souvient localement (`state.barcodeIngredientMap`, dans
  le store `kv` déjà existant) : rescanner le même code-barres
  incrémente directement la quantité de 1, sans jamais rouvrir le
  formulaire.

**Ce qui a été implémenté** :
- `lookupProductByBarcode(barcode)` : interroge Open Food Facts (base
  ouverte et gratuite, aucune clé requise), ne renvoie jamais
  d'erreur — un échec réseau ou un produit inconnu retombe simplement
  sur une saisie manuelle, comme le reste de l'application avec les
  services externes déjà utilisés.
- `openBarcodeScanModal()` : lecture caméra via le détecteur natif du
  navigateur (`BarcodeDetector`, formats `ean_13`/`ean_8`/`upc_a`/
  `upc_e`) — **jsQR (déjà embarqué) ne peut PAS décoder ce type de
  code-barres**, symbologie différente d'un QR code ; sans détecteur
  natif disponible (Safari/iOS notamment), un message explicite
  l'indique et seule la saisie manuelle du code-barres reste possible
  (`openBarcodePasteModal`), plutôt que d'ajouter une nouvelle
  bibliothèque tierce pour ce seul cas.
- `openAddItemModal` étendu avec un paramètre `prefill` (nom/quantité/
  unité/indication, uniquement pour un nouvel article) et un callback
  `onSaved` — réutilise entièrement le formulaire et la logique déjà
  validés plutôt que d'écrire une modale parallèle.
- Bouton d'entrée sur l'écran garde-manger ("📷 Scanner un
  code-barres"), toujours visible (même garde-manger vide).
- 4 langues (fr/en/es/de).

**Un vrai bug trouvé et corrigé pendant l'écriture** (avant tout test,
en relisant la logique) : la mémorisation par code-barres ne retenait
initialement que le NOM choisi, pas l'unité — un produit ajouté une
première fois avec une autre unité que "boîte" (ex. "kg" pour un sac
de riz) aurait fait correspondre les scans suivants sur une fausse
ligne "boîte" plutôt que d'incrémenter la bonne, recréant exactement
le doublon que cette fonctionnalité doit éviter. Corrigé en mémorisant
`{name, unit}` plutôt que le nom seul — couvert par un cas de test
dédié.

**Confidentialité** : nouvel appel réseau externe (Open Food Facts),
documenté dans `POLITIQUE_CONFIDENTIALITE.md`/`confidentialite.html`
(gardés identiques) et `GUIDE_SECURITE_DONNEES_PLAY_STORE.md`, sur le
même modèle que les services déjà utilisés pour l'import de recette
par lien — seul le numéro de code-barres est transmis, jamais l'image
de la caméra ni aucune autre donnée.

**Vérifié** (`tests/test_barcode_pantry.py`, réseau réel jamais
utilisé — requêtes vers Open Food Facts interceptées et remplacées par
des réponses contrôlées) :
- Vrai chemin caméra de bout en bout (caméra factice Chromium +
  détecteur simulé) jusqu'à l'ajout réel au garde-manger.
- Caméra/détecteur indisponible → message clair, repli manuel
  fonctionnel.
- Code-barres manuel trop court refusé.
- Produit trouvé → nom et poids net pré-remplis ; produit non trouvé
  et panne réseau → repli propre sur la saisie manuelle, sans
  plantage.
- Confirmation avec un nom d'ingrédient déjà existant → aucun doublon
  créé.
- Rescan du même code-barres → incrémentation directe (confirmation
  affichée), toujours un seul article.
- Unité différente de "boîte" correctement mémorisée (cas du bug
  ci-dessus) → toujours un seul article après un second scan.
- Mémorisation par code-barres vérifiée sans violation de contraste
  en thème sombre (modale de scan + saisie manuelle), désormais
  couverte à chaque exécution de `test_accessibility_audit.py`.
- Survit à un aller-retour de sauvegarde locale (JSON).

Suite de régression complète (30 scripts + corpus OCR) au vert.

**Version testée** : v238

### 96 — Ajout par code-barres : import depuis une photo (en plus du scan caméra en direct)

Demande explicite de l'utilisateur, à côté du bouton "Scanner un
code-barres" (point 95) : un second bouton pour importer depuis une
photo déjà prise plutôt que d'ouvrir systématiquement la caméra en
direct — utile quand le produit est déjà rangé et difficile à
réatteindre, ou quand une photo existe déjà.

Reprend exactement le motif déjà utilisé pour le scan de QR code
("choisir une image", `decodeQrImageFile`) plutôt que d'inventer une
nouvelle mécanique : chargement du fichier en `data:` URL (technique
déjà en place, plus fiable que `URL.createObjectURL` sur certains
appareils), dessin dans un `<canvas>`, puis le même détecteur natif
que le scan en direct (`BarcodeDetector`, formats EAN/UPC — jsQR ne
peut toujours pas décoder ce type de code). `detectImageMimeType`
(auparavant une fonction interne à `openQrScanModal`) a été hissée au
niveau du module pour être réutilisée par les deux chemins plutôt que
dupliquée.

Résultat identique au scan caméra ensuite (recherche Open Food Facts,
formulaire à confirmer, mémorisation par code-barres) : les deux
boutons alimentent la même fonction `handleScannedBarcode`.

**Vérifié** (mêmes principes que le point 95 — détection simulée,
réseau Open Food Facts intercepté) :
- Code-barres détecté sur une photo → déclenche bien la recherche du
  produit, jusqu'au formulaire pré-rempli.
- Aucun code-barres reconnu sur la photo → message clair, pas de
  plantage.
- Détecteur natif indisponible → message explicite au lieu de tenter
  un décodage impossible.
- Aucun débordement des deux boutons côte à côte à 320px ni 390px de
  large (repassent l'un sous l'autre si nécessaire).
- Aucune violation de contraste critique/sérieuse introduite (thème
  sombre).

Suite de régression complète (30 scripts + corpus OCR) au vert.

**Version testée** : v239

### 97 — Date de péremption : saisie 6 chiffres avec "/" automatiques (remplace le calendrier)

Demande explicite de l'utilisateur : le calendrier natif
(`<input type="date">`) demandait trop de clics sur mobile pour
remplir une seule date. Remplacé par un champ texte (`inputmode`
numérique, clavier numérique direct sur téléphone) où seuls les
chiffres sont retenus (`formatShortDateInput`) — les deux "/" du
format JJ/MM/AA s'insèrent automatiquement après le 2ᵉ et le 4ᵉ
chiffre tapé, sans action de l'utilisateur.

La validation (`parseShortDateToIso`) distingue deux erreurs, chacune
avec un message dédié affiché sous le champ : date incomplète (moins
de 6 chiffres) et date invalide (6 chiffres, mais jour ou mois hors
bornes réelles — ex. "31/02", qui n'existe dans aucun mois). Le
stockage interne (`item.expirationDate`) reste inchangé, au format
ISO habituel — seule la saisie change, pas la donnée mémorisée ni la
sauvegarde locale.

**Vérifié** :
- Les "/" s'insèrent automatiquement après 2 puis 4 chiffres tapés,
  sans que l'utilisateur les tape lui-même.
- Date incomplète (moins de 6 chiffres) → message d'erreur dédié,
  article non enregistré.
- Date calendaire impossible (ex. 31 février) → message d'erreur
  dédié, article non enregistré.
- Date valide → toujours enregistrée correctement au format ISO
  habituel (`item.expirationDate`), comme avant ce changement.
- Pré-remplissage à l'édition toujours correct, désormais au format
  JJ/MM/AA affiché plutôt qu'au format du calendrier natif.
- Champ effaçable (repasse à `null`), comportement inchangé.
- Survit à un aller-retour de sauvegarde locale (JSON), comportement
  inchangé (le format de stockage n'a pas changé).

Suite de régression complète (30 scripts + corpus OCR) au vert.

**Version testée** : v240

### 98 — Message d'erreur caméra spécifique à la cause réelle (permission désactivée / aucune caméra / caméra occupée)

Demande explicite de l'utilisateur : après avoir découvert sur son
téléphone que l'autorisation caméra était désactivée, il a signalé que
le message affiché ("Accès à la caméra refusé ou indisponible.
Vérifiez les autorisations...") ne l'aidait pas à comprendre qu'il
fallait précisément aller réactiver cette autorisation, ni comment s'y
prendre.

`getUserMedia` rejette avec un nom d'erreur distinct selon la cause
réelle (`NotAllowedError` : permission refusée ou désactivée,
`NotFoundError` : aucune caméra sur l'appareil, `NotReadableError` :
caméra déjà utilisée par une autre application) — jusqu'ici, les trois
cas (et tout autre) affichaient exactement le même texte générique.
Une nouvelle fonction `describeCameraError(e)` distingue maintenant
ces trois cas avec un message dédié à chacun, dont un qui explique
précisément le chemin à suivre dans les réglages du téléphone pour
réactiver la permission (`Réglages → Applications → (nom de
l'application) → Autorisations → Appareil photo → Autoriser`) — et
retombe sur le message générique d'origine pour toute autre erreur
inattendue. Partagée par le scan de QR code et le scan de code-barres,
qui utilisaient déjà le même message générique avant ce changement.

**Vérifié** (permission simulée via un remplacement direct de
`getUserMedia`, sans dépendre d'une vraie invite navigateur) :
- `NotAllowedError` → message spécifique "autorisation désactivée",
  avec les étapes pour la réactiver, à la fois pour le scan de QR code
  et le scan de code-barres.
- `NotFoundError` → message spécifique "aucune caméra détectée".
- `NotReadableError` → message spécifique "caméra utilisée par une
  autre application".
- Le repli "choisir une image" reste disponible dans tous les cas.
- Cas normal (permission accordée, caméra factice) toujours
  fonctionnel, sans régression.

Suite de régression complète (30 scripts + corpus OCR) au vert.

**Version testée** : v241

### 99 — Glisser-déposer manuel : liste de courses, garde-manger, ingrédients d'une recette

Demande explicite de l'utilisateur, après l'avoir évoquée comme piste
d'amélioration possible : pouvoir réordonner soi-même une liste (par
exemple dans l'ordre du magasin) plutôt que de dépendre uniquement des
tris automatiques existants (alphabétique, rayon, péremption).

Mécanisme partagé (`attachDragReorder` dans app.js) plutôt qu'une
implémentation distincte par écran : une poignée dédiée (☰) déclenche
le geste via les Pointer Events (jamais l'API HTML5
`dragstart`/`dragover`, non prise en charge du tout au toucher par
Safari iOS sans polyfill) — un clone visuel suit le doigt en position
fixe pendant le glissement, tandis que la vraie ligne, simplement
estompée, n'est déplacée dans le DOM qu'au moment où ce clone franchit
le milieu d'une ligne voisine.

- **Liste de courses** : le bouton de bascule "Trier par rayon/nom"
  est remplacé par un sélecteur à 3 choix (Alphabétique / Rayon /
  Manuel), cohérent avec celui déjà existant du garde-manger. Le tri
  manuel n'impose jamais les articles cochés en fin de liste,
  contrairement aux deux autres tris — c'est justement le seul mode où
  la disposition entière reste à la main de l'utilisateur.
- **Garde-manger** : nouvelle option "Manuel" ajoutée au sélecteur de
  tri existant (Alphabétique / Péremption).
- **Ingrédients d'un formulaire de recette** : toujours disponible
  (pas de sélecteur de mode ici, la liste éditée n'ayant pas d'autre
  tri) ; réordonne le tableau `state.formIngredients` en mémoire, pas
  encore de persistance IndexedDB à ce stade.

Pour les deux premiers, un nouveau champ `order` sur chaque article est
introduit ; les articles créés avant ce changement (ou depuis, dans un
autre tri) reçoivent une valeur de départ dès le premier passage en
tri manuel, calculée à partir de l'ordre d'affichage habituel plutôt
que d'un ordre arbitraire, pour ne pas mélanger la liste sans raison.

**Vérifié** :
- Glisser-déposer effectif sur les 3 écrans (l'ordre affiché change
  bien après le geste).
- Ordre manuel persistant (courses, garde-manger) : survit à un
  rechargement complet de la page ET à un aller-retour de sauvegarde
  locale (export puis import).
- Les tris existants (alphabétique, rayon, péremption) restent
  inchangés par l'introduction du tri manuel — aucune régression sur
  leur comportement propre (notamment les articles cochés toujours en
  fin de liste pour ces tris-là).
- Formulaire de recette : le glisser-déposer réordonne bien à la fois
  l'affichage ET le tableau en mémoire, l'ordre obtenu est celui
  réellement enregistré dans la recette après sauvegarde, et le bouton
  "supprimer" d'une ligne cible toujours le bon ingrédient après un
  glisser-déposer (non-régression d'un bug d'index périmé identifié
  pendant le développement : l'ancien code capturait l'index de
  création de la ligne dans une fermeture jamais mise à jour).
- Aucun débordement horizontal introduit par la nouvelle poignée, à
  320px de large comme à 390px.
- Aucune régression sur l'export PDF de la liste de courses (le mode
  de tri utilisé pour le regroupement par rayon a changé de variable
  interne, sans changement de comportement).

Suite de régression complète (31 scripts + corpus OCR) au vert.

**Version testée** : v242

### 100 — Corrections suite à un audit externe (autre IA), 7 points sur 9 retenus

L'utilisateur a soumis un audit complet rédigé par une autre IA sur
l'ensemble du code. Chaque point a été vérifié moi-même directement
dans le code avant correction plutôt qu'accepté tel quel — 2 points
(sur les 9 soulevés) ont été volontairement écartés à la demande de
l'utilisateur (fiabilité du manifeste dynamique par langue, `alt=""`
sur les photos de recette) après avoir signalé qu'ils étaient
plausibles mais non vérifiables avec certitude ou discutables plutôt
que clairement faux — voir la conversation pour le détail de cette
nuance.

**Corrigé** :
1. **Cache des fichiers JSON de référence** (`sw.js`) : passait en
   "cache d'abord" pur, restant figé indéfiniment tant que `CACHE_NAME`
   n'est pas manuellement incrémenté. Passé en
   "stale-while-revalidate" pour ces fichiers précis uniquement
   (`data/*.json`) : la version en cache répond immédiatement, une
   requête silencieuse en arrière-plan rafraîchit le cache pour la
   prochaine ouverture — les autres fichiers non critiques (polices,
   bibliothèques, moteur OCR) restent en cache-d'abord pur comme avant
   (les revalider à chaque fois gaspillerait de la donnée pour des
   fichiers qui ne changent presque jamais).
2. **Préférence système du thème ignorée au 1er lancement** :
   `applyTheme(localStorage.getItem("theme") || "light")` forçait le
   clair pour quiconque n'avait jamais choisi explicitement, même avec
   le téléphone réglé en sombre. Une nouvelle fonction
   `initThemeFromSystemPreference()` suit maintenant
   `prefers-color-scheme` par défaut, continue de la suivre EN DIRECT
   si elle change pendant l'utilisation, et un choix explicite via
   l'interrupteur (nouveau marqueur `themeSetByUser` dans
   `localStorage`) désactive définitivement ce suivi automatique.
   Migration sans surprise pour les utilisateurs déjà installés : un
   thème sombre déjà enregistré ne pouvait provenir que d'un vrai clic
   (l'app n'a jamais basculé seule en sombre avant ce changement) et
   n'est donc jamais écrasé ; un thème clair déjà enregistré reste
   ambigu (défaut forcé ou vrai choix) et suit désormais l'OS.
3. **Position de défilement jamais restaurée** : `render()` ramenait
   systématiquement en haut de page à chaque changement d'écran,
   y compris un simple retour depuis la fiche d'une recette après
   avoir fait défiler une longue liste. La position de chaque écran
   quitté est maintenant mémorisée (`_scrollPositions`, jamais
   persisté) et restaurée uniquement lors d'un vrai "retour" (bouton
   dédié) — une navigation fraîche (barre du bas, etc.) continue de
   partir du haut comme avant.
4. **Orientation forcée au portrait dans le manifeste** :
   `"orientation": "portrait-primary"` retiré des 4 manifestes de
   langue, pour permettre un usage confortable sur tablette, PC ou
   téléphone posé à plat en mode paysage — l'interface est déjà
   responsive. **Captures d'écran "wide" absentes** : 2 nouvelles
   captures générées (1920×1080, vraies données de démonstration,
   mêmes recettes que les captures "narrow" existantes) et ajoutées au
   manifeste principal, pour que l'invite d'installation sur PC/tablette
   affiche aussi un aperçu.
6. **Téléchargement OCR sans avertissement sur réseau limité** :
   nouveau bandeau (non bloquant) sur l'écran d'import photo, affiché
   uniquement si l'API Network Information signale l'économie de
   données active ET que le modèle de langue Tesseract nécessaire
   n'est pas déjà en cache — l'utilisateur reste libre de continuer
   ou d'attendre le Wi-Fi.
8. **Écouteur `visibilitychange` sans garde contre un double
   appel** : `init()` n'était en pratique jamais appelé deux fois,
   rendant le risque réel nul, mais une garde d'idempotence
   (`_appInitialized`) corrige la cause plutôt que de laisser un
   `removeEventListener` sans point de nettoyage naturel.
9. **Pas de favicon 32×32 dédiée** : `icons/icon-32.png` généré (par
   redimensionnement réel du 192×192 via un `<canvas>`, pas une simple
   copie) et lié explicitement (`sizes="32x32"`) dans `index.html`,
   pour un rendu net dans les onglets/favoris de bureau plutôt qu'un
   redimensionnement à la volée par le navigateur.

**Volontairement écartés (points 5 et 7 de l'audit)** :
- **Fiabilité du manifeste dynamique par langue** (`manifest-loader.js`
  modifie le `href` du `<link rel="manifest">` de façon synchrone,
  juste après le `<link>` dans le HTML) : le risque général décrit
  (un navigateur ignorant un changement tardif) est réel dans
  l'absolu, mais rien ne prouve qu'il s'applique à cette modification
  précoce et synchrone précise — aucun test ne peut vérifier le nom
  réellement proposé dans une vraie invite d'installation sans un
  appareil physique.
- **`alt=""` sur les photos de recette** : techniquement exact, mais
  dans tous les endroits cités le nom de la recette est déjà affiché
  en texte à côté de la photo — `alt=""` (image décorative) y est un
  choix défendable, pas une perte d'information avérée.

**Vérifié** (voir `tests/test_external_audit_fixes.py`, nouveau, et
les ajouts à `tests/test_pwa_manifest.py`) :
- Thème système suivi au 1er lancement (clair et sombre), suivi en
  direct d'un changement d'OS, choix explicite jamais écrasé ensuite,
  et les deux cas de migration (thème déjà enregistré, sombre ou
  clair) se comportent exactement comme prévu.
- Défilement restauré au bouton "retour", jamais lors d'une navigation
  fraîche.
- Fichier JSON de référence : réponse immédiate depuis le cache
  (même volontairement périmée pour le test), cache réellement
  rafraîchi en arrière-plan avec le vrai contenu.
- Bandeau d'économie de données : absent sans l'API ou sans
  l'option active, affiché quand active ET modèle non caché, de
  nouveau absent une fois le modèle mis en cache.
- Second appel à `init()` : aucun nouvel écouteur `visibilitychange`
  posé (idempotence vérifiée directement).
- Manifeste : absence de la clé `orientation` sur les 4 langues,
  présence d'au moins une capture "wide", dimensions et ratio (≤2:1)
  de toutes les captures vérifiés, favicon 32×32 présente et aux
  bonnes dimensions.

Suite de régression complète (32 scripts + corpus OCR) au vert.

**Version testée** : v243

### 101 — Corrections suite à un second audit externe (autre IA), 12 points confirmés

L'utilisateur a fait tester la v243 par une autre IA (lecture du code,
exécution de ses fonctions en environnement isolé, essais dans
l'application publiée). Chaque point a de nouveau été vérifié
moi-même directement dans le code avant correction. Tous les points
signalés se sont révélés exacts.

**Corrigé** :
1. **Mode cuisine : quantités non recalculées selon les convives** —
   confirmé : `recipe.ingredients[i].quantity` est stocké pour 1
   personne (la fiche recette multiplie par `state.viewPersons` pour
   l'affichage), mais `openCookingMode()` ne recevait ni n'utilisait
   ce nombre, affichant toujours la quantité pour 1 seule personne.
   `openCookingMode(recipe, persons)` accepte maintenant ce paramètre
   (transmis depuis la fiche recette), et multiplie chaque quantité en
   conséquence — à défaut de valeur (réouverture depuis une
   notification de minuteur), repli sur `recipe.defaultPersons`.
2. **"Remplacer tout" en ZIP conservait les anciennes recettes** —
   confirmé : `const existing = merge ? await storeAll("recipes") :
   [];` — en mode remplacement, `existing` valait `[]`, donc la
   boucle de suppression qui suivait ne supprimait rien. Corrigé pour
   toujours charger `storeAll("recipes")`, fusion ou remplacement.
3. **Import ZIP partiellement appliqué en cas d'erreur** — confirmé,
   les écritures étaient séquentielles sans validation préalable
   globale. `restoreFromSharedZip()` analyse et convertit maintenant
   l'intégralité de l'archive (JSON + conversion de chaque recette)
   AVANT toute écriture IndexedDB : une entrée invalide fait échouer
   l'import entier, jamais une partie seulement.
4. **Dates de péremption perdues dans le format ZIP partagé** —
   confirmé, `pantryToSharedFormat()` ne recopiait pas
   `expirationDate` dans le dictionnaire exporté. Champ ajouté, dans
   les deux sens.
5. **Articles du garde-manger de même nom écrasés dans le ZIP** —
   confirmé, le dictionnaire exporté n'était indexé que par nom
   (`dict[nom] = {...}`), donc un second article de même nom (ex.
   "Farine" en kg ET en g) écrasait le premier. La clé combine
   maintenant nom ET unité — la FORME de chaque valeur reste
   inchangée pour l'application de bureau (compatibilité conservée),
   seule la clé qui l'index change. Le mode fusion associe désormais
   aussi par nom+unité (au lieu du nom seul) pour la même raison.
6. **Une erreur HTTP pouvait détruire le bon cache** — confirmé,
   `fetch()` ne rejette jamais sur un code d'erreur HTTP (seulement
   sur un échec réseau) : une réponse 500 transitoire sur
   app.js/i18n.js/index.html était mise en cache comme si c'était le
   vrai fichier, et resservie ensuite. `res.ok` est maintenant
   vérifié : une réponse en erreur retombe sur le cache existant sans
   jamais l'écraser.
7. **Péremption incorrecte selon le fuseau horaire** — confirmé,
   `new Date("YYYY-MM-DD")` interprète cette chaîne comme minuit UTC,
   comparée ensuite à minuit LOCAL — décalage d'un jour dans les
   fuseaux à l'ouest de l'UTC (ex. Amérique), où un article expirant
   aujourd'hui apparaissait déjà "expiré". Nouvelle fonction
   `parseCalendarDateLocal()` dédiée, utilisée pour le calcul du
   statut et l'affichage.
8. **Stock augmenté malgré un échec d'enregistrement** — confirmé,
   `addOrIncrementPantryItem()` incrémentait `existing.quantity`
   (objet partagé par référence avec `state.pantry`) AVANT que
   `storePut` soit confirmé — un échec d'écriture laissait quand même
   le stock affiché augmenté. Écrit maintenant une copie d'abord, ne
   modifie l'objet partagé qu'après confirmation.
9. **Suppression de caches d'autres applications du même domaine** —
   confirmé, le nettoyage à l'activation supprimait tout cache
   différent de `CACHE_NAME` exact, sans distinction — risque réel
   pour une autre PWA hébergée sur le même domaine GitHub Pages (Cache
   Storage est partagé par origine, pas par application). Filtré
   maintenant par un préfixe dédié (`mes-recettes-cache-`).
10. **Faux fichier ZIP accepté silencieusement** — confirmé,
    `parseZipFile()` renvoie `[]` sans erreur si la signature ZIP est
    absente, menant à un rapport "0 élément importé" présenté comme
    un succès. `restoreFromSharedZip()` lève maintenant une erreur
    explicite si l'archive ne contient AUCUN des fichiers reconnus.
11. **Glisser-déposer inaccessible au clavier** — confirmé (défaut que
    j'ai moi-même introduit lors de l'ajout de cette fonctionnalité,
    point 99) : poignées en `<span>`, jamais focalisables, et
    `attachDragReorder()` ne gérait que les événements de pointeur.
    Poignées converties en vrais `<button>`, flèches haut/bas
    ajoutées pour réordonner sans geste tactile ni souris.
12. **Libellé des valeurs nutritionnelles ambigu** — confirmé, les
    valeurs sont toujours calculées pour 1 personne, sans que le
    libellé ne le précise, alors que les ingrédients juste au-dessus
    sont affichés multipliés par le nombre de convives sélectionné.
    "par personne" ajouté au libellé (et à sa variante "estimation
    partielle").

**Corrigé par prudence (risque signalé, jamais reproduit)** :
- **`waitUntil()` manquant pour le rafraîchissement en arrière-plan
  (stale-while-revalidate, point 100)** — sans lui, rien n'empêchait
  le navigateur de considérer l'événement "fetch" terminé dès la
  réponse (le cache) renvoyée, risquant de couper le service worker
  avant la fin de la requête de rafraîchissement. Ajouté par
  précaution.

**Test corrigé (masquait un vrai bug)** :
- `test_shared_backup.py` vidait lui-même la base avant de tester le
  mode "remplacer tout", empêchant de jamais détecter que les
  anciennes recettes restaient (point 2 ci-dessus) — puisqu'il n'y
  avait justement plus rien à supprimer au moment du test. Réécrit
  pour laisser une recette différente en place avant l'import, et
  vérifier explicitement sa disparition après.

**Vérifié mais non retenu comme bug** (voir aussi la conversation) :
poids du premier chargement (~54 Mo, les 6 variantes du moteur WASM
Tesseract sont préchargées) — observation valide, mais chantier plus
large volontairement laissé de côté pour l'instant.

**Vérifié** (voir `tests/test_external_audit_fixes_round2.py`, nouveau,
et `tests/test_shared_backup.py`, réécrit) :
- Mode cuisine : la quantité affichée correspond bien au nombre de
  personnes choisi sur la fiche recette (400 g pour 4 personnes,
  cohérent des deux côtés).
- Import ZIP : une entrée invalide n'applique plus rien (recette
  préexistante non affectée, recette valide de la même archive jamais
  importée non plus) ; un faux fichier ZIP lève une erreur explicite ;
  "remplacer tout" supprime réellement les anciennes recettes.
- Garde-manger (ZIP) : 2 articles de même nom mais d'unité différente
  survivent tous les deux à l'aller-retour, avec leur date de
  péremption conservée.
- Service worker : une erreur HTTP simulée (500) sur app.js ne casse
  pas le chargement (repli sur le cache valide) et n'altère jamais ce
  cache ; le cache d'une autre application simulée survit à la
  réactivation du service worker.
- Date de péremption : un article expirant "aujourd'hui" n'est pas
  déjà "expired" dans le fuseau America/New_York.
- Garde-manger : la quantité (mémoire ET IndexedDB) reste inchangée
  après un échec d'écriture simulé.
- Glisser-déposer : la poignée est un vrai `<button>` ; la flèche bas
  déplace bien la ligne d'une position au clavier.
- Libellé nutrition : contient bien "par personne".

Suite de régression complète (33 scripts + corpus OCR) au vert.

**Version testée** : v244

### 102 — Corrections suite à un troisième audit externe (deux autres IA), atomicité réelle du ZIP et dates invalides

L'utilisateur a fait tester la v244 par deux autres IA. La première a
confirmé l'ensemble des corrections du point 101 sans rien trouver de
nouveau. La seconde a démontré, par exécution directe des fonctions
réelles (stockage et réseau simulés), que la protection "tout-ou-rien"
ajoutée au point 101 restait incomplète dans deux scénarios précis
qu'elle ne couvrait pas encore. Chaque point vérifié moi-même dans le
code avant correction.

**Confirmé et corrigé** :
1. **Import ZIP toujours non atomique face à un échec d'ÉCRITURE** —
   confirmé : le point 101 empêchait bien une donnée invalide
   *détectée à l'avance* de déclencher une écriture partielle, mais
   les différentes sections (recettes, ingrédients, garde-manger,
   personnalisations) continuaient à s'écrire dans des transactions
   IndexedDB séparées. Un échec survenant PENDANT l'écriture
   elle-même (quota dépassé, panne...) — pas seulement une donnée
   invalide — pouvait donc encore laisser l'import à moitié appliqué
   (scénario reproduit : ancienne recette supprimée, une seule des
   deux nouvelles recettes écrite avant l'échec). Corrigé en
   réutilisant `storeWriteManyAcrossStores()` (déjà présente dans le
   code, utilisée ailleurs pour le même besoin — ex. fusion de
   doublons de courses) : toutes les écritures de toutes les
   sections sont désormais regroupées dans UNE SEULE transaction
   IndexedDB multi-entrepôts, calculée entièrement en mémoire avant
   la moindre écriture réelle.
2. **Validation de forme encore incomplète** — confirmé : un JSON
   syntaxiquement valide mais de mauvaise forme (ex.
   `ingredients.json` = `{"bad": 1}` au lieu d'un tableau) ne fait
   pas échouer `JSON.parse`, donc passait la validation du point 101
   (qui ne vérifiait que la syntaxe JSON et la forme des recettes) —
   l'erreur (`... is not iterable`) ne survenait que pendant
   l'écriture de cette section, après que les sections précédentes
   (ex. les recettes) avaient déjà été appliquées. Une vérification
   de forme explicite (tableau pour les ingrédients, objet simple
   pour les personnalisations) a été ajoutée, dans la même phase de
   validation qui précède désormais toute écriture.
3. **Date de péremption restaurée invalide : plantage de
   l'affichage** — confirmé : `parseCalendarDateLocal()` (ajoutée au
   point 100 pour corriger le bug de fuseau horaire) renvoie
   correctement `null` pour une chaîne qui n'est pas une date, mais
   `pantryExpirationSuffixHtml()` appelait `.toLocaleDateString()`
   directement sur ce résultat sans jamais vérifier qu'il n'était pas
   `null` — plantage total de l'écran garde-manger dès qu'un seul
   article restauré avait une date corrompue. Corrigé (ne montre
   simplement aucune mention de péremption pour cet article plutôt
   que de planter). Une date de péremption invalide est en plus
   désormais nettoyée à `null` dès l'import (`sanitizeBackupItem`),
   pour ne jamais entrer dans la base une donnée qui aurait pu
   déclencher ce même problème ailleurs.
4. **Date calendaire impossible acceptée silencieusement** —
   confirmé : `new Date(année, mois, jour)` ne valide jamais les
   bornes du mois lui-même — `2026-02-31` "roulait" silencieusement
   sur le 3 mars au lieu d'être signalée comme invalide.
   `parseCalendarDateLocal()` valide maintenant explicitement le
   nombre de jours du mois (même technique que `parseShortDateToIso`,
   déjà utilisée pour la saisie manuelle), cohérent quelle que soit
   l'origine de la donnée.

**Corrigé par la même occasion (risque signalé au point 101, jamais
reproduit, maintenant confirmé et corrigé)** :
- **`waitUntil()` du rafraîchissement en arrière-plan (SWR) ne
  couvrait pas `cache.put()`** — confirmé : `cache.put(...)` était
  appelé sans que sa promesse soit renvoyée dans la chaîne, donc
  `networkUpdate` (protégée par `event.waitUntil()`) se résolvait dès
  la réponse réseau reçue, pas une fois l'écriture dans le cache
  vraiment terminée. Corrigé (`return cache.put(...).then(() =>
  res)`).

**Vérifié** (voir `tests/test_external_audit_fixes_round3.py`,
nouveau) :
- Un échec simulé PENDANT l'écriture (pas une donnée invalide) ne
  laisse aucune trace : ni les anciennes données supprimées, ni la
  moindre nouvelle donnée écrite.
- `ingredients.json` de mauvaise forme est rejeté avant toute
  écriture, y compris pour une recette par ailleurs valide de la même
  archive.
- Une date de péremption restaurée invalide ("not-a-date" ou
  "2026-02-31") ne fait plus planter l'affichage, et est bien
  nettoyée à `null` avec un rapport de correction structurelle.
- `parseCalendarDateLocal("2026-02-31")` renvoie bien `null`.

Suite de régression complète (34 scripts + corpus OCR) au vert.

**Version testée** : v245

### 103 — Nouvelle fonctionnalité : prise/import de photo pour la date de péremption (garde-manger)

Demande explicite de l'utilisateur : le garde-manger dispose déjà de
l'ajout par photo/scan pour le code-barres (points 95-96) ; il fallait
la même possibilité pour la DATE DE PÉREMPTION elle-même — prendre une
photo de l'étiquette (ou en importer une déjà prise) plutôt que de
toujours devoir saisir les 6 chiffres à la main.

- Deux nouveaux boutons dans le formulaire d'ajout/modification d'un
  article du garde-manger, juste sous le champ de date déjà existant :
  "📷 Prendre en photo" et "🖼️ Importer une photo" — même motif que
  les autres imports photo de l'app (recette, journal de cuisine...) :
  deux champs `<input type="file">` distincts (`capture="environment"`
  pour la caméra, sans pour la galerie), plutôt qu'un seul champ
  combiné qui empêcherait de choisir une image déjà présente sur le
  téléphone.
- OCR dédié, plus léger que celui des photos de recette
  (`runExpirationDateOcr`) : redimensionnement et correction
  d'orientation réutilisés à l'identique (mêmes fonctions que l'import
  photo de recette), mais reconnaissance en texte brut seulement — pas
  besoin ici de la reconstruction de mise en page (blocs/grille/
  tableau), une étiquette de péremption n'étant jamais une fiche
  recette en colonnes.
- Nouvelle heuristique d'extraction (`extractExpirationDateFromOcrText`)
  : recherche deux formats de date séparément (ISO `AAAA-MM-JJ` et
  européen `JJ-MM-AA(AA)`, l'année à 2 chiffres étant toujours comprise
  comme 20XX), chaque candidat noté selon la présence d'un mot-clé de
  péremption ("DLC", "DDM", "DLUO", "à consommer avant", "best
  before", "MHD"... dans les 4 langues de l'app plus l'anglais, très
  fréquent même sur des emballages vendus en France) juste avant la
  date, et selon sa plausibilité générale (ni trop dans le passé, ni
  improbablement lointaine) — le candidat le mieux noté est retenu,
  ce qui permet par exemple de préférer une vraie date de péremption
  à une date de fabrication présente ailleurs sur la même étiquette.
  Une date calendairement impossible (31 février) n'est jamais
  retenue, même mécanisme de validation que `parseCalendarDateLocal`
  (point 102).
- **Le résultat ne fait jamais foi seul** : il ne fait que PRÉ-REMPLIR
  le champ de saisie existant (au même format JJ/MM/AA que la saisie
  manuelle), à vérifier ou corriger avant d'enregistrer — exactement
  comme le nom/poids suggéré après un scan de code-barres. Aucune
  date reconnue -> message clair invitant à réessayer ou saisir
  manuellement, sans jamais bloquer le formulaire. Échec de l'OCR
  lui-même (bibliothèque indisponible hors connexion sans le fichier
  encore téléchargé...) -> message d'erreur lisible, jamais de
  plantage.
- Avertissement "économie de données" déjà existant (point 93)
  affiché ici aussi si applicable, puisque cette action peut
  déclencher le même téléchargement du modèle de langue Tesseract
  qu'un import photo de recette.

**Vérifié** (voir `tests/test_pantry_expiration_photo_ocr.py`,
nouveau) :
- Heuristique d'extraction testée directement avec de vrais textes
  OCR représentatifs : mot-clé + ISO, mot-clé + européen, année à 2
  chiffres, mot-clé préféré à une autre date sans mot-clé dans le même
  texte, date seule sans mot-clé malgré tout retenue, date impossible
  ignorée (avec repli sur une autre date valide du même texte si
  présente), aucune date -> aucun résultat, texte vide/nul -> aucun
  résultat (jamais d'erreur).
- Bout en bout dans le vrai formulaire (OCR simulé, jamais le vrai
  Tesseract) : bouton caméra ET bouton galerie préremplissent
  correctement le champ ; rien n'est enregistré avant le clic sur
  "Enregistrer" ; une fois confirmé, l'article est bien sauvegardé
  avec la date issue de la photo ; message d'échec clair si aucune
  date n'est reconnue (champ resté vide) ; message d'erreur lisible si
  l'OCR lui-même échoue.
- **Demande de suivi de l'utilisateur** ("faudrait aussi... détecter le
  sens pour remettre à l'endroit si nécessaire") : déjà couvert dès la
  première version de cette fonctionnalité ci-dessus —
  `runExpirationDateOcr` réutilise directement `detectAndCorrectOrientation`
  (la fonction déjà chargée de remettre à l'endroit une photo de
  recette prise à l'envers ou de côté, point 16), jamais une
  réimplémentation séparée. Vérifié pour de vrai avec une photo
  200×100 volontairement non carrée (une rotation 90°/270° change ses
  dimensions, contrairement à une image carrée qui masquerait un
  défaut de câblage) : rotation effectivement appliquée avant l'OCR
  quand l'orientation est détectée avec une confiance suffisante
  (dimensions bien inversées, 200×100 -> 100×200), image laissée
  strictement inchangée (le `File` d'origine, jamais converti en
  `<canvas>`) si la confiance est trop faible ou si la détection
  d'orientation elle-même échoue — dans les deux cas sans jamais
  bloquer l'OCR qui continue normalement.

Suite de régression complète (35 scripts + corpus OCR) au vert.

**Version testée** : v246

### 104 — Import de code-barres depuis une photo qui n'est pas droite : essai de plusieurs rotations

Signalé par l'utilisateur avec 4 vraies photos de produits (jambon,
boîte en carton, 2 conserves) — toutes prises de travers (portrait, à
l'envers ou de côté, aucune droite), non reconnues par l'import photo
de code-barres. Les 4 codes-barres ont été relus à l'œil sur les
photos et validés par le calcul de la clé de contrôle EAN-13 :
3245412950872, 3245411815059, 3560071006822 et 3560071493882, les 4
valides — confirme que la lecture est correcte et que ce ne sont pas
des codes-barres corrompus ou mal imprimés.

**Limite reconnue avant correction** : le `BarcodeDetector` natif du
navigateur (API "Shape Detection") n'existe pas dans le Chromium de
cet environnement de test (`"BarcodeDetector" in window` renvoie
`false`, vérifié directement) — impossible donc de reproduire ici
l'échec exact que l'utilisateur observe sur son téléphone, ni de
confirmer avec certitude la cause exacte. Cela dit, `decodeBarcodeImageFile()`
transmettait jusqu'ici toujours l'image exactement comme prise, sans
aucune tentative de rotation — contrairement au scan caméra en direct
(appareil tenu à peu près à l'horizontale), une photo déjà prise d'un
produit peut être cadrée dans n'importe quel sens, et un détecteur de
code-barres statique s'est montré, dans les faits, généralement moins
tolérant à la rotation qu'un flux vidéo en direct (optimisé, lui,
pour un cadrage globalement horizontal en continu).

**Corrigé (sans certitude que ce soit LA cause exacte, mais un vrai
gain de robustesse dans tous les cas)** : `decodeBarcodeImageFile()`
essaie maintenant l'image telle que prise, puis — si rien n'est
trouvé — 3 rotations supplémentaires (90°, 180°, 270°) avant
d'abandonner, en s'arrêtant dès qu'une rotation réussit. Réutilise
`rotateImageClockwise()` (même fonction que la correction
d'orientation avant l'OCR, point 16) plutôt que de dupliquer le calcul
de rotation.

**Vérifié** (voir `tests/test_barcode_rotation_retry.py`, nouveau) —
avec le détecteur simulé, puisque le vrai n'est pas disponible ici :
- Une réussite dès la 1ère tentative (0°) ne déclenche aucune rotation
  inutile (comportement inchangé pour le cas déjà courant).
- Un échec sur les 2 premières tentatives (0° et 90°) laisse bien
  essayer la 3e (180°), qui réussit — avec les bonnes dimensions
  d'image à chaque tentative (200×100, puis 100×200, puis 200×100).
- Aucune rotation qui réussit -> `null` après avoir essayé les 4,
  sans planter.
- Une exception sur une rotation (pas seulement un tableau vide)
  n'interrompt pas l'essai des rotations suivantes.
- Suite de régression complète de l'import code-barres
  (`test_barcode_pantry.py`) toujours au vert : les mocks existants
  (succès ou échec dès le premier appel) ne sont pas affectés par la
  boucle de rotation.

**Non vérifié, à confirmer par l'utilisateur sur son téléphone** :
que cette correction résout réellement l'échec observé sur les 4
photos d'origine — impossible à tester avec le vrai détecteur natif
dans cet environnement.

Suite de régression complète (36 scripts + corpus OCR) au vert.

**Version testée** : v247

### 105 — Deux bugs confirmés par un second audit externe sur le résultat d'un scan de code-barres

Suite au point 104, l'utilisateur a partagé l'avis d'une autre IA
ayant testé les 4 mêmes photos avec un décodeur indépendant
(ZXing-C++, puisque le vrai `BarcodeDetector` natif de son téléphone
Samsung n'est pas non plus disponible dans son propre environnement de
test). Deux points structurels ont été vérifiés dans le code puis
corrigés ; les autres points de cet avis (absence de moteur de secours
pur JS pour les codes-barres, difficulté de lecture propre à une
photo précise) sont des constats exacts mais non corrigés ici — voir
plus bas.

**Confirmé et corrigé** :
1. **Un poids trouvé masquait silencieusement l'avertissement "nom
   non trouvé"** — confirmé : `openBarcodeResultModal()` traitait les
   deux indications (poids net / nom introuvable) comme mutuellement
   exclusives via un `if/else`, alors qu'elles sont indépendantes.
   Sur le produit réel signalé (300 g, aucun nom dans la fiche), seul
   le poids s'affichait, sans aucune explication sur le champ nom
   resté vide. Corrigé : les deux messages s'affichent maintenant
   ensemble quand les deux s'appliquent (`white-space:pre-line` sur le
   paragraphe pour bien les séparer visuellement).
2. **Panne réseau et produit vraiment absent de la base
   indiscernables** — confirmé : `lookupProductByBarcode()` renvoyait
   exactement le même résultat (`{name: null}`) pour une vraie panne
   (aucune réponse, délai dépassé, erreur HTTP) que pour une fiche
   simplement absente de la base (`status !== 1`), rendant tout
   diagnostic impossible pour la personne utilisant l'app. Un champ
   `networkError` distinct permet maintenant d'afficher un message
   spécifique ("impossible de vérifier ce produit en ligne") plutôt
   que le message générique "produit non trouvé automatiquement" dans
   ce cas.

**Constats exacts, non corrigés dans ce point** :
- **Aucun moteur de secours pur JS pour les codes-barres** — confirmé
  structurellement (jsQR ne lit que les QR codes, voir le commentaire
  existant dans `openBarcodeScanModal`). Ajouter un décodeur JS de
  secours (type ZXing porté en JS) est une vraie piste, mais un
  ajout de bibliothèque conséquent pour un gain incertain tant que le
  point 104 (rotation) n'a pas eu l'occasion de prouver son effet sur
  le terrain — délibérément non entrepris ici, à réévaluer selon les
  retours de l'utilisateur.
- **Une des 4 photos (maïs) reste probablement illisible même par un
  décodeur robuste** — l'avis externe rapporte un échec du décodeur
  indépendant malgré plusieurs essais de recadrage/contraste sur cette
  photo précise : pourrait nécessiter une nouvelle photo plutôt qu'une
  correction de code.
- Les tests d'import photo continuent de simuler la détection
  (`BarcodeDetector` mocké) — déjà signalé au point 104, aucun moyen
  de le vérifier avec le vrai détecteur natif dans cet environnement.

**Vérifié** (voir `tests/test_barcode_lookup_messages.py`, nouveau) :
- Poids trouvé + nom vide -> les deux messages ("poids net" ET "non
  trouvé automatiquement") apparaissent ensemble.
- Régression : nom ET poids trouvés -> pas de message "non trouvé"
  superflu.
- Régression : produit vraiment absent (aucun poids) -> seul le
  message générique.
- Panne réseau (requête interceptée et annulée) -> message dédié,
  différent du message générique "non trouvé automatiquement".
- Erreur HTTP (500) -> même message dédié de panne réseau, pas le
  message générique.
- Suite complète de l'import code-barres (`test_barcode_pantry.py`)
  toujours au vert.

Suite de régression complète (37 scripts + corpus OCR) au vert.

**Version testée** : v248

### 106 — Retour terrain réel + 3e audit externe : rescan sans contrôle et un vrai 404 Open Food Facts mal classé

Retour terrain direct de l'utilisateur après déploiement du point 104
(rotation) : **3 des 4 photos d'origine décodent désormais
correctement** (confirmation réelle sur son Samsung, jamais vérifiable
depuis cet environnement de test) ; la 4e (jambon 300 g) ouvre bien le
formulaire avec le champ nom vide à compléter, comportement attendu
depuis le point 105 (fiche trouvée sans nom). Un vrai bug d'usage a en
revanche été signalé sur le chemin "code-barres déjà connu", et un
troisième audit externe (une autre IA, ayant testé l'app après le point
105) a confirmé une régression introduite par le correctif du point
105 lui-même.

**Confirmé et corrigé** :
1. **Rescanner un code-barres déjà connu n'offrait aucun moyen de
   saisir une quantité ou une date de péremption** — confirmé par
   l'utilisateur : `handleScannedBarcode()` incrémentait directement
   la quantité de 1 et affichait une simple alerte de confirmation,
   sans jamais rouvrir le formulaire. Un nouvel achat correspond
   pourtant souvent à une quantité différente ET à une nouvelle date
   de péremption imprimée sur cet exemplaire précis. Corrigé : le
   formulaire s'ouvre désormais aussi pour un code-barres déjà connu,
   pré-rempli avec le nom, l'unité et une quantité déjà suggérée
   (l'ancienne + 1, modifiable), permettant de tout ajuster — quantité
   réelle, date de péremption — avant de valider. La fonction dédiée
   à l'ancien raccourci (`addOrIncrementPantryItem`), devenue inutile,
   a été supprimée avec la clé i18n `barcode_added_known` associée.
2. **Un vrai 404 d'Open Food Facts pour un code-barres absent classé
   comme panne réseau** — confirmé : le correctif du point 105
   vérifiait `res.ok` AVANT de lire le corps de la réponse ; or l'API
   v2 d'Open Food Facts répond parfois par un statut HTTP 404 pour un
   code-barres simplement absent de la base, tout en renvoyant malgré
   tout un corps JSON exploitable (`{status: 0, ...}`) — ce cas précis
   affichait donc à tort "impossible de vérifier ce produit en ligne"
   au lieu du message générique "produit non trouvé automatiquement".
   Corrigé : le corps de la réponse est maintenant toujours examiné en
   premier ; seule l'absence totale de corps JSON exploitable (page
   d'erreur générique, coupure...) compte désormais comme une vraie
   panne réseau.

**Vérifié** :
- `tests/test_barcode_pantry.py` (mis à jour) : un rescan d'un
  code-barres connu ouvre bien le formulaire (jamais une alerte
  directe), pré-rempli avec nom/unité/quantité+1 ; la quantité et la
  date de péremption saisies à la main sont bien prises en compte
  (pas figées à l'incrément suggéré) ; le cas d'une unité différente
  de "boîte" mémorisée se comporte pareillement.
- `tests/test_barcode_lookup_messages.py` (étendu) : un vrai 404 avec
  un corps JSON `{status:0}` exploitable est bien traité comme un
  produit inconnu, jamais comme une panne réseau ; une erreur HTTP
  sans corps exploitable reste bien classée comme une panne.
- `tests/test_external_audit_fixes_round2.py` (adapté) : la garantie
  "le stock en mémoire n'augmente pas si l'écriture échoue" (point 63)
  est revérifiée via le nouveau chemin réel (rescan -> formulaire ->
  confirmation), la fonction supprimée n'existant plus.

**Constats du 3e audit externe non repris ici** (améliorations
identifiées, jugées trop conséquentes pour ce point précis — liste
communiquée à l'utilisateur, à discuter avant d'entreprendre l'une
d'elles) : décodeur JS de secours pour les navigateurs sans
`BarcodeDetector` (iOS/Safari, Firefox), validation du checksum EAN en
saisie manuelle avant de requêter Open Food Facts pour rien,
redimensionnement de l'image avant `detect()` (photos réelles pouvant
dépasser 2000 px de large), torche/zoom/vibration en scan caméra live,
mode de scan continu pour ranger plusieurs articles d'un coup, gestion
de plusieurs codes-barres détectés dans une même image, mise en cache
d'une fiche produit complète (pas seulement nom+unité) pour un usage
hors connexion.

Suite de régression complète (37 scripts + corpus OCR) au vert.

**Version testée** : v249

### 107 — Retour de l'utilisateur sur le point 106 : le préremplissage "ancien total + 1" était trompeur

Immédiatement après le point 106, l'utilisateur a repéré un vrai
défaut d'ergonomie dans sa propre correction : préremplir la quantité
avec l'ANCIEN TOTAL + 1 (ex. 3, si 2 étaient déjà présents) laisse
penser à la personne qu'elle doit saisir combien elle vient d'EN
AJOUTER, pas le nouveau total. Exemple concret donné par l'utilisateur
: 2 déjà présents, la personne en ajoute 2 de plus, voit "3" préaffiché,
le corrige en "2" (le nombre qu'elle ajoute réellement) — le total
final devient alors 2 (écrasé) au lieu de 4 (2 déjà là + 2 ajoutés),
reproduisant silencieusement une erreur de stock.

**Corrigé** : la case quantité représente désormais TOUJOURS "combien
j'en ajoute" pour un rescan de code-barres connu — préremplie à 1 (pas
l'ancien total), avec une indication explicite du stock actuel affichée
sous la case ("Stock actuel : X {unité} — indiquez ici combien vous
venez d'en ajouter"). La quantité saisie est ADDITIONNÉE au stock
existant seulement au moment d'enregistrer (jamais avant, cohérent avec
le principe déjà appliqué ailleurs de ne jamais modifier l'état en
mémoire avant confirmation de l'écriture — point 63). Un nouveau
paramètre `opts.addQuantityMode` sur `openAddItemModal()` porte ce
comportement, sans toucher aux autres appels du même formulaire (modifier
manuellement un article existant continue d'afficher et de remplacer sa
quantité absolue, comme avant).

**Vérifié** (`tests/test_barcode_pantry.py`, mis à jour) :
- Le rescan préremplit la quantité à 1 (jamais l'ancien total), avec
  l'indication du stock actuel affichée.
- Reproduction exacte du cas signalé : 2 déjà présents + 2 ajoutés = 4
  au total (jamais écrasé à 2).
- Le cas d'une unité mémorisée différente de "boîte" (Riz Basmati, kg)
  se comporte pareillement.
- Suite complète (`test_external_audit_fixes_round2.py`, point 63)
  toujours au vert : un échec d'écriture pendant ce même parcours ne
  modifie ni la mémoire ni la base.

Suite de régression complète (37 scripts + corpus OCR) au vert.

**Version testée** : v250

### 108 — Deux améliorations de robustesse demandées par l'utilisateur (checksum EAN + redimensionnement photo)

Suite au 3e audit externe (points D et G de sa liste, voir point 106),
l'utilisateur a explicitement demandé ces deux améliorations précises
parmi la liste plus large de pistes proposées.

1. **Validation de la clé de contrôle EAN-8/UPC-A/EAN-13 en saisie
   manuelle** — jusqu'ici, seule la LONGUEUR du code (au moins 8
   chiffres) était vérifiée avant d'interroger Open Food Facts ; un
   code de bonne longueur mais avec une clé de contrôle fausse (erreur
   de frappe plausible : un chiffre oublié, inversé...) déclenchait
   quand même une requête réseau pour aboutir de toute façon à "produit
   non trouvé". Nouvelle fonction `isValidEanChecksum()` (algorithme
   GS1 standard, identique pour les 3 longueurs 8/12/13 — seul le
   nombre de chiffres change) : un code de longueur correcte mais de
   clé invalide est désormais refusé avant toute requête, avec un
   message dédié ("ne semble pas valide") distinct du message
   "incomplet" existant. Validé contre 3 vrais exemples connus
   (EAN-8 `96385074`, UPC-A `036000291452`, EAN-13 `3017620422003`) et
   les 4 vrais codes-barres photographiés par l'utilisateur (points
   104-107) : tous valides, confirmant que l'algorithme ne rejette
   jamais un vrai code.
2. **Redimensionnement de la photo avant l'analyse du code-barres** —
   `decodeBarcodeImageFile()` dessinait jusqu'ici le canvas à la taille
   d'origine de la photo (`naturalWidth`/`naturalHeight`), parfois
   2000 px de large ou plus sur une vraie photo de smartphone — bien
   plus grand que ce qu'un code-barres nécessite pour être lu, au prix
   d'un canvas plus lourd et d'une analyse plus lente sur un appareil
   d'entrée de gamme. Limité désormais à 1600 px de plus grand côté
   (même seuil déjà utilisé par `resizeImageForOcr` pour les photos de
   recette), ratio conservé.

**Effet de bord positif à noter** : plusieurs codes-barres factices
utilisés dans les tests existants (`1111111111111`, `9999999999999`,
et une série `10000000000X`) avaient une clé de contrôle invalide —
sans conséquence avant ce point puisque rien ne la vérifiait, mais
ces fixtures auraient été rejetées à tort par la nouvelle validation.
Remplacées par des codes de clé valide (`1111111111116`,
`9999999999994`, `3017620422003` réutilisé) — la valeur exacte de ces
codes n'a jamais eu d'importance pour ce qu'ils testent (mémorisation,
repli réseau...), seule leur validité de forme compte désormais.

**Vérifié** :
- `tests/test_barcode_pantry.py` (étendu) : un code de longueur
  correcte mais de clé invalide est refusé, AUCUNE requête réseau
  n'est envoyée (vérifié en interceptant les requêtes) ; un EAN-8 et
  un UPC-A valides sont bien acceptés.
- `tests/test_barcode_rotation_retry.py` (étendu) : une photo
  2000×1125 (dimensions des photos réelles d'origine) est bien
  limitée à 1600×900 avant l'analyse, ratio 16:9 conservé.
- Suite complète de l'import code-barres toujours au vert avec les
  fixtures corrigées.

Suite de régression complète (37 scripts + corpus OCR) au vert.

**Version testée** : v251

### 109 — Examen d'un paquet "ui-kit" (autre IA) : conflits réels confirmés, adoption partielle

L'utilisateur a transmis un paquet de 3 fichiers (`ui-kit.js`,
`ui-kit.css`, des consignes) produit par une autre IA n'ayant plus accès
au dépôt réel pour le vérifier elle-même : une barre d'onglets, un
bouton flottant (FAB) et une bibliothèque d'icônes SVG, présentés comme
strictement additifs ("n'enveloppe que render(), ne modifie aucun
fichier existant"). Chaque affirmation a été vérifiée dans le vrai code
avant d'agir, plutôt que d'appliquer le paquet tel que fourni.

**Conflits réels confirmés, non appliqués** :
1. **Barre d'onglets dupliquée** — l'app dispose déjà d'une vraie
   navigation basse (`renderBottomNav()`, classe `.bottom-nav`,
   `position:fixed;bottom:0;z-index:30`). La nouvelle barre proposée
   (`#tabbar`, mêmes `position:fixed;bottom:0`, mais `z-index:25`,
   donc rendue EN DESSOUS) se serait retrouvée entièrement masquée
   derrière la vraie barre — présente dans le DOM, injectée à chaque
   `render()`, mais invisible et morte.
2. **Bouton flottant dupliqué avec un comportement différent** — l'app
   a déjà un vrai FAB contextuel (`.fab`, `position:fixed;right:18px`,
   z-index 25) affiché sur recettes/courses/garde-manger/menus. Le
   nouveau FAB proposé (`#fab`, position quasi identique, z-index 26,
   donc PAR-DESSUS) aurait pris sa place visuellement, mais avec une
   logique différente : sur l'écran garde-manger, son mode "scan"
   recherche par texte un bouton "Scanner un code-barres" à cliquer,
   au lieu d'ouvrir le formulaire d'ajout manuel (comportement actuel
   du vrai bouton "+") — un vrai changement de comportement, jamais
   demandé, découvert avant application plutôt qu'après.
3. **Classe `recipe-grid` inexistante, `.recipe-thumb` en no-op** — la
   consigne demandait d'ajouter une classe `recipe-grid` dans
   `renderRecipeList()`, mais aucune trace de cette classe dans le
   vrai code : la liste de recettes utilise déjà `.recipe-list` (voir
   point retenu ci-dessous). La règle `.recipe-thumb { aspect-ratio:
   16/10 }` proposée n'aurait eu aucun effet : ce thumbnail a déjà une
   largeur ET une hauteur fixes (56×56px, une icône carrée dans une
   ligne de liste, pas une photo de carte) — `aspect-ratio` ne
   s'applique jamais quand les deux dimensions sont déjà fixées.
4. **Recouvrement de valeurs déjà réglées** — `:focus-visible` et les
   états `:active` des boutons sont déjà définis dans `styles.css`
   (contraste déjà vérifié à plusieurs reprises cette session, voir
   points 90-91) ; les redéfinir avec des valeurs différentes aurait
   changé un comportement déjà accessible sans raison vérifiée.
5. **Variables de couleur en thème sombre non vérifiées** — le paquet
   proposait de redéfinir `--text-muted`/`--danger` en thème sombre
   "si nécessaire" (condition non vérifiée par son auteur) : non
   appliqué, pour ne pas risquer de régresser des valeurs déjà
   auditées par axe-core à plusieurs reprises.
6. Création d'une branche séparée et d'une pull request non
   fusionnée, demandée par les consignes du paquet — non fait,
   contraire à l'instruction explicite déjà donnée par l'utilisateur
   plus tôt dans cette session ("je veux plus que tu crée de branche
   à côté") : toute modification va directement sur `main`.

**Retenu et appliqué, après vérification** :
1. **Bandeau "Annuler" (snackbar) pour la suppression d'un article du
   garde-manger** — genuinement nouveau, sans rien dupliquer : la
   suppression reste immédiate (aucun changement de ce comportement),
   mais un bandeau temporaire avec un bouton "Annuler" permet de
   restaurer l'article (nom, quantité, unité, seuil, date de
   péremption) en cas d'erreur, plutôt qu'aucun filet de sécurité du
   tout comme avant. Fonctions `showSnackbar()`/`hideSnackbar()`
   ajoutées directement dans `app.js` (pas de fichier séparé, pour
   rester cohérent avec la structure à un seul fichier déjà en place).
2. **Bug réel trouvé EN COURS d'examen, sans rapport avec le "ui-kit"
   lui-même** : `row.querySelector("button")` sans classe précise, dans
   le gestionnaire de suppression du garde-manger, sélectionnait à
   tort la poignée de glisser-déposer (premier `<button>` de la ligne
   en mode tri manuel, avant `.remove-ing`) — cliquer sur la poignée ☰
   supprimait donc l'article au lieu de rien faire. Reproduit
   directement avant correction (`row.querySelector(".remove-ing")`).
3. **Grille à 2 colonnes sur écran large pour la liste de recettes** —
   appliquée sur la vraie classe `.recipe-list` (pas une classe
   inventée), simple ajout d'une media query `@media (min-width:
   720px)` : aucun changement JS/HTML nécessaire. Vérifié à l'œil
   (capture d'écran à 900px) : rendu propre, cohérent avec le design
   existant.
4. **Chevauchement visuel repéré sur cette même capture d'écran** :
   le bouton flottant (+) et le nouveau snackbar occupent le même coin
   — corrigé en masquant le bouton pendant l'affichage du snackbar
   (`body:has(#snackbar.show) .fab { display: none; }`, repli sans
   risque si `:has()` n'est pas supporté).
5. **Chiffres tabulaires** (`font-variant-numeric: tabular-nums` sur
   les quantités et champs numériques) et **animation d'entrée des
   fenêtres modales** (respecte la règle `prefers-reduced-motion` déjà
   en place) — polish visuel à coût nul, aucun conflit détecté.

**Vérifié** (voir `tests/test_pantry_delete_undo_and_polish.py`,
nouveau) :
- Cliquer sur la poignée ☰ en tri manuel ne supprime plus l'article.
- Suppression toujours immédiate ; le bandeau "Annuler" restaure
  l'article avec la totalité de ses champs (pas seulement le nom).
- Le snackbar disparaît seul après son délai.
- Le bouton flottant se masque bien pendant l'affichage du snackbar.
- La liste de recettes reste en colonne unique sur mobile, passe en
  grille à partir de 720px de large.
- Audit d'accessibilité (axe-core) toujours au vert, aucune nouvelle
  violation introduite par le snackbar ou les animations.

Suite de régression complète (38 scripts + corpus OCR) au vert.

### 110 — "Patch graphique" demandé explicitement : icônes SVG à la place des emoji de chrome d'interface

Suite au point 109, l'utilisateur a explicitement confirmé vouloir malgré
tout le changement visuel : "c un patch graphique que je veux donc
applique aussi les changement graphique". Plutôt que d'appliquer le
paquet "ui-kit" tel que fourni (qui aurait dupliqué la navigation et le
bouton flottant, voir point 109), le jeu d'icônes SVG qu'il proposait a
été repris seul et intégré directement DANS les éléments d'interface
déjà existants — jamais en les dupliquant.

**Fait** :
- Nouvel objet `ICONS`/fonction `icon(name)` dans `app.js` (juste après
  `escapeHtml`) : 11 icônes SVG au trait (`currentColor`, `viewBox="0 0
  24 24"`), rendu strictement identique quel que soit l'appareil, à la
  différence des emoji dont le dessin varie sensiblement d'un fabricant
  à l'autre. Chaque icône est marquée `aria-hidden="true"` (purement
  décorative — le texte ou l'`aria-label` du bouton porte déjà le sens).
- Emoji de CHROME remplacés par l'icône SVG correspondante, en modifiant
  chaque élément existant sur place (jamais de nouvel élément dupliqué) :
  les 4 onglets de la navigation du bas, les 3 boutons flottants (+),
  le bouton "retour", le bouton recherche et le bouton thème (lune/
  soleil, y compris sa bascule dynamique) de la barre du haut, les 4
  loupes décoratives des barres de recherche, et tous les boutons de
  suppression/fermeture (garde-manger ×2, liste de courses, gestion des
  ingrédients, journal de cuisine, minuteur de cuisson, planning ×2,
  photo à importer).
- Emoji de CONTENU volontairement PAS touchés (hors périmètre de la
  demande, ce ne sont jamais des icônes de chrome) : étoile de favori
  (⭐/☆), illustrations d'écran vide (🔍/🛒/📦/🗑️), poignée de
  glisser-déposer (☰), bouton de don (☕), bouton de cycle de langue,
  crayon d'édition (✏️), boutons lecture/réinitialisation du minuteur
  (▶️/🔄) — aucun de ces derniers n'appartenait au jeu d'icônes proposé
  par le paquet examiné au point 109, donc laissés en l'état pour ne pas
  élargir la demande initiale.
- CSS : nouvelle classe `.ui-icon` (taille par défaut adaptée aux petits
  boutons ronds, avec des tailles spécifiques `.nav-icon .ui-icon`/
  `.fab .ui-icon` reprenant les anciens `font-size` de ces contextes).

**Bug de test pré-existant découvert et corrigé en cours de
vérification, sans rapport avec ce changement d'icônes** : le test
d'audit d'accessibilité (`test_accessibility_audit.py`, point 90)
échouait de façon intermittente (environ 1 essai sur 2-3, reproduit
5 fois via `git stash` sur le code NON modifié pour confirmer que la
cause n'était pas les icônes) sur une fausse alerte "color-contrast"
dans la fenêtre de saisie manuelle de code-barres. Cause réelle :
l'animation d'entrée des fenêtres modales (`modal-fade-in`, 0.18s —
ajoutée au point 109) entrait en course avec le délai fixe de 150ms
attendu avant chaque appel à `axe.run()`, qui pouvait donc mesurer le
contraste EN PLEIN FONDU (opacité < 1). Corrigé en demandant au
navigateur de test la préférence `prefers-reduced-motion: reduce` (déjà
respectée par l'application elle-même, voir sa règle globale dans
`styles.css`) via `page.emulate_media(reduced_motion="reduce")` — 5
exécutions consécutives toutes au vert après ce correctif, contre 1
échec sur 3 avant.

**Vérifié** (voir `tests/test_ui_icon_replacement.py`, nouveau, et
captures d'écran manuelles clair/sombre sur les 4 écrans principaux +
détail recette + fenêtre de recherche) :
- Les 4 onglets, le bouton flottant, le bouton retour, les boutons
  recherche/thème et un bouton de suppression contiennent bien une
  icône SVG (`svg.ui-icon`) et déclenchent toujours exactement la même
  action qu'avant (navigation, ouverture de fenêtre, suppression,
  bascule de thème).
- L'étoile de favori et l'illustration d'écran vide du garde-manger
  restent des emoji, non remplacées.
- Chaque icône SVG est bien `aria-hidden="true"` ; chaque bouton garde
  son `aria-label` (ou son texte visible, pour les onglets) inchangé —
  un lecteur d'écran annonce donc exactement la même chose qu'avant ce
  changement purement visuel.
- Audit d'accessibilité (axe-core) toujours au vert dans les deux
  thèmes, désormais de façon fiable (voir correctif ci-dessus).
- Rendu visuel vérifié à l'œil (captures d'écran) : icônes nettes,
  centrées, contraste correct dans les deux thèmes.

Suite de régression complète (39 scripts + corpus OCR) au vert.

**Version testée** : v253

### 111 — "Vague visuelle 1" : cartes photo, barres translucides, superposition héro/pills

Retour direct de l'utilisateur sur le point 110 : "seules 4 [icônes] ont
atterri, et 3 d'entre elles sont quasi invisibles sur un téléphone" —
constat exact (grille tablette à 720px, chiffres tabulaires et
animation de modale sont en effet peu visibles sur téléphone). L'utilisateur
a alors transmis 7 transformations CSS concrètes, vérifiées dans le vrai
`styles.css`/`app.js` avant application (contrairement au paquet "ui-kit"
du point 109, chaque classe citée — `.recipe-row`, `.recipe-thumb`,
`.topbar`, `.bottom-nav`, `.nav-item`, `.recipe-hero`, `.stat-row`,
`.stat-pill`, `.empty-state .emoji`, `.chip`, `.autocomplete-item` —
existe réellement et correspond à l'usage décrit).

**2 écarts corrigés par rapport aux instructions transmises, trouvés en
vérifiant puis en testant** :
1. **Bug réel introduit puis corrigé avant même le premier commit** : les
   instructions scopaient déjà certaines surcharges à `.recipe-row`
   (`.recipe-row .recipe-thumb`, etc.) en pensant éviter tout effet sur
   la fenêtre de sélection de recette (`openRecipePickerModal`) et la
   liste des menus, qui réutilisent les mêmes classes. Mais la fenêtre
   de sélection utilise EXACTEMENT `class="recipe-row"` (sans `.card`),
   alors que la liste de recettes, la liste des menus et "Que puis-je
   cuisiner ?" utilisent toutes `class="card recipe-row"` — `.recipe-row`
   seul les confondait donc toutes. Un premier essai a bien reproduit le
   bug (fenêtre de sélection transformée en grandes cartes photo, testé
   et vu avant correction) puis corrigé en rescopant tout sur
   `.card.recipe-row` (les deux classes ensemble), qui ne cible plus que
   les listes en carte, jamais la fenêtre de sélection compacte.
2. **Étoile de favori** : la mise en page en colonne (photo pleine
   largeur au-dessus du texte) aurait autrement repoussé l'étoile, 3e
   élément du flex avant ce changement, sous le texte au lieu de rester
   un repère visuel sur la carte — non traité par les instructions
   transmises. Repensée en badge rond superposé en haut à droite de la
   photo (`position: absolute`).
3. **Marge négative du chevauchement héro/statistiques** : les
   instructions proposaient `.stat-row { margin-top: -26px; ... }` sans
   scoping, mais cette même classe sert aussi au bloc de valeurs
   nutritionnelles plus bas sur la fiche recette (hors de toute photo) —
   une marge négative non scopée y aurait fait remonter les pastilles
   sur le texte au-dessus. Restreint à `.recipe-hero + .stat-row`
   (sélecteur de frère adjacent), qui ne correspond qu'au bloc juste
   après la photo.

**Vrai bug de contraste trouvé en testant (pas une supposition)** : les
premières valeurs de transparence proposées (`.topbar` à 82%, `.bottom-nav`
à 86%) faisaient chuter le contraste des libellés de navigation sous le
seuil AA (3,98 au lieu de 4,5 minimum) sur l'écran diagnostic — un vrai
bouton `.btn-primary` de couleur foncée s'y trouve juste derrière la
navigation translucide au moment du test, et `color-mix()` composé avec
cette couleur assombrit trop l'arrière-plan effectif du texte. Diagnostiqué
précisément via `document.elementsFromPoint()` (identification de
l'élément réel derrière chaque pixel) et un calcul manuel de contraste
WCAG, confirmant que le blocage venait de ce bouton spécifique. Corrigé en
relevant l'opacité à 95% pour les deux barres — calculé pour rester ≥4,5:1
même dans ce cas le plus défavorable (bouton `--primary-strong` foncé
derrière), tout en gardant un effet de flou (`backdrop-filter`) visible.

**Appliqué** (les 7 points, une fois les 2 écarts et le bug de contraste
corrigés) :
1. Cartes de recette à grande photo 16/9 (au lieu d'une miniature 56px),
   titre en police Fraunces — rend la grille 2 colonnes à 720px enfin
   nettement visible.
2. Barres du haut et du bas translucides (`backdrop-filter: blur(12px)
   saturate(1.4)`, repli `@supports` sans flou).
3. Pastille de fond (`--primary-light`) derrière l'icône de l'onglet actif.
4. Photo de fiche recette agrandie (220px), dégradé sombre en bas, pastilles
   de statistiques (préparation/cuisson/difficulté) superposées en
   chevauchement, translucides avec flou.
5. Cercle `--primary-light` derrière l'emoji des écrans vides.
6. `scale(.97)` au clic sur les puces de filtre, onglets et suggestions
   d'autocomplétion.
7. Photos légèrement adoucies (`brightness(.92) saturate(1.05)`) en thème
   sombre uniquement.

**Vérifié** (voir `tests/test_visual_wave_1.py`, nouveau, et captures
d'écran manuelles clair/sombre + largeur tablette) :
- Les cartes de recette ont bien une photo 16/9 pleine largeur et un
  titre Fraunces ; la grille 2 colonnes à 720px fonctionne toujours.
- Le badge de favori reste visible et dans les limites de la carte.
- La fenêtre de sélection de recette (et elle seule) n'est PAS transformée
  — miniature et police inchangées, confirmant la correction du bug de
  scoping.
- Barres translucides confirmées (couleur avec canal alpha, flou visible
  sur une capture d'écran avec contenu défilé dessous).
- Onglet actif : pastille de fond confirmée.
- Le `.stat-row` de la nutrition (hors fiche recette) n'a PAS de marge
  négative — seul celui juste après `.recipe-hero` chevauche la photo.
- Écrans vides : cercle coloré confirmé derrière l'emoji.
- Audit d'accessibilité (axe-core) au vert dans les deux thèmes sur
  l'écran diagnostic (scénario exact qui avait révélé le bug de
  contraste) — 3 exécutions consécutives sans échec après le correctif.
- **Captures d'écran de manifeste régénérées** (`screenshots/01_accueil.png`,
  `02_recettes.png`, `03_fiche_recette.png`, `04_courses.png`,
  `wide_01_accueil.png`, `wide_02_recettes.png`) avec les mêmes données de
  démonstration qu'avant (mêmes recettes, mêmes quantités, même liste de
  courses — reconstituées à l'identique à partir des anciennes captures),
  pour refléter le nouveau design plutôt que de laisser les captures du
  manifeste PWA (visibles dans l'invite d'installation) montrer l'ancienne
  interface.

Suite de régression complète (40 scripts + corpus OCR) au vert.

**Version testée** : v254

### 112 — Grille 2 colonnes dès le mobile (pas seulement à partir de 720px)

Retour direct de l'utilisateur avec une capture d'écran de référence (un
mockup de l'appli en 2 colonnes sur téléphone) : la grille 2 colonnes
introduite au point 109 ne se déclenchait qu'à partir de 720px de large
(tablette) — sur un vrai téléphone, la liste de recettes restait donc en
une seule colonne verticale, rendant les grandes cartes photo de la
"vague visuelle 1" (point 111) moins spectaculaires que prévu tant
qu'aucun écran large n'était utilisé.

**Fait** : `.recipe-list` passe en grille 2 colonnes fixes
(`grid-template-columns: repeat(2, 1fr)`) dès le mobile, sans condition
de largeur d'écran. La media query à 720px ne fait plus que changer le
NOMBRE de colonnes pour un écran large (`auto-fill, minmax(240px, 1fr)`,
qui donne 2-3 colonnes selon la largeur disponible, l'écran restant de
toute façon plafonné à 640px — voir `.screen`) plutôt que d'activer la
grille elle-même.

Ce changement s'applique à toutes les listes qui réutilisent
`.recipe-list`/`.card.recipe-row` : la liste principale des recettes, la
section "Favoris" de l'accueil, et la liste des menus — toutes gagnent la
grille 2 colonnes de façon cohérente, sans code supplémentaire.

**Vérifié** (capture d'écran à 360px et 390px, clair et sombre, voir
aussi la mise à jour du test existant `test_pantry_delete_undo_and_polish.py`
qui vérifiait auparavant l'ANCIEN comportement — colonne unique sur
mobile — désormais volontairement changé) :
- Sur mobile (360-390px), la liste de recettes affiche bien 2 cartes
  côte à côte sur la même ligne, sans débordement horizontal, titres et
  photos restent lisibles dans les deux thèmes.
- Sur écran large (900px), la grille reste fonctionnelle (auto-fill).
- Audit d'accessibilité (axe-core) toujours au vert (3 exécutions
  consécutives).

Suite de régression complète (40 scripts + corpus OCR) au vert.

**Version testée** : v255

### 113 — Plusieurs recettes par repas dans le planning (entrée + plat + dessert)

Retour direct de l'utilisateur : "le déjeuner et le dîner sont constitué
généralement d'une entrée, un plat principal et un dessert, là on peut
choisir uniquement une recette alors qu'il en faudrait au moins 3". Le
planning de la semaine ne permettait en effet d'assigner qu'UNE seule
recette par créneau jour/repas (`state.weeklyPlan[jour][repas] =
{recipeId, persons}`) — vérifié dans le vrai code (`renderPlanning`)
avant de modifier quoi que ce soit.

**Fait** : chaque créneau jour/repas contient désormais un TABLEAU
d'assignations plutôt qu'une assignation unique. Nouvelle fonction
`planSlotAssignments(assigned)` qui accepte les DEUX formes (l'ancienne,
un objet unique ; la nouvelle, un tableau) — utilisée à chaque lecture
d'une case du planning (écran principal, génération de la liste de
courses, historique). Aucune migration réécrivant le stockage n'a été
nécessaire : une case au format hérité continue de s'afficher
normalement, et se convertit proprement en tableau dès qu'elle est
modifiée à nouveau (ajout d'une 2e recette) — un vrai planning déjà
enregistré par l'utilisateur avant ce changement n'est donc jamais
perdu ni cassé, vérifié directement en simulant ce cas précis avant
d'écrire le test permanent.

Chaque créneau affiche maintenant une ligne par recette assignée (avec
son propre bouton de suppression individuel), plus un bouton "+
Ajouter" toujours visible pour en ajouter d'autres — aucune limite
imposée dans l'interface (l'utilisateur peut mettre 1, 3, ou davantage),
la limite basse de 3 pour un repas complet restant une convention, pas
une contrainte technique. Supprimer la dernière recette d'un créneau
retire la case entièrement (`delete`) plutôt que de laisser un tableau
vide, pour ne pas fausser `planHasAnyAssignment()` (qui déciderait à
tort qu'un créneau vide compte comme "planning rempli").

Trois autres endroits qui lisaient une case du planning ont été mis à
jour pour parcourir toutes les recettes assignées, plus seulement la
première : la génération de la liste de courses depuis le planning
(`genBtn`), l'affichage de l'historique des semaines archivées
(`renderPlanningHistory`, qui joint les noms avec " + " sur une seule
ligne), et `planHasAnyAssignment()` (utilisée avant d'archiver
automatiquement le planning actuel). Les modèles de planning et le
réappliquage d'un historique n'ont pas eu besoin de changement : ils
clonent `state.weeklyPlan` tel quel (`JSON.parse(JSON.stringify(...))`),
sans jamais interpréter sa structure interne.

**Vérifié** (voir `tests/test_weekly_plan_multi_recipe.py`, nouveau) :
- 3 recettes assignées au même créneau s'affichent bien chacune sur sa
  propre ligne, avec son propre bouton de suppression.
- Supprimer une recette du milieu d'un créneau à 3 recettes laisse les
  2 autres intactes.
- Supprimer la dernière recette d'un créneau retire la case (pas un
  tableau vide) ; `planHasAnyAssignment()` ne compte plus alors le
  planning comme rempli.
- Une case au format hérité (objet unique, simulée comme si elle avait
  été enregistrée avant ce changement) s'affiche toujours correctement,
  et se convertit en tableau de 2 éléments (sans perdre l'ancienne
  recette) après l'ajout d'une seconde.
- "Générer la liste de courses" ajoute bien les ingrédients des 3
  recettes d'un repas complet (entrée + plat + dessert), pas seulement
  la première.
- L'archivage automatique dans l'historique (avant effacement du
  planning) conserve la totalité des 3 recettes assignées à un repas.
- Audit d'accessibilité (axe-core) au vert (3 exécutions consécutives).

Suite de régression complète (41 scripts + corpus OCR) au vert.

**Version testée** : v256

### 114 — Ingrédients sans quantité dupliqués en ajoutant une recette/un menu à une liste de courses déjà existante

Retour direct de l'utilisateur avec une capture d'écran : ajouter une
recette ou un menu à une liste de courses déjà existante créait des
doublons — précisément pour les ingrédients qui n'ont pas de quantité
indiquée dans la recette (ex. "sel" sans dosage). Diagnostiqué en lisant
le vrai code avant de le modifier : trois endroits distincts partageaient
exactement la même erreur.

**Cause confirmée** : `addRecipeToShoppingSilent()` (planning, menus),
`addRecipeToShopping()` (bouton "Ajouter aux courses" d'une fiche
recette) et le rappel "stock bas" de l'accueil recherchaient bien un
article déjà présent dans la liste (même nom, même unité, pas coché),
mais ne le réutilisaient QUE si les DEUX quantités (celle déjà dans la
liste ET celle ajoutée) étaient non nulles :

```js
if (existing && qty != null && existing.quantity != null) { /* fusionne */ }
else { /* crée un nouvel article */ }
```

Un ingrédient sans quantité (`qty === null`) ratait cette condition même
quand un article correspondant existait déjà, et retombait dans le
"else" — créant un doublon au lieu de reconnaître l'article déjà
présent. Le rappel "stock bas" de l'accueil avait le même défaut (jamais
signalé par l'utilisateur, corrigé par cohérence, cause identique).

**Corrigé** : dès qu'un article correspondant existe, il est toujours
réutilisé (jamais de doublon) — sa quantité n'est mise à jour que si le
nouvel ajout en précise une (en partant de 0 si l'article existant n'en
avait pas encore). Un article déjà coché n'est toujours pas réutilisé
(comportement existant, inchangé) : cocher un article "termine" cette
occurrence, un ajout ultérieur du même ingrédient doit repartir sur un
nouvel article.

**Vérifié** (voir `tests/test_shopping_no_duplicate_missing_qty.py`,
nouveau, y compris un scénario de bout en bout reproduisant exactement
le cas signalé — recette ajoutée à une liste déjà existante) :
- Existant sans quantité + ajout sans quantité → aucun doublon.
- Existant avec quantité + ajout sans quantité → aucun doublon, quantité
  existante conservée.
- Existant sans quantité + ajout avec quantité → aucun doublon, quantité
  mise à jour.
- Un article déjà coché n'est pas réutilisé (comportement inchangé,
  vérifié pour ne pas avoir régressé avec ce correctif).
- Scénario réel : une recette avec un ingrédient sans quantité (déjà
  dans la liste), un avec quantité (cumulé correctement) et un nouveau
  (ajouté), ajoutée à une liste de courses déjà existante — exactement
  3 articles au total, aucun doublon.
- Audit d'accessibilité (axe-core) au vert (3 exécutions consécutives).

Suite de régression complète (42 scripts + corpus OCR) au vert.

**Version testée** : v257

### 115 — Troisième audit externe (autre IA) sur la restauration ZIP, la liste de courses et le service worker : 6 bugs réels confirmés et corrigés, 3 points écartés après vérification

L'utilisateur a transmis un audit détaillé (9 points) produit par une
autre IA sur la version en ligne. Comme pour les audits précédents,
chaque point a été vérifié directement dans le code réel avant toute
correction — aucun n'a été appliqué "sur parole".

**Bugs confirmés et corrigés** :

1. **Critique — perte de données lors d'une restauration ZIP partagé
   avec un identifiant déjà existant.** `storeWriteManyAcrossStores()`
   (utilisée par `restoreFromSharedZip`) appliquait les `puts` d'une
   opération AVANT ses `deletes` dans la même transaction IndexedDB. En
   mode "remplacer", l'opération de restauration supprime d'abord tout
   (une opération avec seulement des `deletes`) puis réinsère le contenu
   importé (une opération avec seulement des `puts`) — l'ordre
   `puts`-avant-`deletes` n'affectait donc pas ce cas précis, MAIS
   exposait un vrai risque pour tout futur appel combinant les deux dans
   une même opération sur la même clé (un `put` suivi d'un `delete` sur
   le même id aurait silencieusement supprimé l'élément qui venait
   d'être écrit). Corrigé en inversant l'ordre : `deletes` toujours
   avant `puts` dans chaque opération. Vérifié sur les 3 points d'appel
   existants (renommage d'ingrédient, fusion de doublons, restauration
   ZIP) : aucun n'est affecté négativement, le point de restauration ZIP
   est maintenant protégé contre toute évolution future du code.

   1bis. Même fonction, même correctif : les réglages personnalisés
   d'ingrédient (`ingredientOverrides`, clé = nom) partagent exactement
   le même chemin de code et bénéficient donc automatiquement du même
   correctif.

2. **Recette mal formée dans un ZIP partagé non validée.**
   `recipeFromSharedFormat()` acceptait tel quel un nom non-chaîne (ex.
   un nombre) et un tableau d'ingrédients contenant des entrées `null`
   ou non-objets — provoquant un plantage au tri alphabétique
   (`.localeCompare` sur un nombre) et des lignes d'ingrédient cassées
   à l'affichage. Corrigé en réutilisant `sanitizeBackupItem()` (déjà
   utilisée et éprouvée par le chemin de restauration JSON complet) sur
   chaque recette importée d'un ZIP partagé : coercion du nom en
   chaîne, filtrage des entrées d'ingrédient invalides, mêmes garanties
   que la sauvegarde JSON.

3. **États en mémoire non rechargés après une restauration JSON
   complète.** `importAllData()` rechargeait bien `state.recipes`,
   `state.shopping`, `state.pantry`, etc., mais pas
   `state.menus`, `state.planTemplates`, `state.planHistory`,
   `state.trash`, `state.savedShoppingLists`, ni `state.weeklyPlan`
   (stocké via le magasin générique "kv") — un menu ou un modèle de
   planning restauré depuis un fichier de sauvegarde restait invisible
   tant que l'application n'était pas rechargée manuellement. Corrigé
   en ajoutant le rechargement de ces 6 collections à la fin de
   `importAllData()`.

4. **Quantité fictive possible en cas d'échec d'écriture dans la liste
   de courses.** `addRecipeToShoppingSilent()` et
   `addRecipeToShopping()` mettaient à jour `existing.quantity` en
   mémoire de façon synchrone AVANT que l'écriture asynchrone en base
   (`storePut`) soit confirmée. Si cette écriture échouait (quota
   dépassé, erreur IndexedDB), la quantité affichée à l'écran restait
   augmentée alors que la base, elle, n'avait pas changé — un
   rechargement faisait alors "perdre" cette quantité sans que
   l'utilisateur comprenne pourquoi. Corrigé en inversant l'ordre :
   écriture en base d'abord (`await storePut`), mise à jour de l'état
   en mémoire seulement après confirmation. Même correctif appliqué,
   par cohérence, au rappel "stock bas" de l'écran d'accueil qui
   partageait le même défaut.

5. **Accessibilité de la liste de courses et du garde-manger.** La
   case à cocher de chaque article n'avait pas de `aria-label` (un
   lecteur d'écran l'annonçait comme "case à cocher" sans préciser de
   quel ingrédient), et le texte cliquable pour éditer un article était
   un `<span>` — invisible au clavier (pas de `tabindex`, pas
   d'activation à la touche Entrée). Corrigé : `aria-label` ajouté sur
   la case à cocher (nom de l'ingrédient + quantité), `<span>` remplacé
   par un vrai `<button>` pour le texte d'édition. Appliqué à la fois à
   la liste de courses (signalée par l'audit) et au garde-manger (même
   motif de code, même défaut, trouvé par cohérence).

6. **Écritures de cache du service worker non protégées.** Sur les 3
   branches du gestionnaire `fetch` de `sw.js`, seule celle des
   fichiers JSON de référence (déjà corrigée au point 69) enveloppait
   son écriture `cache.put()` dans `event.waitUntil()`. Les deux autres
   (fichiers critiques app.js/i18n.js/index.html, et le repli
   générique cache-d'abord pour images/bibliothèques/moteur OCR)
   lançaient `cache.put()` sans l'attendre : rien n'empêchait le
   navigateur de couper le service worker avant la fin de cette
   écriture, laissant potentiellement une version obsolète en cache
   pour l'usage hors-ligne suivant. Corrigé en appliquant le même
   `event.waitUntil(caches.open(CACHE_NAME).then((cache) =>
   cache.put(...)))` aux deux branches restantes.

**Points signalés mais écartés après vérification** :

- **Fusion de quantité "5g + quantité non précisée"** : l'audit note
  que fusionner un article sans quantité avec un ajout quantifié (ou
  l'inverse) peut afficher une quantité partielle qui masque le fait
  qu'une partie de l'ingrédient reste "à doser". C'est un comportement
  déjà délibéré, mis en place volontairement au point 114 de ce même
  document à la demande explicite de l'utilisateur (éviter les
  doublons). Il ne s'agit pas d'un bug mais d'un compromis
  d'affichage — non modifié unilatéralement, à reposer à l'utilisateur
  s'il souhaite un affichage différent (ex. "5g + quantité non
  précisée").
- **Convertisseur d'unités qui suppose 1 L = 1000 g** : confirmé exact
  et déjà documenté explicitement dans le code
  (`CONVERTER_UNIT_KEYS`) comme une simplification volontaire, à
  l'identique de l'application de bureau — limite connue, non urgente,
  non corrigée.
- **Absence d'indication dans l'interface de sauvegarde sur le format à
  utiliser (ZIP partagé vs JSON complet)** : vérifié directement sur
  l'écran de sauvegarde réel — un texte d'aide distinguant clairement
  les deux formats est déjà présent. Ce point de l'audit est faux (audit
  probablement basé sur un extrait de code incomplet), aucune
  correction nécessaire.

**Vérifié** (voir `tests/test_third_audit_backup_and_shopping_bugs.py`,
nouveau, exécutant les vraies fonctions de l'application via
Playwright) : les 6 bugs ci-dessus sont chacun reproduits puis
confirmés corrigés (ZIP "remplacer" avec identifiant commun,
`ingredientOverrides` avec nom commun, recette mal formée sans
plantage ni ingrédient `null` conservé, rechargement des 6 collections
après restauration JSON, absence de quantité fictive après un échec
d'écriture simulé, `aria-label`/bouton focalisable sur courses et
garde-manger, absence d'écriture de cache non enveloppée dans
`sw.js`). Audit d'accessibilité (axe-core) au vert (3 exécutions
consécutives). Suite de régression complète (43 scripts + corpus OCR)
au vert.

**Version testée** : v258
