"""
Recherche web d'une recette depuis l'écran « Importer depuis un lien »,
reprise de l'app Windows (TESTS_NON_REGRESSION.md, entrée 146).

Vérifie l'adresse construite (mot « recette » dans la langue de
l'interface, sites de recettes vérifiés par l'app Windows pour fr/en/es/
de, aucun filtre de site pour les autres langues, encodage des caractères
spéciaux, champ vide -> page d'accueil Google), puis le formulaire
(bouton et touche Entrée ouvrent un nouvel onglet, pas de débordement à
320 px).
"""
import http.server
import socket
import sys
import threading
import urllib.parse

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


def query_of(url):
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("q", [""])[0]


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { await ensureUiTranslationsLoaded('fr'); setLang('fr'); }")

        urls = page.evaluate("""() => ({
            fr: buildRecipeSearchUrl('tarte aux poireaux', 'fr'),
            de: buildRecipeSearchUrl('Lauchkuchen', 'de'),
            it: buildRecipeSearchUrl('torta salata', 'it'),
            special: buildRecipeSearchUrl('  poulet & riz #1  ', 'fr'),
            empty: buildRecipeSearchUrl('   ', 'fr'),
        })""")
        q = query_of(urls["fr"])
        check("français : mot « recette » + sites vérifiés", q.startswith("tarte aux poireaux recette (site:marmiton.org OR ") and "site:papillesetpupilles.fr)" in q, q)
        check("adresse Google", urls["fr"].startswith("https://www.google.com/search?q="), urls["fr"][:40])
        q = query_of(urls["de"])
        check("allemand : « Rezept » + sites allemands", q.startswith("Lauchkuchen Rezept (site:chefkoch.de") , q)
        q = query_of(urls["it"])
        check("italien : « ricetta », sans filtre de site (comme Windows)", q == "torta salata ricetta", q)
        q = query_of(urls["special"])
        check("caractères spéciaux encodés, espaces superflus retirés", q.startswith("poulet & riz #1 recette (site:"), q)
        check("champ vide : page d'accueil Google", urls["empty"] == "https://www.google.com/", urls["empty"])

        # --- Écran ---
        page.evaluate("""() => {
            window.__opened = [];
            window.open = (url, target, features) => { window.__opened.push({ url, target, features }); return null; };
            state.screen = 'importUrl'; render();
        }""")
        check("carte de recherche affichée avant le champ du lien",
              page.evaluate("() => { const s = document.querySelector('.import-web-search'), u = document.querySelector('#import-url-input'); return !!s && !!u && !!(s.compareDocumentPosition(u) & Node.DOCUMENT_POSITION_FOLLOWING); }"))
        page.fill("#import-web-search-input", "gratin dauphinois")
        page.click(".import-web-search button[type=submit]")
        opened = page.evaluate("() => window.__opened")
        check("bouton : nouvel onglet sur la recherche", len(opened) == 1 and query_of(opened[0]["url"]).startswith("gratin dauphinois recette") and opened[0]["target"] == "_blank" and "noopener" in opened[0]["features"], opened)
        page.fill("#import-web-search-input", "crêpes")
        page.press("#import-web-search-input", "Enter")
        opened = page.evaluate("() => window.__opened")
        check("touche Entrée : même recherche, pas de rechargement", len(opened) == 2 and query_of(opened[1]["url"]).startswith("crêpes recette") and page.evaluate("() => state.screen") == "importUrl", opened[-1:])
        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        check("pas de débordement à 320 px", not overflow)

        page.evaluate("async () => { await ensureUiTranslationsLoaded('sv'); setLang('sv'); }")
        page.wait_for_function("() => document.querySelector('.import-web-search label') && document.querySelector('.import-web-search label').textContent.includes('recept')")
        page.fill("#import-web-search-input", "köttbullar")
        page.click(".import-web-search button[type=submit]")
        opened = page.evaluate("() => window.__opened")
        check("langue de l'interface suivie (suédois : « recept »)", query_of(opened[-1]["url"]) == "köttbullar recept", opened[-1])

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
