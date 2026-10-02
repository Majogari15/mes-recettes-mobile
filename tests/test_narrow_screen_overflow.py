"""
Aucun écran ne doit déborder horizontalement sur un téléphone étroit
(320 px de large), dans les langues aux libellés les plus longs. Voir
TESTS_NON_REGRESSION.md, entrée 137.

Débordements trouvés à l'audit v303 : boutons Modifier/Dupliquer/
Supprimer de la fiche recette (fr, de, no), champ d'adresse de l'import
par lien (toutes langues), noms longs de la gestion des ingrédients
(sv, de), bouton « Coller le texte » des courses (de).
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
LANGS = ["fr", "de", "sv", "no", "pt", "it"]
SCREENS = ["home", "recipes", "recipe", "form", "shopping", "pantry", "ingredients", "backup",
           "diagnostic", "compare", "menus", "menu", "planning", "planningHistory", "importUrl",
           "unitConverter", "trash", "savedShoppingLists", "whatCanICook", "cookbookExport",
           "manageSubstitutions", "statistics", "importPhoto"]


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
        page = browser.new_page(viewport={"width": 320, "height": 700})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc).split("\n")[0]))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate(
            """async () => {
                const now = new Date().toISOString();
                await storePut('recipes', { id: 'n1', name: 'Recette', category: 'Plat', defaultPersons: 4, ingredients: [{ name: 'Farine', quantity: 100, unit: 'g' }], cookLog: [], createdAt: now });
                await storePut('menus', { id: 'nm', name: 'Menu', items: [{ recipeId: 'n1', persons: 4 }] });
                await storePut('shopping', { id: 'ns', name: 'Tomate', quantity: 2, unit: 'pièce', checked: false });
                state.recipes = await storeAll('recipes'); state.menus = await storeAll('menus'); state.shopping = await storeAll('shopping');
            }"""
        )
        for lang in LANGS:
            page.evaluate("async (l) => { await ensureUiTranslationsLoaded(l); await ensureIngredientTranslationsLoaded(l); setLang(l); }", lang)
            bad = []
            for screen in SCREENS:
                page.evaluate(
                    "(sc) => { state.currentRecipeId = 'n1'; state.currentMenuId = sc === 'menu' ? 'nm' : null; if (sc === 'form') state.editingRecipeId = 'n1'; state.screen = sc; render(); window.scrollTo(0, 0); }",
                    screen,
                )
                over = page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
                if over > 0:
                    bad.append(f"{screen} (+{over}px)")
            ok = not bad
            print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {lang} — " + ("aucun débordement" if ok else "débordements : " + ", ".join(bad)))
            all_ok = all_ok and ok
        if errors:
            print("❌ ÉCHEC  erreurs JS :", "; ".join(errors[:3]))
            all_ok = False
        browser.close()
    httpd.shutdown()
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
