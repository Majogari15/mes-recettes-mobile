"""
La recherche d'ingrédients (searchIngredientNames) et "vouliez-vous dire"
(findClosestIngredientMatch) gardent en mémoire les formes normalisées des
noms et des traductions (normalizeCached, normalizedTranslatedIngredientName
dans app.js) pour ne plus les recalculer à chaque frappe.

Vérifie qu'un cache rempli AVANT une modification de la liste ne renvoie
jamais de résultat périmé, hors français (où les traductions entrent en
jeu) : après renommage, suppression et ajout, la recherche reflète la liste
actuelle, y compris la recherche par nom traduit.
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"


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
    base_url = f"http://127.0.0.1:{port}/index.html"
    all_ok = True

    def check(label, ok, detail=""):
        nonlocal all_ok
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=15000)
        page.evaluate("() => appReady")

        r = page.evaluate(
            """async () => {
                await ensureUiTranslationsLoaded('en');
                await ensureIngredientTranslationsLoaded('en');
                setLang('en');
                const tomato = state.ingredientNames.find((n) => n === 'Tomate');
                const butter = state.ingredientNames.find((n) => n === 'Beurre');
                // Remplit le cache AVANT les modifications.
                const before = {
                    tomato: searchIngredientNames('Tomato', 50).includes(tomato),
                    butter: searchIngredientNames('Butter', 50).includes(butter),
                };
                await renameIngredientName(tomato, 'Tomate du jardin');
                await deleteIngredientName(butter);
                await addIngredientName('Zzyzx ajout test');
                return {
                    before,
                    // Renommé : garde son lien au catalogue, donc toujours trouvé par sa traduction, sous son nouveau nom.
                    renamedByTranslation: searchIngredientNames('Tomato', 50).includes('Tomate du jardin'),
                    oldNameGone: !searchIngredientNames('Tomato', 50).includes('Tomate'),
                    renamedByNewName: searchIngredientNames('Tomate du jardin', 8).includes('Tomate du jardin'),
                    deletedGone: !searchIngredientNames('Butter', 50).includes('Beurre'),
                    added: searchIngredientNames('Zzyzx', 8).includes('Zzyzx ajout test'),
                    closestAdded: (findClosestIngredientMatch('Zzyzx ajout tesst') || {}).name,
                };
            }"""
        )
        check("cache rempli avant modification (Tomate et Beurre trouvés par leur traduction)", r["before"]["tomato"] and r["before"]["butter"], str(r["before"]))
        check("renommé : trouvé par sa traduction sous son nouveau nom", r["renamedByTranslation"], str(r))
        check("renommé : l'ancien nom n'apparaît plus", r["oldNameGone"], str(r))
        check("renommé : trouvé par son nouveau nom", r["renamedByNewName"], str(r))
        check("supprimé : n'apparaît plus", r["deletedGone"], str(r))
        check("ajouté : trouvé par la recherche", r["added"], str(r))
        check("ajouté : proposé par 'vouliez-vous dire'", r["closestAdded"] == "Zzyzx ajout test", str(r["closestAdded"]))

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
