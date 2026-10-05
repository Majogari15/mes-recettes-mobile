"""
Arabe (arabe standard moderne) — interface de droite à gauche
(TESTS_NON_REGRESSION.md, entrée 164 ; intégration en cours sur une
branche, pas encore sur main).

Contrôle statique : les 700 textes d'interface traduits, mêmes
paramètres {…} que l'anglais, chacun contient de l'arabe (sauf formats
techniques) ; manifeste arabe (dir rtl) déclaré partout.

Audit en direct, comme pour le chinois (voir ci-dessous), plus :
document lang="ar" dir="rtl", flèche retour retournée, bouton flottant et
navigation inversés, chiffres occidentaux (aucun chiffre arabe oriental),
valeurs insérées isolées (FSI…PDI) pour l'ordre des mots, retour au
français en gauche à droite.

Les noms d'ingrédients restent en français tant que leur traduction
arabe (étape 2) n'existe pas : ils sont acceptés ici, et les deux
fichiers data/ingredient_*_ar.json absents (404) ignorés.

Pour chacun des 24 écrans et 10 fenêtres (360 px, données d'exemple) :
aucune erreur JavaScript, aucun débordement horizontal, aucun texte
visible (ni placeholder / aria-label / title / alt) uniquement en
alphabet latin hors liste blanche (noms des langues, sigles, marques).
"""
import http.server
import json
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
AR = re.compile(r"[\u0600-\u06ff]")
# Textes latins attendus : noms des langues (sélecteur de langue), sigles,
# marques, systèmes, adresses d'exemple.
ALLOWED_LATIN = re.compile(
    r"^(?:Français|English|Español|Deutsch|Bahasa Indonesia|Português|Italiano|Svenska|Norsk|"
    r"(?:Chrome|Firefox|Safari|Edg|Version)/[\d.]+.*|PDF|QR|URL|ICS|JSON|ZIP|CSV|OK|Linux|Windows|Android|iOS|macOS|Mac OS|Chrome|Chromium|Safari|Firefox|"
    r"Google|Cloudflare|Jina|Tesseract|Open Food Facts|IndexedDB|Mes Recettes, Mes Courses|"
    r"https?://\S+|[\d\s.,:/%x×-]*(?:MB|KB|GB|ms|px)?)$")


CATALOGUE = [e["fr"] for e in json.load(open(f"{PROJECT_ROOT}/data/ingredients_catalogue.json", encoding="utf-8"))]
CATALOGUE_SET = set(CATALOGUE)


def is_catalogue_text(t):
    """Nom d'ingrédient du catalogue (encore en français avant l'étape 2)."""
    parts = [p.strip(" ✕") for p in re.split(r" ↔ ", re.sub(r"^\[[a-z-]+\] ", "", t))]
    return all(p in CATALOGUE_SET for p in parts if p)


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


