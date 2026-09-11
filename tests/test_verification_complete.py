#!/usr/bin/env python3
"""
Tests permanents pour 3 défauts découverts lors d'une vérification
complète sur toutes les vraies photos du projet (voir
TESTS_NON_REGRESSION.md point 49) :

1. Le découpage en 2 colonnes des ingrédients (v192) s'appliquait à
   tort à des photos à une seule colonne, fragmentant chaque ligne en
   deux et produisant des dizaines d'ingrédients incohérents au lieu
   d'une dizaine de vrais ingrédients.
2. Une photo d'ingrédients cadrée sans la ligne d'en-tête "Ingrédients
   pour N personnes" visible se retrouvait classée à tort
   "Préparation", avec zéro ingrédient extrait.
3. Le nombre de personnes, quand réellement inconnu, était deviné
   silencieusement à "4" pour diviser les quantités — faussant les
   quantités STOCKÉES, pas seulement un affichage.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_verification_complete.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import json
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(os.path.dirname(__file__), "ocr-corpus")


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


# Texte OCR réel d'une photo Carbonara (Marmiton) cadrée sans la ligne
# d'en-tête "Ingrédients" visible.
CARBONARA_NO_MARKER_TEXT = """Gousse d'ail
Oignon 1 pieces
Persil* 1 sachet (
Spaghetti 180 g
Chapelure panko % sachet(s
Noix concassées 1 sachet(s)
Lardons fumés sans nitrite* 150g
-reme lig lide* i 1 paquet(s
E 1 sachet(s)
. % piéce(s)
i lcs
1 2¢s
selon votre golit
ur
nell
; Par portion Pour 100g
4364 /1043 1259 /301
: 63 18
26,1 >
1 82 2
8,4 2,4
5 1
37 11
- 3 :
: °
allergenes. En cas
avant de cuisiner. Les"""


def main():
    with open(os.path.join(CORPUS_DIR, "photo_cassoulet_ingredients_2colonnes.json"), encoding="utf-8") as f:
        cassoulet = json.load(f)
    with open(os.path.join(CORPUS_DIR, "photo4_barramundi_ingredients.json"), encoding="utf-8") as f:
        barramundi = json.load(f)

    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"

    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(500)

        print("=== 1. Le découpage en 2 colonnes ne doit jamais fragmenter une liste à une seule colonne ===\n")
        result = page.evaluate(
            """
            ([rawText, layoutText]) => {
                const detected = detectPhotoSection(parseOcrRecipeText(rawText), rawText);
                const sectionData = deriveSectionDataForPhoto(rawText, detected || 'ingredients', layoutText, null, null);
                return sectionData.ingredients.length;
            }
            """,
            [barramundi["rawText"], barramundi["layoutText"]],
        )
        ok = result <= 15
        status = "✅ OK" if ok else "❌ ÉCHEC"
        print(f"{status}  vraie photo Barramundi (une colonne), sans découpage 2 colonnes")
        print(f"        {result} ingrédients obtenus (doit rester raisonnable, ≤15 — 11 attendus)")
        if not ok:
            all_ok = False
        print()

        # Confirme aussi que le garde-fou de qualité protège même
        # quand computeTwoColumnIngredients simule un mauvais résultat
        # (beaucoup d'items sans quantité, comme une vraie fragmentation
        # à tort produirait).
        result2 = page.evaluate(
            """
            ([rawText, layoutText]) => {
                const fakeBadTwoColumn = Array.from({length: 30}, (_, i) => ({ name: 'fragment' + i, quantity: null, unit: 'pièce', confidence: 'uncertain' }));
                const sectionData = deriveSectionDataForPhoto(rawText, 'ingredients', layoutText, null, fakeBadTwoColumn);
                return sectionData.ingredients.length;
            }
            """,
            [barramundi["rawText"], barramundi["layoutText"]],
        )
        ok2 = result2 <= 15
        status2 = "✅ OK" if ok2 else "❌ ÉCHEC"
        print(f"{status2}  garde-fou qualité : un faux résultat 2 colonnes à faible qualité (30 fragments sans quantité) est rejeté")
        print(f"        {result2} ingrédients obtenus (doit rester raisonnable, ≤15)")
        if not ok2:
            all_ok = False
        print()

        print("=== 2. Photo d'ingrédients sans ligne d'en-tête visible ===\n")
        result3 = page.evaluate(
            "(t) => detectPhotoSection(parseOcrRecipeText(t), t)",
            CARBONARA_NO_MARKER_TEXT,
        )
        ok3 = result3 == "ingredients"
        status3 = "✅ OK" if ok3 else "❌ ÉCHEC"
        print(f"{status3}  cas réel Carbonara, cadrage sans \"Ingrédients pour N personnes\" visible")
        print(f"        section obtenue={result3!r} (attendu 'ingredients')")
        if not ok3:
            all_ok = False
        print()

        print("=== 3. Personnes réellement inconnues : pas de division silencieuse par 4 ===\n")
        result4 = page.evaluate(
            """
            () => {
                const photos = [{ status: 'done', sectionData: { name: 'Test', ingredients: [{name:'Spaghetti', quantity: 180, unit:'g'}], description: '', persons: null, prepTime: null, cookTime: null } }];
                return mergeMultiPhotoResults(photos, null);
            }
            """
        )
        ok4 = result4["persons"] is None and result4["ingredients"][0]["quantity"] == 180
        status4 = "✅ OK" if ok4 else "❌ ÉCHEC"
        print(f"{status4}  personnes inconnues sur toutes les photos → pas de division par 4 deviné")
        print(f"        persons={result4['persons']!r} (attendu None), quantité={result4['ingredients'][0]['quantity']!r} (attendu 180, non divisée)")
        if not ok4:
            all_ok = False
        print()

        result5 = page.evaluate(
            """
            () => {
                const photos = [{ status: 'done', sectionData: { name: 'Test', ingredients: [{name:'Sel', quantity: 500, unit:'g'}], description: '', persons: 2, prepTime: null, cookTime: null } }];
                return mergeMultiPhotoResults(photos, null);
            }
            """
        )
        ok5 = result5["persons"] == 2 and result5["ingredients"][0]["quantity"] == 250
        status5 = "✅ OK" if ok5 else "❌ ÉCHEC"
        print(f"{status5}  non-régression : personnes connues (2) → division normale toujours correcte")
        print(f"        persons={result5['persons']!r} (attendu 2), quantité={result5['ingredients'][0]['quantity']!r} (attendu 250)")
        if not ok5:
            all_ok = False
        print()

        browser.close()

    httpd.shutdown()

    print("=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
