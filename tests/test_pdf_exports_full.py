#!/usr/bin/env python3
"""Test permanent : les 3 exports PDF (recette seule, liste de courses,
livre de cuisine multi-recettes) produisent réellement un fichier PDF
valide de bout en bout — pas seulement que les bons textes sont
"dessinés" (déjà couvert par test_pdf_allergens.py pour la recette
seule), mais que `doc.save()` aboutit à un vrai téléchargement non
vide, structurellement un PDF.

Ajouté lors de l'audit de régression suivant la mise à jour de jsPDF
2.5.1 → 4.2.1 (voir TESTS_NON_REGRESSION.md points 90-91) : les 3
fonctions d'export (`exportRecipePdf`, `exportShoppingListPdf`,
`exportCookbookPdf`) n'étaient, avant ce test, jamais exercées jusqu'à
`doc.save()` par la suite automatisée — seul le contenu texte de la
recette seule l'était.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pdf_exports_full.py

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


def is_valid_pdf(path):
    with open(path, "rb") as f:
        head = f.read(5)
    return head == b"%PDF-" and os.path.getsize(path) > 500


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
        page = browser.new_page(viewport={"width": 390, "height": 844}, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")

        print("=== Export PDF d'une recette seule (sans photo, pas de confirmation à gérer) ===\n")
        page.evaluate(
            """
            async () => {
                const recipe = {
                    id: 'pdf-1', name: 'Recette export test', category: 'Plat', persons: 2,
                    ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }],
                    description: 'Une description.', notes: '', allergens: [], photo: null,
                    createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], timesCooked: 0, defaultPersons: 2,
                };
                await storePut('recipes', recipe);
                state.recipes = await storeAll('recipes');
            }
            """
        )
        with page.expect_download(timeout=8000) as dl_info:
            page.evaluate("async () => { await exportRecipePdf(state.recipes.find(r => r.id === 'pdf-1'), 2); }")
        download = dl_info.value
        pdf_path = download.path()
        check("Le PDF de recette téléchargé est un fichier PDF valide et non vide", is_valid_pdf(pdf_path), f"{os.path.getsize(pdf_path)} octets")

        print("\n=== Export PDF de la liste de courses (avec tri par rayon) ===\n")
        page.evaluate(
            """
            async () => {
                state.shopping = [
                    { name: 'Tomate', quantity: 3, unit: 'pièce', checked: false },
                    { name: 'Lait', quantity: 1, unit: 'L', checked: true },
                ];
                state.shoppingSortByRayon = true;
            }
            """
        )
        with page.expect_download(timeout=8000) as dl_info2:
            page.evaluate("async () => { await exportShoppingListPdf(); }")
        download2 = dl_info2.value
        pdf_path2 = download2.path()
        check("Le PDF de liste de courses téléchargé est un fichier PDF valide et non vide", is_valid_pdf(pdf_path2), f"{os.path.getsize(pdf_path2)} octets")

        print("\n=== Export PDF \"livre de cuisine\" (plusieurs recettes, sommaire avec numéros de page) ===\n")
        page.evaluate(
            """
            async () => {
                const recipes = [];
                for (let i = 0; i < 3; i++) {
                    const r = {
                        id: `pdf-book-${i}`, name: `Recette livre ${i}`, category: 'Plat', persons: 2,
                        ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }],
                        description: 'Description.', notes: '', allergens: [], photo: null,
                        createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], timesCooked: 0, defaultPersons: 2,
                    };
                    await storePut('recipes', r);
                    recipes.push(r);
                }
                state.recipes = await storeAll('recipes');
                window.__cookbookTestRecipes = state.recipes.filter(r => r.id.startsWith('pdf-book-'));
            }
            """
        )
        with page.expect_download(timeout=8000) as dl_info3:
            page.evaluate("async () => { await exportCookbookPdf(window.__cookbookTestRecipes, false); }")
        download3 = dl_info3.value
        pdf_path3 = download3.path()
        check("Le PDF \"livre de cuisine\" téléchargé est un fichier PDF valide et non vide", is_valid_pdf(pdf_path3), f"{os.path.getsize(pdf_path3)} octets")
        check("Le PDF \"livre de cuisine\" est nettement plus gros qu'une recette seule (page de garde + sommaire + 3 recettes)", os.path.getsize(pdf_path3) > os.path.getsize(pdf_path), f"{os.path.getsize(pdf_path3)} vs {os.path.getsize(pdf_path)} octets")

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
