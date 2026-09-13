#!/usr/bin/env python3
"""
Test permanent pour la section allergènes dans l'export PDF de
recette — absente jusqu'ici de drawRecipeContent, alors que le champ
recipe.allergens existe et est affiché à l'écran. Voir
TESTS_NON_REGRESSION.md, point 64.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pdf_allergens.py

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
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => { setLang('fr'); }")

        print("=== Recette avec allergènes : la section apparaît dans le PDF ===\n")
        page.evaluate(
            """
            async () => {
                await storePut('recipes', { id: 'r1', name: 'Avec allergenes', category: 'Dessert', ingredients: [{name:'Beurre', quantity:1, unit:'pièce'}], allergens: ['Gluten', 'Lactose'], description: 'Test', notes: '', personalRating: 0, photo: null, createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], timesCooked: 0, defaultPersons: 2 });
                state.recipes = await storeAll('recipes');
            }
            """
        )
        result = page.evaluate(
            """
            () => {
                const recipe = state.recipes[0];
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF({ unit: "mm", format: "a4" });
                const margin = 20;
                const maxWidth = doc.internal.pageSize.getWidth() - margin * 2;
                const drawnTexts = [];
                const originalText = doc.text.bind(doc);
                doc.text = (text, x, y) => { drawnTexts.push(text); return originalText(text, x, y); };
                drawRecipeContent(doc, recipe, 2, margin, maxWidth, false);
                return drawnTexts;
            }
            """
        )
        ok = "Allergènes" in result and any("Gluten" in t and "Lactose" in t for t in result)
        status = "✅ OK" if ok else "❌ ÉCHEC"
        print(f"{status}  textes dessinés : {result}")
        if not ok:
            all_ok = False
        print()

        print("=== Recette sans allergène : aucune section vide ou parasite ===\n")
        page.evaluate(
            """
            async () => {
                await storePut('recipes', { id: 'r2', name: 'Sans allergene', category: 'Dessert', ingredients: [{name:'Sucre', quantity:1, unit:'pièce'}], allergens: [], description: 'Test', notes: '', personalRating: 0, photo: null, createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], timesCooked: 0, defaultPersons: 2 });
                state.recipes = await storeAll('recipes');
            }
            """
        )
        result2 = page.evaluate(
            """
            () => {
                const recipe = state.recipes.find(r => r.id === 'r2');
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF({ unit: "mm", format: "a4" });
                const margin = 20;
                const maxWidth = doc.internal.pageSize.getWidth() - margin * 2;
                const drawnTexts = [];
                const originalText = doc.text.bind(doc);
                doc.text = (text, x, y) => { drawnTexts.push(text); return originalText(text, x, y); };
                drawRecipeContent(doc, recipe, 2, margin, maxWidth, false);
                return drawnTexts;
            }
            """
        )
        ok2 = "Allergènes" not in result2
        status2 = "✅ OK" if ok2 else "❌ ÉCHEC"
        print(f"{status2}  textes dessinés : {result2}")
        if not ok2:
            all_ok = False
        print()

        print("Erreurs JS sur tout le parcours:", errors if errors else "AUCUNE")
        if errors:
            all_ok = False

        browser.close()

    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
