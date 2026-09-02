"use strict";

/* ======================================================================
   BASE DE DONNÉES LOCALE (IndexedDB)
   Toutes les données restent sur l'appareil, rien n'est envoyé nulle
   part. Trois entrepôts : recettes, liste de courses, réglages.
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

/* ======================================================================
   ÉTAT DE L'APPLICATION
   ====================================================================== */
const state = {
  screen: "home", // home | recipes | recipe | form | shopping | pantry
  recipes: [],
  shopping: [],
  pantry: [],
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
};

const CATEGORY_OPTIONS = ["Petit-déjeuner", "Entrée", "Plat", "Dessert", "Apéro", "Boisson", "Sauce", "Autre"];
const DIFFICULTY_OPTIONS = ["Facile", "Moyen", "Difficile"];
const UNIT_OPTIONS = ["pièce", "g", "kg", "cl", "L", "c. à soupe", "c. à café", "autre"];

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
function fmtQty(qty) {
  if (qty == null || qty === "") return "";
  const n = Number(qty);
  if (Number.isNaN(n)) return qty;
  return n % 1 === 0 ? String(n) : String(Math.round(n * 100) / 100).replace(".", ",");
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

function render() {
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
    const btn = el(`<button class="nav-item ${active ? "active" : ""}">
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
  if (!isRunningStandalone() && (deferredInstallPrompt || isIosDevice())) {
    const installBtn = el(`<button class="btn btn-secondary" style="margin-bottom:14px;">${t("home_install_button")}</button>`);
    installBtn.addEventListener("click", triggerInstall);
    wrap.appendChild(installBtn);
  }
  wrap.appendChild(el(`<div class="section"><h2 class="display" style="font-size:22px;">${t("home_title")}</h2></div>`));

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
  const importQrPasteBtn = el(`<button class="btn btn-outline" style="margin-bottom:10px;">${t("home_qr_paste_button")}</button>`);
  importQrPasteBtn.addEventListener("click", () => openQrPasteModal());
  importActions.appendChild(importUrlBtn);
  importActions.appendChild(importPhotoBtn);
  importActions.appendChild(importQrBtn);
  importActions.appendChild(importQrPasteBtn);
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
    <div class="recipe-meta">${escapeHtml(translateCategory(recipe.category))}${recipe.prepTime || recipe.cookTime ? " · " + ((Number(recipe.prepTime) || 0) + (Number(recipe.cookTime) || 0)) + " " + t("recipe_min") : ""}</div>
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
    <input type="search" placeholder="${t("search_placeholder")}" />
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
  const delBtn = el(`<button class="btn btn-danger">${t("recipe_delete")}</button>`);
  delBtn.addEventListener("click", async () => {
    if (confirm(t("recipe_delete_confirm"))) {
      await moveRecipeToTrash(r);
      state.screen = "recipes";
      render();
    }
  });
  editRow.appendChild(editBtn);
  editRow.appendChild(delBtn);
  wrap.appendChild(editRow);

  return wrap;
}

/* ======================================================================
   ÉCRAN : FORMULAIRE RECETTE (ajout / modification)
   ====================================================================== */
function openRecipeForm(recipeId) {
  state.editingRecipeId = recipeId;
  if (recipeId) {
    const r = state.recipes.find((x) => x.id === recipeId);
    state.formIngredients = (r.ingredients || []).map((i) => ({ ...i }));
    state.formPhoto = r.photo || null;
    state.formAllergens = (r.allergens || []).slice();
  } else {
    state.formIngredients = [{ name: "", quantity: "", unit: "pièce" }];
    state.formPhoto = null;
    state.formAllergens = [];
  }
  state.screen = "form";
  render();
}

function renderRecipeForm() {
  const r = state.editingRecipeId ? state.recipes.find((x) => x.id === state.editingRecipeId) : null;
  // Pré-remplissage à usage unique venant de l'import depuis un lien
  // (ne s'applique jamais en modification d'une recette existante).
  const prefill = !r && state._importPrefill ? state._importPrefill : null;
  state._importPrefill = null;
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
    <input type="text" id="f-name" placeholder="${t("form_name_placeholder")}" value="${escapeHtml(r ? r.name : (prefill ? prefill.name : ""))}">
  </div>`));

  const row1 = el(`<div class="field-row"></div>`);
  const catField = el(`<div class="field"><label for="f-category">${t("form_category")}</label><select id="f-category"></select></div>`);
  const catSelect = catField.querySelector("select");
  CATEGORY_OPTIONS.forEach((c) => catSelect.appendChild(el(`<option value="${c}">${escapeHtml(translateCategory(c))}</option>`)));
  if (r) catSelect.value = r.category;
  else if (prefill && prefill.category) catSelect.value = prefill.category;
  row1.appendChild(catField);
  const diffField = el(`<div class="field"><label for="f-difficulty">${t("form_difficulty")}</label><select id="f-difficulty"></select></div>`);
  const diffSelect = diffField.querySelector("select");
  DIFFICULTY_OPTIONS.forEach((d) => diffSelect.appendChild(el(`<option value="${d}">${escapeHtml(translateDifficulty(d))}</option>`)));
  if (r) diffSelect.value = r.difficulty || "Facile";
  row1.appendChild(diffField);
  wrap.appendChild(row1);

  const row2 = el(`<div class="field-row"></div>`);
  row2.appendChild(el(`<div class="field"><label for="f-persons">${t("form_persons")}</label><input type="number" min="1" id="f-persons" value="${r ? r.defaultPersons : (prefill ? prefill.persons : 4)}"></div>`));
  row2.appendChild(el(`<div class="field"><label for="f-prep">${t("form_prep_time")}</label><input type="number" min="0" id="f-prep" value="${r && r.prepTime ? r.prepTime : (prefill && prefill.prepTime ? prefill.prepTime : "")}"></div>`));
  row2.appendChild(el(`<div class="field"><label for="f-cook">${t("form_cook_time")}</label><input type="number" min="0" id="f-cook" value="${r && r.cookTime ? r.cookTime : (prefill && prefill.cookTime ? prefill.cookTime : "")}"></div>`));
  wrap.appendChild(row2);

  const checks = el(`<div class="card" style="padding:2px 14px;margin-bottom:20px;">
    <div class="checkbox-row"><input type="checkbox" id="f-favorite" ${r && r.favorite ? "checked" : ""}><label for="f-favorite">${t("form_favorite")}</label></div>
    <div class="checkbox-row"><input type="checkbox" id="f-vegetarian" ${r && r.vegetarian ? "checked" : ""}><label for="f-vegetarian">${t("form_vegetarian")}</label></div>
    <div class="checkbox-row"><input type="checkbox" id="f-wishlist" ${r && r.wishlist ? "checked" : ""}><label for="f-wishlist">${t("form_wishlist")}</label></div>
  </div>`);
  wrap.appendChild(checks);

  const ingSection = el(`<div class="section"><div class="section-label">${t("form_ingredients")}</div>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 12px;line-height:1.4;">${escapeHtml(t("form_ingredients_hint"))}</p>
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
  renderAllergenCheckboxes(allergenHolder);

  wrap.appendChild(el(`<div class="field">
    <label for="f-description">${t("form_description")}</label>
    <textarea id="f-description">${escapeHtml(r ? r.description || "" : (prefill ? prefill.description : ""))}</textarea>
  </div>`));
  wrap.appendChild(el(`<div class="field">
    <label for="f-notes">${t("form_notes")}</label>
    <textarea id="f-notes">${escapeHtml(r ? r.notes || "" : "")}</textarea>
  </div>`));

  const submitBtn = el(`<button type="submit" class="btn btn-primary" style="margin-bottom:10px;">${t("form_save")}</button>`);
  const cancelBtn = el(`<button type="button" class="btn btn-outline">${t("form_cancel")}</button>`);
  cancelBtn.addEventListener("click", () => {
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
      <div class="autocomplete-wrap"><input type="text" class="ing-name" placeholder="${t("form_ingredient_name")}" value="${escapeHtml(translateIngredientName(ing.name))}"></div>
      <input type="number" step="any" class="qty ing-qty" placeholder="${t("form_ingredient_qty")}" value="${ing.quantity || ""}">
      <select class="ing-unit"></select>
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
  if (!name) { alert(t("form_error_name")); return; }
  const validIngredients = state.formIngredients
    .map((i) => ({ name: resolveIngredientInput((i.name || "").trim()), quantity: parseQtyOrNull(i.quantity), unit: i.unit }))
    .filter((i) => i.name);
  if (!validIngredients.length) { alert(t("form_error_ingredient")); return; }

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
    photo: state.formPhoto,
    createdAt: existing ? existing.createdAt : new Date().toISOString(),
  };
  await storePut("recipes", recipe);
  const idx = state.recipes.findIndex((x) => x.id === recipe.id);
  if (idx >= 0) state.recipes[idx] = recipe; else state.recipes.push(recipe);

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
  await addRecipeToShoppingSilent(recipe, persons);
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
  wrap.appendChild(el(`<div class="progress-bar-track"><div class="progress-bar-fill" style="width:${totalCount ? (checked / totalCount) * 100 : 0}%"></div></div>`));

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
    const name = prompt(t("shopping_save_list_prompt"));
    if (!name || !name.trim()) return;
    const saved = { id: uid(), name: name.trim(), items: JSON.parse(JSON.stringify(state.shopping)), createdAt: new Date().toISOString() };
    await storePut("savedShoppingLists", saved);
    state.savedShoppingLists.push(saved);
    render();
  });
  wrap.appendChild(saveListBtn);

  const clearBtn = el(`<button class="btn btn-danger" style="margin-top:10px;">${t("shopping_clear")}</button>`);
  clearBtn.addEventListener("click", async () => {
    if (confirm(t("shopping_clear_confirm"))) {
      await storeClear("shopping");
      state.shopping = [];
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
      if (state.shopping.length && !confirm(t("shopping_load_list_confirm"))) return;
      await storeClear("shopping");
      const items = JSON.parse(JSON.stringify(saved.items)).map((i) => ({ ...i, id: uid() }));
      for (const item of items) await storePut("shopping", item);
      state.shopping = items;
      state.screen = "shopping";
      render();
    });
    card.querySelector(".del").addEventListener("click", async () => {
      if (!confirm(t("shopping_delete_list_confirm"))) return;
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
    <span class="label">${escapeHtml(translateIngredientName(item.name))}${item.quantity != null ? " — " + fmtQty(item.quantity) + " " + escapeHtml(translateUnit(item.unit)) : ""}</span>
  </div>`);
  row.querySelector("input").addEventListener("change", async (e) => {
    item.checked = e.target.checked;
    await storePut("shopping", item);
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
    const item = {
      id: isEdit ? existingItem.id : uid(),
      name,
      quantity: parseQtyOrNull(sheet.querySelector("#modal-ing-qty").value),
      unit: unitSelect.value,
    };
    if (storeName === "shopping") item.checked = isEdit ? existingItem.checked : false;
    if (isPantry) item.threshold = parseQtyOrNull(sheet.querySelector("#modal-ing-threshold").value);
    await storePut(storeName, item);
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
    return wrap;
  }
  const list = el(`<div class="card" style="padding:4px 16px;"></div>`);
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
        render();
      });
      list.appendChild(row);
    });
  wrap.appendChild(list);
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
    <input type="search" placeholder="${t("ingredient_search_placeholder")}" />
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
        if (confirm(t("ingredient_delete_confirm", { name }))) {
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
    <input type="search" placeholder="${t("manage_substitutions_search_placeholder")}" />
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
    ).sort((a, b) => a.localeCompare(b, "fr"));
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
        <div class="autocomplete-wrap" style="flex:1;"><input type="text" class="sub-name" placeholder="${t("ingredient_substitute_name_placeholder")}" value="${escapeHtml(sub.nom)}"></div>
        <input type="text" class="sub-note" placeholder="${t("ingredient_substitute_note_placeholder")}" value="${escapeHtml(sub.note || "")}" style="flex:1.4;">
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
        alert(t("ingredient_already_exists"));
        return;
      }
      if (value !== existingName) await renameIngredientName(existingName, value);
    } else {
      if (state.ingredientNames.some((n) => normalize(n) === normalize(value))) {
        alert(t("ingredient_already_exists"));
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
  }

  doc.setFontSize(8);
  doc.setTextColor(150);
  doc.text(t("pdf_generated_by"), margin, 290);
  doc.setTextColor(0);
}

