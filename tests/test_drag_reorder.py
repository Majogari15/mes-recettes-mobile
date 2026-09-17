#!/usr/bin/env python3
"""Test permanent : glisser-déposer manuel pour réordonner la liste de
courses, le garde-manger et les ingrédients d'un formulaire de recette
(demande explicite de l'utilisateur) — voir TESTS_NON_REGRESSION.md
point 99.

Le glisser-déposer est simulé via de vrais événements souris
(page.mouse.down/move/up), que Chromium traduit en Pointer Events
identiques à un geste tactile réel — le code de l'application
(attachDragReorder dans app.js) n'utilise que les Pointer Events,
jamais l'API HTML5 native dragstart/dragover.

Couvre : réordonnancement effectif (courses, garde-manger, formulaire
de recette), persistance de l'ordre en tri manuel (IndexedDB, survit à
un rechargement de page ET à un aller-retour de sauvegarde locale),
non-régression des tris existants (nom/rayon toujours triés comme
avant, jamais impactés par le tri manuel), absence de bug d'index
périmé après un glisser-déposer dans le formulaire de recette (le
bouton "supprimer" doit cibler le bon ingrédient), et absence de
débordement horizontal introduit par la nouvelle poignée.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_drag_reorder.py

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


def drag(page, handle_selector, dy, nth=0):
    """Simule un glisser du nth-ième élément correspondant à
    handle_selector, de dy pixels vers le bas (négatif pour vers le
    haut)."""
    box = page.eval_on_selector_all(
        handle_selector,
        "(els, nth) => { const r = els[nth].getBoundingClientRect(); return {x: r.x + r.width / 2, y: r.y + r.height / 2}; }",
        nth,
    )
    page.mouse.move(box["x"], box["y"])
    page.mouse.down()
    page.mouse.move(box["x"], box["y"] + dy / 2, steps=5)
    page.mouse.move(box["x"], box["y"] + dy, steps=5)
    page.mouse.up()


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

        print("=== Garde-manger : tri manuel disponible + glisser-déposer ===\n")
        page.evaluate(
            """
            async () => {
                const items = [
                    { id: 'p-a', name: 'Alpha', quantity: 1, unit: 'pièce' },
                    { id: 'p-b', name: 'Beta', quantity: 1, unit: 'pièce' },
                    { id: 'p-c', name: 'Charlie', quantity: 1, unit: 'pièce' },
                ];
                for (const it of items) await storePut('pantry', it);
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                render();
            }
            """
        )
        page.wait_for_timeout(200)
        options = page.evaluate("() => Array.from(document.querySelectorAll('#pantry-sort-select option')).map(o => o.value)")
        check("Le sélecteur de tri du garde-manger propose bien 'manual'", "manual" in options, str(options))
        page.select_option("#pantry-sort-select", "manual")
        page.wait_for_timeout(200)
        check("La poignée de glisser-déposer apparaît en tri manuel", page.is_visible("#app .shopping-item .drag-handle"))
        order_before = page.evaluate("() => Array.from(document.querySelectorAll('#app .shopping-item .label')).map(e => e.textContent)")
        drag(page, "#app .shopping-item .drag-handle", 120, nth=0)
        page.wait_for_timeout(300)
        order_after = page.evaluate("() => Array.from(document.querySelectorAll('#app .shopping-item .label')).map(e => e.textContent)")
        check(
            "Le premier article (Alpha) se retrouve en dernier après un glisser vers le bas",
            order_before[0] == "Alpha — 1 pièce" and order_after[-1] == "Alpha — 1 pièce" and order_after != order_before,
            f"avant={order_before} après={order_after}",
        )
        pantry_orders = page.evaluate("() => state.pantry.map(i => i.order)")
        check(
            "Chaque article a bien reçu une valeur 'order' distincte, persistée en mémoire",
            len(set(pantry_orders)) == 3 and all(isinstance(o, (int, float)) for o in pantry_orders),
            str(pantry_orders),
        )

        print("\n=== Le nouvel ordre survit à un rechargement de page (IndexedDB) ===\n")
        page.reload()
        page.wait_for_timeout(1200)
        page.evaluate("() => setLang('fr')")
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.wait_for_timeout(200)
        page.select_option("#pantry-sort-select", "manual")
        page.wait_for_timeout(200)
        order_reloaded = page.evaluate("() => Array.from(document.querySelectorAll('#app .shopping-item .label')).map(e => e.textContent)")
        check("L'ordre choisi persiste après un rechargement complet de la page", order_reloaded == order_after, str(order_reloaded))

        print("\n=== Les tris existants (nom/péremption) restent inchangés par le tri manuel ===\n")
        page.select_option("#pantry-sort-select", "name")
        page.wait_for_timeout(200)
        order_by_name = page.evaluate("() => Array.from(document.querySelectorAll('#app .shopping-item .label')).map(e => e.textContent)")
        check(
            "Le tri alphabétique reste alphabétique, indépendamment de l'ordre manuel mémorisé",
            order_by_name == ["Alpha — 1 pièce", "Beta — 1 pièce", "Charlie — 1 pièce"],
            str(order_by_name),
        )
        check("Aucune poignée affichée en tri alphabétique (pas en tri manuel)", not page.is_visible("#app .shopping-item .drag-handle"))

        print("\n=== Survie à un aller-retour de sauvegarde locale (export -> import) ===\n")
        roundtrip = page.evaluate(
            """
            async () => {
                const backup = await buildBackupData();
                await importAllData(backup, 'replace');
                return state.pantry.map(i => ({ name: i.name, order: i.order }));
            }
            """
        )
        check(
            "Les valeurs 'order' du garde-manger survivent à un export puis réimport",
            all(isinstance(i["order"], (int, float)) for i in roundtrip) and len(set(i["order"] for i in roundtrip)) == 3,
            str(roundtrip),
        )

        print("\n=== Liste de courses : 3 modes de tri (nom/rayon/manuel) + glisser-déposer ===\n")
        page.evaluate(
            """
            async () => {
                await storeClear('pantry');
                const items = [
                    { id: 's-a', name: 'Pommes', quantity: 1, unit: 'kg', checked: false },
                    { id: 's-b', name: 'Pain', quantity: 1, unit: 'pièce', checked: true },
                    { id: 's-c', name: 'Lait', quantity: 1, unit: 'L', checked: false },
                ];
                for (const it of items) await storePut('shopping', it);
                state.shopping = await storeAll('shopping');
                state.screen = 'shopping';
                render();
            }
            """
        )
        page.wait_for_timeout(200)
        shopping_options = page.evaluate("() => Array.from(document.querySelectorAll('#shopping-sort-select option')).map(o => o.value)")
        check("Le sélecteur de tri de la liste de courses propose nom/rayon/manuel", shopping_options == ["name", "rayon", "manual"], str(shopping_options))
        name_order = page.evaluate("() => Array.from(document.querySelectorAll('#app .shopping-item .label')).map(e => e.textContent)")
        check(
            "Tri par nom : les articles cochés (Pain) restent en fin de liste",
            name_order[-1].startswith("Pain"),
            str(name_order),
        )

        page.select_option("#shopping-sort-select", "manual")
        page.wait_for_timeout(200)
        manual_order_before = page.evaluate("() => Array.from(document.querySelectorAll('#app .shopping-item .label')).map(e => e.textContent)")
        drag(page, "#app .shopping-item .drag-handle", -140, nth=2)
        page.wait_for_timeout(300)
        manual_order_after = page.evaluate("() => Array.from(document.querySelectorAll('#app .shopping-item .label')).map(e => e.textContent)")
        check(
            "Le tri manuel de la liste de courses n'impose pas les articles cochés en fin de liste",
            manual_order_after != manual_order_before and manual_order_after[0] == manual_order_before[-1],
            f"avant={manual_order_before} après={manual_order_after}",
        )

        print("\n=== Formulaire de recette : glisser-déposer des ingrédients (en mémoire) ===\n")
        page.evaluate("async () => { await openRecipeForm(); }")
        page.wait_for_timeout(300)
        page.evaluate(
            """
            () => {
                state.formIngredients = [
                    { name: 'Farine', quantity: 200, unit: 'g' },
                    { name: 'Sucre', quantity: 100, unit: 'g' },
                    { name: 'Beurre', quantity: 50, unit: 'g' },
                ];
                renderIngredientRows(document.getElementById('ing-holder'));
            }
            """
        )
        page.wait_for_timeout(200)
        ing_names_before = page.evaluate("() => Array.from(document.querySelectorAll('.ing-form-row .ing-name')).map(e => e.value)")
        drag(page, ".ing-form-row .drag-handle", 90, nth=0)
        page.wait_for_timeout(300)
        ing_names_after = page.evaluate("() => Array.from(document.querySelectorAll('.ing-form-row .ing-name')).map(e => e.value)")
        state_order = page.evaluate("() => state.formIngredients.map(i => i.name)")
        check(
            "Le glisser-déposer réordonne bien l'affichage ET le tableau en mémoire (formIngredients)",
            ing_names_after == state_order and ing_names_after != ing_names_before and ing_names_after[-1] == "Farine",
            f"avant={ing_names_before} après (DOM)={ing_names_after} après (mémoire)={state_order}",
        )

        # Non-régression du bug d'index périmé : après un glisser-déposer,
        # le bouton "supprimer" d'une ligne doit cibler l'ingrédient
        # RÉELLEMENT affiché sur cette ligne, pas celui qui s'y trouvait
        # avant le déplacement (l'ancien index capturé à la création de
        # la ligne, jamais mis à jour, aurait sinon supprimé le mauvais
        # ingrédient).
        first_name_now = page.evaluate("() => document.querySelector('.ing-form-row .ing-name').value")
        page.click(".ing-form-row .remove-ing")
        page.wait_for_timeout(200)
        remaining = page.evaluate("() => state.formIngredients.map(i => i.name)")
        check(
            f"Le bouton 'supprimer' de la 1ère ligne cible bien l'ingrédient qui y est affiché ('{first_name_now}'), pas un index périmé",
            first_name_now not in remaining,
            str(remaining),
        )

        print("\n=== Enregistrement de la recette : l'ordre glissé-déposé est conservé ===\n")
        page.evaluate(
            """
            () => {
                state.formIngredients = [
                    { name: 'Farine', quantity: 200, unit: 'g' },
                    { name: 'Sucre', quantity: 100, unit: 'g' },
                ];
                renderIngredientRows(document.getElementById('ing-holder'));
            }
            """
        )
        page.wait_for_timeout(200)
        drag(page, ".ing-form-row .drag-handle", 60, nth=0)
        page.wait_for_timeout(300)
        page.fill("#f-name", "Recette drag test")
        page.click("#recipe-form button[type=submit]")
        page.wait_for_timeout(300)
        saved_order = page.evaluate("() => { const r = state.recipes.find(x => x.name === 'Recette drag test'); return r ? r.ingredients.map(i => i.name) : null; }")
        check("L'ordre des ingrédients glissés-déposés est bien celui enregistré dans la recette", saved_order == ["Sucre", "Farine"], str(saved_order))

        print("\n=== Aucun débordement horizontal introduit par la nouvelle poignée (320px) ===\n")
        page2 = browser.new_page(viewport={"width": 320, "height": 844})
        page2.on("pageerror", lambda exc: errors.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(1000)
        page2.evaluate("() => setLang('fr')")
        page2.evaluate(
            """
            async () => {
                await storePut('pantry', { id: 'ov-1', name: 'Article test débordement', quantity: 1, unit: 'pièce' });
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                render();
            }
            """
        )
        page2.wait_for_timeout(200)
        page2.select_option("#pantry-sort-select", "manual")
        page2.wait_for_timeout(200)
        overflow_info = page2.evaluate(
            """
            () => {
                const row = document.querySelector('.shopping-item');
                return { rowWidth: row.getBoundingClientRect().width, rowScrollWidth: row.scrollWidth };
            }
            """
        )
        check(
            "La ligne du garde-manger avec poignée ne déborde pas horizontalement à 320px",
            overflow_info["rowScrollWidth"] <= overflow_info["rowWidth"] + 1,
            str(overflow_info),
        )
        page2.close()

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
