"""
Chinois simplifié — audit de l'interface (TESTS_NON_REGRESSION.md,
entrée 162 ; intégration en cours sur une branche, pas encore sur main).

Parcourt les 24 écrans et 10 fenêtres de l'application en chinois, avec
des données d'exemple (recettes, courses, garde-manger, menu, planning,
corbeille, liste enregistrée), à 360 px de large. Pour chacun : aucune
erreur JavaScript, aucun débordement horizontal, langue du document
zh-CN, et aucun texte visible (ni placeholder / aria-label / title / alt)
uniquement en alphabet latin — signe d'un texte français ou anglais
oublié — hors liste blanche (noms des langues dans le sélecteur, sigles
techniques, marques). Les textes mélangeant chinois et latin (noms de
catalogue « 巴约讷火腿（Bayonne） », codes de devise « CHF — 瑞士法郎 »)
sont acceptés.
"""
import http.server
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
CJK = re.compile(r"[\u4e00-\u9fff]")
# Textes latins attendus : noms des langues (sélecteur de langue), sigles,
# marques, systèmes, adresses d'exemple.
ALLOWED_LATIN = re.compile(
    r"^(?:Français|English|Español|Deutsch|Bahasa Indonesia|Português|Italiano|Svenska|Norsk|"
    r"(?:Chrome|Firefox|Safari|Edg|Version)/[\d.]+.*|PDF|QR|URL|ICS|JSON|ZIP|CSV|OK|Linux|Windows|Android|iOS|macOS|Mac OS|Chrome|Chromium|Safari|Firefox|"
    r"Google|Cloudflare|Jina|Tesseract|Open Food Facts|IndexedDB|Mes Recettes, Mes Courses|"
    r"https?://\S+|[\d\s.,:/%x×-]*(?:MB|KB|GB|ms|px)?)$")


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
  const de=document.documentElement; return {texts:[...new Set(texts)], overflow: de.scrollWidth>de.clientWidth, title: document.title, lang: de.lang};}"""
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

    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 360, "height": 760})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate(SEED)
        page.reload()
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('zh'); await ensureIngredientTranslationsLoaded('zh'); setLang('zh'); }")

        def audit(label):
            r = page.evaluate(COLLECT)
            latin = sorted({t for t in r["texts"]
                            if not CJK.search(t) and re.search(r"[A-Za-zÀ-ÿ]{3,}", re.sub(r"^\[[a-z-]+\] ", "", t))
                            and not ALLOWED_LATIN.match(re.sub(r"^\[[a-z-]+\] ", "", t).strip())})
            ok = not errors and not r["overflow"] and r["lang"] == "zh-CN" and not latin
            check(f"{label} : chinois, sans débordement ni erreur", ok,
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
        page.evaluate("() => setLang('fr')")
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
