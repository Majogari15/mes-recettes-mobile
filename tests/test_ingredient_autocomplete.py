#!/usr/bin/env python3
"""Test permanent : le menu d'autocomplétion d'un champ ingrédient doit
s'afficher dès qu'on clique dans le champ, avec les premiers noms connus
(ordre alphabétique), pas seulement après avoir tapé la première lettre.
Demande explicite de l'utilisateur — voir TESTS_NON_REGRESSION.md.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_ingredient_autocomplete.py

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
        page.evaluate("async () => { await openRecipeForm(null); state.screen = 'form'; render(); }")
        page.wait_for_timeout(300)

        print("=== Un simple clic dans le champ vide affiche déjà des suggestions ===\n")
        page.locator(".ing-name").first.click()
        page.wait_for_timeout(200)
        on_click = page.evaluate(
            """
            () => {
                const d = document.querySelector('.autocomplete-dropdown');
                return d ? Array.from(d.querySelectorAll('.autocomplete-item')).map((i) => i.textContent) : null;
            }
            """
        )
        check(
            "le menu s'affiche dès le clic, sans avoir tapé quoi que ce soit",
            on_click is not None and len(on_click) > 0,
            str(on_click),
        )
        check(
            "les suggestions sont triées par ordre alphabétique (même ordre que partout ailleurs)",
            on_click == sorted(on_click) if on_click else False,
            str(on_click),
        )
        print()

        print("=== Taper une recherche filtre toujours correctement la liste ===\n")
        page.locator(".ing-name").first.type("tomate")
        page.wait_for_timeout(200)
        after_typing = page.evaluate(
            """
            () => {
                const d = document.querySelector('.autocomplete-dropdown');
                return d ? Array.from(d.querySelectorAll('.autocomplete-item')).map((i) => i.textContent) : null;
            }
            """
        )
        check(
            "la recherche par le texte tapé fonctionne toujours normalement",
            after_typing is not None and any("omate" in item for item in after_typing),
            str(after_typing),
        )
        print()

        print("=== Effacer le texte revient à la liste par défaut (pas de menu vide bloqué) ===\n")
        page.locator(".ing-name").first.fill("")
        page.wait_for_timeout(200)
        after_clearing = page.evaluate(
            """
            () => {
                const d = document.querySelector('.autocomplete-dropdown');
                return d ? Array.from(d.querySelectorAll('.autocomplete-item')).map((i) => i.textContent) : null;
            }
            """
        )
        check(
            "la liste par défaut revient après avoir effacé le texte tapé",
            after_clearing is not None and len(after_clearing) > 0,
            str(after_clearing),
        )
        print()

        print("Erreurs JS sur tout le parcours:", "AUCUNE" if not errors else "; ".join(errors))
        if errors:
            all_ok = False
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "DES ÉCHECS SUBSISTENT")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
