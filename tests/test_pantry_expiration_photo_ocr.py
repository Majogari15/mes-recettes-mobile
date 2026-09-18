#!/usr/bin/env python3
"""Test permanent : prise/import de photo pour préremplir la date de
péremption du garde-manger (demande explicite de l'utilisateur — même
principe que le scan de code-barres, déjà disponible, mais appliqué
cette fois à la date elle-même) — voir TESTS_NON_REGRESSION.md point 103.

Le vrai moteur Tesseract n'est jamais invoqué ici (trop lent et non
déterministe pour un test automatisé) : seule la fonction
`runExpirationDateOcr` (celle qui pilote Tesseract) est simulée, exactement
comme `storePut`/`storeWriteManyAcrossStores` sont simulées ailleurs pour
tester une logique en aval sans dépendre de la vraie couche sous-jacente.
L'heuristique d'extraction de date elle-même (`extractExpirationDateFromOcrText`)
est en revanche une fonction pure, testée directement avec de vrais textes
OCR représentatifs (mots-clés, formats ISO/européen, dates impossibles).

Couvre :
- Extraction correcte depuis un texte contenant un mot-clé de péremption
  ("DLC", "best before"...) juste avant la date.
- Une date sans mot-clé à proximité mais seule dans le texte reste malgré
  tout retenue (mieux qu'aucune pré-saisie).
- Une date accolée à un mot-clé de péremption est préférée à une autre
  date par ailleurs présente dans le même texte (ex. date de fabrication).
- Formats ISO et européen (JJ/MM/AA et JJ/MM/AAAA) tous deux reconnus.
- Une date calendairement impossible (31 février) est ignorée, sans faire
  planter l'extraction ni faire remonter cette fausse date.
- Aucune date dans le texte -> aucun résultat (jamais d'erreur).
- Bout en bout dans le formulaire du garde-manger : le bouton caméra et le
  bouton galerie déclenchent bien l'OCR simulé, préremplissent le champ de
  date en cas de succès (jamais un enregistrement automatique — l'article
  n'est sauvegardé qu'après un clic explicite sur "Enregistrer"), et
  affichent un message clair en cas d'échec (aucune date trouvée, ou erreur
  de l'OCR lui-même).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pantry_expiration_photo_ocr.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

        print("=== extractExpirationDateFromOcrText : heuristique pure ===\n")
        context1 = browser.new_context()
        page1 = context1.new_page()
        errors1 = []
        page1.on("pageerror", lambda exc: errors1.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(300)

        cases = page1.evaluate(
            """
            () => ({
                withKeywordIso: extractExpirationDateFromOcrText('Yaourt nature\\nDLC : 2026-03-15\\nLot A123'),
                withKeywordEuro: extractExpirationDateFromOcrText('CONSERVER AU FRAIS\\nA consommer avant le 15/03/2026\\nLot A123'),
                shortYear: extractExpirationDateFromOcrText('best before 15/03/26'),
                keywordPreferredOverOther: extractExpirationDateFromOcrText('Fabrique le 01/01/2026\\nDLC 15/03/2026'),
                bareDateAloneStillReturned: extractExpirationDateFromOcrText('Produit laitier 15/03/2026 conserver au frais'),
                impossibleDateIgnored: extractExpirationDateFromOcrText('DLC 31/02/2026'),
                impossibleDateWithValidFallback: extractExpirationDateFromOcrText('31/02/2026 mais DLC 10/04/2026'),
                noDateAtAll: extractExpirationDateFromOcrText('Yaourt nature au lait entier, sans aucune date'),
                emptyText: extractExpirationDateFromOcrText(''),
                nullText: extractExpirationDateFromOcrText(null),
            })
            """
        )
        check("Date ISO avec mot-clé DLC reconnue", cases["withKeywordIso"] == "2026-03-15", str(cases["withKeywordIso"]))
        check("Date européenne avec mot-clé reconnue", cases["withKeywordEuro"] == "2026-03-15", str(cases["withKeywordEuro"]))
        check("Année à 2 chiffres normalisée en 20XX", cases["shortYear"] == "2026-03-15", str(cases["shortYear"]))
        check(
            "Date accolée au mot-clé DLC préférée à la date de fabrication",
            cases["keywordPreferredOverOther"] == "2026-03-15",
            str(cases["keywordPreferredOverOther"]),
        )
        check("Une date seule sans mot-clé reste malgré tout retenue", cases["bareDateAloneStillReturned"] == "2026-03-15", str(cases["bareDateAloneStillReturned"]))
        check("Le 31 février (impossible) n'est jamais retenu", cases["impossibleDateIgnored"] is None, str(cases["impossibleDateIgnored"]))
        check(
            "Le 31 février ignoré, la date valide restante est retenue à la place",
            cases["impossibleDateWithValidFallback"] == "2026-04-10",
            str(cases["impossibleDateWithValidFallback"]),
        )
        check("Aucune date dans le texte -> aucun résultat", cases["noDateAtAll"] is None, str(cases["noDateAtAll"]))
        check("Texte vide -> aucun résultat (pas d'erreur)", cases["emptyText"] is None, str(cases["emptyText"]))
        check("Texte nul -> aucun résultat (pas d'erreur)", cases["nullText"] is None, str(cases["nullText"]))
        check("Aucune erreur JS pendant ces appels", not errors1, "; ".join(errors1))
        context1.close()

        print("\n=== Formulaire garde-manger : photo caméra/galerie préremplit la date, jamais d'enregistrement automatique ===\n")
        context2 = browser.new_context(viewport={"width": 390, "height": 844})
        page2 = context2.new_page()
        errors2 = []
        page2.on("pageerror", lambda exc: errors2.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(500)
        page2.evaluate("() => setLang('fr')")
        page2.evaluate("async () => { for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id); state.pantry = []; state.screen = 'pantry'; render(); }")
        page2.wait_for_timeout(200)

        # Simule l'OCR (jamais le vrai Tesseract dans ce test) : renvoie un
        # texte fixe contenant une date de péremption reconnaissable.
        page2.evaluate(
            """
            () => {
                window.__realRunExpirationDateOcr = window.runExpirationDateOcr;
                window.runExpirationDateOcr = async () => 'DLC : 20/12/2026';
            }
            """
        )
        page2.click(".fab")
        page2.wait_for_timeout(200)
        page2.click("#modal-ing-expiration-camera-btn")
        page2.set_input_files("#modal-ing-expiration-camera-input", FIXTURE_PNG)
        page2.wait_for_timeout(400)
        expirationValue = page2.eval_on_selector("#modal-ing-expiration", "el => el.value")
        statusText = page2.eval_on_selector("#modal-ing-expiration-ocr-status", "el => el.textContent")
        check("Le champ date est prérempli à partir de la photo (caméra)", expirationValue == "20/12/26", expirationValue)
        check("Un message de confirmation de la date détectée est affiché", "20/12/2026" in statusText or "20/12/26" in statusText, statusText)

        # Toujours pas enregistré tant que "Enregistrer" n'a pas été cliqué.
        pantryBeforeSave = page2.evaluate("() => storeAll('pantry')")
        check("Rien n'est encore enregistré avant le clic sur Enregistrer", pantryBeforeSave == [], str(pantryBeforeSave))

        page2.fill("#modal-ing-name", "Fromage à raclette")
        page2.click("#modal-confirm")
        page2.wait_for_timeout(300)
        pantryAfterSave = page2.evaluate("() => storeAll('pantry')")
        check(
            "Après confirmation manuelle, l'article est enregistré avec la date issue de la photo",
            len(pantryAfterSave) == 1 and pantryAfterSave[0]["expirationDate"] == "2026-12-20",
            str(pantryAfterSave),
        )

        print("\n=== Photo sans date reconnaissable : message d'échec clair, champ non modifié ===\n")
        page2.evaluate("async () => { for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id); state.pantry = []; render(); }")
        page2.wait_for_timeout(200)
        page2.evaluate("() => { window.runExpirationDateOcr = async () => 'Emballage sans aucune date visible'; }")
        page2.click(".fab")
        page2.wait_for_timeout(200)
        page2.click("#modal-ing-expiration-gallery-btn")
        page2.set_input_files("#modal-ing-expiration-gallery-input", FIXTURE_PNG)
        page2.wait_for_timeout(400)
        expirationValueAfterFail = page2.eval_on_selector("#modal-ing-expiration", "el => el.value")
        statusAfterFail = page2.eval_on_selector("#modal-ing-expiration-ocr-status", "el => el.textContent")
        check("Le champ reste vide quand aucune date n'est reconnue", expirationValueAfterFail == "", expirationValueAfterFail)
        check("Un message signale l'échec de la reconnaissance", bool(statusAfterFail) and "date" in statusAfterFail.lower(), statusAfterFail)
        page2.click("#modal-cancel")

        print("\n=== Échec de l'OCR lui-même (ex. erreur Tesseract) : message d'erreur affiché, jamais de plantage ===\n")
        page2.evaluate("() => { window.runExpirationDateOcr = async () => { throw new Error('tesseract_lib_load_failed'); }; }")
        page2.click(".fab")
        page2.wait_for_timeout(200)
        page2.click("#modal-ing-expiration-camera-btn")
        page2.set_input_files("#modal-ing-expiration-camera-input", FIXTURE_PNG)
        page2.wait_for_timeout(400)
        statusAfterError = page2.eval_on_selector("#modal-ing-expiration-ocr-status", "el => el.textContent")
        check("Un message d'erreur lisible est affiché en cas d'échec de l'OCR", "tesseract_lib_load_failed" in statusAfterError, statusAfterError)
        page2.click("#modal-cancel")

        page2.evaluate("() => { window.runExpirationDateOcr = window.__realRunExpirationDateOcr; }")
        check("Aucune erreur JS pendant tout le parcours du formulaire", not errors2, "; ".join(errors2))
        context2.close()

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
