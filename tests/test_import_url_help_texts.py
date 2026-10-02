"""
Écran « Importer depuis un lien » : nouvelle description (mode d'emploi
en 3 étapes, compatibilité, confidentialité), avertissement sur les
doublons en gris, et conseil en cas d'échec affiché SEULEMENT après un
vrai échec (il était en rouge en permanence). Voir
TESTS_NON_REGRESSION.md, entrée 139.
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
LANGS = ["fr", "en", "es", "de", "id", "pt", "it", "sv", "no"]


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

    def check(label, ok, detail=""):
        nonlocal all_ok
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}" + (f" — {detail}" if detail else ""))
        all_ok = all_ok and ok

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 360, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        for lang in LANGS:
            r = page.evaluate(
                """async (l) => {
                    await ensureUiTranslationsLoaded(l); setLang(l);
                    state.screen = 'importUrl'; render();
                    const intro = document.querySelector('.import-url-intro');
                    const text = document.getElementById('app').innerText;
                    return {
                        steps: intro ? intro.querySelectorAll('li').length : 0,
                        hasPrivacy: text.includes(t('import_url_privacy')),
                        hintBefore: !!document.querySelector('.import-url-failure-hint') || text.includes(t('import_url_failure_warning')),
                        overflow: document.documentElement.scrollWidth - window.innerWidth,
                    };
                }""",
                lang,
            )
            check(f"{lang} : 3 étapes, mention de confidentialité, pas de conseil d'échec avant d'essayer, pas de débordement",
                  r["steps"] == 3 and r["hasPrivacy"] and not r["hintBefore"] and r["overflow"] <= 0, str(r))

        # Échec simulé (sans réseau réel) : le conseil apparaît.
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); setLang('fr'); state.screen = 'importUrl'; render(); window.fetchRecipeFromUrl = async () => { throw new Error('test'); }; }")
        page.fill("#import-url-input", "https://exemple.com/recette")
        page.click("button.btn-primary")
        page.wait_for_selector(".import-url-failure-hint", timeout=5000)
        r = page.evaluate("() => ({ hint: document.querySelector('.import-url-failure-hint').textContent, error: document.getElementById('app').innerText.includes(t('import_url_error')) })")
        check("après un échec : message d'erreur + conseil affichés", r["error"] and "capture" in r["hint"], str(r))
        if errors:
            check("aucune erreur JS", False, "; ".join(errors))
        browser.close()
    httpd.shutdown()
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
