#!/usr/bin/env python3
"""
Tests permanents pour parseIngredientString — vérifie des comportements
précis qui ont déjà fait l'objet de corrections réelles (voir
TESTS_NON_REGRESSION.md, point 40), pour s'assurer qu'ils ne
régressent jamais silencieusement.

Contrairement au corpus OCR (tests/ocr-corpus/), qui vérifie le
pipeline complet à partir d'un vrai texte OCR, ce fichier teste
directement parseIngredientString sur des chaînes ciblées — plus
proche d'un test unitaire classique, adapté à des règles de format
précises (abréviations, symboles) plutôt qu'à un texte de photo
complet.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_ingredient_parsing.py

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


# Chaque cas : (texte en entrée, quantité attendue, unité attendue ou
# None pour ne pas vérifier l'unité, description courte du cas).

# Un nombre suivi directement de "%" n'est jamais une quantité
# d'ingrédient — descripteur de pourcentage (matière grasse, alcool...),
# pas un compte d'unités, même en tête de ligne. Voir
# TESTS_NON_REGRESSION.md point 40.
PERCENT_CASES = [
    ("20% MG crème fraîche", None, None, "pourcentage en tête de ligne"),
    ("Crème fraîche 20% MG", None, None, "pourcentage en fin de ligne"),
    ("200 g crème fraîche 20% MG", 200, "g", "vraie quantité présente par ailleurs"),
    ("1,5% Lait demi-écrémé", None, None, "pourcentage décimal avec virgule"),
]

# Les abréviations françaises courantes ("c." pour "cuillère") doivent
# être reconnues au même titre que la forme complète. Voir
# TESTS_NON_REGRESSION.md point 40.
SPOON_CASES = [
    ("2 c. à soupe de crème de noix de coco", 2, "c. à soupe", "abréviation avec point, soupe"),
    ("1 c à café de sel", 1, "c. à café", "abréviation sans point, café"),
    ("3 c. à café de sucre", 3, "c. à café", "abréviation avec point, café"),
    ("1 c à soupe d'huile", 1, "c. à soupe", "abréviation sans point, soupe"),
    ("2 cuillères à soupe de sucre", 2, "c. à soupe", "forme complète, pluriel"),
    ("1 cuillère à café de sel", 1, "c. à café", "forme complète, singulier"),
]

# Une fraction Unicode (½, ⅔...) mal reconnue par l'OCR comme "%" doit
# être signalée "à vérifier", jamais silencieusement ignorée ni
# inventée. Voir TESTS_NON_REGRESSION.md points 39 et 34 (système de
# score de confiance).
FRACTION_MISREAD_CASES = [
    ("Echalote % piece(s)", True, "cas réel du corpus salade grecque"),
    ("Origan séché % sachet", True, "cas réel du corpus salade grecque"),
    ("Filet de poulet et crème de coco", False, "vrai ingrédient, pas de faux positif"),
]

# La parenthèse fermante de "(s)" (marqueur de pluriel optionnel) est
# fréquemment omise par l'OCR — voir TESTS_NON_REGRESSION.md point 45 :
# sans cette tolérance, la quantité et l'unité disparaissaient
# complètement sur ces lignes, constaté sur une vraie photo réelle
# ("Persil plat et ciboulette* 1 sachet(s", sans le ")" final).
MISSING_CLOSING_PAREN_CASES = [
    ("Persil plat et ciboulette* 1 sachet(s", 1, "sachet", "cas réel, parenthèse manquante"),
    ("Tomates cerises 1 barquette(s", 1, "barquette", "même motif, autre unité"),
    ("Filet de barramundi 2 piece(s)", 2, "pièce", "avec la parenthèse présente, doit rester correct"),
    ("Persil* 1 sachet (", 1, "sachet", "variant encore plus incomplet, cas réel Carbonara — voir point 48"),
]


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

        print("=== Pourcentages non pris pour une quantité ===\n")
        for text, expected_qty, expected_unit, label in PERCENT_CASES:
            result = page.evaluate("(s) => parseIngredientString(s)", text)
            ok = result["quantity"] == expected_qty
            if expected_unit is not None:
                ok = ok and result["unit"] == expected_unit
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label} — {text!r}")
            print(f"        obtenu quantity={result['quantity']!r} unit={result['unit']!r}")
            if not ok:
                all_ok = False
            print()

        print("=== Abréviations de cuillères ===\n")
        for text, expected_qty, expected_unit, label in SPOON_CASES:
            result = page.evaluate("(s) => parseIngredientString(s)", text)
            ok = result["quantity"] == expected_qty and result["unit"] == expected_unit
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label} — {text!r}")
            print(f"        obtenu quantity={result['quantity']!r} unit={result['unit']!r}")
            if not ok:
                all_ok = False
            print()

        print("=== Fractions mal reconnues par l'OCR ===\n")
        for text, expected_flag, label in FRACTION_MISREAD_CASES:
            result = page.evaluate("(s) => parseIngredientString(s)", text)
            got_flag = bool(result.get("likelyMisreadFraction"))
            ok = got_flag == expected_flag
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label} — {text!r}")
            print(f"        signal obtenu={got_flag} (attendu {expected_flag})")
            if not ok:
                all_ok = False
            print()

        print("=== Parenthèse fermante manquante ===\n")
        for text, expected_qty, expected_unit, label in MISSING_CLOSING_PAREN_CASES:
            result = page.evaluate("(s) => parseIngredientString(s)", text)
            ok = result["quantity"] == expected_qty and result["unit"] == expected_unit
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label} — {text!r}")
            print(f"        obtenu quantity={result['quantity']!r} unit={result['unit']!r}")
            if not ok:
                all_ok = False
            print()

        browser.close()

    httpd.shutdown()

    print("=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
