// Enregistrement du service worker, le plus tôt possible — indépendant
// du reste de l'initialisation de l'app (app.js), qui peut prendre un
// moment (première ouverture d'IndexedDB, plusieurs magasins à créer).
// Séparé dans ce petit fichier chargé en tout premier, plutôt que
// d'attendre que app.js ait fini de s'exécuter pour s'en charger :
// certains outils d'analyse externes (ex. PWABuilder) semblent
// prendre un instantané trop tôt pour détecter un enregistrement fait
// plus tard dans le cycle de vie de la page, même si ce délai reste
// largement invisible pour un usage normal.
//
// app.js enregistre lui aussi le service worker (voir sa propre
// logique de détection de mise à jour) : appeler register() une
// seconde fois avec la même URL ne crée pas de doublon, le navigateur
// renvoie simplement l'enregistrement déjà en cours — sans risque de
// conflit entre les deux appels.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(function () { /* app.js retentera et gérera l'erreur */ });
}
