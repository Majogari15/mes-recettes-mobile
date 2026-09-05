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

## Résumé — état au 05/09/2026 (v156)

- **jsQR et jsPDF désormais embarqués localement** (v141) — seul
  Tesseract (import par photo) reste chargé depuis un CDN.
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
