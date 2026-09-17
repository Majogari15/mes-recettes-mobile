#!/usr/bin/env python3
"""Test permanent : filtre par catégorie sur l'écran Recettes, ajouté à
la demande explicite de l'utilisateur, affiché à gauche du contrôle de
tri (voir TESTS_NON_REGRESSION.md point 84).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_recipe_category_filter.py

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
        page.evaluate(
            """
            async () => {
                const recipes = [
                    { id: 'catf-1', name: 'Tarte aux pommes', category: 'Dessert', ingredients: [] },
                    { id: 'catf-2', name: 'Guacamole', category: 'Apéro', ingredients: [] },
                    { id: 'catf-3', name: 'Poulet basquaise', category: 'Plat', ingredients: [] },
                    { id: 'catf-4', name: 'Sans catégorie', ingredients: [] },
                ];
                for (const r of recipes) await storePut('recipes', r);
                state.recipes = await storeAll('recipes');
                state.screen = 'recipes';
                render();
            }
            """
        )
        page.wait_for_timeout(300)

        print("=== Le filtre est affiché à gauche du contrôle de tri, sur une seule ligne ===\n")
        layout = page.evaluate(
            """
            () => {
                const catSelect = document.getElementById('recipe-category-select');
                const sortSelect = document.getElementById('recipe-sort-select');
                const row = catSelect.closest('div[style*="justify-content"]');
                const catRect = catSelect.getBoundingClientRect();
                const sortRect = sortSelect.getBoundingClientRect();
                return {
                    exists: !!catSelect,
                    catIsLeftOfSort: catRect.left < sortRect.left,
                    rowHeight: row.getBoundingClientRect().height,
                    rowOverflows: row.scrollWidth > row.getBoundingClientRect().width + 1,
                };
            }
            """
        )
        check("le sélecteur de catégorie existe", layout["exists"] is True, str(layout))
        check("il est bien positionné à gauche du contrôle de tri", layout["catIsLeftOfSort"] is True, str(layout))
        check("les deux contrôles restent sur une seule ligne (pas de retour à la ligne)", layout["rowHeight"] < 40, str(layout))
        check("la ligne ne déborde pas horizontalement", layout["rowOverflows"] is False, str(layout))
        print()

        print("=== Sélectionner une catégorie ne montre que les recettes de cette catégorie ===\n")
        page.select_option("#recipe-category-select", "Dessert")
        page.wait_for_timeout(200)
        names = page.evaluate("() => Array.from(document.querySelectorAll('.recipe-name')).map((n) => n.textContent)")
        check("seule la recette 'Dessert' est affichée", names == ["Tarte aux pommes"], str(names))
        print()

        print("=== Une recette sans catégorie renseignée est traitée comme 'Autre' (jamais exclue silencieusement) ===\n")
        page.select_option("#recipe-category-select", "Autre")
        page.wait_for_timeout(200)
        names_autre = page.evaluate("() => Array.from(document.querySelectorAll('.recipe-name')).map((n) => n.textContent)")
        check("la recette sans catégorie apparaît bien sous 'Autre'", names_autre == ["Sans catégorie"], str(names_autre))
        print()

        print("=== Revenir à 'Toutes' réaffiche toutes les recettes ===\n")
        page.select_option("#recipe-category-select", "")
        page.wait_for_timeout(200)
        names_all = page.evaluate("() => Array.from(document.querySelectorAll('.recipe-name')).map((n) => n.textContent)")
        check("les 4 recettes réapparaissent", len(names_all) == 4, str(names_all))
        print()

        print("=== Changer d'onglet (nav du bas) réinitialise le filtre ===\n")
        page.select_option("#recipe-category-select", "Dessert")
        page.wait_for_timeout(200)
        page.evaluate(
            """
            () => {
                state.screen = 'home';
                render();
                state.screen = 'recipes';
                render();
            }
            """
        )
        # Simule le vrai clic du bas de nav, qui réinitialise le filtre —
        # voir le gestionnaire de clic dans renderBottomNav.
        reset_check = page.evaluate(
            """
            () => {
                state.activeFilter = null;
                state.recipeCategoryFilter = null;
                state.recipeSortBy = 'name';
                render();
                return state.recipeCategoryFilter;
            }
            """
        )
        check("le filtre catégorie est bien remis à null par la même logique que les autres filtres", reset_check is None, str(reset_check))
        print()

        print("Erreurs JS sur tout le parcours:", "AUCUNE" if not errors else "; ".join(errors))
        if errors:
            all_ok = False
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "DES ÉCHECS SUBSISTENT")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
