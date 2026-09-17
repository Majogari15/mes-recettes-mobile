#!/usr/bin/env python3
"""Test permanent : le formulaire de recette permet d'importer une photo
déjà présente sur le téléphone, pas seulement d'en prendre une nouvelle.
Demande explicite de l'utilisateur — voir TESTS_NON_REGRESSION.md.

Avant ce correctif, le seul champ disponible portait l'attribut
`capture="environment"`, qui force les navigateurs mobiles à ouvrir
directement l'appareil photo et empêche de choisir une image existante
dans la galerie. Corrigé avec deux boutons distincts (comme le fait déjà
l'écran d'import photo/OCR) : un pour prendre une photo, un pour en
choisir une depuis la galerie (sans `capture`).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_recipe_form_photo_gallery.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import base64
import http.server
import os
import socket
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Un PNG 1x1 minimal valide, suffisant pour être décodé par le
# redimensionnement canvas de l'app sans dépendance externe (Pillow).
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="


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

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(base64.b64decode(TINY_PNG_B64))
        tmp_photo_path = tmp.name

    try:
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

            print("=== Deux boutons distincts (photo / galerie), aucun champ dans la zone d'aperçu ===\n")
            structure = page.evaluate(
                """
                () => {
                    const box = document.querySelector('.photo-upload');
                    const inputs = Array.from(document.querySelectorAll('input[type=file]'));
                    return {
                        noInputInsidePreview: box.querySelectorAll('input[type=file]').length === 0,
                        inputCount: inputs.length,
                        captures: inputs.map((i) => i.getAttribute('capture')),
                        cameraButtonExists: Array.from(document.querySelectorAll('button')).some((b) => b.textContent.includes('Prendre une photo')),
                        galleryButtonExists: Array.from(document.querySelectorAll('button')).some((b) => b.textContent.includes('galerie')),
                    };
                }
                """
            )
            check(
                "la zone d'aperçu n'a plus de champ de fichier à l'intérieur (juste un aperçu)",
                structure["noInputInsidePreview"] is True,
                str(structure),
            )
            check(
                "il existe exactement 2 champs de fichier : un avec capture (appareil photo), un sans (galerie)",
                structure["inputCount"] == 2 and "environment" in structure["captures"] and None in structure["captures"],
                str(structure),
            )
            check("le bouton 'Prendre une photo' existe", structure["cameraButtonExists"] is True, str(structure))
            check("le bouton 'Choisir depuis la galerie' existe", structure["galleryButtonExists"] is True, str(structure))
            print()

            print("=== Choisir un fichier via le bouton Galerie définit bien la photo de la recette ===\n")
            gallery_input = page.locator("input[type=file]:not([capture])")
            gallery_input.set_input_files(tmp_photo_path)
            page.wait_for_timeout(300)
            after_gallery = page.evaluate("() => ({ hasPhoto: !!state.formPhoto, previewHasImg: !!document.querySelector('.photo-upload img') })")
            check(
                "state.formPhoto est bien défini après un import depuis la galerie",
                after_gallery["hasPhoto"] is True,
                str(after_gallery),
            )
            check(
                "l'aperçu affiche bien l'image choisie",
                after_gallery["previewHasImg"] is True,
                str(after_gallery),
            )
            print()

            print("=== Les boutons restent disponibles après un premier choix (pour changer la photo) ===\n")
            still_available = page.evaluate(
                """
                () => ({
                    cameraButtonExists: Array.from(document.querySelectorAll('button')).some((b) => b.textContent.includes('Prendre une photo')),
                    galleryButtonExists: Array.from(document.querySelectorAll('button')).some((b) => b.textContent.includes('galerie')),
                })
                """
            )
            check(
                "les deux boutons restent visibles après avoir déjà choisi une photo",
                still_available["cameraButtonExists"] and still_available["galleryButtonExists"],
                str(still_available),
            )
            print()

            print("Erreurs JS sur tout le parcours:", "AUCUNE" if not errors else "; ".join(errors))
            if errors:
                all_ok = False
            browser.close()
        httpd.shutdown()
    finally:
        os.unlink(tmp_photo_path)

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "DES ÉCHECS SUBSISTENT")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
