#!/usr/bin/env python3
"""Test permanent : accès matériel réel à la caméra pour le scanner de
QR code et le scan de code-barres (`openQrScanModal` et
`openBarcodeScanModal`, les deux seuls endroits de l'application
appelant `getUserMedia` — le sélecteur de photo de recette utilise lui
un simple `<input type="file" capture>`, qui délègue entièrement à
l'application caméra du système et n'a donc pas de permission
navigateur à tester) — voir TESTS_NON_REGRESSION.md points 92 et 98.

Couvre aussi le message d'erreur spécifique à la cause réelle de
l'échec (`describeCameraError` dans app.js, demandé explicitement par
l'utilisateur après avoir découvert que l'autorisation caméra était
désactivée sur son téléphone sans que le message d'origine, générique,
ne le précise) : permission refusée/désactivée, aucune caméra détectée,
caméra déjà utilisée par une autre application.

Utilise une caméra factice fournie par Chromium
(--use-fake-device-for-media-stream) plutôt qu'un vrai capteur : dans
cet environnement sans écran ni matériel, c'est la façon standard de
vérifier que le VRAI chemin de code `getUserMedia` (permission,
obtention du flux, affichage dans un <video>) fonctionne, plutôt que de
se contenter de vérifier que le bouton existe.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pwa_camera_permission.py

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
        print("=== Permission caméra accordée + caméra factice (cas normal) ===\n")
        browser = p.chromium.launch(
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
            ]
        )
        context = browser.new_context(viewport={"width": 390, "height": 844}, permissions=["camera"])
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")

        page.evaluate("() => { openQrScanModal(); }")
        page.wait_for_timeout(1500)

        video_playing = page.evaluate(
            """
            () => {
                const video = document.querySelector('#qrscan-holder video');
                return !!video && video.readyState >= 2 && video.videoWidth > 0;
            }
            """
        )
        check("Un flux vidéo réel (caméra factice) est bien affiché dans le scanner QR", video_playing)
        manual_enabled = page.evaluate("() => { const b = document.getElementById('qrscan-manual'); return b && !b.disabled; }")
        check("Le bouton de saisie manuelle se débloque une fois la caméra active", manual_enabled)
        browser.close()

        print("\n=== Permission caméra refusée par l'utilisateur ===\n")
        browser2 = p.chromium.launch()
        context2 = browser2.new_context(viewport={"width": 390, "height": 844})
        page2 = context2.new_page()
        page2.on("pageerror", lambda exc: errors.append(str(exc)))
        # Aucune permission accordée au contexte, et on force le refus
        # explicitement : simule un clic "Refuser" sur la vraie invite du
        # navigateur, plutôt que le silence d'une permission simplement
        # non accordée (qui pourrait masquer un vrai NotAllowedError).
        page2.add_init_script(
            """
            navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
            """
        )
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(1000)
        page2.evaluate("() => setLang('fr')")
        page2.evaluate("() => { openQrScanModal(); }")
        page2.wait_for_timeout(500)
        denied_message = page2.evaluate("() => document.getElementById('qrscan-camera-status').textContent.trim()")
        expected_permission_msg = page2.evaluate("() => t('qrscan_camera_denied_permission')")
        check(
            "Le message spécifique 'autorisation désactivée' (pas le message générique) s'affiche quand la permission caméra est refusée",
            denied_message == expected_permission_msg,
            denied_message,
        )
        fallback_visible = page2.is_visible("#qrscan-choose-image")
        check("Le repli \"choisir une image\" reste disponible malgré le refus de permission", fallback_visible)
        browser2.close()

        print("\n=== Aucune caméra détectée sur l'appareil ===\n")
        browser3 = p.chromium.launch()
        context3 = browser3.new_context(viewport={"width": 390, "height": 844})
        page3 = context3.new_page()
        page3.on("pageerror", lambda exc: errors.append(str(exc)))
        page3.add_init_script(
            """
            navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('No camera', 'NotFoundError'));
            """
        )
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(1000)
        page3.evaluate("() => setLang('fr')")
        page3.evaluate("() => { openQrScanModal(); }")
        page3.wait_for_timeout(500)
        notfound_message = page3.evaluate("() => document.getElementById('qrscan-camera-status').textContent.trim()")
        expected_notfound_msg = page3.evaluate("() => t('qrscan_camera_denied_notfound')")
        check(
            "Le message spécifique 'aucune caméra détectée' s'affiche pour une NotFoundError",
            notfound_message == expected_notfound_msg,
            notfound_message,
        )
        browser3.close()

        print("\n=== Caméra déjà utilisée par une autre application ===\n")
        browser4 = p.chromium.launch()
        context4 = browser4.new_context(viewport={"width": 390, "height": 844})
        page4 = context4.new_page()
        page4.on("pageerror", lambda exc: errors.append(str(exc)))
        page4.add_init_script(
            """
            navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Camera busy', 'NotReadableError'));
            """
        )
        page4.goto(base_url, timeout=8000)
        page4.wait_for_timeout(1000)
        page4.evaluate("() => setLang('fr')")
        page4.evaluate("() => { openQrScanModal(); }")
        page4.wait_for_timeout(500)
        busy_message = page4.evaluate("() => document.getElementById('qrscan-camera-status').textContent.trim()")
        expected_busy_msg = page4.evaluate("() => t('qrscan_camera_denied_busy')")
        check(
            "Le message spécifique 'caméra déjà utilisée' s'affiche pour une NotReadableError",
            busy_message == expected_busy_msg,
            busy_message,
        )
        browser4.close()

        print("\n=== Le scan de code-barres partage le même message spécifique (permission refusée) ===\n")
        browser5 = p.chromium.launch()
        context5 = browser5.new_context(viewport={"width": 390, "height": 844})
        page5 = context5.new_page()
        page5.on("pageerror", lambda exc: errors.append(str(exc)))
        page5.add_init_script(
            """
            navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
            window.BarcodeDetector = class {
                constructor() {}
                async detect() { return []; }
            };
            """
        )
        page5.goto(base_url, timeout=8000)
        page5.wait_for_timeout(1000)
        page5.evaluate("() => setLang('fr')")
        page5.evaluate("() => { state.screen = 'pantry'; render(); openBarcodeScanModal(); }")
        page5.wait_for_timeout(500)
        barcode_denied_message = page5.evaluate("() => document.getElementById('barcode-camera-status').textContent.trim()")
        expected_barcode_msg = page5.evaluate("() => t('qrscan_camera_denied_permission')")
        check(
            "Le scan de code-barres affiche aussi le message spécifique 'autorisation désactivée'",
            barcode_denied_message == expected_barcode_msg,
            barcode_denied_message,
        )
        browser5.close()

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
