# Guide — formulaire "Sécurité des données" (Play Console)

Ce formulaire est une source fréquente de refus s'il est mal rempli —
voici comment répondre honnêtement, question par question, en cochant
les bonnes cases.

## Cette application collecte-t-elle ou partage-t-elle des types de
## données utilisateur ?

**Réponse : Non** (ou "Aucune donnée collectée", selon la formulation
exacte de l'interface au moment où vous remplissez le formulaire).

Justification : toutes les données créées dans l'application
(recettes, garde-manger, listes de courses, planning, photos)
restent stockées localement sur l'appareil de l'utilisateur, ne sont
jamais transmises au développeur, ni à un tiers. Aucun compte,
aucune inscription, aucun identifiant utilisateur.

## Cas particulier à connaître : l'import de recette par lien

Si Google Play vous demande de préciser si l'application "communique
avec un serveur" ou "accède à internet", vous pouvez répondre "oui" à
cette question précise, en précisant :
- Donnée concernée : l'adresse (URL) que l'utilisateur saisit
  volontairement pour importer une recette
- Finalité : fonctionnalité de l'application elle-même (aller chercher
  le contenu de la page), pas de la publicité, pas de l'analyse
  d'audience
- Cette donnée n'est ni partagée avec un tiers, ni conservée après la
  requête
- Cette action ne se produit que si l'utilisateur choisit
  explicitement d'importer une recette par lien — ce n'est pas un
  comportement automatique ou en arrière-plan

Si le formulaire vous propose une case du type "Toutes les données
utilisateur transmises par cette application sont chiffrées en
transit", cochez-la si votre worker Cloudflare utilise HTTPS (à
vérifier — l'adresse `https://mes-recettes-proxy.fabricemoritel.workers.dev`
utilisée dans le code est bien en HTTPS).

## Section "Pratiques de sécurité"

- "Les données sont-elles chiffrées en transit ?" → Oui (HTTPS partout)
- "Les utilisateurs peuvent-ils demander la suppression de leurs
  données ?" → Non applicable / sans objet, puisque aucune donnée
  n'est collectée par le développeur (tout est déjà sous le contrôle
  direct de l'utilisateur, sur son propre appareil)

## Politique de confidentialité à renseigner

L'URL de la politique de confidentialité fournie séparément
(`POLITIQUE_CONFIDENTIALITE.md`), une fois hébergée en ligne (par
exemple une page sur votre dépôt GitHub Pages), est **obligatoire**
dans Play Console même si l'application ne collecte aucune donnée —
Google exige ce lien pour toutes les applications, sans exception.

## Section "Public cible et contenu"

- Tranche d'âge : selon votre choix, mais évitez de cocher une
  tranche incluant les enfants seuls (moins de 13 ans) — les PWA
  encapsulées (TWA) ne sont pas autorisées à cibler exclusivement les
  enfants par la politique Google (accès potentiel à tout le web).
  Choisissez plutôt "tout public" ou une tranche incluant les adultes.
- Contenu : aucun contenu utilisateur généré n'est partagé
  publiquement (les recettes restent privées, sur l'appareil de
  chacun) — utile à préciser si le formulaire pose la question.

## En résumé

Ce que vous répondez à ce formulaire doit rester **honnête et
factuel** — ne cochez jamais "aucune donnée collectée" si vous avez un
doute, et inversement, ne déclarez pas des collectes qui n'existent
pas. Ce document reflète ce que le code fait réellement, tel qu'audité
ligne par ligne au moment de sa rédaction — si vous ajoutez une
fonctionnalité impliquant un serveur par la suite (statistiques,
compte utilisateur...), pensez à revenir mettre à jour votre
déclaration dans Play Console en conséquence.
