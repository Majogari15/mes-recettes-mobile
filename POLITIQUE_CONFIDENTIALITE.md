# Politique de confidentialité — Mes Recettes, Mes Courses

*Dernière mise à jour : [complétez la date de publication]*

## Résumé en une phrase

Cette application stocke toutes vos données uniquement sur votre
téléphone ; rien n'est envoyé à un serveur, sauf lorsque vous
choisissez vous-même d'importer une recette depuis un lien internet.

## Quelles données sont stockées, et où

Vos recettes, votre garde-manger, vos listes de courses, votre
planning et vos préférences sont enregistrés **uniquement sur votre
appareil** (stockage local du navigateur). Aucun compte n'est requis.
Personne d'autre que vous — ni le développeur, ni un tiers — n'a accès
à ces données.

Si vous désinstallez l'application ou effacez les données de votre
navigateur, ces informations sont supprimées définitivement, à moins
que vous n'ayez exporté une sauvegarde vous-même au préalable.

## Les seuls cas où une information transite par un serveur

**Importer une recette depuis un lien internet** : l'adresse (URL) que
vous saisissez est transmise à un service tiers pour aller chercher le
contenu de cette page et vous le renvoyer. Plusieurs services sont
utilisés l'un après l'autre en cas d'échec du premier, pour maximiser
les chances de réussite de l'import :

1. Un serveur (Cloudflare Worker) exploité par le développeur, en
   premier
2. Si celui-ci échoue : **Jina AI Reader** (r.jina.ai)
3. Si celui-ci échoue aussi : l'un des trois services publics
   **AllOrigins**, **CodeTabs** ou **cors.lol**, en dernier recours

Dans tous les cas, seule l'adresse de la page que vous voulez importer
est transmise — jamais vos recettes, votre garde-manger ou toute autre
donnée personnelle. Ces services ne sont pas exploités par le
développeur (à l'exception du premier) et peuvent avoir leurs propres
règles de conservation, sur lesquelles le développeur n'a pas de
contrôle direct. Cette action ne se produit que si vous choisissez
explicitement d'importer une recette par lien — ce n'est jamais un
comportement automatique ou en arrière-plan.

**Polices de caractères** : l'application utilise des polices
(Fraunces, Inter) chargées depuis Google Fonts. Google peut recevoir
votre adresse IP à cette occasion, comme pour tout site utilisant ce
service — voir la politique de confidentialité de Google.

## Ce que l'application NE fait PAS

- Le développeur ne collecte aucune donnée personnelle (nom, email,
  localisation...) — voir cependant la section précédente : votre
  adresse IP est techniquement visible des quelques services réseau
  sollicités (import par lien, polices), comme pour n'importe quelle
  requête sur internet
- Elle n'utilise aucun outil d'analyse d'audience ou de suivi publicitaire
- Elle n'affiche aucune publicité
- Elle ne partage, ne vend, ni ne transmet vos recettes ou vos données à qui que ce soit
- Elle ne nécessite aucun compte ni inscription

## Permissions de l'appareil utilisées

- **Appareil photo** : uniquement lorsque vous choisissez d'importer
  une recette depuis une photo, ou d'ajouter une photo à une recette
  ou à votre journal de cuisine. Les photos restent stockées localement.
- **Notifications** : uniquement pour vous prévenir qu'un minuteur de
  cuisine est terminé.

## Vos droits

Puisqu'aucune donnée n'est collectée par le développeur, il n'y a rien
à demander de supprimer, corriger ou exporter auprès de lui — vos
données vous appartiennent et restent sous votre contrôle direct sur
votre appareil, à tout moment.

## Contact

Pour toute question sur cette politique de confidentialité :
[votre adresse email]

## Modifications de cette politique

Si cette politique venait à changer (par exemple en cas d'ajout d'une
nouvelle fonctionnalité impliquant un serveur), la date de mise à jour
en haut de ce document sera modifiée en conséquence.
