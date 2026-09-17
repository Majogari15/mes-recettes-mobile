#!/usr/bin/env python3
"""Test permanent : mise en page sur des écrans plus grands qu'un
téléphone (tablette, tablette pliable dépliée) — voir
TESTS_NON_REGRESSION.md point 90 (audit étendu, manque "compatibilité
multi-appareils" par rapport à une checklist QA générique). Complète
les tests existants qui ne couvraient que 390px/320px (téléphone).

Vérifie l'absence de débordement horizontal (scrollbar horizontale) et
que les contrôles principaux restent bien dans la fenêtre visible — pas
une optimisation visuelle dédiée tablette (non demandée), seulement
l'absence de mise en page cassée.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_responsive_large_screens.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VIEWPORTS = {
    "tablette portrait (768x1024)": {"width": 768, "height": 1024},
    "tablette paysage (1024x768)": {"width": 1024, "height": 768},
    "pliable dépliée (673x841, ex. Galaxy Z Fold)": {"width": 673, "height": 841},
}
SCREENS = ["home", "recipes", "form", "recipe", "shopping", "pantry", "planning"]


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
        errors = []

        for label, viewport in VIEWPORTS.items():
            print(f"\n=== {label} ===\n")
            page = browser.new_page(viewport=viewport)
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(base_url, timeout=8000)
            page.wait_for_timeout(1000)
            page.evaluate("() => setLang('fr')")
            page.evaluate(
                """
                async () => {
                    const recipe = { id: 'resp-1', name: 'Recette test tablette', category: 'Plat', persons: 2,
                        ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }], steps: 'Etape 1', prepTime: 10, cookTime: 20 };
                    await storePut('recipes', recipe);
                    state.recipes = await storeAll('recipes');
                    state.currentRecipeId = 'resp-1';
                    state.editingRecipeId = 'resp-1';
                }
                """
            )

            for screen in SCREENS:
                page.evaluate("(s) => { state.screen = s; render(); }", screen)
                page.wait_for_timeout(150)
                metrics = page.evaluate(
                    """
                    () => ({
                        scrollWidth: document.documentElement.scrollWidth,
                        clientWidth: document.documentElement.clientWidth,
                        navRect: document.querySelector('.bottom-nav')
                            ? document.querySelector('.bottom-nav').getBoundingClientRect()
                            : null,
                    })
                    """
                )
                no_overflow = metrics["scrollWidth"] <= metrics["clientWidth"] + 2
                check(
                    f"Écran '{screen}' : pas de débordement horizontal",
                    no_overflow,
                    f"scrollWidth={metrics['scrollWidth']} clientWidth={metrics['clientWidth']}",
                )
                if metrics["navRect"]:
                    nav_in_bounds = metrics["navRect"]["right"] <= metrics["clientWidth"] + 2 and metrics["navRect"]["left"] >= -2
                    check(f"Écran '{screen}' : la barre de navigation reste dans la largeur visible", nav_in_bounds)

            page.close()

        check("Aucune erreur JS sur tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
