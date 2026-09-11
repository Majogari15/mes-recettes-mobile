#!/usr/bin/env python3
"""
Tests permanents pour la détection de section (detectPhotoSection) et
l'analyse du titre/durée (parseOcrRecipeText) — couvre plusieurs
corrections issues de vraies photos Marmiton (recette Cassoulet à
l'ancienne), voir TESTS_NON_REGRESSION.md point 46.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_section_detection.py

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


# Une couverture Marmiton affiche parfois déjà le tout début de la
# vraie liste d'ingrédients au bas du cadrage — ne doit jamais faire
# perdre le nom, la durée et la difficulté de la couverture. Voir
# TESTS_NON_REGRESSION.md point 46.
COVER_LEAK_CASES = [
    (
        "Cassoulet à l'ancienne 4.7/5 3 commentaires\n6h10 • Facile • Assez cher\nIngrédients\n8 personnes\nsel\npoivre\n1 oignon\n2 oignons",
        "general",
        "cas réel Marmiton Cassoulet, 4 ingrédients visibles en bas du cadrage",
    ),
    (
        "Barramundi en croûte persillée\nIngrédients pour 2 personnes\nGrenailles 500g\nHaricots verts 1 sachet\nCitron 1 pièce\nAneth 1 sachet",
        "ingredients",
        "vraie photo d'ingrédients (pas de prepTime), doit rester classée normalement",
    ),
]

# Durée isolée sans préfixe explicite (format Marmiton) — voir
# TESTS_NON_REGRESSION.md point 46.
ISOLATED_DURATION_CASES = [
    ("Cassoulet à l'ancienne\n6h10 • Facile • Assez cher", 370, "cas réel Marmiton"),
    ("Une phrase assez longue qui ne devrait pas déclencher ce motif hXX", None, "pas de faux positif sur du texte non lié"),
]

# Note et nombre de commentaires collés au titre par l'OCR — voir
# TESTS_NON_REGRESSION.md point 46.
TITLE_CLEANUP_CASES = [
    (
        "Cassoulet à l'ancienne 4.7/5 3 commentaires\n6h10 • Facile • Assez cher",
        "Cassoulet à l'ancienne",
        "cas réel Marmiton",
    ),
    (
        "Barramundi en croûte persillée & tomates rôties\navec une purée à la ciboulette\nÀ table dans : 35 - 45 Min",
        "Barramundi en croûte persillée & tomates rôties avec une purée à la ciboulette",
        "non-régression : fusion de sous-titre HelloFresh toujours correcte",
    ),
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

        print("=== Couverture ne devant pas être classée \"Ingrédients\" ===\n")
        for text, expected, label in COVER_LEAK_CASES:
            parsed = page.evaluate("(t) => parseOcrRecipeText(t)", text)
            detected = page.evaluate("(p) => detectPhotoSection(p)", parsed)
            ok = detected == expected
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label}")
            print(f"        section obtenue={detected!r} (attendu {expected!r})")
            if not ok:
                all_ok = False
            print()

        print("=== Durée isolée sans préfixe (format \"6h10\") ===\n")
        for text, expected, label in ISOLATED_DURATION_CASES:
            result = page.evaluate("(t) => parseOcrRecipeText(t).prepTime", text)
            ok = result == expected
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label}")
            print(f"        prepTime obtenu={result!r} (attendu {expected!r})")
            if not ok:
                all_ok = False
            print()

        print("=== Nettoyage du titre (note, commentaires) ===\n")
        for text, expected, label in TITLE_CLEANUP_CASES:
            result = page.evaluate("(t) => parseOcrRecipeText(t).name", text)
            ok = result == expected
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label}")
            print(f"        nom obtenu={result!r} (attendu {expected!r})")
            if not ok:
                all_ok = False
            print()

        print("=== Champ personnes : pas de valeur inventée en contexte d'import ===\n")
        # Voir TESTS_NON_REGRESSION.md point 48 : le formulaire retombait
        # silencieusement sur "4" par défaut quand aucune photo n'avait
        # détecté le nombre de personnes, masquant le fait que la vraie
        # valeur n'a pas pu être lue plutôt que d'alerter l'utilisateur.
        persons_cases = [
            (
                "import, personnes non détectées → champ vide",
                "async () => { state._importPrefill = { name: 'Test', ingredients: [], description: '', persons: null, prepTime: null, cookTime: null }; await openRecipeForm(null); return document.getElementById('f-persons').value; }",
                "",
            ),
            (
                "import, personnes détectées à 2 → conservées",
                "async () => { state._importPrefill = { name: 'Test', ingredients: [], description: '', persons: 2, prepTime: null, cookTime: null }; await openRecipeForm(null); return document.getElementById('f-persons').value; }",
                "2",
            ),
            (
                "nouvelle recette vierge (pas d'import) → 4 par défaut, comportement inchangé",
                "async () => { state._importPrefill = null; await openRecipeForm(null); return document.getElementById('f-persons').value; }",
                "4",
            ),
        ]
        for label, script, expected in persons_cases:
            result = page.evaluate(script)
            ok = result == expected
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {label}")
            print(f"        valeur obtenue={result!r} (attendu {expected!r})")
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
