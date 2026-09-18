#!/usr/bin/env python3
"""Test permanent : import de code-barres depuis une photo qui n'est PAS
droite (photo cadrée en portrait, à l'envers, ou de côté) — signalé par
l'utilisateur avec 4 vraies photos de produits (toutes prises de travers)
que l'application ne reconnaissait pas.

Contexte : le détecteur natif (`BarcodeDetector`) recevait jusqu'ici
toujours l'image exactement comme prise, sans aucune correction —
contrairement au scan caméra en direct où l'appareil est généralement
tenu à peu près à l'horizontale, une photo déjà prise d'un produit peut
être cadrée dans n'importe quel sens. `decodeBarcodeImageFile()` essaie
désormais l'image telle que prise puis, si rien n'est trouvé, 3 rotations
supplémentaires (90/180/270°) avant d'abandonner — même fonction de
rotation (`rotateImageClockwise`) que celle qui remet déjà à l'endroit une
photo pour l'OCR.

Important — limite connue de ce test : le vrai `BarcodeDetector` natif
n'existe pas dans Chromium hors d'un vrai appareil (vérifié directement :
`"BarcodeDetector" in window` renvoie `false` dans cet environnement de
test), donc son comportement réel face à une rotation ne peut pas être
observé ici. Ce test simule `BarcodeDetector` pour vérifier ce qui EST
vérifiable automatiquement : que le code appelle bien `detect()` sur
chacune des 4 rotations dans l'ordre, avec une image aux bonnes
dimensions à chaque fois, qu'il s'arrête dès qu'une rotation réussit
(sans essayer les suivantes), qu'une exception sur une rotation
n'interrompt pas l'essai des suivantes, et qu'aucune rotation qui réussit
nulle part renvoie bien `null` (pas de plantage). Il ne prouve PAS que
cela résout le cas réel signalé par l'utilisateur — seul un nouveau test
sur le vrai téléphone peut le confirmer.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_barcode_rotation_retry.py

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


# Fabrique un fichier JPEG 200x100 (volontairement non carré, comme les
# vraies photos signalées : une rotation change ses dimensions, ce qui
# permet de vérifier que chaque tentative reçoit bien l'image dans le
# bon sens plutôt que de le supposer).
MAKE_TEST_FILE_JS = """
async () => {
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 100;
    canvas.getContext('2d').fillRect(0, 0, 200, 100);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg'));
    return new File([blob], 'photo.jpg', { type: 'image/jpeg' });
}
"""


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

        print("=== Réussite dès la 1ère tentative (0°) : comportement inchangé, une seule tentative ===\n")
        context1 = browser.new_context()
        page1 = context1.new_page()
        errors1 = []
        page1.on("pageerror", lambda exc: errors1.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(300)
        result1 = page1.evaluate(
            """
            async () => {
                const file = await (%s)();
                let callCount = 0;
                const capturedDims = [];
                window.BarcodeDetector = class {
                    constructor() {}
                    async detect(input) {
                        callCount += 1;
                        capturedDims.push([input.width, input.height]);
                        return [{ rawValue: '3245412950872' }];
                    }
                };
                const result = await decodeBarcodeImageFile(file);
                return { result, callCount, capturedDims };
            }
            """ % MAKE_TEST_FILE_JS
        )
        check("Le code-barres est bien renvoyé", result1["result"] == "3245412950872", str(result1))
        check("Une seule tentative suffit quand la 1ère réussit (pas de rotation inutile)", result1["callCount"] == 1, str(result1))
        check("La 1ère tentative reçoit l'image dans ses dimensions d'origine (200x100)", result1["capturedDims"] == [[200, 100]], str(result1))
        context1.close()

        print("\n=== Échec à 0° et 90°, réussite à 180° : les rotations suivantes sont bien essayées, dans l'ordre, avec les bonnes dimensions ===\n")
        context2 = browser.new_context()
        page2 = context2.new_page()
        errors2 = []
        page2.on("pageerror", lambda exc: errors2.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(300)
        result2 = page2.evaluate(
            """
            async () => {
                const file = await (%s)();
                let callCount = 0;
                const capturedDims = [];
                window.BarcodeDetector = class {
                    constructor() {}
                    async detect(input) {
                        callCount += 1;
                        capturedDims.push([input.width, input.height]);
                        if (callCount === 3) return [{ rawValue: '3560071006822' }];
                        return [];
                    }
                };
                const result = await decodeBarcodeImageFile(file);
                return { result, callCount, capturedDims };
            }
            """ % MAKE_TEST_FILE_JS
        )
        check("Le code-barres de la 3e tentative (180°) est bien renvoyé", result2["result"] == "3560071006822", str(result2))
        check("Exactement 3 tentatives (arrêt dès la réussite, la 4e — 270° — n'est jamais essayée)", result2["callCount"] == 3, str(result2))
        check(
            "Dimensions correctes à chaque tentative : 200x100 (0°), 100x200 (90°), 200x100 (180°)",
            result2["capturedDims"] == [[200, 100], [100, 200], [200, 100]],
            str(result2),
        )
        context2.close()

        print("\n=== Aucune rotation ne fonctionne : renvoie null après avoir essayé les 4, pas de plantage ===\n")
        context3 = browser.new_context()
        page3 = context3.new_page()
        errors3 = []
        page3.on("pageerror", lambda exc: errors3.append(str(exc)))
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(300)
        result3 = page3.evaluate(
            """
            async () => {
                const file = await (%s)();
                let callCount = 0;
                window.BarcodeDetector = class {
                    constructor() {}
                    async detect() { callCount += 1; return []; }
                };
                const result = await decodeBarcodeImageFile(file);
                return { result, callCount };
            }
            """ % MAKE_TEST_FILE_JS
        )
        check("Renvoie null (aucun code-barres trouvé) sans planter", result3["result"] is None, str(result3))
        check("Les 4 rotations (0/90/180/270°) ont bien été essayées", result3["callCount"] == 4, str(result3))
        context3.close()

        print("\n=== Une exception sur une rotation n'interrompt pas l'essai des suivantes ===\n")
        context4 = browser.new_context()
        page4 = context4.new_page()
        errors4 = []
        page4.on("pageerror", lambda exc: errors4.append(str(exc)))
        page4.goto(base_url, timeout=8000)
        page4.wait_for_timeout(300)
        result4 = page4.evaluate(
            """
            async () => {
                const file = await (%s)();
                let callCount = 0;
                window.BarcodeDetector = class {
                    constructor() {}
                    async detect() {
                        callCount += 1;
                        if (callCount <= 2) throw new Error('detector_transient_error');
                        return [{ rawValue: '3560071493882' }];
                    }
                };
                const result = await decodeBarcodeImageFile(file);
                return { result, callCount };
            }
            """ % MAKE_TEST_FILE_JS
        )
        check(
            "Malgré 2 exceptions successives, la 3e tentative (180°) réussit bien",
            result4["result"] == "3560071493882" and result4["callCount"] == 3,
            str(result4),
        )
        context4.close()

        errors_all = errors1 + errors2 + errors3 + errors4
        check("Aucune erreur JS pendant tout le parcours", not errors_all, "; ".join(errors_all))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
