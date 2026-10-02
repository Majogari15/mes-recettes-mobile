"""
Écrans « Gérer les ingrédients » et « Gérer les substituts » : la phrase
« N ingrédients affichés sur M — tapez ci-dessus pour rechercher… »
s'affiche AU-DESSUS de la liste (elle était tout en bas, après 200
lignes). Voir TESTS_NON_REGRESSION.md, entrée 138.
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
    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        for screen, holder in (("ingredients", "#ingredient-list-holder"), ("manageSubstitutions", "#subs-list-holder")):
            r = page.evaluate(
                """([sc, holder]) => {
                    state.screen = sc; render();
                    const h = document.querySelector(holder);
                    const hint = h.querySelector('.list-truncated-hint');
                    const card = h.querySelector('.card');
                    return {
                        hint: !!hint,
                        before: !!(hint && card && (hint.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING)),
                        text: hint ? hint.textContent : null,
                    };
                }""",
                [screen, holder],
            )
            ok = r["hint"] and r["before"]
            print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {screen} — phrase {'au-dessus' if r['before'] else 'PAS au-dessus'} de la liste ({r['text']})")
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
