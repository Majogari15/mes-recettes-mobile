"""
Vérifie la détection de la langue du téléphone/navigateur au tout premier
lancement (aucun choix encore enregistré), demandée explicitement par
l'utilisateur (voir TESTS_NON_REGRESSION.md point 122) :

1. Une langue du navigateur (`navigator.language`) parmi les 4 supportées
   (fr/en/es/de) doit être adoptée automatiquement dès le premier
   chargement.
2. Une langue du navigateur NON supportée (ex. italien) doit désormais
   retomber sur l'ANGLAIS par défaut — et non plus le français comme
   avant ce correctif.
3. Un choix de langue déjà enregistré (`localStorage.lang`, un lancement
   précédent ou un changement manuel) garde toujours la priorité sur la
   langue du navigateur, supportée ou non.

Chaque scénario utilise un contexte de navigateur Playwright dédié avec
son propre `locale`, pour que `navigator.language` reflète vraiment ce
que teste le scénario — jamais une simple simulation en JS après coup,
qui ne testerait pas le VRAI chemin de code (celui-ci s'exécute au tout
premier chargement de i18n.js, avant qu'aucun script de test ne puisse
intervenir).
"""
import http.server
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

    def check(label, condition, detail):
        nonlocal all_ok
        mark = "✅ OK " if condition else "❌ ECHEC"
        print(f"{mark} {label} — {detail}")
        if not condition:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()

        print("=== 1. Langue navigateur supportée (espagnol) adoptée au premier lancement ===")
        ctx1 = browser.new_context(viewport={"width": 390, "height": 900}, locale="es-ES")
        page1 = ctx1.new_page()
        errors1 = []
        page1.on("pageerror", lambda exc: errors1.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(600)
        r1 = page1.evaluate("() => ({ lang: CURRENT_LANG, navLang: navigator.language, htmlLang: document.documentElement.lang })")
        check(
            "espagnol (supporté) détecté et adopté",
            r1["lang"] == "es" and r1["htmlLang"] == "es",
            str(r1),
        )
        ctx1.close()

        print("\n=== 2. Langue navigateur NON supportée (italien) -> repli sur l'anglais (pas le français) ===")
        ctx2 = browser.new_context(viewport={"width": 390, "height": 900}, locale="it-IT")
        page2 = ctx2.new_page()
        errors2 = []
        page2.on("pageerror", lambda exc: errors2.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(600)
        r2 = page2.evaluate("() => ({ lang: CURRENT_LANG, navLang: navigator.language, htmlLang: document.documentElement.lang })")
        check(
            "italien (non supporté) retombe sur l'anglais",
            r2["lang"] == "en" and r2["htmlLang"] == "en",
            str(r2),
        )
        ctx2.close()

        print("\n=== 3. Un choix déjà enregistré garde la priorité sur le navigateur (même non supporté) ===")
        ctx3 = browser.new_context(viewport={"width": 390, "height": 900}, locale="it-IT")
        ctx3.add_init_script("localStorage.setItem('lang', 'de');")
        page3 = ctx3.new_page()
        errors3 = []
        page3.on("pageerror", lambda exc: errors3.append(str(exc)))
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(600)
        r3 = page3.evaluate("() => ({ lang: CURRENT_LANG, navLang: navigator.language })")
        check(
            "choix enregistré (allemand) prioritaire sur le navigateur non supporté (italien)",
            r3["lang"] == "de",
            str(r3),
        )
        ctx3.close()

        print("\n=== 4. Langue navigateur non affectée (français) toujours détectée correctement ===")
        ctx4 = browser.new_context(viewport={"width": 390, "height": 900}, locale="fr-FR")
        page4 = ctx4.new_page()
        errors4 = []
        page4.on("pageerror", lambda exc: errors4.append(str(exc)))
        page4.goto(base_url, timeout=8000)
        page4.wait_for_timeout(600)
        r4 = page4.evaluate("() => CURRENT_LANG")
        check("français (supporté) toujours détecté correctement", r4 == "fr", str(r4))
        ctx4.close()

        check(
            "Aucune erreur JS pendant tout le parcours (4 scénarios)",
            not (errors1 or errors2 or errors3 or errors4),
            str(errors1 + errors2 + errors3 + errors4),
        )

        print("\n=== TOUT VERIFIE ===" if all_ok else "\n=== AU MOINS UN ECHEC ===")
        browser.close()
    httpd.shutdown()
    return all_ok


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
