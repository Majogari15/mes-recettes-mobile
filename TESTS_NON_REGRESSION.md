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

## Résumé — état au 06/09/2026 (v183)

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
