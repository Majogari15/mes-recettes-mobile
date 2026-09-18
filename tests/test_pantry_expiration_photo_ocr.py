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
- `runExpirationDateOcr` remet réellement à l'endroit une photo pivotée
  avant l'OCR (même pipeline `detectAndCorrectOrientation` que l'import
  photo de recette, point 16) : rotation appliquée si l'orientation est
  détectée avec une confiance suffisante, image inchangée si la confiance
  est trop faible ou si la détection elle-même échoue (jamais bloquant).

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

        print("\n=== runExpirationDateOcr : la photo pivotée est bien remise à l'endroit avant l'OCR (même pipeline que l'import de recette, point 16) ===\n")
        context3 = browser.new_context()
        page3 = context3.new_page()
        errors3 = []
        page3.on("pageerror", lambda exc: errors3.append(str(exc)))
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(300)

        # runExpirationDateOcr() réutilise detectAndCorrectOrientation() —
        # la même fonction déjà chargée de remettre à l'endroit une photo de
        # recette prise à l'envers ou de côté (point 16) — jamais une copie
        # ni une réimplémentation. Pour le vérifier réellement (pas
        # seulement en le lisant dans le code), seuls les DEUX workers
        # Tesseract sous-jacents sont simulés ici (OSD pour l'orientation,
        # principal pour la reconnaissance) ; detectAndCorrectOrientation,
        # resizeImageForOcr et rotateImageClockwise tournent pour de vrai,
        # sur une vraie image 200x100 (volontairement non carrée : une
        # rotation de 90°/270° change ses dimensions, contrairement à une
        # image carrée qui masquerait le bug si la rotation ne se produisait
        # pas réellement).
        result3 = page3.evaluate(
            """
            async ({ orientationDegrees, confidence }) => {
                const canvas = document.createElement('canvas');
                canvas.width = 200;
                canvas.height = 100;
                canvas.getContext('2d').fillRect(0, 0, 200, 100);
                const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg'));
                const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });

                window.getSharedOsdWorker = async () => ({
                    detect: async () => ({ data: { orientation_degrees: orientationDegrees, orientation_confidence: confidence } }),
                });
                let capturedWidth = null, capturedHeight = null;
                window.getSharedTesseractWorker = async () => ({
                    recognize: async (input) => {
                        capturedWidth = input.width;
                        capturedHeight = input.height;
                        return { data: { text: 'DLC 2026-01-01' } };
                    },
                });
                await runExpirationDateOcr(file);
                return { capturedWidth, capturedHeight };
            }
            """,
            {"orientationDegrees": 90, "confidence": 10},
        )
        check(
            "Rotation 90° avec confiance suffisante : largeur/hauteur bien inversées avant l'OCR (200x100 -> 100x200)",
            result3["capturedWidth"] == 100 and result3["capturedHeight"] == 200,
            str(result3),
        )

        # Note : un fichier NON pivoté reste le File original (jamais
        # converti en <canvas>) — il n'a donc pas de propriété
        # width/height comme un <canvas> pivoté en aurait, contrairement à
        # ce qu'on pourrait naïvement comparer ; c'est justement la
        # présence ou l'absence de cette conversion en <canvas> qui permet
        # de distinguer de façon fiable "pivoté" de "laissé inchangé" ici.
        result3_low_confidence = page3.evaluate(
            """
            async ({ orientationDegrees, confidence }) => {
                const canvas = document.createElement('canvas');
                canvas.width = 200;
                canvas.height = 100;
                canvas.getContext('2d').fillRect(0, 0, 200, 100);
                const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg'));
                const file = new File([blob], 'photo2.jpg', { type: 'image/jpeg' });

                window.getSharedOsdWorker = async () => ({
                    detect: async () => ({ data: { orientation_degrees: orientationDegrees, orientation_confidence: confidence } }),
                });
                let wasConvertedToCanvas = null, sameFileInstance = null;
                window.getSharedTesseractWorker = async () => ({
                    recognize: async (input) => {
                        wasConvertedToCanvas = input instanceof HTMLCanvasElement;
                        sameFileInstance = input === file;
                        return { data: { text: 'DLC 2026-01-01' } };
                    },
                });
                await runExpirationDateOcr(file);
                return { wasConvertedToCanvas, sameFileInstance };
            }
            """,
            {"orientationDegrees": 90, "confidence": 0},
        )
        check(
            "Confiance insuffisante : l'image n'est PAS pivotée à tort (le File original arrive inchangé à l'OCR)",
            result3_low_confidence["wasConvertedToCanvas"] is False and result3_low_confidence["sameFileInstance"] is True,
            str(result3_low_confidence),
        )

        result3_osd_failure = page3.evaluate(
            """
            async () => {
                const canvas = document.createElement('canvas');
                canvas.width = 200;
                canvas.height = 100;
                canvas.getContext('2d').fillRect(0, 0, 200, 100);
                const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg'));
                const file = new File([blob], 'photo3.jpg', { type: 'image/jpeg' });

                window.getSharedOsdWorker = async () => { throw new Error('osd_unavailable'); };
                let wasConvertedToCanvas = null, sameFileInstance = null, ocrError = null;
                window.getSharedTesseractWorker = async () => ({
                    recognize: async (input) => {
                        wasConvertedToCanvas = input instanceof HTMLCanvasElement;
                        sameFileInstance = input === file;
                        return { data: { text: 'DLC 2026-01-01' } };
                    },
                });
                try {
                    await runExpirationDateOcr(file);
                } catch (e) {
                    ocrError = String(e);
                }
                return { wasConvertedToCanvas, sameFileInstance, ocrError };
            }
            """
        )
        check(
            "OSD indisponible : jamais bloquant, l'OCR continue sur l'image inchangée (le File original, pas converti)",
            result3_osd_failure["ocrError"] is None and result3_osd_failure["wasConvertedToCanvas"] is False and result3_osd_failure["sameFileInstance"] is True,
            str(result3_osd_failure),
        )
        check("Aucune erreur JS pendant ces appels", not errors3, "; ".join(errors3))
        context3.close()

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
