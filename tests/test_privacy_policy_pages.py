"""
Politique de confidentialité (TESTS_NON_REGRESSION.md, entrée 149).

Garde-fou : chaque service externe contacté par le code (adresse
https://… dans app.js) doit être cité dans la page française ET la page
anglaise ; une nouvelle connexion ajoutée sans mettre la politique à jour
fait échouer ce test. Vérifie aussi : les 9 langues de la reconnaissance de
texte citées, les deux pages liées entre elles avec la même date (et le
.md), les deux pages en cache hors ligne, et le lien de l'écran Sauvegarde
qui ouvre la page dans la langue de l'interface (français -> page
française, autres langues -> page anglaise).
"""
import http.server
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

# Hôte trouvé dans app.js -> mot qui doit figurer dans les deux pages.
EXPECTED_MENTIONS = {
    "workers.dev": ("Cloudflare", "Cloudflare"),
    "r.jina.ai": ("r.jina.ai", "r.jina.ai"),
    "allorigins.win": ("allorigins.win", "allorigins.win"),
    "codetabs.com": ("codetabs.com", "codetabs.com"),
    "cors.lol": ("cors.lol", "cors.lol"),
    "openfoodfacts.org": ("openfoodfacts.org", "openfoodfacts.org"),
    "buymeacoffee.com": ("buymeacoffee.com", "buymeacoffee.com"),
    "google.com": ("Google", "Google"),
}
# Adresses du code qui ne sont pas des connexions de l'application.
IGNORED_HOSTS = ("majogari15.github.io", "www.w3.org", "schema.org", "votre-pseudo", "exemple.com")
OCR_LANGS_FR = ["français", "anglais", "espagnol", "allemand", "indonésien", "portugais", "italien", "suédois", "norvégien"]
OCR_LANGS_EN = ["French", "English", "Spanish", "German", "Indonesian", "Portuguese", "Italian", "Swedish", "Norwegian"]


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
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    app = open(f"{PROJECT_ROOT}/app.js", encoding="utf-8").read()
    fr = open(f"{PROJECT_ROOT}/confidentialite.html", encoding="utf-8").read()
    en = open(f"{PROJECT_ROOT}/privacy.html", encoding="utf-8").read()
    md = open(f"{PROJECT_ROOT}/POLITIQUE_CONFIDENTIALITE.md", encoding="utf-8").read()
    sw = open(f"{PROJECT_ROOT}/sw.js", encoding="utf-8").read()

    hosts = sorted({h for h in re.findall(r"https?://([a-zA-Z0-9.-]+)", app) if h and not any(i in h for i in IGNORED_HOSTS)})
    unknown = [h for h in hosts if not any(h == k or h.endswith("." + k) or h.endswith(k) for k in EXPECTED_MENTIONS)]
    check("toute adresse externe du code est connue de ce test (sinon : mettre la politique à jour)", not unknown, unknown)
    for key, (word_fr, word_en) in EXPECTED_MENTIONS.items():
        used = any(h == key or h.endswith(key) for h in hosts)
        check(f"{key} : {'utilisé, ' if used else 'non utilisé, '}cité en français et en anglais", word_fr in fr and word_en in en and word_fr in md, key)

    check("reconnaissance de texte : 9 langues citées (fr, en, md)",
          all(l in fr for l in OCR_LANGS_FR) and all(l in en for l in OCR_LANGS_EN) and all(l in md for l in OCR_LANGS_FR))
    def plain(html):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html))
    check("fichiers de reconnaissance : venant du site de l'application (fr, en)",
          "depuis le site de l'application elle-même (aucun service tiers)" in plain(fr)
          and "from the application's own website (no third-party service)" in plain(en))

    date_fr = re.search(r"dernière mise à jour : ([^·<]+?)\s*·", fr)
    date_md = re.search(r"Dernière mise à jour : ([^—*]+?)\s*—", md)
    check("même date dans la page française et le .md", date_fr and date_md and date_fr.group(1) == date_md.group(1), (date_fr and date_fr.group(1), date_md and date_md.group(1)))
    check("pages liées entre elles", 'href="privacy.html"' in fr and 'href="confidentialite.html"' in en)
    check("page anglaise déclarée en anglais", '<html lang="en">' in en)
    check("les deux pages en cache hors ligne (sw.js)", '"./confidentialite.html"' in sw and '"./privacy.html"' in sw)

    # --- Lien de l'écran Sauvegarde selon la langue ---
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 800})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")

        def link_for(lang):
            return page.evaluate(
                """async (lang) => {
                    await ensureUiTranslationsLoaded(lang); setLang(lang);
                    state.screen = 'backup'; render();
                    const a = [...document.querySelectorAll('a')].find(x => /confidentialite|privacy/.test(x.href));
                    return a && a.href;
                }""",
                lang,
            )

        href = link_for("fr")
        check("interface en français -> confidentialite.html", href and href.endswith("/confidentialite.html"), href)
        href = link_for("de")
        check("interface en allemand -> privacy.html (anglais)", href and href.endswith("/privacy.html"), href)
        for path in ("confidentialite.html", "privacy.html"):
            resp = page.request.get(f"http://127.0.0.1:{port}/{path}")
            check(f"{path} servie", resp.status == 200, resp.status)
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()

    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