function exportRecipePdf(recipe, persons) {
  if (!window.jspdf) {
    alert(t("backup_import_error"));
    return;
  }
  const includePhoto = recipe.photo ? confirm(t("pdf_include_photo_confirm")) : false;
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const margin = 20;
  const maxWidth = doc.internal.pageSize.getWidth() - margin * 2;

  drawRecipeContent(doc, recipe, persons, margin, maxWidth, includePhoto);

  const safeName = recipe.name.replace(/[^\w\s-]/g, "").trim() || "recette";
  doc.save(`${safeName}.pdf`);
}

function exportShoppingListPdf() {
  if (!window.jspdf) {
    alert(t("backup_import_error"));
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
  doc.save("liste-de-courses.pdf");
}

// Génère un seul PDF regroupant plusieurs recettes : une page de garde,
// un sommaire, puis une recette par page (ou plus si elle est longue).
// Les numéros de page du sommaire sont remplis après coup, une fois que
// la vraie page de chaque recette est connue (chaque recette démarre
// toujours sur une page neuve, ce qui rend ce numéro prévisible).
function exportCookbookPdf(recipes, includePhotos) {
  if (!window.jspdf) {
    alert(t("backup_import_error"));
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
  doc.text(new Date().toLocaleDateString(), margin, 125);
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

  doc.save("mon-livre-de-recettes.pdf");
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
  exportBtn.addEventListener("click", () => {
    if (!selected.size) { alert(t("cookbook_no_selection")); return; }
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
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.0.3/qrcode.min.js";
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
  // Sans ce réglage, la bibliothèque n'encode pas en UTF-8 par défaut et
  // corrompt les caractères accentués (é, è, à...) — ce qui cassait la
  // reconnaissance automatique du mot "Ingrédients" au moment du scan.
  if (window.qrcode.stringToBytesFuncs && window.qrcode.stringToBytesFuncs["UTF-8"]) {
    window.qrcode.stringToBytes = window.qrcode.stringToBytesFuncs["UTF-8"];
  }
  let lastError = null;
  for (let typeNumber = 1; typeNumber <= 40; typeNumber++) {
    try {
      const qr = window.qrcode(typeNumber, "M");
      qr.addData(text);
      qr.make();
      return qr.createImgTag(5, 4);
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError || new Error("qrcode_generation_failed");
}

async function openQrCodeModal(recipe, persons) {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("qrcode_title")}</h2>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("qrcode_hint"))}</p>
    <div id="qrcode-canvas-holder" style="display:flex;justify-content:center;margin-bottom:20px;min-height:240px;align-items:center;text-align:center;"><span style="font-size:13px;color:var(--text-muted);">${escapeHtml(t("qrcode_loading"))}</span></div>
    <div class="modal-actions">
      <button type="button" class="btn btn-outline" id="qrcode-close">${t("cooking_close")}</button>
      <button type="button" class="btn btn-primary" id="qrcode-save">${t("qrcode_save_button")}</button>
    </div>
  </div>`);
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);

  const lines = [recipe.name, ""];
  if (recipe.prepTime) lines.push(`${t("pdf_prep_label")} : ${recipe.prepTime} ${t("recipe_min")}`);
  if (recipe.cookTime) lines.push(`${t("pdf_cook_label")} : ${recipe.cookTime} ${t("recipe_min")}`);
  if (recipe.allergens && recipe.allergens.length) {
    lines.push(`${t("recipe_allergens")} : ${recipe.allergens.map(translateAllergen).join(", ")}`);
  }
  lines.push("", t("qrcode_ingredients_heading", { persons: String(persons) }));
  (recipe.ingredients || []).forEach((ing) => {
    const scaled = ing.quantity != null ? ing.quantity * persons : null;
    const qty = scaled != null ? `${fmtQty(scaled)} ${translateUnit(ing.unit)} ` : "";
    lines.push(`- ${qty}${translateIngredientName(ing.name)}`);
  });
  let content = lines.join("\n");
  // Un QR code a une capacité limitée : au-delà d'une certaine taille, il
  // devient soit impossible à générer, soit trop dense pour être scanné
  // de façon fiable — on tronque proprement plutôt que d'échouer.
  const MAX_QR_LENGTH = 800;
  if (content.length > MAX_QR_LENGTH) content = content.slice(0, MAX_QR_LENGTH - 1) + "…";

  const holder = sheet.querySelector("#qrcode-canvas-holder");
  try {
    await loadQrCodeLib();
    holder.innerHTML = generateQrCodeImgTag(content);
  } catch (e) {
    holder.innerHTML = `<div><span style="font-size:13px;color:var(--danger);">${escapeHtml(t("qrcode_load_error"))}</span><div style="font-size:11px;color:var(--text-muted);margin-top:6px;word-break:break-word;">${escapeHtml((e && e.name ? e.name + " — " : "") + (e && e.message ? e.message : String(e)))}</div></div>`;
  }

  sheet.querySelector("#qrcode-close").addEventListener("click", () => overlay.remove());
  sheet.querySelector("#qrcode-save").addEventListener("click", () => {
    const img = holder.querySelector("img");
    if (!img) return;
    const safeName = (recipe.name || "recette").replace(/[^\w\s-]/g, "").trim() || "recette";
    const link = document.createElement("a");
    link.download = `${safeName}-qrcode.png`;
    link.href = img.src;
    link.click();
  });
}

/* ======================================================================
   PARTAGE DE LA LISTE DE COURSES VIA QR CODE
   Format compact (pas du JSON, pour maximiser ce qui tient dans un seul
   QR code) : une ligne d'en-tête pour identifier le format, puis une
   ligne par article "nom|quantité|unité|coché".
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
function parseRecipeFromQrText(text) {
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
  // le temps de préparation/cuisson et les allergènes, si présents à la
  // génération — recherche tolérante (accepte français et anglais).
  let prepTime = null, cookTime = null, allergens = [];
  lines.slice(1, ingIdx).forEach((line) => {
    const prepMatch = line.match(/pr[eé]paration\s*:\s*(\d+)/i) || line.match(/prep(?:aration)?\s*time\s*:\s*(\d+)/i);
    if (prepMatch) prepTime = parseInt(prepMatch[1], 10);
    const cookMatch = line.match(/cuisson\s*:\s*(\d+)/i) || line.match(/cook\s*time\s*:\s*(\d+)/i);
    if (cookMatch) cookTime = parseInt(cookMatch[1], 10);
    const allergenMatch = line.match(/allerg[eè]nes?\s*:\s*(.+)/i);
    if (allergenMatch) allergens = allergenMatch[1].split(",").map((a) => a.trim()).filter(Boolean);
  });

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
  return { name, ingredients, prepTime, cookTime, allergens, persons };
}

// Retire des articles (depuis la fin) jusqu'à ce que le contenu tienne
// dans la capacité d'un QR code, plutôt que de couper au milieu d'une
// ligne et casser le format.
function buildTruncatedShoppingQrContent(items, maxLength) {
  let truncated = items.slice();
  let content = encodeShoppingListForQr(truncated);
  while (content.length > maxLength && truncated.length > 1) {
    truncated = truncated.slice(0, -1);
    content = encodeShoppingListForQr(truncated);
  }
  return { content, includedCount: truncated.length, totalCount: items.length };
}

async function openShoppingQrCodeModal() {
  const overlay = el(`<div class="modal-overlay"></div>`);
  const sheet = el(`<div class="modal-sheet">
    <h2>${t("qrcode_shopping_title")}</h2>
    <p style="font-size:13px;color:var(--text-muted);margin:0 0 16px;">${escapeHtml(t("qrcode_shopping_hint"))}</p>
    <div id="qrcode-shopping-holder" style="display:flex;justify-content:center;margin-bottom:12px;min-height:240px;align-items:center;text-align:center;"><span style="font-size:13px;color:var(--text-muted);">${escapeHtml(t("qrcode_loading"))}</span></div>
    <div id="qrcode-shopping-note" style="font-size:12px;color:var(--text-muted);text-align:center;margin-bottom:16px;"></div>
    <button type="button" class="btn btn-outline">${t("cooking_close")}</button>
  </div>`);
  overlay.appendChild(sheet);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  sheet.querySelector("button").addEventListener("click", () => overlay.remove());

  const holder = sheet.querySelector("#qrcode-shopping-holder");
  const noteHolder = sheet.querySelector("#qrcode-shopping-note");
  const MAX_QR_LENGTH = 900;
  const { content, includedCount, totalCount } = buildTruncatedShoppingQrContent(state.shopping, MAX_QR_LENGTH);
  if (includedCount < totalCount) {
    noteHolder.textContent = t("qrcode_shopping_truncated", { included: String(includedCount), total: String(totalCount) });
  }

  try {
    await loadQrCodeLib();
    holder.innerHTML = generateQrCodeImgTag(content);
  } catch (e) {
    holder.innerHTML = `<div><span style="font-size:13px;color:var(--danger);">${escapeHtml(t("qrcode_load_error"))}</span><div style="font-size:11px;color:var(--text-muted);margin-top:6px;word-break:break-word;">${escapeHtml((e && e.name ? e.name + " — " : "") + (e && e.message ? e.message : String(e)))}</div></div>`;
  }
}

// Charge le lecteur de QR code (jsQR) à la demande, uniquement quand le
// scan est réellement utilisé.
let jsQrLibPromise = null;
function loadJsQrLib() {
  if (window.jsQR) return Promise.resolve();
  if (jsQrLibPromise) return jsQrLibPromise;
  jsQrLibPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js";
    script.onload = () => resolve();
    script.onerror = () => { jsQrLibPromise = null; reject(new Error("jsqr_lib_load_failed")); };
    document.head.appendChild(script);
  });
  return jsQrLibPromise;
}

async function confirmImportScannedShoppingList(items) {
  if (!confirm(t("qrscan_import_confirm", { count: String(items.length) }))) return;
  for (const item of items) {
    await storePut("shopping", item);
    state.shopping.push(item);
  }
  alert(t("qrscan_import_success"));
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
    <button type="button" class="btn btn-outline" id="qrscan-close">${t("cooking_close")}</button>
  </div>`);
  overlay.appendChild(sheet);
  document.body.appendChild(overlay);

  const holder = sheet.querySelector("#qrscan-holder");
  const cameraStatusEl = sheet.querySelector("#qrscan-camera-status");
  const statusEl = sheet.querySelector("#qrscan-status");
  const manualBtn = sheet.querySelector("#qrscan-manual");
  let stream = null;
  let stopped = false;

  function cleanup() {
    stopped = true;
    if (stream) stream.getTracks().forEach((tr) => tr.stop());
  }
  sheet.querySelector("#qrscan-close").addEventListener("click", () => { cleanup(); overlay.remove(); });
  overlay.addEventListener("click", (e) => { if (e.target === overlay) { cleanup(); overlay.remove(); } });

  if (!window.isSecureContext) {
    cameraStatusEl.textContent = t("qrscan_camera_https_hint");
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraStatusEl.textContent = t("qrscan_camera_denied");
    return;
  }

  cameraStatusEl.textContent = t("qrcode_loading");
  try {
    await loadJsQrLib();
  } catch (e) {
    cameraStatusEl.textContent = t("qrscan_lib_load_error");
    return;
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

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  // Analyse une image de la caméra ; retourne true si un QR code
  // reconnu (liste ou recette) a été trouvé et traité.
  function processFrame() {
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
    const imageData = ctx.getImageData(0, 0, size, size);
    const code = window.jsQR(imageData.data, imageData.width, imageData.height);
    if (!code || !code.data) return { status: "no_code", width: canvas.width, height: canvas.height };
    const items = decodeShoppingListFromQr(code.data);
    if (items && items.length) {
      cleanup();
      overlay.remove();
      confirmImportScannedShoppingList(items);
      return { status: "success" };
    }
    const parsedRecipe = parseRecipeFromQrText(code.data);
    if (parsedRecipe) {
      cleanup();
      overlay.remove();
      confirmImportScannedRecipe(parsedRecipe);
      return { status: "success" };
    }
    // Affiche le texte brut réellement décodé (tronqué) : plutôt que de
    // deviner encore à l'aveugle pourquoi il n'est pas reconnu, ça
    // permet de voir exactement ce que la caméra a lu.
    const preview = code.data.length > 200 ? code.data.slice(0, 200) + "…" : code.data;
    statusEl.innerHTML = "";
    statusEl.appendChild(el(`<div>${escapeHtml(t("qrscan_not_recognized"))}</div>`));
    statusEl.appendChild(el(`<div style="font-size:11px;margin-top:6px;word-break:break-word;white-space:pre-wrap;user-select:text;">${escapeHtml(preview)}</div>`));
    return { status: "not_recognized" };
  }

  function tick() {
    if (stopped) return;
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      try {
        processFrame();
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

  manualBtn.addEventListener("click", () => {
    try {
      const result = processFrame();
      if (result.status === "no_code") {
        statusEl.textContent = `${t("qrscan_no_code_found")} (${result.width}×${result.height}px, ${video.videoWidth}×${video.videoHeight})`;
      }
    } catch (e) {
      statusEl.textContent = (e && e.name ? e.name + " — " : "") + (e && e.message ? e.message : String(e));
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
  if (!confirm(t("qrscan_recipe_import_confirm", { name: parsed.name }))) return;
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
    description: "",
    defaultPersons: parsed.persons || 4,
    prepTime: parsed.prepTime,
    cookTime: parsed.cookTime,
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
      const dateStr = new Date(entry.date).toLocaleDateString();
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
        if (!confirm(t("cooklog_delete_confirm"))) return;
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
    id: uid(), minutes: 5, seconds: 0, remaining: 5 * 60,
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
    timer.remaining--;
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
      timer.running = true;
      startBtn.textContent = "⏸";
      startBtn.setAttribute("aria-label", t("cooking_timer_pause"));
      setInputsDisabled(true);
      timer.interval = setInterval(tick, 1000);
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

function openCookingMode(recipe) {
  const overlay = el(`<div class="cooking-overlay"></div>`);
  const header = el(`<div class="cooking-header">
    <h2 style="font-size:19px;">${escapeHtml(recipe.name)}</h2>
    <button class="icon-btn">${t("cooking_close")}</button>
  </div>`);
  header.querySelector("button").addEventListener("click", () => {
    state.cookingTimers.forEach(stopCookingTimer);
    state.cookingTimers = [];
    stopSpeaking();
    overlay.remove();
  });
  overlay.appendChild(header);

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
    alert(t("install_already_installed"));
  } else if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
  } else if (isIosDevice()) {
    openIosInstallInstructions();
  } else {
    alert(t("install_already_installed"));
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

function translateIngredientName(name) {
  if (!name || CURRENT_LANG === "fr") return name;
  const dict = INGREDIENT_TRANSLATIONS[CURRENT_LANG];
  if (!dict) return name;
  return dict[name] || name;
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
    state.ingredientNames = existing.map((i) => i.name).sort((a, b) => a.localeCompare(b, "fr"));
    return;
  }
  // Première utilisation : préremplit avec la liste fournie.
  try {
    const res = await fetch("./data/ingredients_par_defaut.json");
    const defaults = res.ok ? await res.json() : [];
    for (const name of defaults) await storePut("ingredients", { name });
    state.ingredientNames = defaults.slice().sort((a, b) => a.localeCompare(b, "fr"));
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
  state.ingredientNames.sort((a, b) => a.localeCompare(b, "fr"));
  return true;
}
async function renameIngredientName(oldName, newName) {
  const trimmed = (newName || "").trim();
  if (!trimmed || trimmed === oldName) return false;
  await storeDelete("ingredients", oldName);
  await storePut("ingredients", { name: trimmed });
  state.ingredientNames = state.ingredientNames.filter((n) => n !== oldName);
  state.ingredientNames.push(trimmed);
  state.ingredientNames.sort((a, b) => a.localeCompare(b, "fr"));
  await moveIngredientOverride(oldName, trimmed);
  // Met aussi à jour ce nom partout où il est déjà utilisé, pour ne pas
  // casser les recettes/listes existantes.
  let touched = false;
  state.recipes.forEach((r) => {
    (r.ingredients || []).forEach((ing) => {
      if (ing.name === oldName) { ing.name = trimmed; touched = true; }
    });
  });
  if (touched) for (const r of state.recipes) await storePut("recipes", r);
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

function attachIngredientAutocomplete(input, onChange) {
  let dropdown = null;

  function close() {
    if (dropdown) { dropdown.remove(); dropdown = null; }
  }
  function open() {
    close();
    const results = searchIngredientNames(input.value, 8);
    const closest = findClosestIngredientMatch(input.value);
    const showSuggestion = closest && !results.some((r) => normalize(r) === normalize(closest.name));
    if (!results.length && !showSuggestion) return;
    dropdown = document.createElement("div");
    dropdown.className = "autocomplete-dropdown";
    if (showSuggestion) {
      const suggestItem = document.createElement("div");
      suggestItem.className = "autocomplete-item add-new";
      suggestItem.textContent = t("ingredient_did_you_mean", { name: translateIngredientName(closest.name) });
      suggestItem.addEventListener("mousedown", (e) => e.preventDefault());
      suggestItem.addEventListener("click", () => {
        input.value = translateIngredientName(closest.name);
        onChange(closest.name);
        close();
      });
      dropdown.appendChild(suggestItem);
    }
    results.forEach((frenchName) => {
      const item = document.createElement("div");
      item.className = "autocomplete-item";
      item.textContent = translateIngredientName(frenchName);
      item.addEventListener("mousedown", (e) => e.preventDefault());
      item.addEventListener("click", () => {
        input.value = translateIngredientName(frenchName);
        onChange(frenchName);
        close();
      });
      dropdown.appendChild(item);
    });
    input.parentElement.appendChild(dropdown);
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
  return { kind: "count", value: quantity };
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

async function exportAllData() {
  const data = { exportedAt: new Date().toISOString(), version: 1 };
  for (const storeName of BACKUP_STORES) {
    data[storeName] = await storeAll(storeName);
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const dateStr = new Date().toISOString().slice(0, 10);
  a.href = url;
  a.download = `mes-recettes-sauvegarde-${dateStr}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function importAllData(file, mode) {
  const text = await file.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    throw new Error("invalid");
  }
  if (!data || typeof data !== "object" || !BACKUP_STORES.some((s) => Array.isArray(data[s]))) {
    throw new Error("invalid");
  }
  if (mode === "replace") {
    for (const storeName of BACKUP_STORES) await storeClear(storeName);
  }
  for (const storeName of BACKUP_STORES) {
    const items = Array.isArray(data[storeName]) ? data[storeName] : [];
    for (const item of items) await storePut(storeName, item);
  }
  state.recipes = await storeAll("recipes");
  state.shopping = await storeAll("shopping");
  state.pantry = await storeAll("pantry");
  await ensureIngredientListLoaded();
  await loadIngredientOverrides();
}

function renderBackup() {
  const wrap = el(`<div></div>`);

  const exportSection = el(`<div class="section">
    <div class="section-label">${t("backup_export_title")}</div>
    <div class="card" style="padding:16px;">
      <p class="prose" style="margin:0 0 14px;font-size:14px;">${escapeHtml(t("backup_export_text"))}</p>
      <button class="btn btn-primary" id="export-btn">${t("backup_export_button")}</button>
    </div>
  </div>`);
  exportSection.querySelector("#export-btn").addEventListener("click", async () => {
    await exportAllData();
    alert(t("backup_export_success"));
  });
  wrap.appendChild(exportSection);

  const importSection = el(`<div class="section">
    <div class="section-label">${t("backup_import_title")}</div>
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
        <input type="file" accept="application/json,.json" id="import-file">
      </div>
    </div>
  </div>`);
  importSection.querySelector("#import-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const mode = importSection.querySelector("#import-mode").value;
    if (mode === "replace" && !confirm(t("backup_import_confirm_replace"))) {
      e.target.value = "";
      return;
    }
    try {
      await importAllData(file, mode);
      alert(t("backup_import_success"));
      state.screen = "home";
      render();
    } catch (err) {
      alert(t("backup_import_error"));
    }
  });
  wrap.appendChild(importSection);

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
    <div class="search-bar"><span>🔍</span><input type="search" placeholder="${t("search_placeholder")}"></div>
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
    if (!nameValue) { alert(t("menu_error_name")); return null; }
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
      if (confirm(t("menu_delete_confirm"))) {
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
    const name = prompt(t("planning_save_template_prompt"));
    if (!name || !name.trim()) return;
    const template = { id: uid(), name: name.trim(), plan: JSON.parse(JSON.stringify(state.weeklyPlan)) };
    await storePut("planTemplates", template);
    state.planTemplates.push(template);
    render();
  });
  wrap.appendChild(saveTemplateBtn);

  const clearBtn = el(`<button class="btn btn-danger" style="margin-bottom:20px;">${t("planning_clear")}</button>`);
  clearBtn.addEventListener("click", async () => {
    if (confirm(t("planning_clear_confirm"))) {
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
        if (!confirm(t("planning_apply_template_confirm"))) return;
        await archiveCurrentPlanIfNotEmpty();
        state.weeklyPlan = JSON.parse(JSON.stringify(template.plan));
        await saveWeeklyPlan();
        render();
      });
      row.querySelector(".del").addEventListener("click", async () => {
        if (!confirm(t("planning_delete_template_confirm"))) return;
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
    const dateStr = new Date(entry.date).toLocaleDateString();
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
      if (!confirm(t("planning_history_reapply_confirm"))) return;
      await archiveCurrentPlanIfNotEmpty();
      state.weeklyPlan = JSON.parse(JSON.stringify(entry.plan));
      await saveWeeklyPlan();
      state.screen = "planning";
      render();
    });
    const delBtn = el(`<button class="btn btn-danger">${t("common_delete")}</button>`);
    delBtn.addEventListener("click", async () => {
      if (!confirm(t("planning_history_delete_confirm"))) return;
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
function parseIngredientString(str) {
  const text = String(str || "").trim();
  const match = text.match(/^([\d]+(?:[.,]\d+)?(?:\s*\/\s*\d+)?)\s*([a-zA-Zéèàêûîôçñü]*)\.?\s*(.*)$/);
  if (!match || !match[1]) return { name: text, quantity: null, unit: "pièce" };
  const [, qtyStr, unitWordRaw, rest] = match;
  let quantity;
  if (qtyStr.includes("/")) {
    const [num, den] = qtyStr.split("/").map((s) => parseFloat(s.trim().replace(",", ".")));
    quantity = den ? num / den : null;
  } else {
    quantity = parseFloat(qtyStr.replace(",", "."));
  }
  if (Number.isNaN(quantity)) quantity = null;

  const uw = unitWordRaw.toLowerCase().replace(/s$/, "");
  let unit = null;
  let factor = 1;
  if (["g", "gr", "gram", "gramme"].includes(uw)) unit = "g";
  else if (["kg", "kilo"].includes(uw)) unit = "kg";
  else if (uw === "ml") { unit = "cl"; factor = 0.1; }
  else if (uw === "cl") unit = "cl";
  else if (["l", "litre", "liter"].includes(uw)) unit = "L";
  else if (["tbsp", "tablespoon"].includes(uw)) unit = "c. à soupe";
  else if (["tsp", "teaspoon"].includes(uw)) unit = "c. à café";
  else if (uw === "cup") { unit = "cl"; factor = 24; }
  else if (["oz", "ounce"].includes(uw)) { unit = "g"; factor = 28.35; }
  else if (["lb", "pound"].includes(uw)) { unit = "g"; factor = 453.6; }

  let name;
  if (unit) {
    quantity = quantity != null ? Math.round(quantity * factor * 100) / 100 : null;
    name = rest.trim();
  } else {
    unit = "pièce";
    name = (unitWordRaw + " " + rest).trim();
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
  // Ces deux services attendent l'adresse cible collée directement à la
  // fin (pas en paramètre nommé) — sans encodage, un "?" ou "&" dans
  // l'adresse d'origine (courant sur beaucoup de sites de recettes)
  // pouvait être mal interprété par le serveur du proxy lui-même et
  // provoquer une erreur 404.
  (url) => "https://cors.x2u.in/" + encodeURIComponent(url),
  (url) => "https://api.cors.lol/?url=" + encodeURIComponent(url),
  (url) => "https://corsfix.com/" + encodeURIComponent(url),
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

async function fetchHtmlViaProxies(targetUrl, onAttempt) {
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
      return html;
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
function parseOcrRecipeText(rawText) {
  const lines = (rawText || "").split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return { name: "", ingredients: [], description: "", prepTime: null, cookTime: null };

  const ingredientMarker = /^(ingr[ée]dients?|ingredients|ingredientes|zutaten)\s*:?\s*$/i;
  const instructionMarker = /^(pr[ée]paration|[ée]tapes|instructions?|method|steps|elaboraci[oó]n|preparaci[oó]n|zubereitung|anleitung)\s*:?\s*$/i;
  // Toute section qui doit arrêter la liste des ingrédients, pas
  // seulement celle des étapes — "Ustensiles" par exemple, très courant
  // juste après les ingrédients et avant la vraie section de
  // préparation sur beaucoup de sites.
  const sectionBoundaryMarker = /^(pr[ée]paration|[ée]tapes|instructions?|method|steps|elaboraci[oó]n|preparaci[oó]n|zubereitung|anleitung|ustensiles?|utensils?|mat[ée]riel|equipment)\s*:?\s*$/i;
  // Marque la fin du vrai contenu de la recette : au-delà, ce n'est
  // presque toujours plus que des avis, des recettes similaires ou de
  // la navigation — sans ça, la description engloberait toute la fin
  // de la page.
  const descriptionEndMarker = /^(commentaires?|comments?|avis|reviews?|vous aimerez aussi|you (may|might) also like|related recipes?|plus de recettes|ces contenus devraient vous int[ée]resser|note de l['’]auteur|donnez votre avis)/i;

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
      .filter((l) => !/^personnes?\s*[+\-]?$/i.test(l));
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

  // Les temps de préparation/cuisson apparaissent souvent après les
  // ingrédients (pas avant) — recherche sur tout le texte plutôt que
  // sur une zone précise.
  let prepTime = null, cookTime = null;
  lines.forEach((line) => {
    const prepMatch = line.match(/pr[eé]paration\s*:\s*(\d+)/i) || line.match(/prep(?:aration)?\s*time\s*:\s*(\d+)/i);
    if (prepMatch) prepTime = parseInt(prepMatch[1], 10);
    const cookMatch = line.match(/cuisson\s*:\s*(\d+)/i) || line.match(/cook\s*time\s*:\s*(\d+)/i);
    if (cookMatch) cookTime = parseInt(cookMatch[1], 10);
  });

  return { name, ingredients, description: descriptionLines.join("\n"), prepTime, cookTime };
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

async function runOcrOnImage(file) {
  await loadTesseractLib();
  const lang = TESSERACT_LANG_MAP[CURRENT_LANG] || "eng";
  const worker = await window.Tesseract.createWorker(lang);
  try {
    const { data } = await worker.recognize(file);
    return data.text;
  } finally {
    await worker.terminate();
  }
}

function renderImportPhoto() {
  const wrap = el(`<div></div>`);
  wrap.appendChild(el(`<p style="font-size:13px;color:var(--text-muted);margin:0 0 20px;line-height:1.5;">${escapeHtml(t("import_photo_disclaimer"))}</p>`));

  const fileInput = el(`<input type="file" accept="image/*" capture="environment" style="display:none;">`);
  const chooseBtn = el(`<button class="btn btn-primary">${t("import_photo_choose_button")}</button>`);
  chooseBtn.addEventListener("click", () => fileInput.click());
  wrap.appendChild(chooseBtn);
  wrap.appendChild(fileInput);

  const statusHolder = el(`<div style="margin-top:16px;font-size:14px;"></div>`);
  wrap.appendChild(statusHolder);

  fileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    chooseBtn.disabled = true;
    statusHolder.textContent = t("import_photo_processing");
    try {
      const rawText = await runOcrOnImage(file);
      if (!rawText || !rawText.trim()) {
        statusHolder.textContent = t("import_photo_no_text");
        chooseBtn.disabled = false;
        return;
      }
      const parsed = parseOcrRecipeText(rawText);
      state.editingRecipeId = null;
      state.formIngredients = parsed.ingredients.length ? parsed.ingredients : [{ name: "", quantity: "", unit: "pièce" }];
      state.formAllergens = [];
      state.formPhoto = null;
      state.screen = "form";
      state._importPrefill = { name: parsed.name, description: parsed.description, defaultPersons: 4, prepTime: parsed.prepTime, cookTime: parsed.cookTime };
      render();
    } catch (err) {
      statusHolder.innerHTML = "";
      statusHolder.appendChild(el(`<div>${escapeHtml(t("import_photo_error"))}</div>`));
      statusHolder.appendChild(el(`<div style="font-size:11px;color:var(--text-muted);margin-top:6px;word-break:break-word;">${escapeHtml((err && err.name ? err.name + " — " : "") + (err && err.message ? err.message : String(err)))}</div>`));
      chooseBtn.disabled = false;
    }
  });

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
  const attempts = [imageUrl, ...CORS_PROXIES.map((p) => p(imageUrl))];
  for (const attemptUrl of attempts) {
    try {
      const res = await fetchWithTimeout(attemptUrl, 15000);
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

async function fetchRecipeFromUrl(url, onAttempt) {
  // Jina AI Reader en premier : plus fiable en pratique que les 5
  // services CORS classiques, même si son texte nettoyé donne une
  // extraction un peu moins précise (pas de photo automatique, temps/
  // nombre de personnes parfois approximatifs) qu'une vraie extraction
  // de données structurées quand elle réussit.
  try {
    const markdown = await fetchViaJinaReader(url);
    const cleanedText = stripJinaMarkdownNoise(markdown);
    const parsedFromText = parseOcrRecipeText(cleanedText);
    if (parsedFromText && parsedFromText.ingredients.length) {
      return {
        name: parsedFromText.name,
        description: parsedFromText.description,
        ingredients: parsedFromText.ingredients.map((i) => ({ ...i, name: resolveImportedIngredientName(i.name) })),
        persons: 4,
        prepTime: parsedFromText.prepTime,
        cookTime: parsedFromText.cookTime,
        category: "Autre",
        photo: null,
      };
    }
  } catch (e) {
    // Jina a échoué ou n'a rien trouvé d'exploitable : on tente les 5
    // services habituels ci-dessous avant d'abandonner définitivement.
  }

  let recipeData = null;
  try {
    const html = await fetchHtmlViaProxies(url, onAttempt);
    const parser = new DOMParser();
    const docHtml = parser.parseFromString(html, "text/html");
    recipeData = extractJsonLdRecipe(docHtml) || extractMicrodataRecipe(docHtml);
  } catch (e) {
    // Tous les services intermédiaires habituels ont aussi échoué.
  }

  if (!recipeData) throw new Error("no_recipe_found");

  const name = typeof recipeData.name === "string" ? recipeData.name : "";
  const instructions = extractRecipeInstructions(recipeData);
  const shortDescription = typeof recipeData.description === "string" ? recipeData.description.trim() : "";
  const description = instructions || shortDescription;

  const rawIngredients = Array.isArray(recipeData.recipeIngredient) ? recipeData.recipeIngredient : [];
  const ingredients = rawIngredients
    .map(parseIngredientString)
    .filter((i) => i.name)
    .map((i) => ({ ...i, name: resolveImportedIngredientName(i.name) }));

  let persons = 4;
  const yieldRaw = recipeData.recipeYield || recipeData.yield;
  if (yieldRaw) {
    let y = Array.isArray(yieldRaw) ? yieldRaw[0] : yieldRaw;
    if (y && typeof y === "object") y = y.value || y.name || "";
    const m = String(y).match(/\d+/);
    if (m) persons = parseInt(m[0], 10);
  }

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
    const url = wrap.querySelector("#import-url-input").value.trim();
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
        defaultPersons: result.persons,
        category: result.category,
        prepTime: result.prepTime,
        cookTime: result.cookTime,
      };
      render();
    } catch (e) {
      statusHolder.innerHTML = "";
      statusHolder.appendChild(el(`<div>${escapeHtml(t("import_url_error"))}</div>`));
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
    const dateStr = new Date(entry.deletedAt).toLocaleDateString();
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
      if (!confirm(t("trash_delete_forever_confirm"))) return;
      await deleteFromTrashForever(entry.id);
      render();
    });
    wrap.appendChild(card);
  });
  const emptyAllBtn = el(`<button class="btn btn-danger" style="margin-top:8px;">${t("trash_empty_all_button")}</button>`);
  emptyAllBtn.addEventListener("click", async () => {
    if (!confirm(t("trash_empty_all_confirm"))) return;
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
    months.push({ key, label: d.toLocaleDateString(undefined, { month: "short" }), count: monthCounts[key] || 0 });
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

async function init() {
  applyTheme(localStorage.getItem("theme") || "light");

  if ("serviceWorker" in navigator) {
    try {
      const registration = await navigator.serviceWorker.register("./sw.js");
      // Force une vérification de nouvelle version à chaque ouverture de
      // l'application, plutôt que d'attendre la vérification automatique
      // et différée du navigateur — pour que les corrections arrivent
      // plus vite après une mise à jour du dépôt.
      registration.update().catch(() => {});
    } catch (e) { /* ignore */ }
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

  render();
}

init();
