"""
Recettes similaires en bas de la fiche, reprises de l'app Windows
(TESTS_NON_REGRESSION.md, entrée 145).

Score Windows : +2 même catégorie, +1 par étiquette commune, +1 par
ingrédient commun (5 au plus), 5 recettes au plus, égalités par nom.
Écarts voulus vérifiés ici : la catégorie seule ne suffit pas, et sel,
poivre, eau, huiles ne comptent pas. Puis l'affichage (raisons, appui ->
fiche de la recette proposée, section absente sans suggestion, 320 px).
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
    const base = { createdAt: '2026-01-01', cookLog: [], defaultPersons: 4, difficulty: 'Facile' };
    const ings = (...names) => names.map((name) => ({ name, quantity: 1, unit: 'pièce' }));
    const recipes = [
        { id: 't', name: 'Poulet curry', category: 'Plat', tags: ['épicé'], ingredients: ings('Poulet', 'Lait de coco', 'Curry', 'Oignon', 'Sel', 'Poivre', "Huile d'olive") },
        // même catégorie + 3 ingrédients + 1 étiquette = 6
        { id: 'a', name: 'Poulet tikka', category: 'Plat', tags: ['Épicé'], ingredients: ings('Poulet', 'Curry', 'Oignon', 'Yaourt') },
        // autre catégorie + 2 ingrédients = 2
        { id: 'b', name: 'Soupe coco', category: 'Entrée', ingredients: ings('Lait de coco', 'Oignon', 'Carotte') },
        // même catégorie, seulement sel/poivre/huile en commun -> exclue
        { id: 'c', name: 'Steak frites', category: 'Plat', ingredients: ings('Steak', 'Pomme de terre', 'Sel', 'Poivre', "Huile d'olive") },
        // même catégorie, rien en commun -> exclue (catégorie seule)
        { id: 'd', name: 'Lasagnes', category: 'Plat', ingredients: ings('Pâtes', 'Boeuf') },
        // seulement l'étiquette en commun, autre catégorie = 1
        { id: 'e', name: 'Chili', category: 'Autre', tags: ['épicé'], ingredients: ings('Haricots rouges') },
        // même score que b (2), départage par nom : « Curry de légumes » avant « Soupe coco »
        { id: 'f', name: 'Curry de légumes', category: 'Entrée', ingredients: ings('Curry', 'Oignon') },
    ];
    for (const r of recipes) await storePut('recipes', { ...base, ...r });
    state.recipes = await storeAll('recipes');
}"""


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); setLang('fr'); }")
        page.evaluate(SEED)

        r = page.evaluate("() => findSimilarRecipes(state.recipes.find(x => x.id === 't')).map(s => [s.recipe.id, s.score, s.commonIngredients, s.commonTags, s.sameCategory])")
        ids = [x[0] for x in r]
        check("ordre : score décroissant puis nom", ids == ["a", "f", "b", "e"], r)
        check("score Windows : catégorie 2 + étiquette 1 + ingrédients 3 = 6", r[0][1:] == [6, 3, 1, True], r[0])
        check("étiquette comparée sans casse ni accent (« Épicé » = « épicé »)", r[0][3] == 1)
        check("sel, poivre, huile ignorés (« Steak frites » absent)", "c" not in ids)
        check("catégorie seule insuffisante (« Lasagnes » absent)", "d" not in ids)
        check("la recette elle-même n'est jamais proposée", "t" not in ids)

        r = page.evaluate("""() => {
            const big = { id: 'big', name: 'Big', category: 'Plat', ingredients: Array.from({ length: 12 }, (_, i) => ({ name: 'Ing' + i })) };
            const twin = { id: 'twin', name: 'Twin', category: 'Plat', ingredients: big.ingredients };
            const saved = state.recipes;
            state.recipes = [big, twin, ...Array.from({ length: 8 }, (_, i) => ({ id: 'x' + i, name: 'X' + i, category: 'Autre', ingredients: [{ name: 'Ing0' }] }))];
            const out = findSimilarRecipes(big).map(s => [s.recipe.id, s.score]);
            state.recipes = saved;
            return out;
        }""")
        check("ingrédients communs plafonnés à 5, 5 recettes au plus", r[0] == ["twin", 7] and len(r) == 5, r)

        # --- Affichage ---
        page.evaluate("() => { state.currentRecipeId = 't'; state.viewPersons = 4; state.screen = 'recipe'; render(); }")
        rows = page.evaluate("() => [...document.querySelectorAll('.similar-recipe-row')].map(b => ({ name: b.querySelector('.name').textContent, why: b.querySelector('.why').textContent }))")
        check("4 suggestions affichées", len(rows) == 4, rows)
        check("raisons lisibles", rows and rows[0] == {"name": "Poulet tikka", "why": "3 ingrédient(s) en commun · 1 étiquette(s) en commun · même catégorie"}, rows[:1])
        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        check("pas de débordement à 320 px", not overflow)
        page.locator(".similar-recipe-row").nth(2).click()
        r = page.evaluate("() => ({ id: state.currentRecipeId, persons: state.viewPersons, title: document.querySelector('.similar-recipes') ? 'section' : 'none' })")
        check("appui -> fiche de la recette proposée", r["id"] == "b" and r["persons"] == 4, r)
        page.evaluate("() => { state.currentRecipeId = 'd'; render(); }")
        check("aucune suggestion -> section absente", page.locator(".similar-recipes").count() == 0)

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
