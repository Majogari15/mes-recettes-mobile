#!/usr/bin/env python3
"""
Tests permanents pour le format de sauvegarde partagé avec l'application
Windows (voir TESTS_NON_REGRESSION.md, chantier "compatibilité des
sauvegardes") : module ZIP maison (lecture/écriture, sans dépendance
externe), et export/import au format partagé (recettes+photos,
ingrédients, garde-manger, personnalisations).

Ce fichier ne teste que le côté application mobile (JavaScript) — la
compatibilité réelle avec l'application Windows (Python) a été vérifiée
manuellement en faisant circuler de vraies archives dans les deux sens
entre les deux vrais codes (voir TESTS_NON_REGRESSION.md pour le détail),
mais ne peut pas être automatisée ici : l'application Windows utilise
tkinter, qui n'est pas installable dans cet environnement de test.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_shared_backup.py

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
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(500)

        print("=== Module ZIP maison : aller-retour écriture/lecture ===\n")
        result = page.evaluate(
            """
            async () => {
                const entries = [
                    { name: 'recipes.json', data: new TextEncoder().encode(JSON.stringify({hello: 'world', accents: 'éàçù'})) },
                    { name: 'images/photo1.jpg', data: new Uint8Array([255, 216, 255, 224, 0, 1, 2, 3, 4, 5]) },
                ];
                const blob = await buildZipFile(entries);
                const buffer = await blob.arrayBuffer();
                const parsed = await parseZipFile(buffer);
                return {
                    fileCount: parsed.length,
                    jsonOk: new TextDecoder().decode(parsed.find(f => f.name === 'recipes.json').data) === '{"hello":"world","accents":"éàçù"}',
                    photoOk: JSON.stringify(Array.from(parsed.find(f => f.name === 'images/photo1.jpg').data)) === JSON.stringify([255, 216, 255, 224, 0, 1, 2, 3, 4, 5]),
                };
            }
            """
        )
        ok = result["fileCount"] == 2 and result["jsonOk"] and result["photoOk"]
        status = "✅ OK" if ok else "❌ ÉCHEC"
        print(f"{status}  aller-retour ZIP (texte UTF-8 avec accents + données binaires)")
        print(f"        {result}")
        if not ok:
            all_ok = False
        print()

        print("=== Export/import au format partagé : aller-retour complet ===\n")
        result2 = page.evaluate(
            """
            async () => {
                const photoDataUri = "data:image/jpeg;base64," + btoa("fake jpeg bytes test permanent");
                const recipe = {
                    id: 'test-r1', name: 'Recette de test', category: 'Dessert', difficulty: 'Facile',
                    defaultPersons: 4, prepTime: 20, cookTime: 30, favorite: true, vegetarian: true,
                    wishlist: false, ingredients: [{name:'pommes', quantity:4, unit:'pièce'}],
                    allergens: ['gluten'], description: 'Une description', notes: 'Une note',
                    personalRating: 5, familyOpinion: '', improvementNotes: '', actualDifficulty: '',
                    photo: photoDataUri, createdAt: '2026-01-01T00:00:00.000Z',
                    cookLog: [{date:'2026-01-05T12:00:00.000Z', note:'Bon', photo:null}], timesCooked: 1,
                };
                await storePut('recipes', recipe);
                await storePut('ingredients', { name: 'pommes' });

                const zipBlob = await buildSharedBackupZip();
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                for (const i of await storeAll('ingredients')) await storeDelete('ingredients', i.name);

                const zipFile = new File([zipBlob], 'test.zip', { type: 'application/zip' });
                const report = await restoreFromSharedZip(zipFile, false);
                const recipesAfter = await storeAll('recipes');

                return {
                    report,
                    recipe: recipesAfter[0],
                    photoMatches: recipesAfter[0] && recipesAfter[0].photo === photoDataUri,
                };
            }
            """
        )
        ok2 = (
            result2["report"]["recipesImported"] == 1
            and result2["recipe"]["name"] == "Recette de test"
            and result2["recipe"]["defaultPersons"] == 4
            and result2["recipe"]["ingredients"][0]["name"] == "pommes"
            and result2["photoMatches"]
        )
        status2 = "✅ OK" if ok2 else "❌ ÉCHEC"
        print(f"{status2}  export puis réimport complet (recette avec photo, ingrédients)")
        print(f"        rapport={result2['report']}, photo identique={result2['photoMatches']}")
        if not ok2:
            all_ok = False
        print()

        browser.close()

    httpd.shutdown()

    print("=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
