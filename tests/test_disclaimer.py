"""
Clause de responsabilité au premier lancement, reprise de l'app Windows
(TESTS_NON_REGRESSION.md, entrée 147).

La clause n'est pas imposée quand navigator.webdriver est vrai (tests
automatiques) ; ce test le force à false pour se comporter comme un vrai
téléphone. Vérifie : affichage bloquant, « Continuer » inactif tant que la
case n'est pas cochée, ni Échap ni un appui à côté ne la ferment,
changement de langue avant d'accepter (case conservée), acceptation
mémorisée après rechargement, relecture depuis l'écran Sauvegarde, bouton
« Continuer » visible sans faire défiler la page sur un petit écran.
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
AS_REAL_PHONE = "Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false, configurable: true });"


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
    url = f"http://127.0.0.1:{port}/index.html"
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors = []

        # --- Tests automatiques ordinaires : jamais affichée ---
        ctx0 = browser.new_context(viewport={"width": 320, "height": 640})
        page0 = ctx0.new_page()
        page0.on("pageerror", lambda exc: errors.append(str(exc)))
        page0.goto(url, timeout=15000)
        page0.evaluate("() => appReady")
        check("navigateur de test (webdriver) : clause non imposée", page0.locator(".disclaimer-overlay").count() == 0)
        ctx0.close()

        # --- Comme un vrai téléphone, petit écran ---
        ctx = browser.new_context(viewport={"width": 320, "height": 568}, locale="fr-FR")
        ctx.add_init_script(AS_REAL_PHONE)
        page = ctx.new_page()
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(url, timeout=15000)
        page.evaluate("() => appReady")
        page.evaluate("async () => { if (CURRENT_LANG !== 'fr') { await ensureUiTranslationsLoaded('fr'); setLang('fr'); render(); } }")
        page.wait_for_selector(".disclaimer-overlay")
        r = page.evaluate("""() => ({
            heading: document.querySelector('#disclaimer-heading').textContent,
            text: document.querySelector('.disclaimer-text').textContent,
            disabled: document.querySelector('#disclaimer-continue').disabled,
            hasQuit: !!document.querySelector('.disclaimer-sheet').textContent.includes('Quitter'),
        })""")
        check("premier lancement : clause affichée", "Clause de responsabilité" in r["heading"] and "Article 1 – Allergènes" in r["text"], r["heading"])
        check("texte v2 : éditeur et contact, articles 1 à 6, plus de « critères d'allergies »",
              "majogari81@gmail.com" in r["text"] and "Article 6 – Modifications et droit applicable" in r["text"]
              and "calculés automatiquement" in r["text"] and "critères d'allergies" not in r["text"] and "ARTICLE 1" not in r["text"], r["text"][:80])
        intro = page.evaluate("() => document.querySelector('.disclaimer-intro').textContent")
        check("premier lancement : introduction normale", "Merci de lire" in intro, intro)
        check("« Continuer » inactif tant que la case n'est pas cochée", r["disabled"])
        check("pas de bouton « Quitter » (impossible pour une appli web)", not r["hasQuit"])

        btn = page.evaluate("() => { const b = document.querySelector('#disclaimer-continue').getBoundingClientRect(); return { top: b.top, bottom: b.bottom, h: innerHeight, sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }; }")
        check("bouton « Continuer » visible sans défiler (320×568)", btn["bottom"] <= btn["h"] and btn["top"] >= 0, btn)
        check("pas de débordement horizontal", btn["sw"] <= btn["cw"], btn)

        page.keyboard.press("Escape")
        page.mouse.click(160, 5)
        page.wait_for_timeout(200)
        check("ni Échap ni un appui à côté ne la ferment", page.locator(".disclaimer-overlay").count() == 1)
        screen_before = page.evaluate("() => state.screen")
        page.mouse.click(160, 300)
        check("application masquée derrière (aucun appui ne passe)", page.evaluate("() => state.screen") == screen_before)

        page.check("#disclaimer-accept")
        check("case cochée -> « Continuer » actif", not page.evaluate("() => document.querySelector('#disclaimer-continue').disabled"))

        # Changement de langue avant d'accepter.
        page.select_option("#disclaimer-lang-select", "en")
        page.wait_for_function("() => document.querySelector('#disclaimer-heading').textContent.includes('Disclaimer')")
        r = page.evaluate("() => ({ lang: CURRENT_LANG, checked: document.querySelector('#disclaimer-accept').checked, enabled: !document.querySelector('#disclaimer-continue').disabled, label: document.querySelector('label[for=disclaimer-accept]').textContent })")
        check("langue changée (anglais), case et bouton conservés", r["lang"] == "en" and r["checked"] and r["enabled"] and "I have read" in r["label"], r)
        page.select_option("#disclaimer-lang-select", "fr")
        page.wait_for_function("() => document.querySelector('#disclaimer-heading').textContent.includes('Clause')")

        page.click("#disclaimer-continue")
        r = page.evaluate("() => ({ open: !!document.querySelector('.disclaimer-overlay'), saved: localStorage.getItem('disclaimerAcceptedAt'), version: localStorage.getItem('disclaimerAcceptedVersion') })")
        check("« Continuer » : clause fermée, acceptation et version enregistrées", not r["open"] and r["saved"] and r["version"] == "2", r)

        page.reload()
        page.evaluate("() => appReady")
        page.wait_for_timeout(300)
        check("après rechargement : plus redemandée", page.locator(".disclaimer-overlay").count() == 0)

        # Acceptation d'une ancienne version (v313 : date seule, sans
        # numéro) -> redemandée, avec une introduction qui dit pourquoi.
        page.evaluate("() => { localStorage.removeItem('disclaimerAcceptedVersion'); }")
        page.reload()
        page.evaluate("() => appReady")
        page.wait_for_selector(".disclaimer-overlay")
        intro = page.evaluate("() => document.querySelector('.disclaimer-intro').textContent")
        check("ancienne version acceptée : clause redemandée (texte mis à jour)", "mis à jour" in intro, intro)
        page.check("#disclaimer-accept")
        page.click("#disclaimer-continue")
        page.reload()
        page.evaluate("() => appReady")
        page.wait_for_timeout(300)
        check("nouvelle version acceptée : plus redemandée", page.locator(".disclaimer-overlay").count() == 0)

        # Relecture depuis l'écran Sauvegarde.
        page.evaluate("() => { state.screen = 'backup'; render(); }")
        page.click("#open-disclaimer")
        page.wait_for_selector(".disclaimer-overlay")
        r = page.evaluate("() => ({ checkbox: !!document.querySelector('#disclaimer-accept'), close: !!document.querySelector('#disclaimer-close'), text: document.querySelector('.disclaimer-text').textContent.includes('Article 6') })")
        check("relecture : texte complet, sans case à cocher", r == {"checkbox": False, "close": True, "text": True}, r)
        page.keyboard.press("Escape")
        check("relecture : Échap ferme", page.locator(".disclaimer-overlay").count() == 0)
        ctx.close()

        # Stockage local refusé : redemandée, sans planter.
        ctx3 = browser.new_context(viewport={"width": 390, "height": 800})
        ctx3.add_init_script(AS_REAL_PHONE)
        page3 = ctx3.new_page()
        page3.on("pageerror", lambda exc: errors.append(str(exc)))
        page3.goto(url, timeout=15000)
        page3.evaluate("() => appReady")
        page3.wait_for_selector(".disclaimer-overlay")
        page3.evaluate("() => { Storage.prototype.setItem = () => { throw new Error('quota'); }; }")
        page3.check("#disclaimer-accept")
        page3.click("#disclaimer-continue")
        check("stockage refusé : clause fermée quand même, sans erreur", page3.locator(".disclaimer-overlay").count() == 0)
        ctx3.close()

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
