#!/usr/bin/env python3
"""Test permanent : logique JS de l'invite d'installation PWA
(bandeau "Ajouter à l'écran d'accueil") — voir TESTS_NON_REGRESSION.md
point 92.

Le vrai événement natif `beforeinstallprompt` ne se déclenche jamais
dans un navigateur headless (il dépend d'heuristiques d'engagement du
navigateur, hors de notre contrôle) — ce test le SIMULE donc en le
dispatchant nous-mêmes sur `window`, exactement comme le ferait un
vrai navigateur, pour vérifier que le code de l'application (pas le
navigateur) réagit correctement : affichage du bandeau, mémorisation
du refus, appel de `prompt()` au clic sur "Installer".

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pwa_install_flow.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_local_server(port):
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
        *args, directory=PROJECT_ROOT, **kwargs
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def dispatch_fake_prompt(page):
    return page.evaluate(
        """
        () => {
            window.__promptCalled = false;
            window.__userChoiceAwaited = false;
            const evt = new Event('beforeinstallprompt', { cancelable: true });
            evt.prompt = () => { window.__promptCalled = true; };
            evt.userChoice = Promise.resolve({ outcome: 'dismissed' });
            window.dispatchEvent(evt);
            return true;
        }
        """
    )


def main():
    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"

    all_ok = True

    def check(label, ok, detail=""):
        nonlocal all_ok
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()

        print("=== Bandeau affiché au bon moment (événement natif reçu, jamais refusé avant) ===\n")
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")
        check("Pas de bandeau avant l'événement", not page.is_visible(".install-banner"))
        dispatch_fake_prompt(page)
        page.wait_for_timeout(200)
        check("Le bandeau apparaît après l'événement beforeinstallprompt", page.is_visible(".install-banner"))

        print("\n=== Clic \"Installer\" appelle bien prompt() sur l'événement différé ===\n")
        page.click(".install-banner .btn-install")
        page.wait_for_timeout(200)
        prompt_called = page.evaluate("() => window.__promptCalled")
        check("prompt() a été appelé sur l'événement différé", prompt_called)
        check("Le bandeau se referme après le clic", not page.is_visible(".install-banner"))
        page.close()

        print("\n=== Clic \"Non merci\" : mémorisé, bandeau ne revient plus ===\n")
        page2 = browser.new_page(viewport={"width": 390, "height": 844})
        page2.on("pageerror", lambda exc: errors.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(1000)
        page2.evaluate("() => setLang('fr')")
        dispatch_fake_prompt(page2)
        page2.wait_for_timeout(200)
        page2.click(".install-banner .btn-dismiss")
        page2.wait_for_timeout(200)
        check("Le bandeau se referme après \"Non merci\"", not page2.is_visible(".install-banner"))
        dismissed_flag = page2.evaluate("() => localStorage.getItem('install_dismissed')")
        check("Le refus est mémorisé dans localStorage", dismissed_flag == "1")

        # Rechargement de la page : même avec un nouvel événement
        # beforeinstallprompt, le bandeau ne doit plus s'afficher.
        page2.reload()
        page2.wait_for_timeout(1000)
        dispatch_fake_prompt(page2)
        page2.wait_for_timeout(200)
        check("Le bandeau ne réapparaît pas après un rechargement, même avec un nouvel événement", not page2.is_visible(".install-banner"))
        page2.close()

        print("\n=== triggerInstall() : détection \"déjà installée\" (mode standalone simulé) ===\n")
        page3 = browser.new_page(viewport={"width": 390, "height": 844})
        page3.on("pageerror", lambda exc: errors.append(str(exc)))
        page3.add_init_script(
            "window.matchMedia = ((orig) => (query) => query.includes('standalone') ? { matches: true } : orig(query))(window.matchMedia);"
        )
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(1000)
        page3.evaluate("() => setLang('fr')")
        is_standalone = page3.evaluate("() => isRunningStandalone()")
        check("isRunningStandalone() détecte bien le mode standalone simulé", is_standalone)
        page3.close()

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
