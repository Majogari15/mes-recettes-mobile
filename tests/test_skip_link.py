"""
Vérifie l'ajout du lien d'évitement ("skip link"), demandé explicitement
par l'utilisateur suite à un audit externe (priorité basse mais retenue,
voir TESTS_NON_REGRESSION.md point 120). Absent auparavant — confirmé
par recherche directe dans index.html/app.js/styles.css avant toute
implémentation.

Le lien est le premier élément focalisable de la page, invisible tant
qu'il n'a pas le focus clavier, et saute vers le contenu de l'écran
actuel (<main id="main-content">, recréé à chaque render() mais avec
un id stable). Il vit HORS de #app (jamais effacé par
`app.innerHTML = ""`), donc sa traduction est synchronisée séparément
depuis i18n.js (chargement initial + setLang()), comme document.title
et document.documentElement.lang le sont déjà pour la même raison.
"""
import http.server
import json
import socket
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_local_server(port):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=PROJECT_ROOT, **k)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


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
        page.wait_for_timeout(600)
        page.evaluate("() => setLang('fr')")

        def check(label, condition, detail):
            nonlocal all_ok
            mark = "✅ OK " if condition else "❌ ECHEC"
            print(f"{mark} {label} — {detail}")
            if not condition:
                all_ok = False

        print("=== 1. Présent, avant #app dans le DOM, invisible par défaut ===")
        r1 = page.evaluate(
            """
            () => {
                const link = document.getElementById('skip-link');
                const appDiv = document.getElementById('app');
                const style = link ? getComputedStyle(link) : null;
                return {
                    present: !!link,
                    href: link ? link.getAttribute('href') : null,
                    text: link ? link.textContent : null,
                    beforeApp: link && appDiv ? (link.compareDocumentPosition(appDiv) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0 : false,
                    topOffscreen: style ? style.top : null,
                };
            }
            """
        )
        check(
            "lien présent, pointe vers #main-content, avant #app, hors écran",
            r1["present"] and r1["href"] == "#main-content" and r1["beforeApp"]
            and r1["text"] == "Aller au contenu principal" and r1["topOffscreen"] == "-60px",
            json.dumps(r1, ensure_ascii=False),
        )

        print("\n=== 2. Devient visible au premier Tab (focus clavier) ===")
        page.keyboard.press("Tab")
        page.wait_for_timeout(250)
        r2 = page.evaluate(
            """
            () => {
                const active = document.activeElement;
                const isSkipLink = active && active.id === 'skip-link';
                const style = isSkipLink ? getComputedStyle(active) : null;
                return { isSkipLink, top: style ? style.top : null };
            }
            """
        )
        check("premier élément focalisable, devient visible", r2["isSkipLink"] and r2["top"] == "8px", json.dumps(r2))

        print("\n=== 3. Activation (Entrée) déplace le focus vers le contenu principal ===")
        page.keyboard.press("Enter")
        page.wait_for_timeout(150)
        r3 = page.evaluate("() => document.activeElement ? document.activeElement.id : null")
        check("focus déplacé sur #main-content", r3 == "main-content", str(r3))

        print("\n=== 4. #main-content présent et stable sur tous les écrans ===")
        r4 = page.evaluate(
            """
            () => {
                const results = [];
                for (const screen of ['home', 'shopping', 'pantry', 'recipes']) {
                    state.screen = screen;
                    render();
                    const main = document.getElementById('main-content');
                    results.push({ screen, present: !!main, tag: main ? main.tagName : null, tabIndex: main ? main.tabIndex : null });
                }
                return results;
            }
            """
        )
        check(
            "présent avec le bon tag/tabindex sur tous les écrans testés",
            all(r["present"] and r["tag"] == "MAIN" and r["tabIndex"] == -1 for r in r4),
            json.dumps(r4),
        )

        print("\n=== 5. Le lien lui-même survit aux changements d'écran (hors de #app) ===")
        r5 = page.evaluate("() => !!document.getElementById('skip-link')")
        check("toujours présent après plusieurs render()", r5 is True, str(r5))

        print("\n=== 6. Texte traduit selon la langue choisie ===")
        r6 = page.evaluate(
            """
            () => {
                setLang('en');
                const textEn = document.getElementById('skip-link').textContent;
                setLang('es');
                const textEs = document.getElementById('skip-link').textContent;
                setLang('de');
                const textDe = document.getElementById('skip-link').textContent;
                setLang('fr');
                const textFr = document.getElementById('skip-link').textContent;
                return { textEn, textEs, textDe, textFr };
            }
            """
        )
        check(
            "traduit dans les 4 langues",
            r6["textEn"] == "Skip to main content" and r6["textEs"] == "Ir al contenido principal"
            and r6["textDe"] == "Zum Hauptinhalt springen" and r6["textFr"] == "Aller au contenu principal",
            json.dumps(r6, ensure_ascii=False),
        )

        check("Aucune erreur JS pendant tout le parcours", not errors, str(errors))

        print("\n=== Résumé ===")
        print("TOUT CORRECT" if all_ok else "AU MOINS UN ECHEC")
        browser.close()
    httpd.shutdown()
    return all_ok


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
