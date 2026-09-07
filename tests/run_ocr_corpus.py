#!/usr/bin/env python3
"""
Exécute tout le corpus OCR permanent (tests/ocr-corpus/*.json) contre le
code réel de app.js, et rapporte un résumé pass/fail pour chaque cas.

Objectif : mesurer objectivement si un changement à l'analyseur OCR
améliore ou dégrade la situation globale, plutôt que de corriger un
exemple au risque d'en casser un autre — exactement le problème vécu à
plusieurs reprises lors du développement de l'analyseur (v168 à v179).

Chaque fichier du corpus contient :
- rawText / layoutText : texte OCR réel, sauvegardé lors d'une vraie
  exécution de Tesseract.js sur une vraie photo (pas un texte inventé),
  ou une version synthétique équivalente si l'original contenait des
  informations personnelles (voir tests/private-ocr-corpus/README.md) ;
- expected : les résultats attendus actuels — pas nécessairement
  "parfaits", mais l'état correct et connu tel qu'accepté après
  vérification (voir le champ "notes" de chaque fichier pour le
  contexte et les limites connues). Peut inclure :
    - detectedSection, persons, prepTime, nameContains : vérifications
      simples (égalité ou sous-chaîne) ;
    - ingredientCount / ingredientCountMax : nombre de lignes ;
    - keyIngredients : liste d'ingrédients dont la présence (nom
      contenant une sous-chaîne donnée, avec quantité et unité exactes)
      est vérifiée n'importe où dans la liste, indépendamment de
      l'ordre — plus robuste qu'une égalité stricte de toute la liste,
      qui s'est révélée fragile même sur des données figées (l'ordre
      interne des mots d'un nom peut varier selon des détails de
      reconstruction sans que ce soit une vraie régression) ;
    - descriptionMinLength / descriptionContainsAll : vérifications sur
      le texte de préparation.

Utilisation (installe Playwright au préalable, démarre et arrête
lui-même un serveur local temporaire — une seule commande) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/run_ocr_corpus.py

Code de sortie : 0 si tous les cas passent, 1 sinon (utilisable dans un
script ou une vérification automatisée).
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
    """Démarre un serveur HTTP local servant le dossier du projet, dans
    un thread démon (s'arrête automatiquement à la fin du script) —
    rend le test exécutable en une seule commande, sans étape manuelle
    préalable."""
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
        *args, directory=PROJECT_ROOT, **kwargs
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def run_case(page, entry):
    """Exécute un cas du corpus contre le code réel de l'application, et
    compare aux attentes. Retourne (ok: bool, details: list[str])."""
    exp = entry.get("expected", {})
    details = []
    ok = True

    result = page.evaluate(
        """
        ([rawText, layoutText, gridText]) => {
            const parsed = parseOcrRecipeText(rawText);
            const detected = detectPhotoSection(parsed);
            const sectionData = deriveSectionDataForPhoto(rawText, detected || 'other', layoutText, gridText);
            return {
                detected,
                persons: sectionData.persons,
                ingredients: sectionData.ingredients || [],
                description: sectionData.description || '',
                name: sectionData.name || parsed.name,
                prepTime: sectionData.prepTime,
            };
        }
        """,
        [entry["rawText"], entry["layoutText"], entry.get("gridText")],
    )
    ingredient_count = len(result["ingredients"])
    description_length = len(result["description"])

    if "detectedSection" in exp and result["detected"] != exp["detectedSection"]:
        ok = False
        details.append(f"section attendue {exp['detectedSection']!r}, obtenue {result['detected']!r}")

    if "persons" in exp and result["persons"] != exp["persons"]:
        ok = False
        details.append(f"personnes attendues {exp['persons']!r}, obtenues {result['persons']!r}")

    if "ingredientCount" in exp and ingredient_count != exp["ingredientCount"]:
        ok = False
        details.append(f"nombre d'ingrédients attendu {exp['ingredientCount']}, obtenu {ingredient_count}")

    if "ingredientCountMax" in exp and ingredient_count > exp["ingredientCountMax"]:
        ok = False
        details.append(f"nombre d'ingrédients {ingredient_count} dépasse le maximum accepté {exp['ingredientCountMax']}")

    if "keyIngredients" in exp:
        for key_ing in exp["keyIngredients"]:
            needle = key_ing["nameContains"].lower()
            match = next(
                (
                    i for i in result["ingredients"]
                    if needle in (i.get("name") or "").lower()
                    and i.get("quantity") == key_ing.get("quantity")
                    and i.get("unit") == key_ing.get("unit")
                ),
                None,
            )
            if match is not None and "confidence" in key_ing and match.get("confidence") != key_ing["confidence"]:
                ok = False
                details.append(
                    f"ingrédient-clé {key_ing['nameContains']!r} : confiance attendue "
                    f"{key_ing['confidence']!r}, obtenue {match.get('confidence')!r}"
                )
            if match is None:
                ok = False
                details.append(
                    f"ingrédient-clé introuvable : nom contenant {key_ing['nameContains']!r} "
                    f"avec quantité {key_ing.get('quantity')!r} et unité {key_ing.get('unit')!r}"
                )

    if "descriptionMinLength" in exp and description_length < exp["descriptionMinLength"]:
        ok = False
        details.append(f"description trop courte ({description_length} car., minimum {exp['descriptionMinLength']})")

    if "descriptionContainsAll" in exp:
        desc_lower = result["description"].lower()
        for keyword in exp["descriptionContainsAll"]:
            if keyword.lower() not in desc_lower:
                ok = False
                details.append(f"description ne contient pas le mot-clé attendu {keyword!r}")

    if "nameContains" in exp and exp["nameContains"].lower() not in (result["name"] or "").lower():
        ok = False
        details.append(f"nom attendu contenant {exp['nameContains']!r}, obtenu {result['name']!r}")

    if "prepTime" in exp and result["prepTime"] != exp["prepTime"]:
        ok = False
        details.append(f"durée attendue {exp['prepTime']!r}, obtenue {result['prepTime']!r}")

    return ok, details


def main():
    paths = sorted(glob.glob(os.path.join(CORPUS_DIR, "*.json")))
    if not paths:
        print(f"Aucun fichier corpus trouvé dans {CORPUS_DIR}")
        sys.exit(1)

    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"

    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(500)

        print(f"=== Corpus OCR — {len(paths)} cas ===\n")
        for path in paths:
            with open(path, encoding="utf-8") as f:
                entry = json.load(f)
            ok, details = run_case(page, entry)
            status = "✅ OK" if ok else "❌ ÉCHEC"
            print(f"{status}  {entry['id']}")
            if entry.get("expected", {}).get("notes"):
                print(f"        note : {entry['expected']['notes']}")
            for d in details:
                print(f"        - {d}")
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
