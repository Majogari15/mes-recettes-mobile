"use strict";

/* ======================================================================
   BASE DE DONNÉES LOCALE (IndexedDB)
   Toutes les données restent sur l'appareil, rien n'est envoyé nulle
   part. Onze entrepôts : recettes, liste de courses, garde-manger,
   ingrédients personnalisés et leurs surcharges, menus, modèles et
   historique de planning, corbeille, listes de courses enregistrées,
   et un entrepôt clé-valeur générique (réglages, brouillons...).
   ====================================================================== */
const DB_NAME = "mes-recettes-db";
const DB_VERSION = 7;
let dbInstance = null;

function openDB() {
  return new Promise((resolve, reject) => {
    if (dbInstance) return resolve(dbInstance);
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains("recipes")) {
        db.createObjectStore("recipes", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("shopping")) {
        db.createObjectStore("shopping", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("pantry")) {
        db.createObjectStore("pantry", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("ingredients")) {
        db.createObjectStore("ingredients", { keyPath: "name" });
      }
      if (!db.objectStoreNames.contains("ingredientOverrides")) {
        db.createObjectStore("ingredientOverrides", { keyPath: "name" });
      }
      if (!db.objectStoreNames.contains("menus")) {
        db.createObjectStore("menus", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("planTemplates")) {
        db.createObjectStore("planTemplates", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("planHistory")) {
        db.createObjectStore("planHistory", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("trash")) {
        db.createObjectStore("trash", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("savedShoppingLists")) {
        db.createObjectStore("savedShoppingLists", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("kv")) {
        db.createObjectStore("kv", { keyPath: "key" });
      }
    };
    request.onsuccess = (event) => {
      dbInstance = event.target.result;
      resolve(dbInstance);
    };
    request.onerror = () => reject(request.error);
  });
}

function storeAll(storeName) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, "readonly");
        const req = tx.objectStore(storeName).getAll();
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      })
  );
}
function storePut(storeName, value) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, "readwrite");
        tx.objectStore(storeName).put(value);
        tx.oncomplete = () => resolve(value);
        tx.onerror = () => reject(tx.error);
      })
  );
}
function storeDelete(storeName, key) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, "readwrite");
        tx.objectStore(storeName).delete(key);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      })
  );
}
function storeClear(storeName) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, "readwrite");
        tx.objectStore(storeName).clear();
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      })
  );
}
function kvGet(key) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction("kv", "readonly");
        const req = tx.objectStore("kv").get(key);
        req.onsuccess = () => resolve(req.result ? req.result.value : null);
        req.onerror = () => reject(req.error);
      })
  );
}
function kvSet(key, value) {
  return storePut("kv", { key, value });
}

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

// Formate une date selon la langue choisie DANS L'APPLICATION
// (CURRENT_LANG), pas celle du téléphone — sans ça, une application
// réglée en allemand sur un téléphone resté en français affichait quand
// même les dates au format français.
function localeDateStr(date) {
  return new Date(date).toLocaleDateString(CURRENT_LANG);
}
function localeDateTimeStr(date) {
  return new Date(date).toLocaleString(CURRENT_LANG);
}

// Formate une erreur interceptée en texte lisible, quelle que soit sa
// forme réelle — un rejet de promesse n'est pas toujours un vrai objet
// Error (Tesseract, par exemple, peut rejeter sans aucune valeur), et
// `String(undefined)` produit littéralement le texte "undefined" à
// l'écran, ce qui n'aide personne à comprendre ce qui s'est passé.
function formatCaughtError(err) {
  if (err instanceof Error) return (err.name ? err.name + " — " : "") + (err.message || "");
  if (err && typeof err === "object") {
    if (err.message) return String(err.message);
    if (err.type) return "Event — " + err.type; // ex. une erreur DOM capturée comme un Event, pas une vraie Error
    try {
      const asJson = JSON.stringify(err);
      if (asJson && asJson !== "{}") return asJson;
    } catch (e) { /* pas sérialisable, retombe sur String(err) ci-dessous */ }
  }
  return err === undefined || err === null ? "Erreur inconnue" : String(err);
}

/* ======================================================================
   ÉTAT DE L'APPLICATION
   ====================================================================== */
const state = {
  screen: "home", // home | recipes | recipe | form | shopping | pantry
  recipes: [],
  shopping: [],
  pantry: [],
  // Registre des réservations du garde-manger pour la session en
  // cours — un tableau d'entrées {id, ingredientKey, amount,
  // sourceType, sourceId}, voir commitPantryClaim() et
  // computePantryReduction(). Remis à zéro entièrement lors d'une
  // opération globale (vider toute la liste, en charger une autre,
  // restaurer une sauvegarde) ; libéré précisément par source sinon.
  pantryClaimedThisSession: [],
  currentRecipeId: null,
  editingRecipeId: null,
  search: "",
  activeFilter: null, // 'favorite' | 'quick' | 'vegetarian' | 'wishlist'
  viewPersons: 4,
  formIngredients: [],
  formAllergens: [],
  ingredientNames: [],
  formPhoto: null,
  cookingTimers: [],
  shoppingSortByRayon: false,
  currentMenuId: null,
  weeklyPlan: {},
  menus: [],
  planTemplates: [],
  planHistory: [],
  trash: [],
  savedShoppingLists: [],
  whatCanICookIngredients: null,
  _importPrefill: null,
  multiPhotoImport: [], // import par plusieurs photos, en cours de traitement
};

const CATEGORY_OPTIONS = ["Petit-déjeuner", "Entrée", "Plat", "Dessert", "Apéro", "Boisson", "Sauce", "Autre"];
const DIFFICULTY_OPTIONS = ["Facile", "Moyen", "Difficile"];
const UNIT_OPTIONS = ["pièce", "g", "kg", "cl", "L", "c. à soupe", "c. à café", "boîte", "sachet", "pot", "tranche", "gousse", "autre"];

/* ======================================================================
   UTILITAIRES
   ====================================================================== */
function el(html) {
  const tpl = document.createElement("template");
  tpl.innerHTML = html.trim();
  return tpl.content.firstElementChild;
}
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}
// Remplace window.alert()/window.confirm() par des fenêtres propres à
// l'application — les fenêtres natives du navigateur affichent toujours
// le nom du site ("majogari15.github.io indique...") avant le message,
// ce qui n'est pas adapté à une application destinée au grand public.
// Piège le focus (Tab/Maj+Tab) à l'intérieur d'une fenêtre modale, et
// permet de fermer avec la touche Échap — comportement standard attendu
// pour tout dialogue, indispensable à la navigation au clavier.
function trapFocusInModal(sheet, onEscape) {
  const focusable = sheet.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const handler = (e) => {
    if (e.key === "Escape") { e.preventDefault(); onEscape(); return; }
    if (e.key !== "Tab" || !first || !last) return;
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };
  document.addEventListener("keydown", handler);
  return () => document.removeEventListener("keydown", handler);
}

// Ajoute à une fenêtre modale déjà affichée (overlay + sheet, déjà
// insérés dans la page) : rôle de dialogue, piège de focus, fermeture
// par Échap, et restauration du focus vers l'élément qui avait le
// focus juste avant l'ouverture. Utilise un MutationObserver pour
// détecter automatiquement le moment où la fenêtre est retirée du DOM
// — peu importe comment elle se ferme (bouton, clic à l'extérieur,
// Échap...) — plutôt que de devoir adapter la logique de fermeture
// propre à chacune des nombreuses fenêtres de l'application.
function initModalA11y(overlay, sheet, options = {}) {
  if (!sheet.hasAttribute("role")) sheet.setAttribute("role", "dialog");
  sheet.setAttribute("aria-modal", "true");
  // Relie automatiquement le titre (premier <h2>) pour qu'un lecteur
  // d'écran annonce "Scanner un QR code" ou "Journal de cuisine" par
  // exemple, plutôt que simplement "dialogue" sans plus de précision.
  const title = sheet.querySelector("h2");
  if (title && !sheet.hasAttribute("aria-labelledby")) {
    if (!title.id) title.id = `modal-title-${uid()}`;
    sheet.setAttribute("aria-labelledby", title.id);
  }
  const previouslyFocused = document.activeElement;
  // "beforeClose" permet à une fenêtre avec une ressource à libérer
  // (caméra du scanner QR, par exemple) de le faire avant de
  // disparaître — sans ça, une fermeture par Échap contournait ce
  // nettoyage (les fermetures par bouton dédié l'appelaient déjà,
  // mais Échap passait uniquement par overlay.remove() directement).
  let closed = false;
  const closeModal = () => {
    if (closed) return;
    closed = true;
    if (options.beforeClose) options.beforeClose();
    overlay.remove();
  };
  const removeTrap = trapFocusInModal(sheet, closeModal);
  const observer = new MutationObserver(() => {
    if (!document.body.contains(overlay)) {
      removeTrap();
      observer.disconnect();
      // Si la fenêtre a été retirée par un autre chemin que closeModal
      // (ex. un bouton qui appelle lui-même overlay.remove() sans
      // passer par ici), on nettoie quand même une seule fois.
      if (!closed && options.beforeClose) options.beforeClose();
      closed = true;
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
    }
  });
  observer.observe(document.body, { childList: true });
  const focusable = sheet.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (focusable) focusable.focus();
}

function customAlert(message) {
  return new Promise((resolve) => {
    const previouslyFocused = document.activeElement;
    const overlay = el(`<div class="modal-overlay"></div>`);
    const sheet = el(`<div class="modal-sheet" role="alertdialog" aria-modal="true" aria-labelledby="custom-alert-message">
      <p id="custom-alert-message" style="margin:0 0 20px;font-size:15px;line-height:1.5;white-space:pre-line;">${escapeHtml(message)}</p>
      <button type="button" class="btn btn-primary" id="custom-alert-ok">${t("common_ok")}</button>
    </div>`);
    overlay.appendChild(sheet);
    document.body.appendChild(overlay);
    const okBtn = sheet.querySelector("#custom-alert-ok");
    const removeTrap = trapFocusInModal(sheet, close);
    function close() {
      removeTrap();
      overlay.remove();
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
      resolve();
    }
    okBtn.addEventListener("click", close);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
    okBtn.focus();
  });
}
function customPrompt(message, defaultValue) {
  return new Promise((resolve) => {
    const previouslyFocused = document.activeElement;
    const overlay = el(`<div class="modal-overlay"></div>`);
    const sheet = el(`<div class="modal-sheet" role="dialog" aria-modal="true" aria-labelledby="custom-prompt-message">
      <p id="custom-prompt-message" style="margin:0 0 12px;font-size:15px;line-height:1.5;white-space:pre-line;">${escapeHtml(message)}</p>
      <input type="text" id="custom-prompt-input" aria-labelledby="custom-prompt-message" value="${escapeHtml(defaultValue || "")}" style="width:100%;padding:10px;border-radius:8px;border:1px solid var(--border);font-size:15px;margin-bottom:20px;box-sizing:border-box;">
      <div class="modal-actions">
        <button type="button" class="btn btn-outline" id="custom-prompt-cancel">${t("form_cancel")}</button>
        <button type="button" class="btn btn-primary" id="custom-prompt-ok">${t("common_ok")}</button>
      </div>
    </div>`);
    overlay.appendChild(sheet);
    document.body.appendChild(overlay);
    const input = sheet.querySelector("#custom-prompt-input");
    const removeTrap = trapFocusInModal(sheet, () => finish(null));
    function finish(value) {
      removeTrap();
      overlay.remove();
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
      resolve(value);
    }
    sheet.querySelector("#custom-prompt-cancel").addEventListener("click", () => finish(null));
    sheet.querySelector("#custom-prompt-ok").addEventListener("click", () => finish(input.value));
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") finish(input.value); });
    overlay.addEventListener("click", (e) => { if (e.target === overlay) finish(null); });
    input.focus();
    input.select();
  });
}
function customConfirm(message) {
  return new Promise((resolve) => {
    const previouslyFocused = document.activeElement;
    const overlay = el(`<div class="modal-overlay"></div>`);
    const sheet = el(`<div class="modal-sheet" role="dialog" aria-modal="true" aria-labelledby="custom-confirm-message">
      <p id="custom-confirm-message" style="margin:0 0 20px;font-size:15px;line-height:1.5;white-space:pre-line;">${escapeHtml(message)}</p>
      <div class="modal-actions">
        <button type="button" class="btn btn-outline" id="custom-confirm-cancel">${t("form_cancel")}</button>
        <button type="button" class="btn btn-primary" id="custom-confirm-ok">${t("common_ok")}</button>
      </div>
    </div>`);
    overlay.appendChild(sheet);
    document.body.appendChild(overlay);
    const removeTrap = trapFocusInModal(sheet, () => finish(false));
    function finish(value) {
      removeTrap();
      overlay.remove();
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
      resolve(value);
    }
    sheet.querySelector("#custom-confirm-cancel").addEventListener("click", () => finish(false));
    sheet.querySelector("#custom-confirm-ok").addEventListener("click", () => finish(true));
    overlay.addEventListener("click", (e) => { if (e.target === overlay) finish(false); });
    sheet.querySelector("#custom-confirm-ok").focus();
  });
}
function fmtQty(qty) {
  if (qty == null || qty === "") return "";
  const n = Number(qty);
  if (Number.isNaN(n)) return qty;
  if (n === 0) return "0";
  if (n % 1 === 0) return String(n);
  // Pour les très petites quantités non nulles (ex. 1g converti en kg =
  // 0,001), 2 décimales fixes arrondiraient à 0 — on augmente la
  // précision progressivement jusqu'à ce qu'un chiffre significatif
  // apparaisse, plutôt que de perdre la valeur entièrement.
  let decimals = 2;
  while (Math.round(n * Math.pow(10, decimals)) === 0 && decimals < 6) {
    decimals++;
  }
  const factor = Math.pow(10, decimals);
  return String(Math.round(n * factor) / factor).replace(".", ",");
}
function normalize(str) {
  return (str || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}
function parseQtyOrNull(value) {
  if (value === "" || value == null) return null;
  const n = Number(value);
  return Number.isNaN(n) ? null : n;
}

/* ======================================================================
   RENDU — COQUILLE PRINCIPALE
   ====================================================================== */
const app = document.getElementById("app");

let _previousScreen = null;
function render() {
  if (_previousScreen === "importPhoto" && state.screen !== "importPhoto" && sharedTesseractWorker) {
    terminateSharedTesseractWorker().catch(() => { /* sans conséquence, nettoyage best-effort */ });
  }
  _previousScreen = state.screen;
  app.innerHTML = "";
  const topbar = renderTopbar();
  const screenEl = document.createElement("div");
  screenEl.className = "screen";

  switch (state.screen) {
    case "home":
      screenEl.appendChild(renderHome());
      break;
    case "recipes":
      screenEl.appendChild(renderRecipeList());
      break;
    case "recipe":
      screenEl.appendChild(renderRecipeView());
      break;
    case "form":
      screenEl.appendChild(renderRecipeForm());
      break;
    case "shopping":
      screenEl.appendChild(renderShopping());
      break;
    case "pantry":
      screenEl.appendChild(renderPantry());
      break;
    case "ingredients":
      screenEl.appendChild(renderIngredientManage());
      break;
    case "ingredientDuplicates":
      screenEl.appendChild(renderIngredientDuplicates());
      break;
    case "backup":
      screenEl.appendChild(renderBackup());
      break;
    case "diagnostic": {
      const placeholder = el(`<div style="text-align:center;padding:40px 0;color:var(--text-muted);font-size:13px;">${escapeHtml(t("qrcode_loading"))}</div>`);
      screenEl.appendChild(placeholder);
      renderDiagnostic().then((content) => {
        if (state.screen === "diagnostic" && placeholder.isConnected) placeholder.replaceWith(content);
      });
      break;
    }
    case "compare":
      screenEl.appendChild(renderCompare());
      break;
    case "menus":
      screenEl.appendChild(renderMenuList());
      break;
    case "menu":
      screenEl.appendChild(renderMenuDetail());
      break;
    case "planning":
      screenEl.appendChild(renderPlanning());
      break;
    case "planningHistory":
      screenEl.appendChild(renderPlanningHistory());
      break;
    case "importUrl":
      screenEl.appendChild(renderImportUrl());
      break;
    case "unitConverter":
      screenEl.appendChild(renderUnitConverter());
      break;
    case "trash":
      screenEl.appendChild(renderTrash());
      break;
    case "savedShoppingLists":
      screenEl.appendChild(renderSavedShoppingLists());
      break;
    case "whatCanICook":
      screenEl.appendChild(renderWhatCanICook());
      break;
    case "cookbookExport":
      screenEl.appendChild(renderCookbookExport());
      break;
    case "manageSubstitutions":
      screenEl.appendChild(renderManageSubstitutions());
      break;
    case "statistics":
      screenEl.appendChild(renderStatistics());
      break;
    case "importPhoto":
      screenEl.appendChild(renderImportPhoto());
      break;
  }

  app.appendChild(topbar);

  if (state.updateAvailable) {
    const updateBanner = el(`<div style="background:var(--primary);color:#fff;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13px;font-weight:600;">
      <span>${escapeHtml(t("update_available_banner"))}</span>
      <button type="button" style="background:#fff;color:var(--primary);border:none;border-radius:999px;padding:6px 14px;font-weight:700;font-size:12px;">${t("update_available_button")}</button>
    </div>`);
    updateBanner.querySelector("button").addEventListener("click", () => location.reload());
    app.appendChild(updateBanner);
  }

  app.appendChild(screenEl);

  if (!["form", "ingredients", "ingredientDuplicates", "backup", "compare", "menus", "menu", "planning", "planningHistory", "importUrl", "unitConverter", "trash", "savedShoppingLists", "whatCanICook", "cookbookExport", "manageSubstitutions", "statistics", "importPhoto"].includes(state.screen)) {
    app.appendChild(renderBottomNav());
  }
  if (["recipes", "shopping", "pantry"].includes(state.screen)) {
    const fabLabel = state.screen === "pantry" ? t("pantry_add") : state.screen === "shopping" ? t("shopping_title") : t("home_add_recipe");
    const fab = el(`<button class="fab" aria-label="${fabLabel}">＋</button>`);
    fab.addEventListener("click", () => {
      if (state.screen === "pantry") { openPantryAddPrompt(); }
      else if (state.screen === "shopping") { openShoppingAddPrompt(); }
      else { openRecipeForm(null); }
    });
    app.appendChild(fab);
  }
  if (state.screen === "menus") {
    const fab = el(`<button class="fab" aria-label="${t("menu_new_title")}">＋</button>`);
    fab.addEventListener("click", () => openMenuDetail(null));
    app.appendChild(fab);
  }
  if (state.screen === "ingredients") {
    const fab = el(`<button class="fab" aria-label="${t("form_add_ingredient")}">＋</button>`);
    fab.addEventListener("click", () => openIngredientNameModal(null));
    app.appendChild(fab);
  }
  window.scrollTo(0, 0);
}

function renderTopbar() {
  const titles = {
    home: t("app_name"),
    recipes: t("nav_recipes"),
    recipe: null,
    form: state.editingRecipeId ? t("form_title_edit") : t("form_title_new"),
    shopping: t("nav_shopping"),
    pantry: t("nav_pantry"),
    ingredients: t("nav_manage_ingredients"),
    ingredientDuplicates: t("ingredient_duplicates_title"),
    backup: t("nav_backup"),
    compare: t("compare_title"),
    menus: t("nav_menus"),
    menu: state.currentMenuId ? t("menu_edit_title") : t("menu_new_title"),
    planning: t("nav_planning"),
    planningHistory: t("planning_history_title"),
    importUrl: t("nav_import_url"),
    unitConverter: t("unitconv_title"),
    trash: t("trash_title"),
    savedShoppingLists: t("shopping_saved_lists_title"),
    whatCanICook: t("whatcancook_title"),
    cookbookExport: t("home_cookbook_export"),
    manageSubstitutions: t("manage_substitutions_title"),
    statistics: t("stats_title"),
    importPhoto: t("import_photo_title"),
  };
  const showBack = ["recipe", "form", "ingredients", "ingredientDuplicates", "backup", "compare", "menus", "menu", "planning", "planningHistory", "importUrl", "unitConverter", "trash", "savedShoppingLists", "whatCanICook", "cookbookExport", "manageSubstitutions", "statistics", "importPhoto"].includes(state.screen);
  const bar = el(`<div class="topbar"></div>`);

  if (showBack) {
    const back = el(`<button class="back-btn" aria-label="${t("common_back")}">←</button>`);
    back.addEventListener("click", () => {
      if (state.screen === "form") { state.screen = state.editingRecipeId ? "recipe" : "recipes"; }
      else if (state.screen === "menu") { state.screen = "menus"; }
      else if (state.screen === "planningHistory") { state.screen = "planning"; }
      else if (state.screen === "ingredientDuplicates") { state.screen = "ingredients"; }
      else if (state.screen === "savedShoppingLists") { state.screen = "shopping"; }
      else if (["ingredients", "backup", "compare", "menus", "planning", "importUrl", "unitConverter", "trash", "whatCanICook", "cookbookExport", "manageSubstitutions", "statistics", "importPhoto"].includes(state.screen)) { state.screen = "home"; }
      else { state.screen = "recipes"; }
      render();
    });
    bar.appendChild(back);
    const titleWrap = el(`<div class="topbar-title"><span class="subtitle"></span></div>`);
    titleWrap.querySelector("span").textContent = titles[state.screen] || "";
    if (state.screen === "recipe") {
      const r = state.recipes.find((x) => x.id === state.currentRecipeId);
      const h = el(`<h1 style="font-size:18px;">${escapeHtml(r ? r.name : "")}</h1>`);
      bar.appendChild(h);
    } else {
      bar.appendChild(titleWrap);
    }
  } else {
    const titleWrap = el(`<div class="topbar-title"><h1>${escapeHtml(titles[state.screen] || t("app_name"))}</h1></div>`);
    bar.appendChild(titleWrap);
  }

  const actions = el(`<div class="topbar-actions"></div>`);
  if (["home", "recipes", "shopping", "pantry"].includes(state.screen)) {
    const searchBtn = el(`<button class="icon-btn" aria-label="${t("quick_search_label")}">🔍</button>`);
    searchBtn.addEventListener("click", () => {
      openRecipePickerModal((recipe) => {
        state.currentRecipeId = recipe.id;
        state.viewPersons = recipe.defaultPersons || 4;
        state.screen = "recipe";
        render();
      });
    });
    actions.appendChild(searchBtn);

    const donateBtn = el(`<button class="icon-btn" aria-label="${t("home_donate_button")}">☕</button>`);
    donateBtn.addEventListener("click", () => {
      window.open("https://buymeacoffee.com/majogari", "_blank");
    });
    actions.appendChild(donateBtn);

    const langBtn = el(`<button class="icon-btn lang-cycle-btn" aria-label="${t("lang_label")}">${CURRENT_LANG.toUpperCase()}</button>`);
    langBtn.addEventListener("click", () => {
      const order = ["fr", "en", "es", "de"];
      const next = order[(order.indexOf(CURRENT_LANG) + 1) % order.length];
      setLang(next);
      render();
    });
    actions.appendChild(langBtn);

    const themeBtn = el(`<button class="icon-btn" aria-label="${t("theme_toggle")}">🌙</button>`);
    themeBtn.textContent = document.documentElement.dataset.theme === "dark" ? "☀️" : "🌙";
    themeBtn.addEventListener("click", toggleTheme);
    actions.appendChild(themeBtn);
  }
  if (state.screen === "recipe") {
    const r = state.recipes.find((x) => x.id === state.currentRecipeId);
    if (r) {
      const starBtn = el(`<button class="icon-btn" aria-label="${t("form_favorite")}">${r.favorite ? "⭐" : "☆"}</button>`);
      starBtn.addEventListener("click", async () => {
        r.favorite = !r.favorite;
        await storePut("recipes", r);
        render();
      });
      actions.appendChild(starBtn);
    }
  }
  bar.appendChild(actions);
  return bar;
}

function renderBottomNav() {
  const items = [
    { key: "home", icon: "🏠", label: t("nav_home") },
    { key: "recipes", icon: "📖", label: t("nav_recipes") },
    { key: "shopping", icon: "🛒", label: t("nav_shopping") },
    { key: "pantry", icon: "📦", label: t("nav_pantry") },
  ];
  const nav = el(`<nav class="bottom-nav"></nav>`);
  items.forEach((item) => {
    const active = state.screen === item.key || (state.screen === "recipe" && item.key === "recipes");
    const btn = el(`<button class="nav-item ${active ? "active" : ""}" ${active ? 'aria-current="page"' : ""}>
      <span class="nav-icon">${item.icon}</span><span>${escapeHtml(item.label)}</span>
    </button>`);
    btn.addEventListener("click", () => {
      state.screen = item.key;
      state.activeFilter = null;
      render();
    });
    nav.appendChild(btn);
  });
  return nav;
}

/* ======================================================================
   ÉCRAN : ACCUEIL
   ====================================================================== */
function renderHome() {
  const wrap = el(`<div></div>`);
  const installBannerDismissed = !!localStorage.getItem("install_dismissed");
  if (!isRunningStandalone() && (isIosDevice() || (deferredInstallPrompt && installBannerDismissed))) {
    const installBtn = el(`<button class="btn btn-secondary" style="margin-bottom:14px;">${t("home_install_button")}</button>`);
    installBtn.addEventListener("click", triggerInstall);
    wrap.appendChild(installBtn);
  }
  wrap.appendChild(el(`<div class="section"><h2 class="display" style="font-size:22px;">${t("home_title")}</h2></div>`));

  if (state.recipes.length === 0) {
    const restoreHint = el(`<div style="background:var(--primary-light);color:var(--primary);border-radius:12px;padding:12px 14px;margin-bottom:16px;font-size:13px;text-align:center;">
      <p style="margin:0 0 8px;">${escapeHtml(t("home_empty_restore_hint"))}</p>
      <button class="btn btn-secondary" id="empty-restore-btn" style="width:auto;padding:8px 16px;">${t("home_empty_restore_button")}</button>
    </div>`);
    restoreHint.querySelector("#empty-restore-btn").addEventListener("click", () => { state.screen = "backup"; render(); });
    wrap.appendChild(restoreHint);
  }

  const lowStock = getLowStockPantryItems();
  if (lowStock.length) {
    const names = lowStock.map((i) => translateIngredientName(i.name)).sort().join(", ");
    const reminder = el(`<div style="background:var(--accent-light);color:var(--accent);border-radius:12px;padding:10px 14px;margin-bottom:14px;font-size:13px;font-weight:600;text-align:center;cursor:pointer;">
      ${escapeHtml(t("home_low_stock_reminder", { count: String(lowStock.length), names }))}
    </div>`);
    reminder.addEventListener("click", async () => {
      const puts = [];
      lowStock.forEach((pantryItem) => {
        const qty = pantryItem.threshold;
        const existing = state.shopping.find((i) => normalize(i.name) === normalize(pantryItem.name) && i.unit === pantryItem.unit && !i.checked);
        if (existing && qty != null && existing.quantity != null) {
          existing.quantity += qty;
          puts.push(existing);
        } else {
          const item = { id: uid(), name: pantryItem.name, quantity: qty, unit: pantryItem.unit, checked: false };
          state.shopping.push(item);
          puts.push(item);
        }
      });
      await Promise.all(puts.map((item) => storePut("shopping", item)));
      state.screen = "shopping";
      render();
    });
    wrap.appendChild(reminder);
  }

  // Rappel de sauvegarde : dès qu'il y a une donnée importante à
  // protéger (pas seulement des recettes — une personne n'ayant que des
  // courses, un garde-manger, des menus ou des plannings mérite aussi
  // le rappel), et si ça fait longtemps (ou jamais) qu'un export/partage
  // a eu lieu.
  const hasImportantData = [
    state.recipes, state.shopping, state.pantry, state.menus,
    state.planTemplates, state.planHistory, state.savedShoppingLists,
  ].some((arr) => arr.length > 0) || Object.keys(state.weeklyPlan || {}).length > 0;
  const lastBackupAt = localStorage.getItem("lastBackupAt");
  const daysSinceBackup = lastBackupAt ? (Date.now() - new Date(lastBackupAt).getTime()) / 86400000 : Infinity;
  if (hasImportantData && daysSinceBackup >= 14) {
    const backupReminder = el(`<div style="background:var(--accent-light);color:var(--accent);border-radius:12px;padding:10px 14px;margin-bottom:14px;font-size:13px;font-weight:600;text-align:center;cursor:pointer;">
      ${escapeHtml(t("home_backup_reminder"))}
    </div>`);
    backupReminder.addEventListener("click", () => { state.screen = "backup"; render(); });
    wrap.appendChild(backupReminder);
  }

  const shoppingCount = state.shopping.filter((i) => !i.checked).length;

  // Groupe principal (sans en-tête, actions les plus utilisées)
  const mainActions = el(`<div class="section"></div>`);
  const addBtn = el(`<button class="btn btn-primary" style="margin-bottom:10px;">${t("home_add_recipe")}</button>`);
  addBtn.addEventListener("click", () => openRecipeForm(null));
  const viewBtn = el(`<button class="btn btn-secondary" style="margin-bottom:10px;">${t("home_view_recipes")}</button>`);
  viewBtn.addEventListener("click", () => { state.screen = "recipes"; render(); });
  const shopBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_shopping_list")}${shoppingCount ? ` (${shoppingCount})` : ""}</button>`);
  shopBtn.addEventListener("click", () => { state.screen = "shopping"; render(); });
  mainActions.appendChild(viewBtn);
  mainActions.appendChild(shopBtn);
  mainActions.appendChild(addBtn);
  wrap.appendChild(mainActions);

  // Groupe "Importer une recette"
  const importActions = el(`<div class="section"><div class="section-label">${t("home_group_import")}</div></div>`);
  const importUrlBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_import_url")}</button>`);
  importUrlBtn.addEventListener("click", () => { state.screen = "importUrl"; render(); });
  const importPhotoBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_import_photo")}</button>`);
  importPhotoBtn.addEventListener("click", () => { state.screen = "importPhoto"; render(); });
  const importQrBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("shopping_qr_scan_button")}</button>`);
  importQrBtn.addEventListener("click", () => openQrScanModal());
  importActions.appendChild(importUrlBtn);
  importActions.appendChild(importPhotoBtn);
  importActions.appendChild(importQrBtn);
  wrap.appendChild(importActions);

  // Groupe "Organiser"
  const organizeActions = el(`<div class="section"><div class="section-label">${t("home_group_organize")}</div></div>`);
  const ingBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_manage_ingredients")}</button>`);
  ingBtn.addEventListener("click", () => { state.screen = "ingredients"; render(); });
  const manageSubsBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_manage_substitutions")}</button>`);
  manageSubsBtn.addEventListener("click", () => { state.screen = "manageSubstitutions"; render(); });
  const planningBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_planning")}</button>`);
  planningBtn.addEventListener("click", () => { state.screen = "planning"; render(); });
  const menusBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_menus")}</button>`);
  menusBtn.addEventListener("click", () => { state.screen = "menus"; render(); });
  organizeActions.appendChild(ingBtn);
  organizeActions.appendChild(manageSubsBtn);
  organizeActions.appendChild(planningBtn);
  organizeActions.appendChild(menusBtn);
  wrap.appendChild(organizeActions);

  // Groupe "Outils"
  const toolsActions = el(`<div class="section"><div class="section-label">${t("home_group_tools")}</div></div>`);
  const compareBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_compare_recipes")}</button>`);
  compareBtn.addEventListener("click", () => { state.screen = "compare"; render(); });
  const unitConvBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_unit_converter")}</button>`);
  unitConvBtn.addEventListener("click", () => { state.screen = "unitConverter"; render(); });
  const whatCanICookBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_what_can_i_cook")}</button>`);
  whatCanICookBtn.addEventListener("click", () => { state.whatCanICookIngredients = null; state.screen = "whatCanICook"; render(); });
  const cookbookBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_cookbook_export")}</button>`);
  cookbookBtn.addEventListener("click", () => { state.screen = "cookbookExport"; render(); });
  const statsBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_statistics")}</button>`);
  statsBtn.addEventListener("click", () => { state.screen = "statistics"; render(); });
  toolsActions.appendChild(compareBtn);
  toolsActions.appendChild(unitConvBtn);
  toolsActions.appendChild(whatCanICookBtn);
  toolsActions.appendChild(cookbookBtn);
  toolsActions.appendChild(statsBtn);
  wrap.appendChild(toolsActions);

  // Groupe "Autre"
  const otherActions = el(`<div class="section"><div class="section-label">${t("home_group_other")}</div></div>`);
  const trashBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_trash")}${state.trash.length ? ` (${state.trash.length})` : ""}</button>`);
  trashBtn.addEventListener("click", () => { state.screen = "trash"; render(); });
  const backupBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_backup")}</button>`);
  backupBtn.addEventListener("click", () => { state.screen = "backup"; render(); });
  otherActions.appendChild(trashBtn);
  otherActions.appendChild(backupBtn);
  wrap.appendChild(otherActions);

  // Favoris rapides
  const favorites = state.recipes.filter((r) => r.favorite);
  if (favorites.length) {
    const favSection = el(`<div class="section"><div class="section-label">${t("filter_favorites")}</div></div>`);
    const list = el(`<div class="recipe-list"></div>`);
    favorites.slice(0, 4).forEach((r) => list.appendChild(renderRecipeRow(r)));
    favSection.appendChild(list);
    wrap.appendChild(favSection);
  }

  return wrap;
}

/* ======================================================================
   ÉCRAN : LISTE DES RECETTES
   ====================================================================== */
function renderRecipeRow(recipe) {
  const row = el(`<button class="card recipe-row"></button>`);
  const thumb = el(`<div class="recipe-thumb"></div>`);
  if (recipe.photo) {
    thumb.innerHTML = `<img src="${recipe.photo}" alt="">`;
  } else {
    thumb.textContent = "🍽️";
  }
  row.appendChild(thumb);
  const info = el(`<div class="recipe-info">
    <div class="recipe-name">${escapeHtml(recipe.name)}</div>
    <div class="recipe-meta">${escapeHtml(translateCategory(recipe.category))}${recipe.prepTime || recipe.cookTime ? " · " + ((Number(recipe.prepTime) || 0) + (Number(recipe.cookTime) || 0)) + " " + t("recipe_min") : ""}${recipe.personalRating ? ` · ${"★".repeat(recipe.personalRating)}` : ""}</div>
  </div>`);
  row.appendChild(info);
  if (recipe.favorite) row.appendChild(el(`<span class="recipe-star">⭐</span>`));
  row.addEventListener("click", () => {
    state.currentRecipeId = recipe.id;
    state.viewPersons = recipe.defaultPersons || 4;
    state.screen = "recipe";
    render();
  });
  return row;
}

function filteredRecipes() {
  let list = state.recipes.slice();
  const key = normalize(state.search);
  if (key) list = list.filter((r) => normalize(r.name).includes(key));
  if (state.activeFilter === "favorite") list = list.filter((r) => r.favorite);
  if (state.activeFilter === "quick") list = list.filter((r) => (Number(r.prepTime) || 0) + (Number(r.cookTime) || 0) > 0 && (Number(r.prepTime) || 0) + (Number(r.cookTime) || 0) <= 30);
  if (state.activeFilter === "vegetarian") list = list.filter((r) => r.vegetarian);
  if (state.activeFilter === "wishlist") list = list.filter((r) => r.wishlist);
  return list.sort((a, b) => a.name.localeCompare(b.name));
}

function renderRecipeList() {
  const wrap = el(`<div></div>`);
  const searchBar = el(`<div class="search-bar">
    <span>🔍</span>
    <input type="search" placeholder="${t("search_placeholder")}" aria-label="${escapeHtml(t("search_placeholder"))}" />
  </div>`);
  const input = searchBar.querySelector("input");
  input.value = state.search;
  input.addEventListener("input", (e) => {
    state.search = e.target.value;
    renderRecipeListInto(wrap);
  });
  wrap.appendChild(searchBar);

  const chips = el(`<div class="chip-row"></div>`);
  const filters = [
    { key: "favorite", label: t("filter_favorites") },
    { key: "quick", label: t("filter_quick") },
    { key: "vegetarian", label: t("filter_vegetarian") },
    { key: "wishlist", label: t("filter_wishlist") },
  ];
  filters.forEach((f) => {
    const chip = el(`<button class="chip ${state.activeFilter === f.key ? "active" : ""}">${escapeHtml(f.label)}</button>`);
    chip.addEventListener("click", () => {
      state.activeFilter = state.activeFilter === f.key ? null : f.key;
      render();
    });
    chips.appendChild(chip);
  });
  wrap.appendChild(chips);

  const listHolder = el(`<div id="recipe-list-holder"></div>`);
  wrap.appendChild(listHolder);
  fillRecipeListHolder(listHolder);
  return wrap;
}
function renderRecipeListInto(wrap) {
  const holder = wrap.querySelector("#recipe-list-holder");
  if (holder) fillRecipeListHolder(holder);
}
function fillRecipeListHolder(holder) {
  holder.innerHTML = "";
  const list = filteredRecipes();
  if (!state.recipes.length) {
    holder.appendChild(el(`<div class="empty-state"><div class="emoji">🍲</div><p>${escapeHtml(t("no_recipes_yet"))}</p></div>`));
    return;
  }
  if (!list.length) {
    holder.appendChild(el(`<div class="empty-state"><div class="emoji">🔍</div><p>${escapeHtml(t("no_recipes_found"))}</p></div>`));
    return;
  }
  const listEl = el(`<div class="recipe-list"></div>`);
  list.forEach((r) => listEl.appendChild(renderRecipeRow(r)));
  holder.appendChild(listEl);
}

/* ======================================================================
   ÉCRAN : FICHE RECETTE
   ====================================================================== */
function renderRecipeView() {
  const r = state.recipes.find((x) => x.id === state.currentRecipeId);
  if (!r) {
    state.screen = "recipes";
    return el(`<div></div>`);
  }
  const wrap = el(`<div></div>`);
  const hero = el(`<div class="recipe-hero"></div>`);
  hero.innerHTML = r.photo ? `<img src="${r.photo}" alt="">` : "🍽️";
  wrap.appendChild(hero);

  const stats = el(`<div class="stat-row"></div>`);
  if (r.prepTime) stats.appendChild(el(`<div class="stat-pill"><div class="value">${escapeHtml(r.prepTime)}</div><div class="label">${t("recipe_prep")}</div></div>`));
  if (r.cookTime) stats.appendChild(el(`<div class="stat-pill"><div class="value">${escapeHtml(r.cookTime)}</div><div class="label">${t("recipe_cook")}</div></div>`));
  if (r.difficulty) stats.appendChild(el(`<div class="stat-pill"><div class="value">${escapeHtml(translateDifficulty(r.difficulty))}</div><div class="label">${t("recipe_difficulty")}</div></div>`));
  wrap.appendChild(stats);

  const stepperWrap = el(`<div class="section" style="display:flex;align-items:center;justify-content:space-between;"></div>`);
  const stepper = el(`<div class="persons-stepper">
    <button data-action="minus" aria-label="${t("common_minus")}">−</button>
    <span class="count">${state.viewPersons}</span>
    <span style="font-size:13px;color:var(--text-muted);">${t("recipe_persons")}</span>
    <button data-action="plus" aria-label="${t("common_plus")}">+</button>
  </div>`);
  stepper.querySelector('[data-action="minus"]').addEventListener("click", () => {
    if (state.viewPersons > 1) { state.viewPersons--; render(); }
  });
  stepper.querySelector('[data-action="plus"]').addEventListener("click", () => {
    state.viewPersons++; render();
  });
  stepperWrap.appendChild(stepper);
  wrap.appendChild(stepperWrap);

  const ingSection = el(`<div class="section"><div class="section-label">${t("recipe_ingredients")}</div></div>`);
  const ingCard = el(`<div class="card" style="padding: 4px 16px;"></div>`);
  (r.ingredients || []).forEach((ing) => {
    const scaled = ing.quantity ? (Number(ing.quantity) * state.viewPersons) : null;
    ingCard.appendChild(el(`<div class="ingredient-item">
      <span>${escapeHtml(translateIngredientName(ing.name))}</span>
      <span class="ingredient-qty">${scaled != null ? fmtQty(scaled) + " " + escapeHtml(translateUnit(ing.unit)) : ""}</span>
    </div>`));
  });
  ingSection.appendChild(ingCard);
  wrap.appendChild(ingSection);

  if (r.allergens && r.allergens.length) {
    const allergenTags = el(`<div class="allergen-tags"></div>`);
    r.allergens.forEach((a) => allergenTags.appendChild(el(`<span class="allergen-tag">${escapeHtml(translateAllergen(a))}</span>`)));
    wrap.appendChild(el(`<div class="section"><div class="section-label">${t("recipe_allergens")}</div></div>`));
    wrap.lastElementChild.appendChild(allergenTags);
  }

  const nutrition = computeRecipeNutrition(r.ingredients);
  if (nutrition) {
    const nutriLabel = nutrition.partial
      ? `${t("recipe_nutrition_base")} (${t("recipe_nutrition_partial")})`
      : t("recipe_nutrition");
    const nutriCard = el(`<div class="card" style="padding:14px 16px;"></div>`);
    nutriCard.appendChild(el(`<div class="stat-row" style="margin-bottom:0;">
      <div class="stat-pill"><div class="value">${nutrition.kcal}</div><div class="label">${t("nutrition_kcal")}</div></div>
      <div class="stat-pill"><div class="value">${nutrition.protein}g</div><div class="label">${t("nutrition_protein")}</div></div>
      <div class="stat-pill"><div class="value">${nutrition.carbs}g</div><div class="label">${t("nutrition_carbs")}</div></div>
      <div class="stat-pill"><div class="value">${nutrition.fat}g</div><div class="label">${t("nutrition_fat")}</div></div>
    </div>`));
    wrap.appendChild(el(`<div class="section"><div class="section-label">${escapeHtml(nutriLabel)}</div></div>`));
    wrap.lastElementChild.appendChild(nutriCard);
  }

  if (r.description) {
    wrap.appendChild(el(`<div class="section"><div class="section-label">${t("recipe_description")}</div><div class="card" style="padding:14px 16px;"><p class="prose">${escapeHtml(r.description)}</p></div></div>`));
  }
  if (r.notes) {
    wrap.appendChild(el(`<div class="section"><div class="section-label">${t("recipe_notes")}</div><div class="card" style="padding:14px 16px;"><p class="prose">${escapeHtml(r.notes)}</p></div></div>`));
  }
  if (r.personalRating) {
    const filledStars = "★".repeat(r.personalRating) + "☆".repeat(5 - r.personalRating);
    wrap.appendChild(el(`<div class="section"><div class="section-label">${t("recipe_my_rating")}</div><div class="card" style="padding:14px 16px;"><p style="margin:0;font-size:22px;color:var(--accent);letter-spacing:4px;">${filledStars}</p></div></div>`));
  }
  if (r.familyOpinion) {
    wrap.appendChild(el(`<div class="section"><div class="section-label">${t("recipe_family_opinion")}</div><div class="card" style="padding:14px 16px;"><p class="prose">${escapeHtml(r.familyOpinion)}</p></div></div>`));
  }
  if (r.improvementNotes) {
    wrap.appendChild(el(`<div class="section"><div class="section-label">${t("recipe_improvement_notes")}</div><div class="card" style="padding:14px 16px;"><p class="prose">${escapeHtml(r.improvementNotes)}</p></div></div>`));
  }
  if (r.actualDifficulty) {
    wrap.appendChild(el(`<div class="section"><div class="section-label">${t("recipe_actual_difficulty")}</div><div class="card" style="padding:14px 16px;"><p class="prose">${escapeHtml(translateDifficulty(r.actualDifficulty))}</p></div></div>`));
  }

  const actions = el(`<div class="action-row"></div>`);
  const addShopBtn = el(`<button class="btn btn-primary">${t("recipe_add_to_shopping")}</button>`);
  addShopBtn.addEventListener("click", () => addRecipeToShopping(r, state.viewPersons));
  const cookBtn = el(`<button class="btn btn-secondary">${t("recipe_cooking_mode")}</button>`);
  cookBtn.addEventListener("click", () => openCookingMode(r));
  actions.appendChild(addShopBtn);
  actions.appendChild(cookBtn);
  wrap.appendChild(actions);

  const subRow = el(`<div class="action-row"></div>`);
  const subBtn = el(`<button class="btn btn-outline">🔄 ${t("substitutes_title")}</button>`);
  subBtn.addEventListener("click", () => openSubstitutesModal(r));
  const pdfBtn = el(`<button class="btn btn-outline">${t("recipe_export_pdf")}</button>`);
  pdfBtn.addEventListener("click", () => exportRecipePdf(r, state.viewPersons));
  subRow.appendChild(subBtn);
  subRow.appendChild(pdfBtn);
  wrap.appendChild(subRow);

  const logRow = el(`<div class="action-row"></div>`);
  const cookedBtn = el(`<button class="btn btn-secondary">${t("recipe_cooked_button")}</button>`);
  cookedBtn.addEventListener("click", () => openCookLogAddModal(r));
  const viewLogBtn = el(`<button class="btn btn-outline">${t("cooklog_view_button")}${r.cookLog && r.cookLog.length ? ` (${r.cookLog.length})` : ""}</button>`);
  viewLogBtn.addEventListener("click", () => openCookLogViewModal(r));
  logRow.appendChild(cookedBtn);
  logRow.appendChild(viewLogBtn);
  wrap.appendChild(logRow);

  const qrRow = el(`<div class="action-row"></div>`);
  const qrBtn = el(`<button class="btn btn-outline">${t("recipe_qrcode_button")}</button>`);
  qrBtn.addEventListener("click", () => openQrCodeModal(r, state.viewPersons));
  qrRow.appendChild(qrBtn);
  wrap.appendChild(qrRow);

  const editRow = el(`<div class="action-row"></div>`);
  const editBtn = el(`<button class="btn btn-outline">${t("recipe_edit")}</button>`);
  editBtn.addEventListener("click", () => openRecipeForm(r.id));
  const dupBtn = el(`<button class="btn btn-outline">${t("recipe_duplicate")}</button>`);
  dupBtn.addEventListener("click", async () => {
    // Copie complète de la recette (ingrédients, allergènes, photo...)
    // avec un nouvel identifiant, mais sans hériter de l'historique de
    // cuisine ni du statut favori de l'originale — c'est une nouvelle
    // variante, pas encore cuisinée.
    const duplicate = {
      ...r,
      id: uid(),
      name: r.name + t("recipe_duplicate_suffix"),
      favorite: false,
      timesCooked: 0,
      cookLog: [],
      personalRating: 0,
      familyOpinion: "",
      improvementNotes: "",
      actualDifficulty: "",
      notes: "",
      ingredients: (r.ingredients || []).map((i) => ({ ...i })),
      allergens: [...(r.allergens || [])],
    };
    await storePut("recipes", duplicate);
    state.recipes.push(duplicate);
    await customAlert(t("recipe_duplicate_success"));
    state.editingRecipeId = null;
    state.currentRecipeId = duplicate.id;
    state.screen = "recipe";
    render();
  });
  const delBtn = el(`<button class="btn btn-danger">${t("recipe_delete")}</button>`);
  delBtn.addEventListener("click", async () => {
    if (await customConfirm(t("recipe_delete_confirm"))) {
      await moveRecipeToTrash(r);
      state.screen = "recipes";
      render();
    }
  });
  editRow.appendChild(editBtn);
  editRow.appendChild(dupBtn);
  editRow.appendChild(delBtn);
  wrap.appendChild(editRow);

  return wrap;
}

/* ======================================================================
   ÉCRAN : FORMULAIRE RECETTE (ajout / modification)
   ====================================================================== */
// Brouillon automatique : si l'utilisateur quitte accidentellement
// l'application en pleine création OU modification d'une recette,
// l'état du formulaire est capturé quand la page passe en
// arrière-plan, et une restauration est proposée à la prochaine
// ouverture du même contexte (nouvelle recette, ou modification de
// cette même recette précise). Stocké dans IndexedDB plutôt que
// localStorage : une photo en base64 peut facilement dépasser le quota
// habituel de localStorage (quelques Mo), provoquant une erreur
// silencieuse qui empêchait le brouillon d'être réellement sauvegardé.
const RECIPE_DRAFT_KEY = "recipeDraft";
async function captureRecipeFormDraft() {
  if (state.screen !== "form") return;
  const nameEl = document.getElementById("f-name");
  if (!nameEl) return; // le formulaire n'est pas (ou plus) affiché
  const draft = {
    savedAt: new Date().toISOString(),
    recipeId: state.editingRecipeId || null,
    name: nameEl.value,
    category: document.getElementById("f-category").value,
    difficulty: document.getElementById("f-difficulty").value,
    persons: document.getElementById("f-persons").value,
    prepTime: document.getElementById("f-prep").value,
    cookTime: document.getElementById("f-cook").value,
    favorite: document.getElementById("f-favorite").checked,
    vegetarian: document.getElementById("f-vegetarian").checked,
    wishlist: document.getElementById("f-wishlist").checked,
    description: document.getElementById("f-description").value,
    notes: document.getElementById("f-notes").value,
    personalRating: Number(document.getElementById("f-rating-stars").dataset.value) || 0,
    familyOpinion: document.getElementById("f-family-opinion").value,
    improvementNotes: document.getElementById("f-improvement-notes").value,
    actualDifficulty: document.getElementById("f-actual-difficulty").value,
    ingredients: state.formIngredients,
    allergens: state.formAllergens,
    photo: state.formPhoto,
  };
  // Un brouillon vide (rien de saisi) n'a aucun intérêt à être gardé.
  const hasContent = draft.name.trim() || draft.ingredients.some((i) => (i.name || "").trim());
  if (!hasContent) return;
  try {
    await kvSet(RECIPE_DRAFT_KEY, draft);
  } catch (e) {
    // Espace de stockage insuffisant ou autre échec : le brouillon
    // n'est simplement pas conservé, sans casser le reste de l'app.
  }
}
async function getRecipeFormDraft() {
  try {
    return await kvGet(RECIPE_DRAFT_KEY);
  } catch (e) {
    return null;
  }
}
async function clearRecipeFormDraft() {
  try {
    await storeDelete("kv", RECIPE_DRAFT_KEY);
  } catch (e) { /* déjà absent ou erreur sans conséquence */ }
}

async function openRecipeForm(recipeId) {
  state.editingRecipeId = recipeId;
  state._formDraftToApply = null;
  const draft = await getRecipeFormDraft();
  // Un brouillon n'est proposé que s'il correspond exactement au
  // contexte actuel : soit les deux concernent une nouvelle recette
  // (recipeId absent des deux côtés), soit les deux concernent la
  // modification de la même recette précise — jamais un brouillon de
  // modification d'une autre recette, ni un brouillon de nouvelle
  // recette lors de la modification d'une recette existante.
  const draftMatches = draft && (draft.recipeId || null) === (recipeId || null);
  if (recipeId) {
    const r = state.recipes.find((x) => x.id === recipeId);
    if (draftMatches && await customConfirm(t("form_draft_found_confirm", { name: draft.name || r.name }))) {
      state.formIngredients = draft.ingredients && draft.ingredients.length ? draft.ingredients : [{ name: "", quantity: "", unit: "pièce" }];
      state.formPhoto = draft.photo || null;
      state.formAllergens = draft.allergens || [];
      state._formDraftToApply = draft;
    } else {
      if (draftMatches) await clearRecipeFormDraft();
      state.formIngredients = (r.ingredients || []).map((i) => ({ ...i }));
      state.formPhoto = r.photo || null;
      state.formAllergens = (r.allergens || []).slice();
    }
  } else {
    if (draftMatches && await customConfirm(t("form_draft_found_confirm", { name: draft.name || t("form_draft_untitled") }))) {
      state.formIngredients = draft.ingredients && draft.ingredients.length ? draft.ingredients : [{ name: "", quantity: "", unit: "pièce" }];
      state.formPhoto = draft.photo || null;
      state.formAllergens = draft.allergens || [];
      state._formDraftToApply = draft;
    } else {
      if (draftMatches) await clearRecipeFormDraft();
      state.formIngredients = [{ name: "", quantity: "", unit: "pièce" }];
      state.formPhoto = null;
      state.formAllergens = [];
    }
  }
  state.screen = "form";
  render();
}

function renderRecipeForm() {
  const r = state.editingRecipeId ? state.recipes.find((x) => x.id === state.editingRecipeId) : null;
  // Pré-remplissage venant soit d'un import (toujours pour une nouvelle
  // recette uniquement), soit d'un brouillon retrouvé — celui-ci peut
  // concerner aussi bien une nouvelle recette qu'une modification en
  // cours (voir openRecipeForm, qui ne le propose que si son recipeId
  // correspond exactement au contexte actuel). Le brouillon, quand il
  // existe, prend la priorité sur les valeurs déjà enregistrées dans
  // "r" : il représente un état plus récent, pas encore sauvegardé.
  const draftPrefill = state._formDraftToApply || null;
  const importPrefill = !r ? state._importPrefill || null : null;
  const prefill = draftPrefill || importPrefill;
  const isRealImport = !!importPrefill;
  state._importPrefill = null;
  state._formDraftToApply = null;
  const wrap = el(`<form id="recipe-form"></form>`);

  const photoBox = el(`<div class="photo-upload">
    ${state.formPhoto ? `<img src="${state.formPhoto}" alt="">` : `<div>${t("form_photo")}</div>`}
    <input type="file" accept="image/*" capture="environment" id="photo-input">
  </div>`);
  photoBox.querySelector("#photo-input").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      // Redimensionne pour ne pas saturer le stockage local
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const maxW = 800;
        const scale = Math.min(1, maxW / img.width);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        state.formPhoto = canvas.toDataURL("image/jpeg", 0.8);
        render();
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
  wrap.appendChild(photoBox);

  wrap.appendChild(el(`<div class="field">
    <label for="f-name">${t("form_name")}</label>
    <input type="text" id="f-name" placeholder="${t("form_name_placeholder")}" value="${escapeHtml(prefill ? prefill.name : (r ? r.name : ""))}">
  </div>`));

  const row1 = el(`<div class="field-row"></div>`);
  const catField = el(`<div class="field"><label for="f-category">${t("form_category")}</label><select id="f-category"></select></div>`);
  const catSelect = catField.querySelector("select");
  CATEGORY_OPTIONS.forEach((c) => catSelect.appendChild(el(`<option value="${c}">${escapeHtml(translateCategory(c))}</option>`)));
  if (prefill && prefill.category) catSelect.value = prefill.category;
  else if (r) catSelect.value = r.category;
  row1.appendChild(catField);
  const diffField = el(`<div class="field"><label for="f-difficulty">${t("form_difficulty")}</label><select id="f-difficulty"></select></div>`);
  const diffSelect = diffField.querySelector("select");
  DIFFICULTY_OPTIONS.forEach((d) => diffSelect.appendChild(el(`<option value="${d}">${escapeHtml(translateDifficulty(d))}</option>`)));
  if (prefill && prefill.difficulty) diffSelect.value = prefill.difficulty;
  else if (r) diffSelect.value = r.difficulty || "Facile";
  row1.appendChild(diffField);
  wrap.appendChild(row1);

  const row2 = el(`<div class="field-row"></div>`);
  row2.appendChild(el(`<div class="field"><label for="f-persons">${t("form_persons")}</label><input type="number" min="1" id="f-persons" value="${prefill && prefill.persons ? prefill.persons : (r ? r.defaultPersons : 4)}"></div>`));
  row2.appendChild(el(`<div class="field"><label for="f-prep">${t("form_prep_time")}</label><input type="number" min="0" id="f-prep" value="${prefill && prefill.prepTime ? prefill.prepTime : (r && r.prepTime ? r.prepTime : "")}"></div>`));
  row2.appendChild(el(`<div class="field"><label for="f-cook">${t("form_cook_time")}</label><input type="number" min="0" id="f-cook" value="${prefill && prefill.cookTime ? prefill.cookTime : (r && r.cookTime ? r.cookTime : "")}"></div>`));
  wrap.appendChild(row2);

  const checks = el(`<div class="card" style="padding:2px 14px;margin-bottom:20px;">
    <div class="checkbox-row"><input type="checkbox" id="f-favorite" ${prefill ? (prefill.favorite ? "checked" : "") : (r && r.favorite ? "checked" : "")}><label for="f-favorite">${t("form_favorite")}</label></div>
    <div class="checkbox-row"><input type="checkbox" id="f-vegetarian" ${prefill ? (prefill.vegetarian ? "checked" : "") : (r && r.vegetarian ? "checked" : "")}><label for="f-vegetarian">${t("form_vegetarian")}</label></div>
    <div class="checkbox-row"><input type="checkbox" id="f-wishlist" ${prefill ? (prefill.wishlist ? "checked" : "") : (r && r.wishlist ? "checked" : "")}><label for="f-wishlist">${t("form_wishlist")}</label></div>
  </div>`);
  wrap.appendChild(checks);

  const ingSection = el(`<div class="section"><div class="section-label">${t("form_ingredients")}</div>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 12px;line-height:1.4;">${escapeHtml(t("form_ingredients_hint"))}</p>
    ${isRealImport && prefill && prefill.persons && prefill.persons > 1 ? `<div style="background:var(--accent-light);color:var(--accent);border-radius:10px;padding:10px 12px;margin-bottom:12px;font-size:13px;line-height:1.4;">${escapeHtml(t("form_import_quantity_reminder", { persons: String(prefill.persons) }))}</div>` : ""}
  </div>`);
  const ingHolder = el(`<div id="ing-holder"></div>`);
  ingSection.appendChild(ingHolder);
  const addIngBtn = el(`<button type="button" class="btn btn-secondary btn-sm">${t("form_add_ingredient")}</button>`);
  addIngBtn.addEventListener("click", () => {
    state.formIngredients.push({ name: "", quantity: "", unit: "pièce" });
    renderIngredientRows(ingHolder);
  });
  ingSection.appendChild(addIngBtn);
  wrap.appendChild(ingSection);
  renderIngredientRows(ingHolder);

  const allergenSection = el(`<div class="section"><div class="section-label">${t("form_allergens")}</div>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 12px;line-height:1.4;">${escapeHtml(t("form_allergens_hint"))}</p>
  </div>`);
  const allergenHolder = el(`<div id="allergen-holder" class="card allergen-grid" style="padding:2px 14px;margin-bottom:10px;"></div>`);
  allergenSection.appendChild(allergenHolder);
  const detectBtn = el(`<button type="button" class="btn btn-secondary btn-sm">${t("form_detect_allergens")}</button>`);
  detectBtn.addEventListener("click", () => {
    const validNow = state.formIngredients
      .map((i) => ({ name: (i.name || "").trim() }))
      .filter((i) => i.name);
    state.formAllergens = computeRecipeAllergens(validNow);
    renderAllergenCheckboxes(allergenHolder);
  });
  allergenSection.appendChild(detectBtn);
  wrap.appendChild(allergenSection);
  // Détection automatique une seule fois juste après un import (lien,
  // photo, QR code ou brouillon retrouvé) : épargne le geste manuel
  // dans le cas le plus courant, tout en gardant l'avertissement
  // ci-dessus qui rappelle de vérifier le résultat. "prefill" n'est
  // vrai que sur le tout premier rendu suivant l'import (voir plus
  // haut, où il est aussitôt réinitialisé) — un ajout d'ingrédient ou
  // toute autre interaction ultérieure re-render le formulaire sans
  // jamais redéclencher cette détection, donc un décochage manuel
  // reste toujours respecté ensuite. On ne détecte automatiquement que
  // si aucun allergène n'est déjà connu avec certitude par la source de
  // l'import elle-même (un QR code de recette, par exemple, peut
  // directement indiquer les allergènes d'origine — les écraser par une
  // détection seulement basée sur les noms d'ingrédients serait une
  // régression, pas une aide).
  if (prefill && !state.formAllergens.length && state.formIngredients.some((i) => (i.name || "").trim())) {
    state.formAllergens = computeRecipeAllergens(state.formIngredients.map((i) => ({ name: (i.name || "").trim() })).filter((i) => i.name));
  }
  renderAllergenCheckboxes(allergenHolder);

  wrap.appendChild(el(`<div class="field">
    <label for="f-description">${t("form_description")}</label>
    <textarea id="f-description">${escapeHtml(prefill ? prefill.description || "" : (r ? r.description || "" : ""))}</textarea>
  </div>`));
  wrap.appendChild(el(`<div class="field">
    <label for="f-notes">${t("form_notes")}</label>
    <textarea id="f-notes">${escapeHtml(prefill ? prefill.notes || "" : (r ? r.notes || "" : ""))}</textarea>
  </div>`));

  // Note personnelle : 5 étoiles cliquables, valeur gardée dans un
  // attribut data-value plutôt qu'un champ de formulaire classique.
  const initialRating = prefill ? prefill.personalRating || 0 : (r ? r.personalRating || 0 : 0);
  const ratingField = el(`<div class="field">
    <label id="f-rating-label">${t("form_my_rating_label")}</label>
    <div id="f-rating-stars" data-value="${initialRating}" role="radiogroup" aria-labelledby="f-rating-label" style="font-size:30px;letter-spacing:6px;line-height:1;"></div>
  </div>`);
  const starsEl = ratingField.querySelector("#f-rating-stars");
  function renderStars(value) {
    starsEl.dataset.value = String(value);
    // Une seule étoile dans l'ordre de tabulation (comportement
    // standard d'un groupe radio) : celle qui correspond à la valeur
    // actuelle, ou la première si aucune note n'est encore donnée —
    // les flèches permettent ensuite de se déplacer entre elles sans
    // jamais avoir à tabuler cinq fois de suite.
    const tabbableStar = value || 1;
    starsEl.innerHTML = [1, 2, 3, 4, 5].map((n) =>
      `<button type="button" data-star="${n}" role="radio" aria-checked="${n === value}" aria-label="${n}" tabindex="${n === tabbableStar ? "0" : "-1"}" style="background:none;border:none;padding:0 2px;cursor:pointer;font:inherit;color:${n <= value ? "var(--accent)" : "var(--border)"};">★</button>`
    ).join("");
  }
  renderStars(initialRating);
  starsEl.addEventListener("click", (e) => {
    const starEl = e.target.closest("[data-star]");
    if (!starEl) return;
    const clicked = Number(starEl.dataset.star);
    // Cliquer sur l'étoile déjà sélectionnée comme valeur maximale
    // efface la note, pour pouvoir revenir à "pas encore noté".
    renderStars(clicked === Number(starsEl.dataset.value) ? 0 : clicked);
  });
  starsEl.addEventListener("keydown", (e) => {
    const current = Number(starsEl.dataset.value) || 1;
    let next = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") next = Math.min(5, current + 1);
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = Math.max(1, current - 1);
    if (next == null || next === current) return;
    e.preventDefault();
    renderStars(next);
    starsEl.querySelector(`[data-star="${next}"]`).focus();
  });
  wrap.appendChild(ratingField);

  wrap.appendChild(el(`<div class="field">
    <label for="f-family-opinion">${t("form_family_opinion_label")}</label>
    <input type="text" id="f-family-opinion" placeholder="${t("form_family_opinion_placeholder")}" value="${escapeHtml(prefill ? prefill.familyOpinion || "" : (r ? r.familyOpinion || "" : ""))}">
  </div>`));
  wrap.appendChild(el(`<div class="field">
    <label for="f-improvement-notes">${t("form_improvement_notes_label")}</label>
    <input type="text" id="f-improvement-notes" placeholder="${t("form_improvement_notes_placeholder")}" value="${escapeHtml(prefill ? prefill.improvementNotes || "" : (r ? r.improvementNotes || "" : ""))}">
  </div>`));
  const actualDiffField = el(`<div class="field">
    <label for="f-actual-difficulty">${t("form_actual_difficulty_label")}</label>
    <select id="f-actual-difficulty"><option value="">${t("form_actual_difficulty_placeholder")}</option></select>
  </div>`);
  const actualDiffSelect = actualDiffField.querySelector("#f-actual-difficulty");
  DIFFICULTY_OPTIONS.forEach((d) => actualDiffSelect.appendChild(el(`<option value="${d}">${escapeHtml(translateDifficulty(d))}</option>`)));
  actualDiffSelect.value = prefill ? prefill.actualDifficulty || "" : (r ? r.actualDifficulty || "" : "");
  wrap.appendChild(actualDiffField);

  const submitBtn = el(`<button type="submit" class="btn btn-primary" style="margin-bottom:10px;">${t("form_save")}</button>`);
  const cancelBtn = el(`<button type="button" class="btn btn-outline">${t("form_cancel")}</button>`);
  cancelBtn.addEventListener("click", async () => {
    await clearRecipeFormDraft();
    state.screen = r ? "recipe" : "recipes";
    render();
  });
  wrap.appendChild(submitBtn);
  wrap.appendChild(cancelBtn);

  wrap.addEventListener("submit", async (e) => {
    e.preventDefault();
    await saveRecipeForm(wrap, r);
  });

  return wrap;
}

function renderIngredientRows(holder) {
  holder.innerHTML = "";
  state.formIngredients.forEach((ing, idx) => {
    const row = el(`<div class="ing-form-row">
      <div class="autocomplete-wrap"><input type="text" class="ing-name" placeholder="${t("form_ingredient_name")}" aria-label="${escapeHtml(t("form_ingredient_name"))}" value="${escapeHtml(translateIngredientName(ing.name))}"></div>
      <input type="number" step="any" class="qty ing-qty" placeholder="${t("form_ingredient_qty")}" aria-label="${escapeHtml(t("form_ingredient_qty"))}" value="${ing.quantity || ""}">
      <select class="ing-unit" aria-label="${escapeHtml(t("form_ingredient_unit"))}"></select>
      <button type="button" class="remove-ing" aria-label="${t("common_delete")}">${t("form_remove")}</button>
    </div>`);
    const unitSelect = row.querySelector(".ing-unit");
    UNIT_OPTIONS.forEach((u) => unitSelect.appendChild(el(`<option value="${u}">${escapeHtml(translateUnit(u))}</option>`)));
    unitSelect.value = ing.unit || "pièce";

    const nameInput = row.querySelector(".ing-name");
    attachIngredientAutocomplete(nameInput, (value) => (ing.name = value));
    row.querySelector(".ing-qty").addEventListener("input", (e) => (ing.quantity = e.target.value));
    unitSelect.addEventListener("change", (e) => (ing.unit = e.target.value));
    row.querySelector(".remove-ing").addEventListener("click", () => {
      state.formIngredients.splice(idx, 1);
      if (!state.formIngredients.length) state.formIngredients.push({ name: "", quantity: "", unit: "pièce" });
      renderIngredientRows(holder);
    });
    holder.appendChild(row);
  });
}

function renderAllergenCheckboxes(holder) {
  holder.innerHTML = "";
  ALLERGEN_OPTIONS.forEach((allergen) => {
    const id = "allergen-" + normalize(allergen).replace(/[^a-z0-9]/g, "");
    const checked = state.formAllergens.includes(allergen);
    const row = el(`<div class="checkbox-row">
      <input type="checkbox" id="${id}" ${checked ? "checked" : ""}>
      <label for="${id}">${escapeHtml(translateAllergen(allergen))}</label>
    </div>`);
    row.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) {
        if (!state.formAllergens.includes(allergen)) state.formAllergens.push(allergen);
      } else {
        state.formAllergens = state.formAllergens.filter((a) => a !== allergen);
      }
    });
    holder.appendChild(row);
  });
}

async function saveRecipeForm(wrap, existing) {
  const name = wrap.querySelector("#f-name").value.trim();
  if (!name) { await customAlert(t("form_error_name")); return; }
  const validIngredients = state.formIngredients
    .map((i) => ({ name: resolveIngredientInput((i.name || "").trim()), quantity: parseQtyOrNull(i.quantity), unit: i.unit }))
    .filter((i) => i.name);
  if (!validIngredients.length) { await customAlert(t("form_error_ingredient")); return; }

  // Tout ingrédient réellement nouveau (ne correspondant à aucun nom déjà
  // connu, ni en français ni traduit) est ajouté à la liste des
  // ingrédients, pour être immédiatement disponible en autocomplétion
  // partout ailleurs (autre recette, liste de courses, garde-manger) —
  // notamment utile après un import de recette depuis un lien, qui
  // introduit souvent des noms absents de la liste par défaut.
  for (const ing of validIngredients) {
    if (!state.ingredientNames.some((n) => normalize(n) === normalize(ing.name))) {
      await addIngredientName(ing.name);
    }
  }

  const recipe = {
    id: existing ? existing.id : uid(),
    name,
    category: wrap.querySelector("#f-category").value,
    difficulty: wrap.querySelector("#f-difficulty").value,
    defaultPersons: Number(wrap.querySelector("#f-persons").value) || 4,
    prepTime: wrap.querySelector("#f-prep").value ? Number(wrap.querySelector("#f-prep").value) : null,
    cookTime: wrap.querySelector("#f-cook").value ? Number(wrap.querySelector("#f-cook").value) : null,
    favorite: wrap.querySelector("#f-favorite").checked,
    vegetarian: wrap.querySelector("#f-vegetarian").checked,
    wishlist: wrap.querySelector("#f-wishlist").checked,
    ingredients: validIngredients,
    allergens: state.formAllergens.slice(),
    description: wrap.querySelector("#f-description").value.trim(),
    notes: wrap.querySelector("#f-notes").value.trim(),
    personalRating: Number(wrap.querySelector("#f-rating-stars").dataset.value) || 0,
    familyOpinion: wrap.querySelector("#f-family-opinion").value.trim(),
    improvementNotes: wrap.querySelector("#f-improvement-notes").value.trim(),
    actualDifficulty: wrap.querySelector("#f-actual-difficulty").value,
    photo: state.formPhoto,
    createdAt: existing ? existing.createdAt : new Date().toISOString(),
    // Sans cette reprise explicite, modifier une recette existante (même
    // un simple changement de nom) effaçait silencieusement tout
    // l'historique de préparation — puisque l'objet "recipe" ci-dessus
    // est entièrement reconstruit à partir des seuls champs du
    // formulaire, qui ne contient ni le journal ni ce compteur.
    cookLog: existing ? existing.cookLog || [] : [],
    timesCooked: existing ? existing.timesCooked || 0 : 0,
  };
  await storePut("recipes", recipe);
  const idx = state.recipes.findIndex((x) => x.id === recipe.id);
  if (idx >= 0) state.recipes[idx] = recipe; else state.recipes.push(recipe);
  await clearRecipeFormDraft();

  state.currentRecipeId = recipe.id;
  state.viewPersons = recipe.defaultPersons;
  state.screen = "recipe";
  render();
}

/* ======================================================================
   LISTE DE COURSES
   ====================================================================== */
function addRecipeToShoppingSilent(recipe, persons) {
  const items = state.shopping;
  const puts = [];
  (recipe.ingredients || []).forEach((ing) => {
    const qty = ing.quantity != null ? Number(ing.quantity) * persons : null;
    const existing = items.find((i) => normalize(i.name) === normalize(ing.name) && i.unit === ing.unit && !i.checked);
    if (existing && qty != null && existing.quantity != null) {
      existing.quantity += qty;
      puts.push(existing);
    } else {
      const item = { id: uid(), name: ing.name, quantity: qty, unit: ing.unit, checked: false };
      items.push(item);
      puts.push(item);
    }
  });
  return Promise.all(puts.map((item) => storePut("shopping", item)));
}
async function addRecipeToShopping(recipe, persons) {
  const items = state.shopping;
  const summaryLines = [];
  const plan = []; // ingrédients pas entièrement couverts : deviendront un article de courses
  const fullyCoveredClaims = []; // ingrédients entièrement couverts : aucun article de courses ne les représente
  // Copie locale des réservations déjà confirmées : les nouvelles
  // réservations de cette recette y sont ajoutées provisoirement pour
  // le calcul (afin que plusieurs ingrédients identiques dans la même
  // recette se cumulent correctement), sans toucher au vrai état tant
  // que l'utilisateur n'a pas confirmé.
  const pendingClaims = [...state.pantryClaimedThisSession];
  // Identifiant unique de cette opération d'ajout : sert de source pour
  // les réservations d'ingrédients entièrement couverts, qui n'ont pas
  // d'article de courses correspondant auquel s'attacher.
  const operationId = uid();

  (recipe.ingredients || []).forEach((ing) => {
    const neededQty = ing.quantity != null ? Number(ing.quantity) * persons : null;
    const { adjustedQty, reducedAmount, fullyCovered, claimKey, claimAmount } = computePantryReduction(ing.name, ing.unit, neededQty, pendingClaims);
    if (fullyCovered) {
      summaryLines.push(t("pantry_reduction_fully_covered", { name: translateIngredientName(ing.name) }));
    } else if (reducedAmount > 0) {
      summaryLines.push(t("pantry_reduction_reduced", { name: translateIngredientName(ing.name), qty: fmtQty(adjustedQty), unit: translateUnit(ing.unit) }));
    }
    if (claimKey && claimAmount) {
      pendingClaims.push({ ingredientKey: claimKey, amount: claimAmount });
    }
    if (fullyCovered) {
      if (claimKey && claimAmount) fullyCoveredClaims.push({ claimKey, claimAmount });
    } else {
      plan.push({ name: ing.name, quantity: adjustedQty, unit: ing.unit, claimKey, claimAmount });
    }
  });

  if (summaryLines.length) {
    const summaryText = `${t("pantry_reduction_summary_title")}\n\n${summaryLines.join("\n")}\n\n${t("pantry_reduction_confirm_continue")}`;
    if (!await customConfirm(summaryText)) return;
  }
  // Les réservations ne sont appliquées pour de vrai qu'à partir
  // d'ici — après un éventuel "Annuler" ci-dessus, rien n'aura été
  // modifié. Celles des ingrédients entièrement couverts sont
  // attachées à cette opération d'ajout précise (voir operationId).
  fullyCoveredClaims.forEach(({ claimKey, claimAmount }) => commitPantryClaim(claimKey, claimAmount, "recipe", operationId));

  const puts = [];
  plan.forEach((ing) => {
    const existing = items.find((i) => normalize(i.name) === normalize(ing.name) && i.unit === ing.unit && !i.checked);
    let resultItem;
    if (existing && ing.quantity != null && existing.quantity != null) {
      existing.quantity += ing.quantity;
      resultItem = existing;
    } else {
      resultItem = { id: uid(), name: ing.name, quantity: ing.quantity, unit: ing.unit, checked: false };
      items.push(resultItem);
    }
    puts.push(resultItem);
    // Attachée à l'article de courses réel qui en résulte (existant
    // fusionné, ou nouvellement créé) — permet de la libérer
    // précisément si CET article est ensuite supprimé ou modifié.
    if (ing.claimKey && ing.claimAmount) commitPantryClaim(ing.claimKey, ing.claimAmount, "shopping", resultItem.id);
  });
  await Promise.all(puts.map((item) => storePut("shopping", item)));
  state.screen = "shopping";
  render();
}

function renderShopping() {
  const wrap = el(`<div></div>`);
  const topRow = el(`<div class="action-row" style="margin-bottom:14px;"></div>`);
  const savedListsBtn = el(`<button class="btn btn-outline btn-sm">${t("shopping_saved_lists_button")}${state.savedShoppingLists.length ? ` (${state.savedShoppingLists.length})` : ""}</button>`);
  savedListsBtn.addEventListener("click", () => { state.screen = "savedShoppingLists"; render(); });
  const scanBtn = el(`<button class="btn btn-outline btn-sm">${t("shopping_qr_scan_button")}</button>`);
  scanBtn.addEventListener("click", () => openQrScanModal());
  const pasteBtn = el(`<button class="btn btn-outline btn-sm">${t("shopping_qr_paste_button_short")}</button>`);
  pasteBtn.addEventListener("click", () => openQrPasteModal());
  topRow.appendChild(savedListsBtn);
  topRow.appendChild(scanBtn);
  topRow.appendChild(pasteBtn);
  wrap.appendChild(topRow);

  if (!state.shopping.length) {
    wrap.appendChild(el(`<div class="empty-state"><div class="emoji">🛒</div><p>${escapeHtml(t("shopping_empty"))}</p></div>`));
    return wrap;
  }
  const totalCount = state.shopping.length;
  const checked = state.shopping.filter((i) => i.checked).length;
  wrap.appendChild(el(`<div style="font-size:13px;color:var(--text-muted);margin-bottom:8px;">${checked} / ${totalCount} ${t("shopping_checked_of")}</div>`));
  wrap.appendChild(el(`<div class="progress-bar-track" role="progressbar" aria-valuenow="${checked}" aria-valuemin="0" aria-valuemax="${totalCount}" aria-label="${escapeHtml(`${checked} / ${totalCount} ${t("shopping_checked_of")}`)}"><div class="progress-bar-fill" style="width:${totalCount ? (checked / totalCount) * 100 : 0}%"></div></div>`));

  const costInfo = computeShoppingTotal(state.shopping);
  const totalRow = el(`<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;">
    <span style="font-weight:700;font-size:16px;">${t("shopping_total_label")} : ${fmtQty(costInfo.total)} €</span>
    ${costInfo.unknown ? `<span style="font-size:12px;color:var(--text-muted);">${escapeHtml(t("shopping_unknown_price", { count: costInfo.unknown }))}</span>` : ""}
  </div>`);
  wrap.appendChild(totalRow);

  const sortBtn = el(`<button class="btn btn-secondary btn-sm" style="margin-bottom:14px;">${state.shoppingSortByRayon ? t("shopping_sort_by_name") : t("shopping_sort_by_rayon")}</button>`);
  sortBtn.addEventListener("click", () => {
    state.shoppingSortByRayon = !state.shoppingSortByRayon;
    renderShoppingInto(wrap);
  });
  wrap.appendChild(sortBtn);

  const listHolder = el(`<div id="shopping-list-holder"></div>`);
  wrap.appendChild(listHolder);
  fillShoppingList(listHolder, wrap);

  const exportPdfBtn = el(`<button class="btn btn-outline" style="margin-top:20px;">${t("recipe_export_pdf")}</button>`);
  exportPdfBtn.addEventListener("click", () => exportShoppingListPdf());
  wrap.appendChild(exportPdfBtn);

  const shareQrBtn = el(`<button class="btn btn-outline" style="margin-top:10px;">${t("shopping_qr_share_button")}</button>`);
  shareQrBtn.addEventListener("click", () => openShoppingQrCodeModal());
  wrap.appendChild(shareQrBtn);

  const saveListBtn = el(`<button class="btn btn-secondary" style="margin-top:10px;">${t("shopping_save_list_button")}</button>`);
  saveListBtn.addEventListener("click", async () => {
    const name = await customPrompt(t("shopping_save_list_prompt"));
    if (!name || !name.trim()) return;
    const saved = { id: uid(), name: name.trim(), items: JSON.parse(JSON.stringify(state.shopping)), createdAt: new Date().toISOString() };
    await storePut("savedShoppingLists", saved);
    state.savedShoppingLists.push(saved);
    render();
  });
  wrap.appendChild(saveListBtn);

  const clearBtn = el(`<button class="btn btn-danger" style="margin-top:10px;">${t("shopping_clear")}</button>`);
  clearBtn.addEventListener("click", async () => {
    if (await customConfirm(t("shopping_clear_confirm"))) {
      await storeClear("shopping");
      state.shopping = [];
      state.pantryClaimedThisSession = []; persistPantryClaims();
      render();
    }
  });
  wrap.appendChild(clearBtn);
  return wrap;
}

/* ======================================================================
   LISTES DE COURSES ENREGISTRÉES
   ====================================================================== */
function renderSavedShoppingLists() {
  const wrap = el(`<div></div>`);
  if (!state.savedShoppingLists.length) {
    wrap.appendChild(el(`<div class="empty-state"><div class="emoji">📋</div><p>${escapeHtml(t("shopping_saved_lists_empty"))}</p></div>`));
    return wrap;
  }
  state.savedShoppingLists.forEach((saved) => {
    const card = el(`<div class="card" style="padding:14px 16px;margin-bottom:12px;">
      <div style="font-weight:600;margin-bottom:2px;">${escapeHtml(saved.name)}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">${escapeHtml(t("shopping_list_item_count", { count: saved.items.length }))}</div>
      <div class="modal-actions" style="margin-top:0;">
        <button type="button" class="btn btn-outline btn-sm del">${t("common_delete")}</button>
        <button type="button" class="btn btn-primary btn-sm load">${t("shopping_load_list_button")}</button>
      </div>
    </div>`);
    card.querySelector(".load").addEventListener("click", async () => {
      if (state.shopping.length && !await customConfirm(t("shopping_load_list_confirm"))) return;
      await storeClear("shopping");
      const items = JSON.parse(JSON.stringify(saved.items)).map((i) => ({ ...i, id: uid() }));
      for (const item of items) await storePut("shopping", item);
      state.shopping = items;
      state.pantryClaimedThisSession = []; persistPantryClaims();
      state.screen = "shopping";
      render();
    });
    card.querySelector(".del").addEventListener("click", async () => {
      if (!await customConfirm(t("shopping_delete_list_confirm"))) return;
      await storeDelete("savedShoppingLists", saved.id);
      state.savedShoppingLists = state.savedShoppingLists.filter((x) => x.id !== saved.id);
      render();
    });
    wrap.appendChild(card);
  });
  return wrap;
}

function shoppingItemRow(item, wrap) {
  const row = el(`<div class="shopping-item ${item.checked ? "checked" : ""}">
    <input type="checkbox" ${item.checked ? "checked" : ""}>
    <span class="label" style="flex:1;cursor:pointer;">${escapeHtml(translateIngredientName(item.name))}${item.quantity != null ? " — " + fmtQty(item.quantity) + " " + escapeHtml(translateUnit(item.unit)) : ""}</span>
    <button type="button" class="shopping-item-delete" aria-label="${escapeHtml(t("common_delete"))}" style="background:none;border:none;color:var(--text-muted);font-size:18px;padding:4px 8px;cursor:pointer;line-height:1;">×</button>
  </div>`);
  row.querySelector("input").addEventListener("change", async (e) => {
    item.checked = e.target.checked;
    await storePut("shopping", item);
    renderShoppingInto(wrap);
  });
  // Toucher le texte de l'article ouvre la même fenêtre de modification
  // que pour un article du garde-manger — permet de corriger le nom, la
  // quantité ou l'unité sans avoir à tout supprimer et retaper.
  row.querySelector(".label").addEventListener("click", () => openAddItemModal("shopping", item));
  row.querySelector(".shopping-item-delete").addEventListener("click", async (e) => {
    e.stopPropagation();
    if (!await customConfirm(t("shopping_item_delete_confirm", { name: translateIngredientName(item.name) }))) return;
    await storeDelete("shopping", item.id);
    state.shopping = state.shopping.filter((i) => i.id !== item.id);
    releasePantryClaimsForSource("shopping", item.id);
    renderShoppingInto(wrap);
  });
  return row;
}

function fillShoppingList(listHolder, wrap) {
  listHolder.innerHTML = "";
  if (state.shoppingSortByRayon) {
    const byRayon = {};
    state.shopping.forEach((item) => {
      const rayon = getIngredientRayon(item.name);
      (byRayon[rayon] = byRayon[rayon] || []).push(item);
    });
    RAYON_ORDER.forEach((rayon) => {
      const items = byRayon[rayon];
      if (!items || !items.length) return;
      const group = el(`<div class="shopping-group"><div class="shopping-group-title">${escapeHtml(translateRayonName(rayon))}</div></div>`);
      const card = el(`<div class="card" style="padding:4px 16px;"></div>`);
      items
        .slice()
        .sort((a, b) => (a.checked === b.checked ? a.name.localeCompare(b.name) : a.checked ? 1 : -1))
        .forEach((item) => card.appendChild(shoppingItemRow(item, wrap)));
      group.appendChild(card);
      listHolder.appendChild(group);
    });
  } else {
    const list = el(`<div class="card" style="padding:4px 16px;"></div>`);
    state.shopping
      .slice()
      .sort((a, b) => (a.checked === b.checked ? a.name.localeCompare(b.name) : a.checked ? 1 : -1))
      .forEach((item) => list.appendChild(shoppingItemRow(item, wrap)));
    listHolder.appendChild(list);
  }
}
function renderShoppingInto(oldWrap) {
  const fresh = renderShopping();
  oldWrap.replaceWith(fresh);
}
// Articles du garde-manger dont la quantité est passée sous le seuil
// d'alerte défini par l'utilisateur (uniquement ceux où un seuil a été
// renseigné) — même logique que la version bureau.
function getLowStockPantryItems() {
  return state.pantry.filter((item) => item.threshold != null && (item.quantity || 0) < item.threshold);
}

function openAddItemModal(storeName, existingItem) {
  const isEdit = !!existingItem;
  const isPantry = storeName === "pantry";
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${isEdit ? t("form_edit_ingredient") : t("form_add_ingredient")}</h2>
    <div class="field">
      <label for="modal-ing-name">${t("form_ingredient_name")}</label>
      <div class="autocomplete-wrap"><input type="text" id="modal-ing-name" placeholder="${t("form_ingredient_name")}"></div>
    </div>
    <div class="field-row">
      <div class="field"><label for="modal-ing-qty">${t("form_ingredient_qty")}</label><input type="number" step="any" id="modal-ing-qty"></div>
      <div class="field"><label for="modal-ing-unit">${t("form_ingredient_unit")}</label><select id="modal-ing-unit"></select></div>
    </div>
    ${isPantry ? `<div class="field">
      <label for="modal-ing-threshold">${t("pantry_threshold_label")}</label>
      <input type="number" step="any" id="modal-ing-threshold">
      <p style="font-size:12px;color:var(--text-muted);margin:4px 0 0;">${escapeHtml(t("pantry_threshold_hint"))}</p>
    </div>` : ""}
    <div class="modal-actions">
      <button type="button" class="btn btn-outline" id="modal-cancel">${t("form_cancel")}</button>
      <button type="button" class="btn btn-primary" id="modal-confirm">${t("form_save")}</button>
    </div>
  </div>`);
  const unitSelect = sheet.querySelector("#modal-ing-unit");
  UNIT_OPTIONS.forEach((u) => unitSelect.appendChild(el(`<option value="${u}">${escapeHtml(translateUnit(u))}</option>`)));
  unitSelect.value = isEdit ? (existingItem.unit || "pièce") : "pièce";

  let typedName = isEdit ? existingItem.name : "";
  const nameInput = sheet.querySelector("#modal-ing-name");
  if (isEdit) {
    nameInput.value = translateIngredientName(existingItem.name);
    if (existingItem.quantity != null) sheet.querySelector("#modal-ing-qty").value = existingItem.quantity;
    if (isPantry && existingItem.threshold != null) sheet.querySelector("#modal-ing-threshold").value = existingItem.threshold;
  }
  attachIngredientAutocomplete(nameInput, (value) => (typedName = value));

  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  sheet.querySelector("#modal-cancel").addEventListener("click", () => overlay.remove());
  sheet.querySelector("#modal-confirm").addEventListener("click", async () => {
    const name = resolveIngredientInput((typedName || nameInput.value).trim());
    if (!name) { nameInput.focus(); return; }
    let quantity = parseQtyOrNull(sheet.querySelector("#modal-ing-qty").value);
    const unit = unitSelect.value;
    // Déterminé maintenant (avant toute réservation), pour pouvoir
    // attacher précisément la nouvelle réservation à cet article
    // précis — indispensable pour pouvoir la libérer plus tard sans
    // toucher aux réservations d'autres articles.
    const itemId = isEdit ? existingItem.id : uid();

    // Vérifie le garde-manger uniquement pour un nouvel article de la
    // liste de courses (pas en modification, ni pour le garde-manger
    // lui-même, où ça n'aurait pas de sens).
    if (storeName === "shopping" && !isEdit) {
      const { adjustedQty, reducedAmount, fullyCovered, claimKey, claimAmount } = computePantryReduction(name, unit, quantity);
      if (fullyCovered || reducedAmount > 0) {
        const line = fullyCovered
          ? t("pantry_reduction_fully_covered", { name: translateIngredientName(name) })
          : t("pantry_reduction_reduced", { name: translateIngredientName(name), qty: fmtQty(adjustedQty), unit: translateUnit(unit) });
        const summaryText = `${t("pantry_reduction_summary_title")}\n\n${line}\n\n${t("pantry_reduction_confirm_continue")}`;
        if (!await customConfirm(summaryText)) return;
        // La réservation n'est appliquée pour de vrai qu'après ce point,
        // une fois la confirmation acceptée — attachée à cet article de
        // courses précis (voir itemId ci-dessus).
        if (claimKey && claimAmount) commitPantryClaim(claimKey, claimAmount, "shopping", itemId);
        if (fullyCovered) { overlay.remove(); return; }
        quantity = adjustedQty;
      }
    }

    const item = {
      id: itemId,
      name,
      quantity,
      unit,
    };
    if (storeName === "shopping") item.checked = isEdit ? existingItem.checked : false;
    if (isPantry) item.threshold = parseQtyOrNull(sheet.querySelector("#modal-ing-threshold").value);
    await storePut(storeName, item);
    if (storeName === "shopping" && isEdit) {
      // Modifier un article de courses existant rend sa réservation
      // éventuelle obsolète (basée sur l'ancienne quantité) — libère
      // UNIQUEMENT sa propre réservation, jamais celles créées par
      // d'autres articles pour ce même ingrédient.
      releasePantryClaimsForSource("shopping", itemId);
    }
    if (isPantry) {
      // Le stock physique du garde-manger a changé de façon
      // imprévisible (quantité, voire nom si renommé) — toute
      // réservation contre cet ingrédient devient invalide, peu
      // importe quelle source l'avait créée.
      releasePantryClaimsForIngredient(normalize(name));
      if (isEdit && normalize(existingItem.name) !== normalize(name)) {
        releasePantryClaimsForIngredient(normalize(existingItem.name));
      }
    }
    if (isEdit) {
      const idx = state[storeName].findIndex((i) => i.id === existingItem.id);
      if (idx >= 0) state[storeName][idx] = item;
    } else {
      state[storeName].push(item);
    }
    overlay.remove();
    render();
  });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
  nameInput.focus();
}
function openShoppingAddPrompt() {
  openAddItemModal("shopping");
}

/* ======================================================================
   GARDE-MANGER (version simple)
   ====================================================================== */
function renderPantry() {
  const wrap = el(`<div></div>`);
  if (!state.pantry.length) {
    wrap.appendChild(el(`<div class="empty-state"><div class="emoji">📦</div><p>${escapeHtml(t("pantry_empty"))}</p></div>`));
  } else {
    const list = el(`<div class="card" style="padding:4px 16px;margin-bottom:20px;"></div>`);
    state.pantry
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((item) => {
        const row = el(`<div class="shopping-item">
          <span class="label" style="cursor:pointer;">${escapeHtml(translateIngredientName(item.name))}${item.quantity != null ? " — " + fmtQty(item.quantity) + " " + escapeHtml(translateUnit(item.unit)) : ""}${item.threshold != null ? escapeHtml(t("pantry_threshold_suffix", { threshold: fmtQty(item.threshold) })) : ""}</span>
          <button class="remove-ing" style="width:32px;height:32px;" aria-label="${t("common_delete")}">🗑</button>
        </div>`);
        row.querySelector(".label").addEventListener("click", () => openAddItemModal("pantry", item));
        row.querySelector("button").addEventListener("click", async () => {
          await storeDelete("pantry", item.id);
          state.pantry = state.pantry.filter((p) => p.id !== item.id);
          releasePantryClaimsForIngredient(normalize(item.name));
          render();
        });
        list.appendChild(row);
      });
    wrap.appendChild(list);
  }

  // Section des réservations — affichée même si le garde-manger est
  // vide (une réservation peut survivre à la suppression de tous les
  // articles de garde-manger si elle n'a jamais été explicitement
  // effacée), pour que l'utilisateur garde toujours la main dessus.
  wrap.appendChild(el(`<div class="section-label">${t("pantry_reservations_title")}</div>`));
  const reservationsCard = el(`<div class="card" style="padding:14px 16px;"></div>`);
  reservationsCard.appendChild(el(`<p style="font-size:12px;color:var(--text-muted);margin:0 0 12px;">${escapeHtml(t("pantry_reservations_hint"))}</p>`));
  if (!state.pantryClaimedThisSession.length) {
    reservationsCard.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0;">${escapeHtml(t("pantry_reservations_none"))}</p>`));
  } else {
    state.pantryClaimedThisSession.forEach((claim) => {
      let sourceLabel;
      if (claim.sourceType === "recipe") {
        sourceLabel = t("pantry_reservation_from_recipe");
      } else {
        const shoppingItem = state.shopping.find((i) => i.id === claim.sourceId);
        sourceLabel = shoppingItem
          ? t("pantry_reservation_from_shopping", { name: translateIngredientName(shoppingItem.name) })
          : t("pantry_reservation_from_shopping_deleted");
      }
      // "claim.ingredientKey" est normalisée (minuscules, sans accents)
      // — il faut retrouver le nom correctement casé pour que
      // translateIngredientName() le reconnaisse, sinon la traduction
      // échoue silencieusement et affiche la clé brute non traduite.
      const properName = state.ingredientNames.find((n) => normalize(n) === claim.ingredientKey) || claim.ingredientKey;
      const row = el(`<div class="shopping-item">
        <span class="label">${escapeHtml(translateIngredientName(properName))} — ${fmtQty(claim.amount)} <span style="color:var(--text-muted);font-size:12px;">(${escapeHtml(sourceLabel)})</span></span>
        <button class="remove-ing" style="width:32px;height:32px;" aria-label="${escapeHtml(t("pantry_reservation_cancel"))}">🗑</button>
      </div>`);
      row.querySelector("button").addEventListener("click", () => {
        state.pantryClaimedThisSession = state.pantryClaimedThisSession.filter((c) => c.id !== claim.id);
        persistPantryClaims();
        render();
      });
      reservationsCard.appendChild(row);
    });
    const resetBtn = el(`<button type="button" class="btn btn-outline btn-sm" style="margin-top:12px;">${escapeHtml(t("pantry_reservations_reset_all"))}</button>`);
    resetBtn.addEventListener("click", async () => {
      if (!await customConfirm(t("pantry_reservations_reset_confirm"))) return;
      state.pantryClaimedThisSession = [];
      persistPantryClaims();
      render();
    });
    reservationsCard.appendChild(resetBtn);
  }
  wrap.appendChild(reservationsCard);
  return wrap;
}
function openPantryAddPrompt() {
  openAddItemModal("pantry");
}

/* ======================================================================
   GESTION DES INGRÉDIENTS (ajouter / modifier / supprimer)
   ====================================================================== */
function renderIngredientManage() {
  const wrap = el(`<div></div>`);
  const dupBtn = el(`<button class="btn btn-secondary btn-sm" style="margin-bottom:14px;">${t("ingredient_duplicates_button")}</button>`);
  dupBtn.addEventListener("click", () => { state.screen = "ingredientDuplicates"; render(); });
  wrap.appendChild(dupBtn);
  const searchBar = el(`<div class="search-bar">
    <span>🔍</span>
    <input type="search" placeholder="${t("ingredient_search_placeholder")}" aria-label="${escapeHtml(t("ingredient_search_placeholder"))}" />
  </div>`);
  wrap.appendChild(searchBar);
  const listHolder = el(`<div id="ingredient-list-holder"></div>`);
  wrap.appendChild(listHolder);

  function fillList(query) {
    listHolder.innerHTML = "";
    const key = normalize(query || "");
    const names = state.ingredientNames.filter((n) => !key || normalize(n).includes(key));
    if (!names.length) {
      listHolder.appendChild(el(`<div class="empty-state"><div class="emoji">🥕</div><p>${escapeHtml(t("ingredient_no_results"))}</p></div>`));
      return;
    }
    const card = el(`<div class="card" style="padding:2px 14px;"></div>`);
    names.forEach((name) => {
      const row = el(`<div class="ingredient-manage-row">
        <span class="name">${escapeHtml(translateIngredientName(name))}</span>
        <div class="row-actions">
          <button class="edit" aria-label="${t("recipe_edit")}">✏️</button>
          <button class="del" aria-label="${t("common_delete")}">🗑</button>
        </div>
      </div>`);
      row.querySelector(".edit").addEventListener("click", () => openIngredientNameModal(name));
      row.querySelector(".del").addEventListener("click", async () => {
        if (await customConfirm(t("ingredient_delete_confirm", { name }))) {
          await deleteIngredientName(name);
          fillList(searchBar.querySelector("input").value);
        }
      });
      card.appendChild(row);
    });
    listHolder.appendChild(card);
  }
  searchBar.querySelector("input").addEventListener("input", (e) => fillList(e.target.value));
  fillList("");
  return wrap;
}

/* ======================================================================
   VÉRIFICATION DES DOUBLONS D'INGRÉDIENTS
   ====================================================================== */
function renderManageSubstitutions() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;line-height:1.5;">${escapeHtml(t("manage_substitutions_hint"))}</p>`));
  const searchBar = el(`<div class="search-bar">
    <span>🔍</span>
    <input type="search" placeholder="${t("manage_substitutions_search_placeholder")}" aria-label="${escapeHtml(t("manage_substitutions_search_placeholder"))}" />
  </div>`);
  wrap.appendChild(searchBar);
  const listHolder = el(`<div id="subs-list-holder"></div>`);
  wrap.appendChild(listHolder);

  function fillList(query) {
    listHolder.innerHTML = "";
    const key = normalize(query || "");
    const names = (key
      ? state.ingredientNames.filter((n) => normalize(n).includes(key))
      : state.ingredientNames.filter((n) => getIngredientSubstitutes(n).length > 0)
    ).sort(compareIngredientNamesForDisplay);
    if (!names.length) {
      listHolder.appendChild(el(`<div class="empty-state"><div class="emoji">🔄</div><p>${escapeHtml(key ? t("no_recipes_found") : t("manage_substitutions_none"))}</p></div>`));
      return;
    }
    const card = el(`<div class="card" style="padding:2px 16px;"></div>`);
    names.forEach((name) => {
      const subs = getIngredientSubstitutes(name);
      const row = el(`<div class="ingredient-manage-row">
        <span class="name">${escapeHtml(translateIngredientName(name))}${subs.length ? ` <span style="color:var(--text-muted);font-size:12px;">(${escapeHtml(t("manage_substitutions_count", { count: String(subs.length) }))})</span>` : ""}</span>
        <div class="row-actions"><button class="edit" aria-label="${t("recipe_edit")}">✏️</button></div>
      </div>`);
      row.querySelector(".edit").addEventListener("click", () => openIngredientNameModal(name));
      card.appendChild(row);
    });
    listHolder.appendChild(card);
  }
  searchBar.querySelector("input").addEventListener("input", (e) => fillList(e.target.value));
  fillList("");
  return wrap;
}

function renderIngredientDuplicates() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;line-height:1.5;">${escapeHtml(t("ingredient_duplicates_hint"))}</p>`));
  const listHolder = el(`<div id="dup-list-holder"></div>`);
  wrap.appendChild(listHolder);

  function fillList() {
    listHolder.innerHTML = "";
    const allPairs = findSimilarIngredientPairs(state.ingredientNames, 0.9);
    const pairs = allPairs.filter(([a, b]) => !isPairDismissed(a, b));
    if (!pairs.length) {
      listHolder.appendChild(el(`<div class="empty-state"><div class="emoji">✅</div><p>${escapeHtml(t("ingredient_duplicates_none_found"))}</p></div>`));
      return;
    }
    pairs.forEach(([nameA, nameB, ratio]) => {
      const card = el(`<div class="card" style="padding:14px 16px;margin-bottom:12px;">
        <div style="font-weight:600;margin-bottom:2px;">${escapeHtml(translateIngredientName(nameA))} ↔ ${escapeHtml(translateIngredientName(nameB))}</div>
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">${Math.round(ratio * 100)}%</div>
        <div class="modal-actions" style="margin-top:0;">
          <button type="button" class="btn btn-outline btn-sm dismiss-btn">${t("ingredient_duplicates_dismiss_button")}</button>
          <button type="button" class="btn btn-primary btn-sm merge-btn">${t("ingredient_duplicates_merge_button")}</button>
        </div>
      </div>`);
      card.querySelector(".dismiss-btn").addEventListener("click", async () => {
        await dismissPair(nameA, nameB);
        fillList();
      });
      card.querySelector(".merge-btn").addEventListener("click", () => {
        openMergeChoiceModal(nameA, nameB, fillList);
      });
      listHolder.appendChild(card);
    });
  }
  fillList();
  return wrap;
}

function openMergeChoiceModal(nameA, nameB, onDone) {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("ingredient_duplicates_merge_title")}</h2>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("ingredient_duplicates_merge_hint"))}</p>
  </div>`);
  [nameA, nameB].forEach((keep) => {
    const remove = keep === nameA ? nameB : nameA;
    const btn = el(`<button type="button" class="btn btn-outline" style="margin-bottom:10px;">${escapeHtml(translateIngredientName(keep))}</button>`);
    btn.addEventListener("click", async () => {
      await mergeIngredientNames(keep, remove);
      overlay.remove();
      onDone();
    });
    sheet.appendChild(btn);
  });
  const cancelBtn = el(`<button type="button" class="btn btn-outline" style="margin-top:6px;">${t("form_cancel")}</button>`);
  cancelBtn.addEventListener("click", () => overlay.remove());
  sheet.appendChild(cancelBtn);
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
}

function openIngredientNameModal(existingName) {
  const currentAllergens = existingName ? getIngredientAllergens(existingName) : [];
  const currentNutrition = existingName ? getIngredientNutrition(existingName) : null;
  const currentPrice = existingName ? getIngredientPrice(existingName) : null;
  let selectedAllergens = currentAllergens.slice();

  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${existingName ? t("ingredient_edit_title") : t("ingredient_new_title")}</h2>
    <div class="field">
      <label for="modal-ing-rename">${t("ingredient_name_label")}</label>
      <input type="text" id="modal-ing-rename" value="${escapeHtml(existingName || "")}">
    </div>

    <div class="section-label">${t("form_allergens")}</div>
    <div id="modal-allergen-holder" class="card allergen-grid" style="padding:2px 14px;margin-bottom:18px;"></div>

    <div class="section-label">${t("recipe_nutrition")}</div>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 12px;line-height:1.4;">${escapeHtml(t("ingredient_nutrition_hint"))}</p>
    <div class="field-row">
      <div class="field"><label for="modal-nutri-kcal">${t("nutrition_kcal")}</label><input type="number" min="0" step="any" id="modal-nutri-kcal" value="${currentNutrition ? currentNutrition.kcal : ""}"></div>
      <div class="field"><label for="modal-nutri-protein">${t("nutrition_protein")} (g)</label><input type="number" min="0" step="any" id="modal-nutri-protein" value="${currentNutrition ? currentNutrition.protein_g : ""}"></div>
    </div>
    <div class="field-row">
      <div class="field"><label for="modal-nutri-carbs">${t("nutrition_carbs")} (g)</label><input type="number" min="0" step="any" id="modal-nutri-carbs" value="${currentNutrition ? currentNutrition.carbs_g : ""}"></div>
      <div class="field"><label for="modal-nutri-fat">${t("nutrition_fat")} (g)</label><input type="number" min="0" step="any" id="modal-nutri-fat" value="${currentNutrition ? currentNutrition.fat_g : ""}"></div>
    </div>

    <div class="section-label">${t("ingredient_price_label")}</div>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 12px;line-height:1.4;">${escapeHtml(t("ingredient_price_hint"))}</p>
    <div class="field-row">
      <div class="field"><label for="modal-price-amount">${t("ingredient_price_label")}</label><input type="number" min="0" step="any" id="modal-price-amount" value="${currentPrice ? currentPrice.amount : ""}"></div>
      <div class="field"><label for="modal-price-unit">${t("ingredient_price_for")}</label><select id="modal-price-unit"></select></div>
    </div>

    <div class="section-label">${t("ingredient_substitutes_label")}</div>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 12px;line-height:1.4;">${escapeHtml(t("ingredient_substitutes_hint"))}</p>
    <div id="modal-substitutes-holder"></div>

    <div class="modal-actions">
      <button type="button" class="btn btn-outline" id="modal-cancel">${t("form_cancel")}</button>
      <button type="button" class="btn btn-primary" id="modal-confirm">${t("form_save")}</button>
    </div>
  </div>`);

  const allergenHolder = sheet.querySelector("#modal-allergen-holder");
  ALLERGEN_OPTIONS.forEach((allergen) => {
    const id = "modal-allergen-" + normalize(allergen).replace(/[^a-z0-9]/g, "");
    const checked = selectedAllergens.includes(allergen);
    const row = el(`<div class="checkbox-row">
      <input type="checkbox" id="${id}" ${checked ? "checked" : ""}>
      <label for="${id}">${escapeHtml(translateAllergen(allergen))}</label>
    </div>`);
    row.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) {
        if (!selectedAllergens.includes(allergen)) selectedAllergens.push(allergen);
      } else {
        selectedAllergens = selectedAllergens.filter((a) => a !== allergen);
      }
    });
    allergenHolder.appendChild(row);
  });

  const priceUnitSelect = sheet.querySelector("#modal-price-unit");
  UNIT_OPTIONS.filter((u) => u !== "autre").forEach((u) => priceUnitSelect.appendChild(el(`<option value="${u}">${escapeHtml(translateUnit(u))}</option>`)));
  priceUnitSelect.value = currentPrice ? currentPrice.unit : "kg";

  const substitutesHolder = sheet.querySelector("#modal-substitutes-holder");
  let customSubstitutes = existingName ? getCustomSubstitutes(existingName).map((s) => ({ ...s })) : [];
  function fillSubstitutes() {
    substitutesHolder.innerHTML = "";
    customSubstitutes.forEach((sub, idx) => {
      const row = el(`<div class="ing-form-row">
        <div class="autocomplete-wrap" style="flex:1;"><input type="text" class="sub-name" placeholder="${t("ingredient_substitute_name_placeholder")}" aria-label="${escapeHtml(t("ingredient_substitute_name_placeholder"))}" value="${escapeHtml(sub.nom)}"></div>
        <input type="text" class="sub-note" placeholder="${t("ingredient_substitute_note_placeholder")}" aria-label="${escapeHtml(t("ingredient_substitute_note_placeholder"))}" value="${escapeHtml(sub.note || "")}" style="flex:1.4;">
        <button type="button" class="remove-ing" aria-label="${t("common_delete")}">${t("form_remove")}</button>
      </div>`);
      const subNameInput = row.querySelector(".sub-name");
      attachIngredientAutocomplete(subNameInput, (value) => (sub.nom = value));
      row.querySelector(".sub-note").addEventListener("input", (e) => (sub.note = e.target.value));
      row.querySelector(".remove-ing").addEventListener("click", () => {
        customSubstitutes.splice(idx, 1);
        fillSubstitutes();
      });
      substitutesHolder.appendChild(row);
    });
  }
  fillSubstitutes();
  const addSubstituteBtn = el(`<button type="button" class="btn btn-secondary btn-sm" style="margin-bottom:20px;">${t("ingredient_add_substitute")}</button>`);
  addSubstituteBtn.addEventListener("click", () => {
    customSubstitutes.push({ nom: "", note: "" });
    fillSubstitutes();
  });
  substitutesHolder.insertAdjacentElement("afterend", addSubstituteBtn);

  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  sheet.querySelector("#modal-cancel").addEventListener("click", () => overlay.remove());
  const input = sheet.querySelector("#modal-ing-rename");
  sheet.querySelector("#modal-confirm").addEventListener("click", async () => {
    const value = input.value.trim();
    if (!value) { input.focus(); return; }
    if (existingName) {
      if (value !== existingName && state.ingredientNames.some((n) => normalize(n) === normalize(value))) {
        await customAlert(t("ingredient_already_exists"));
        return;
      }
      if (value !== existingName) await renameIngredientName(existingName, value);
    } else {
      if (state.ingredientNames.some((n) => normalize(n) === normalize(value))) {
        await customAlert(t("ingredient_already_exists"));
        return;
      }
      await addIngredientName(value);
    }
    const kcal = parseQtyOrNull(sheet.querySelector("#modal-nutri-kcal").value);
    const protein = parseQtyOrNull(sheet.querySelector("#modal-nutri-protein").value);
    const carbs = parseQtyOrNull(sheet.querySelector("#modal-nutri-carbs").value);
    const fat = parseQtyOrNull(sheet.querySelector("#modal-nutri-fat").value);
    const hasNutrition = kcal != null || protein != null || carbs != null || fat != null;
    const nutrition = hasNutrition
      ? { kcal: kcal || 0, protein_g: protein || 0, carbs_g: carbs || 0, fat_g: fat || 0 }
      : null;
    const priceAmount = parseQtyOrNull(sheet.querySelector("#modal-price-amount").value);
    const price = priceAmount != null ? { amount: priceAmount, unit: priceUnitSelect.value } : null;
    const validSubstitutes = customSubstitutes
      .map((s) => ({ nom: (s.nom || "").trim(), note: (s.note || "").trim() }))
      .filter((s) => s.nom);
    await setIngredientOverride(value, selectedAllergens, nutrition, price, validSubstitutes);
    overlay.remove();
    render();
  });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
  input.focus();
  input.select();
}

/* ======================================================================
   SUBSTITUTS D'INGRÉDIENTS
   ====================================================================== */
/* ======================================================================
   EXPORT PDF D'UNE RECETTE
   ====================================================================== */
// Dessine le contenu d'une recette dans un PDF déjà positionné en début
// de page (y=22) — logique partagée entre l'export d'une seule recette
// et l'export "livre de cuisine" (plusieurs recettes à la suite).
function drawRecipeContent(doc, recipe, persons, margin, maxWidth, includePhoto) {
  let y = 22;

  function ensureSpace(needed) {
    if (y + needed > 280) {
      doc.addPage();
      y = 20;
    }
  }
  function heading(text) {
    ensureSpace(12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.text(text, margin, y);
    y += 8;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
  }
  function paragraph(text) {
    doc.splitTextToSize(text, maxWidth).forEach((line) => {
      ensureSpace(6);
      doc.text(line, margin, y);
      y += 6;
    });
  }

  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.splitTextToSize(recipe.name, maxWidth).forEach((line) => {
    doc.text(line, margin, y);
    y += 9;
  });

  if (includePhoto && recipe.photo) {
    try {
      const props = doc.getImageProperties(recipe.photo);
      const maxPhotoHeight = 85;
      let displayWidth = maxWidth;
      let displayHeight = displayWidth * (props.height / props.width);
      if (displayHeight > maxPhotoHeight) {
        // Repasse les deux dimensions en proportion plutôt que de ne
        // plafonner que la hauteur, qui aurait étiré l'image.
        displayHeight = maxPhotoHeight;
        displayWidth = displayHeight * (props.width / props.height);
      }
      ensureSpace(displayHeight + 6);
      doc.addImage(recipe.photo, "JPEG", margin, y, displayWidth, displayHeight);
      y += displayHeight + 8;
    } catch (e) {
      // Photo illisible (format inattendu) : on continue sans elle plutôt
      // que de faire échouer tout l'export.
    }
  }

  // Les 4 informations clés (catégorie, personnes, préparation, cuisson)
  // sont alignées sur une seule ligne, en colonnes de largeur fixe —
  // plus lisible qu'empilées, et cohérent d'une recette à l'autre dans
  // le livre de cuisine.
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  const colWidth = maxWidth / 4;
  doc.text(translateCategory(recipe.category), margin, y);
  doc.text(`${persons} ${t("recipe_persons")}`, margin + colWidth, y);
  if (recipe.prepTime) doc.text(`${t("pdf_prep_label")}: ${recipe.prepTime} ${t("recipe_min")}`, margin + colWidth * 2, y);
  if (recipe.cookTime) doc.text(`${t("pdf_cook_label")}: ${recipe.cookTime} ${t("recipe_min")}`, margin + colWidth * 3, y);
  y += 8;
  doc.setFontSize(11);
  if (recipe.difficulty) { doc.text(`${t("pdf_difficulty_label")}: ${translateDifficulty(recipe.difficulty)}`, margin, y); y += 6; }
  y += 5;

  heading(t("pdf_ingredients_label"));
  (recipe.ingredients || []).forEach((ing) => {
    ensureSpace(6);
    const scaled = ing.quantity != null ? ing.quantity * persons : null;
    const qty = scaled != null ? `${fmtQty(scaled)} ${translateUnit(ing.unit)} ` : "";
    doc.text(`-  ${qty}${translateIngredientName(ing.name)}`, margin, y);
    y += 6;
  });
  y += 5;

  if (recipe.description) {
    heading(t("pdf_description_label"));
    paragraph(recipe.description);
    y += 5;
  }
  if (recipe.notes) {
    heading(t("pdf_notes_label"));
    paragraph(recipe.notes);
    y += 5;
  }
  if (recipe.personalRating) {
    heading(t("recipe_my_rating"));
    // Le texte simple "X / 5" plutôt que les caractères ★/☆ : la
    // police PDF actuelle ne les prend pas correctement en charge et
    // peut afficher d'autres symboles à la place.
    paragraph(`${recipe.personalRating} / 5`);
    y += 5;
  }
  if (recipe.familyOpinion) {
    heading(t("recipe_family_opinion"));
    paragraph(recipe.familyOpinion);
    y += 5;
  }
  if (recipe.improvementNotes) {
    heading(t("recipe_improvement_notes"));
    paragraph(recipe.improvementNotes);
    y += 5;
  }
  if (recipe.actualDifficulty) {
    heading(t("recipe_actual_difficulty"));
    paragraph(translateDifficulty(recipe.actualDifficulty));
  }

  doc.setFontSize(8);
  doc.setTextColor(150);
  doc.text(t("pdf_generated_by"), margin, 290);
  doc.setTextColor(0);
}

async function exportRecipePdf(recipe, persons) {
  if (!window.jspdf) {
    await customAlert(t("backup_import_error"));
    return;
  }
  const includePhoto = recipe.photo ? await customConfirm(t("pdf_include_photo_confirm")) : false;
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const margin = 20;
  const maxWidth = doc.internal.pageSize.getWidth() - margin * 2;

  drawRecipeContent(doc, recipe, persons, margin, maxWidth, includePhoto);

  const safeName = recipe.name.replace(/[^\w\s-]/g, "").trim() || "recette";
  doc.save(`${safeName}.pdf`);
}

async function exportShoppingListPdf() {
  if (!window.jspdf) {
    await customAlert(t("backup_import_error"));
    return;
  }
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const margin = 20;
  let y = 22;

  function ensureSpace(needed) {
    if (y + needed > 280) {
      doc.addPage();
      y = 20;
    }
  }
  function itemLine(item) {
    ensureSpace(6);
    const qty = item.quantity != null ? `${fmtQty(item.quantity)} ${translateUnit(item.unit)} ` : "";
    const box = item.checked ? "[x] " : "[ ] ";
    doc.text(`${box}${qty}${translateIngredientName(item.name)}`, margin, y);
    y += 6;
  }

  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.text(t("shopping_title"), margin, y);
  y += 10;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);

  if (state.shoppingSortByRayon) {
    const byRayon = {};
    state.shopping.forEach((item) => {
      const rayon = getIngredientRayon(item.name);
      (byRayon[rayon] = byRayon[rayon] || []).push(item);
    });
    RAYON_ORDER.forEach((rayon) => {
      const items = byRayon[rayon];
      if (!items || !items.length) return;
      ensureSpace(10);
      doc.setFont("helvetica", "bold");
      doc.text(translateRayonName(rayon), margin, y);
      y += 7;
      doc.setFont("helvetica", "normal");
      items.forEach(itemLine);
      y += 3;
    });
  } else {
    state.shopping.forEach(itemLine);
  }

  doc.setFontSize(8);
  doc.setTextColor(150);
  doc.text(t("pdf_generated_by"), margin, 290);
  doc.save(`${t("pdf_shopping_filename")}.pdf`);
}

// Génère un seul PDF regroupant plusieurs recettes : une page de garde,
// un sommaire, puis une recette par page (ou plus si elle est longue).
// Les numéros de page du sommaire sont remplis après coup, une fois que
// la vraie page de chaque recette est connue (chaque recette démarre
// toujours sur une page neuve, ce qui rend ce numéro prévisible).
async function exportCookbookPdf(recipes, includePhotos) {
  if (!window.jspdf) {
    await customAlert(t("backup_import_error"));
    return;
  }
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const margin = 20;
  const pageWidth = doc.internal.pageSize.getWidth();
  const maxWidth = pageWidth - margin * 2;

  // Page de garde
  doc.setFont("helvetica", "bold");
  doc.setFontSize(28);
  doc.splitTextToSize(t("cookbook_title"), maxWidth).forEach((line, idx) => {
    doc.text(line, margin, 100 + idx * 11);
  });
  doc.setFont("helvetica", "normal");
  doc.setFontSize(12);
  doc.text(localeDateStr(new Date()), margin, 125);
  doc.text(t("cookbook_recipe_count", { count: String(recipes.length) }), margin, 133);

  // Sommaire : une page dédiée (ou plusieurs si beaucoup de recettes),
  // avec le nom de chaque recette pour l'instant, le numéro de page
  // sera ajouté après coup.
  doc.addPage();
  let tocY = 22;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text(t("cookbook_toc_title"), margin, tocY);
  tocY += 12;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  const tocEntries = [];
  recipes.forEach((recipe) => {
    if (tocY > 280) {
      doc.addPage();
      tocY = 22;
    }
    doc.text(recipe.name, margin, tocY);
    tocEntries.push({ recipe, tocPageIndex: doc.internal.getNumberOfPages(), tocY });
    tocY += 8;
  });

  // Une recette par page (toujours démarrée sur une page neuve, pour
  // que son numéro de page soit connu à l'avance).
  tocEntries.forEach((entry) => {
    doc.addPage();
    entry.pageNumber = doc.internal.getNumberOfPages();
    drawRecipeContent(doc, entry.recipe, entry.recipe.defaultPersons || 4, margin, maxWidth, includePhotos);
  });

  // Retour sur les pages du sommaire pour y écrire les numéros de page,
  // maintenant connus.
  tocEntries.forEach((entry) => {
    doc.setPage(entry.tocPageIndex);
    doc.text(String(entry.pageNumber), pageWidth - margin, entry.tocY, { align: "right" });
  });

  doc.save(`${t("pdf_recipes_filename")}.pdf`);
}

function renderCookbookExport() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;line-height:1.5;">${escapeHtml(t("cookbook_export_hint"))}</p>`));

  const sortedRecipes = state.recipes.slice().sort((a, b) => a.name.localeCompare(b.name, "fr"));
  const selected = new Set();

  const toggleRow = el(`<div class="action-row" style="margin-bottom:14px;"></div>`);
  const selectAllBtn = el(`<button class="btn btn-outline btn-sm">${t("cookbook_select_all")}</button>`);
  const deselectAllBtn = el(`<button class="btn btn-outline btn-sm">${t("cookbook_deselect_all")}</button>`);
  toggleRow.appendChild(selectAllBtn);
  toggleRow.appendChild(deselectAllBtn);
  wrap.appendChild(toggleRow);

  const listCard = el(`<div class="card" style="padding:2px 16px;margin-bottom:16px;"></div>`);
  const checkboxes = [];
  sortedRecipes.forEach((recipe) => {
    const row = el(`<div class="checkbox-row">
      <input type="checkbox" id="cb-${recipe.id}">
      <label for="cb-${recipe.id}">${escapeHtml(recipe.name)}</label>
    </div>`);
    const checkbox = row.querySelector("input");
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) selected.add(recipe.id);
      else selected.delete(recipe.id);
    });
    checkboxes.push(checkbox);
    listCard.appendChild(row);
  });
  wrap.appendChild(listCard);

  selectAllBtn.addEventListener("click", () => {
    checkboxes.forEach((cb) => { cb.checked = true; selected.add(cb.id.replace("cb-", "")); });
  });
  deselectAllBtn.addEventListener("click", () => {
    checkboxes.forEach((cb) => (cb.checked = false));
    selected.clear();
  });

  const photosRow = el(`<div class="checkbox-row" style="margin-bottom:16px;">
    <input type="checkbox" id="cb-include-photos">
    <label for="cb-include-photos">${t("cookbook_include_photos")}</label>
  </div>`);
  wrap.appendChild(photosRow);

  const exportBtn = el(`<button class="btn btn-primary">${t("cookbook_export_button")}</button>`);
  exportBtn.addEventListener("click", async () => {
    if (!selected.size) { await customAlert(t("cookbook_no_selection")); return; }
    const chosen = sortedRecipes.filter((r) => selected.has(r.id));
    const includePhotos = wrap.querySelector("#cb-include-photos").checked;
    exportCookbookPdf(chosen, includePhotos);
  });
  wrap.appendChild(exportBtn);

  return wrap;
}

/* ======================================================================
   QR CODE D'UNE RECETTE
   ====================================================================== */
// Charge la bibliothèque de QR code à la demande plutôt que de compter
// uniquement sur la balise <script> statique de la page : ça élimine
// tout risque de dépendre d'un ordre/délai de chargement, et permet de
// remonter une vraie erreur si le chargement échoue réellement (plutôt
// que d'afficher un message générique et sans rapport).
let qrCodeLibPromise = null;
function loadQrCodeLib() {
  if (window.qrcode) return Promise.resolve();
  if (qrCodeLibPromise) return qrCodeLibPromise;
  qrCodeLibPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "./lib/qrcode-generator.js";
    script.onload = () => resolve();
    script.onerror = () => { qrCodeLibPromise = null; reject(new Error("qrcode_lib_load_failed")); };
    document.head.appendChild(script);
  });
  return qrCodeLibPromise;
}
// Construit une balise <img> (PNG en base64) contenant le QR code du
// texte donné — l'API de qrcode-generator est volontairement très
// simple (pas de canvas requis), pour une compatibilité maximale même
// avec d'anciens navigateurs Android.
// Le "type" (1 à 40) détermine la taille/capacité du QR code pour cette
// bibliothèque — 0 n'est pas une valeur valide pour "automatique" comme
// on aurait pu le supposer, ce qui provoquait une erreur interne. On
// essaie donc des tailles croissantes jusqu'à ce qu'une soit assez
// grande pour contenir le texte.
function generateQrCodeImgTag(text) {
  // La version de la bibliothèque réellement chargée (1.0.3) n'expose
  // pas de propriété "stringToBytesFuncs" — la vérification qui suivait
  // auparavant ne s'activait donc jamais, et l'encodage par défaut de la
  // bibliothèque (un octet par caractère, tronqué) corrompait tous les
  // caractères accentués (é, è, à...). Or même une recette presque vide
  // contient "Préparation", "Ingrédients", "Allergènes" ou "pièce" — un
  // seul caractère mal encodé suffit à faire échouer certains lecteurs
  // (jsQR notamment, plus strict qu'un décodeur comme celui utilisé
  // pour vérifier ce correctif). TextEncoder est une API standard des
  // navigateurs qui produit un vrai encodage UTF-8 fiable.
  if (window.TextEncoder) {
    window.qrcode.stringToBytes = (s) => Array.from(new TextEncoder().encode(s));
  }
  let lastError = null;
  for (let typeNumber = 1; typeNumber <= 40; typeNumber++) {
    try {
      // Niveau "L" (plutôt que "M") : moins de redondance de correction
      // d'erreur, donc un code moins dense pour la même quantité de
      // texte — plus simple à décoder correctement une fois
      // photographié depuis un autre appareil.
      const qr = window.qrcode(typeNumber, "L");
      qr.addData(text);
      qr.make();
      // Important : le deuxième paramètre de createImgTag() est une
      // marge exprimée directement en pixels, pas en "modules" comme on
      // pourrait le supposer (vérifié dans le code source de la
      // bibliothèque) — la norme QR exige une zone blanche d'au moins 4
      // modules, soit ici 4 × 6 = 24 pixels avec des cellules de 6px.
      // La valeur précédente (4, littéralement 4 pixels) violait cette
      // exigence et pouvait gêner la lecture par certains décodeurs.
      const cellSize = 6;
      const margin = cellSize * 4;
      return qr.createImgTag(cellSize, margin);
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError || new Error("qrcode_generation_failed");
}

// Préfixe identifiant un fragment de recette multi-QR — distinct du
// format compact JSON à usage unique (qui commence par "{") pour que
// le lecteur puisse reconnaître immédiatement qu'il s'agit d'une seule
// partie parmi plusieurs, avant même d'essayer de l'interpréter comme
// une recette complète.
const MULTI_QR_PREFIX = "MRQ1";
// Somme de contrôle simple (pas cryptographique, juste utile pour
// détecter une corruption accidentelle) — permet de vérifier après
// réassemblage que le contenu reconstitué correspond exactement à
// celui d'origine, plutôt que de compter uniquement sur JSON.parse()
// qui ne détecte pas toute altération restant syntaxiquement valide.
function computeChecksum(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i += 1) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) >>> 0;
  }
  return hash.toString(36);
}
// Découpe un texte trop long pour un seul QR en plusieurs fragments à
// peu près égaux, chacun précédé d'un petit en-tête indiquant sa
// position ("2/3" par exemple), un identifiant commun à toutes les
// parties, et une somme de contrôle du contenu complet — nécessaire
// pour que le lecteur puisse regrouper des fragments provenant de
// scans séparés, potentiellement dans le désordre, détecter s'il en
// manque encore, et vérifier l'intégrité une fois tout reconstitué.
// Découpe "content" en fragments dont la taille en OCTETS UTF-8 (pas en
// nombre de caractères) ne dépasse jamais "maxChunkBytes" — un accent
// ou un caractère spécial peut peser 2 à 4 octets en UTF-8 pour un seul
// caractère JavaScript, donc se fier uniquement à .length aurait pu
// produire des fragments plus lourds que prévu une fois encodés dans
// le QR. Ne coupe jamais au milieu d'un caractère : avance caractère
// par caractère (pas octet par octet) pour décider où couper.
function splitIntoQrParts(content, maxChunkBytes) {
  const encoder = new TextEncoder();
  if (encoder.encode(content).length <= maxChunkBytes) return [content];

  const chars = Array.from(content); // respecte les paires de substitution Unicode
  const chunks = [];
  let current = "";
  let currentBytes = 0;
  for (const ch of chars) {
    const chBytes = encoder.encode(ch).length;
    if (currentBytes + chBytes > maxChunkBytes && current) {
      chunks.push(current);
      current = "";
      currentBytes = 0;
    }
    current += ch;
    currentBytes += chBytes;
  }
  if (current) chunks.push(current);

  // uid().slice(0, 6) ne prenait que le début de l'horodatage (jamais
  // la partie aléatoire, qui vient après) — deux recettes générées à
  // quelques millisecondes d'écart recevaient donc exactement le même
  // identifiant de lot, confirmé concrètement en test. crypto.randomUUID()
  // est réellement aléatoire sur toute sa longueur ; repli sur uid()
  // complet (pas juste ses 6 premiers caractères) si indisponible.
  const batchId = (crypto.randomUUID ? crypto.randomUUID().replace(/-/g, "") : uid()).slice(0, 12);
  const totalParts = chunks.length;
  const checksum = computeChecksum(content);
  return chunks.map((chunk, i) => `${MULTI_QR_PREFIX}|${batchId}|${i + 1}|${totalParts}|${checksum}|${chunk}`);
}
// Reconnaît un fragment multi-QR et en extrait les composants, ou
// retourne null si le texte ne correspond pas à ce format (auquel cas
// le lecteur doit essayer les autres formats reconnus).
function tryParseMultiPartQrFragment(text) {
  if (typeof text !== "string" || !text.startsWith(MULTI_QR_PREFIX + "|")) return null;
  const firstSep = text.indexOf("|", MULTI_QR_PREFIX.length + 1);
  const secondSep = text.indexOf("|", firstSep + 1);
  const thirdSep = text.indexOf("|", secondSep + 1);
  const fourthSep = text.indexOf("|", thirdSep + 1);
  if (firstSep < 0 || secondSep < 0 || thirdSep < 0 || fourthSep < 0) return null;
  const batchId = text.slice(MULTI_QR_PREFIX.length + 1, firstSep);
  const partIndex = parseInt(text.slice(firstSep + 1, secondSep), 10);
  const totalParts = parseInt(text.slice(secondSep + 1, thirdSep), 10);
  const checksum = text.slice(thirdSep + 1, fourthSep);
  const chunk = text.slice(fourthSep + 1);
  if (!batchId || !checksum || !Number.isFinite(partIndex) || !Number.isFinite(totalParts) || partIndex < 1 || partIndex > totalParts) return null;
  return { batchId, partIndex, totalParts, checksum, chunk };
}

async function openQrCodeModal(recipe, persons) {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("qrcode_title")}</h2>
    <p id="qrcode-hint" style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("qrcode_hint"))}</p>
    <div id="qrcode-canvas-holder" style="display:flex;justify-content:center;margin-bottom:12px;min-height:240px;align-items:center;text-align:center;"><span style="font-size:13px;color:var(--text-muted);">${escapeHtml(t("qrcode_loading"))}</span></div>
    <div id="qrcode-part-nav" style="display:none;align-items:center;justify-content:space-between;gap:10px;margin-bottom:16px;">
      <button type="button" class="btn btn-outline" id="qrcode-part-prev" style="flex:1;"></button>
      <span id="qrcode-part-indicator" style="font-size:13px;font-weight:600;color:var(--text-muted);white-space:nowrap;"></span>
      <button type="button" class="btn btn-outline" id="qrcode-part-next" style="flex:1;"></button>
    </div>
    <div class="modal-actions">
      <button type="button" class="btn btn-outline" id="qrcode-close">${t("cooking_close")}</button>
      <button type="button" class="btn btn-primary" id="qrcode-save">${t("qrcode_save_button")}</button>
    </div>
  </div>`);
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);

  // Format compact et indépendant de la langue : utilise les noms
  // internes canoniques (français) directement, sans jamais passer par
  // la traduction ni par une analyse de texte — évite à la fois la
  // densité inutile des libellés écrits en toutes lettres et les
  // problèmes de reconnaissance (unités composées, allergènes en
  // anglais...) qui ne peuvent plus se produire puisqu'aucune
  // traduction n'intervient à aucun moment entre la génération et la
  // lecture.
  const compact = { v: 1, n: recipe.name, p: persons };
  if (recipe.difficulty) compact.d = recipe.difficulty;
  if (recipe.prepTime) compact.pt = recipe.prepTime;
  if (recipe.cookTime) compact.ct = recipe.cookTime;
  if (recipe.allergens && recipe.allergens.length) compact.a = recipe.allergens;
  if (recipe.description) compact.de = recipe.description;
  if (recipe.notes) compact.no = recipe.notes;
  compact.i = (recipe.ingredients || []).map((ing) => {
    const scaled = ing.quantity != null ? Math.round(ing.quantity * persons * 100) / 100 : null;
    return [ing.name, scaled, ing.unit];
  });
  const content = JSON.stringify(compact);
  // Au-delà de cette taille, un seul QR devient trop dense pour être
  // scanné de façon fiable — la recette est alors répartie sur
  // plusieurs QR à scanner successivement, plutôt que de raccourcir ou
  // de retirer des informations (la préparation ne doit jamais être
  // incomplète silencieusement).
  const MAX_QR_LENGTH = 800;
  const parts = splitIntoQrParts(content, MAX_QR_LENGTH);
  let currentPart = 0;

  const holder = sheet.querySelector("#qrcode-canvas-holder");
  const navBar = sheet.querySelector("#qrcode-part-nav");
  const indicator = sheet.querySelector("#qrcode-part-indicator");
  const prevBtn = sheet.querySelector("#qrcode-part-prev");
  const nextBtn = sheet.querySelector("#qrcode-part-next");
  prevBtn.textContent = t("qrcode_part_prev");
  nextBtn.textContent = t("qrcode_part_next");

  async function renderCurrentPart() {
    holder.innerHTML = `<span style="font-size:13px;color:var(--text-muted);">${escapeHtml(t("qrcode_loading"))}</span>`;
    try {
      await loadQrCodeLib();
      holder.innerHTML = generateQrCodeImgTag(parts[currentPart]);
    } catch (e) {
      holder.innerHTML = `<div><span style="font-size:13px;color:var(--danger);">${escapeHtml(t("qrcode_load_error"))}</span><div style="font-size:11px;color:var(--text-muted);margin-top:6px;word-break:break-word;">${escapeHtml(formatCaughtError(e))}</div></div>`;
    }
    if (parts.length > 1) {
      navBar.style.display = "flex";
      indicator.textContent = t("qrcode_part_indicator", { current: String(currentPart + 1), total: String(parts.length) });
      prevBtn.disabled = currentPart === 0;
      nextBtn.disabled = currentPart === parts.length - 1;
      sheet.querySelector("#qrcode-hint").textContent = t("qrcode_multi_hint", { total: String(parts.length) });
    }
  }
  prevBtn.addEventListener("click", () => { if (currentPart > 0) { currentPart -= 1; renderCurrentPart(); } });
  nextBtn.addEventListener("click", () => { if (currentPart < parts.length - 1) { currentPart += 1; renderCurrentPart(); } });
  await renderCurrentPart();

  sheet.querySelector("#qrcode-close").addEventListener("click", () => overlay.remove());
  sheet.querySelector("#qrcode-save").addEventListener("click", () => {
    const img = holder.querySelector("img");
    if (!img) return;
    const safeName = (recipe.name || "recette").replace(/[^\w\s-]/g, "").trim() || "recette";
    const suffix = parts.length > 1 ? `-${currentPart + 1}sur${parts.length}` : "";
    // La bibliothèque de génération produit en réalité un GIF (voir
    // "data:image/gif;base64," dans lib/qrcode-generator.js) —
    // l'enregistrer tel quel sous une extension .png produisait un
    // fichier dont le contenu réel ne correspondait pas à son
    // extension, ce que certains appareils Android refusent ensuite de
    // décoder correctement en le resélectionnant comme image. On
    // redessine donc l'image sur un canvas pour produire un vrai
    // fichier PNG, cohérent avec son extension.
    const canvas = document.createElement("canvas");
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    canvas.getContext("2d").drawImage(img, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.download = `${safeName}-qrcode${suffix}.png`;
      link.href = url;
      link.click();
      URL.revokeObjectURL(url);
    }, "image/png");
  });
}

/* ======================================================================
   PARTAGE DE LA LISTE DE COURSES VIA QR CODE
   Format compact (pas du JSON, pour rester léger) : une ligne d'en-tête
   pour identifier le format, puis une ligne par article
   "nom|quantité|unité|coché". Réparti automatiquement sur plusieurs QR
   si nécessaire (voir splitIntoQrParts) — aucun article n'est jamais
   retiré, contrairement à l'ancienne troncature.
   ====================================================================== */
const SHOPPING_QR_PREFIX = "MESRECETTES_SHOPPING:1\n";

function encodeShoppingListForQr(items) {
  const lines = items.map((item) => {
    const name = (item.name || "").replace(/[|\n]/g, " ");
    const qty = item.quantity != null ? item.quantity : "";
    const unit = item.unit || "";
    const checked = item.checked ? "1" : "0";
    return `${name}|${qty}|${unit}|${checked}`;
  });
  return SHOPPING_QR_PREFIX + lines.join("\n");
}
function decodeShoppingListFromQr(text) {
  // Normalise les fins de ligne et les espaces superflus avant de
  // comparer : le caractère exact de retour à la ligne peut varier
  // légèrement selon l'encodage/décodage du QR code, même quand le
  // texte affiché semble identique.
  const normalized = (text || "").replace(/\r\n/g, "\n").trim();
  const prefixCore = SHOPPING_QR_PREFIX.trim(); // "MESRECETTES_SHOPPING:1", sans le saut de ligne
  if (!normalized.startsWith(prefixCore)) return null;
  const body = normalized.slice(prefixCore.length).replace(/^\n/, "");
  return body.split("\n").filter(Boolean).map((line) => {
    const [name, qty, unit, checked] = line.split("|");
    return {
      id: uid(),
      name: name || "",
      quantity: qty !== "" && qty != null ? parseFloat(qty) : null,
      unit: unit || "pièce",
      checked: checked === "1",
    };
  }).filter((i) => i.name);
}

// Reconnaît un QR code de recette, qu'il vienne du bureau ("- Farine :
// 200g") ou du mobile ("- 200 g Farine") — les deux utilisent la même
// structure générale (nom, puis une ligne "Ingrédients", puis la
// liste), seul l'ordre quantité/nom dans chaque ligne diffère.
function parseQrIngredientLine(line) {
  const cleaned = line.replace(/^[-•*]\s*/, "").trim();
  const colonMatch = cleaned.match(/^(.+?)\s*:\s*([\d.,]+)\s*(\S*)$/);
  if (colonMatch) {
    return {
      name: colonMatch[1].trim(),
      quantity: parseFloat(colonMatch[2].replace(",", ".")),
      unit: colonMatch[3] || "pièce",
    };
  }
  return parseIngredientString(cleaned);
}
// Tente de lire le texte comme le format JSON compact généré par la
// version actuelle de l'application ; retourne null (sans erreur) s'il
// ne s'agit manifestement pas de ce format, pour laisser le lecteur
// tenter ensuite l'ancien format texte, utilisé par d'éventuels QR
// générés par une version antérieure.
function tryParseCompactRecipeQr(text) {
  const trimmed = (text || "").trim();
  if (!trimmed.startsWith("{")) return null;
  let data;
  try {
    data = JSON.parse(trimmed);
  } catch (e) {
    return null;
  }
  if (!data || typeof data !== "object" || data.v !== 1 || typeof data.n !== "string" || !Array.isArray(data.i)) {
    return null;
  }
  const ingredients = data.i
    .filter((tuple) => Array.isArray(tuple) && typeof tuple[0] === "string" && tuple[0].trim())
    .map((tuple) => ({ name: resolveImportedIngredientName(tuple[0]), quantity: tuple[1] != null ? Number(tuple[1]) : null, unit: tuple[2] || "pièce" }));
  const persons = Number(data.p) > 0 ? Number(data.p) : 4;
  return {
    name: data.n,
    ingredients: ingredients.map((i) => ({ ...i, quantity: i.quantity != null ? i.quantity / persons : null })),
    prepTime: Number(data.pt) > 0 ? Number(data.pt) : null,
    cookTime: Number(data.ct) > 0 ? Number(data.ct) : null,
    difficulty: typeof data.d === "string" ? data.d : null,
    allergens: Array.isArray(data.a) ? data.a : [],
    description: typeof data.de === "string" ? data.de : "",
    notes: typeof data.no === "string" ? data.no : "",
    persons,
  };
}

function parseRecipeFromQrText(text) {
  // Format compact prioritaire : essaie d'abord de lire le texte comme
  // le JSON généré par la version actuelle de l'application — les noms
  // d'ingrédients et d'allergènes y sont déjà dans leur forme interne
  // canonique, donc aucune traduction ni analyse de texte n'est
  // nécessaire pour les reconnaître correctement.
  const compactParsed = tryParseCompactRecipeQr(text);
  if (compactParsed) return compactParsed;

  const lines = (text || "").split("\n").map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) return null;
  // Volontairement très permissif ("ingr" seul, sans exiger la suite) :
  // si l'encodage du caractère accentué a été corrompu quelque part
  // entre la génération et la lecture du QR code, seul le début du mot
  // ("Ingr", toujours en ASCII simple) est garanti de rester intact.
  const ingredientMarker = /ingr|zutat/i;
  const ingIdx = lines.findIndex((l) => ingredientMarker.test(l));
  if (ingIdx < 1) return null; // pas de section ingrédients reconnue, ou rien avant elle
  const name = lines[0];

  // Les lignes entre le nom et la section ingrédients peuvent contenir
  // le temps de préparation/cuisson, la difficulté, les allergènes, et
  // la description/les notes personnelles (sur plusieurs lignes) — les
  // deux derniers passent par un suivi de "section courante", puisque
  // leur contenu libre peut s'étaler sur plusieurs lignes contrairement
  // aux autres champs, tous tenant sur une seule ligne "clé : valeur".
  let prepTime = null, cookTime = null, allergens = [], difficulty = null;
  const descriptionLines = [], notesLines = [];
  let currentSection = null;
  lines.slice(1, ingIdx).forEach((line) => {
    const prepMatch = line.match(/pr[eé]paration\s*:\s*(\d+)/i) || line.match(/prep(?:aration)?\s*time\s*:\s*(\d+)/i);
    if (prepMatch) { prepTime = parseInt(prepMatch[1], 10); currentSection = null; return; }
    const cookMatch = line.match(/cuisson\s*:\s*(\d+)/i) || line.match(/cook\s*time\s*:\s*(\d+)/i);
    if (cookMatch) { cookTime = parseInt(cookMatch[1], 10); currentSection = null; return; }
    const difficultyMatch = line.match(/difficult[ée]\s*:\s*(.+)/i) || line.match(/difficulty\s*:\s*(.+)/i);
    if (difficultyMatch) {
      const key = normalize(difficultyMatch[1]);
      difficulty = DIFFICULTY_OPTIONS.find((d) => normalize(d) === key || normalize(translateDifficulty(d)) === key) || null;
      currentSection = null;
      return;
    }
    const allergenMatch = line.match(/allerg(?:[eè]ne|en)s?\s*:\s*(.+)/i);
    if (allergenMatch) { allergens = allergenMatch[1].split(",").map((a) => a.trim()).filter(Boolean); currentSection = null; return; }
    if (/^descri?ption\s*:?\s*$/i.test(line)) { currentSection = "description"; return; }
    if (/^(personal\s+)?notes?(\s+personnelles?)?\s*:?\s*$/i.test(line)) { currentSection = "notes"; return; }
    if (currentSection === "description") descriptionLines.push(line);
    else if (currentSection === "notes") notesLines.push(line);
  });
  const description = descriptionLines.join("\n");
  const notes = notesLines.join("\n");

  // Le nombre de personnes est indiqué dans la ligne d'en-tête des
  // ingrédients ("... pour 4 personnes ..."). Important : les quantités
  // du QR code sont déjà calculées pour ce nombre précis, alors que
  // l'application stocke toujours les quantités "pour 1 personne" en
  // interne — sans cette division, les quantités importées seraient
  // multipliées une seconde fois à l'affichage.
  const personsMatch = lines[ingIdx].match(/\d+/);
  const persons = personsMatch ? Math.max(1, parseInt(personsMatch[0], 10)) : 4;

  const ingredients = lines.slice(ingIdx + 1)
    .map(parseQrIngredientLine)
    .filter((i) => i.name)
    .map((i) => ({ ...i, quantity: i.quantity != null ? i.quantity / persons : null }));
  if (!ingredients.length) return null;
  return { name, ingredients, prepTime, cookTime, difficulty, allergens, description, notes, persons };
}

// Retire des articles (depuis la fin) jusqu'à ce que le contenu tienne
// dans la capacité d'un QR code, plutôt que de couper au milieu d'une
// ligne et casser le format.

async function openShoppingQrCodeModal() {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("qrcode_shopping_title")}</h2>
    <p id="qrcode-shopping-hint" style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("qrcode_shopping_hint"))}</p>
    <div id="qrcode-shopping-holder" style="display:flex;justify-content:center;margin-bottom:12px;min-height:240px;align-items:center;text-align:center;"><span style="font-size:13px;color:var(--text-muted);">${escapeHtml(t("qrcode_loading"))}</span></div>
    <div id="qrcode-shopping-part-nav" style="display:none;align-items:center;justify-content:space-between;gap:10px;margin-bottom:16px;">
      <button type="button" class="btn btn-outline" id="qrcode-shopping-part-prev" style="flex:1;"></button>
      <span id="qrcode-shopping-part-indicator" style="font-size:13px;font-weight:600;color:var(--text-muted);white-space:nowrap;"></span>
      <button type="button" class="btn btn-outline" id="qrcode-shopping-part-next" style="flex:1;"></button>
    </div>
    <button type="button" class="btn btn-outline">${t("cooking_close")}</button>
  </div>`);
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
  sheet.querySelector("button:last-of-type").addEventListener("click", () => overlay.remove());

  const holder = sheet.querySelector("#qrcode-shopping-holder");
  const navBar = sheet.querySelector("#qrcode-shopping-part-nav");
  const indicator = sheet.querySelector("#qrcode-shopping-part-indicator");
  const prevBtn = sheet.querySelector("#qrcode-shopping-part-prev");
  const nextBtn = sheet.querySelector("#qrcode-shopping-part-next");
  prevBtn.textContent = t("qrcode_part_prev");
  nextBtn.textContent = t("qrcode_part_next");

  // Découpe en plusieurs QR si nécessaire (même système que les
  // recettes) plutôt que de retirer des articles pour faire tenir la
  // liste dans un seul QR — aucun article n'est plus jamais perdu, même
  // silencieusement avec un avertissement.
  const content = encodeShoppingListForQr(state.shopping);
  const MAX_QR_LENGTH = 800;
  const parts = splitIntoQrParts(content, MAX_QR_LENGTH);
  let currentPart = 0;

  async function renderCurrentPart() {
    holder.innerHTML = `<span style="font-size:13px;color:var(--text-muted);">${escapeHtml(t("qrcode_loading"))}</span>`;
    try {
      await loadQrCodeLib();
      holder.innerHTML = generateQrCodeImgTag(parts[currentPart]);
    } catch (e) {
      holder.innerHTML = `<div><span style="font-size:13px;color:var(--danger);">${escapeHtml(t("qrcode_load_error"))}</span><div style="font-size:11px;color:var(--text-muted);margin-top:6px;word-break:break-word;">${escapeHtml(formatCaughtError(e))}</div></div>`;
    }
    if (parts.length > 1) {
      navBar.style.display = "flex";
      indicator.textContent = t("qrcode_part_indicator", { current: String(currentPart + 1), total: String(parts.length) });
      prevBtn.disabled = currentPart === 0;
      nextBtn.disabled = currentPart === parts.length - 1;
      sheet.querySelector("#qrcode-shopping-hint").textContent = t("qrcode_multi_hint", { total: String(parts.length) });
    }
  }
  prevBtn.addEventListener("click", () => { if (currentPart > 0) { currentPart -= 1; renderCurrentPart(); } });
  nextBtn.addEventListener("click", () => { if (currentPart < parts.length - 1) { currentPart += 1; renderCurrentPart(); } });
  await renderCurrentPart();
}

// Charge le lecteur de QR code (jsQR) à la demande, uniquement quand le
// scan est réellement utilisé. Fichier local (lib/jsQR.js) : plus
// besoin d'une connexion au CDN, ni au premier chargement ni ensuite.
let jsQrLibPromise = null;
function loadJsQrLib() {
  if (window.jsQR) return Promise.resolve();
  if (jsQrLibPromise) return jsQrLibPromise;
  jsQrLibPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "./lib/jsQR.js";
    script.onload = () => resolve();
    script.onerror = () => { jsQrLibPromise = null; reject(new Error("jsqr_lib_load_failed")); };
    document.head.appendChild(script);
  });
  return jsQrLibPromise;
}

async function confirmImportScannedShoppingList(items) {
  if (!await customConfirm(t("qrscan_import_confirm", { count: String(items.length) }))) return;
  for (const item of items) {
    await storePut("shopping", item);
    state.shopping.push(item);
  }
  await customAlert(t("qrscan_import_success"));
  render();
}

// Ouvre la caméra et scanne en continu jusqu'à trouver un QR code de
// liste de courses reconnu. Nécessite un contexte sécurisé (HTTPS) —
// indisponible tant que l'application tourne en Wi-Fi local.
async function openQrScanModal() {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("qrscan_title")}</h2>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("qrscan_hint"))}</p>
    <div id="qrscan-holder" style="position:relative;width:100%;aspect-ratio:1;background:#000;border-radius:12px;overflow:hidden;margin-bottom:12px;display:flex;align-items:center;justify-content:center;">
      <span id="qrscan-camera-status" style="color:#fff;font-size:13px;text-align:center;padding:20px;"></span>
    </div>
    <div id="qrscan-status" style="font-size:12px;color:var(--text-muted);margin-bottom:12px;min-height:16px;"></div>
    <button type="button" class="btn btn-secondary" id="qrscan-manual" style="margin-bottom:10px;" disabled>${t("qrscan_manual_button")}</button>
    <button type="button" class="btn btn-outline" id="qrscan-choose-image" style="margin-bottom:10px;">${t("qrscan_choose_image_button")}</button>
    <input type="file" accept="image/*" id="qrscan-file-input" style="display:none;">
    <button type="button" id="qrscan-paste-fallback" style="background:none;border:none;color:var(--text-muted);font-size:12px;text-decoration:underline;cursor:pointer;display:block;margin:0 auto 10px;padding:4px;">${escapeHtml(t("qrscan_paste_fallback_link"))}</button>
    <button type="button" class="btn btn-outline" id="qrscan-close">${t("cooking_close")}</button>
  </div>`);
  overlay.appendChild(sheet);
  document.body.appendChild(overlay);
  // "cleanup" est déclarée plus bas (via une fonction nommée, donc
  // accessible dès maintenant grâce au hoisting), mais on l'appelle
  // depuis une fonction anonyme pour rester explicite plutôt que de
  // compter silencieusement sur ce détail.
  initModalA11y(overlay, sheet, { beforeClose: () => cleanup() });

  const holder = sheet.querySelector("#qrscan-holder");
  const cameraStatusEl = sheet.querySelector("#qrscan-camera-status");
  const statusEl = sheet.querySelector("#qrscan-status");
  const manualBtn = sheet.querySelector("#qrscan-manual");
  sheet.querySelector("#qrscan-paste-fallback").addEventListener("click", () => {
    cleanup();
    overlay.remove();
    openQrPasteModal();
  });
  let stream = null;
  let stopped = false;
  // Accumule les parties d'une recette répartie sur plusieurs QR — ne
  // suit qu'un seul lot à la fois : si un fragment d'un lot différent
  // est scanné en cours de route, on recommence avec ce nouveau lot
  // plutôt que de mélanger deux recettes différentes.
  let multiPartAccumulator = null;

  function cleanup() {
    // Idempotente : peut être appelée plusieurs fois sans effet
    // supplémentaire (le bouton Fermer l'appelle directement, et le
    // mécanisme générique de fermeture des fenêtres peut aussi la
    // déclencher via beforeClose — arrêter une piste déjà arrêtée est
    // sans risque, mais autant l'éviter proprement).
    if (stopped) return;
    stopped = true;
    if (stream) stream.getTracks().forEach((tr) => tr.stop());
  }
  sheet.querySelector("#qrscan-close").addEventListener("click", () => { cleanup(); overlay.remove(); });
  overlay.addEventListener("click", (e) => { if (e.target === overlay) { cleanup(); overlay.remove(); } });

  // Le détecteur natif du système (disponible sur Chrome Android depuis
  // 2020) utilise le même moteur de reconnaissance que les applications
  // de scan classiques — nettement plus fiable en pratique qu'une
  // bibliothèque JavaScript pure.
  let nativeBarcodeDetector = null;
  if ("BarcodeDetector" in window) {
    try {
      nativeBarcodeDetector = new BarcodeDetector({ formats: ["qr_code"] });
    } catch (e) {
      nativeBarcodeDetector = null;
    }
  }

  // Ce qui suit (canvas, décodage, bouton "choisir une image") est mis
  // en place avant même de vérifier si la caméra est disponible : cette
  // voie alternative doit continuer à fonctionner même si la caméra
  // échoue entièrement (contexte non sécurisé, permission refusée,
  // appareil sans caméra...), puisqu'elle ne dépend pas d'elle.
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  // Décode le contenu actuellement dessiné dans "canvas" (taille
  // size×size) — natif en priorité avec repli automatique sur jsQR,
  // factorisé ici pour être utilisé aussi bien sur une image de la
  // caméra que sur une image importée depuis un fichier.
  async function decodeCanvasContent(size) {
    let decodedText = null;
    let nativeError = null;
    if (nativeBarcodeDetector) {
      try {
        const barcodes = await nativeBarcodeDetector.detect(canvas);
        if (barcodes && barcodes.length) decodedText = barcodes[0].rawValue;
      } catch (e) {
        nativeError = e;
        if (e && (e.name === "NotSupportedError" || e.name === "NotAllowedError")) {
          nativeBarcodeDetector = null;
          if (!window.jsQR) {
            statusEl.textContent = t("qrscan_native_fallback");
            try { await loadJsQrLib(); } catch (loadErr) { /* si jsQR ne charge pas non plus, le repli habituel s'appliquera juste en dessous */ }
          }
        }
      }
    }
    if (decodedText == null && window.jsQR) {
      const imageData = ctx.getImageData(0, 0, size, size);
      const code = window.jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: "attemptBoth" });
      if (code && code.data) decodedText = code.data;
    }
    return { decodedText, nativeError };
  }

  // Traite un texte décodé (peu importe sa source, caméra ou fichier
  // importé) de façon identique : reconnaissance recette/liste de
  // courses, ou affichage du texte brut si non reconnu.
  function handleDecodedText(decodedText, nativeError, size) {
    if (decodedText == null) {
      return {
        status: "no_code",
        width: size,
        height: size,
        nativeError: nativeError ? ((nativeError.name || "Error") + " — " + (nativeError.message || String(nativeError))) : null,
      };
    }
    // Un fragment de recette répartie sur plusieurs QR est traité en
    // priorité, avant même d'essayer les autres formats reconnus —
    // aucune chance qu'il corresponde à une liste de courses ou une
    // recette complète de toute façon, mais être explicite évite toute
    // ambiguïté.
    const fragment = tryParseMultiPartQrFragment(decodedText);
    if (fragment) {
      if (!multiPartAccumulator || multiPartAccumulator.batchId !== fragment.batchId) {
        // Nouveau lot : soit le tout premier fragment scanné, soit un
        // changement de recette en cours de route — dans les deux cas,
        // on repart d'un accumulateur neuf plutôt que de mélanger deux
        // recettes différentes.
        const isSwitch = !!multiPartAccumulator;
        multiPartAccumulator = { batchId: fragment.batchId, totalParts: fragment.totalParts, checksum: fragment.checksum, parts: {} };
        if (isSwitch) {
          statusEl.textContent = t("qrscan_multi_new_batch");
        }
      }
      if (fragment.totalParts !== multiPartAccumulator.totalParts || fragment.checksum !== multiPartAccumulator.checksum) {
        // Même identifiant de lot, mais nombre de parties ou somme de
        // contrôle incohérente : un fragment corrompu ou mal transmis.
        // On l'ignore plutôt que de risquer une reconstitution erronée.
        statusEl.textContent = t("qrscan_multi_inconsistent");
        return { status: "partial" };
      }
      if (multiPartAccumulator.parts[fragment.partIndex]) {
        statusEl.textContent = t("qrscan_multi_already_have");
        return { status: "partial" };
      }
      multiPartAccumulator.parts[fragment.partIndex] = fragment.chunk;
      const receivedCount = Object.keys(multiPartAccumulator.parts).length;
      if (receivedCount < multiPartAccumulator.totalParts) {
        statusEl.textContent = t("qrscan_multi_progress", { current: String(receivedCount), total: String(multiPartAccumulator.totalParts) });
        return { status: "partial" };
      }
      // Toutes les parties sont là : reconstitue le contenu complet
      // dans l'ordre, vérifie la somme de contrôle (JSON.parse() seul
      // ne détecte pas toute altération restant syntaxiquement
      // valide), puis le traite exactement comme un QR de recette
      // classique en un seul morceau.
      let reassembled = "";
      for (let i = 1; i <= multiPartAccumulator.totalParts; i += 1) reassembled += multiPartAccumulator.parts[i];
      const expectedChecksum = multiPartAccumulator.checksum;
      multiPartAccumulator = null;
      if (computeChecksum(reassembled) !== expectedChecksum) {
        statusEl.textContent = t("qrscan_multi_checksum_failed");
        return { status: "not_recognized" };
      }
      const parsedRecipe = tryParseCompactRecipeQr(reassembled);
      if (parsedRecipe) {
        cleanup();
        overlay.remove();
        confirmImportScannedRecipe(parsedRecipe);
        return { status: "success" };
      }
      const parsedShoppingItems = decodeShoppingListFromQr(reassembled);
      if (parsedShoppingItems && parsedShoppingItems.length) {
        cleanup();
        overlay.remove();
        confirmImportScannedShoppingList(parsedShoppingItems);
        return { status: "success" };
      }
      statusEl.textContent = t("qrscan_not_recognized");
      return { status: "not_recognized" };
    }
    const items = decodeShoppingListFromQr(decodedText);
    if (items && items.length) {
      cleanup();
      overlay.remove();
      confirmImportScannedShoppingList(items);
      return { status: "success" };
    }
    const parsedRecipe = parseRecipeFromQrText(decodedText);
    if (parsedRecipe) {
      cleanup();
      overlay.remove();
      confirmImportScannedRecipe(parsedRecipe);
      return { status: "success" };
    }
    const preview = decodedText.length > 200 ? decodedText.slice(0, 200) + "…" : decodedText;
    statusEl.innerHTML = "";
    statusEl.appendChild(el(`<div>${escapeHtml(t("qrscan_not_recognized"))}</div>`));
    statusEl.appendChild(el(`<div style="font-size:11px;margin-top:6px;word-break:break-word;white-space:pre-wrap;user-select:text;">${escapeHtml(preview)}</div>`));
    return { status: "not_recognized" };
  }

  // Décode une image choisie depuis les fichiers de l'appareil (une
  // capture d'écran, ou le PNG enregistré via "Enregistrer en image")
  // — un chemin totalement indépendant de la caméra, qui sert à la
  // fois de vraie fonctionnalité (recevoir un QR reçu par message) et
  // de test de diagnostic pour savoir si un souci vient de la caméra
  // ou du décodage lui-même.
  // Détecte le vrai format d'une image à partir de sa signature d'octets
  // plutôt que de se fier à l'extension du fichier ou à son type MIME
  // déclaré (potentiellement incorrect, notamment pour d'anciens QR
  // enregistrés sous l'extension .png mais contenant en réalité un GIF).
  function detectImageMimeType(bytes) {
    const sig = Array.from(bytes.slice(0, 8));
    if (sig[0] === 0x89 && sig[1] === 0x50 && sig[2] === 0x4e && sig[3] === 0x47) return "image/png";
    if (sig[0] === 0x47 && sig[1] === 0x49 && sig[2] === 0x46) return "image/gif";
    if (sig[0] === 0xff && sig[1] === 0xd8 && sig[2] === 0xff) return "image/jpeg";
    if (sig[0] === 0x52 && sig[1] === 0x49 && sig[2] === 0x46 && sig[3] === 0x46) return "image/webp";
    return null;
  }
  async function decodeQrImageFile(file) {
    const img = new Image();
    try {
      // Construit une URL data: directement à partir des octets réels du
      // fichier, avec le type MIME détecté par signature — plus fiable
      // dans la pratique qu'un Blob avec URL.createObjectURL (qui s'est
      // révélé échouer sur certains appareils même pour un fichier
      // parfaitement valide dont le type MIME était pourtant correct),
      // et corrige au passage le cas des anciens QR enregistrés sous
      // l'extension .png alors qu'ils contenaient en réalité un GIF.
      const bytes = new Uint8Array(await file.arrayBuffer());
      const mimeType = detectImageMimeType(bytes) || file.type || "image/png";
      let binary = "";
      const chunkSize = 8192;
      for (let i = 0; i < bytes.length; i += chunkSize) {
        binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
      }
      const dataUrl = `data:${mimeType};base64,${btoa(binary)}`;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = () => reject(new Error(t("qrscan_image_load_error")));
        img.src = dataUrl;
      });
      const size = Math.max(img.naturalWidth, img.naturalHeight);
      canvas.width = size;
      canvas.height = size;
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, size, size);
      ctx.drawImage(img, (size - img.naturalWidth) / 2, (size - img.naturalHeight) / 2);
      const { decodedText, nativeError } = await decodeCanvasContent(size);
      return handleDecodedText(decodedText, nativeError, size);
    } catch (e) {
      if (e instanceof Error) throw e;
      throw new Error(t("qrscan_image_load_error"));
    }
  }

  const fileInput = sheet.querySelector("#qrscan-file-input");
  sheet.querySelector("#qrscan-choose-image").addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const result = await decodeQrImageFile(file);
      if (result.status === "no_code") {
        statusEl.textContent = `${t("qrscan_no_code_found")} (${result.width}×${result.height}px)` + (result.nativeError ? ` [${result.nativeError}]` : "");
      }
    } catch (err) {
      statusEl.textContent = formatCaughtError(err);
    }
    e.target.value = "";
  });

  if (!window.isSecureContext) {
    cameraStatusEl.textContent = t("qrscan_camera_https_hint");
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraStatusEl.textContent = t("qrscan_camera_denied");
    return;
  }

  cameraStatusEl.textContent = t("qrcode_loading");
  if (nativeBarcodeDetector) {
    // Charge quand même jsQR en tâche de fond, comme vrai filet de
    // secours si le détecteur natif échoue silencieusement pour une
    // raison quelconque — sans bloquer le démarrage de la caméra dessus.
    loadJsQrLib().catch(() => {});
  } else {
    try {
      await loadJsQrLib();
    } catch (e) {
      cameraStatusEl.textContent = t("qrscan_lib_load_error");
      return;
    }
  }
  if (stopped) return;

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: "environment",
        // Sans ces contraintes, certains navigateurs démarrent la
        // caméra en basse résolution par défaut — largement suffisant
        // pour un appel vidéo, mais souvent trop flou/petit pour qu'un
        // QR code y soit détecté correctement.
        width: { ideal: 1920 },
        height: { ideal: 1080 },
      },
    });
  } catch (e) {
    cameraStatusEl.textContent = t("qrscan_camera_denied");
    return;
  }
  if (stopped) { stream.getTracks().forEach((tr) => tr.stop()); return; }

  const video = document.createElement("video");
  video.setAttribute("playsinline", "true");
  video.muted = true;
  video.srcObject = stream;
  video.style.cssText = "width:100%;height:100%;object-fit:cover;";
  holder.innerHTML = "";
  holder.appendChild(video);
  await video.play();
  manualBtn.disabled = false;
  // Indicateur de diagnostic : utile pour savoir, en cas de nouveau
  // souci, si la détection native a bien été utilisée ou si l'appareil
  // est retombé sur jsQR.
  statusEl.textContent = nativeBarcodeDetector ? t("qrscan_using_native") : t("qrscan_using_jsqr");

  // Analyse une image de la caméra ; retourne true si un QR code
  // reconnu (liste ou recette) a été trouvé et traité.
  async function processFrame() {
    // Ne garde que le carré central de l'image — c'est la seule partie
    // réellement visible à l'écran (le CSS recadre l'aperçu en carré
    // avec "object-fit: cover"). Sans ce recadrage, l'image analysée
    // était bien plus grande que ce que l'utilisateur vise et vers quoi
    // il cadre le QR code, qui y occupait une part trop petite pour
    // être détecté de façon fiable.
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const size = Math.min(vw, vh);
    const sx = (vw - size) / 2;
    const sy = (vh - size) / 2;
    canvas.width = size;
    canvas.height = size;
    ctx.drawImage(video, sx, sy, size, size, 0, 0, size, size);

    const { decodedText, nativeError } = await decodeCanvasContent(size);
    return handleDecodedText(decodedText, nativeError, size);
  }

  async function tick() {
    if (stopped) return;
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      try {
        await processFrame();
      } catch (e) {
        // Une erreur de décodage ponctuelle sur une image ne doit pas
        // arrêter la détection en continu — mais si le lecteur est
        // réellement cassé, le bouton manuel ci-dessous permettra de
        // voir le détail exact de l'erreur plutôt qu'un blocage muet.
      }
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  manualBtn.addEventListener("click", async () => {
    try {
      const result = await processFrame();
      if (result.status === "no_code") {
        statusEl.textContent = `${t("qrscan_no_code_found")} (${result.width}×${result.height}px, ${video.videoWidth}×${video.videoHeight})` + (result.nativeError ? ` [${result.nativeError}]` : "");
      }
    } catch (e) {
      statusEl.textContent = formatCaughtError(e);
    }
  });
}

// Solution de repli face aux limites de la lecture QR par caméra sur
// certains appareils : scanner avec n'importe quelle autre application
// (celle de l'appareil photo, un lecteur de QR classique...), copier le
// texte obtenu, puis le coller ici — la même reconnaissance (recette ou
// liste de courses) s'applique ensuite.
function openQrPasteModal() {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("qrpaste_title")}</h2>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("qrpaste_hint"))}</p>
    <div class="field">
      <label for="qrpaste-input">${t("qrpaste_label")}</label>
      <textarea id="qrpaste-input" rows="6"></textarea>
    </div>
    <div id="qrpaste-status" style="font-size:12px;color:var(--text-muted);margin-bottom:12px;min-height:16px;word-break:break-word;white-space:pre-wrap;"></div>
    <div class="modal-actions">
      <button type="button" class="btn btn-outline" id="qrpaste-close">${t("form_cancel")}</button>
      <button type="button" class="btn btn-primary" id="qrpaste-submit">${t("qrpaste_submit_button")}</button>
    </div>
  </div>`);
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
  sheet.querySelector("#qrpaste-close").addEventListener("click", () => overlay.remove());

  const statusEl = sheet.querySelector("#qrpaste-status");
  sheet.querySelector("#qrpaste-submit").addEventListener("click", () => {
    const text = sheet.querySelector("#qrpaste-input").value;
    if (!text.trim()) { statusEl.textContent = t("qrpaste_empty"); return; }
    const items = decodeShoppingListFromQr(text);
    if (items && items.length) {
      overlay.remove();
      confirmImportScannedShoppingList(items);
      return;
    }
    const parsedRecipe = parseRecipeFromQrText(text);
    if (parsedRecipe) {
      overlay.remove();
      confirmImportScannedRecipe(parsedRecipe);
      return;
    }
    statusEl.textContent = t("qrscan_not_recognized");
  });
}

async function confirmImportScannedRecipe(parsed) {
  if (!await customConfirm(t("qrscan_recipe_import_confirm", { name: parsed.name }))) return;
  state.editingRecipeId = null;
  state.formIngredients = parsed.ingredients.map((i) => ({
    name: resolveImportedIngredientName(i.name),
    quantity: i.quantity,
    unit: i.unit,
  }));
  // Fait correspondre les allergènes lus (potentiellement traduits) à
  // la liste interne (toujours en français) — ignore silencieusement
  // ceux qui ne correspondent à rien de connu plutôt que d'échouer.
  state.formAllergens = (parsed.allergens || [])
    .map((name) => {
      const key = normalize(name);
      return ALLERGEN_OPTIONS.find((a) => normalize(a) === key || normalize(translateAllergen(a)) === key);
    })
    .filter(Boolean);
  state.formPhoto = null;
  state.screen = "form";
  state._importPrefill = {
    name: parsed.name,
    description: parsed.description || "",
    persons: parsed.persons || 4,
    prepTime: parsed.prepTime,
    cookTime: parsed.cookTime,
    difficulty: parsed.difficulty,
    notes: parsed.notes || "",
  };
  render();
}

function openSubstitutesModal(recipe) {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("substitutes_title")}</h2>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("substitutes_disclaimer"))}</p>
  </div>`);

  let anyFound = false;
  (recipe.ingredients || []).forEach((ing) => {
    const subs = getDisplaySubstitutes(ing.name);
    if (!subs.length) return;
    anyFound = true;
    sheet.appendChild(el(`<div class="section-label">${escapeHtml(translateIngredientName(ing.name))}</div>`));
    const card = el(`<div class="card" style="padding:2px 16px;margin-bottom:16px;"></div>`);
    subs.forEach((sub) => {
      card.appendChild(el(`<div class="ingredient-item" style="display:block;">
        <div style="font-weight:600;">${escapeHtml(sub.nom)}</div>
        ${sub.note ? `<div style="font-size:13px;color:var(--text-muted);margin-top:2px;">${escapeHtml(sub.note)}</div>` : ""}
      </div>`));
    });
    sheet.appendChild(card);
  });
  if (!anyFound) {
    sheet.appendChild(el(`<div class="empty-state" style="padding:24px 0;"><p>${escapeHtml(t("substitutes_none"))}</p></div>`));
  }

  const closeBtn = el(`<button type="button" class="btn btn-outline">${t("cooking_close")}</button>`);
  closeBtn.addEventListener("click", () => overlay.remove());
  sheet.appendChild(closeBtn);

  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
}

/* ======================================================================
   JOURNAL DE CUISINE
   Chaque entrée est stockée directement dans la recette (recipe.cookLog),
   avec une note et une photo optionnelles, ainsi qu'un compteur du
   nombre de fois cuisinée (recipe.timesCooked).
   ====================================================================== */
function openCookLogAddModal(recipe, existingEntry, onDone) {
  const isEdit = !!existingEntry;
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${escapeHtml(recipe.name)}</h2>
    <div class="field">
      <label for="cooklog-note">${t("cooklog_add_note_label")}</label>
      <textarea id="cooklog-note">${escapeHtml(isEdit ? existingEntry.note || "" : "")}</textarea>
    </div>
    <div class="photo-upload" style="margin-bottom:20px;">
      <div id="cooklog-photo-preview">${isEdit && existingEntry.photo ? `<img src="${existingEntry.photo}" alt="" style="width:100%;border-radius:10px;display:block;">` : escapeHtml(t("cooklog_add_photo_label"))}</div>
      <input type="file" accept="image/*" capture="environment" id="cooklog-photo-input">
    </div>
    <div class="modal-actions">
      ${isEdit ? `<button type="button" class="btn btn-outline" id="cooklog-remove-photo">${t("cooklog_remove_photo_button")}</button>` : `<button type="button" class="btn btn-outline" id="cooklog-skip">${t("cooklog_skip_button")}</button>`}
      <button type="button" class="btn btn-primary" id="cooklog-save">${t("cooklog_save_button")}</button>
    </div>
  </div>`);

  const photoPreview = sheet.querySelector("#cooklog-photo-preview");
  let photoData = isEdit ? (existingEntry.photo || null) : null;
  sheet.querySelector("#cooklog-photo-input").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const maxW = 800;
        const scale = Math.min(1, maxW / img.width);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        photoData = canvas.toDataURL("image/jpeg", 0.8);
        // Retour visuel immédiat : sans ça, rien n'indique que la photo a
        // bien été prise avant l'enregistrement de l'entrée.
        photoPreview.innerHTML = `<img src="${photoData}" alt="" style="width:100%;border-radius:10px;display:block;">`;
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
  if (isEdit) {
    sheet.querySelector("#cooklog-remove-photo").addEventListener("click", () => {
      photoData = null;
      photoPreview.textContent = t("cooklog_add_photo_label");
    });
  }

  async function saveEntry(withDetails) {
    if (isEdit) {
      existingEntry.note = sheet.querySelector("#cooklog-note").value.trim();
      existingEntry.photo = photoData;
    } else {
      const entry = {
        date: new Date().toISOString(),
        note: withDetails ? sheet.querySelector("#cooklog-note").value.trim() : "",
        photo: withDetails ? photoData : null,
      };
      recipe.cookLog = recipe.cookLog || [];
      recipe.cookLog.unshift(entry);
      recipe.timesCooked = (recipe.timesCooked || 0) + 1;
    }
    await storePut("recipes", recipe);
    const idx = state.recipes.findIndex((x) => x.id === recipe.id);
    if (idx >= 0) state.recipes[idx] = recipe;
    overlay.remove();
    if (onDone) onDone(); else render();
  }
  if (!isEdit) sheet.querySelector("#cooklog-skip").addEventListener("click", () => saveEntry(false));
  sheet.querySelector("#cooklog-save").addEventListener("click", () => saveEntry(true));

  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
}

function openCookLogViewModal(recipe) {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("cooklog_title")}</h2>
  </div>`);
  const entriesHolder = el(`<div id="cooklog-entries-holder"></div>`);
  sheet.appendChild(entriesHolder);

  function fillEntries() {
    entriesHolder.innerHTML = "";
    const entries = recipe.cookLog || [];
    if (!entries.length) {
      entriesHolder.appendChild(el(`<div class="empty-state" style="padding:20px 0;"><p>${escapeHtml(t("cooklog_no_entries"))}</p></div>`));
      return;
    }
    entries.forEach((entry) => {
      const dateStr = localeDateStr(entry.date);
      const card = el(`<div class="card" style="padding:12px 16px;margin-bottom:12px;"></div>`);
      const headerRow = el(`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-weight:600;font-size:13px;color:var(--text-muted);">${escapeHtml(dateStr)}</span>
        <span style="display:flex;gap:10px;">
          <button class="edit" aria-label="${t("recipe_edit")}" style="border:none;background:none;color:var(--primary);font-size:15px;">✏️</button>
          <button class="del" aria-label="${t("common_delete")}" style="border:none;background:none;color:var(--danger);font-size:15px;">🗑</button>
        </span>
      </div>`);
      headerRow.querySelector(".edit").addEventListener("click", () => {
        openCookLogAddModal(recipe, entry, fillEntries);
      });
      headerRow.querySelector(".del").addEventListener("click", async () => {
        if (!await customConfirm(t("cooklog_delete_confirm"))) return;
        recipe.cookLog = (recipe.cookLog || []).filter((x) => x !== entry);
        recipe.timesCooked = Math.max(0, (recipe.timesCooked || 1) - 1);
        await storePut("recipes", recipe);
        const idx = state.recipes.findIndex((x) => x.id === recipe.id);
        if (idx >= 0) state.recipes[idx] = recipe;
        fillEntries();
      });
      card.appendChild(headerRow);
      if (entry.photo) card.appendChild(el(`<img src="${entry.photo}" style="width:100%;border-radius:10px;margin-bottom:8px;" alt="">`));
      if (entry.note) card.appendChild(el(`<p class="prose" style="margin:0;">${escapeHtml(entry.note)}</p>`));
      entriesHolder.appendChild(card);
    });
  }
  fillEntries();

  const closeBtn = el(`<button type="button" class="btn btn-outline">${t("cooking_close")}</button>`);
  closeBtn.addEventListener("click", () => { overlay.remove(); render(); });
  sheet.appendChild(closeBtn);
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
}

/* ======================================================================
   MODE CUISINE (avec minuteur)
   ====================================================================== */
function playBeep() {
  try {
    if (!window._audioCtx) window._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const ctx = window._audioCtx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sine";
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.4);
  } catch (e) {
    // Audio indisponible (rare, certains navigateurs en arrière-plan) :
    // le clignotement visuel reste là pour prévenir quand même.
  }
}
function vibrateDevice() {
  // Non disponible sur tous les navigateurs (notamment iOS Safari) : on
  // vérifie avant d'appeler, sans jamais faire planter le minuteur si ce
  // n'est pas pris en charge.
  if ("vibrate" in navigator) {
    try { navigator.vibrate([200, 100, 200]); } catch (e) { /* ignore */ }
  }
}
function formatCountdown(totalSeconds) {
  const clamped = Math.max(0, totalSeconds);
  const m = String(Math.floor(clamped / 60)).padStart(2, "0");
  const s = String(clamped % 60).padStart(2, "0");
  return `${m}:${s}`;
}
function createCookingTimer(holder) {
  const timer = {
    id: uid(), minutes: 5, seconds: 0, remaining: 5 * 60, endAt: null,
    running: false, interval: null, alarming: false, alarmInterval: null,
  };
  state.cookingTimers.push(timer);
  renderTimerRow(holder, timer);
}
function stopCookingTimer(timer) {
  if (timer.interval) { clearInterval(timer.interval); timer.interval = null; }
  if (timer.alarmInterval) { clearInterval(timer.alarmInterval); timer.alarmInterval = null; }
  timer.running = false;
  timer.alarming = false;
}
function renderTimerRow(holder, timer) {
  const row = el(`<div class="timer-row card" data-id="${timer.id}">
    <div class="timer-set-inputs">
      <input type="number" min="0" max="99" inputmode="numeric" class="tmin" value="${timer.minutes}" aria-label="${t("cooking_min_label")}">
      <span>${t("cooking_min_label")}</span>
      <input type="number" min="0" max="59" inputmode="numeric" class="tsec" value="${String(timer.seconds).padStart(2, "0")}" aria-label="${t("cooking_sec_label")}">
      <span>${t("cooking_sec_label")}</span>
    </div>
    <div class="timer-countdown">${formatCountdown(timer.remaining)}</div>
    <div class="timer-row-controls">
      <button class="start-btn" aria-label="${t("cooking_timer_start")}">▶️</button>
      <button class="reset-btn" aria-label="${t("cooking_timer_reset")}">🔄</button>
      <button class="stop-btn" aria-label="${t("cooking_remove_timer")}">🗑</button>
    </div>
  </div>`);

  const minInput = row.querySelector(".tmin");
  const secInput = row.querySelector(".tsec");
  const countdownEl = row.querySelector(".timer-countdown");
  const startBtn = row.querySelector(".start-btn");

  function refreshRemainingFromInputs() {
    if (timer.running || timer.alarming) return;
    timer.remaining = timer.minutes * 60 + timer.seconds;
    countdownEl.textContent = formatCountdown(timer.remaining);
  }
  minInput.addEventListener("input", () => {
    timer.minutes = Math.max(0, Math.min(99, Number(minInput.value) || 0));
    refreshRemainingFromInputs();
  });
  secInput.addEventListener("input", () => {
    timer.seconds = Math.max(0, Math.min(59, Number(secInput.value) || 0));
    refreshRemainingFromInputs();
  });

  function setInputsDisabled(disabled) {
    minInput.disabled = disabled;
    secInput.disabled = disabled;
  }
  function dismissAlarm() {
    stopCookingTimer(timer);
    row.classList.remove("alarming");
    startBtn.textContent = "▶️";
    startBtn.setAttribute("aria-label", t("cooking_timer_start"));
    timer.remaining = timer.minutes * 60 + timer.seconds;
    countdownEl.textContent = formatCountdown(timer.remaining);
    setInputsDisabled(false);
  }
  function tick() {
    // Recalculé à partir de l'échéance réelle (endAt), pas par simple
    // décrémentation — si Android retarde ou saute un tick (l'app
    // passe brièvement en arrière-plan, le moteur JS est occupé...),
    // "remaining--" accumulerait ce retard silencieusement, faisant
    // sonner l'alarme plus tard que prévu même à l'écran visible.
    timer.remaining = Math.max(0, Math.round((timer.endAt - Date.now()) / 1000));
    if (timer.remaining <= 0) {
      clearInterval(timer.interval);
      timer.interval = null;
      timer.running = false;
      timer.alarming = true;
      countdownEl.textContent = t("cooking_timer_done");
      row.classList.add("alarming");
      startBtn.setAttribute("aria-label", t("cooking_stop_alarm"));
      playBeep();
      vibrateDevice();
      showTimerNotification();
      timer.alarmInterval = setInterval(() => { playBeep(); vibrateDevice(); }, 1200);
    } else {
      countdownEl.textContent = formatCountdown(timer.remaining);
    }
  }
  startBtn.addEventListener("click", () => {
    if (timer.alarming) { dismissAlarm(); return; }
    if (timer.running) {
      clearInterval(timer.interval);
      timer.interval = null;
      timer.running = false;
      startBtn.textContent = "▶️";
      startBtn.setAttribute("aria-label", t("cooking_timer_start"));
      setInputsDisabled(false);
    } else {
      if (timer.remaining <= 0) timer.remaining = timer.minutes * 60 + timer.seconds;
      if (timer.remaining <= 0) return;
      timer.endAt = Date.now() + timer.remaining * 1000;
      timer.running = true;
      startBtn.textContent = "⏸";
      startBtn.setAttribute("aria-label", t("cooking_timer_pause"));
      setInputsDisabled(true);
      timer.interval = setInterval(tick, 1000);
      ensureNotificationPermission();
    }
  });
  row.querySelector(".reset-btn").addEventListener("click", () => {
    dismissAlarm();
  });
  row.querySelector(".stop-btn").addEventListener("click", () => {
    stopCookingTimer(timer);
    state.cookingTimers = state.cookingTimers.filter((x) => x.id !== timer.id);
    row.remove();
  });
  holder.appendChild(row);
}

function speakText(text) {
  if (!("speechSynthesis" in window)) return false;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const langMap = { fr: "fr-FR", en: "en-US", es: "es-ES", de: "de-DE" };
  utterance.lang = langMap[CURRENT_LANG] || "fr-FR";
  window.speechSynthesis.speak(utterance);
  return true;
}
function stopSpeaking() {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
}

// Empêche l'écran de s'éteindre automatiquement pendant le mode
// cuisine — sans ça, un minuteur en cours peut ne se déclencher qu'au
// rallumage de l'écran plutôt qu'au bon moment (Android suspend le
// minuteur basé sur setInterval quand l'écran est éteint). Le
// verrou est automatiquement relâché par le navigateur si l'onglet
// devient invisible (changement d'application, par exemple) : il faut
// donc le redemander quand la visibilité revient, tant que le mode
// cuisine est encore ouvert.
let currentWakeLock = null;
// Une promesse partagée tant qu'une demande est en cours — empêche
// deux demandes simultanées (une à l'ouverture, une autre lors d'un
// retour de visibilité) de s'exécuter en parallèle, ce qui pouvait
// faire perdre la référence de l'une des deux (celle qui se termine en
// premier se faisant écraser par celle qui se termine ensuite).
let wakeLockRequestInFlight = null;
async function requestWakeLock() {
  if (!("wakeLock" in navigator)) return false;
  if (wakeLockRequestInFlight) return wakeLockRequestInFlight;
  wakeLockRequestInFlight = (async () => {
    try {
      currentWakeLock = await navigator.wakeLock.request("screen");
      return true;
    } catch (e) {
      // Refusé (économie d'énergie, batterie faible...) : l'écran pourra
      // s'éteindre normalement, ce n'est pas une erreur à signaler comme
      // un vrai problème technique.
      currentWakeLock = null;
      return false;
    } finally {
      wakeLockRequestInFlight = null;
    }
  })();
  return wakeLockRequestInFlight;
}
async function releaseWakeLock() {
  // Capturé localement et la variable globale remise à null
  // IMMÉDIATEMENT, avant d'attendre release() — si un nouveau verrou
  // est assigné à currentWakeLock pendant cette attente (par une
  // demande différente), il ne doit surtout pas être effacé une fois
  // ce relâchement-ci terminé.
  const lock = currentWakeLock;
  currentWakeLock = null;
  if (lock) {
    try { await lock.release(); } catch (e) { /* sans conséquence */ }
  }
}

// Demande l'autorisation de notification, une seule fois par session —
// déclenchée au premier démarrage d'un minuteur (un moment naturel où
// l'utilisateur vient d'exprimer l'intérêt pour cette fonctionnalité),
// jamais de façon proactive au chargement de la page.
let notificationPermissionAsked = false;
async function ensureNotificationPermission() {
  if (!("Notification" in window)) return false;
  if (Notification.permission === "granted") return true;
  if (Notification.permission === "denied" || notificationPermissionAsked) return false;
  notificationPermissionAsked = true;
  try {
    const result = await Notification.requestPermission();
    return result === "granted";
  } catch (e) {
    return false;
  }
}
// Affiche via le service worker (registration.showNotification) plutôt
// que le constructeur Notification direct — bien mieux pris en charge
// sur Chrome Android, et permet de gérer le clic dessus (voir
// "notificationclick" dans sw.js) pour revenir à l'application.
async function showTimerNotification() {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  try {
    if ("serviceWorker" in navigator) {
      const registration = await navigator.serviceWorker.ready;
      await registration.showNotification(t("cooking_notification_title"), {
        body: t("cooking_notification_body"),
        icon: "./icons/icon-192.png",
        tag: "cooking-timer",
      });
    } else {
      new Notification(t("cooking_notification_title"), { body: t("cooking_notification_body") });
    }
  } catch (e) { /* sans conséquence, le minuteur continue de sonner/vibrer normalement */ }
}

function openCookingMode(recipe) {
  const overlay = el(`<div class="cooking-overlay"></div>`);
  const header = el(`<div class="cooking-header">
    <h2 style="font-size:19px;">${escapeHtml(recipe.name)}</h2>
    <button class="icon-btn">${t("cooking_close")}</button>
  </div>`);
  let cookingModeOpen = true;
  const handleVisibilityChange = () => {
    // Le verrou est automatiquement relâché par le navigateur quand
    // l'onglet devient invisible — le redemander dès que la visibilité
    // revient, tant que le mode cuisine est toujours ouvert. La
    // demande étant asynchrone, l'état est revérifié après coup (voir
    // commentaire sur requestWakeLock ci-dessous).
    if (cookingModeOpen && document.visibilityState === "visible") {
      requestWakeLock().then(() => {
        if (!cookingModeOpen) releaseWakeLock();
      });
    }
  };
  document.addEventListener("visibilitychange", handleVisibilityChange);
  // Fonction nommée réutilisée à la fois par le bouton de fermeture ET
  // par "beforeClose" (déclenché par Échap) — une fermeture par Échap
  // avec un clavier externe contournait auparavant tout ce nettoyage,
  // laissant les minuteurs actifs, la lecture à voix haute en cours et
  // le Wake Lock jamais relâché. Rendue idempotente (le bouton ET le
  // MutationObserver de initModalA11y peuvent tous deux l'appeler).
  let cookingModeCleaned = false;
  function cleanupCookingMode() {
    if (cookingModeCleaned) return;
    cookingModeCleaned = true;
    state.cookingTimers.forEach(stopCookingTimer);
    state.cookingTimers = [];
    stopSpeaking();
    cookingModeOpen = false;
    document.removeEventListener("visibilitychange", handleVisibilityChange);
    releaseWakeLock();
  }
  header.querySelector("button").addEventListener("click", () => {
    cleanupCookingMode();
    overlay.remove();
  });
  overlay.appendChild(header);

  const wakeLockStatus = el(`<p style="font-size:12px;color:var(--text-muted);margin:0 0 16px;"></p>`);
  overlay.appendChild(wakeLockStatus);
  // La demande est asynchrone : si le mode cuisine est fermé avant la
  // réponse d'Android, le verrou pourrait être accordé APRÈS le
  // nettoyage (qui ne trouverait alors encore rien à relâcher) et
  // rester actif indéfiniment. Revérifie donc l'état une fois la
  // réponse reçue, et relâche immédiatement si entre-temps fermé.
  requestWakeLock().then((success) => {
    if (!cookingModeOpen) { releaseWakeLock(); return; }
    wakeLockStatus.textContent = success ? t("cooking_wake_lock_active") : t("cooking_wake_lock_unavailable");
  });

  overlay.appendChild(el(`<div class="section-label">${t("recipe_ingredients")}</div>`));
  const ingCard = el(`<div class="card" style="padding:4px 16px;margin-bottom:20px;"></div>`);
  (recipe.ingredients || []).forEach((ing) => {
    ingCard.appendChild(el(`<div class="ingredient-item"><span>${escapeHtml(translateIngredientName(ing.name))}</span><span class="ingredient-qty">${ing.quantity != null ? fmtQty(ing.quantity) + " " + escapeHtml(translateUnit(ing.unit)) : ""}</span></div>`));
  });
  overlay.appendChild(ingCard);

  if (recipe.description) {
    overlay.appendChild(el(`<div class="section-label">${t("recipe_description")}</div>`));
    overlay.appendChild(el(`<div class="card" style="padding:14px 16px;margin-bottom:12px;"><p class="prose">${escapeHtml(recipe.description)}</p></div>`));
    if ("speechSynthesis" in window) {
      const readBtn = el(`<button type="button" class="btn btn-secondary btn-sm" style="margin-bottom:20px;">${t("cooking_read_aloud")}</button>`);
      let reading = false;
      readBtn.addEventListener("click", () => {
        if (reading) {
          stopSpeaking();
          reading = false;
          readBtn.textContent = t("cooking_read_aloud");
        } else {
          speakText(recipe.description);
          reading = true;
          readBtn.textContent = t("cooking_stop_reading");
        }
      });
      // Si la lecture se termine naturellement (fin du texte), remet le
      // bouton dans son état initial plutôt que de rester bloqué sur
      // "Arrêter la lecture".
      const checkInterval = setInterval(() => {
        if (!overlay.isConnected) { clearInterval(checkInterval); return; }
        if (reading && !window.speechSynthesis.speaking) {
          reading = false;
          readBtn.textContent = t("cooking_read_aloud");
        }
      }, 500);
      overlay.appendChild(readBtn);
    }
  }

  overlay.appendChild(el(`<div class="section-label">${t("cooking_timer")}</div>`));
  state.cookingTimers = [];
  const timersHolder = el(`<div id="timers-holder"></div>`);
  overlay.appendChild(timersHolder);
  createCookingTimer(timersHolder);
  const addTimerBtn = el(`<button type="button" class="btn btn-secondary btn-sm" style="margin-bottom:24px;">${t("cooking_add_timer")}</button>`);
  addTimerBtn.addEventListener("click", () => createCookingTimer(timersHolder));
  overlay.appendChild(addTimerBtn);

  document.body.appendChild(overlay);
  initModalA11y(overlay, overlay, { beforeClose: () => cleanupCookingMode() });
}

/* ======================================================================
   THÈME
   ====================================================================== */
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("theme", theme);
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) metaTheme.setAttribute("content", theme === "dark" ? "#1C1A16" : "#2F5233");
}
function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  render();
}

/* ======================================================================
   INSTALLATION PWA (bandeau "Ajouter à l'écran d'accueil")
   ====================================================================== */
let deferredInstallPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  if (!localStorage.getItem("install_dismissed")) showInstallBanner();
});
function isRunningStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
}
function isIosDevice() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}
async function triggerInstall() {
  if (isRunningStandalone()) {
    await customAlert(t("install_already_installed"));
  } else if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
  } else if (isIosDevice()) {
    openIosInstallInstructions();
  } else {
    await customAlert(t("install_already_installed"));
  }
}
function openIosInstallInstructions() {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("install_ios_title")}</h2>
    <p class="prose" style="margin:0 0 20px;">${escapeHtml(t("install_ios_instructions"))}</p>
    <button type="button" class="btn btn-primary">${t("install_ios_close")}</button>
  </div>`);
  sheet.querySelector("button").addEventListener("click", () => overlay.remove());
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
}
function showInstallBanner() {
  if (document.querySelector(".install-banner")) return;
  const banner = el(`<div class="install-banner">
    <div class="text"><strong>${t("install_prompt_title")}</strong><span>${t("install_prompt_text")}</span></div>
    <button class="btn-install">${t("install_prompt_button")}</button>
    <button class="btn-dismiss">${t("install_prompt_dismiss")}</button>
  </div>`);
  banner.querySelector(".btn-install").addEventListener("click", async () => {
    banner.remove();
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
    }
  });
  banner.querySelector(".btn-dismiss").addEventListener("click", () => {
    localStorage.setItem("install_dismissed", "1");
    banner.remove();
  });
  document.body.appendChild(banner);
}

/* ======================================================================
   INITIALISATION
   ====================================================================== */
/* ======================================================================
   ALLERGÈNES ET NUTRITION
   Bases fournies avec l'application (mêmes données que la version
   bureau), chargées une fois au démarrage et gardées en mémoire — ce
   sont des données de référence, jamais modifiées par l'utilisateur, pas
   besoin de les stocker dans IndexedDB.
   ====================================================================== */
let ALLERGEN_DB = {};
let NUTRITION_DB = {};
let INGREDIENT_TRANSLATIONS = {}; // {en: {...}, es: {...}, de: {...}}
let INGREDIENT_REVERSE_TRANSLATIONS = {}; // même contenu, indexé en minuscules pour la résolution
let SUBSTITUTIONS_DB = {}; // clé : nom d'ingrédient en minuscules -> [{nom, note}]
let SUBSTITUTIONS_TRANSLATIONS = {}; // {en: {...}, es: {...}, de: {...}}, même structure, même ordre

async function loadReferenceData() {
  try {
    const [allergenRes, nutritionRes, enRes, esRes, deRes, subRes, subEnRes, subEsRes, subDeRes] = await Promise.all([
      fetch("./data/ingredient_allergenes.json"),
      fetch("./data/valeurs_nutritionnelles.json"),
      fetch("./data/ingredient_translations_en.json"),
      fetch("./data/ingredient_translations_es.json"),
      fetch("./data/ingredient_translations_de.json"),
      fetch("./data/ingredient_substitutions.json"),
      fetch("./data/ingredient_substitutions_en.json"),
      fetch("./data/ingredient_substitutions_es.json"),
      fetch("./data/ingredient_substitutions_de.json"),
    ]);
    ALLERGEN_DB = allergenRes.ok ? await allergenRes.json() : {};
    NUTRITION_DB = nutritionRes.ok ? await nutritionRes.json() : {};
    INGREDIENT_TRANSLATIONS = {
      en: enRes.ok ? await enRes.json() : {},
      es: esRes.ok ? await esRes.json() : {},
      de: deRes.ok ? await deRes.json() : {},
    };
    INGREDIENT_REVERSE_TRANSLATIONS = {};
    Object.keys(INGREDIENT_TRANSLATIONS).forEach((lang) => {
      INGREDIENT_REVERSE_TRANSLATIONS[lang] = {};
      Object.entries(INGREDIENT_TRANSLATIONS[lang]).forEach(([fr, translated]) => {
        INGREDIENT_REVERSE_TRANSLATIONS[lang][normalize(translated)] = fr;
      });
    });
    SUBSTITUTIONS_DB = subRes.ok ? await subRes.json() : {};
    SUBSTITUTIONS_TRANSLATIONS = {
      en: subEnRes.ok ? await subEnRes.json() : {},
      es: subEsRes.ok ? await subEsRes.json() : {},
      de: subDeRes.ok ? await subDeRes.json() : {},
    };
  } catch (e) {
    // Hors connexion au tout premier lancement (avant mise en cache) :
    // l'application continue de fonctionner, simplement sans détection
    // automatique ni traduction d'ingrédient tant que ces fichiers n'ont
    // pas pu être récupérés une première fois.
    ALLERGEN_DB = {};
    NUTRITION_DB = {};
    INGREDIENT_TRANSLATIONS = {};
    INGREDIENT_REVERSE_TRANSLATIONS = {};
    SUBSTITUTIONS_DB = {};
    SUBSTITUTIONS_TRANSLATIONS = {};
  }
}

function getReferenceSubstitutes(name) {
  return SUBSTITUTIONS_DB[(name || "").trim().toLowerCase()] || [];
}
// Les substituts personnalisés sont stockés dans la surcharge de
// l'ingrédient (comme les allergènes/nutrition/prix) — l'utilisateur les
// tape dans la langue de son choix, ils s'affichent donc tels quels,
// sans traduction automatique (contrairement à ceux de la base fournie).
function getCustomSubstitutes(name) {
  const override = INGREDIENT_OVERRIDES[(name || "").trim()];
  return (override && override.substitutes) || [];
}
function getIngredientSubstitutes(name) {
  return getReferenceSubstitutes(name).concat(getCustomSubstitutes(name));
}
// Retourne les substituts d'un ingrédient traduits pour l'affichage,
// en conservant toujours la même donnée française en interne pour ceux
// de la base fournie. La traduction se fait par position dans la liste
// (même ordre que la base française), avec repli sur le texte français
// si l'index n'a pas d'équivalent traduit. Les substituts personnalisés
// sont ajoutés après, toujours dans leur langue d'origine.
function getDisplaySubstitutes(name) {
  const referenceList = getReferenceSubstitutes(name);
  const customList = getCustomSubstitutes(name);
  if (CURRENT_LANG === "fr" || !referenceList.length) {
    return referenceList.concat(customList);
  }
  const key = (name || "").trim().toLowerCase();
  const translatedList = (SUBSTITUTIONS_TRANSLATIONS[CURRENT_LANG] || {})[key];
  const translatedReference = translatedList ? referenceList.map((entry, idx) => translatedList[idx] || entry) : referenceList;
  return translatedReference.concat(customList);
}

// Calculé une seule fois par langue (mis en cache) : l'ensemble des
// traductions qui correspondent à plusieurs noms français différents
// (souvent de vrais synonymes, ex. "Arachide"/"Cacahuète" donnant tous
// deux "Peanut" en anglais) — sans désambiguïsation, ces ingrédients
// pourtant différents apparaissent comme deux suggestions identiques.
const _ingredientTranslationCollisionsCache = {};
function getIngredientTranslationCollisions(lang) {
  if (_ingredientTranslationCollisionsCache[lang]) return _ingredientTranslationCollisionsCache[lang];
  const dict = INGREDIENT_TRANSLATIONS[lang];
  const collisions = new Set();
  if (dict) {
    const counts = {};
    Object.values(dict).forEach((v) => { counts[v] = (counts[v] || 0) + 1; });
    Object.keys(counts).forEach((v) => { if (counts[v] > 1) collisions.add(v); });
  }
  _ingredientTranslationCollisionsCache[lang] = collisions;
  return collisions;
}
function translateIngredientName(name) {
  if (!name || CURRENT_LANG === "fr") return name;
  const dict = INGREDIENT_TRANSLATIONS[CURRENT_LANG];
  if (!dict) return name;
  const translated = dict[name];
  if (!translated) return name;
  const collisions = getIngredientTranslationCollisions(CURRENT_LANG);
  return collisions.has(translated) ? `${translated} (${name})` : translated;
}
// Compare deux noms d'ingrédients selon leur traduction AFFICHÉE dans la
// langue actuelle, pas selon leur nom français interne — sans ça, la
// liste apparaissait triée dans le désordre pour toute langue autre que
// le français (l'ordre alphabétique français ne correspond pas
// forcément à l'ordre alphabétique de la traduction affichée).
function compareIngredientNamesForDisplay(a, b) {
  return translateIngredientName(a).localeCompare(translateIngredientName(b), CURRENT_LANG);
}
// Résout un nom d'ingrédient tapé ou sélectionné, qu'il soit en français
// ou dans la langue actuellement affichée, vers son nom canonique
// français — pour que la saisie reste bilingue comme partout ailleurs
// dans l'application (même principe que la version bureau).
function resolveIngredientInput(typedName) {
  const trimmed = (typedName || "").trim();
  if (!trimmed) return trimmed;
  const exact = state.ingredientNames.find((n) => normalize(n) === normalize(trimmed));
  if (exact) return exact;
  // Forme désambiguïsée d'une collision de traduction, ex.
  // "Peanut (Arachide)" — la partie entre parenthèses est le nom
  // français d'origine (voir translateIngredientName) : si elle
  // correspond à un ingrédient déjà connu, on la retrouve directement,
  // sans quoi resaisir ce libellé complet créerait à tort un nouvel
  // ingrédient personnalisé plutôt que de reconnaître l'original.
  const parenMatch = trimmed.match(/\(([^()]+)\)\s*$/);
  if (parenMatch) {
    const inner = parenMatch[1].trim();
    const exactInner = state.ingredientNames.find((n) => normalize(n) === normalize(inner));
    if (exactInner) return exactInner;
  }
  const dict = INGREDIENT_REVERSE_TRANSLATIONS[CURRENT_LANG];
  if (dict) {
    const resolved = dict[normalize(trimmed)];
    if (resolved) return resolved;
  }
  return trimmed;
}

/* ======================================================================
   LISTE DES INGRÉDIENTS (utilisée pour la recherche/autocomplétion)
   Contrairement aux allergènes/nutrition (données de référence figées),
   cette liste appartient à l'utilisateur : préremplie avec les ~1000
   ingrédients courants au premier lancement, puis modifiable (ajout,
   renommage, suppression) depuis "🥕 Gérer les ingrédients".
   ====================================================================== */
async function ensureIngredientListLoaded() {
  const existing = await storeAll("ingredients");
  if (existing.length) {
    state.ingredientNames = existing.map((i) => i.name).sort(compareIngredientNamesForDisplay);
    return;
  }
  // Première utilisation : préremplit avec la liste fournie.
  try {
    const res = await fetch("./data/ingredients_par_defaut.json");
    const defaults = res.ok ? await res.json() : [];
    for (const name of defaults) await storePut("ingredients", { name });
    state.ingredientNames = defaults.slice().sort(compareIngredientNamesForDisplay);
  } catch (e) {
    state.ingredientNames = [];
  }
}
async function addIngredientName(name) {
  const trimmed = (name || "").trim();
  if (!trimmed) return false;
  const key = normalize(trimmed);
  if (state.ingredientNames.some((n) => normalize(n) === key)) return false;
  await storePut("ingredients", { name: trimmed });
  state.ingredientNames.push(trimmed);
  state.ingredientNames.sort(compareIngredientNamesForDisplay);
  return true;
}
async function renameIngredientName(oldName, newName) {
  const trimmed = (newName || "").trim();
  if (!trimmed || trimmed === oldName) return false;
  await storeDelete("ingredients", oldName);
  await storePut("ingredients", { name: trimmed });
  state.ingredientNames = state.ingredientNames.filter((n) => n !== oldName);
  state.ingredientNames.push(trimmed);
  state.ingredientNames.sort(compareIngredientNamesForDisplay);
  await moveIngredientOverride(oldName, trimmed);
  // Met aussi à jour ce nom partout où il est déjà utilisé, pour ne pas
  // casser les recettes/listes existantes — sans cette propagation, un
  // ingrédient renommé continuait à apparaître sous son ancien nom dans
  // la liste de courses, le garde-manger et les listes enregistrées,
  // créant des doublons de fait entre l'ancien et le nouveau nom.
  let touched = false;
  state.recipes.forEach((r) => {
    (r.ingredients || []).forEach((ing) => {
      if (ing.name === oldName) { ing.name = trimmed; touched = true; }
    });
  });
  if (touched) for (const r of state.recipes) await storePut("recipes", r);

  for (const item of state.shopping) {
    if (item.name === oldName) {
      item.name = trimmed;
      await storePut("shopping", item);
    }
  }
  for (const item of state.pantry) {
    if (item.name === oldName) {
      item.name = trimmed;
      await storePut("pantry", item);
    }
  }
  let savedListsTouched = false;
  state.savedShoppingLists.forEach((list) => {
    (list.items || []).forEach((item) => {
      if (item.name === oldName) { item.name = trimmed; savedListsTouched = true; }
    });
  });
  if (savedListsTouched) {
    for (const list of state.savedShoppingLists) await storePut("savedShoppingLists", list);
  }
  return true;
}
async function deleteIngredientName(name) {
  await storeDelete("ingredients", name);
  state.ingredientNames = state.ingredientNames.filter((n) => n !== name);
  await deleteIngredientOverrideFor(name);
}
function searchIngredientNames(query, limit) {
  const key = normalize(query);
  if (!key) return [];
  const starts = [];
  const contains = [];
  state.ingredientNames.forEach((n) => {
    const nk = normalize(n);
    const tk = CURRENT_LANG !== "fr" ? normalize(translateIngredientName(n)) : null;
    if (nk.startsWith(key) || (tk && tk.startsWith(key))) starts.push(n);
    else if (nk.includes(key) || (tk && tk.includes(key))) contains.push(n);
  });
  return starts.concat(contains).slice(0, limit || 8);
}

/* ======================================================================
   DÉTECTION DE DOUBLONS D'INGRÉDIENTS
   Repère les paires de noms d'ingrédients qui se ressemblent fortement
   (ex. "Tomate" / "Tomates", "Echalotte" / "Échalote"), pouvant indiquer
   un doublon ou une faute de frappe dans la liste. Même algorithme que
   la version bureau (Ratcliff/Obershelp, comme Python difflib), pour un
   comportement identique entre les deux applications.
   ====================================================================== */
function findLongestMatch(a, b, alo, ahi, blo, bhi) {
  let besti = alo, bestj = blo, bestsize = 0;
  const b2j = {};
  for (let i = blo; i < bhi; i++) {
    const c = b[i];
    (b2j[c] = b2j[c] || []).push(i);
  }
  let j2len = {};
  for (let i = alo; i < ahi; i++) {
    const newj2len = {};
    const indices = b2j[a[i]] || [];
    for (const j of indices) {
      if (j < blo) continue;
      if (j >= bhi) break;
      const k = (j2len[j - 1] || 0) + 1;
      newj2len[j] = k;
      if (k > bestsize) { besti = i - k + 1; bestj = j - k + 1; bestsize = k; }
    }
    j2len = newj2len;
  }
  return [besti, bestj, bestsize];
}
function matchingBlocksRec(a, b, alo, ahi, blo, bhi, result) {
  const [i, j, k] = findLongestMatch(a, b, alo, ahi, blo, bhi);
  if (k > 0) {
    if (alo < i && blo < j) matchingBlocksRec(a, b, alo, i, blo, j, result);
    result.push(k);
    if (i + k < ahi && j + k < bhi) matchingBlocksRec(a, b, i + k, ahi, j + k, bhi, result);
  }
}
function sequenceMatcherRatio(a, b) {
  const result = [];
  matchingBlocksRec(a, b, 0, a.length, 0, b.length, result);
  const matches = result.reduce((sum, k) => sum + k, 0);
  const total = a.length + b.length;
  return total === 0 ? 1 : (2 * matches) / total;
}
function findSimilarIngredientPairs(names, threshold) {
  threshold = threshold || 0.9;
  const normalized = names.map((n) => [n, normalize(n)]);
  const buckets = {};
  normalized.forEach(([name, key]) => {
    const prefix = key.length >= 2 ? key.slice(0, 2) : key;
    (buckets[prefix] = buckets[prefix] || []).push([name, key]);
  });
  const pairs = [];
  Object.values(buckets).forEach((bucket) => {
    for (let i = 0; i < bucket.length; i++) {
      const [nameA, keyA] = bucket[i];
      for (let j = i + 1; j < bucket.length; j++) {
        const [nameB, keyB] = bucket[j];
        if (keyA === keyB) continue;
        const isPluralVariant = keyA === keyB + "s" || keyA === keyB + "x" || keyB === keyA + "s" || keyB === keyA + "x";
        const ratio = sequenceMatcherRatio(keyA, keyB);
        if (isPluralVariant || ratio >= threshold) {
          pairs.push([nameA, nameB, isPluralVariant ? Math.max(ratio, 0.9) : ratio]);
        }
      }
    }
  });
  pairs.sort((a, b) => b[2] - a[2]);
  return pairs;
}

let DISMISSED_PAIRS = new Set();
function pairKey(a, b) {
  return [normalize(a), normalize(b)].sort().join("␟");
}
async function loadDismissedPairs() {
  const saved = await kvGet("dismissedIngredientPairs");
  DISMISSED_PAIRS = new Set(saved || []);
}
async function dismissPair(a, b) {
  DISMISSED_PAIRS.add(pairKey(a, b));
  await kvSet("dismissedIngredientPairs", Array.from(DISMISSED_PAIRS));
}
function isPairDismissed(a, b) {
  return DISMISSED_PAIRS.has(pairKey(a, b));
}

// Fusionne deux ingrédients considérés comme doublons : "remove" disparaît
// de la liste, et toutes les recettes qui l'utilisaient sont mises à jour
// pour utiliser "keep" à la place. Si "remove" avait des données propres
// (allergènes/nutrition/prix) et que "keep" n'en a pas encore, elles sont
// conservées ; sinon celles de "keep" priment.
async function mergeIngredientNames(keep, remove) {
  await storeDelete("ingredients", remove);
  state.ingredientNames = state.ingredientNames.filter((n) => n !== remove);
  if (!INGREDIENT_OVERRIDES[keep] && INGREDIENT_OVERRIDES[remove]) {
    await moveIngredientOverride(remove, keep);
  } else if (INGREDIENT_OVERRIDES[remove]) {
    await deleteIngredientOverrideFor(remove);
  }
  let touched = false;
  state.recipes.forEach((r) => {
    (r.ingredients || []).forEach((ing) => {
      if (normalize(ing.name) === normalize(remove)) { ing.name = keep; touched = true; }
    });
  });
  if (touched) for (const r of state.recipes) await storePut("recipes", r);
  // La fusion doit aussi se propager à la liste de courses, au
  // garde-manger et aux listes de courses enregistrées — sans ça,
  // l'ancien nom pouvait rester visible à ces endroits après une
  // fusion, comme s'il s'agissait encore d'un ingrédient différent.
  let shoppingTouched = false;
  state.shopping.forEach((item) => {
    if (normalize(item.name) === normalize(remove)) { item.name = keep; shoppingTouched = true; }
  });
  if (shoppingTouched) for (const item of state.shopping) await storePut("shopping", item);
  let pantryTouched = false;
  state.pantry.forEach((item) => {
    if (normalize(item.name) === normalize(remove)) { item.name = keep; pantryTouched = true; }
  });
  if (pantryTouched) for (const item of state.pantry) await storePut("pantry", item);
  let savedListsTouched = false;
  state.savedShoppingLists.forEach((saved) => {
    (saved.items || []).forEach((item) => {
      if (normalize(item.name) === normalize(remove)) { item.name = keep; savedListsTouched = true; }
    });
  });
  if (savedListsTouched) for (const saved of state.savedShoppingLists) await storePut("savedShoppingLists", saved);
}

/* ======================================================================
   AUTOCOMPLÉTION D'INGRÉDIENT (composant réutilisable)
   Attache à un champ texte une liste déroulante filtrée au fur et à
   mesure de la saisie, pour retrouver et sélectionner rapidement un
   ingrédient existant. La saisie libre reste toujours possible (pour un
   ingrédient réellement nouveau) : la liste ne fait que suggérer.
   ====================================================================== */
// Cherche l'ingrédient existant le plus proche d'un texte tapé, même
// quand ça ne correspond à aucun résultat de recherche classique (ex.
// "Tomates" tapé alors que seul "Tomate" existe : la recherche par
// sous-chaîne classique ne le trouve pas puisque le texte tapé est plus
// long que l'ingrédient existant). Utilisé pour suggérer "Vouliez-vous
// dire..." et éviter de créer un doublon par variante plurielle ou
// faute de frappe.
function findClosestIngredientMatch(typedName) {
  const key = normalize(typedName);
  if (key.length < 3) return null;
  let best = null;
  state.ingredientNames.forEach((name) => {
    const nk = normalize(name);
    if (nk === key) return;
    const isPluralVariant = key === nk + "s" || key === nk + "x" || nk === key + "s" || nk === key + "x";
    const ratio = sequenceMatcherRatio(key, nk);
    const effectiveRatio = isPluralVariant ? Math.max(ratio, 0.9) : ratio;
    if (effectiveRatio >= 0.85 && (!best || effectiveRatio > best.ratio)) {
      best = { name, ratio: effectiveRatio };
    }
  });
  return best;
}

let autocompleteIdCounter = 0;
function attachIngredientAutocomplete(input, onChange) {
  let dropdown = null;
  let items = []; // éléments actuellement affichés dans la liste
  let highlightedIndex = -1;
  const listboxId = `autocomplete-listbox-${++autocompleteIdCounter}`;

  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", listboxId);

  function setHighlighted(index) {
    items.forEach((item, i) => item.setAttribute("aria-selected", String(i === index)));
    highlightedIndex = index;
    if (index >= 0 && items[index]) {
      items[index].scrollIntoView({ block: "nearest" });
      input.setAttribute("aria-activedescendant", items[index].id);
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  function close() {
    if (dropdown) { dropdown.remove(); dropdown = null; }
    items = [];
    highlightedIndex = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }
  function open() {
    close();
    const results = searchIngredientNames(input.value, 8);
    const closest = findClosestIngredientMatch(input.value);
    const showSuggestion = closest && !results.some((r) => normalize(r) === normalize(closest.name));
    if (!results.length && !showSuggestion) return;
    dropdown = document.createElement("div");
    dropdown.className = "autocomplete-dropdown";
    dropdown.id = listboxId;
    dropdown.setAttribute("role", "listbox");
    let itemIndex = 0;
    if (showSuggestion) {
      const suggestItem = document.createElement("div");
      suggestItem.className = "autocomplete-item add-new";
      suggestItem.id = `${listboxId}-item-${itemIndex++}`;
      suggestItem.setAttribute("role", "option");
      suggestItem.setAttribute("aria-selected", "false");
      suggestItem.textContent = t("ingredient_did_you_mean", { name: translateIngredientName(closest.name) });
      suggestItem.addEventListener("mousedown", (e) => e.preventDefault());
      suggestItem.addEventListener("click", () => {
        input.value = translateIngredientName(closest.name);
        onChange(closest.name);
        close();
      });
      dropdown.appendChild(suggestItem);
      items.push(suggestItem);
    }
    results.forEach((frenchName) => {
      const item = document.createElement("div");
      item.className = "autocomplete-item";
      item.id = `${listboxId}-item-${itemIndex++}`;
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", "false");
      item.textContent = translateIngredientName(frenchName);
      item.addEventListener("mousedown", (e) => e.preventDefault());
      item.addEventListener("click", () => {
        input.value = translateIngredientName(frenchName);
        onChange(frenchName);
        close();
      });
      dropdown.appendChild(item);
      items.push(item);
    });
    input.parentElement.appendChild(dropdown);
    input.setAttribute("aria-expanded", "true");
  }

  input.addEventListener("input", () => {
    // Tant que rien n'est explicitement sélectionné dans la liste, on
    // résout au mieux ce qui est tapé (au cas où ça correspondrait déjà
    // exactement à un ingrédient connu, en français ou dans la langue
    // affichée) ; sinon on garde le texte libre tel quel pour permettre
    // un ingrédient réellement nouveau.
    onChange(resolveIngredientInput(input.value));
    open();
  });
  input.addEventListener("focus", open);
  input.addEventListener("blur", () => setTimeout(close, 200));
  // Navigation au clavier : flèches pour parcourir la liste, Entrée
  // pour choisir l'élément en surbrillance, Échap pour fermer — sans
  // ça, l'autocomplétion n'était utilisable qu'à la souris/au toucher.
  input.addEventListener("keydown", (e) => {
    if (!items.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted(highlightedIndex < items.length - 1 ? highlightedIndex + 1 : 0);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted(highlightedIndex > 0 ? highlightedIndex - 1 : items.length - 1);
    } else if (e.key === "Enter" && highlightedIndex >= 0) {
      e.preventDefault();
      items[highlightedIndex].dispatchEvent(new MouseEvent("mousedown"));
      items[highlightedIndex].click();
    } else if (e.key === "Escape") {
      close();
    }
  });
}

/* ======================================================================
   SURCHARGES PERSONNALISÉES D'INGRÉDIENT (allergènes / nutrition)
   Un utilisateur peut corriger ou compléter les allergènes et valeurs
   nutritionnelles d'un ingrédient précis, sans jamais modifier les
   bases fournies avec l'application : la surcharge est prioritaire
   quand elle existe, sinon on retombe sur la base de référence.
   ====================================================================== */
let INGREDIENT_OVERRIDES = {};
async function loadIngredientOverrides() {
  const all = await storeAll("ingredientOverrides");
  INGREDIENT_OVERRIDES = {};
  all.forEach((o) => { INGREDIENT_OVERRIDES[o.name] = o; });
}
async function setIngredientOverride(name, allergens, nutrition, price, substitutes) {
  const record = { name, allergens: allergens || [], nutrition: nutrition || null, price: price || null, substitutes: substitutes || [] };
  await storePut("ingredientOverrides", record);
  INGREDIENT_OVERRIDES[name] = record;
}
async function moveIngredientOverride(oldName, newName) {
  if (!INGREDIENT_OVERRIDES[oldName]) return;
  const record = { ...INGREDIENT_OVERRIDES[oldName], name: newName };
  await storeDelete("ingredientOverrides", oldName);
  await storePut("ingredientOverrides", record);
  delete INGREDIENT_OVERRIDES[oldName];
  INGREDIENT_OVERRIDES[newName] = record;
}
async function deleteIngredientOverrideFor(name) {
  if (!INGREDIENT_OVERRIDES[name]) return;
  await storeDelete("ingredientOverrides", name);
  delete INGREDIENT_OVERRIDES[name];
}

function getIngredientAllergens(name) {
  const key = (name || "").trim();
  if (INGREDIENT_OVERRIDES[key]) return INGREDIENT_OVERRIDES[key].allergens || [];
  return ALLERGEN_DB[key] || [];
}
function computeRecipeAllergens(ingredients) {
  const found = new Set();
  (ingredients || []).forEach((ing) => {
    getIngredientAllergens(ing.name).forEach((a) => found.add(a));
  });
  return ALLERGEN_OPTIONS.filter((a) => found.has(a));
}
function getIngredientNutrition(name) {
  const key = (name || "").trim();
  if (INGREDIENT_OVERRIDES[key]) return INGREDIENT_OVERRIDES[key].nutrition || null;
  return NUTRITION_DB[key] || null;
}
function computeRecipeNutrition(ingredients) {
  let kcal = 0, protein = 0, carbs = 0, fat = 0, known = 0;
  const total = (ingredients || []).length;
  (ingredients || []).forEach((ing) => {
    const info = getIngredientNutrition(ing.name);
    if (!info || ing.quantity == null) return;
    // Les quantités des ingrédients sont stockées pour 1 personne : le
    // résultat de ce calcul est donc directement une estimation "par
    // personne", sans avoir besoin de multiplier par le nombre de
    // convives affiché.
    const unitLower = (ing.unit || "").toLowerCase();
    let grams = null;
    if (unitLower === "g") grams = ing.quantity;
    else if (unitLower === "kg") grams = ing.quantity * 1000;
    else if (unitLower === "cl") grams = ing.quantity * 10;
    else if (unitLower === "l") grams = ing.quantity * 1000;
    if (grams == null) return;
    const factor = grams / 100;
    kcal += (info.kcal || 0) * factor;
    protein += (info.protein_g || 0) * factor;
    carbs += (info.carbs_g || 0) * factor;
    fat += (info.fat_g || 0) * factor;
    known++;
  });
  if (!known) return null;
  return {
    kcal: Math.round(kcal),
    protein: Math.round(protein * 10) / 10,
    carbs: Math.round(carbs * 10) / 10,
    fat: Math.round(fat * 10) / 10,
    partial: known < total,
    known,
    total,
  };
}

/* ======================================================================
   PRIX DES INGRÉDIENTS
   Comme la nutrition et les allergènes, le prix d'un ingrédient est
   stocké dans sa surcharge personnelle (ingredientOverrides) : {amount,
   unit} représentant "prix pour 1 [unit]" (ex. 2,50 € pour 1 kg).
   ====================================================================== */
function getIngredientPrice(name) {
  const key = (name || "").trim();
  const override = INGREDIENT_OVERRIDES[key];
  return (override && override.price) || null;
}

// Convertit une quantité + unité vers une unité de base commune (poids en
// grammes, volume en centilitres, ou comptage à l'unité), pour pouvoir
// comparer un prix et une quantité même si leurs unités diffèrent
// (ex. prix au kg, quantité en g). Deux quantités ne sont comparables
// que si elles ont la même "famille" (kind) — un prix au kg ne peut pas
// s'appliquer à une quantité en pièces, par exemple.
function unitToBase(quantity, unit) {
  const lu = (unit || "").toLowerCase();
  if (lu === "g") return { kind: "weight", value: quantity };
  if (lu === "kg") return { kind: "weight", value: quantity * 1000 };
  if (lu === "cl") return { kind: "volume", value: quantity };
  if (lu === "l") return { kind: "volume", value: quantity * 100 };
  // Les unités restantes (pièce, boîte, sachet, pot, tranche, gousse,
  // autre) ne sont PAS interchangeables entre elles — une boîte n'a
  // pas de taille standard comparable à une pièce ou un sachet. Chacune
  // devient son propre groupe ("count:unité"), pour n'être jamais
  // considérée compatible avec une autre unité de comptage différente.
  return { kind: "count:" + lu, value: quantity };
}

// Réduit la quantité à acheter d'un ingrédient selon ce qui est déjà
// disponible au garde-manger — uniquement quand les unités sont
// directement comparables (même nature : poids, volume, ou nombre de
// pièces), sinon on ne déduit rien plutôt que de risquer un calcul
// trompeur (ex. "2 pièces" contre "500 g" ne se comparent pas).
//
// Important : suit aussi, pour la session en cours, la quantité déjà
// "réservée" par des ajouts précédents (state.pantryClaimedThisSession)
// — sans ce suivi, ajouter séparément deux recettes ayant chacune
// besoin de 800 g d'un ingrédient dont le garde-manger contient 1 kg
// aboutissait à ce que les DEUX soient considérées comme entièrement
// couvertes (chacune comparée seule au stock complet), alors que le
// besoin réel cumulé (1,6 kg) dépasse largement ce qui est disponible.
//
// Le registre est un TABLEAU d'entrées individuelles (pas un simple
// total par ingrédient) : { id, ingredientKey, amount, sourceType,
// sourceId }. "sourceType"/"sourceId" identifient précisément ce qui a
// créé la réservation (un article de courses, un article de
// garde-manger, ou l'ajout d'une recette entière) — ce qui permet de
// libérer UNIQUEMENT la réservation concernée quand sa source
// disparaît, sans jamais effacer une réservation créée par une autre
// source pour ce même ingrédient (défaut confirmé des versions
// précédentes : effacer toute réservation portant le même nom
// d'ingrédient, même si deux recettes différentes l'avaient réservé
// séparément).
function getTotalClaimedForIngredient(ingredientKey, claimsArray) {
  const claims = claimsArray || state.pantryClaimedThisSession;
  return claims.filter((c) => c.ingredientKey === ingredientKey).reduce((sum, c) => sum + c.amount, 0);
}
// Calcule la réduction possible sans modifier l'état — un simple calcul
// en lecture seule. "pendingClaims" permet de simuler des réservations
// pas encore confirmées (utile pour cumuler plusieurs ingrédients d'une
// même recette avant la confirmation, sans toucher au vrai état tant
// que l'utilisateur n'a pas validé).
function computePantryReduction(name, unit, neededQty, pendingClaims) {
  const noReduction = { adjustedQty: neededQty, reducedAmount: 0, fullyCovered: false };
  if (neededQty == null) return noReduction;
  const pantryItem = state.pantry.find((p) => normalize(p.name) === normalize(name));
  if (!pantryItem || pantryItem.quantity == null) return noReduction;
  const neededBase = unitToBase(neededQty, unit);
  const pantryBase = unitToBase(pantryItem.quantity, pantryItem.unit);
  if (neededBase.kind !== pantryBase.kind || neededBase.value <= 0) return noReduction;

  const key = normalize(name);
  const claims = pendingClaims || state.pantryClaimedThisSession;
  const alreadyClaimed = getTotalClaimedForIngredient(key, claims);
  const effectiveAvailable = Math.max(0, pantryBase.value - alreadyClaimed);
  if (effectiveAvailable <= 0) return noReduction;

  if (effectiveAvailable >= neededBase.value) {
    return { adjustedQty: null, reducedAmount: neededQty, fullyCovered: true, claimKey: key, claimAmount: neededBase.value };
  }
  const remainingRatio = (neededBase.value - effectiveAvailable) / neededBase.value;
  const adjustedQty = neededQty * remainingRatio;
  return { adjustedQty, reducedAmount: neededQty - adjustedQty, fullyCovered: false, claimKey: key, claimAmount: effectiveAvailable };
}
// N'applique réellement la réservation qu'une fois l'utilisateur passé
// par la confirmation — à appeler uniquement après un customConfirm()
// accepté, jamais avant, pour qu'un "Annuler" n'affecte jamais l'état.
// "sourceType"/"sourceId" identifient ce qui crée cette réservation
// précise (voir commentaire ci-dessus) — obligatoires pour pouvoir la
// libérer plus tard sans toucher aux réservations d'autres sources.
function commitPantryClaim(ingredientKey, amount, sourceType, sourceId) {
  state.pantryClaimedThisSession.push({ id: uid(), ingredientKey, amount, sourceType, sourceId });
  persistPantryClaims();
}
// Libère uniquement les réservations liées à cette source précise —
// jamais les autres réservations du même ingrédient créées ailleurs.
// Libère TOUTES les réservations d'un ingrédient, peu importe leur
// source — spécifiquement pour la suppression/modification d'un
// article de GARDE-MANGER : si le stock physique réservé change ou
// disparaît de façon imprévisible, toute réservation contre ce stock
// devient invalide, quelle que soit la source qui l'avait créée
// (contrairement à la suppression d'un article de COURSES, qui ne
// devrait libérer que SA propre réservation — voir
// releasePantryClaimsForSource ci-dessus).
function releasePantryClaimsForIngredient(ingredientKey) {
  const before = state.pantryClaimedThisSession.length;
  state.pantryClaimedThisSession = state.pantryClaimedThisSession.filter((c) => c.ingredientKey !== ingredientKey);
  if (state.pantryClaimedThisSession.length !== before) persistPantryClaims();
}
function releasePantryClaimsForSource(sourceType, sourceId) {
  const before = state.pantryClaimedThisSession.length;
  state.pantryClaimedThisSession = state.pantryClaimedThisSession.filter(
    (c) => !(c.sourceType === sourceType && c.sourceId === sourceId)
  );
  if (state.pantryClaimedThisSession.length !== before) persistPantryClaims();
}
// Sauvegarde légère dans localStorage (pas IndexedDB, un simple tableau
// suffit) — sans ça, les réservations de la session n'étaient
// conservées qu'en mémoire et disparaissaient à chaque redémarrage de
// l'application, pouvant faire recompter deux fois le même stock si
// l'utilisateur fermait puis rouvrait l'app entre deux ajouts de
// recettes à la liste de courses.
function persistPantryClaims() {
  kvSet("pantryClaimedThisSession", state.pantryClaimedThisSession).catch(() => { /* sans conséquence */ });
}
// Valide chaque entrée individuellement — un tableau chargé (depuis une
// sauvegarde restaurée, potentiellement modifiée à la main ou
// corrompue) peut contenir des entrées malformées qui provoqueraient
// des erreurs ailleurs (affichage des réservations, calculs de
// réduction) si elles étaient conservées telles quelles.
function sanitizePantryClaims(rawClaims) {
  if (!Array.isArray(rawClaims)) return [];
  return rawClaims.filter((c) =>
    c && typeof c === "object" && !Array.isArray(c) &&
    typeof c.ingredientKey === "string" && c.ingredientKey.trim() &&
    Number.isFinite(c.amount) && c.amount > 0 &&
    (c.sourceType === "recipe" || c.sourceType === "shopping") &&
    typeof c.sourceId === "string" && c.sourceId.trim()
  );
}
async function loadPantryClaims() {
  try {
    const raw = await kvGet("pantryClaimedThisSession");
    // Compatibilité avec l'ancien format (objet {ingrédient: total},
    // utilisé jusqu'à la v153) — ignoré simplement plutôt que de
    // planter dessus : ces anciennes réservations n'ont de toute façon
    // plus d'origine identifiable, elles ne peuvent pas être converties
    // fidèlement vers le nouveau format par source précise.
    state.pantryClaimedThisSession = sanitizePantryClaims(raw);
  } catch (e) {
    state.pantryClaimedThisSession = [];
  }
}

function computeIngredientCost(name, quantity, unit) {
  const price = getIngredientPrice(name);
  if (!price || quantity == null || !price.amount) return null;
  const itemBase = unitToBase(quantity, unit);
  const priceUnitBase = unitToBase(1, price.unit);
  if (itemBase.kind !== priceUnitBase.kind) return null;
  return (price.amount / priceUnitBase.value) * itemBase.value;
}

function computeShoppingTotal(items) {
  let total = 0;
  let known = 0;
  let unknown = 0;
  (items || []).forEach((item) => {
    const cost = computeIngredientCost(item.name, item.quantity, item.unit);
    if (cost == null) unknown++;
    else { total += cost; known++; }
  });
  return { total: Math.round(total * 100) / 100, known, unknown };
}

/* ======================================================================
   SAUVEGARDE / RESTAURATION
   Exporte toutes les données personnelles dans un seul fichier .json
   téléchargeable, et permet de le recharger plus tard (sur le même
   appareil après réinitialisation, ou sur un autre appareil).
   ====================================================================== */
const BACKUP_STORES = ["recipes", "shopping", "pantry", "ingredients", "ingredientOverrides", "menus", "planTemplates", "planHistory", "trash", "savedShoppingLists", "kv"];

async function buildBackupData() {
  const data = { exportedAt: new Date().toISOString(), version: 1 };
  for (const storeName of BACKUP_STORES) {
    data[storeName] = await storeAll(storeName);
  }
  return data;
}
function backupFileName() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const dateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const timeStr = `${pad(now.getHours())}-${pad(now.getMinutes())}`;
  return `mes-recettes-sauvegarde-${dateStr}_${timeStr}.json`;
}
// Nom dédié au partage (pas au téléchargement direct) : ".txt" plutôt
// que ".json", cohérent avec le type "text/plain" déjà utilisé pour le
// partage — une extension qui ne correspond pas au type MIME déclaré
// peut faire échouer la validation de certains navigateurs avant même
// que le menu de partage ne s'ouvre. Le contenu reste le même JSON ;
// seule l'extension change. La restauration accepte déjà les deux
// extensions par contenu, pas seulement par extension.
function backupShareFileName() {
  return backupFileName().replace(/\.json$/, ".txt");
}
async function buildBackupFile() {
  const data = await buildBackupData();
  // "text/plain" plutôt que "application/json" pour le partage
  // spécifiquement : plusieurs sources indiquent une prise en charge
  // plus large de ce type MIME par le partage natif Android, alors que
  // application/json n'est pas toujours reconnu comme partageable. Le
  // nom de fichier utilise désormais ".txt" (voir backupShareFileName),
  // cohérent avec ce type MIME — la réimportation accepte les deux
  // extensions par contenu, pas seulement par extension.
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "text/plain" });
  return new File([blob], backupShareFileName(), { type: "text/plain" });
}
async function exportAllData() {
  const data = await buildBackupData();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = backupFileName();
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  localStorage.setItem("lastBackupAt", new Date().toISOString());
}
// Ouvre le menu de partage natif du téléphone avec le fichier de
// sauvegarde, pour l'envoyer vers Google Drive, Dropbox, OneDrive, par
// email... selon ce que l'utilisateur a d'installé — pas d'intégration
// directe avec un service en particulier, l'utilisateur choisit à
// chaque fois. Retourne { ok: false } si le partage échoue.
//
// Prend directement un fichier déjà résolu (pas une promesse) : aucun
// await ne doit précéder l'appel à navigator.share() lui-même, sinon le
// navigateur peut considérer que le clic de l'utilisateur n'est plus
// "actif" au moment de l'appel, ce qui provoque une erreur
// "NotAllowedError" même quand le partage serait normalement possible.
function shareBackupData(file) {
  if (!navigator.canShare || !navigator.canShare({ files: [file] })) {
    return Promise.resolve({ ok: false, cancelled: false });
  }
  return navigator.share({ files: [file], title: t("backup_share_title") }).then(
    () => {
      localStorage.setItem("lastBackupAt", new Date().toISOString());
      return { ok: true, cancelled: false };
    },
    (e) => {
      // "AbortError" : l'utilisateur a lui-même fermé le menu de partage
      // sans rien choisir — un choix délibéré, pas une erreur à afficher
      // ni un cas où basculer sur le téléchargement classique. Toute
      // autre erreur est un vrai échec technique à ne pas cacher.
      if (e && e.name === "AbortError") return { ok: true, cancelled: true };
      return { ok: false, cancelled: false, error: formatCaughtError(e) };
    }
  );
}

// Taille maximale raisonnable pour un fichier de sauvegarde — au-delà,
// soit le fichier est corrompu/mal formé, soit il ne peut de toute
// façon pas provenir d'un usage normal de l'application (même avec
// beaucoup de photos, cette limite laisse une large marge).
const MAX_BACKUP_FILE_SIZE = 50 * 1024 * 1024; // 50 Mo

// Un champ photo valide est soit absent, soit une image encodée en
// data URL — jamais une chaîne arbitraire, pour éviter qu'une valeur
// fabriquée dans un fichier de sauvegarde modifié ne se retrouve
// utilisée telle quelle comme adresse d'image ailleurs dans l'app.
function isValidPhotoField(photo) {
  return photo == null || (typeof photo === "string" && /^data:image\/(png|jpe?g|webp|gif);base64,/i.test(photo));
}

// Un identifiant valide est une chaîne non vide — tous les entrepôts de
// sauvegarde utilisent soit "id" soit "key" (pour "kv") comme clé
// primaire ; un enregistrement sans identifiant valide serait rejeté
// silencieusement par IndexedDB ou pourrait en écraser un autre de
// façon imprévisible.
function hasValidId(item, storeName) {
  // "kv" utilise "key", "ingredients" et "ingredientOverrides"
  // utilisent "name" (voir la création des entrepôts IndexedDB) — tous
  // les autres utilisent "id". Sans cette distinction, chaque
  // restauration filtrait silencieusement la totalité des ingrédients
  // personnalisés et de leurs surcharges (allergènes, prix, valeurs
  // nutritionnelles modifiés), puisqu'ils possèdent "name" mais pas
  // "id" et étaient donc à tort considérés comme invalides.
  const keyField = storeName === "kv" ? "key" : (storeName === "ingredients" || storeName === "ingredientOverrides") ? "name" : "id";
  return typeof item[keyField] === "string" && item[keyField].trim().length > 0;
}

// Ramène toute valeur numérique négative ou invalide à null plutôt que
// de la conserver telle quelle — une quantité, un temps de préparation
// ou un seuil négatif n'a pas de sens et pourrait fausser des calculs
// ailleurs dans l'application (listes de courses, statistiques...).
function sanitizeNonNegativeNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) && n >= 0 ? n : null;
}

// Nettoie un enregistrement individuel selon les champs numériques et
// photo connus pour son entrepôt — filtre les valeurs dangereuses ou
// incohérentes sans rejeter l'enregistrement entier pour autant (un
// champ isolé invalide ne doit pas faire perdre le reste d'une
// recette par ailleurs valide).
function sanitizeBackupItem(item, storeName, report) {
  const cleaned = { ...item };
  if ("photo" in cleaned && cleaned.photo != null && !isValidPhotoField(cleaned.photo)) {
    cleaned.photo = null;
    report.photosRemoved += 1;
  }
  if (storeName === "recipes") {
    // Un nom absent ou non textuel peut faire planter le tri de la
    // liste des recettes (localeCompare exige une vraie chaîne) —
    // remplacé par une chaîne vide plutôt que de rejeter toute la
    // recette pour un seul champ corrompu.
    if (typeof cleaned.name !== "string" || !cleaned.name.trim()) {
      cleaned.name = "";
      report.structuralFixes += 1;
    }
    // Une note hors de l'intervalle 0-5 peut faire mal s'afficher le
    // widget d'étoiles (boucle sur 1..5 comparée à la valeur stockée).
    if ("personalRating" in cleaned && cleaned.personalRating != null) {
      const n = Number(cleaned.personalRating);
      const clamped = Number.isFinite(n) ? Math.max(0, Math.min(5, Math.round(n))) : 0;
      if (clamped !== cleaned.personalRating) report.structuralFixes += 1;
      cleaned.personalRating = clamped;
    }
    if (cleaned.category && !CATEGORY_OPTIONS.includes(cleaned.category)) {
      cleaned.category = "Autre";
      report.structuralFixes += 1;
    }
    if (cleaned.difficulty && !DIFFICULTY_OPTIONS.includes(cleaned.difficulty)) {
      cleaned.difficulty = null;
      report.structuralFixes += 1;
    }
    ["prepTime", "cookTime"].forEach((field) => {
      if (field in cleaned && cleaned[field] != null) {
        const sanitized = sanitizeNonNegativeNumber(cleaned[field]);
        if (sanitized !== cleaned[field]) report.numbersFixed += 1;
        cleaned[field] = sanitized;
      }
    });
    if ("defaultPersons" in cleaned) {
      const sanitized = sanitizeNonNegativeNumber(cleaned.defaultPersons) || 4;
      if (sanitized !== cleaned.defaultPersons) report.numbersFixed += 1;
      cleaned.defaultPersons = sanitized;
    }
    if ("timesCooked" in cleaned) cleaned.timesCooked = sanitizeNonNegativeNumber(cleaned.timesCooked) || 0;
    if (Array.isArray(cleaned.ingredients)) {
      const beforeCount = cleaned.ingredients.length;
      cleaned.ingredients = cleaned.ingredients
        // Un ingrédient qui n'est même pas un objet ne peut pas être
        // réparé — retiré plutôt que conservé tel quel, ce qui
        // provoquerait des erreurs partout où le code s'attend à un
        // vrai objet ingrédient (affichage, calculs, export...).
        .filter((i) => i && typeof i === "object" && !Array.isArray(i))
        .map((i) => {
          const fixedName = typeof i.name === "string" ? i.name : "";
          if (fixedName !== i.name) report.structuralFixes += 1;
          const fixedUnit = i.unit && !UNIT_OPTIONS.includes(i.unit) ? "pièce" : i.unit;
          if (fixedUnit !== i.unit) report.structuralFixes += 1;
          const sanitized = i.quantity != null ? sanitizeNonNegativeNumber(i.quantity) : i.quantity;
          if (sanitized !== i.quantity) report.numbersFixed += 1;
          return { ...i, name: fixedName, unit: fixedUnit, quantity: sanitized };
        });
      if (cleaned.ingredients.length !== beforeCount) report.structuralFixes += 1;
    } else if ("ingredients" in cleaned) {
      cleaned.ingredients = [];
      report.structuralFixes += 1;
    }
    if (Array.isArray(cleaned.cookLog)) {
      const beforeCount = cleaned.cookLog.length;
      cleaned.cookLog = cleaned.cookLog
        .filter((entry) => entry && typeof entry === "object" && !Array.isArray(entry))
        .map((entry) => {
          if ("photo" in entry && entry.photo != null && !isValidPhotoField(entry.photo)) {
            report.photosRemoved += 1;
            return { ...entry, photo: null };
          }
          return entry;
        });
      if (cleaned.cookLog.length !== beforeCount) report.structuralFixes += 1;
    } else if ("cookLog" in cleaned) {
      cleaned.cookLog = [];
      report.structuralFixes += 1;
    }
  }
  if (storeName === "shopping" || storeName === "pantry") {
    ["quantity", "threshold"].forEach((field) => {
      if (field in cleaned && cleaned[field] != null) {
        const sanitized = sanitizeNonNegativeNumber(cleaned[field]);
        if (sanitized !== cleaned[field]) report.numbersFixed += 1;
        cleaned[field] = sanitized;
      }
    });
  }
  return cleaned;
}

async function parseBackupFile(file) {
  if (file.size > MAX_BACKUP_FILE_SIZE) {
    throw new Error("file_too_large");
  }
  const text = await file.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    throw new Error("invalid");
  }
  if (!data || typeof data !== "object" || Array.isArray(data) || !BACKUP_STORES.some((s) => Array.isArray(data[s]))) {
    throw new Error("invalid");
  }
  // Nettoie chaque entrepôt : ne garde que les enregistrements qui sont
  // de vrais objets avec un identifiant valide, et assainit leurs
  // champs numériques/photo — un enregistrement individuellement
  // corrompu est simplement ignoré plutôt que de faire échouer tout
  // l'import. Le rapport retourné permet d'informer l'utilisateur de ce
  // qui a été filtré ou corrigé, plutôt que de le faire silencieusement.
  const report = { validCount: 0, ignoredCount: 0, photosRemoved: 0, numbersFixed: 0, structuralFixes: 0 };
  const cleanedData = { ...data };
  BACKUP_STORES.forEach((storeName) => {
    if (!Array.isArray(data[storeName])) return;
    const valid = [];
    data[storeName].forEach((item) => {
      if (item && typeof item === "object" && !Array.isArray(item) && hasValidId(item, storeName)) {
        valid.push(sanitizeBackupItem(item, storeName, report));
      } else {
        report.ignoredCount += 1;
      }
    });
    report.validCount += valid.length;
    cleanedData[storeName] = valid;
  });
  return { data: cleanedData, report };
}
function buildBackupPreviewText(data, report) {
  const count = (storeName) => (Array.isArray(data[storeName]) ? data[storeName].length : 0);
  const dateLabel = data.exportedAt ? localeDateTimeStr(data.exportedAt) + "\n" : "";
  let text = t("backup_preview_text", {
    date: dateLabel,
    recipes: String(count("recipes")),
    ingredients: String(count("ingredients")),
    menus: String(count("menus")),
    shopping: String(count("shopping")),
  });
  // N'affiche le rapport de validation que s'il y a effectivement
  // quelque chose à signaler — inutile d'alourdir l'aperçu d'une
  // sauvegarde parfaitement saine avec des lignes à "0".
  if (report) {
    if (report.ignoredCount > 0) text += t("backup_ignored_items", { count: String(report.ignoredCount) });
    if (report.photosRemoved > 0) text += t("backup_photos_removed", { count: String(report.photosRemoved) });
    if (report.numbersFixed > 0) text += t("backup_numbers_fixed", { count: String(report.numbersFixed) });
    if (report.structuralFixes > 0) text += t("backup_structural_fixes", { count: String(report.structuralFixes) });
  }
  return text;
}
async function importAllData(data, mode) {
  const db = await openDB();
  // Une seule transaction couvrant tous les entrepôts à la fois : soit
  // l'ensemble des opérations (vidage puis réécriture) réussit
  // entièrement, soit IndexedDB annule automatiquement tout ce qui a
  // déjà été fait dans cette même transaction en cas d'erreur — plutôt
  // que l'ancienne approche (une mini-transaction séparée par entrepôt
  // et par élément), où une panne en plein milieu pouvait laisser
  // certains entrepôts vidés sans être repeuplés, ou partiellement
  // réécrits avec un mélange d'anciennes et de nouvelles données.
  await new Promise((resolve, reject) => {
    const tx = db.transaction(BACKUP_STORES, "readwrite");
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error("transaction_error"));
    tx.onabort = () => reject(tx.error || new Error("transaction_aborted"));
    try {
      BACKUP_STORES.forEach((storeName) => {
        const store = tx.objectStore(storeName);
        if (mode === "replace") store.clear();
        const items = Array.isArray(data[storeName]) ? data[storeName] : [];
        items.forEach((item) => store.put(item));
      });
    } catch (e) {
      tx.abort();
    }
  });
  state.recipes = await storeAll("recipes");
  state.shopping = await storeAll("shopping");
  state.pantry = await storeAll("pantry");
  // Les réservations sont désormais incluses dans les sauvegardes (via
  // le store kv, restauré comme les autres ci-dessus) — on les recharge
  // donc depuis ce qui vient d'être restauré, plutôt que de toujours
  // les remettre à zéro comme avant leur inclusion dans les sauvegardes.
  await loadPantryClaims();
  await ensureIngredientListLoaded();
  await loadIngredientOverrides();
}

async function renderDiagnostic() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<button type="button" class="btn btn-outline" id="diag-back" style="margin-bottom:16px;">← ${escapeHtml(t("cooking_close"))}</button>`));
  wrap.querySelector("#diag-back").addEventListener("click", () => { state.screen = "backup"; render(); });

  wrap.appendChild(el(`<h2>${escapeHtml(t("diagnostic_title"))}</h2>`));
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;line-height:1.5;">${escapeHtml(t("diagnostic_intro"))}</p>`));

  const rowsHolder = el(`<div class="card" style="padding:4px 16px;"></div>`);
  wrap.appendChild(rowsHolder);

  function addRow(label, value) {
    rowsHolder.appendChild(el(`<div style="display:flex;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid var(--border);font-size:13px;">
      <span style="color:var(--text-muted);">${escapeHtml(label)}</span>
      <span style="text-align:right;font-weight:500;word-break:break-word;">${escapeHtml(value)}</span>
    </div>`));
  }

  // Version de l'app et du cache actuellement servi (ce dernier lu
  // directement depuis les caches réels du navigateur, plutôt que
  // supposé identique à APP_VERSION — utile si les deux venaient un
  // jour à diverger).
  let cacheVersionLabel = String(APP_VERSION);
  try {
    const cacheKeys = await caches.keys();
    const recipeCache = cacheKeys.find((k) => k.startsWith("mes-recettes-cache-"));
    if (recipeCache) cacheVersionLabel = recipeCache.replace("mes-recettes-cache-", "");
  } catch (e) { /* API caches indisponible, on garde la valeur par défaut */ }
  addRow(t("diagnostic_app_version"), `v${APP_VERSION}`);
  addRow(t("diagnostic_cache_version"), cacheVersionLabel);

  // Navigateur et système : extraction simple depuis userAgent, sans
  // prétendre à une détection exhaustive — suffisant pour un
  // diagnostic technique de base.
  const ua = navigator.userAgent || "";
  const browserMatch = ua.match(/(Chrome|Firefox|Safari|Edg|Samsung)\/?[\d.]*/);
  addRow(t("diagnostic_browser"), browserMatch ? browserMatch[0] : ua.slice(0, 60));
  const osMatch = ua.match(/(Android [\d.]+|iPhone OS [\d_]+|Windows NT [\d.]+|Mac OS X [\d_]+|Linux)/);
  addRow(t("diagnostic_os"), osMatch ? osMatch[0].replace(/_/g, ".") : "?");

  const isStandalone = window.matchMedia && window.matchMedia("(display-mode: standalone)").matches;
  addRow(t("diagnostic_install_mode"), isStandalone ? t("diagnostic_install_standalone") : t("diagnostic_install_browser"));

  // Stockage persistant : évite que le système ne purge les données en
  // cas de manque d'espace — utile de savoir si ce n'est pas le cas.
  if (navigator.storage && navigator.storage.persisted) {
    try {
      const persisted = await navigator.storage.persisted();
      addRow(t("diagnostic_storage_persistent"), persisted ? t("diagnostic_storage_granted") : t("diagnostic_storage_not_granted"));
    } catch (e) {
      addRow(t("diagnostic_storage_persistent"), t("diagnostic_storage_unsupported"));
    }
  } else {
    addRow(t("diagnostic_storage_persistent"), t("diagnostic_storage_unsupported"));
  }
  if (navigator.storage && navigator.storage.estimate) {
    try {
      const estimate = await navigator.storage.estimate();
      const usedMb = estimate.usage != null ? (estimate.usage / (1024 * 1024)).toFixed(1) : "?";
      addRow(t("diagnostic_storage_used"), `${usedMb} Mo`);
    } catch (e) { /* estimation indisponible, on n'affiche simplement pas cette ligne */ }
  }

  const lastBackupAt = localStorage.getItem("lastBackupAt");
  addRow(t("diagnostic_last_backup"), lastBackupAt ? localeDateTimeStr(lastBackupAt) : t("diagnostic_never"));

  const lastImportService = localStorage.getItem("lastImportService");
  addRow(t("diagnostic_last_import_service"), lastImportService || t("diagnostic_none"));
  const lastImportError = localStorage.getItem("lastImportError");
  addRow(t("diagnostic_last_import_error"), lastImportError || t("diagnostic_none"));
  const lastShareError = localStorage.getItem("lastShareError");
  addRow(t("diagnostic_last_share_error"), lastShareError || t("diagnostic_none"));
  const lastWorkerError = localStorage.getItem("lastWorkerError");
  addRow(t("diagnostic_last_worker_error"), lastWorkerError || t("diagnostic_none"));

  addRow(t("diagnostic_connection"), navigator.onLine ? t("diagnostic_online") : t("diagnostic_offline"));
  addRow(t("diagnostic_qr_native"), ("BarcodeDetector" in window) ? t("diagnostic_available") : t("diagnostic_unavailable"));

  const copyBtn = el(`<button type="button" class="btn btn-primary" style="margin-top:16px;">${escapeHtml(t("diagnostic_copy_button"))}</button>`);
  copyBtn.addEventListener("click", async () => {
    const lines = Array.from(rowsHolder.children).map((row) => {
      const spans = row.querySelectorAll("span");
      return `${spans[0].textContent} : ${spans[1].textContent}`;
    });
    const text = lines.join("\n");
    try {
      await navigator.clipboard.writeText(text);
      copyBtn.textContent = t("diagnostic_copied");
      setTimeout(() => { copyBtn.textContent = t("diagnostic_copy_button"); }, 2000);
    } catch (e) {
      await customAlert(text);
    }
  });
  wrap.appendChild(copyBtn);

  return wrap;
}

function renderBackup() {
  const wrap = el(`<div></div>`);

  const canShareFiles = !!(navigator.canShare && navigator.canShare({ files: [new File([""], "test.txt", { type: "text/plain" })] }));

  const exportSection = el(`<div class="section">
    <div class="section-label">${t("backup_export_title")}</div>
    <div class="card" style="padding:16px;">
      <p class="prose" style="margin:0 0 14px;font-size:14px;">${escapeHtml(t("backup_export_text"))}</p>
      <button class="btn btn-primary" id="export-btn" style="margin-bottom:10px;">${t("backup_export_button")}</button>
      ${canShareFiles ? `<button class="btn btn-secondary" id="share-btn" disabled>${t("backup_share_preparing")}</button>
      <p style="font-size:12px;color:var(--text-muted);margin:8px 0 0;">${escapeHtml(t("backup_share_hint"))}</p>` : ""}
    </div>
  </div>`);
  exportSection.querySelector("#export-btn").addEventListener("click", async () => {
    await exportAllData();
    await customAlert(t("backup_export_success"));
  });
  if (canShareFiles) {
    const shareBtn = exportSection.querySelector("#share-btn");
    // Le fichier est entièrement préparé et résolu AVANT que le bouton
    // ne devienne cliquable — pas seulement "lancé en tâche de fond" —
    // pour garantir qu'aucun await ne se produise entre le clic de
    // l'utilisateur et l'appel à navigator.share() lui-même, condition
    // nécessaire pour que le navigateur reconnaisse encore le geste
    // comme "actif" à ce moment précis.
    let readyFile = null;
    buildBackupFile().then((file) => {
      readyFile = file;
      shareBtn.disabled = false;
      shareBtn.textContent = t("backup_share_button");
    });
    shareBtn.addEventListener("click", () => {
      if (!readyFile) return; // ne devrait pas arriver, bouton désactivé jusque-là
      shareBackupData(readyFile).then(async (result) => {
        if (result.ok && !result.cancelled) {
          // Réussite confirmée (pas juste annulée) : efface l'ancienne
          // erreur, sans quoi elle restait affichée dans le diagnostic
          // même après un partage qui fonctionne désormais correctement.
          try { localStorage.removeItem("lastShareError"); } catch (e) { /* sans conséquence */ }
        }
        if (!result.ok) {
          // Le partage a échoué (pas simplement annulé par l'utilisateur,
          // ce cas renvoie cancelled:true sans passer ici) : le fichier
          // est tout de même mis en sécurité par téléchargement classique,
          // mais l'utilisateur doit être informé que ce n'est PAS ce qu'il
          // a demandé — un message explicite évite de lui laisser croire
          // à tort que le partage vers le cloud a réussi. Le détail
          // technique est conservé pour le diagnostic (voir Sauvegarde →
          // Diagnostic) : les tentatives précédentes de corriger ce
          // problème sans connaître l'erreur exacte n'ont pas abouti.
          if (result.error) {
            try { localStorage.setItem("lastShareError", `${new Date().toISOString()} — ${result.error}`.slice(0, 300)); } catch (e) { /* sans conséquence */ }
          }
          await exportAllData();
          const detail = result.error ? `\n\n(${result.error})` : "";
          await customAlert(t("backup_share_fallback_notice") + detail);
        }
      });
    });
  }
  wrap.appendChild(exportSection);

  const androidTip = el(`<div style="background:var(--accent-light);color:var(--accent);border-radius:12px;padding:12px 14px;margin-bottom:16px;font-size:13px;">
    <strong>${escapeHtml(t("backup_android_tip_title"))}</strong>
    <p style="margin:6px 0 0;line-height:1.5;">${escapeHtml(t("backup_android_tip_text"))}</p>
  </div>`);
  wrap.appendChild(androidTip);

  const importSection = el(`<div class="section">    <div class="section-label">${t("backup_import_title")}</div>
    <div class="card" style="padding:16px;">
      <p class="prose" style="margin:0 0 14px;font-size:14px;">${escapeHtml(t("backup_import_text"))}</p>
      <div class="field">
        <label for="import-mode">${t("backup_import_mode_title")}</label>
        <select id="import-mode">
          <option value="merge">${t("backup_import_mode_merge")}</option>
          <option value="replace">${t("backup_import_mode_replace")}</option>
        </select>
      </div>
      <div class="field">
        <label for="import-file">${t("backup_import_button")}</label>
        <input type="file" accept="application/json,text/plain,.json,.txt" id="import-file">
      </div>
    </div>
  </div>`);
  importSection.querySelector("#import-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const mode = importSection.querySelector("#import-mode").value;

    let data, report;
    try {
      ({ data, report } = await parseBackupFile(file));
    } catch (err) {
      await customAlert(t("backup_import_error"));
      e.target.value = "";
      return;
    }

    if (!await customConfirm(buildBackupPreviewText(data, report))) {
      e.target.value = "";
      return;
    }

    let didSafetyBackup = false;
    if (mode === "replace") {
      if (!await customConfirm(t("backup_import_confirm_replace"))) {
        e.target.value = "";
        return;
      }
      // Sauvegarde automatique des données actuelles avant de les
      // remplacer — au cas où le mauvais fichier aurait été
      // sélectionné par erreur, rien n'est perdu définitivement. On
      // vérifie tous les entrepôts (pas seulement les recettes) : un
      // utilisateur sans aucune recette peut très bien avoir une liste
      // de courses, un garde-manger ou des menus à protéger.
      const storeContents = await Promise.all(BACKUP_STORES.map((s) => storeAll(s)));
      const hasAnyData = storeContents.some((items) => items && items.length > 0);
      if (hasAnyData) {
        await exportAllData();
        didSafetyBackup = true;
      }
    }
    try {
      await importAllData(data, mode);
      await customAlert(t(didSafetyBackup ? "backup_import_success_with_safety" : "backup_import_success"));
      state.screen = "home";
      render();
    } catch (err) {
      await customAlert(t("backup_import_error"));
    }
  });
  wrap.appendChild(importSection);

  const diagLink = el(`<p style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px;">v${APP_VERSION} · <a href="#" id="open-diagnostic" style="color:var(--accent);">${escapeHtml(t("nav_diagnostic"))}</a></p>`);
  diagLink.querySelector("#open-diagnostic").addEventListener("click", (e) => {
    e.preventDefault();
    state.screen = "diagnostic";
    render();
  });
  wrap.appendChild(diagLink);

  return wrap;
}

/* ======================================================================
   COMPARER DEUX RECETTES
   ====================================================================== */
function renderCompare() {
  const wrap = el(`<div></div>`);
  const sortedRecipes = state.recipes.slice().sort((a, b) => a.name.localeCompare(b.name, "fr"));

  const pickerRow = el(`<div class="field-row"></div>`);
  const fieldA = el(`<div class="field"><label for="compare-a">${t("compare_recipe_a")}</label><select id="compare-a"></select></div>`);
  const fieldB = el(`<div class="field"><label for="compare-b">${t("compare_recipe_b")}</label><select id="compare-b"></select></div>`);
  [fieldA, fieldB].forEach((field) => {
    const select = field.querySelector("select");
    select.appendChild(el(`<option value="">—</option>`));
    sortedRecipes.forEach((r) => select.appendChild(el(`<option value="${r.id}">${escapeHtml(r.name)}</option>`)));
  });
  pickerRow.appendChild(fieldA);
  pickerRow.appendChild(fieldB);
  wrap.appendChild(pickerRow);

  const resultHolder = el(`<div id="compare-result"></div>`);
  wrap.appendChild(resultHolder);

  function refresh() {
    const idA = fieldA.querySelector("select").value;
    const idB = fieldB.querySelector("select").value;
    resultHolder.innerHTML = "";
    const recipeA = state.recipes.find((r) => r.id === idA);
    const recipeB = state.recipes.find((r) => r.id === idB);
    if (!recipeA || !recipeB) {
      resultHolder.appendChild(el(`<div class="empty-state"><div class="emoji">⚖️</div><p>${escapeHtml(t("compare_select_both"))}</p></div>`));
      return;
    }

    const headers = el(`<div class="compare-headers">
      <div class="spacer"></div>
      <div class="header-values">
        <div><div class="name">${escapeHtml(recipeA.name)}</div></div>
        <div><div class="name">${escapeHtml(recipeB.name)}</div></div>
      </div>
    </div>`);
    const headerCols = headers.querySelectorAll(".header-values > div");
    const viewBtnA = el(`<button class="view-btn">${t("compare_view_recipe")}</button>`);
    viewBtnA.addEventListener("click", () => {
      state.currentRecipeId = recipeA.id;
      state.viewPersons = recipeA.defaultPersons || 4;
      state.screen = "recipe";
      render();
    });
    const viewBtnB = el(`<button class="view-btn">${t("compare_view_recipe")}</button>`);
    viewBtnB.addEventListener("click", () => {
      state.currentRecipeId = recipeB.id;
      state.viewPersons = recipeB.defaultPersons || 4;
      state.screen = "recipe";
      render();
    });
    headerCols[0].appendChild(viewBtnA);
    headerCols[1].appendChild(viewBtnB);
    resultHolder.appendChild(headers);

    const statsCard = el(`<div class="card" style="padding:2px 14px;margin-bottom:16px;"></div>`);
    const rows = [
      [t("compare_category"), translateCategory(recipeA.category), translateCategory(recipeB.category)],
      [t("compare_difficulty"), translateDifficulty(recipeA.difficulty) || "—", translateDifficulty(recipeB.difficulty) || "—"],
      [t("compare_prep"), recipeA.prepTime ? recipeA.prepTime + " " + t("recipe_min") : "—", recipeB.prepTime ? recipeB.prepTime + " " + t("recipe_min") : "—"],
      [t("compare_cook"), recipeA.cookTime ? recipeA.cookTime + " " + t("recipe_min") : "—", recipeB.cookTime ? recipeB.cookTime + " " + t("recipe_min") : "—"],
      [t("compare_persons"), recipeA.defaultPersons, recipeB.defaultPersons],
      [t("recipe_allergens"), (recipeA.allergens && recipeA.allergens.length) ? recipeA.allergens.map(translateAllergen).join(", ") : "—", (recipeB.allergens && recipeB.allergens.length) ? recipeB.allergens.map(translateAllergen).join(", ") : "—"],
    ];
    rows.forEach(([label, a, b]) => {
      statsCard.appendChild(el(`<div class="compare-row">
        <div class="compare-label">${escapeHtml(label)}</div>
        <div class="compare-values"><div>${escapeHtml(String(a))}</div><div>${escapeHtml(String(b))}</div></div>
      </div>`));
    });
    resultHolder.appendChild(statsCard);

    const namesA = new Set((recipeA.ingredients || []).map((i) => normalize(i.name)));
    const namesB = new Set((recipeB.ingredients || []).map((i) => normalize(i.name)));
    const byNormA = {};
    (recipeA.ingredients || []).forEach((i) => (byNormA[normalize(i.name)] = i.name));
    const byNormB = {};
    (recipeB.ingredients || []).forEach((i) => (byNormB[normalize(i.name)] = i.name));

    const common = [...namesA].filter((n) => namesB.has(n)).map((n) => byNormA[n]);
    const onlyA = [...namesA].filter((n) => !namesB.has(n)).map((n) => byNormA[n]);
    const onlyB = [...namesB].filter((n) => !namesA.has(n)).map((n) => byNormB[n]);

    function ingredientListBlock(title, names) {
      const block = el(`<div class="section"><div class="section-label">${escapeHtml(title)}</div></div>`);
      const card = el(`<div class="card compare-ing-list" style="padding:12px 16px;"></div>`);
      card.textContent = names.length ? names.map(translateIngredientName).join(", ") : t("compare_none");
      block.appendChild(card);
      resultHolder.appendChild(block);
    }
    ingredientListBlock(t("compare_common_ingredients"), common);

    const onlyBlock = el(`<div class="section"><div class="section-label">${escapeHtml(t("compare_only_in"))}</div></div>`);
    const onlyCard = el(`<div class="card compare-only-columns"></div>`);
    const colA = el(`<div><div class="col-title">${escapeHtml(recipeA.name)}</div></div>`);
    const colB = el(`<div><div class="col-title">${escapeHtml(recipeB.name)}</div></div>`);
    if (onlyA.length) {
      onlyA.forEach((n) => colA.appendChild(el(`<div>${escapeHtml(translateIngredientName(n))}</div>`)));
    } else {
      colA.appendChild(el(`<div style="color:var(--text-muted);">${escapeHtml(t("compare_none"))}</div>`));
    }
    if (onlyB.length) {
      onlyB.forEach((n) => colB.appendChild(el(`<div>${escapeHtml(translateIngredientName(n))}</div>`)));
    } else {
      colB.appendChild(el(`<div style="color:var(--text-muted);">${escapeHtml(t("compare_none"))}</div>`));
    }
    onlyCard.appendChild(colA);
    onlyCard.appendChild(colB);
    onlyBlock.appendChild(onlyCard);
    resultHolder.appendChild(onlyBlock);
  }

  fieldA.querySelector("select").addEventListener("change", refresh);
  fieldB.querySelector("select").addEventListener("change", refresh);
  refresh();

  return wrap;
}

/* ======================================================================
   SÉLECTEUR DE RECETTE (partagé : menus et planning)
   ====================================================================== */
function openRecipePickerModal(onPick) {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("planning_pick_recipe_title")}</h2>
    <div class="search-bar"><span>🔍</span><input type="search" placeholder="${t("search_placeholder")}" aria-label="${escapeHtml(t("search_placeholder"))}"></div>
    <div id="picker-list" style="max-height:50vh;overflow-y:auto;"></div>
    <div class="modal-actions"><button type="button" class="btn btn-outline" id="picker-cancel">${t("form_cancel")}</button></div>
  </div>`);
  const listHolder = sheet.querySelector("#picker-list");
  function fillList(query) {
    listHolder.innerHTML = "";
    const key = normalize(query || "");
    const list = state.recipes
      .filter((r) => !key || normalize(r.name).includes(key))
      .sort((a, b) => a.name.localeCompare(b.name, "fr"));
    if (!list.length) {
      listHolder.appendChild(el(`<div class="empty-state" style="padding:20px 0;"><p>${escapeHtml(t("no_recipes_found"))}</p></div>`));
      return;
    }
    list.forEach((r) => {
      const row = el(`<button class="recipe-row" style="width:100%;margin-bottom:8px;">
        <div class="recipe-thumb">${r.photo ? `<img src="${r.photo}" alt="">` : "🍽️"}</div>
        <div class="recipe-info"><div class="recipe-name">${escapeHtml(r.name)}</div></div>
      </button>`);
      row.addEventListener("click", () => {
        overlay.remove();
        onPick(r);
      });
      listHolder.appendChild(row);
    });
  }
  sheet.querySelector("input").addEventListener("input", (e) => fillList(e.target.value));
  fillList("");
  sheet.querySelector("#picker-cancel").addEventListener("click", () => overlay.remove());
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  initModalA11y(overlay, sheet);
}

/* ======================================================================
   MENUS
   ====================================================================== */
function openMenuDetail(menuId) {
  state.currentMenuId = menuId;
  state.screen = "menu";
  render();
}

function renderMenuList() {
  const wrap = el(`<div></div>`);
  if (!state.menus.length) {
    wrap.appendChild(el(`<div class="empty-state"><div class="emoji">📋</div><p>${escapeHtml(t("menu_no_menus"))}</p></div>`));
    return wrap;
  }
  const list = el(`<div class="recipe-list"></div>`);
  state.menus
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name, "fr"))
    .forEach((menu) => {
      const row = el(`<button class="card recipe-row">
        <div class="recipe-thumb">📋</div>
        <div class="recipe-info"><div class="recipe-name">${escapeHtml(menu.name)}</div><div class="recipe-meta">${(menu.items || []).length}</div></div>
      </button>`);
      row.addEventListener("click", () => openMenuDetail(menu.id));
      list.appendChild(row);
    });
  wrap.appendChild(list);
  return wrap;
}

function renderMenuDetail() {
  const wrap = el(`<div></div>`);
  const existing = state.currentMenuId ? state.menus.find((m) => m.id === state.currentMenuId) : null;
  const items = existing ? existing.items.map((i) => ({ ...i })) : [];

  wrap.appendChild(el(`<div class="field">
    <label for="menu-name">${t("menu_name_label")}</label>
    <input type="text" id="menu-name" placeholder="${t("menu_name_placeholder")}" value="${escapeHtml(existing ? existing.name : "")}">
  </div>`));

  wrap.appendChild(el(`<div class="section-label">${t("menu_recipes_label")}</div>`));
  const itemsHolder = el(`<div id="menu-items-holder"></div>`);
  wrap.appendChild(itemsHolder);

  function fillItems() {
    itemsHolder.innerHTML = "";
    if (!items.length) {
      itemsHolder.appendChild(el(`<div class="empty-state" style="padding:16px 0;"><p>${escapeHtml(t("menu_no_recipes"))}</p></div>`));
      return;
    }
    const card = el(`<div class="card" style="padding:2px 16px;margin-bottom:16px;"></div>`);
    items.forEach((item, idx) => {
      const recipe = state.recipes.find((r) => r.id === item.recipeId);
      const row = el(`<div class="ingredient-item">
        <span>${escapeHtml(recipe ? recipe.name : "?")}</span>
        <span style="display:flex;align-items:center;gap:8px;">
          <input type="number" min="1" value="${item.persons}" style="width:50px;text-align:center;border:1px solid var(--border);border-radius:8px;padding:6px;">
          <button aria-label="${t("common_delete")}" style="width:32px;height:32px;border:none;border-radius:8px;background:var(--danger-light);color:var(--danger);">🗑</button>
        </span>
      </div>`);
      row.querySelector("input").addEventListener("input", (e) => { item.persons = Math.max(1, Number(e.target.value) || 1); });
      row.querySelector("button").addEventListener("click", () => { items.splice(idx, 1); fillItems(); });
      card.appendChild(row);
    });
    itemsHolder.appendChild(card);
  }
  fillItems();

  const addBtn = el(`<button type="button" class="btn btn-secondary btn-sm" style="margin-bottom:20px;">${t("menu_add_recipe")}</button>`);
  addBtn.addEventListener("click", () => {
    openRecipePickerModal((recipe) => {
      items.push({ recipeId: recipe.id, persons: recipe.defaultPersons || 4 });
      fillItems();
    });
  });
  wrap.appendChild(addBtn);

  async function saveMenu() {
    const nameValue = wrap.querySelector("#menu-name").value.trim();
    if (!nameValue) { await customAlert(t("menu_error_name")); return null; }
    const menu = { id: existing ? existing.id : uid(), name: nameValue, items: items.slice() };
    await storePut("menus", menu);
    const idx = state.menus.findIndex((m) => m.id === menu.id);
    if (idx >= 0) state.menus[idx] = menu; else state.menus.push(menu);
    return menu;
  }

  const saveBtn = el(`<button class="btn btn-primary" style="margin-bottom:10px;">${t("form_save")}</button>`);
  saveBtn.addEventListener("click", async () => {
    const menu = await saveMenu();
    if (menu) { state.currentMenuId = menu.id; render(); }
  });
  wrap.appendChild(saveBtn);

  if (existing) {
    const shopBtn = el(`<button class="btn btn-secondary" style="margin-bottom:10px;">${t("menu_generate_shopping")}</button>`);
    shopBtn.addEventListener("click", async () => {
      for (const item of items) {
        const recipe = state.recipes.find((r) => r.id === item.recipeId);
        if (recipe) await addRecipeToShoppingSilent(recipe, item.persons);
      }
      state.screen = "shopping";
      render();
    });
    wrap.appendChild(shopBtn);

    const delBtn = el(`<button class="btn btn-danger">${t("common_delete")}</button>`);
    delBtn.addEventListener("click", async () => {
      if (await customConfirm(t("menu_delete_confirm"))) {
        await storeDelete("menus", existing.id);
        state.menus = state.menus.filter((m) => m.id !== existing.id);
        state.screen = "menus";
        render();
      }
    });
    wrap.appendChild(delBtn);
  }

  return wrap;
}

/* ======================================================================
   PLANNING DE LA SEMAINE + MODÈLES
   ====================================================================== */
async function saveWeeklyPlan() {
  await kvSet("weeklyPlan", state.weeklyPlan);
}

const PLAN_HISTORY_MAX = 26; // environ 6 mois, même limite que la version bureau

function planHasAnyAssignment(plan) {
  return WEEKDAYS.some((day) => MEAL_SLOTS.some((slot) => (plan[day] || {})[slot]));
}

// Archive automatiquement le planning actuel avant qu'il ne soit effacé
// ou remplacé (par un modèle), s'il contient au moins une recette
// assignée — pour ne jamais perdre une semaine sans laisser de trace,
// contrairement aux modèles qui doivent être enregistrés manuellement.
async function archiveCurrentPlanIfNotEmpty() {
  if (!planHasAnyAssignment(state.weeklyPlan)) return;
  const entry = { id: uid(), date: new Date().toISOString(), plan: JSON.parse(JSON.stringify(state.weeklyPlan)) };
  await storePut("planHistory", entry);
  state.planHistory.unshift(entry);
  if (state.planHistory.length > PLAN_HISTORY_MAX) {
    const toRemove = state.planHistory.slice(PLAN_HISTORY_MAX);
    state.planHistory = state.planHistory.slice(0, PLAN_HISTORY_MAX);
    for (const old of toRemove) await storeDelete("planHistory", old.id);
  }
}

function renderPlanning() {
  const wrap = el(`<div></div>`);
  const daysHolder = el(`<div id="days-holder"></div>`);
  wrap.appendChild(daysHolder);

  function fillDays() {
    daysHolder.innerHTML = "";
    WEEKDAYS.forEach((day) => {
      daysHolder.appendChild(el(`<div class="section-label">${escapeHtml(translateWeekday(day))}</div>`));
      const card = el(`<div class="card" style="padding:2px 16px;margin-bottom:16px;"></div>`);
      MEAL_SLOTS.forEach((slot) => {
        const assigned = (state.weeklyPlan[day] || {})[slot];
        const recipe = assigned ? state.recipes.find((r) => r.id === assigned.recipeId) : null;
        const row = el(`<div class="ingredient-item"></div>`);
        if (recipe) {
          row.innerHTML = `<span>${escapeHtml(translateSlot(slot))} — <strong>${escapeHtml(recipe.name)}</strong></span>`;
          const clearBtn = el(`<button aria-label="${t("common_delete")}" style="width:28px;height:28px;border:none;border-radius:8px;background:var(--danger-light);color:var(--danger);">✕</button>`);
          clearBtn.addEventListener("click", async () => {
            delete state.weeklyPlan[day][slot];
            await saveWeeklyPlan();
            fillDays();
          });
          row.appendChild(clearBtn);
        } else {
          row.innerHTML = `<span style="color:var(--text-muted);">${escapeHtml(translateSlot(slot))}</span>`;
          const addBtn = el(`<button style="border:none;background:none;color:var(--primary);font-weight:600;font-size:13px;">${t("planning_empty_slot")}</button>`);
          addBtn.addEventListener("click", () => {
            openRecipePickerModal(async (recipe) => {
              if (!state.weeklyPlan[day]) state.weeklyPlan[day] = {};
              state.weeklyPlan[day][slot] = { recipeId: recipe.id, persons: recipe.defaultPersons || 4 };
              await saveWeeklyPlan();
              fillDays();
            });
          });
          row.appendChild(addBtn);
        }
        card.appendChild(row);
      });
      daysHolder.appendChild(card);
    });
  }
  fillDays();

  const historyBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("planning_view_history")}${state.planHistory.length ? ` (${state.planHistory.length})` : ""}</button>`);
  historyBtn.addEventListener("click", () => { state.screen = "planningHistory"; render(); });
  wrap.appendChild(historyBtn);

  const genBtn = el(`<button class="btn btn-primary" style="margin-bottom:10px;">${t("planning_generate_shopping")}</button>`);
  genBtn.addEventListener("click", async () => {
    let any = false;
    for (const day of WEEKDAYS) {
      for (const slot of MEAL_SLOTS) {
        const assigned = (state.weeklyPlan[day] || {})[slot];
        if (!assigned) continue;
        const recipe = state.recipes.find((r) => r.id === assigned.recipeId);
        if (recipe) { await addRecipeToShoppingSilent(recipe, assigned.persons); any = true; }
      }
    }
    if (any) { state.screen = "shopping"; render(); }
  });
  wrap.appendChild(genBtn);

  const saveTemplateBtn = el(`<button class="btn btn-secondary" style="margin-bottom:10px;">${t("planning_save_template")}</button>`);
  saveTemplateBtn.addEventListener("click", async () => {
    const name = await customPrompt(t("planning_save_template_prompt"));
    if (!name || !name.trim()) return;
    const template = { id: uid(), name: name.trim(), plan: JSON.parse(JSON.stringify(state.weeklyPlan)) };
    await storePut("planTemplates", template);
    state.planTemplates.push(template);
    render();
  });
  wrap.appendChild(saveTemplateBtn);

  const clearBtn = el(`<button class="btn btn-danger" style="margin-bottom:20px;">${t("planning_clear")}</button>`);
  clearBtn.addEventListener("click", async () => {
    if (await customConfirm(t("planning_clear_confirm"))) {
      await archiveCurrentPlanIfNotEmpty();
      state.weeklyPlan = {};
      await saveWeeklyPlan();
      fillDays();
    }
  });
  wrap.appendChild(clearBtn);

  wrap.appendChild(el(`<div class="section-label">${t("planning_templates_title")}</div>`));
  if (!state.planTemplates.length) {
    wrap.appendChild(el(`<div class="empty-state" style="padding:16px 0;"><p>${escapeHtml(t("planning_no_templates"))}</p></div>`));
  } else {
    const tCard = el(`<div class="card" style="padding:2px 16px;"></div>`);
    state.planTemplates.forEach((template) => {
      const row = el(`<div class="ingredient-item">
        <span>${escapeHtml(template.name)}</span>
        <span style="display:flex;gap:8px;">
          <button class="apply" style="border:none;border-radius:8px;background:var(--primary-light);color:var(--primary);padding:6px 12px;font-weight:600;font-size:13px;">${t("planning_apply_template")}</button>
          <button class="del" aria-label="${t("common_delete")}" style="width:32px;height:32px;border:none;border-radius:8px;background:var(--danger-light);color:var(--danger);">🗑</button>
        </span>
      </div>`);
      row.querySelector(".apply").addEventListener("click", async () => {
        if (!await customConfirm(t("planning_apply_template_confirm"))) return;
        await archiveCurrentPlanIfNotEmpty();
        state.weeklyPlan = JSON.parse(JSON.stringify(template.plan));
        await saveWeeklyPlan();
        render();
      });
      row.querySelector(".del").addEventListener("click", async () => {
        if (!await customConfirm(t("planning_delete_template_confirm"))) return;
        await storeDelete("planTemplates", template.id);
        state.planTemplates = state.planTemplates.filter((x) => x.id !== template.id);
        render();
      });
      tCard.appendChild(row);
    });
    wrap.appendChild(tCard);
  }

  return wrap;
}

/* ======================================================================
   HISTORIQUE DU PLANNING (archivage automatique)
   ====================================================================== */
function renderPlanningHistory() {
  const wrap = el(`<div></div>`);
  if (!state.planHistory.length) {
    wrap.appendChild(el(`<div class="empty-state"><div class="emoji">🕘</div><p>${escapeHtml(t("planning_history_empty"))}</p></div>`));
    return wrap;
  }
  state.planHistory.forEach((entry) => {
    const dateStr = localeDateStr(entry.date);
    const block = el(`<div class="section"><div class="section-label">${escapeHtml(t("planning_history_week_of", { date: dateStr }))}</div></div>`);
    const card = el(`<div class="card" style="padding:2px 16px;margin-bottom:8px;"></div>`);
    let anyRow = false;
    WEEKDAYS.forEach((day) => {
      MEAL_SLOTS.forEach((slot) => {
        const assigned = (entry.plan[day] || {})[slot];
        if (!assigned) return;
        const recipe = state.recipes.find((r) => r.id === assigned.recipeId);
        anyRow = true;
        card.appendChild(el(`<div class="ingredient-item"><span>${escapeHtml(translateWeekday(day))} · ${escapeHtml(translateSlot(slot))}</span><span class="ingredient-qty">${escapeHtml(recipe ? recipe.name : "?")}</span></div>`));
      });
    });
    if (!anyRow) {
      card.appendChild(el(`<div class="ingredient-item"><span style="color:var(--text-muted);">${escapeHtml(t("compare_none"))}</span></div>`));
    }
    block.appendChild(card);

    const actionsRow = el(`<div class="action-row" style="margin-bottom:20px;"></div>`);
    const reapplyBtn = el(`<button class="btn btn-secondary">${t("planning_history_reapply")}</button>`);
    reapplyBtn.addEventListener("click", async () => {
      if (!await customConfirm(t("planning_history_reapply_confirm"))) return;
      await archiveCurrentPlanIfNotEmpty();
      state.weeklyPlan = JSON.parse(JSON.stringify(entry.plan));
      await saveWeeklyPlan();
      state.screen = "planning";
      render();
    });
    const delBtn = el(`<button class="btn btn-danger">${t("common_delete")}</button>`);
    delBtn.addEventListener("click", async () => {
      if (!await customConfirm(t("planning_history_delete_confirm"))) return;
      await storeDelete("planHistory", entry.id);
      state.planHistory = state.planHistory.filter((x) => x.id !== entry.id);
      render();
    });
    actionsRow.appendChild(reapplyBtn);
    actionsRow.appendChild(delBtn);
    block.appendChild(actionsRow);

    wrap.appendChild(block);
  });
  return wrap;
}

/* ======================================================================
   IMPORT DE RECETTE DEPUIS UN LIEN
   Récupère la page via un service intermédiaire public (nécessaire pour
   contourner une restriction de sécurité du navigateur, CORS), puis
   cherche les données structurées "Recipe" (schema.org) que la plupart
   des grands sites de recettes intègrent déjà pour les moteurs de
   recherche. La reconnaissance des quantités reste approximative :
   l'utilisateur est toujours invité à vérifier avant d'enregistrer.
   ====================================================================== */
// Fractions unicode courantes (½, ⅔...) vers leur valeur décimale — les
// photos de recettes (HelloFresh notamment) les utilisent souvent au
// lieu d'un nombre classique, ce que l'analyse ne reconnaissait pas du
// tout jusqu'ici.
const UNICODE_FRACTIONS = { "½": 0.5, "⅓": 0.33, "⅔": 0.67, "¼": 0.25, "¾": 0.75, "⅕": 0.2, "⅖": 0.4, "⅗": 0.6, "⅘": 0.8, "⅙": 0.17, "⅚": 0.83, "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875 };
function normalizeUnicodeFractions(str) {
  return str.replace(/(\d+\s*)?([½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])/g, (match, whole, frac) => {
    const wholeNum = whole ? parseFloat(whole) : 0;
    return String(Math.round((wholeNum + UNICODE_FRACTIONS[frac]) * 100) / 100);
  });
}
function parseIngredientString(str) {
  let text = String(str || "").trim();
  text = normalizeUnicodeFractions(text);
  // "(s)" est un simple marqueur de pluriel optionnel sur certaines
  // fiches (HelloFresh notamment : "sachet(s)", "boîte(s)") — ne porte
  // aucune information utile et gênait la reconnaissance de l'unité.
  text = text.replace(/\(s\)/gi, "");

  // Repère d'abord les unités françaises composées de plusieurs mots
  // ("cuillère à café/soupe") : la reconnaissance générale ci-dessous
  // ne capture qu'un seul mot comme unité candidate, donc "cuillère"
  // seul y était reconnu, jamais l'expression complète — le reste
  // ("à café de gingembre") finissait alors inclus dans le nom de
  // l'ingrédient plutôt que dans son unité.
  const spoonMatch = text.match(/^([\d]+(?:[.,]\d+)?(?:\s*\/\s*\d+)?)\s*cuill[eè]res?\s+à\s+(caf[eé]|soupe)\s+(?:de\s+|d['’])?(.*)$/i);
  if (spoonMatch) {
    const [, qtyStr, spoonType, rest] = spoonMatch;
    let spoonQty;
    if (qtyStr.includes("/")) {
      const [num, den] = qtyStr.split("/").map((s) => parseFloat(s.trim().replace(",", ".")));
      spoonQty = den ? num / den : null;
    } else {
      spoonQty = parseFloat(qtyStr.replace(",", "."));
    }
    if (Number.isNaN(spoonQty)) spoonQty = null;
    const spoonUnit = /caf[eé]/i.test(spoonType) ? "c. à café" : "c. à soupe";
    return { name: rest.trim() || text, quantity: spoonQty, unit: spoonUnit };
  }

  const match = text.match(/^([\d]+(?:[.,]\d+)?(?:\s*\/\s*\d+)?)\s*([a-zA-Zéèàêûîôçñü]*)\.?\s*(.*)$/);
  if (!match || !match[1]) {
    // Aucun chiffre en tête : essaie l'ordre inversé "Nom Quantité
    // Unité" (ex. "Grenailles 500 g", "Thon au naturel 1 boîte") — un
    // format courant sur certains sites/kits repas (HelloFresh
    // notamment), où la quantité et l'unité arrivent à la fin plutôt
    // qu'au début.
    const reversedMatch = text.match(/^(.+?)\s+([\d]+(?:[.,]\d+)?(?:\s*\/\s*\d+)?)\s*([a-zA-Zéèàêûîôçñü]+)\.?\s*$/i);
    if (reversedMatch) {
      const [, namePart, qtyStr, unitWordRaw] = reversedMatch;
      const reversedResult = parseIngredientString(`${qtyStr} ${unitWordRaw} ${namePart}`);
      if (reversedResult.name) return reversedResult;
    }
    return { name: text, quantity: null, unit: "pièce" };
  }
  const [, qtyStr, unitWordRaw, rest] = match;
  let quantity;
  if (qtyStr.includes("/")) {
    const [num, den] = qtyStr.split("/").map((s) => parseFloat(s.trim().replace(",", ".")));
    quantity = den ? num / den : null;
  } else {
    quantity = parseFloat(qtyStr.replace(",", "."));
  }
  if (Number.isNaN(quantity)) quantity = null;

  const uwRaw = unitWordRaw.toLowerCase();
  const uw = uwRaw.replace(/s$/, "");
  let unit = null;
  let factor = 1;
  // "cs"/"cc" (abréviations HelloFresh) sont vérifiées sur le mot brut,
  // avant le retrait du "s" final ci-dessus qui transformerait sinon à
  // tort "cs" en "c" (perdu, jamais reconnu comme cuillère à soupe).
  if (uwRaw === "cs") unit = "c. à soupe";
  else if (uwRaw === "cc") unit = "c. à café";
  else if (uwRaw === "el") unit = "c. à soupe";
  else if (uwRaw === "tl") unit = "c. à café";
  else if (["pièce", "piece", "pieza", "piezas", "stück"].includes(uw)) unit = "pièce";
  else if (["g", "gr", "gram", "gramme"].includes(uw)) unit = "g";
  else if (["kg", "kilo"].includes(uw)) unit = "kg";
  else if (uw === "ml") { unit = "cl"; factor = 0.1; }
  else if (uw === "cl") unit = "cl";
  else if (["l", "litre", "liter"].includes(uw)) unit = "L";
  else if (["tbsp", "tablespoon", "cucharada", "cucharadas"].includes(uw)) unit = "c. à soupe";
  else if (["tsp", "teaspoon"].includes(uw)) unit = "c. à café";
  else if (uw === "cup") { unit = "cl"; factor = 24; }
  else if (["oz", "ounce"].includes(uw)) { unit = "g"; factor = 28.35; }
  else if (["lb", "pound"].includes(uw)) { unit = "g"; factor = 453.6; }
  // Unités-contenants françaises courantes : gardées comme unité à part
  // entière (comptage simple, sans conversion de poids/volume — une
  // "boîte" n'a pas de taille standard), plutôt que de tomber dans le
  // nom de l'ingrédient sous l'unité générique "pièce".
  else if (["boîte", "boite", "conserve", "lata", "latas", "dose", "dosen"].includes(uw)) unit = "boîte";
  else if (uw === "sachet") unit = "sachet";
  else if (uw === "pot") unit = "pot";
  else if (["paquet", "paquete", "paquetes", "packung", "packungen"].includes(uw)) unit = "sachet";
  else if (["tranche", "tranches"].includes(uw)) unit = "tranche";
  else if (["gousse", "gousses"].includes(uw)) unit = "gousse";

  let name;
  if (unit) {
    quantity = quantity != null ? Math.round(quantity * factor * 100) / 100 : null;
    name = rest.trim().replace(/^(?:de\s+|d['’])/i, "");
  } else {
    unit = "pièce";
    name = (unitWordRaw + " " + rest).trim();
  }
  // Ingrédients alternatifs ("oie ou canard") : le nombre indiqué avant
  // la seconde option répète souvent exactement la quantité déjà
  // extraite ("1 oie ou 1 canard") — sans ce nettoyage, il restait
  // collé au nom au lieu de disparaître comme la première occurrence.
  if (quantity != null && name) {
    const redundantNumberRegex = new RegExp("(\\bou\\s+)" + quantity.toString().replace(".", "[.,]") + "\\s+", "i");
    name = name.replace(redundantNumberRegex, "$1");
  }
  return { name: name || text, quantity, unit };
}

// Plusieurs services intermédiaires, essayés dans l'ordre : aucun d'eux
// n'a de garantie de disponibilité (services gratuits), donc si le
// premier échoue ou met trop de temps à répondre, on passe au suivant
// automatiquement avant d'abandonner. Corrige le comportement "ça marche
// une fois sur deux" observé avec un seul service.
const CORS_PROXIES = [
  (url) => "https://api.allorigins.win/raw?url=" + encodeURIComponent(url),
  (url) => "https://api.codetabs.com/v1/proxy?quest=" + encodeURIComponent(url),
  (url) => "https://api.cors.lol/?url=" + encodeURIComponent(url),
];

function fetchWithTimeout(url, ms) {
  // Volontairement pas d'AbortController/signal ici : sur certains
  // anciens navigateurs Android, l'option "signal" passée à fetch()
  // fait échouer la requête immédiatement avec une erreur générique
  // ("Failed to fetch"), même quand fetch() tout seul fonctionne très
  // bien. Une simple course entre la requête et un délai limite évite
  // ce souci de compatibilité, quitte à ne pas vraiment annuler la
  // requête d'origine (elle continue en arrière-plan, sans conséquence
  // puisqu'on en ignore alors le résultat).
  return Promise.race([
    fetch(url),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

async function fetchRecipeDataViaProxies(targetUrl, onAttempt) {
  let lastError = null;
  const failureDetails = [];
  for (let i = 0; i < CORS_PROXIES.length; i++) {
    if (onAttempt) onAttempt(i + 1, CORS_PROXIES.length);
    try {
      const res = await fetchWithTimeout(CORS_PROXIES[i](targetUrl), 30000);
      if (!res.ok) {
        lastError = new Error("http_" + res.status);
        failureDetails.push(`Service ${i + 1} : HTTP ${res.status}`);
        continue;
      }
      const html = await res.text();
      if (!html || html.length < 50) {
        lastError = new Error("empty_response");
        failureDetails.push(`Service ${i + 1} : réponse vide`);
        continue;
      }
      // Vérifie que la réponse contient réellement une recette
      // structurée, plutôt que de considérer toute réponse assez
      // longue comme une réussite : une page de blocage, d'erreur ou
      // d'inscription renvoyée par un service dépasse très souvent
      // 50 caractères sans contenir la moindre recette, ce qui
      // empêchait auparavant d'essayer les services suivants.
      const parser = new DOMParser();
      const docHtml = parser.parseFromString(html, "text/html");
      const recipeData = extractJsonLdRecipe(docHtml) || extractMicrodataRecipe(docHtml);
      if (recipeData) return recipeData;
      lastError = new Error("no_recipe_in_response");
      failureDetails.push(`Service ${i + 1} : page reçue mais sans recette reconnaissable`);
    } catch (e) {
      lastError = e;
      failureDetails.push(`Service ${i + 1} : ${e.name || "Error"} — ${e.message || "inconnue"}`);
    }
  }
  const finalError = lastError || new Error("all_proxies_failed");
  finalError.details = failureDetails.join(" · ");
  throw finalError;
}

// Convertit une durée au format ISO 8601 (ex. "PT1H30M") en minutes.
// Format utilisé par la plupart des sites de recettes pour prepTime et
// cookTime dans leurs données structurées.
function parseIsoDurationToMinutes(duration) {
  if (!duration || typeof duration !== "string") return null;
  const match = duration.match(/^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?/);
  if (!match) return null;
  const days = parseInt(match[1] || "0", 10);
  const hours = parseInt(match[2] || "0", 10);
  const minutes = parseInt(match[3] || "0", 10);
  const total = days * 24 * 60 + hours * 60 + minutes;
  return total > 0 ? total : null;
}

// Reconstruit les étapes de préparation, numérotées, à partir du champ
// "recipeInstructions" — qui peut être une simple chaîne, un tableau de
// chaînes, un tableau d'étapes (HowToStep), ou des sections groupées
// (HowToSection) selon le site. Bien plus utile que la simple
// "description" (souvent juste une accroche marketing).
/* ======================================================================
   IMPORT DE RECETTE DEPUIS UNE PHOTO (OCR)
   La reconnaissance de texte se fait entièrement sur l'appareil (aucune
   photo n'est envoyée où que ce soit), via Tesseract.js chargé à la
   demande. Le texte brut obtenu est ensuite découpé heuristiquement en
   nom / ingrédients / description, en repérant des mots-clés courants
   ("Ingrédients", "Préparation"...) dans plusieurs langues — bien moins
   fiable qu'un import par lien (pas de données structurées), donc la
   relecture avant enregistrement est essentielle.
   ====================================================================== */
const OCR_INGREDIENT_MARKER = /^(ingr[ée]dients?|ingredients|ingredientes|zutaten)\b/i;
const OCR_INSTRUCTION_MARKER = /^(pr[ée]paration|[ée]tapes|instructions?|method|steps|elaboraci[oó]n|preparaci[oó]n|zubereitung|anleitung)\b/i;
// Toute section qui doit arrêter la liste des ingrédients, pas
// seulement celle des étapes — "Ustensiles" par exemple, très courant
// juste après les ingrédients et avant la vraie section de
// préparation sur beaucoup de sites.
const OCR_SECTION_BOUNDARY_MARKER = /^(pr[ée]paration|[ée]tapes|instructions?|method|steps|elaboraci[oó]n|preparaci[oó]n|zubereitung|anleitung|ustensiles?|utensils?|mat[ée]riel|equipment|valeurs?\s+nutritionnelles?|nutritional\s+values?|valores?\s+nutricionales?|n[äa]hrwerte?|allerg[èe]nes?|allergens?|al[ée]rgenos?)\b/i;
// Nombre de personnes indiqué juste après le mot-clé "Ingrédients" sur
// la même ligne (ex. "Ingrédients pour 2 personnes", très courant sur
// les fiches HelloFresh) — extrait avant de retirer la ligne, pour ne
// pas perdre cette information quand le titre est filtré.
const OCR_PERSONS_IN_TITLE = /\b(\d+)\s*(?:personnes?|people|persons?|personas?|personen)\b/i;
function parseOcrRecipeText(rawText) {
  const lines = (rawText || "").split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return { name: "", ingredients: [], description: "", prepTime: null, cookTime: null };

  const ingredientMarker = OCR_INGREDIENT_MARKER;
  const instructionMarker = OCR_INSTRUCTION_MARKER;
  const sectionBoundaryMarker = OCR_SECTION_BOUNDARY_MARKER;
  // Marque la fin du vrai contenu de la recette : au-delà, ce n'est
  // presque toujours plus que des avis, des recettes similaires ou de
  // la navigation — sans ça, la description engloberait toute la fin
  // de la page. Liste élargie après avoir constaté des sections encore
  // non couvertes (ex. "Qu'est-ce qu'on mange ce soir ?", propre à
  // Marmiton mais représentative du genre de contenu à exclure).
  const descriptionEndMarker = /^(commentaires?|comments?|avis|reviews?|vous aimerez aussi|you (may|might) also like|related recipes?|plus de recettes|ces contenus devraient vous int[ée]resser|note de l['’]auteur|donnez votre avis|qu['’]est-ce qu['’]on mange|découvrir aussi|à découvrir|on vous propose|d[ée]couvrez aussi|dans la m[êe]me cat[ée]gorie|recettes similaires|similar recipes?|nos coups de coeur|publicit[ée]|advertisement|partager cette recette|share this recipe|imprimer|print recipe|newsletter)/i;

  const name = lines[0];
  const ingIdx = lines.findIndex((l) => ingredientMarker.test(l));
  const boundaryIdx = lines.findIndex((l, i) => (ingIdx < 0 || i > ingIdx) && sectionBoundaryMarker.test(l));
  const instrIdx = lines.findIndex((l, i) => (ingIdx < 0 || i > ingIdx) && instructionMarker.test(l));

  let ingredientLines = [];
  let descriptionLines = [];
  if (ingIdx >= 0) {
    const end = boundaryIdx >= 0 ? boundaryIdx : lines.length;
    ingredientLines = lines.slice(ingIdx + 1, end)
      // Repère de compteur "- personnes +" (choix du nombre de
      // personnes sur la page), pas un ingrédient.
      .filter((l) => !/^(pour\s+|for\s+)?\d*\s*(personnes?|people|persons?|personas?|personen)\s*[+\-]?$/i.test(l));
  }
  if (instrIdx >= 0) {
    const descEndIdx = lines.findIndex((l, i) => i > instrIdx && descriptionEndMarker.test(l));
    descriptionLines = lines.slice(instrIdx + 1, descEndIdx >= 0 ? descEndIdx : lines.length);
  } else if (ingIdx < 0) {
    // Aucun des deux mots-clés trouvé : impossible de distinguer les
    // sections, tout ce qui suit le nom devient la description — mieux
    // vaut laisser les ingrédients vides (à remplir à la main) qu'un
    // découpage hasardeux.
    const descEndIdx = lines.findIndex((l, i) => i > 0 && descriptionEndMarker.test(l));
    descriptionLines = lines.slice(1, descEndIdx >= 0 ? descEndIdx : lines.length);
  }

  const ingredients = ingredientLines
    .map((l) => l.replace(/^[-•*]\s*/, ""))
    .map(parseIngredientString)
    .filter((i) => i.name);

  // Les quantités reconnues dans le texte correspondent à la recette
  // entière pour le nombre de personnes indiqué sur la page d'origine
  // (quand il est repérable), pas à une seule personne. On ne divise
  // plus ici : avec l'import à plusieurs photos, le nombre de
  // personnes peut être détecté sur une AUTRE photo que celle des
  // ingrédients, donc diviser trop tôt (avant de connaître le nombre
  // final retenu après fusion) provoquait un doublement des quantités
  // affichées. La division se fait une seule fois, après la fusion
  // complète — voir mergeMultiPhotoResults et le repli Jina ci-dessous.
  let persons = null;
  lines.forEach((line) => {
    if (persons != null) return;
    const personsMatch = line.match(/\b(\d+)\s*(?:personnes?|convives?|parts?|servings?|portions?|personas?|raciones?|personen|portionen)\b/i);
    if (personsMatch) persons = Math.max(1, parseInt(personsMatch[1], 10));
  });

  // Convertit une expression de durée en minutes, en gérant les formats
  // "Xh YY" (heures + minutes, ex. "5h30" pour un temps de cuisson
  // long), "Xh" seul, ou un simple nombre de minutes — sans cette
  // conversion, "5h30" était pris à tort pour "5 minutes" (seul le
  // premier nombre était lu, sans tenir compte du "h").
  function parseTimeExpression(str) {
    if (!str) return null;
    const s = str.trim();
    const hourMinMatch = s.match(/(\d+)\s*h\s*(\d+)/i);
    if (hourMinMatch) return parseInt(hourMinMatch[1], 10) * 60 + parseInt(hourMinMatch[2], 10);
    const hourOnlyMatch = s.match(/(\d+)\s*h\b/i);
    if (hourOnlyMatch) return parseInt(hourOnlyMatch[1], 10) * 60;
    const minMatch = s.match(/(\d+)/);
    return minMatch ? parseInt(minMatch[1], 10) : null;
  }
  // Les temps de préparation/cuisson apparaissent souvent après les
  // ingrédients (pas avant) — recherche sur tout le texte plutôt que
  // sur une zone précise.
  let prepTime = null, cookTime = null;
  lines.forEach((line) => {
    const prepMatch = line.match(/pr[eé]paration\s*:\s*([^\n]+)/i) || line.match(/prep(?:aration)?\s*time\s*:\s*([^\n]+)/i);
    if (prepMatch) { const t = parseTimeExpression(prepMatch[1]); if (t != null) prepTime = t; }
    const cookMatch = line.match(/cuisson\s*:\s*([^\n]+)/i) || line.match(/cook\s*time\s*:\s*([^\n]+)/i);
    if (cookMatch) { const t = parseTimeExpression(cookMatch[1]); if (t != null) cookTime = t; }
  });

  return { name, ingredients, description: descriptionLines.join("\n"), prepTime, cookTime, persons };
}

let tesseractLibPromise = null;
function loadTesseractLib() {
  if (window.Tesseract) return Promise.resolve();
  if (tesseractLibPromise) return tesseractLibPromise;
  tesseractLibPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js";
    script.onload = () => resolve();
    script.onerror = () => { tesseractLibPromise = null; reject(new Error("tesseract_lib_load_failed")); };
    document.head.appendChild(script);
  });
  return tesseractLibPromise;
}
const TESSERACT_LANG_MAP = { fr: "fra", en: "eng", es: "spa", de: "deu" };

// Un seul Worker Tesseract réutilisé pour toute une série de photos,
// plutôt que d'en créer et détruire un à chaque image — avec huit
// photos, cela représentait huit initialisations complètes du moteur
// (chargement du modèle de langue compris), lent et gourmand en
// mémoire sur les appareils d'entrée de gamme.
let sharedTesseractWorker = null;
let sharedTesseractWorkerLang = null;
async function getSharedTesseractWorker() {
  await loadTesseractLib();
  const lang = TESSERACT_LANG_MAP[CURRENT_LANG] || "eng";
  if (sharedTesseractWorker && sharedTesseractWorkerLang === lang) return sharedTesseractWorker;
  if (sharedTesseractWorker) await sharedTesseractWorker.terminate();
  sharedTesseractWorker = await window.Tesseract.createWorker(lang);
  sharedTesseractWorkerLang = lang;
  return sharedTesseractWorker;
}
async function terminateSharedTesseractWorker() {
  if (sharedTesseractWorker) {
    const w = sharedTesseractWorker;
    sharedTesseractWorker = null;
    sharedTesseractWorkerLang = null;
    await w.terminate();
  }
}
async function runOcrOnImage(file) {
  const worker = await getSharedTesseractWorker();
  const { data } = await worker.recognize(file);
  return data.text;
}

// Devine à quelle section appartient le texte reconnu sur une photo :
// une photo peut ne contenir que les ingrédients, que les étapes, les
// deux à la fois (une fiche courte tenant sur une seule photo), ou
// aucun des deux de façon franche (photo de couverture, infos
// générales...). Retourne null si le résultat est trop incertain pour
// choisir automatiquement — il faudra alors demander à l'utilisateur.
function detectPhotoSection(parsed) {
  const hasIngredients = parsed.ingredients && parsed.ingredients.length > 0;
  const hasDescription = parsed.description && parsed.description.trim().length > 20;
  if (hasIngredients && hasDescription) return "mixed";
  if (hasIngredients) return "ingredients";
  if (hasDescription) return "preparation";
  return null;
}

// Réinterprète le texte brut d'une photo selon la section choisie
// (automatiquement ou manuellement) — le choix manuel doit vraiment
// changer la méthode d'analyse, pas seulement l'étiquette affichée.
// Une photo classée "Ingrédients" traite chaque ligne comme un
// ingrédient potentiel, sans exiger de mot-clé "Ingrédients" en tête
// (la photo est déjà supposée cadrée sur cette seule section) ; une
// photo "Préparation" garde tout le texte tel quel comme étapes ; une
// photo "Recette complète" utilise l'analyse habituelle (recherche des
// deux sections dans le même texte) ; "Infos générales" ne cherche que
// le nom, le nombre de personnes et les temps, jamais d'ingrédients ni
// d'étapes ; "Autre" ne participe pas à la fusion.
function deriveSectionDataForPhoto(rawText, section) {
  const empty = { name: "", ingredients: [], description: "", persons: null, prepTime: null, cookTime: null };
  if (section === "mixed") return parseOcrRecipeText(rawText);
  if (section === "general") {
    const full = parseOcrRecipeText(rawText);
    return { ...empty, name: full.name, persons: full.persons, prepTime: full.prepTime, cookTime: full.cookTime };
  }
  if (section === "ingredients") {
    const lines = (rawText || "").split("\n").map((l) => l.trim()).filter(Boolean);
    // Un titre complet ("Ingrédients pour 2 personnes") contient à la
    // fois le mot-clé de section ET le nombre de personnes — il faut
    // extraire ce nombre avant de retirer la ligne, sinon cette
    // information serait perdue plutôt que simplement filtrée.
    let persons = null;
    lines.forEach((l) => {
      if (persons != null) return;
      if (OCR_INGREDIENT_MARKER.test(l)) {
        const m = l.match(OCR_PERSONS_IN_TITLE);
        if (m) persons = Math.max(1, parseInt(m[1], 10));
      }
    });
    const ingredients = lines
      .filter((l) => !OCR_INGREDIENT_MARKER.test(l) && !OCR_SECTION_BOUNDARY_MARKER.test(l))
      .filter((l) => !/^(pour\s+|for\s+)?\d*\s*(personnes?|people|persons?|personas?|personen)\s*[+\-]?$/i.test(l))
      .map((l) => l.replace(/^[-•*]\s*/, ""))
      .map(parseIngredientString)
      .filter((i) => i.name);
    return { ...empty, ingredients, persons };
  }
  if (section === "preparation") {
    const lines = (rawText || "").split("\n").map((l) => l.trim()).filter(Boolean);
    const cleaned = lines.filter((l) => !OCR_INSTRUCTION_MARKER.test(l));
    return { ...empty, description: cleaned.join("\n") };
  }
  return empty; // "other" : aucune extraction
}

// Combine les résultats de plusieurs photos, chacune étiquetée avec sa
// section, en une seule recette prête à être vérifiée dans le
// formulaire — dans l'ordre où les photos ont été ajoutées. Le nom et
// le nombre de personnes ne viennent jamais d'une photo "Ingrédients"
// ou "Préparation" seule (leur "première ligne" n'a aucune raison
// d'être le nom de la recette), et une valeur de secours (4 personnes)
// n'est appliquée qu'une fois toutes les photos combinées, jamais
// avant — sinon, une photo sans portion détectée imposait sa valeur
// par défaut avant même qu'une autre photo n'ait pu fournir la vraie
// valeur, selon l'ordre d'ajout.
function mergeMultiPhotoResults(photos, confirmedPersons) {
  let name = "";
  let ingredients = [];
  let descriptionParts = [];
  let persons = null, prepTime = null, cookTime = null;
  photos.forEach((p) => {
    const data = p.sectionData;
    if (!data) return;
    if (data.ingredients && data.ingredients.length) ingredients = ingredients.concat(data.ingredients);
    if (data.description && data.description.trim()) descriptionParts.push(data.description.trim());
    if (!name && data.name) name = data.name;
    if (persons == null && data.persons) persons = data.persons;
    if (prepTime == null && data.prepTime) prepTime = data.prepTime;
    if (cookTime == null && data.cookTime) cookTime = data.cookTime;
  });
  // Les quantités reconnues sur chaque photo sont des totaux bruts,
  // jamais divisés avant ce point (voir parseOcrRecipeText et
  // deriveSectionDataForPhoto) — précisément pour éviter de diviser
  // trop tôt, avant de connaître le nombre de personnes qui pourrait
  // n'être détecté que sur une AUTRE photo que celle des ingrédients.
  // Le nombre confirmé par l'utilisateur (champ visible à l'écran,
  // jamais une simple supposition silencieuse) prime toujours sur la
  // détection automatique interne quand il est fourni.
  const finalPersons = confirmedPersons || persons || 4;
  const dividedIngredients = ingredients.map((i) => ({ ...i, quantity: i.quantity != null ? i.quantity / finalPersons : null }));
  return { name, ingredients: dividedIngredients, description: descriptionParts.join("\n\n"), persons: finalPersons, prepTime, cookTime };
}

const MAX_IMPORT_PHOTOS = 8;

function renderImportPhoto() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 20px;line-height:1.5;">${escapeHtml(t("import_photo_disclaimer_main"))}<span style="color:var(--danger);text-decoration:underline;">${escapeHtml(t("import_photo_disclaimer_warning"))}</span></p>`));

  const listHolder = el(`<div></div>`);
  wrap.appendChild(listHolder);

  const addSection = el(`<div style="display:flex;gap:10px;margin-top:10px;"></div>`);
  const cameraInput = el(`<input type="file" accept="image/*" capture="environment" style="display:none;">`);
  const galleryInput = el(`<input type="file" accept="image/*" style="display:none;">`);
  const cameraBtn = el(`<button type="button" class="btn btn-outline" style="flex:1;">${t("import_photo_add_camera")}</button>`);
  const galleryBtn = el(`<button type="button" class="btn btn-outline" style="flex:1;">${t("import_photo_add_gallery")}</button>`);
  cameraBtn.addEventListener("click", () => cameraInput.click());
  galleryBtn.addEventListener("click", () => galleryInput.click());
  addSection.appendChild(cameraBtn);
  addSection.appendChild(galleryBtn);
  addSection.appendChild(cameraInput);
  addSection.appendChild(galleryInput);
  wrap.appendChild(addSection);

  const maxReachedNote = el(`<p style="font-size:12px;color:var(--text-muted);text-align:center;margin-top:8px;display:none;">${escapeHtml(t("import_photo_max_reached"))}</p>`);
  wrap.appendChild(maxReachedNote);

  // Le nombre de personnes conditionne directement les quantités
  // finales (division une seule fois avant la fusion) — un champ
  // visible et modifiable évite de supposer silencieusement 4 quand
  // aucune photo n'indique clairement le nombre de personnes, ce qui
  // pourrait sinon donner des quantités incorrectes si l'utilisateur
  // corrige seulement APRÈS coup dans le formulaire final.
  const personsSection = el(`<div class="card" style="padding:12px;margin-top:16px;">
    <label for="import-photo-persons" style="font-size:13px;font-weight:600;display:block;margin-bottom:6px;">${escapeHtml(t("import_photo_persons_label"))}</label>
    <input type="number" min="1" id="import-photo-persons" value="4" style="width:100%;padding:8px;border-radius:8px;border:1px solid var(--border);font-size:14px;">
    <p id="import-photo-persons-note" style="font-size:11px;color:var(--text-muted);margin:6px 0 0;"></p>
  </div>`);
  wrap.appendChild(personsSection);
  const personsInput = personsSection.querySelector("#import-photo-persons");
  const personsNote = personsSection.querySelector("#import-photo-persons-note");
  let personsManuallyEdited = false;
  personsInput.addEventListener("input", () => { personsManuallyEdited = true; });

  const mergeBtn = el(`<button type="button" class="btn btn-primary" style="width:100%;margin-top:16px;" disabled>${t("import_photo_merge_button")}</button>`);
  const mergeHint = el(`<p style="font-size:12px;color:var(--text-muted);text-align:center;margin-top:8px;">${escapeHtml(t("import_photo_merge_hint"))}</p>`);
  wrap.appendChild(mergeBtn);
  wrap.appendChild(mergeHint);

  const SECTION_LABELS = {
    ingredients: () => t("import_photo_section_ingredients"),
    preparation: () => t("import_photo_section_preparation"),
    general: () => t("import_photo_section_general"),
    mixed: () => t("import_photo_section_mixed"),
    other: () => t("import_photo_section_other"),
  };

  function refreshUi() {
    listHolder.innerHTML = "";
    state.multiPhotoImport.forEach((p) => {
      const card = el(`<div class="card" style="padding:12px;margin-bottom:10px;display:flex;gap:12px;align-items:flex-start;"></div>`);
      card.appendChild(el(`<img src="${p.thumbnail}" alt="${escapeHtml(t("import_photo_thumbnail_alt"))}" style="width:64px;height:64px;object-fit:cover;border-radius:8px;flex-shrink:0;">`));
      const info = el(`<div style="flex:1;min-width:0;"></div>`);
      if (p.status === "processing") {
        info.appendChild(el(`<div style="font-size:13px;color:var(--text-muted);">${escapeHtml(t("import_photo_processing_short"))}</div>`));
      } else if (p.status === "error") {
        info.appendChild(el(`<div style="font-size:13px;color:var(--danger);">${escapeHtml(t("import_photo_error"))}</div>`));
        info.appendChild(el(`<div style="font-size:11px;color:var(--text-muted);word-break:break-word;">${escapeHtml(p.errorMessage || "")}</div>`));
      } else {
        info.appendChild(el(`<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">${escapeHtml(t("import_photo_section_label"))}</div>`));
        const select = el(`<select style="width:100%;padding:6px;border-radius:8px;border:1px solid var(--border);font-size:13px;">
          ${Object.keys(SECTION_LABELS).map((key) => `<option value="${key}" ${p.section === key ? "selected" : ""}>${escapeHtml(SECTION_LABELS[key]())}</option>`).join("")}
        </select>`);
        select.addEventListener("change", () => {
          p.section = select.value;
          p.autoDetected = false;
          p.sectionData = deriveSectionDataForPhoto(p.rawText, p.section);
          refreshUi();
        });
        info.appendChild(select);
        if (p.autoDetected) {
          info.appendChild(el(`<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">✓ ${escapeHtml(t("import_photo_auto_detected"))}</div>`));
        } else if (p.section === "other") {
          info.appendChild(el(`<div style="font-size:11px;color:var(--accent);margin-top:2px;">${escapeHtml(t("import_photo_manual_needed"))}</div>`));
        }
      }
      card.appendChild(info);
      const removeBtn = el(`<button type="button" aria-label="${escapeHtml(t("import_photo_remove"))}" style="background:none;border:none;color:var(--text-muted);font-size:18px;cursor:pointer;padding:4px;flex-shrink:0;">×</button>`);
      removeBtn.addEventListener("click", () => {
        state.multiPhotoImport = state.multiPhotoImport.filter((x) => x.id !== p.id);
        refreshUi();
      });
      card.appendChild(removeBtn);
      listHolder.appendChild(card);
    });

    const atMax = state.multiPhotoImport.length >= MAX_IMPORT_PHOTOS;
    addSection.style.display = atMax ? "none" : "flex";
    maxReachedNote.style.display = atMax ? "block" : "none";
    const doneCount = state.multiPhotoImport.filter((p) => p.status === "done").length;
    const anyProcessing = state.multiPhotoImport.some((p) => p.status === "processing");
    mergeBtn.disabled = doneCount === 0 || anyProcessing;
    cameraBtn.disabled = anyProcessing;
    galleryBtn.disabled = anyProcessing;

    if (!personsManuallyEdited) {
      const detected = state.multiPhotoImport.map((p) => p.sectionData && p.sectionData.persons).find((v) => v != null);
      personsInput.value = detected || 4;
      personsNote.textContent = detected ? `✓ ${t("import_photo_persons_detected")}` : t("import_photo_persons_assumed");
    }
  }

  async function handleNewPhoto(file) {
    if (!file) return;
    if (state.multiPhotoImport.length >= MAX_IMPORT_PHOTOS) return;
    const thumbnail = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(file);
    });
    const entry = { id: uid(), thumbnail, status: "processing", rawText: null, parsed: null, sectionData: null, section: null, autoDetected: false, errorMessage: null };
    state.multiPhotoImport.push(entry);
    refreshUi();
    try {
      const rawText = await runOcrOnImage(file);
      if (!rawText || !rawText.trim()) {
        entry.status = "error";
        entry.errorMessage = t("import_photo_no_text");
      } else {
        entry.rawText = rawText;
        entry.parsed = parseOcrRecipeText(rawText);
        const detected = detectPhotoSection(entry.parsed);
        entry.section = detected || "other";
        entry.autoDetected = !!detected;
        entry.sectionData = deriveSectionDataForPhoto(rawText, entry.section);
        entry.status = "done";
      }
    } catch (err) {
      entry.status = "error";
      entry.errorMessage = formatCaughtError(err);
    }
    refreshUi();
  }

  cameraInput.addEventListener("change", (e) => { handleNewPhoto(e.target.files[0]); e.target.value = ""; });
  galleryInput.addEventListener("change", (e) => { handleNewPhoto(e.target.files[0]); e.target.value = ""; });

  mergeBtn.addEventListener("click", async () => {
    const usable = state.multiPhotoImport.filter((p) => p.status === "done");
    const confirmedPersons = Math.max(1, parseInt(personsInput.value, 10) || 4);
    const merged = mergeMultiPhotoResults(usable, confirmedPersons);
    state.multiPhotoImport = [];
    try {
      await terminateSharedTesseractWorker();
    } catch (e) {
      // Sans conséquence pour l'utilisateur : le Worker sera de toute
      // façon recréé au prochain import si besoin. La fusion elle-même
      // ne doit jamais rester bloquée pour un problème de nettoyage.
    }
    state.editingRecipeId = null;
    state.formIngredients = merged.ingredients.length ? merged.ingredients : [{ name: "", quantity: "", unit: "pièce" }];
    state.formAllergens = [];
    state.formPhoto = null;
    state.screen = "form";
    state._importPrefill = merged;
    render();
  });

  refreshUi();
  return wrap;
}

function extractRecipeInstructions(recipeData) {
  const raw = recipeData.recipeInstructions;
  if (!raw) return "";
  const lines = [];
  let stepNum = 1;
  function collect(item) {
    if (typeof item === "string" && item.trim()) { lines.push(`${stepNum}. ${item.trim()}`); stepNum++; return; }
    if (!item || typeof item !== "object") return;
    const type = item["@type"];
    if (type === "HowToSection" && Array.isArray(item.itemListElement)) {
      if (item.name) lines.push(`\n${item.name} :`);
      item.itemListElement.forEach(collect);
    } else if (typeof item.text === "string" && item.text.trim()) {
      lines.push(`${stepNum}. ${item.text.trim()}`); stepNum++;
    } else if (typeof item.name === "string" && item.name.trim()) {
      lines.push(`${stepNum}. ${item.name.trim()}`); stepNum++;
    }
  }
  if (Array.isArray(raw)) raw.forEach(collect);
  else collect(raw);
  return lines.join("\n").trim();
}

function extractRecipeImageUrl(recipeData) {
  let img = recipeData.image;
  if (!img) return null;
  if (Array.isArray(img)) img = img[0];
  if (img && typeof img === "object" && typeof img.url === "string") img = img.url;
  return typeof img === "string" && img.trim() ? img.trim() : null;
}

// Devine la catégorie interne (toujours en français) à partir du texte
// libre "recipeCategory" fourni par le site, quelle que soit sa langue —
// simple recherche de mots-clés, pas une traduction complète.
function guessCategoryFromText(text) {
  if (!text) return "Autre";
  const key = normalize(String(text));
  if (/dessert|sweet|postre|nachtisch|suss/.test(key)) return "Dessert";
  if (/starter|entree|appetizer|vorspeise|aperitivo|antipasto/.test(key)) return "Entrée";
  if (/breakfast|petit.?dejeuner|desayuno|fruhstuck/.test(key)) return "Petit-déjeuner";
  if (/drink|beverage|boisson|bebida|getranke|cocktail/.test(key)) return "Boisson";
  if (/sauce/.test(key)) return "Sauce";
  if (/apero|aperitif|snack|amuse/.test(key)) return "Apéro";
  if (/main|plat|plato|hauptgericht|dinner|lunch|entree course/.test(key)) return "Plat";
  return "Autre";
}

// Résout le nom d'un ingrédient importé vers un ingrédient déjà connu
// quand c'est manifestement le même (correspondance exacte ou traduite,
// ou variante plurielle/faute de frappe très proche) — pour que l'import
// par lien rejoigne naturellement la liste existante plutôt que de
// systématiquement créer de nouvelles entrées proches de doublons.
function resolveImportedIngredientName(rawName) {
  const trimmed = (rawName || "").trim();
  const exact = resolveIngredientInput(trimmed);
  if (normalize(exact) !== normalize(trimmed) || state.ingredientNames.some((n) => normalize(n) === normalize(trimmed))) {
    return exact;
  }
  const fuzzy = findClosestIngredientMatch(trimmed);
  if (fuzzy && fuzzy.ratio >= 0.9) return fuzzy.name;
  return trimmed;
}

function resizeBlobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const maxW = 800;
        const scale = Math.min(1, maxW / img.width);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/jpeg", 0.8));
      };
      img.onerror = () => reject(new Error("image_decode_failed"));
      img.src = reader.result;
    };
    reader.onerror = () => reject(new Error("image_read_failed"));
    reader.readAsDataURL(blob);
  });
}

// Récupère l'image d'une recette (photo de couverture) et la convertit
// en vignette utilisable par l'application — tentative directe d'abord
// (fonctionne pour beaucoup de CDN d'images qui autorisent déjà l'accès
// depuis n'importe quel site), puis via les mêmes services intermédiaires
// que pour la page elle-même en repli. Un échec ici n'empêche jamais
// l'import du reste de la recette.
async function fetchImageAsDataUrl(imageUrl) {
  const attempts = [{ url: imageUrl, timeout: 15000 }];
  // Le Worker Cloudflare personnel (si configuré) est essayé avant les
  // 3 services de repli publics, pour la même raison de fiabilité que
  // pour le texte de la recette — avec un délai plus généreux (30s,
  // supérieur aux 25s internes du Worker), les images pouvant prendre
  // plus de temps à récupérer que les autres services plus simples.
  if (CLOUDFLARE_WORKER_URL) attempts.push({ url: CLOUDFLARE_WORKER_URL + "?url=" + encodeURIComponent(imageUrl), timeout: 30000 });
  attempts.push(...CORS_PROXIES.map((p) => ({ url: p(imageUrl), timeout: 15000 })));
  for (const attempt of attempts) {
    try {
      const res = await fetchWithTimeout(attempt.url, attempt.timeout);
      if (!res.ok) continue;
      const blob = await res.blob();
      if (!blob.type.startsWith("image/")) continue;
      return await resizeBlobToDataUrl(blob);
    } catch (e) { /* tentative suivante */ }
  }
  return null;
}

// Cherche des données structurées "Recipe" au format JSON-LD (le plus
// courant sur les grands sites).
function extractJsonLdRecipe(docHtml) {
  const scripts = docHtml.querySelectorAll('script[type="application/ld+json"]');
  let found = null;
  scripts.forEach((script) => {
    if (found) return;
    try {
      const json = JSON.parse(script.textContent);
      const candidates = Array.isArray(json) ? json : (json["@graph"] || [json]);
      for (const item of candidates) {
        const types = Array.isArray(item["@type"]) ? item["@type"] : [item["@type"]];
        if (types.includes("Recipe")) { found = item; break; }
      }
    } catch (e) { /* bloc JSON-LD mal formé, on l'ignore */ }
  });
  return found;
}

// Repli pour les sites (souvent plus anciens) qui utilisent le format
// "microdonnées" (attributs itemscope/itemprop dans le HTML) plutôt que
// le JSON-LD. Reconstruit un objet de même forme que le JSON-LD pour
// pouvoir être traité exactement de la même façon ensuite.
function extractMicrodataRecipe(docHtml) {
  const scope = docHtml.querySelector('[itemscope][itemtype*="Recipe"]');
  if (!scope) return null;
  function getAll(prop) {
    const els = scope.querySelectorAll(`[itemprop="${prop}"]`);
    return Array.from(els).map((elm) => {
      if (elm.hasAttribute("content")) return elm.getAttribute("content");
      if (elm.tagName === "IMG") return elm.getAttribute("src");
      if (elm.tagName === "META") return elm.getAttribute("content");
      if (elm.tagName === "TIME") return elm.getAttribute("datetime") || elm.textContent.trim();
      return elm.textContent.trim();
    }).filter(Boolean);
  }
  const ingredientProp = getAll("recipeIngredient").length ? "recipeIngredient" : "ingredients";
  return {
    name: getAll("name")[0] || "",
    description: getAll("description")[0] || "",
    recipeIngredient: getAll(ingredientProp),
    recipeInstructions: getAll("recipeInstructions"),
    image: getAll("image")[0] || null,
    prepTime: getAll("prepTime")[0] || null,
    cookTime: getAll("cookTime")[0] || null,
    recipeYield: getAll("recipeYield")[0] || null,
    recipeCategory: getAll("recipeCategory")[0] || null,
  };
}

// Jina AI Reader ne renvoie pas le HTML brut mais une version nettoyée
// en texte (Markdown) de la page — inutile pour ma méthode habituelle
// (qui cherche des données structurées cachées dans le HTML), mais un
// bon point de départ pour la même analyse heuristique que l'import
// par photo. Un filet de secours d'un genre différent, pas juste un
// service de plus qui fait la même chose que les autres.
async function fetchViaJinaReader(url) {
  const res = await fetchWithTimeout("https://r.jina.ai/" + url, 20000);
  if (!res.ok) throw new Error("jina_http_" + res.status);
  const text = await res.text();
  if (!text || text.length < 50) throw new Error("jina_empty_response");
  return text;
}

// Retire l'en-tête technique de Jina (Title:/URL Source:/Markdown
// Content:) et la ponctuation Markdown (#, *, -, ** ...) en début de
// ligne, pour que le texte ressemble à ce que l'analyseur heuristique
// (conçu pour du texte brut OCR) sait déjà traiter.
function stripJinaMarkdownNoise(markdown) {
  const rawLines = markdown.split("\n");
  const contentMarkerIdx = rawLines.findIndex((l) => /^markdown content:/i.test(l.trim()));
  let relevant = contentMarkerIdx >= 0 ? rawLines.slice(contentMarkerIdx + 1) : rawLines;

  // Beaucoup de sites (bandeau de cookies, menu de navigation...) font
  // précéder le vrai contenu par des centaines de lignes sans rapport.
  // Le premier "vrai" titre (un seul "#", pas "##"/"###") est presque
  // toujours le titre de la recette elle-même — on coupe tout ce qui
  // précède d'un coup.
  const h1Idx = relevant.findIndex((l) => /^#\s+\S/.test(l.trim()));
  if (h1Idx > 0) relevant = relevant.slice(h1Idx);

  // Nettoie chaque ligne (images, liens, ponctuation Markdown) avant
  // de les regrouper.
  const cleanedRawLines = relevant.map((l) => l
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[image[^\]]*\]/gi, "")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\*\*/g, "")
    .replace(/\*/g, "")
  );

  // Sur certains sites (Marmiton notamment), un seul ingrédient est
  // éclaté sur plusieurs lignes brutes (image, quantité, nom chacun
  // séparément). On regroupe tout ce qui suit une puce ("- ...") en une
  // seule "ligne logique", jusqu'à la puce ou le titre suivant.
  const grouped = [];
  let current = null;
  cleanedRawLines.forEach((raw) => {
    const trimmed = raw.trim();
    if (!trimmed) return; // ligne vide : bruit de mise en page, ignorée

    // Repères de sous-section ("pour la marinade :", "pour la pâte :")
    // ou texte d'interface récurrent ("Voir plus") : on clôt
    // l'ingrédient en cours sans les y mélanger, sans les garder non
    // plus comme ligne à part — ce ne sont ni des ingrédients, ni du
    // vrai contenu de recette.
    const isNoiseLine = /^pour\s+.{1,40}\s*:\s*$/i.test(trimmed)
      || /^voir plus$/i.test(trimmed)
      || /^en cliquant sur les liens/i.test(trimmed);
    if (isNoiseLine) {
      if (current !== null) { grouped.push(current); current = null; }
      return;
    }

    const headingMatch = trimmed.match(/^#{1,6}\s*(.*)$/);
    const bulletMatch = trimmed.match(/^[-*•]\s*(?:\[x\]\s*)?(.*)$/i);

    if (headingMatch) {
      if (current !== null) grouped.push(current);
      current = null;
      grouped.push(headingMatch[1].trim());
    } else if (bulletMatch) {
      if (current !== null) grouped.push(current);
      current = bulletMatch[1].trim();
    } else if (current !== null) {
      current = current.length ? current + " " + trimmed : trimmed;
    } else {
      grouped.push(trimmed);
    }
  });
  if (current !== null) grouped.push(current);

  return grouped.filter(Boolean).join("\n");
}

// ⚠️ À CONFIGURER : une fois votre Worker Cloudflare déployé (voir
// COMMENT_DEPLOYER.md), collez son adresse ici, sans "/" ni paramètre
// à la fin (ex. "https://mes-recettes-proxy.votre-pseudo.workers.dev").
// Laissez vide ("") pour désactiver cette étape et passer directement
// à Jina AI Reader puis aux 3 services de repli.
const CLOUDFLARE_WORKER_URL = "https://mes-recettes-proxy.fabricemoritel.workers.dev";

// Convertit les données structurées "Recipe" (JSON-LD ou microdonnées,
// peu importe le service qui les a fournies) vers le format interne de
// l'application — factorisé ici pour être utilisé aussi bien après le
// Worker Cloudflare qu'après les 3 services de repli, qui produisent
// tous les deux la même forme de données en cas de succès.
async function buildRecipeFromStructuredData(recipeData) {
  const name = typeof recipeData.name === "string" ? recipeData.name : "";
  const instructions = extractRecipeInstructions(recipeData);
  const shortDescription = typeof recipeData.description === "string" ? recipeData.description.trim() : "";
  const description = instructions || shortDescription;

  let persons = 4;
  const yieldRaw = recipeData.recipeYield || recipeData.yield;
  if (yieldRaw) {
    let y = Array.isArray(yieldRaw) ? yieldRaw[0] : yieldRaw;
    if (y && typeof y === "object") y = y.value || y.name || "";
    const m = String(y).match(/\d+/);
    if (m) persons = parseInt(m[0], 10);
  }
  persons = Math.max(1, persons);

  const rawIngredients = Array.isArray(recipeData.recipeIngredient) ? recipeData.recipeIngredient : [];
  const ingredients = rawIngredients
    .map(parseIngredientString)
    // Les quantités indiquées par le site source correspondent à la
    // recette entière pour "persons" personnes, alors que l'application
    // stocke toujours les quantités "pour 1 personne" en interne — sans
    // cette division, elles seraient multipliées une seconde fois à
    // l'affichage (ex. "1 poulet" pour 4 personnes deviendrait "4
    // poulets" une fois affiché pour 4 personnes).
    .map((i) => ({ ...i, quantity: i.quantity != null ? i.quantity / persons : null }))
    .filter((i) => i.name)
    .map((i) => ({ ...i, name: resolveImportedIngredientName(i.name) }));

  const prepTime = parseIsoDurationToMinutes(recipeData.prepTime);
  const cookTime = parseIsoDurationToMinutes(recipeData.cookTime);
  const category = guessCategoryFromText(recipeData.recipeCategory);

  let photo = null;
  const imageUrl = extractRecipeImageUrl(recipeData);
  if (imageUrl) {
    try { photo = await fetchImageAsDataUrl(imageUrl); } catch (e) { photo = null; }
  }

  return { name, description, ingredients, persons, prepTime, cookTime, category, photo };
}

// Récupère et analyse une page via le Worker Cloudflare personnel
// (voir CLOUDFLARE_WORKER_URL ci-dessus) — quand il est configuré et
// fonctionne, c'est la source la plus fiable et la plus complète
// (photo automatique, temps et personnes précis), puisque c'est un
// service qu'on contrôle entièrement plutôt qu'un proxy public
// partagé par de nombreuses autres applications.
async function fetchRecipeDataViaWorker(targetUrl) {
  if (!CLOUDFLARE_WORKER_URL) throw new Error("worker_not_configured");
  const res = await fetchWithTimeout(CLOUDFLARE_WORKER_URL + "?url=" + encodeURIComponent(targetUrl), 30000);
  if (!res.ok) {
    // Le corps de la réponse contient le message précis du Worker (ex.
    // "Refused target host", "Port not allowed"...) — sans le lire ici,
    // seul le code HTTP générique (ex. 400) était visible dans le
    // diagnostic, masquant la vraie raison du refus.
    let detail = "";
    try { detail = (await res.text()).slice(0, 150); } catch (e) { /* corps illisible, tant pis */ }
    throw new Error("worker_http_" + res.status + (detail ? ` (${detail})` : ""));
  }
  const html = await res.text();
  if (!html || html.length < 50) throw new Error("worker_empty_response");
  const parser = new DOMParser();
  const docHtml = parser.parseFromString(html, "text/html");
  const recipeData = extractJsonLdRecipe(docHtml) || extractMicrodataRecipe(docHtml);
  if (!recipeData) throw new Error("worker_no_recipe_in_response");
  return recipeData;
}

// Pour le panneau de diagnostic (voir renderDiagnostic) : garde une
// trace du dernier service d'import ayant réussi et de la dernière
// erreur rencontrée, sans jamais conserver l'adresse importée
// elle-même ni aucun contenu de recette — uniquement le nom du service
// et un message d'erreur générique, utile pour un futur signalement de
// bogue sans exposer de donnée personnelle.
function recordImportDiagnostic(service, errorMessage) {
  try {
    if (service) {
      localStorage.setItem("lastImportService", service);
      // Une réussite efface l'ancienne erreur : sans ça, un import
      // réussi laissait quand même affichée une erreur d'un essai
      // précédent, pouvant faire croire à tort à un problème persistant.
      localStorage.removeItem("lastImportError");
    }
    if (errorMessage) localStorage.setItem("lastImportError", `${new Date().toISOString()} — ${errorMessage}`.slice(0, 300));
  } catch (e) { /* stockage indisponible, sans conséquence pour le diagnostic */ }
}

async function fetchRecipeFromUrl(url, onAttempt) {
  // Mode de test temporaire, activé uniquement en ajoutant
  // "?importtest=..." à l'adresse — jamais présent en usage normal,
  // sert uniquement à vérifier manuellement les vrais chemins de repli
  // (tests 3.3/3.4 de TESTS_NON_REGRESSION.md) sans devoir couper le
  // vrai Worker Cloudflare pour tout le monde. Valeurs reconnues :
  // "jina" (saute le Worker), "proxy" (saute Worker + Jina), "fail"
  // (saute les trois, pour vérifier le message final).
  // Restreint à localhost : sur le site public déployé, ce paramètre
  // est purement et simplement ignoré, pour qu'il ne puisse jamais être
  // utilisé pour perturber volontairement l'import de quelqu'un d'autre.
  const isLocalhost = ["localhost", "127.0.0.1", "[::1]", ""].includes(location.hostname);
  const importTestMode = isLocalhost ? new URLSearchParams(location.search).get("importtest") : null;

  // 1. Worker Cloudflare personnel en premier, si configuré : c'est la
  // source la plus fiable et la plus complète (voir commentaire de
  // fetchRecipeDataViaWorker ci-dessus).
  if (!importTestMode) {
    try {
      const recipeData = await fetchRecipeDataViaWorker(url);
      const result = await buildRecipeFromStructuredData(recipeData);
      recordImportDiagnostic("Worker Cloudflare");
      try { localStorage.removeItem("lastWorkerError"); } catch (e) { /* sans conséquence */ }
      return result;
    } catch (e) {
      // Pas configuré, ou a échoué : on continue avec Jina ci-dessous.
      // L'erreur précise est conservée pour le diagnostic, même si
      // l'import réussit ensuite via un autre service — sans ça,
      // impossible de savoir POURQUOI le Worker a échoué si un service
      // de repli masque le problème en réussissant à sa place.
      try {
        localStorage.setItem("lastWorkerError", `${new Date().toISOString()} — ${formatCaughtError(e)}`.slice(0, 300));
      } catch (err) { /* sans conséquence */ }
    }
  }

  // 2. Jina AI Reader ensuite : plus fiable en pratique que les 3
  // services CORS classiques restants, même si son texte nettoyé donne
  // une extraction un peu moins précise (pas de photo automatique,
  // temps/nombre de personnes parfois approximatifs) qu'une vraie
  // extraction de données structurées quand elle réussit.
  if (importTestMode !== "proxy" && importTestMode !== "fail") {
    try {
      const markdown = await fetchViaJinaReader(url);
      const cleanedText = stripJinaMarkdownNoise(markdown);
      const parsedFromText = parseOcrRecipeText(cleanedText);
      if (parsedFromText && parsedFromText.ingredients.length) {
        recordImportDiagnostic("Jina AI Reader" + (importTestMode ? " (test)" : ""));
        // Divise ici par le nombre de personnes détecté (une seule
        // fois) : parseOcrRecipeText renvoie désormais les quantités
        // totales brutes, la division se faisant au moment opportun
        // selon le chemin d'import (ici directement, puisqu'il n'y a
        // pas d'étape de fusion multi-photos sur ce chemin).
        const detectedPersons = parsedFromText.persons;
        const dividedIngredients = detectedPersons
          ? parsedFromText.ingredients.map((i) => ({ ...i, quantity: i.quantity != null ? i.quantity / detectedPersons : null }))
          : parsedFromText.ingredients;
        return {
          name: parsedFromText.name,
          description: parsedFromText.description,
          ingredients: dividedIngredients.map((i) => ({ ...i, name: resolveImportedIngredientName(i.name) })),
          persons: detectedPersons || 4,
          prepTime: parsedFromText.prepTime,
          cookTime: parsedFromText.cookTime,
          category: "Autre",
          photo: null,
        };
      }
    } catch (e) {
      // Jina a échoué ou n'a rien trouvé d'exploitable : on tente les 3
      // services habituels ci-dessous avant d'abandonner définitivement.
    }
  }

  // 3. Les 3 services CORS publics classiques, en tout dernier
  // recours : les moins fiables des trois approches, mais un dernier
  // filet de secours utile quand les deux précédentes ont échoué.
  let recipeData = null;
  if (importTestMode !== "fail") {
    try {
      recipeData = await fetchRecipeDataViaProxies(url, onAttempt);
    } catch (e) {
      // Tous les services intermédiaires habituels ont aussi échoué.
    }
  }

  if (!recipeData) {
    recordImportDiagnostic(null, "no_recipe_found (tous les services ont échoué)");
    throw new Error("no_recipe_found");
  }
  recordImportDiagnostic("Service de secours (proxy public)" + (importTestMode ? " (test)" : ""));
  return await buildRecipeFromStructuredData(recipeData);
}

function renderImportUrl() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;line-height:1.5;">${escapeHtml(t("import_url_disclaimer"))}</p>`));
  wrap.appendChild(el(`<div class="field">
    <label for="import-url-input">${t("import_url_label")}</label>
    <div style="display:flex;gap:8px;">
      <input type="url" id="import-url-input" placeholder="${t("import_url_placeholder")}" style="flex:1;">
      <button type="button" id="import-url-clear" class="btn btn-outline btn-sm" style="width:auto;flex-shrink:0;">${t("import_url_clear_button")}</button>
    </div>
  </div>`));
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--danger);margin:0 0 20px;line-height:1.5;">${escapeHtml(t("import_url_duplicate_warning"))}</p>`));
  const btn = el(`<button class="btn btn-primary">${t("import_url_button")}</button>`);
  wrap.appendChild(btn);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--danger);margin:12px 0 0;line-height:1.5;">${escapeHtml(t("import_url_failure_warning"))}</p>`));
  const statusHolder = el(`<div style="margin-top:16px;font-size:14px;"></div>`);
  wrap.querySelector("#import-url-clear").addEventListener("click", () => {
    wrap.querySelector("#import-url-input").value = "";
    statusHolder.textContent = "";
    wrap.querySelector("#import-url-input").focus();
  });
  btn.addEventListener("click", async () => {
    let url = wrap.querySelector("#import-url-input").value.trim();
    // Ajoute automatiquement le protocole si absent — cas fréquent
    // quand le lien est copié depuis un endroit qui l'affiche sans
    // préfixe (aperçu, résultat de recherche...) ; sans cette
    // correction, new URL() rejette silencieusement l'adresse comme
    // invalide alors qu'elle est parfaitement reconnaissable.
    if (url && !/^https?:\/\//i.test(url)) url = "https://" + url;
    if (!url) { statusHolder.textContent = t("import_url_no_url"); return; }
    btn.disabled = true;
    statusHolder.textContent = t("import_url_fetching");
    try {
      const result = await fetchRecipeFromUrl(url, (attempt, total) => {
        statusHolder.textContent = total > 1
          ? t("import_url_fetching") + ` (${attempt}/${total})`
          : t("import_url_fetching");
      });
      state.editingRecipeId = null;
      state.formIngredients = result.ingredients.length ? result.ingredients : [{ name: "", quantity: "", unit: "pièce" }];
      state.formAllergens = [];
      state.formPhoto = result.photo || null;
      state.screen = "form";
      state._importPrefill = {
        name: result.name,
        description: result.description,
        persons: result.persons,
        category: result.category,
        prepTime: result.prepTime,
        cookTime: result.cookTime,
      };
      render();
    } catch (e) {
      statusHolder.innerHTML = "";
      statusHolder.appendChild(el(`<div>${escapeHtml(navigator.onLine === false ? t("import_url_error_offline") : t("import_url_error"))}</div>`));
      if (e && e.details) {
        statusHolder.appendChild(el(`<div style="font-size:11px;color:var(--text-muted);margin-top:6px;word-break:break-word;">${escapeHtml(e.details)}</div>`));
      }
      btn.disabled = false;
    }
  });
  wrap.appendChild(statusHolder);
  return wrap;
}

/* ======================================================================
   CONVERTISSEUR D'UNITÉS (indépendant de toute recette)
   Toutes les unités passent par un facteur d'équivalence en grammes
   (même approche que la version bureau) : simple et pratique pour une
   estimation rapide, sans prétendre à une conversion parfaite volume/
   poids qui dépendrait de la densité de chaque ingrédient.
   ====================================================================== */
const CONVERTER_UNIT_KEYS = [
  ["unitconv_gram", 1.0],
  ["unitconv_kilogram", 1000.0],
  ["unitconv_ounce", 28.35],
  ["unitconv_pound", 453.6],
  ["unitconv_milliliter", 1.0],
  ["unitconv_centiliter", 10.0],
  ["unitconv_liter", 1000.0],
  ["unitconv_teaspoon", 5.0],
  ["unitconv_tablespoon", 15.0],
  ["unitconv_cup", 240.0],
];

/* ======================================================================
   CORBEILLE
   Une recette supprimée passe d'abord par ici, récupérable, plutôt que
   d'être effacée immédiatement et définitivement.
   ====================================================================== */
async function moveRecipeToTrash(recipe) {
  const entry = { ...recipe, deletedAt: new Date().toISOString() };
  await storePut("trash", entry);
  await storeDelete("recipes", recipe.id);
  state.trash.unshift(entry);
  state.recipes = state.recipes.filter((r) => r.id !== recipe.id);
}
async function restoreRecipeFromTrash(entry) {
  const { deletedAt, ...recipe } = entry;
  await storePut("recipes", recipe);
  await storeDelete("trash", entry.id);
  state.recipes.push(recipe);
  state.trash = state.trash.filter((x) => x.id !== entry.id);
}
async function deleteFromTrashForever(id) {
  await storeDelete("trash", id);
  state.trash = state.trash.filter((x) => x.id !== id);
}

function renderTrash() {
  const wrap = el(`<div></div>`);
  if (!state.trash.length) {
    wrap.appendChild(el(`<div class="empty-state"><div class="emoji">🗑️</div><p>${escapeHtml(t("trash_empty"))}</p></div>`));
    return wrap;
  }
  state.trash.forEach((entry) => {
    const dateStr = localeDateStr(entry.deletedAt);
    const card = el(`<div class="card" style="padding:14px 16px;margin-bottom:12px;">
      <div style="font-weight:600;margin-bottom:2px;">${escapeHtml(entry.name)}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">${escapeHtml(t("trash_deleted_on", { date: dateStr }))}</div>
      <div class="modal-actions" style="margin-top:0;">
        <button type="button" class="btn btn-outline btn-sm del-forever">${t("trash_delete_forever_button")}</button>
        <button type="button" class="btn btn-primary btn-sm restore">${t("trash_restore_button")}</button>
      </div>
    </div>`);
    card.querySelector(".restore").addEventListener("click", async () => {
      await restoreRecipeFromTrash(entry);
      render();
    });
    card.querySelector(".del-forever").addEventListener("click", async () => {
      if (!await customConfirm(t("trash_delete_forever_confirm"))) return;
      await deleteFromTrashForever(entry.id);
      render();
    });
    wrap.appendChild(card);
  });
  const emptyAllBtn = el(`<button class="btn btn-danger" style="margin-top:8px;">${t("trash_empty_all_button")}</button>`);
  emptyAllBtn.addEventListener("click", async () => {
    if (!await customConfirm(t("trash_empty_all_confirm"))) return;
    await storeClear("trash");
    state.trash = [];
    render();
  });
  wrap.appendChild(emptyAllBtn);
  return wrap;
}

function renderUnitConverter() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 20px;line-height:1.5;">${escapeHtml(t("unitconv_intro"))}</p>`));

  wrap.appendChild(el(`<div class="field">
    <label for="conv-qty">${t("unitconv_quantity_label")}</label>
    <input type="number" step="any" id="conv-qty" value="1">
  </div>`));

  const fromField = el(`<div class="field"><label for="conv-from">${t("unitconv_from_label")}</label><select id="conv-from"></select></div>`);
  const toField = el(`<div class="field"><label for="conv-to">${t("unitconv_to_label")}</label><select id="conv-to"></select></div>`);
  const fromSelect = fromField.querySelector("select");
  const toSelect = toField.querySelector("select");
  CONVERTER_UNIT_KEYS.forEach(([key]) => {
    fromSelect.appendChild(el(`<option value="${key}">${escapeHtml(t(key))}</option>`));
    toSelect.appendChild(el(`<option value="${key}">${escapeHtml(t(key))}</option>`));
  });
  fromSelect.value = CONVERTER_UNIT_KEYS[0][0];
  toSelect.value = CONVERTER_UNIT_KEYS[1][0];
  wrap.appendChild(fromField);
  wrap.appendChild(toField);

  const convertBtn = el(`<button class="btn btn-primary" style="margin-top:6px;">${t("unitconv_convert_button")}</button>`);
  const resultHolder = el(`<div style="margin-top:16px;font-size:18px;font-weight:700;color:var(--primary);text-align:center;"></div>`);

  function doConvert() {
    const qtyRaw = wrap.querySelector("#conv-qty").value.trim().replace(",", ".");
    const quantity = parseFloat(qtyRaw);
    if (Number.isNaN(quantity)) {
      resultHolder.textContent = t("unitconv_error_invalid_quantity");
      return;
    }
    const fromEntry = CONVERTER_UNIT_KEYS.find(([key]) => key === fromSelect.value);
    const toEntry = CONVERTER_UNIT_KEYS.find(([key]) => key === toSelect.value);
    const grams = quantity * fromEntry[1];
    let result = grams / toEntry[1];
    result = Math.round(result * 1000) / 1000;
    if (Number.isInteger(result)) result = result; // reste tel quel, juste pour lisibilité
    resultHolder.textContent = t("unitconv_result", {
      quantity: fmtQty(quantity),
      from_unit: t(fromEntry[0]),
      result: fmtQty(result),
      to_unit: t(toEntry[0]),
    });
  }
  convertBtn.addEventListener("click", doConvert);
  wrap.appendChild(convertBtn);
  wrap.appendChild(resultHolder);
  doConvert();
  return wrap;
}

/* ======================================================================
   "QUE PUIS-JE CUISINER ?"
   Repris du garde-manger comme point de départ pratique, mais modifiable
   librement pour cette vérification précise sans toucher au vrai
   garde-manger.
   ====================================================================== */
function renderWhatCanICook() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;line-height:1.5;">${escapeHtml(t("whatcancook_hint"))}</p>`));

  if (!state.whatCanICookIngredients) {
    const fromPantry = state.pantry.map((p) => p.name);
    const combined = fromPantry.slice();
    PANTRY_STAPLES.forEach((staple) => {
      if (!combined.some((n) => normalize(n) === normalize(staple))) combined.push(staple);
    });
    state.whatCanICookIngredients = combined;
  }

  const chipsHolder = el(`<div class="chip-row" style="flex-wrap:wrap;"></div>`);
  const resultsHolder = el(`<div id="whatcancook-results"></div>`);

  function fillChips() {
    chipsHolder.innerHTML = "";
    state.whatCanICookIngredients.forEach((name) => {
      const chip = el(`<button class="chip active">${escapeHtml(translateIngredientName(name))} ✕</button>`);
      chip.addEventListener("click", () => {
        state.whatCanICookIngredients = state.whatCanICookIngredients.filter((n) => n !== name);
        fillChips();
        fillResults();
      });
      chipsHolder.appendChild(chip);
    });
  }
  fillChips();
  wrap.appendChild(chipsHolder);

  const addField = el(`<div class="field">
    <label for="whatcancook-add">${t("whatcancook_add_ingredient")}</label>
    <div class="autocomplete-wrap"><input type="text" id="whatcancook-add"></div>
  </div>`);
  const addInput = addField.querySelector("input");
  let pendingValue = "";
  attachIngredientAutocomplete(addInput, (value) => (pendingValue = value));
  addInput.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const value = resolveIngredientInput((pendingValue || addInput.value).trim());
    if (value && !state.whatCanICookIngredients.some((n) => normalize(n) === normalize(value))) {
      state.whatCanICookIngredients.push(value);
      addInput.value = "";
      pendingValue = "";
      fillChips();
      fillResults();
    }
  });
  wrap.appendChild(addField);

  function fillResults() {
    resultsHolder.innerHTML = "";
    if (!state.whatCanICookIngredients.length) {
      resultsHolder.appendChild(el(`<div class="empty-state" style="padding:20px 0;"><p>${escapeHtml(t("whatcancook_no_ingredients"))}</p></div>`));
      return;
    }
    const haveSet = new Set(state.whatCanICookIngredients.map((n) => normalize(n)));
    const scored = state.recipes.map((r) => {
      const ings = r.ingredients || [];
      const missing = ings.filter((ing) => !haveSet.has(normalize(ing.name)));
      const haveCount = ings.length - missing.length;
      return { recipe: r, total: ings.length, have: haveCount, missing };
    }).filter((s) => s.total > 0 && s.have > 0);
    scored.sort((a, b) => (b.have / b.total) - (a.have / a.total));

    if (!scored.length) {
      resultsHolder.appendChild(el(`<div class="empty-state" style="padding:20px 0;"><p>${escapeHtml(t("whatcancook_no_matches"))}</p></div>`));
      return;
    }
    scored.forEach(({ recipe, total, have, missing }) => {
      const isFeasible = have === total;
      const row = el(`<button class="card recipe-row" style="margin-bottom:10px;">
        <div class="recipe-thumb">${recipe.photo ? `<img src="${recipe.photo}" alt="">` : "🍽️"}</div>
        <div class="recipe-info">
          <div class="recipe-name">${escapeHtml(recipe.name)}</div>
          <div class="recipe-meta">${isFeasible ? escapeHtml(t("whatcancook_feasible")) : escapeHtml(t("whatcancook_almost", { have: String(have), total: String(total) }))}</div>
          ${!isFeasible ? `<div style="font-size:12px;color:var(--text-muted);margin-top:2px;">${escapeHtml(t("whatcancook_missing", { list: missing.map((m) => translateIngredientName(m.name)).join(", ") }))}</div>` : ""}
        </div>
      </button>`);
      row.addEventListener("click", () => {
        state.currentRecipeId = recipe.id;
        state.viewPersons = recipe.defaultPersons || 4;
        state.screen = "recipe";
        render();
      });
      resultsHolder.appendChild(row);
    });
  }
  fillResults();
  wrap.appendChild(el(`<div class="section-label" style="margin-top:20px;">${t("nav_recipes")}</div>`));
  wrap.appendChild(resultsHolder);

  return wrap;
}

/* ======================================================================
   STATISTIQUES
   Adapté du bureau : la note en étoiles et les tags n'existent pas sur
   mobile, donc remplacés par ce qui est réellement disponible ici
   (coût, calories, historique de cuisine).
   ====================================================================== */
function computeRecipeCostPerPerson(ingredients) {
  let total = 0, known = 0;
  (ingredients || []).forEach((ing) => {
    if (ing.quantity == null) return;
    const cost = computeIngredientCost(ing.name, ing.quantity, ing.unit);
    if (cost == null) return;
    total += cost;
    known++;
  });
  return known ? total : null;
}

function renderStatistics() {
  const wrap = el(`<div></div>`);
  const recipes = state.recipes;
  if (!recipes.length) {
    wrap.appendChild(el(`<div class="empty-state"><div class="emoji">📊</div><p>${escapeHtml(t("stats_empty"))}</p></div>`));
    return wrap;
  }

  function section(title) {
    wrap.appendChild(el(`<div class="section-label" style="margin-top:20px;">${escapeHtml(title)}</div>`));
  }
  function card() {
    const c = el(`<div class="card" style="padding:2px 16px;"></div>`);
    wrap.appendChild(c);
    return c;
  }
  function line(text) {
    return el(`<div class="ingredient-item"><span>${escapeHtml(text)}</span></div>`);
  }

  wrap.appendChild(el(`<p style="font-weight:700;font-size:18px;margin:0 0 16px;">${escapeHtml(t("stats_total_recipes", { count: String(recipes.length) }))}</p>`));

  section(t("stats_by_category"));
  const catCard = card();
  const catCounts = {};
  recipes.forEach((r) => { const c = r.category || "Autre"; catCounts[c] = (catCounts[c] || 0) + 1; });
  CATEGORY_OPTIONS.forEach((cat) => {
    if (catCounts[cat]) catCard.appendChild(line(`${translateCategory(cat)} : ${catCounts[cat]}`));
  });

  section(t("stats_by_difficulty"));
  const diffCard = card();
  const diffCounts = {};
  recipes.forEach((r) => { const d = r.difficulty || "Facile"; diffCounts[d] = (diffCounts[d] || 0) + 1; });
  DIFFICULTY_OPTIONS.forEach((diff) => {
    if (diffCounts[diff]) diffCard.appendChild(line(`${translateDifficulty(diff)} : ${diffCounts[diff]}`));
  });

  const favCount = recipes.filter((r) => r.favorite).length;
  wrap.appendChild(el(`<p style="margin:16px 0 0;font-size:14px;">${escapeHtml(t("stats_favorites_count", { count: String(favCount) }))}</p>`));

  section(t("stats_most_cooked_heading"));
  const cookedCard = card();
  const cooked = recipes.filter((r) => (r.timesCooked || 0) > 0).sort((a, b) => (b.timesCooked || 0) - (a.timesCooked || 0));
  if (cooked.length) {
    cooked.slice(0, 10).forEach((r) => cookedCard.appendChild(line(t("stats_cooked_line", { name: r.name, count: String(r.timesCooked) }))));
  } else {
    cookedCard.appendChild(line(t("stats_none_cooked_yet")));
  }

  const neverCooked = recipes.filter((r) => !(r.timesCooked > 0));
  section(t("stats_never_cooked_heading", { count: String(neverCooked.length) }));
  const neverCard = card();
  if (neverCooked.length) {
    neverCooked.slice(0, 15).forEach((r) => neverCard.appendChild(line(r.name)));
    if (neverCooked.length > 15) neverCard.appendChild(line(t("stats_and_others", { count: String(neverCooked.length - 15) })));
  } else {
    neverCard.appendChild(line(t("stats_all_cooked")));
  }

  const STALE_DAYS = 90;
  const now = Date.now();
  const stale = [];
  recipes.forEach((r) => {
    if (!r.cookLog || !r.cookLog.length) return;
    const lastDate = r.cookLog.reduce((max, entry) => Math.max(max, new Date(entry.date).getTime()), 0);
    const days = Math.floor((now - lastDate) / 86400000);
    if (days >= STALE_DAYS) stale.push({ recipe: r, days });
  });
  stale.sort((a, b) => b.days - a.days);
  section(t("stats_stale_heading", { days: String(STALE_DAYS) }));
  const staleCard = card();
  if (stale.length) {
    stale.slice(0, 15).forEach(({ recipe, days }) => staleCard.appendChild(line(t("stats_stale_line", { name: recipe.name, days: String(days) }))));
  } else {
    staleCard.appendChild(line(t("stats_no_stale_recipe")));
  }

  section(t("stats_avg_cost_heading"));
  const costCard = card();
  const costs = [];
  recipes.forEach((r) => {
    const cost = computeRecipeCostPerPerson(r.ingredients);
    if (cost != null) costs.push(cost);
  });
  if (costs.length) {
    const avg = costs.reduce((s, c) => s + c, 0) / costs.length;
    costCard.appendChild(line(t("stats_avg_cost_line", { avg: fmtQty(Math.round(avg * 100) / 100), count: String(costs.length) })));
  } else {
    costCard.appendChild(line(t("stats_no_priced_recipe")));
  }

  section(t("stats_avg_kcal_heading"));
  const kcalCard = card();
  const kcals = [];
  recipes.forEach((r) => {
    const nutrition = computeRecipeNutrition(r.ingredients);
    if (nutrition) kcals.push(nutrition.kcal);
  });
  if (kcals.length) {
    const avg = kcals.reduce((s, k) => s + k, 0) / kcals.length;
    kcalCard.appendChild(line(t("stats_avg_kcal_line", { avg: String(Math.round(avg)), count: String(kcals.length) })));
  } else {
    kcalCard.appendChild(line(t("stats_no_recognized_recipe")));
  }

  section(t("stats_monthly_chart_title"));
  const monthCounts = {};
  recipes.forEach((r) => {
    (r.cookLog || []).forEach((entry) => {
      const d = new Date(entry.date);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      monthCounts[key] = (monthCounts[key] || 0) + 1;
    });
  });
  const months = [];
  const refDate = new Date();
  for (let i = 11; i >= 0; i--) {
    const d = new Date(refDate.getFullYear(), refDate.getMonth() - i, 1);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    months.push({ key, label: d.toLocaleDateString(CURRENT_LANG, { month: "short" }), count: monthCounts[key] || 0 });
  }
  const maxCount = Math.max(1, ...months.map((m) => m.count));
  const chartCard = el(`<div class="card" style="padding:16px 10px 10px;display:flex;align-items:flex-end;gap:4px;height:150px;"></div>`);
  months.forEach((m) => {
    const barWrap = el(`<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;"></div>`);
    const bar = el(`<div style="width:100%;background:var(--primary);border-radius:3px 3px 0 0;height:${Math.max(2, (m.count / maxCount) * 90)}px;" title="${m.count}"></div>`);
    const label = el(`<div style="font-size:9px;color:var(--text-muted);margin-top:4px;">${escapeHtml(m.label)}</div>`);
    barWrap.appendChild(bar);
    barWrap.appendChild(label);
    chartCard.appendChild(barWrap);
  });
  wrap.appendChild(chartCard);

  return wrap;
}

// À incrémenter à chaque livraison, en même temps que CACHE_NAME dans
// sw.js — affiché sur l'écran de sauvegarde pour vérifier facilement,
// sans deviner, que la dernière version est bien celle actuellement
// utilisée.
const APP_VERSION = 161;

async function init() {
  applyTheme(localStorage.getItem("theme") || "light");
  await loadPantryClaims();

  // Capture un brouillon de la recette en cours de création si
  // l'application passe en arrière-plan ou se ferme — plus fiable que
  // "beforeunload" sur mobile, qui ne se déclenche pas toujours de
  // façon cohérente en changeant d'application.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") captureRecipeFormDraft();
  });

  if ("serviceWorker" in navigator) {
    // Une vraie mise à jour a eu lieu seulement si un contrôleur existait
    // déjà avant ce changement (sinon, c'est juste la toute première
    // prise de contrôle au premier lancement, pas une nouvelle version).
    let hadControllerBefore = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (hadControllerBefore) {
        state.updateAvailable = true;
        render();
      }
      hadControllerBefore = true;
    });
    try {
      const registration = await navigator.serviceWorker.register("./sw.js");
      // Force une vérification de nouvelle version à chaque ouverture de
      // l'application, plutôt que d'attendre la vérification automatique
      // et différée du navigateur — pour que les corrections arrivent
      // plus vite après une mise à jour du dépôt.
      registration.update().catch(() => {});
    } catch (e) { /* ignore */ }
  }

  // Réduit (sans l'éliminer) le risque que le navigateur efface les
  // données automatiquement par manque d'espace — ne protège pas contre
  // un effacement volontaire des données du site par l'utilisateur,
  // d'où l'intérêt des rappels et boutons de sauvegarde par ailleurs.
  if (navigator.storage && navigator.storage.persist) {
    navigator.storage.persist().catch(() => {});
  }

  await loadReferenceData();

  state.recipes = await storeAll("recipes");
  state.shopping = await storeAll("shopping");
  state.pantry = await storeAll("pantry");
  state.menus = await storeAll("menus");
  state.planTemplates = await storeAll("planTemplates");
  state.planHistory = (await storeAll("planHistory")).sort((a, b) => b.date.localeCompare(a.date));
  state.trash = (await storeAll("trash")).sort((a, b) => (b.deletedAt || "").localeCompare(a.deletedAt || ""));
  state.savedShoppingLists = await storeAll("savedShoppingLists");
  const savedPlan = await kvGet("weeklyPlan");
  state.weeklyPlan = savedPlan || {};
  await ensureIngredientListLoaded();
  await loadIngredientOverrides();
  await loadDismissedPairs();

  // Raccourcis PWA (appui long sur l'icône de l'application) : ouvre
  // directement l'écran demandé au lancement, plutôt que de toujours
  // démarrer sur l'accueil.
  const requestedScreen = new URLSearchParams(location.search).get("screen");
  if (requestedScreen) {
    // Retire le paramètre de l'adresse une fois lu — sinon, une simple
    // actualisation de la page rouvrait indéfiniment le même écran au
    // lieu de respecter la navigation normale de l'utilisateur.
    history.replaceState(null, "", location.pathname);
  }
  if (requestedScreen === "form") {
    await openRecipeForm(null); // gère déjà son propre appel à render()
    return;
  }
  if (requestedScreen === "shopping") {
    state.screen = "shopping";
  }

  render();
}

init();
