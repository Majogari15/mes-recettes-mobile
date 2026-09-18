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
# Image minimale valide (1x1 px) — le contenu réel n'a aucune
# importance pour les tests d'import depuis une photo : le détecteur
# de code-barres est simulé (voir plus bas), seul le fait qu'un
# VRAI fichier image se charge correctement dans un <canvas> compte.
FIXTURE_PNG = os.path.join(PROJECT_ROOT, "tests", "fixtures", "tiny_blank.png")


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
        check("Le bouton 'Importer depuis une photo' est visible à côté", page.is_visible("text=Importer depuis une photo"))

        print("\n=== Import depuis une photo : code-barres détecté (détection simulée) ===\n")
        page.route(
            "**/world.openfoodfacts.org/**",
            lambda route: mock_off_route(route, {"status": 1, "product": {"product_name_fr": "Compote de Pommes", "quantity": "4x100g"}}),
        )
        page.evaluate(
            """
            () => {
                window.BarcodeDetector = class {
                    constructor() {}
                    async detect() { return [{ rawValue: '3033710065912' }]; }
                };
            }
            """
        )
        page.set_input_files("#barcode-import-photo-input", str(FIXTURE_PNG))
        page.wait_for_timeout(500)
        photo_prefilled = page.evaluate("() => { const el = document.getElementById('modal-ing-name'); return el ? el.value : null; }")
        check("Le code-barres détecté sur la photo déclenche bien la recherche du produit", photo_prefilled == "Compote de Pommes", photo_prefilled)
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

        print("\n=== Import depuis une photo : aucun code-barres reconnu ===\n")
        page.evaluate(
            """
            () => {
                window.BarcodeDetector = class {
                    constructor() {}
                    async detect() { return []; }
                };
            }
            """
        )
        page.set_input_files("#barcode-import-photo-input", str(FIXTURE_PNG))
        page.wait_for_timeout(500)
        check("Message clair quand aucun code-barres n'est reconnu sur la photo", page.is_visible("text=Aucun code-barres reconnu"))
        page.click("#custom-alert-ok")
        page.wait_for_timeout(200)

        print("\n=== Import depuis une photo : détecteur natif indisponible ===\n")
        page.evaluate("() => { delete window.BarcodeDetector; }")
        page.set_input_files("#barcode-import-photo-input", str(FIXTURE_PNG))
        page.wait_for_timeout(300)
        check("Message 'non pris en charge' affiché (pas de plantage)", page.is_visible("text=n'est pas prise en charge"))
        page.click("#custom-alert-ok")
        page.wait_for_timeout(200)

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

        print("\n=== Saisie manuelle : clé de contrôle EAN invalide refusée AVANT toute requête réseau ===\n")
        # Recommandé par un audit externe : une longueur correcte (8/12/13
        # chiffres) mais une clé de contrôle fausse trahit presque
        # toujours une erreur de frappe — sans cette vérification, un tel
        # code partait quand même interroger Open Food Facts pour rien.
        network_calls = []
        page.on("request", lambda req: network_calls.append(req.url) if "openfoodfacts" in req.url else None)
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        # "3017620422004" : même code que "Maïs en boîte" plus loin, mais
        # avec le dernier chiffre volontairement faussé (clé de contrôle
        # invalide) — simule une erreur de frappe plausible (un chiffre
        # mal recopié) plutôt qu'un code-barres aléatoire.
        page.fill("#barcode-manual-input", "3017620422004")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(300)
        check("Message dédié affiché pour une clé de contrôle invalide (pas le message 'incomplet')", page.is_visible("text=ne semble pas valide"))
        check("Le formulaire de recherche ne s'est PAS ouvert (aucune requête réseau déclenchée)", not page.is_visible("#modal-ing-name"))
        check("Aucune requête vers Open Food Facts n'a été envoyée pour ce code invalide", network_calls == [], str(network_calls))
        page.click("#barcode-manual-close")
        page.wait_for_timeout(200)

        print("\n=== Saisie manuelle : un EAN-8 et un UPC-A (12 chiffres) valides sont bien acceptés ===\n")
        page.route("**/world.openfoodfacts.org/**", lambda route: mock_off_route(route, {"status": 0}))
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "96385074")  # EAN-8 valide
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(300)
        check("Un EAN-8 valide (8 chiffres) est accepté, le formulaire s'ouvre", page.is_visible("#modal-ing-name"))
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "036000291452")  # UPC-A valide
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(300)
        check("Un UPC-A valide (12 chiffres) est accepté, le formulaire s'ouvre", page.is_visible("#modal-ing-name"))
        page.click("#modal-cancel")
        page.wait_for_timeout(200)
        page.unroute("**/world.openfoodfacts.org/**")

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

        print("\n=== Rescanner le MÊME code-barres : formulaire pré-rempli (nom, unité, quantité à AJOUTER = 1 par défaut), jamais d'ajout automatique silencieux ===\n")
        # Retour direct de l'utilisateur (TESTS_NON_REGRESSION.md point
        # 106) : l'ancien raccourci "ajout automatique, +1 direct" ne
        # laissait aucune façon de saisir une quantité différente ou une
        # nouvelle date de péremption sur un rescan. Le formulaire s'ouvre
        # donc maintenant à chaque fois. Une PREMIÈRE version de ce
        # correctif préremplissait la case avec l'ANCIEN TOTAL + 1 — jugé
        # trompeur par l'utilisateur (voir point 107) : la case représente
        # maintenant combien on vient d'EN AJOUTER (préremplie à 1, jamais
        # le nouveau total), additionnée au stock existant seulement à
        # l'enregistrement.
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "3017620422003")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(400)
        rescan_prefill = page.evaluate(
            """
            () => ({
                name: document.getElementById('modal-ing-name')?.value,
                unit: document.getElementById('modal-ing-unit')?.value,
                qty: document.getElementById('modal-ing-qty')?.value,
            })
            """
        )
        check(
            "Le formulaire (pas une alerte) s'ouvre, pré-rempli avec le nom/l'unité connus et une quantité à AJOUTER de 1 (jamais l'ancien total)",
            rescan_prefill == {"name": "Maïs en boîte", "unit": "boîte", "qty": "1"},
            str(rescan_prefill),
        )
        check(
            "Une indication du stock actuel est affichée, pour éviter toute confusion sur ce que représente la case",
            page.is_visible("text=Stock actuel : 1 boîte"),
        )
        page.click("#modal-confirm")
        page.wait_for_timeout(300)
        pantry_after_second = page.evaluate("() => state.pantry.filter(i => normalize(i.name) === normalize('Maïs en boîte'))")
        check(
            "Toujours un seul article (pas de doublon), quantité passée à 2 (1 déjà là + 1 ajouté, valeur par défaut)",
            len(pantry_after_second) == 1 and pantry_after_second[0]["quantity"] == 2,
            str(pantry_after_second),
        )

        print("\n=== Rescanner encore le même code-barres : la quantité saisie s'AJOUTE au stock existant, ne le remplace jamais ===\n")
        # Cas exact soulevé par l'utilisateur : 2 déjà présents, la
        # personne en ajoute 2 de plus -> doit obtenir 4 au total, pas 2
        # (ce qui se serait produit avec l'ancien préremplissage "ancien
        # total + 1", en corrigeant "3" en "2" pour indiquer les 2 ajoutés
        # — un total qui aurait alors ÉCRASÉ les 2 déjà présents).
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.click("text=Scanner un code-barres")
        page.wait_for_timeout(200)
        page.click("text=Saisir le code-barres manuellement")
        page.wait_for_timeout(200)
        page.fill("#barcode-manual-input", "3017620422003")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(400)
        page.fill("#modal-ing-qty", "2")
        page.fill("#modal-ing-expiration", "011226")
        page.click("#modal-confirm")
        page.wait_for_timeout(300)
        pantry_after_third = page.evaluate("() => state.pantry.filter(i => normalize(i.name) === normalize('Maïs en boîte'))")
        check(
            "2 déjà présents + 2 ajoutés = 4 au total (jamais écrasé à 2), et la date de péremption saisie est bien prise en compte",
            len(pantry_after_third) == 1 and pantry_after_third[0]["quantity"] == 4 and pantry_after_third[0]["expirationDate"] == "2026-12-01",
            str(pantry_after_third),
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
        page.fill("#barcode-manual-input", "1111111111116")
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
        page.fill("#barcode-manual-input", "9999999999994")
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
        page.fill("#barcode-manual-input", "9999999999994")
        page.click("#barcode-manual-submit")
        page.wait_for_timeout(400)
        rice_rescan_prefill = page.evaluate(
            """
            () => ({
                unit: document.getElementById('modal-ing-unit')?.value,
                qty: document.getElementById('modal-ing-qty')?.value,
            })
            """
        )
        check(
            "Le rescan pré-remplit bien l'unité mémorisée ('kg', pas 'boîte') avec une quantité à ajouter de 1 (jamais l'ancien total)",
            rice_rescan_prefill == {"unit": "kg", "qty": "1"},
            str(rice_rescan_prefill),
        )
        page.click("#modal-confirm")
        page.wait_for_timeout(300)
        rice_items = page.evaluate("() => state.pantry.filter(i => normalize(i.name) === normalize('Riz Basmati'))")
        check(
            "Un seul article 'Riz Basmati', en kg, quantité 2 (1 déjà là + 1 ajouté, pas de doublon en 'boîte')",
            len(rice_items) == 1 and rice_items[0]["unit"] == "kg" and rice_items[0]["quantity"] == 2,
            str(rice_items),
        )
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
