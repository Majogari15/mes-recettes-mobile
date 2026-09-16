#!/usr/bin/env python3
"""
Test permanent pour la fusion des unités "sachet"/"pot" dans "boîte"
(v220) et les 9 correctifs qui ont suivi (v221) — voir
TESTS_NON_REGRESSION.md, points 76 et 77.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_units_migration.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_local_server(port):
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
        *args, directory=PROJECT_ROOT, **kwargs
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def main():
    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"

    all_ok = True

    def check(label, ok, detail=""):
        nonlocal all_ok
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")

        print("=== UNIT_OPTIONS : une seule entrée fusionnée ===\n")
        options = page.evaluate("() => UNIT_OPTIONS")
        check(
            "boîte présente, sachet/pot absents",
            "boîte" in options and "sachet" not in options and "pot" not in options,
            str(options),
        )
        print()

        print("=== Reconnaissance à l'import : toutes les variantes -> boîte ===\n")
        cases = [
            "2 boîtes de tomates concassées",
            "1 sachet de levure",
            "1 pot de crème fraîche",
            "1 conserve de maïs",
        ]
        for c in cases:
            res = page.evaluate("(s) => parseIngredientString(s)", c)
            check(f'"{c}" -> unit="boîte"', res["unit"] == "boîte", str(res))
        print()

        print("=== containerLabel : conserve le mot d'origine (sachet/pot/boîte) ===\n")
        sachet = page.evaluate("() => parseIngredientString('1 sachet de levure')")
        pot = page.evaluate("() => parseIngredientString('1 pot de crème fraîche')")
        conserve = page.evaluate("() => parseIngredientString('1 conserve de maïs')")
        check('containerLabel="sachet" pour "sachet"', sachet.get("containerLabel") == "sachet", str(sachet))
        check('containerLabel="pot" pour "pot"', pot.get("containerLabel") == "pot", str(pot))
        check(
            "containerLabel absent pour une variante jamais distincte (conserve)",
            conserve.get("containerLabel") is None,
            str(conserve),
        )
        print()

        print("=== Migration au démarrage : prix personnalisés, garde-manger, courses ===\n")
        page.evaluate(
            """
            async () => {
                await storePut('ingredientOverrides', { name: 'Yaourt', price: { amount: 2, unit: 'pot' } });
                await storePut('shopping', { id: 'mig-s1', name: 'Yaourt', unit: 'pot', quantity: 1, checked: false });
                await storePut('pantry', { id: 'mig-p1', name: 'Yaourt', unit: 'sachet', quantity: 3 });
                await storePut('recipes', { id: 'mig-r1', name: 'Recette migration', category: 'Autre', ingredients: [{ name: 'Yaourt', unit: 'sachet', quantity: 1 }] });
            }
            """
        )
        page.reload(timeout=8000)
        page.wait_for_function("() => document.body.innerText.trim().length > 20", timeout=15000)
        page.wait_for_timeout(800)
        result = page.evaluate(
            """
            () => {
                const price = getIngredientPrice('Yaourt');
                const shoppingItem = state.shopping.find((s) => s.id === 'mig-s1');
                const pantryItem = state.pantry.find((p) => p.id === 'mig-p1');
                const recipe = state.recipes.find((r) => r.id === 'mig-r1');
                return {
                    priceUnit: price ? price.unit : null,
                    cost: computeIngredientCost('Yaourt', shoppingItem.quantity, shoppingItem.unit),
                    shoppingUnit: shoppingItem.unit,
                    pantryUnit: pantryItem.unit,
                    recipeUnit: recipe.ingredients[0].unit,
                    recipeContainerLabel: recipe.ingredients[0].containerLabel,
                };
            }
            """
        )
        check("prix migré vers boîte", result["priceUnit"] == "boîte", str(result))
        check("coût calculable après migration (pas null)", result["cost"] == 2, str(result))
        check("garde-manger migré", result["pantryUnit"] == "boîte", str(result))
        check("courses migrées", result["shoppingUnit"] == "boîte", str(result))
        check("recette migrée", result["recipeUnit"] == "boîte", str(result))
        check(
            "containerLabel conservé lors de la migration (sachet)",
            result["recipeContainerLabel"] == "sachet",
            str(result),
        )
        print()

        print("=== Fusion des doublons de courses créés par la migration ===\n")
        page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'dup-1', name: 'Fromage blanc', unit: 'pot', quantity: 1, checked: false });
                await storePut('shopping', { id: 'dup-2', name: 'Fromage blanc', unit: 'sachet', quantity: 2, checked: false });
            }
            """
        )
        page.reload(timeout=8000)
        page.wait_for_function("() => document.body.innerText.trim().length > 20", timeout=15000)
        page.wait_for_timeout(800)
        dup_result = page.evaluate(
            "async () => (await storeAll('shopping')).filter((s) => s.name === 'Fromage blanc')"
        )
        check(
            "une seule ligne après fusion, quantités additionnées (1+2=3)",
            len(dup_result) == 1 and dup_result[0]["quantity"] == 3 and dup_result[0]["unit"] == "boîte",
            str(dup_result),
        )
        print()

        print("=== Import partagé (QR/lien ZIP bureau) migre aussi l'unité ===\n")
        shared = page.evaluate(
            """
            () => {
                const json = { id: 'shared-1', name: 'Recette partagée', ingredients: [{ name: 'Yaourt', unit: 'pot', quantity: 1 }] };
                return recipeFromSharedFormat(json, new Map());
            }
            """
        )
        check(
            "recipeFromSharedFormat migre l'unité",
            shared["ingredients"][0]["unit"] == "boîte",
            str(shared["ingredients"][0]),
        )
        print()

        print("=== Restauration de sauvegarde : select non vide dans le formulaire ===\n")
        page.evaluate(
            """
            async () => {
                const json = { id: 'shared-1', name: 'Recette partagée', ingredients: [{ name: 'Yaourt', unit: 'pot', quantity: 1 }], category: 'Autre' };
                const recipe = recipeFromSharedFormat(json, new Map());
                await storePut('recipes', recipe);
                state.recipes.push(recipe);
                openRecipeForm('shared-1');
            }
            """
        )
        page.wait_for_timeout(300)
        select_info = page.evaluate(
            """
            () => {
                const sel = document.querySelector('.ing-form-row select.ing-unit');
                return sel ? { value: sel.value, selectedIndex: sel.selectedIndex } : null;
            }
            """
        )
        check(
            "menu déroulant d'unité non vide après import partagé",
            select_info is not None and select_info["selectedIndex"] != -1 and select_info["value"] == "boîte",
            str(select_info),
        )
        print()

        # Nettoyage
        page.evaluate(
            """
            async () => {
                for (const id of ['mig-r1', 'shared-1']) await storeDelete('recipes', id);
                for (const id of ['mig-s1', 'dup-1', 'dup-2']) await storeDelete('shopping', id);
                await storeDelete('pantry', 'mig-p1');
                await storeDelete('ingredientOverrides', 'Yaourt');
            }
            """
        )

        browser.close()

    httpd.shutdown()

    print("Erreurs JS sur tout le parcours:", errors if errors else "AUCUNE")
    if errors:
        all_ok = False

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
