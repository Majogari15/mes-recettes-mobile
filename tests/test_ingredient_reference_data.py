#!/usr/bin/env python3
"""
Test permanent protégeant la mise à jour des données de référence
ingrédients (allergènes, valeurs nutritionnelles, traductions),
importées depuis l'application Windows v56 — voir
TESTS_NON_REGRESSION.md, point 53. Source des données : ANSES Table
Ciqual 2025 (allergènes eux-mêmes : catégories Food Standards Agency),
390 corrections vérifiées manuellement côté application Windows avant
cet import (60 allergènes, 290 valeurs nutritionnelles, 26 traductions).

Ce test ne revérifie pas l'exactitude scientifique des valeurs
(hors de portée d'un test automatisé) — il protège contre une
régression accidentelle qui effacerait ou corromprait ces
corrections déjà faites (ex. un futur remplacement malencontreux des
fichiers de données par d'anciennes versions).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_ingredient_reference_data.py

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


# Quelques corrections réelles de l'audit v56 (voir
# AUDIT_INGREDIENTS_v56.md côté application Windows), choisies comme
# échantillon représentatif plutôt qu'une vérification exhaustive des
# 390 corrections.
ALLERGEN_CASES = [
    ("Beurre", "Lactose", True, "corrigé : allergène manquant"),
    ("Courge spaghetti", "Gluten", False, "corrigé : faux positif retiré"),
    ("Crème anglaise", "Œufs", True, "corrigé : allergène manquant ajouté"),
]

# (nom, doit avoir une provenance Ciqual, kcal minimum attendu — juste
# pour confirmer qu'une vraie valeur est chargée, pas une vérification
# nutritionnelle précise)
NUTRITION_CASES = [
    ("Ail en poudre", True, 300),  # corrigé : partageait le profil de l'ail frais
    ("Abricot", True, 30),
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
        page.wait_for_timeout(1500)  # laisse le temps à loadReferenceData

        print("=== Nombre total d'ingrédients de référence ===\n")
        count = page.evaluate("() => Object.keys(NUTRITION_DB).length")
        ok = count == 1030
        status = "✅ OK" if ok else "❌ ÉCHEC"
        print(f"{status}  {count} ingrédients (attendu 1030)")
        if not ok:
            all_ok = False
        print()

        print("=== Corrections d'allergènes (échantillon) ===\n")
        for name, allergen, should_have, label in ALLERGEN_CASES:
            allergens = page.evaluate("(n) => getIngredientAllergens(n)", name)
            has_it = allergen in allergens
            ok = has_it == should_have
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {name} — {label}")
            print(f"        allergènes obtenus={allergens}")
            if not ok:
                all_ok = False
            print()

        print("=== Valeurs nutritionnelles (échantillon) ===\n")
        for name, should_have_ciqual, min_kcal in NUTRITION_CASES:
            info = page.evaluate("(n) => getIngredientNutrition(n)", name)
            has_ciqual = bool(info and info.get("_ciqual"))
            kcal_ok = bool(info and info.get("kcal", 0) >= min_kcal)
            ok = has_ciqual == should_have_ciqual and kcal_ok
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {name}")
            print(f"        kcal={info.get('kcal') if info else None} (≥{min_kcal} attendu), provenance Ciqual={has_ciqual}")
            if not ok:
                all_ok = False
            print()

        print("=== Calcul d'allergènes/nutrition au niveau recette (intégration) ===\n")
        result = page.evaluate(
            """
            () => ({
                allergens: computeRecipeAllergens([{name: 'Beurre', quantity: 50, unit: 'g'}]),
                nutrition: computeRecipeNutrition([{name: 'Abricot', quantity: 100, unit: 'g'}]),
            })
            """
        )
        ok = "Lactose" in result["allergens"] and result["nutrition"] is not None
        status = "✅ OK" if ok else "❌ ÉCHEC"
        print(f"{status}  intégration recette")
        print(f"        {result}")
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
