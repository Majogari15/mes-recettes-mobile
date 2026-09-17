#!/usr/bin/env python3
"""Test permanent : comportement en cas de coupure réseau EN COURS
d'utilisation (pas seulement le mode hors-ligne "propre" du service
worker déjà testé par ailleurs) — voir TESTS_NON_REGRESSION.md point 90
(audit étendu, manque "réseau/interruption" par rapport à une checklist
QA générique).

Simule une vraie coupure (page.context.set_offline) pendant un import de
recette par lien, ce qui fait échouer instantanément les 5 services
essayés en cascade (Worker Cloudflare, Jina AI Reader, 3 proxys CORS —
voir fetchRecipeFromUrl dans app.js) au lieu d'attendre leurs délais
d'expiration (15-30s chacun). Vérifie que l'utilisateur voit un message
d'échec clair en un temps raisonnable, sans page bloquée ni erreur JS
non gérée, et qu'il peut continuer à utiliser l'application ensuite.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_network_interruption.py

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

    def check(label, ok, detail=""):
        nonlocal all_ok
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")
        page.evaluate("() => { state.screen = 'importUrl'; render(); }")
        page.wait_for_timeout(200)

        print("=== Import par lien alors que le réseau vient de couper ===\n")
        page.context.set_offline(True)

        page.fill("#import-url-input", "exemple-de-recette.test/plat")
        page.click("#import-url-input + div + button, .screen button.btn-primary")

        try:
            page.wait_for_function(
                """
                () => {
                    const holder = document.querySelector('.screen div[style*="margin-top:16px"]');
                    return holder && holder.textContent.trim().length > 0 && !holder.textContent.includes('...');
                }
                """,
                timeout=12000,
            )
            timely = True
        except Exception:
            timely = False
        check("Un message (succès ou échec) s'affiche en moins de 12s, sans rester bloqué sur \"en cours\"", timely)

        error_text = page.evaluate(
            """
            () => {
                const holder = document.querySelector('.screen div[style*="margin-top:16px"]');
                return holder ? holder.textContent.trim() : '';
            }
            """
        )
        check(
            "Le message affiché n'est pas vide et ne contient pas de trace technique brute (ex. TypeError)",
            bool(error_text) and "TypeError" not in error_text and "undefined" not in error_text,
            error_text,
        )

        # Le réseau revient : l'application doit rester utilisable normalement,
        # pas coincée dans un état d'erreur permanent.
        page.context.set_offline(False)
        page.evaluate("() => { state.screen = 'home'; render(); }")
        page.wait_for_timeout(200)
        home_ok = page.evaluate("() => document.querySelector('.bottom-nav') !== null")
        check("L'application reste utilisable (retour à l'accueil) après le retour du réseau", home_ok)

        check("Aucune erreur JS non gérée pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
