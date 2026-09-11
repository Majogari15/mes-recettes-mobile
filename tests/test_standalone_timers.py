#!/usr/bin/env python3
"""
Test permanent pour la fenêtre de minuteurs autonome (accessible depuis
Accueil → Outils → Minuteur), voir TESTS_NON_REGRESSION.md.

Couvre le point technique le plus important : un minuteur démarré,
fenêtre fermée puis rouverte, doit continuer de tourner en arrière-plan
ET se réafficher avec le bon temps restant à la réouverture — pas figé
sur l'ancienne valeur ni remis à zéro.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_standalone_timers.py

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


def main():
    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"

    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => { setLang('fr'); }")

        print("=== Ouverture depuis le bouton de l'accueil ===\n")
        result = page.evaluate(
            """
            () => {
                state.screen = 'home';
                render();
                const buttons = Array.from(document.querySelectorAll('button'));
                const timerBtn = buttons.find(b => b.textContent.includes('Minuteur'));
                if (timerBtn) timerBtn.click();
                return {
                    buttonFound: !!timerBtn,
                    overlayOpen: !!document.querySelector('.cooking-overlay'),
                    timerRowCount: document.querySelectorAll('.timer-row').length,
                };
            }
            """
        )
        ok = result["buttonFound"] and result["overlayOpen"] and result["timerRowCount"] == 1
        status = "✅ OK" if ok else "❌ ÉCHEC"
        print(f"{status}  bouton présent, fenêtre ouverte avec 1 minuteur par défaut")
        print(f"        {result}")
        if not ok:
            all_ok = False
        print()

        print("=== Ajout d'un second minuteur ===\n")
        result2 = page.evaluate(
            """
            () => {
                document.querySelector('.btn-secondary.btn-sm').click();
                return { timerRowCount: document.querySelectorAll('.timer-row').length, stateCount: state.cookingTimers.length };
            }
            """
        )
        ok2 = result2["timerRowCount"] == 2 and result2["stateCount"] == 2
        status2 = "✅ OK" if ok2 else "❌ ÉCHEC"
        print(f"{status2}  {result2}")
        if not ok2:
            all_ok = False
        print()

        print("=== En-tête \"Fermer\" correctement dimensionné (pas de débordement) ===\n")
        result3 = page.evaluate(
            """
            () => {
                const btn = document.querySelector('.cooking-header button');
                const rect = btn.getBoundingClientRect();
                return { width: rect.width, height: rect.height, text: btn.textContent.trim() };
            }
            """
        )
        # Largeur auto attendue nettement supérieure aux 40px du cercle
        # d'origine (bug corrigé — voir TESTS_NON_REGRESSION.md).
        ok3 = result3["width"] > 60 and "Fermer" in result3["text"]
        status3 = "✅ OK" if ok3 else "❌ ÉCHEC"
        print(f"{status3}  {result3}")
        if not ok3:
            all_ok = False
        print()

        print("=== Démarrage, fermeture, persistance en arrière-plan, réouverture ===\n")
        result4 = page.evaluate(
            """
            () => {
                document.querySelector('.timer-row .start-btn').click();
                const runningBeforeClose = state.cookingTimers[0].running;
                document.querySelector('.cooking-header button').click();
                return {
                    runningBeforeClose,
                    overlayClosedButStatePersists: !document.querySelector('.cooking-overlay') && state.cookingTimers.length === 2,
                };
            }
            """
        )
        ok4 = result4["runningBeforeClose"] and result4["overlayClosedButStatePersists"]
        status4 = "✅ OK" if ok4 else "❌ ÉCHEC"
        print(f"{status4}  fermeture ne stoppe pas les minuteurs")
        print(f"        {result4}")
        if not ok4:
            all_ok = False
        print()

        page.wait_for_timeout(1500)

        print("=== Réouverture : réaffichage correct, décompte poursuivi ===\n")
        result5 = page.evaluate(
            """
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const timerBtn = buttons.find(b => b.textContent.includes('Minuteur'));
                timerBtn.click();
                const rows = document.querySelectorAll('.timer-row');
                return {
                    timerRowCount: rows.length,
                    firstCountdown: rows[0].querySelector('.timer-countdown').textContent,
                    firstStillRunning: state.cookingTimers[0].running,
                };
            }
            """
        )
        # Parti de 05:00, au moins 1 seconde doit s'être écoulée pendant
        # la fermeture (1,5s d'attente ci-dessus) — ne doit donc plus
        # afficher exactement "05:00".
        ok5 = (
            result5["timerRowCount"] == 2
            and result5["firstCountdown"] != "05:00"
            and result5["firstStillRunning"]
        )
        status5 = "✅ OK" if ok5 else "❌ ÉCHEC"
        print(f"{status5}  décompte poursuivi pendant la fermeture, pas figé ni remis à zéro")
        print(f"        {result5}")
        if not ok5:
            all_ok = False
        print()

        print("Erreurs JS sur tout le parcours:", errors if errors else "AUCUNE")
        if errors:
            all_ok = False

        browser.close()

    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
