#!/usr/bin/env python3
"""
Test permanent vérifiant qu'une information de couverture (temps de
préparation notamment) survit jusqu'à la recette fusionnée finale —
demandé après un test physique où "35 min" semblait absent du PDF
final produit sur un vrai appareil, sans qu'il soit possible de
déterminer avec certitude si la perte avait lieu à l'OCR, au choix de
section ou pendant la fusion (voir TESTS_NON_REGRESSION.md).

Ce test utilise le vrai texte OCR de la couverture Barramundi (issu du
corpus, tests/ocr-corpus/photo3_barramundi_couverture.json) combiné à
des photos synthétiques minimales pour ingrédients et préparation,
pour vérifier spécifiquement le comportement de
mergeMultiPhotoResults — pas l'OCR lui-même, dont la variabilité selon
l'appareil reste un facteur externe à ce test (voir tests/README.md).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_full_merge_pipeline.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import glob
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


def main():
    cover_path = os.path.join(CORPUS_DIR, "photo3_barramundi_couverture.json")
    with open(cover_path, encoding="utf-8") as f:
        cover_entry = json.load(f)

    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"

    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(500)

        result = page.evaluate(
            """
            ([coverRawText, coverLayoutText]) => {
                // Photo 1 : couverture réelle (issue du corpus)
                const coverParsed = parseOcrRecipeText(coverRawText);
                const coverSection = detectPhotoSection(coverParsed);
                const coverData = deriveSectionDataForPhoto(coverRawText, coverSection || 'general', coverLayoutText, null);

                // Photo 2 : ingrédients minimalistes (synthétique, le
                // contenu exact n'est pas ce qui est testé ici)
                const ingText = "Ingrédients pour 2 personnes\\nSel 1 pincée";
                const ingParsed = parseOcrRecipeText(ingText);
                const ingSection = detectPhotoSection(ingParsed);
                const ingData = deriveSectionDataForPhoto(ingText, ingSection || 'ingredients', ingText, null);

                // Photo 3 : préparation minimaliste (synthétique)
                const prepText = "Préparation\\n1. Cuire le plat.";
                const prepParsed = parseOcrRecipeText(prepText);
                const prepSection = detectPhotoSection(prepParsed);
                const prepData = deriveSectionDataForPhoto(prepText, prepSection || 'preparation', prepText, null);

                const entries = [
                    { status: 'done', section: coverSection, sectionData: coverData },
                    { status: 'done', section: ingSection, sectionData: ingData },
                    { status: 'done', section: prepSection, sectionData: prepData },
                ];
                const merged = mergeMultiPhotoResults(entries, 2);
                return {
                    coverPrepTime: coverData.prepTime,
                    coverSection,
                    mergedPrepTime: merged.prepTime,
                    mergedName: merged.name,
                };
            }
            """,
            [cover_entry["rawText"], cover_entry["layoutText"]],
        )

        print("=== Test : le temps de préparation survit à la fusion complète ===\n")
        print(f"Section détectée pour la couverture : {result['coverSection']} (attendu : general)")
        print(f"prepTime sur la photo couverture seule : {result['coverPrepTime']} (attendu : 35)")
        print(f"prepTime après fusion des 3 photos : {result['mergedPrepTime']} (attendu : 35)")
        print(f"Nom après fusion : {result['mergedName']!r}")

        ok = (
            result["coverSection"] == "general"
            and result["coverPrepTime"] == 35
            and result["mergedPrepTime"] == 35
        )
        if not ok:
            all_ok = False
            print("\n❌ ÉCHEC : le temps de préparation n'a pas survécu jusqu'à la fusion")
        else:
            print("\n✅ OK")

        browser.close()

    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