SEED="""async()=>{
 const base={category:'Plat',notes:'',photo:null,createdAt:'2026-01-01T00:00:00.000Z',cookLog:[{date:'2026-09-20'}],allergens:['Œufs'],tags:['快手'],timesCooked:2,personalRating:4};
 await storePut('recipes',{...base,id:'r1',name:'番茄炒蛋',defaultPersons:2,prepTime:10,cookTime:5,difficulty:'Facile',description:'1. 鸡蛋打散。\\n2. 炒番茄。',
   ingredients:[{name:'Tomate',quantity:1,unit:'pièce'},{name:'Oeufs',quantity:1.5,unit:'pièce'},{name:'Sucre',quantity:5,unit:'g'}],favorite:true});
 await storePut('recipes',{...base,id:'r2',name:'红烧肉',category:'Plat',defaultPersons:4,prepTime:20,cookTime:90,difficulty:'Moyen',description:'慢炖。',
   ingredients:[{name:'Sucre',quantity:10,unit:'g'},{name:'Lait',quantity:5,unit:'cl'}],wishlist:true,wishlistSince:'2026-01-01T00:00:00.000Z'});
 await setIngredientOverride('Sucre',[],null,{amount:3,unit:'kg'},[]);
 await storePut('shopping',{id:'s1',name:'Tomate',quantity:3,unit:'pièce',checked:false,rayon:'Fruits & légumes'});
 await storePut('shopping',{id:'s2',name:'Lait',quantity:1,unit:'L',checked:true});
 await storePut('pantry',{id:'p1',name:'Riz',quantity:1,unit:'kg',expirationDate:'2026-10-06'});
 await storePut('menus',{id:'m1',name:'周末菜单',recipeIds:['r1','r2']});
 await kvSet('weeklyPlan',{Lundi:{'Déjeuner':[{recipeId:'r1',persons:2}]}});
 await storePut('trash',{id:'t1',type:'recipe',item:{...base,id:'r9',name:'旧食谱',ingredients:[]},deletedAt:'2026-09-01T00:00:00.000Z'});
 await storePut('savedShoppingLists',{id:'l1',name:'周一清单',items:[{name:'Tomate',quantity:2,unit:'pièce'}],savedAt:'2026-09-01T00:00:00.000Z'});
}"""
SCREENS=["home","recipes","recipe","form","shopping","pantry","ingredients","ingredientDuplicates","backup","diagnostic","compare","menus","menu","planning","planningHistory","importUrl","unitConverter","trash","savedShoppingLists","whatCanICook","cookbookExport","manageSubstitutions","statistics","importPhoto"]
COLLECT="""()=>{const texts=[];const walk=(root)=>{root.querySelectorAll('*').forEach(e=>{
   for(const a of ['placeholder','aria-label','title','alt']){const v=e.getAttribute&&e.getAttribute(a); if(v) texts.push('['+a+'] '+v);} });
   const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const t=n.textContent.trim(); const st=n.parentElement&&getComputedStyle(n.parentElement); if(t && st && st.display!=='none' && st.visibility!=='hidden' && n.parentElement.tagName!=='SCRIPT' && n.parentElement.tagName!=='STYLE' && n.parentElement.tagName!=='NOSCRIPT') texts.push(t);} };
  walk(document.body);
  const de=document.documentElement; return {texts:[...new Set(texts)], overflow: de.scrollWidth>de.clientWidth, title: document.title, lang: de.lang+'/'+de.dir};}"""
MODALS = {
    "ajout courses": "() => openAddItemModal('shopping', null, null, () => {})",
    "ajout garde-manger": "() => openAddItemModal('pantry', null, null, () => {})",
    "ingrédient": "() => openIngredientNameModal('Sucre')",
    "langue": "() => openLanguagePickerModal()",
    "clause": "() => openDisclaimer({ readOnly: true })",
    "choix de recette": "() => openRecipePickerModal(() => {})",
    "mode cuisine": "() => openCookingMode(state.recipes.find((r) => r.id === 'r1'), 2)",
    "QR code": "() => openQrCodeModal(state.recipes.find((r) => r.id === 'r1'), 2)",
    "coller un texte": "() => openQrPasteModal()",
    "confirmation": "() => { customConfirm(t('planning_clear_confirm')); }",
}


