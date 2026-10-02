"""
Import de recette par photo : une photo classée automatiquement
"Ingrédients" mais dont l'extraction finale ne garde aucun ingrédient
n'est plus étiquetée "Ingrédients" (isEmptyIngredientsDetection dans
app.js, appliquée par processPhotoIntoEntry). Voir
TESTS_NON_REGRESSION.md, entrée 136.

Vérifie, sur le vrai pipeline texte (parseOcrRecipeText ->
detectPhotoSection -> deriveSectionDataForPhoto) :
1. Les cas qui produisent réellement ce décalage (fragments trop courts,
   quantités sans nom) sont bien repérés.
2. Une vraie liste garde son étiquette.
3. Une liste vide qui a quand même donné le nombre de personnes garde
   son étiquette (le nombre de personnes ne doit pas être perdu).
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

CASES = [
    # (description, texte OCR, étiquette "Ingrédients" retirée ?)
    ("fragments trop courts", "Ingrédients\nab\ncd\nef\ngh", True),
    ("quantités sans nom", "Ingrédients\n2 g\n3 cl\n1 kg", True),
    ("vraie liste", "Ingrédients\n200 g de farine\n3 oeufs\n50 cl de lait\n1 pincée de sel", False),
    ("liste vide mais personnes trouvées", "Ingrédients pour 4 personnes\nab\ncd\nef", False),
]


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        for label, text, expected in CASES:
            r = page.evaluate(
                """(t) => {
                    const parsed = parseOcrRecipeText(t);
                    const detected = detectPhotoSection(parsed, t);
                    const data = deriveSectionDataForPhoto(t, detected || 'other', t, null, null, null);
                    return { detected, count: data.ingredients.length, persons: data.persons, dropped: isEmptyIngredientsDetection(detected, data) };
                }""",
                text,
            )
            # Les cas "retirée" doivent d'abord être détectés "ingredients"
            # par le classement automatique, sinon le test ne prouve rien.
            ok = r["dropped"] == expected and r["detected"] == "ingredients"
            print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label} — {r}")
            all_ok = all_ok and ok
        if errors:
            print("❌ ÉCHEC  erreurs JS :", "; ".join(errors))
            all_ok = False
        browser.close()
    httpd.shutdown()
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
