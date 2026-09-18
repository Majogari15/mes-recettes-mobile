#!/usr/bin/env python3
"""Test permanent : messages affichés après la recherche d'un produit
scanné, suite à deux bugs confirmés par un audit externe (autre IA) sur
un cas réel signalé par l'utilisateur — voir TESTS_NON_REGRESSION.md
point 105.

Cas réel qui a révélé le premier bug : une fiche Open Food Facts ne
comportait que le poids net (300 g), sans aucun nom de produit renseigné
— `openBarcodeResultModal()` affichait alors UNIQUEMENT le poids,
masquant silencieusement l'avertissement "nom non trouvé" à cause d'un
`if/else` qui traitait les deux indications comme mutuellement
exclusives alors qu'elles sont indépendantes. La personne se retrouvait
avec un champ nom vide sans aucune explication visible.

Second bug, dans la même fonction de recherche (`lookupProductByBarcode`) :
une vraie panne réseau (aucune réponse, délai dépassé, erreur HTTP) et
une fiche simplement absente de la base renvoyaient exactement le même
résultat interne (`{name: null}`), donc le même message générique
"produit non trouvé" — impossible de distinguer les deux cas. Un champ
`networkError` distinct permet maintenant d'afficher un message adapté
à la panne réseau plutôt que le message générique.

Réseau réel jamais utilisé ici : les requêtes vers Open Food Facts sont
interceptées (page.route) et remplacées par des réponses contrôlées.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_barcode_lookup_messages.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import json
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


def mock_off_route(route, product_response, status=200):
    route.fulfill(status=status, content_type="application/json", body=json.dumps(product_response))


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

        def scan(barcode):
            page.evaluate("() => { state.screen = 'pantry'; render(); }")
            page.wait_for_timeout(150)
            page.click("text=Scanner un code-barres")
            page.wait_for_timeout(150)
            page.click("text=Saisir le code-barres manuellement")
            page.wait_for_timeout(150)
            page.fill("#barcode-manual-input", barcode)
            page.click("#barcode-manual-submit")
            page.wait_for_timeout(400)

        def modal_texts():
            name = page.eval_on_selector("#modal-ing-name", "el => el.value")
            hint_p = page.query_selector("#modal-ing-name")
            hint_text = page.evaluate(
                "() => { const p = document.querySelector('#modal-ing-name')?.closest('.field')?.querySelector('p:last-child'); return p ? p.textContent : null; }"
            )
            return name, hint_text

        print("=== Bug confirmé n°1 : poids trouvé mais nom vide -> les DEUX messages doivent apparaître (plus de masquage) ===\n")
        page.route("**/world.openfoodfacts.org/**", lambda route: mock_off_route(route, {"status": 1, "product": {"quantity": "300 g"}}))
        scan("1000000000017")
        name1, hint1 = modal_texts()
        check("Le champ nom reste vide (la fiche n'avait pas de nom)", name1 == "", repr(name1))
        check("Le poids net (300 g) est bien indiqué", bool(hint1) and "300 g" in hint1, repr(hint1))
        check(
            "L'avertissement 'non trouvé automatiquement' apparaît AUSSI (ne disparaît plus derrière le poids)",
            bool(hint1) and "non trouvé automatiquement" in hint1,
            repr(hint1),
        )
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        print("\n=== Régression : produit trouvé avec nom ET poids -> pas de message 'non trouvé' superflu ===\n")
        page.route(
            "**/world.openfoodfacts.org/**",
            lambda route: mock_off_route(route, {"status": 1, "product": {"product_name_fr": "Compote de Pommes", "quantity": "4x100g"}}),
        )
        scan("1000000000024")
        name2, hint2 = modal_texts()
        check("Le nom est bien pré-rempli", name2 == "Compote de Pommes", repr(name2))
        check("Le poids est indiqué", bool(hint2) and "4x100g" in hint2, repr(hint2))
        check("Aucun message 'non trouvé' quand le nom est bien connu", not hint2 or "non trouvé automatiquement" not in hint2, repr(hint2))
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        print("\n=== Régression : produit vraiment absent de la base (aucun poids non plus) -> seul le message générique ===\n")
        page.route("**/world.openfoodfacts.org/**", lambda route: mock_off_route(route, {"status": 0}))
        scan("1000000000031")
        name3, hint3 = modal_texts()
        check("Le champ nom reste vide", name3 == "", repr(name3))
        check("Message générique 'non trouvé automatiquement' affiché", bool(hint3) and "non trouvé automatiquement" in hint3, repr(hint3))
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        print("\n=== Bug confirmé n°2 : panne réseau -> message DIFFÉRENT du 'produit non trouvé' générique ===\n")
        page.route("**/world.openfoodfacts.org/**", lambda route: route.abort())
        scan("1000000000048")
        name4, hint4 = modal_texts()
        check("Le formulaire s'ouvre malgré la panne (pas de plantage)", name4 == "", repr(name4))
        check(
            "Le message de panne réseau est affiché, PAS le message générique 'non trouvé automatiquement'",
            bool(hint4) and "non trouvé automatiquement" not in hint4 and ("connexion" in hint4.lower() or "inaccessible" in hint4.lower()),
            repr(hint4),
        )
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        print("\n=== Erreur HTTP (ex. 500) traitée comme une panne réseau, pas comme un produit inconnu ===\n")
        page.route("**/world.openfoodfacts.org/**", lambda route: mock_off_route(route, {}, status=500))
        scan("1000000000055")
        name5, hint5 = modal_texts()
        check("Le formulaire s'ouvre malgré l'erreur HTTP (pas de plantage)", name5 == "", repr(name5))
        check(
            "Le message de panne réseau est affiché pour une erreur HTTP 500 aussi",
            bool(hint5) and "non trouvé automatiquement" not in hint5 and ("connexion" in hint5.lower() or "inaccessible" in hint5.lower()),
            repr(hint5),
        )
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