def main():
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    # Contrôle statique des textes.
    en = json.load(open(f"{PROJECT_ROOT}/i18n/en.json", encoding="utf-8"))
    ar = json.load(open(f"{PROJECT_ROOT}/i18n/ar.json", encoding="utf-8"))
    check("700 textes : mêmes clés que l'anglais", list(ar) == list(en), (len(ar), len(en)))
    ph = lambda v: sorted(re.findall(r"\{[a-zA-Z_]+\}", v))
    bad_ph = [k for k in en if ph(en[k]) != ph(ar.get(k, ""))]
    check("mêmes paramètres {…} que l'anglais", not bad_ph, bad_ph[:5])
    no_ar = [k for k, v in ar.items() if not AR.search(v)]
    check("chaque texte contient de l'arabe (sauf formats techniques)",
          set(no_ar) <= {"import_url_placeholder", "unitconv_result", "planning_ics_summary", "form_remove"}, no_ar)
    manifest = json.load(open(f"{PROJECT_ROOT}/manifest-ar.json", encoding="utf-8"))
    check("manifeste arabe : lang ar, dir rtl, déclaré au chargement et en cache hors ligne",
          manifest.get("lang") == "ar" and manifest.get("dir") == "rtl"
          and '"ar"' in open(f"{PROJECT_ROOT}/manifest-loader.js").read()
          and "./manifest-ar.json" in open(f"{PROJECT_ROOT}/sw.js").read())

    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 360, "height": 760})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "404" not in m.text else None)
        page.on("response", lambda r: errors.append(f"HTTP {r.status} {r.url}") if r.status >= 400 and not re.search(r"ingredient_(translations|substitutions)_ar\.json", r.url) else None)
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate(SEED)
        page.reload()
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('ar'); await ensureIngredientTranslationsLoaded('ar'); setLang('ar'); }")

        def audit(label):
            r = page.evaluate(COLLECT)
            latin = sorted({t for t in r["texts"]
                            if not AR.search(t) and not is_catalogue_text(t) and re.search(r"[A-Za-zÀ-ÿ]{3,}", re.sub(r"^\[[a-z-]+\] ", "", t))
                            and not ALLOWED_LATIN.match(re.sub(r"^\[[a-z-]+\] ", "", t).strip())})
            ok = not errors and not r["overflow"] and r["lang"] == "ar/rtl" and not latin
            check(f"{label} : arabe, de droite à gauche, sans débordement ni erreur", ok,
                  "" if ok else {"latin": latin[:8], "overflow": r["overflow"], "lang": r["lang"], "errors": errors[:3]})
            errors.clear()

        for sc in SCREENS:
            page.evaluate("""(sc) => { document.querySelectorAll('.modal-overlay').forEach((o) => o.remove());
                state.currentRecipeId = 'r1'; state.viewPersons = 2; state.currentMenuId = 'm1'; state.screen = sc; render(); }""", sc)
            page.wait_for_timeout(700 if sc in ("diagnostic", "ingredientDuplicates", "statistics") else 250)
            audit(f"écran {sc}")
        for label, js in MODALS.items():
            page.evaluate("() => { document.querySelectorAll('.modal-overlay').forEach((o) => o.remove()); state.screen = 'home'; render(); }")
            page.evaluate(js)
            page.wait_for_timeout(500)
            audit(f"fenêtre {label}")
        # Mise en page de droite à gauche.
        r = page.evaluate("""() => {
            document.querySelectorAll('.modal-overlay').forEach((o) => o.remove());
            state.currentRecipeId = 'r1'; state.viewPersons = 2; state.screen = 'recipe'; render();
            const backTransform = getComputedStyle(document.querySelector('.back-btn .ui-icon-back')).transform;
            const backBtn = document.querySelector('.back-btn').getBoundingClientRect();
            state.screen = 'shopping'; render();
            const fab = document.querySelector('.fab').getBoundingClientRect();
            const nav = [...document.querySelectorAll('.bottom-nav button, .bottom-nav a')].map((b) => b.getBoundingClientRect().left);
            state.screen = 'statistics'; render();
            const text = document.body.innerText;
            return {
                backTransform, backRight: backBtn.left > window.innerWidth / 2,
                fabLeft: fab.left < window.innerWidth / 2, navReversed: nav.length > 1 && nav[0] > nav[nav.length - 1],
                easternDigits: /[\u0660-\u0669\u06f0-\u06f9]/.test(text),
                isolated: t('stats_cooked_line', { name: 'Tarte', count: '2' }),
                sep: listSeparator(), date: localeDateStr('2026-10-05T12:00:00'),
            };
        }""")
        check("flèche retour retournée et placée à droite", r["backTransform"].startswith("matrix(-1") and r["backRight"], r)
        check("bouton flottant à gauche, navigation basse inversée (accueil à droite)", r["fabLeft"] and r["navReversed"], r)
        check("chiffres occidentaux partout (aucun chiffre arabe oriental)", not r["easternDigits"] and "2026" in r["date"], r["date"])
        check("valeurs insérées isolées (ordre des mots), virgule arabe « ، »",
              r["isolated"] == "\u2068Tarte\u2069 — \u20682\u2069 مرة" and r["sep"] == "، ", (r["isolated"], r["sep"]))
        r = page.evaluate("() => { setLang('fr'); render(); return [document.documentElement.dir, document.documentElement.lang, t('stats_cooked_line', { name: 'Tarte', count: '2' })]; }")
        check("retour au français : gauche à droite, sans caractères d'isolation", r == ["ltr", "fr", "Tarte — 2 fois"], r)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
