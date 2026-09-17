#!/usr/bin/env python3
"""Test permanent : ajout au garde-manger par scan de code-barres
(demande explicite de l'utilisateur, étape 3 après la date de
péremption) — voir TESTS_NON_REGRESSION.md point 95.

Réseau réel jamais utilisé ici : les requêtes vers Open Food Facts sont
interceptées (page.route) et remplacées par des réponses contrôlées,
pour un test déterministe qui ne dépend ni d'Internet ni du contenu
changeant d'une vraie base de données.

Couvre : caméra indisponible (repli sur la saisie manuelle), code-barres
invalide, produit trouvé/non trouvé/erreur réseau, mémorisation du nom
ET de l'unité choisis pour un scan répété (pas de doublon, y compris
avec une unité différente de "boîte"), et survie de cette mémoire à un
aller-retour de sauvegarde locale.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_barcode_pantry.py

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


def mock_off_route(route, product_response):
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(product_response),
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
        print("=== Chemin caméra réel (détection simulée) : bout en bout jusqu'au garde-manger ===\n")
        cam_browser = p.chromium.launch(
            args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"]
        )
        cam_context = cam_browser.new_context(viewport={"width": 390, "height": 844}, permissions=["camera"])
        cam_page = cam_context.new_page()
        cam_errors = []
        cam_page.on("pageerror", lambda exc: cam_errors.append(str(exc)))
        cam_page.route(
            "**/world.openfoodfacts.org/**",
            lambda route: mock_off_route(route, {"status": 1, "product": {"product_name_fr": "Haricots Verts", "quantity": "400 g"}}),
        )
        cam_page.goto(base_url, timeout=8000)
        cam_page.wait_for_timeout(1000)
        cam_page.evaluate("() => setLang('fr')")
        # Simule une vraie détection : le détecteur natif existe et
        # renvoie un code-barres dès le premier appel, sans dépendre
        # d'un vrai motif de code-barres dans le flux caméra factice
        # (impossible à obtenir dans cet environnement sans écran).
        cam_page.evaluate(
            """
            () => {
                window.BarcodeDetector = class {
                    constructor() {}
                    async detect() { return [{ rawValue: '3170070001010' }]; }
                };
            }
            """
        )
        cam_page.evaluate("() => { state.screen = 'pantry'; render(); }")
        cam_page.click("text=Scanner un code-barres")
        cam_page.wait_for_timeout(2000)
        cam_prefilled = cam_page.evaluate("() => { const el = document.getElementById('modal-ing-name'); return el ? el.value : null; }")
        check(
            "Le vrai chemin caméra (getUserMedia + détecteur) aboutit au formulaire pré-rempli",
            cam_prefilled == "Haricots Verts",
            cam_prefilled,
        )
        if cam_page.is_visible("#modal-confirm"):
            cam_page.click("#modal-confirm")
            cam_page.wait_for_timeout(300)
        added = cam_page.evaluate("() => state.pantry.some(i => normalize(i.name) === normalize('Haricots Verts'))")
        check("L'article détecté par caméra est bien ajouté au garde-manger", added)
        check("Aucune erreur JS sur le chemin caméra", not cam_errors, "; ".join(cam_errors))
        cam_browser.close()

        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.wait_for_timeout(200)

        print("\n=== Bouton d'entrée présent sur l'écran garde-manger ===\n")
        check("Le bouton 'Scanner un code-barres' est visible", page.is_visible("text=Scanner un code-barres"))

        print("\n=== Caméra indisponible (pas de BarcodeDetector) : repli manuel proposé ===\n")
        page.evaluate("() => { delete window.BarcodeDetector; }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        check(
            "Message 'non pris en charge' affiché quand BarcodeDetector est absent",
            page.is_visible("text=n'est pas prise en charge"),
        )
        check("Le lien de saisie manuelle reste disponible", page.is_visible("text=Saisir le code-barres manuellement"))

        print("\n=== Saisie manuelle : code-barres trop court refusé ===\n")
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "123")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(200)
        check("Message d'erreur pour un code-barres incomplet", page.is_visible("text=incomplet"))
        page.click("#barcode-manual-close")
        page.wait_for_timeout(200)

        print("\n=== Produit trouvé (Open Food Facts simulé) : nom et poids net pré-remplis ===\n")
        page.route(
            "**/world.openfoodfacts.org/**",
            lambda route: mock_off_route(route, {
                "status": 1,
                "product": {"product_name_fr": "Maïs Doux Bonduelle", "product_name": "Sweet Corn", "quantity": "285 g"},
            }),
        )
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "3017620422003")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(500)
        prefilled_name = page.evaluate("() => { const el = document.getElementById('modal-ing-name'); return el ? el.value : null; }")
        hint_visible = page.is_visible("text=285 g")
        check("Le nom trouvé (en français) est pré-rempli dans le champ", prefilled_name == "Maïs Doux Bonduelle", prefilled_name)
        check("Le poids net (285 g) est affiché à titre indicatif", hint_visible)

        print("\n=== Confirmation avec un nom d'ingrédient existant (pas de doublon créé) ===\n")
        page.evaluate("""async () => {
            if (!state.ingredientNames.includes('Maïs en boîte')) await addIngredientName('Maïs en boîte');
        }""")
        page.fill("#modal-ing-name", "Maïs en boîte")
        page.click("#modal-confirm")
        page.wait_for_timeout(300)
        pantry_after_first = page.evaluate("() => state.pantry.filter(i => normalize(i.name) === normalize('Maïs en boîte'))")
        check(
            "Un seul article 'Maïs en boîte' créé, quantité 1, unité 'boîte'",
            len(pantry_after_first) == 1 and pantry_after_first[0]["quantity"] == 1 and pantry_after_first[0]["unit"] == "boîte",
            str(pantry_after_first),
        )

        print("\n=== Rescanner le MÊME code-barres : incrémente sans redemander (mémoire) ===\n")
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "3017620422003")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(400)
        alert_text = page.evaluate("() => { const el = document.getElementById('custom-alert-message'); return el ? el.textContent : null; }")
        check(
            "Une confirmation directe s'affiche (pas le formulaire) avec la bonne quantité",
            alert_text is not None and "2" in alert_text and "Maïs en boîte" in alert_text,
            alert_text,
        )
        page.click("#custom-alert-ok")
        page.wait_for_timeout(200)
        pantry_after_second = page.evaluate("() => state.pantry.filter(i => normalize(i.name) === normalize('Maïs en boîte'))")
        check(
            "Toujours un seul article (pas de doublon), quantité passée à 2",
            len(pantry_after_second) == 1 and pantry_after_second[0]["quantity"] == 2,
            str(pantry_after_second),
        )

        print("\n=== Produit non trouvé : formulaire vide + message explicite, pas de plantage ===\n")
        page.route("**/world.openfoodfacts.org/**", lambda route: mock_off_route(route, {"status": 0}))
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "0000000000000")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(500)
        empty_name = page.evaluate("() => { const el = document.getElementById('modal-ing-name'); return el ? el.value : null; }")
        check("Le champ nom reste vide quand le produit n'est pas trouvé", empty_name == "", repr(empty_name))
        check("Le message 'produit non trouvé' est affiché", page.is_visible("text=non trouvé automatiquement"))
        page.click("#modal-cancel")
        page.wait_for_timeout(200)

        print("\n=== Panne réseau : même repli propre (pas de plantage, formulaire manuel) ===\n")
        page.route("**/world.openfoodfacts.org/**", lambda route: route.abort())
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "1111111111111")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(500)
        modal_open_after_failure = page.is_visible("#modal-ing-name")
        check("Le formulaire d'ajout manuel s'ouvre malgré la panne réseau", modal_open_after_failure)
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        print("\n=== Unité différente de \"boîte\" bien mémorisée (pas de doublon avec une fausse unité) ===\n")
        page.route(
            "**/world.openfoodfacts.org/**",
            lambda route: mock_off_route(route, {"status": 1, "product": {"product_name_fr": "Riz Basmati", "quantity": "1 kg"}}),
        )
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "9999999999999")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(500)
        # Choisit "kg" plutôt que la valeur par défaut "boîte" — ce cas
        # précis a corrigé un vrai bug (voir TESTS_NON_REGRESSION.md 95) :
        # la mémorisation ne retenait que le nom, pas l'unité.
        page.select_option("#modal-ing-unit", "kg")
        page.click("#modal-confirm")
        page.wait_for_timeout(300)
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "9999999999999")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(400)
        rice_items = page.evaluate("() => state.pantry.filter(i => normalize(i.name) === normalize('Riz Basmati'))")
        check(
            "Un seul article 'Riz Basmati', en kg, quantité 2 (pas de doublon en 'boîte')",
            len(rice_items) == 1 and rice_items[0]["unit"] == "kg" and rice_items[0]["quantity"] == 2,
            str(rice_items),
        )
        page.click("#custom-alert-ok")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        print("\n=== Survie de la mémoire code-barres à un aller-retour de sauvegarde locale ===\n")
        roundtrip = page.evaluate(
            """
            async () => {
                const backup = await buildBackupData();
                await importAllData(backup, 'replace');
                return state.barcodeIngredientMap['3017620422003'];
            }
            """
        )
        check(
            "La mémorisation (nom + unité) survit à un export puis réimport",
            roundtrip is not None and roundtrip.get("name") == "Maïs en boîte" and roundtrip.get("unit") == "boîte",
            str(roundtrip),
        )

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
