#!/usr/bin/env python3
"""
Test permanent pour le recadrage manuel (v219) et la comparaison photo
source/résultat (v218), et les 5 correctifs qui les concernent (v221)
— voir TESTS_NON_REGRESSION.md, point 77 (défauts 6 à 9).

L'analyse OCR elle-même est simulée (window.runOcrOnImage remplacée)
plutôt que d'utiliser une vraie image et Tesseract : ce test vérifie
la mécanique du recadrage et de la comparaison (état conservé/vidé au
bon moment, coordonnées, accessibilité), pas la qualité de
reconnaissance de texte — déjà couverte par le corpus OCR permanent.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_photo_crop_and_comparison.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TINY_PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQ"
    "VR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


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


def make_big_image(page):
    return page.evaluate(
        """
        async () => {
            const c = document.createElement('canvas');
            c.width = 800; c.height = 800;
            const ctx = c.getContext('2d');
            ctx.fillStyle = '#4a7'; ctx.fillRect(0, 0, 800, 800);
            const blob = await new Promise((resolve) => c.toBlob(resolve, 'image/png'));
            const buf = await blob.arrayBuffer();
            return 'data:image/png;base64,' + btoa(String.fromCharCode(...new Uint8Array(buf)));
        }
        """
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
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")

        # ------------------------------------------------------------
        # Comparaison photo source / résultat : survit à un second rendu
        # ------------------------------------------------------------
        print("=== Comparaison photo : miniature survit à un changement de langue ===\n")
        page.evaluate(
            f"""
            () => {{
                state._importPrefill = {{ name: 'Recette importée', ingredients: [{{ name: 'Farine', unit: 'g', quantity: 200 }}] }};
                state._importSourcePhotos = ['{TINY_PNG}'];
                openRecipeForm(null);
            }}
            """
        )
        page.wait_for_timeout(300)
        before = page.evaluate("() => document.querySelectorAll('.section img, img').length")
        check("miniature présente juste après import", before > 0, f"{before} <img>")

        page.evaluate("() => { setLang('en'); render(); }")
        page.wait_for_timeout(200)
        after_lang_change = page.evaluate("() => document.querySelectorAll('.section img, img').length")
        check("miniature toujours présente après changement de langue", after_lang_change > 0, f"{after_lang_change} <img>")
        page.evaluate("() => { setLang('fr'); render(); }")
        page.wait_for_timeout(200)

        print("\n=== Comparaison photo : ne fuite pas vers un formulaire sans rapport ===\n")
        page.click('#recipe-form button:has-text("Annuler")')
        page.wait_for_timeout(200)
        page.evaluate("() => openRecipeForm(null)")
        page.wait_for_timeout(200)
        leaked = page.evaluate("() => document.querySelectorAll('.section img, img').length")
        check("aucune miniature dans un nouveau formulaire vierge", leaked == 0, f"{leaked} <img>")
        page.click('#recipe-form button:has-text("Annuler")')
        page.wait_for_timeout(200)
        print()

        # ------------------------------------------------------------
        # Recadrage : rôle dialogue, Échap, poignées au clavier
        # ------------------------------------------------------------
        print("=== Recadrage : accessibilité (rôle, Échap, clavier) ===\n")
        big_img = make_big_image(page)
        page.evaluate("(px) => openCropModal(px, () => {})", big_img)
        page.wait_for_timeout(300)
        role_info = page.evaluate(
            """
            () => {
                const overlay = document.querySelector('.modal-overlay');
                return overlay ? overlay.firstElementChild.getAttribute('role') : null;
            }
            """
        )
        check('rôle "dialog" présent sur la fenêtre de recadrage', role_info == "dialog", str(role_info))

        handle_info = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('div[role="button"]')).map((h) => h.getAttribute('tabindex'))
            """
        )
        check("les 4 poignées sont focalisables au clavier (tabindex=0)", handle_info == ["0", "0", "0", "0"], str(handle_info))

        before_count = page.evaluate("() => document.querySelectorAll('.modal-overlay').length")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        after_count = page.evaluate("() => document.querySelectorAll('.modal-overlay').length")
        check("Échap ferme la fenêtre de recadrage", after_count < before_count, f"avant={before_count} après={after_count}")
        print()

        print("=== Recadrage : les flèches du clavier déplacent le cadre ===\n")
        page.evaluate("(px) => openCropModal(px, () => {})", big_img)
        page.wait_for_timeout(300)
        page.evaluate('() => document.querySelector(\'div[role="button"]\').focus()')
        rect_before = page.evaluate(
            """
            () => {
                const r = Array.from(document.querySelectorAll('div')).find((d) => (d.getAttribute('style') || '').includes('9999px'));
                return r.getBoundingClientRect().left;
            }
            """
        )
        page.keyboard.press("ArrowRight")
        page.keyboard.press("ArrowRight")
        rect_after = page.evaluate(
            """
            () => {
                const r = Array.from(document.querySelectorAll('div')).find((d) => (d.getAttribute('style') || '').includes('9999px'));
                return r.getBoundingClientRect().left;
            }
            """
        )
        check("le cadre se déplace avec les flèches du clavier", rect_after != rect_before, f"avant={rect_before} après={rect_after}")
        page.click('button:has-text("Annuler")')
        page.wait_for_timeout(200)
        print()

        # ------------------------------------------------------------
        # Recadrage : suit un redimensionnement (rotation d'écran)
        # ------------------------------------------------------------
        print("=== Recadrage : le cadre suit une rotation d'écran simulée ===\n")
        page.evaluate("(px) => openCropModal(px, () => { window.__cropResult = true; })", big_img)
        page.wait_for_timeout(300)
        # Réduit le cadre à un quart de l'image (glisse le coin bas-droit vers le centre).
        handles = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('div[role="button"]')).map((h) => {
                const r = h.getBoundingClientRect();
                return { left: r.left, top: r.top, width: r.width, height: r.height };
            })
            """
        )
        img_box = page.evaluate(
            """
            () => {
                const img = document.querySelector('div[style*="flex:1"] img');
                const r = img.getBoundingClientRect();
                return { left: r.left, top: r.top, width: r.width, height: r.height };
            }
            """
        )
        br = handles[3]
        page.mouse.move(br["left"] + br["width"] / 2, br["top"] + br["height"] / 2)
        page.mouse.down()
        page.mouse.move(img_box["left"] + img_box["width"] / 2, img_box["top"] + img_box["height"] / 2, steps=5)
        page.mouse.up()
        page.wait_for_timeout(200)

        page.set_viewport_size({"width": 844, "height": 390})
        page.wait_for_timeout(300)
        page.click('button:has-text("Valider le recadrage")')
        page.wait_for_timeout(200)
        result_ok = page.evaluate("() => window.__cropResult === true")
        check("le recadrage se valide sans erreur après une rotation simulée", result_ok, str(result_ok))
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(200)
        print()

        # ------------------------------------------------------------
        # Import photo : original conservé, reset, revert en cas d'échec OCR
        # ------------------------------------------------------------
        print("=== Import photo : original conservé, revert si l'OCR échoue après recadrage ===\n")
        page.evaluate(
            """
            () => {
                let callCount = 0;
                window.runOcrOnImage = async () => {
                    callCount++;
                    if (callCount === 1) {
                        return { rawText: 'Quiche lorraine\\nIngrédients\\nFarine 200 g', layoutText: null, gridText: null, tableText: null, correctedImage: null };
                    }
                    throw new Error('Échec OCR simulé pour ce test');
                };
                state.screen = 'importPhoto';
                render();
            }
            """
        )
        page.wait_for_timeout(200)
        gallery_input = page.query_selector("input[type=file]:not([capture])")
        # Un vrai fichier est nécessaire pour déclencher le <input type=file> —
        # le contenu n'importe pas puisque runOcrOnImage est mocké ci-dessus ;
        # une icône du dépôt fait un fichier image valide bien plus petit et
        # rapide à traiter qu'une vraie photo.
        photo_path = os.path.join(PROJECT_ROOT, "icons", "icon-192.png")
        gallery_input.set_input_files(photo_path)
        page.wait_for_function(
            "() => state.multiPhotoImport.length && state.multiPhotoImport[0].status !== 'processing'",
            timeout=15000,
        )
        before_crop = page.evaluate(
            "() => ({ original: state.multiPhotoImport[0].originalThumbnail, thumbnail: state.multiPhotoImport[0].thumbnail, rawText: state.multiPhotoImport[0].rawText })"
        )
        check("originalThumbnail === thumbnail avant tout recadrage", before_crop["original"] == before_crop["thumbnail"])

        page.click('button:has-text("Recadrer")')
        page.wait_for_timeout(300)
        page.click('button:has-text("Valider le recadrage")')
        page.wait_for_function(
            "() => document.querySelector('.modal-overlay .btn-primary')", timeout=15000
        )
        page.wait_for_timeout(200)
        ok_btn = page.query_selector(".modal-overlay button.btn-primary")
        if ok_btn:
            ok_btn.click()
        page.wait_for_timeout(200)

        after_crop = page.evaluate(
            "() => ({ status: state.multiPhotoImport[0].status, rawText: state.multiPhotoImport[0].rawText, original: state.multiPhotoImport[0].originalThumbnail, thumbnail: state.multiPhotoImport[0].thumbnail })"
        )
        check(
            "après échec de la ré-analyse OCR, le résultat précédent est restauré (status='done')",
            after_crop["status"] == "done",
            str(after_crop["status"]),
        )
        check(
            "le texte reconnu précédent n'a pas été perdu",
            after_crop["rawText"] == before_crop["rawText"],
            str(after_crop["rawText"]),
        )
        check(
            "originalThumbnail toujours intacte après un recadrage",
            after_crop["original"] == before_crop["original"],
        )

        browser.close()

    httpd.shutdown()

    print("\nErreurs JS sur tout le parcours:", errors if errors else "AUCUNE")
    if errors:
        all_ok = False

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
