"""
Fonctions reprises de l'app Windows (TESTS_NON_REGRESSION.md, entrée 141) :
1. Boutons ÷2 / ×2 du nombre de personnes (÷2 arrondi au supérieur,
   jamais sous 1).
2. Coût estimé dans la fiche recette (absent sans prix, ligne
   "estimation partielle" si certains ingrédients n'ont pas de prix).
3. Comparaison enrichie jusqu'à 3 recettes (note, favori, nombre de
   réalisations, coût, calories), sans débordement à 320 px.
4. Rappel liste d'envies après 90 jours (wishlistSince), migration des
   anciennes recettes "à essayer" datées du jour, aller-retour du champ
   wishlist_since dans le format partagé.
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


SEED = """async () => {
    const base = { category: 'Plat', description: '', notes: '', photo: null, createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], allergens: [] };
    const daysAgo = (n) => new Date(Date.now() - n * 86400000).toISOString();
    await storePut('recipes', { ...base, id: 'ra', name: 'Alpha', defaultPersons: 4, personalRating: 4, favorite: true, timesCooked: 3,
        ingredients: [{ name: 'Farine', quantity: 100, unit: 'g' }, { name: 'Lait', quantity: 10, unit: 'cl' }] });
    await storePut('recipes', { ...base, id: 'rb', name: 'Bravo', defaultPersons: 2, personalRating: 0, timesCooked: 0,
        ingredients: [{ name: 'Farine', quantity: 50, unit: 'g' }], wishlist: true, wishlistSince: daysAgo(100) });
    await storePut('recipes', { ...base, id: 'rc', name: 'Charlie au nom vraiment très long pour tester le retour à la ligne', defaultPersons: 5, personalRating: 2, timesCooked: 1,
        ingredients: [{ name: 'Sucre', quantity: 20, unit: 'g' }], wishlist: true, wishlistSince: daysAgo(10) });
    await storePut('recipes', { ...base, id: 'rd', name: 'Delta', defaultPersons: 4, personalRating: 0, timesCooked: 0,
        ingredients: [], wishlist: true });
    // Prix : farine 2 €/kg, lait 1 €/L ; sucre sans prix.
    await setIngredientOverride('Farine', [], null, { amount: 2, unit: 'kg' }, []);
    await setIngredientOverride('Lait', [], null, { amount: 1, unit: 'L' }, []);
}"""


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    results = []

    def check(label, ok, detail=""):
        results.append(ok)
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail else ''}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        url = f"http://127.0.0.1:{port}/index.html"
        page.goto(url, timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate(SEED)
        page.reload()
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); await ensureIngredientTranslationsLoaded('fr'); setLang('fr'); }")

        # --- 4. Migration + rappel liste d'envies ---
        r = page.evaluate("""() => {
            const d = state.recipes.find(r => r.id === 'rd');
            const age = (Date.now() - new Date(d.wishlistSince).getTime()) / 86400000;
            return { migrated: !!d.wishlistSince, ageDays: age, stale: getStaleWishlistRecipes().map(r => r.id).sort() };
        }""")
        check("ancienne recette à essayer datée au démarrage", r["migrated"] and r["ageDays"] < 1, r)
        check("seule la recette de 100 jours déclenche le rappel", r["stale"] == ["rb"], r["stale"])
        r = page.evaluate("""async () => {
            const rec = (await storeAll('recipes')).find(r => r.id === 'rd');
            return !!rec.wishlistSince;
        }""")
        check("date migrée enregistrée dans IndexedDB", r)
        page.evaluate("() => { state.screen = 'home'; render(); }")
        btn = page.locator(".home-wishlist-reminder")
        check("rappel affiché sur l'accueil", btn.count() == 1, btn.all_inner_texts())
        if btn.count():
            btn.click()
            r = page.evaluate("() => ({ screen: state.screen, filter: state.activeFilter })")
            check("clic : liste des recettes filtrée sur les envies", r == {"screen": "recipes", "filter": "wishlist"}, r)
        page.evaluate("""async () => {
            const b = state.recipes.find(r => r.id === 'rb');
            b.wishlist = false; b.wishlistSince = null;
            await storePut('recipes', b);
            state.screen = 'home'; render();
        }""")
        check("plus de rappel une fois la recette retirée des envies", page.locator(".home-wishlist-reminder").count() == 0)

        r = page.evaluate("""async () => {
            const src = { ...state.recipes.find(r => r.id === 'rc') };
            const { json } = await recipeToSharedFormat(src);
            const back = recipeFromSharedFormat(json, new Map());
            const off = (await recipeToSharedFormat({ ...src, wishlist: false })).json;
            return { exported: json.wishlist_since, same: back.wishlistSince === src.wishlistSince, offExport: off.wishlist_since };
        }""")
        check("wishlist_since : aller-retour format partagé", r["same"] and r["exported"] and r["offExport"] is None, r)

        # --- 1. ÷2 / ×2 ---
        def open_recipe(rid, persons):
            page.evaluate(f"() => {{ state.currentRecipeId = '{rid}'; state.viewPersons = {persons}; state.screen = 'recipe'; render(); }}")

        def persons():
            return page.evaluate("() => state.viewPersons")

        open_recipe("ra", 5)
        page.click('[data-action="half"]')
        check("÷2 sur 5 donne 3", persons() == 3, persons())
        page.click('[data-action="double"]')
        check("×2 sur 3 donne 6", persons() == 6, persons())
        open_recipe("ra", 1)
        page.click('[data-action="half"]')
        check("÷2 ne descend jamais sous 1", persons() == 1, persons())
        open_recipe("ra", 4)
        qty = page.evaluate("() => document.querySelector('.ingredient-item') && document.querySelector('.ingredient-item').textContent")
        page.click('[data-action="double"]')
        qty2 = page.evaluate("() => document.querySelector('.ingredient-item') && document.querySelector('.ingredient-item').textContent")
        check("quantités recalculées après ×2", qty and qty2 and "400" in qty and "800" in qty2, (qty, qty2))

        # --- 2. Coût estimé ---
        open_recipe("ra", 4)
        # Farine 100 g × 4 = 0,80 € ; lait 10 cl × 4 = 0,40 € -> 1,20 €, 0,30 €/pers.
        txt = page.evaluate("() => { const c = document.querySelector('.recipe-cost-card'); return c && c.textContent.replace(/\\s+/g, ' ').trim(); }")
        check("coût complet affiché (1,20 € pour 4, 0,30 €/pers.)", txt and "1,20" in txt and "0,30" in txt and "partielle" not in txt, txt)
        page.evaluate("""async () => {
            const a = state.recipes.find(r => r.id === 'ra');
            a.ingredients = [...a.ingredients, { name: 'Sucre', quantity: 10, unit: 'g' }];
            await storePut('recipes', a);
            render();
        }""")
        txt = page.evaluate("() => { const c = document.querySelector('.recipe-cost-card'); return c && c.textContent.replace(/\\s+/g, ' ').trim(); }")
        check("estimation partielle signalée (2 sur 3)", txt and "2" in txt and "3" in txt and "partielle" in txt.lower(), txt)
        open_recipe("rc", 5)
        check("pas de coût sans aucun prix", page.locator(".recipe-cost-card").count() == 0)

        # --- 3. Comparaison à 3 recettes, 320 px ---
        page.evaluate("() => { state.screen = 'compare'; render(); }")
        check("message tant que A et B ne sont pas choisies", page.locator("#compare-result .empty-state").count() == 1)
        page.select_option("#compare-a", "ra")
        page.select_option("#compare-c", "rb")
        check("A + C seulement : comparaison refusée (B obligatoire)", page.locator("#compare-result .empty-state").count() == 1)
        page.select_option("#compare-b", "rc")
        r = page.evaluate("""() => {
            const rows = [...document.querySelectorAll('#compare-result .compare-row')].map(row => ({
                label: row.querySelector('.compare-label').textContent.trim(),
                values: [...row.querySelectorAll('.compare-values > div')].map(d => d.textContent.trim()),
            }));
            return {
                rows,
                headers: document.querySelectorAll('#compare-result .header-values > div').length,
                onlyCols: document.querySelectorAll('#compare-result .compare-only-columns > div').length,
                footnote: !!document.querySelector('#compare-result .compare-footnote'),
                overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
            };
        }""")
        by = {row["label"]: row["values"] for row in r["rows"]}
        check("3 colonnes (en-têtes et « seulement dans »)", r["headers"] == 3 and r["onlyCols"] == 3, (r["headers"], r["onlyCols"]))
        check("toutes les lignes ont 3 valeurs", all(len(v) == 3 for v in by.values()), by)
        check("note", by.get("Note") == ["★★★★", "★★", "—"], by.get("Note"))
        check("favori", by.get("Favori") == ["⭐", "—", "—"], by.get("Favori"))
        check("nombre de réalisations", by.get("Cuisinée") == ["3", "1", "0"], by.get("Cuisinée"))
        cost = by.get("Coût estimé") or []
        # Alpha (sucre sans prix) : partielle -> " *" ; Charlie : aucun prix ; Bravo : 50 g farine × 2 = 0,20 €.
        check("coût", len(cost) == 3 and cost[0].endswith("*") and cost[1] == "—" and "0,20" in cost[2] and not cost[2].endswith("*"), cost)
        check("calories présentes", any(k.lower().startswith("calories") for k in by), list(by))
        check("note de bas de tableau", r["footnote"])
        check("aucun débordement horizontal à 320 px", not r["overflow"])
        page.select_option("#compare-c", "ra")
        n = page.evaluate("() => document.querySelectorAll('#compare-result .header-values > div').length")
        check("recette en double ignorée (C = A)", n == 2, n)

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    print("\n=== Résumé ===")
    ok = all(results)
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
