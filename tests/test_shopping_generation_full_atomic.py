"""
Vérifie le correctif du point 118 étendu à l'ensemble d'une génération
multi-recettes (voir TESTS_NON_REGRESSION.md point 119), suite à une
quatrième relecture externe.

Le point 118 rendait atomique l'ajout d'UNE recette aux courses (une
seule transaction IndexedDB pour tous ses ingrédients). Mais les
boutons "Générer la liste de courses" d'un menu ou du planning
ajoutaient encore chaque recette séparément, dans sa PROPRE transaction
— un échec sur la 2e recette d'une génération de 2 laissait la 1ère
déjà écrite avec succès. Une nouvelle tentative de la génération
complète ré-ajoutait alors cette 1ère recette par-dessus elle-même
(double comptage), exactement reproduit et confirmé par la relecture
externe avant ce correctif.

Corrigé en introduisant addRecipesToShoppingSilent(recipePersonsList)
— calcule l'état final de TOUTES les recettes de la génération sur une
copie de travail commune, puis écrit tout en une seule transaction.
addRecipeToShoppingSilent(recipe, persons) devient un simple raccourci
pour une seule recette. Les deux boutons ("Générer la liste de
courses" du menu et du planning) construisent maintenant la liste
complète des recettes concernées AVANT d'appeler la fonction une seule
fois, au lieu de boucler avec un appel par recette.
"""
import http.server
import json
import socket
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_local_server(port):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=PROJECT_ROOT, **k)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"
    all_ok = True

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(600)
        page.evaluate("() => setLang('fr')")

        def check(label, condition, detail):
            nonlocal all_ok
            mark = "✅ OK " if condition else "❌ ECHEC"
            print(f"{mark} {label} — {detail}")
            if not condition:
                all_ok = False

        print("=== 1. Scénario exact signalé : échec sur la 2e recette, retentative sans double comptage ===")
        r1 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                state.shopping = [];
                const recipeA = { ingredients: [{ name: 'Farine', quantity: 50, unit: 'g' }] };
                const recipeB = { ingredients: [{ name: 'Sel', quantity: 5, unit: 'g' }] };

                const realWriteMany = window.storeWriteManyAcrossStores;
                window.storeWriteManyAcrossStores = () => Promise.reject(new Error('échec simulé'));
                let threw = false;
                try {
                    await addRecipesToShoppingSilent([{ recipe: recipeA, persons: 1 }, { recipe: recipeB, persons: 1 }]);
                } catch (e) { threw = true; }
                window.storeWriteManyAcrossStores = realWriteMany;
                const afterFail = { mem: state.shopping.length, db: (await storeAll('shopping')).length };

                // Nouvelle tentative de la MÊME génération complète (sans échec cette fois).
                await addRecipesToShoppingSilent([{ recipe: recipeA, persons: 1 }, { recipe: recipeB, persons: 1 }]);
                const db = await storeAll('shopping');
                return {
                    threw,
                    afterFail,
                    farineQty: (db.find((i) => i.name === 'Farine') || {}).quantity,
                    selQty: (db.find((i) => i.name === 'Sel') || {}).quantity,
                    count: db.length,
                };
            }
            """
        )
        check(
            "échec propagé, rien n'est écrit ; la retentative complète donne les bonnes quantités (pas de double comptage)",
            r1["threw"] is True and r1["afterFail"]["mem"] == 0 and r1["afterFail"]["db"] == 0
            and r1["farineQty"] == 50 and r1["selQty"] == 5 and r1["count"] == 2,
            json.dumps(r1),
        )

        print("\n=== 2. addRecipesToShoppingSilent : une seule transaction pour N recettes ===")
        r2 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                state.shopping = [];
                const recipeA = { ingredients: [{ name: 'Lait', quantity: 1, unit: 'L' }] };
                const recipeB = { ingredients: [{ name: 'Œufs', quantity: 6, unit: 'pièce' }] };
                const recipeC = { ingredients: [{ name: 'Beurre', quantity: 100, unit: 'g' }] };

                const realWriteMany = window.storeWriteManyAcrossStores;
                let callCount = 0;
                window.storeWriteManyAcrossStores = (ops) => { callCount += 1; return realWriteMany(ops); };
                await addRecipesToShoppingSilent([
                    { recipe: recipeA, persons: 1 },
                    { recipe: recipeB, persons: 1 },
                    { recipe: recipeC, persons: 1 },
                ]);
                window.storeWriteManyAcrossStores = realWriteMany;
                const db = await storeAll('shopping');
                return { callCount, names: db.map((i) => i.name).sort() };
            }
            """
        )
        check(
            "un seul appel de transaction pour les 3 recettes",
            r2["callCount"] == 1 and r2["names"] == ["Beurre", "Lait", "Œufs"],
            json.dumps(r2, ensure_ascii=False),
        )

        print("\n=== 3. Bouton 'Ajouter tout aux courses' d'un menu : réellement en une seule transaction ===")
        r3 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                for (const m of await storeAll('menus')) await storeDelete('menus', m.id);
                state.shopping = [];
                await storePut('recipes', { id: 'ra', name: 'A', category: 'Plat', ingredients: [{ name: 'Farine', quantity: 50, unit: 'g' }] });
                await storePut('recipes', { id: 'rb', name: 'B', category: 'Plat', ingredients: [{ name: 'Sel', quantity: 5, unit: 'g' }] });
                state.recipes = await storeAll('recipes');
                const menu = { id: 'm1', name: 'Menu test', items: [{ recipeId: 'ra', persons: 1 }, { recipeId: 'rb', persons: 1 }] };
                await storePut('menus', menu);
                state.menus = [menu];
                state.currentMenuId = 'm1';
                state.screen = 'menu';
                render();
                await new Promise((r) => setTimeout(r, 100));

                const realWriteMany = window.storeWriteManyAcrossStores;
                let callCount = 0;
                window.storeWriteManyAcrossStores = (ops) => { callCount += 1; return realWriteMany(ops); };
                const btn = [...document.querySelectorAll('button')].find((b) => b.textContent.includes('aux courses'));
                if (btn) btn.click();
                await new Promise((r) => setTimeout(r, 200));
                window.storeWriteManyAcrossStores = realWriteMany;
                const db = await storeAll('shopping');
                return { hasBtn: !!btn, callCount, names: db.map((i) => i.name).sort() };
            }
            """
        )
        check(
            "un seul appel, les 2 recettes du menu ajoutées ensemble",
            r3["hasBtn"] and r3["callCount"] == 1 and r3["names"] == ["Farine", "Sel"],
            json.dumps(r3, ensure_ascii=False),
        )

        print("\n=== 4. Bouton 'Générer la liste de courses' du planning : réellement en une seule transaction ===")
        r4 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                state.shopping = [];
                await storePut('recipes', { id: 'rc', name: 'C', category: 'Plat', ingredients: [{ name: 'Riz', quantity: 200, unit: 'g' }] });
                await storePut('recipes', { id: 'rd', name: 'D', category: 'Plat', ingredients: [{ name: 'Poivron', quantity: 2, unit: 'pièce' }] });
                state.recipes = await storeAll('recipes');
                state.weeklyPlan = { Lundi: { Déjeuner: [{ recipeId: 'rc', persons: 1 }, { recipeId: 'rd', persons: 1 }] } };
                await saveWeeklyPlan();
                state.screen = 'planning';
                render();
                await new Promise((r) => setTimeout(r, 100));

                const realWriteMany = window.storeWriteManyAcrossStores;
                let callCount = 0;
                window.storeWriteManyAcrossStores = (ops) => { callCount += 1; return realWriteMany(ops); };
                const btn = [...document.querySelectorAll('button')].find((b) => b.textContent.includes('liste de courses'));
                if (btn) btn.click();
                await new Promise((r) => setTimeout(r, 200));
                window.storeWriteManyAcrossStores = realWriteMany;
                const db = await storeAll('shopping');
                return { hasBtn: !!btn, callCount, names: db.map((i) => i.name).sort() };
            }
            """
        )
        check(
            "un seul appel, les 2 recettes du planning ajoutées ensemble",
            r4["hasBtn"] and r4["callCount"] == 1 and r4["names"] == ["Poivron", "Riz"],
            json.dumps(r4, ensure_ascii=False),
        )

        print("\n=== 5. addRecipeToShoppingSilent (raccourci mono-recette) toujours fonctionnel ===")
        r5 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                state.shopping = [];
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Tomate', quantity: 3, unit: 'pièce' }] }, 1);
                const db = await storeAll('shopping');
                return { memCount: state.shopping.length, dbCount: db.length, name: (db[0] || {}).name };
            }
            """
        )
        check(
            "toujours fonctionnel pour une seule recette",
            r5["memCount"] == 1 and r5["dbCount"] == 1 and r5["name"] == "Tomate",
            json.dumps(r5, ensure_ascii=False),
        )

        check("Aucune erreur JS pendant tout le parcours", not errors, str(errors))

        print("\n=== Résumé ===")
        print("TOUT CORRECT" if all_ok else "AU MOINS UN ECHEC")
        browser.close()
    httpd.shutdown()
    return all_ok


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
