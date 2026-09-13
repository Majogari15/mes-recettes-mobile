#!/usr/bin/env python3
"""
Test permanent pour l'extraction d'ingrédients à partir d'un tableau à
2 colonnes visuelles (nom à gauche, quantité à droite) reconstruit à
partir des coordonnées réelles des mots — cas des fiches HelloFresh où
les ingrédients ne sont pas une liste à puces mais un vrai tableau.
Voir TESTS_NON_REGRESSION.md, point 65.

Utilise des coordonnées synthétiques plutôt qu'une vraie image : cette
extraction dépend de données géométriques (bbox par mot) qui ne
peuvent pas être rejouées depuis du texte déjà extrait comme le fait
le corpus OCR habituel (tests/ocr-corpus) — un test unitaire direct
sur la structure de données est donc plus adapté ici, et surtout
indépendant de la non-déterminisme de l'OCR réel.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_table_ingredients.py

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


def make_row(name, x0_name, x1_name, qty_text, x0_qty, x1_qty):
    """Construit une ligne synthétique : un mot pour le nom (peut
    contenir des espaces, traité comme un seul "mot" ici par
    simplicité), un ou deux mots pour la quantité, séparés par un
    grand espace horizontal (au-delà du seuil détecté)."""
    words = [{"text": name, "bbox": {"x0": x0_name, "x1": x1_name}}]
    if qty_text:
        words.append({"text": qty_text, "bbox": {"x0": x0_qty, "x1": x1_qty}})
    return {"words": words}


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

        print("=== Tableau propre à 2 colonnes : reconstruction correcte ===\n")
        data = {
            "width": 1000,
            "blocks": [{"paragraphs": [{"lines": [
                make_row("Oignon", 50, 150, "1 pièce(s)", 400, 490),
                make_row("Carotte", 50, 160, "2 pièce(s)", 400, 490),
                make_row("Farine", 50, 150, "200 g", 400, 460),
            ]}]}],
        }
        result = page.evaluate("(data) => reconstructTableRowsFromBlocks(data)", data)
        expected = "Oignon | 1 pièce(s)\nCarotte | 2 pièce(s)\nFarine | 200 g"
        ok = result == expected
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {result!r}")
        if not ok:
            all_ok = False
        print()

        print("=== Analyse en ingrédients propres ===\n")
        ingredients = page.evaluate(
            "(data) => parseTableRowsIngredients(reconstructTableRowsFromBlocks(data))", data
        )
        ok = (
            len(ingredients) == 3
            and ingredients[0]["name"] == "Oignon" and ingredients[0]["quantity"] == 1
            and ingredients[1]["name"] == "Carotte" and ingredients[1]["quantity"] == 2
            and ingredients[2]["name"] == "Farine" and ingredients[2]["quantity"] == 200
        )
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {ingredients}")
        if not ok:
            all_ok = False
        print()

        print("=== Arrêt correct au tableau nutritionnel ===\n")
        data_with_nutrition = {
            "width": 1000,
            "blocks": [{"paragraphs": [{"lines": [
                make_row("Oignon", 50, 150, "1 pièce(s)", 400, 490),
                make_row("Carotte", 50, 160, "2 pièce(s)", 400, 490),
                make_row("Energie (kJ/kcal)", 50, 200, "2657 /635", 400, 490),
                make_row("Protéines(g)", 50, 150, "31", 400, 420),
            ]}]}],
        }
        ingredients2 = page.evaluate(
            "(data) => parseTableRowsIngredients(reconstructTableRowsFromBlocks(data))",
            data_with_nutrition,
        )
        names = [i["name"] for i in ingredients2]
        ok = names == ["Oignon", "Carotte"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {names}")
        if not ok:
            all_ok = False
        print()

        print("=== Arrêt même si l'en-tête nutritionnel est trop déformé pour être reconnu (régression réelle trouvée sur la photo Barramundi) ===\n")
        data_garbled_header = {
            "width": 1000,
            "blocks": [{"paragraphs": [{"lines": [
                make_row("Oignon", 50, 150, "1 pièce(s)", 400, 490),
                make_row("Carotte", 50, 160, "2 pièce(s)", 400, 490),
                # En-tête tellement déformé par l'OCR qu'aucun mot-clé
                # nutrition/énergie/allergène n'y est plus reconnaissable
                # ("(kifkeal)" au lieu de "(kJ/kcal)", constaté sur une
                # vraie photo) — seule la signature numérique
                # "nombre/nombre" reste un signal fiable.
                make_row("(kifkeal)", 50, 150, "2745 /656", 400, 490),
            ]}]}],
        }
        ingredients3 = page.evaluate(
            "(data) => parseTableRowsIngredients(reconstructTableRowsFromBlocks(data))",
            data_garbled_header,
        )
        names3 = [i["name"] for i in ingredients3]
        ok = names3 == ["Oignon", "Carotte"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {names3}")
        if not ok:
            all_ok = False
        print()

        print("=== Ligne sans grand espace (pas de tableau) ignorée ===\n")
        data_no_gap = {
            "width": 1000,
            "blocks": [{"paragraphs": [{"lines": [
                {"words": [
                    {"text": "Une", "bbox": {"x0": 50, "x1": 90}},
                    {"text": "phrase", "bbox": {"x0": 95, "x1": 150}},
                    {"text": "normale", "bbox": {"x0": 155, "x1": 220}},
                ]},
            ]}]}],
        }
        result_no_gap = page.evaluate("(data) => reconstructTableRowsFromBlocks(data)", data_no_gap)
        ok = result_no_gap is None
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {result_no_gap!r}")
        if not ok:
            all_ok = False
        print()

        print("=== Fusion : un ingrédient sans quantité (ex. 'Gousse d'ail') n'est pas perdu ===\n")
        raw_text_with_noqty_item = "Gousse d'ail\nOignon 1 pieces\nPersil 1 sachet\nSpaghetti 180 g\nNoix concassées 1 sachet\nLardons fumés 150g"
        merge_result = page.evaluate(
            """
            ([rawText, data]) => {
                const tableText = reconstructTableRowsFromBlocks(data);
                const parsed = parseOcrRecipeText(rawText);
                return deriveSectionDataForPhoto(rawText, "ingredients", rawText, null, null, tableText).ingredients.map(i => i.name);
            }
            """,
            [raw_text_with_noqty_item, {
                "width": 1000,
                "blocks": [{"paragraphs": [{"lines": [
                    make_row("Oignon", 50, 150, "1 pieces", 400, 490),
                    make_row("Persil", 50, 150, "1 sachet", 400, 490),
                    make_row("Spaghetti", 50, 150, "180 g", 400, 490),
                    make_row("Noix concassées", 50, 180, "1 sachet", 400, 490),
                    make_row("Lardons fumés", 50, 160, "150g", 400, 490),
                ]}]}],
            }],
        )
        ok = any("Gousse" in n for n in merge_result)
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {merge_result}")
        if not ok:
            all_ok = False
        print()

        print("=== Motif '2 ingrédients par ligne' (ex. photo Butternut réelle) correctement séparé en 2 paires ===\n")
        # Reproduit fidèlement la géométrie réelle trouvée sur une photo
        # "Persil 1/2 bouquet Pois chiches (conserve) 200g" — un seul
        # mot par "ligne" ici pour simplifier, mais avec les 3 grandes
        # coupures caractéristiques de ce motif (nom1, qté1, nom2, qté2).
        data_two_per_line = {
            "width": 1400,
            "blocks": [{"paragraphs": [{"lines": [
                {"words": [
                    {"text": "Persil", "bbox": {"x0": 105, "x1": 166}},
                    {"text": "1/2", "bbox": {"x0": 556, "x1": 584}},
                    {"text": "bouquet", "bbox": {"x0": 592, "x1": 676}},
                    {"text": "Pois", "bbox": {"x0": 730, "x1": 777}},
                    {"text": "chiches", "bbox": {"x0": 785, "x1": 871}},
                    {"text": "200g", "bbox": {"x0": 1244, "x1": 1300}},
                ]},
            ]}]}],
        }
        two_per_line_result = page.evaluate(
            "(data) => reconstructTableRowsFromBlocks(data)", data_two_per_line
        )
        expected_two = "Persil | 1/2 bouquet\nPois chiches | 200g"
        ok = two_per_line_result == expected_two
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {two_per_line_result!r}")
        if not ok:
            all_ok = False
        print()

        print("=== Démarrage après un sélecteur de portions, en-tête ignoré ===\n")
        table_text_with_header = (
            "Plat complet | badge\n"
            "20 min | préparation\n"
            "(- 4 personnes | (+)\n"
            "Persil | 1/2 bouquet\n"
            "Quinoa | 100g"
        )
        header_result = page.evaluate(
            "(t) => parseTableRowsIngredients(t).map(i => i.name)", table_text_with_header
        )
        ok = header_result == ["Persil", "Quinoa"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {header_result}")
        if not ok:
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
