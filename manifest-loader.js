// Choisit le bon fichier de manifeste selon la langue déjà enregistrée
// (même mécanisme que le reste de l'app, voir i18n.js) — sans ça, le
// nom de l'app et les raccourcis PWA (appui long sur l'icône)
// resteraient toujours en français, même en anglais/espagnol/allemand.
// Créé dynamiquement plutôt qu'en lien statique, pour être certain
// qu'un seul manifeste (le bon) soit jamais chargé.
//
// Fichier externe plutôt qu'un script en ligne dans index.html : reste
// cohérent avec la politique de sécurité du contenu (CSP), qui autorise
// les scripts venant du site lui-même mais jamais de code en ligne —
// ce script s'exécutait auparavant avant que le navigateur n'ait
// rencontré la CSP, ce qui n'était pas incorrect en pratique mais pas
// non plus la structure la plus propre.
(function () {
  var lang = localStorage.getItem("lang") || (navigator.language || "fr").slice(0, 2);
  var supported = ["fr", "en", "es", "de"];
  var file = supported.indexOf(lang) !== -1 && lang !== "fr" ? "manifest-" + lang + ".json" : "manifest.json";
  var link = document.createElement("link");
  link.rel = "manifest";
  link.href = file;
  document.head.appendChild(link);
})();
