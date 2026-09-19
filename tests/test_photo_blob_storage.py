"""
Vérifie le passage du stockage des photos (recette + journal de cuisine) de
chaînes base64 ("data:image/...;base64,...") à des Blob natifs dans
IndexedDB, demandé explicitement par l'utilisateur ("tu peux lancé le
chantier pour les photo en blob") suite à un audit externe. Le format
EXTERNE (sauvegarde .json, ZIP partagé mobile<->bureau) reste inchangé —
seule la représentation INTERNE change, pour gagner ~33% de place locale
(l'encodage base64 alourdit d'environ un tiers) : le JSON ne pouvant pas
représenter du binaire, l'export réencode toujours en base64 aux
frontières.

Couvre : migration au démarrage, capture (formulaire + journal de
cuisine), affichage (src en blob:, jamais data:), sauvegarde JSON
complète (aller-retour Blob<->base64), ZIP partagé (photo de couverture
externalisée en octets, journal de cuisine toujours en base64 dans le
JSON), export PDF, et le cycle de vie des URL d'objet (révocation au
rendu suivant, pas de fuite mémoire).

Note technique : fetch() d'une URI "data:" est bloqué par la CSP de
l'application (connect-src n'autorise pas "data:", volontairement —
seul img-src l'autorise, pour les <img src="data:...">). Ce test utilise
donc dataUrlToBlob() — la fonction de l'application elle-même, déjà
couverte par ailleurs — pour construire les Blob de test, jamais fetch().
"""
import http.server
import json
import socket
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

# petit JPEG 1x1 valide en base64
TINY_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAj/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
)
TINY_JPEG_DATA_URL = "data:image/jpeg;base64," + TINY_JPEG_B64


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_local_server(port):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=PROJECT_ROOT, **k)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"
    all_ok = True

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(600)
        page.evaluate("() => setLang('fr')")

        def check(label, condition, detail):
            nonlocal all_ok
            mark = "✅ OK " if condition else "❌ ECHEC"
            print(f"{mark} {label} — {detail}")
            if not condition:
                all_ok = False

        print("=== 1. Migration au démarrage : recipe.photo + cookLog[].photo base64 -> Blob ===")
        r1 = page.evaluate(
            """
            async (dataUrl) => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                const legacy = {
                    id: 'legacy1', name: 'Ancienne recette', category: 'Plat', ingredients: [],
                    photo: dataUrl,
                    cookLog: [{ date: new Date().toISOString(), note: 'test', photo: dataUrl }],
                };
                await storePut('recipes', legacy);
                state.recipes = await storeAll('recipes');
                await migratePhotosToBlob();
                const after = (await storeAll('recipes')).find((r) => r.id === 'legacy1');
                return {
                    photoIsBlob: after.photo instanceof Blob,
                    photoType: after.photo ? after.photo.type : null,
                    cookLogPhotoIsBlob: after.cookLog[0].photo instanceof Blob,
                };
            }
            """,
            TINY_JPEG_DATA_URL,
        )
        check(
            "recipe.photo et cookLog[].photo migrés en Blob (idempotent au prochain démarrage)",
            r1["photoIsBlob"] and r1["photoType"] == "image/jpeg" and r1["cookLogPhotoIsBlob"],
            json.dumps(r1),
        )

        print("\n=== 2. Capture (formulaire recette) : canvas.toBlob -> state.formPhoto est un Blob ===")
        r2 = page.evaluate(
            """
            async (dataUrl) => {
                const blob = dataUrlToBlob(dataUrl);
                const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
                state.screen = 'form';
                state.editingRecipeId = null;
                state.formIngredients = [{ name: '', quantity: '', unit: 'pièce' }];
                state.formAllergens = [];
                state.formPhoto = null;
                render();
                await new Promise((r) => setTimeout(r, 100));
                const cameraInput = document.querySelector('input[type=file][capture]');
                const dt = new DataTransfer();
                dt.items.add(file);
                cameraInput.files = dt.files;
                cameraInput.dispatchEvent(new Event('change'));
                await new Promise((r) => setTimeout(r, 300));
                return { isBlob: state.formPhoto instanceof Blob, type: state.formPhoto ? state.formPhoto.type : null };
            }
            """,
            TINY_JPEG_DATA_URL,
        )
        check(
            "state.formPhoto devient un Blob après capture (canvas.toBlob)",
            r2["isBlob"] and r2["type"] == "image/jpeg",
            json.dumps(r2),
        )

        print("\n=== 3. Affichage : <img src> commence par blob: (jamais data:) ===")
        r3 = page.evaluate(
            """
            async (dataUrl) => {
                const blob = dataUrlToBlob(dataUrl);
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'p1', name: 'Photo recette', category: 'Plat', ingredients: [], photo: blob });
                state.recipes = await storeAll('recipes');
                state.screen = 'recipes';
                render();
                await new Promise((r) => setTimeout(r, 100));
                const img = document.querySelector('.recipe-thumb img');
                return { src: img ? img.src : null };
            }
            """,
            TINY_JPEG_DATA_URL,
        )
        check("src commence par blob:", bool(r3["src"]) and r3["src"].startswith("blob:"), json.dumps(r3))

        print("\n=== 4. Sauvegarde JSON complète : export produit du base64, ré-import reconstruit un Blob ===")
        r4 = page.evaluate(
            """
            async (dataUrl) => {
                const blob = dataUrlToBlob(dataUrl);
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', {
                    id: 'bkp1', name: 'Recette sauvegarde', category: 'Plat', ingredients: [],
                    photo: blob, cookLog: [{ date: new Date().toISOString(), note: '', photo: blob }],
                });
                state.recipes = await storeAll('recipes');
                const data = await buildBackupData();
                const exportedPhotoIsString = typeof data.recipes[0].photo === 'string' && data.recipes[0].photo.startsWith('data:image/jpeg;base64,');
                const exportedCookLogPhotoIsString = typeof data.recipes[0].cookLog[0].photo === 'string';
                // Ronde complète : JSON.stringify + JSON.parse (comme un vrai export/import de fichier)
                const roundTripped = JSON.parse(JSON.stringify(data));
                const report = { structuralFixes: 0, numbersFixed: 0, photosRemoved: 0 };
                const sanitized = sanitizeBackupItem(roundTripped.recipes[0], 'recipes', report);
                return {
                    exportedPhotoIsString,
                    exportedCookLogPhotoIsString,
                    reimportedPhotoIsBlob: sanitized.photo instanceof Blob,
                    reimportedCookLogPhotoIsBlob: sanitized.cookLog[0].photo instanceof Blob,
                    photosRemoved: report.photosRemoved,
                };
            }
            """,
            TINY_JPEG_DATA_URL,
        )
        check(
            "export en base64 (compatible JSON), ré-import en Blob, aucune photo perdue",
            r4["exportedPhotoIsString"] and r4["exportedCookLogPhotoIsString"]
            and r4["reimportedPhotoIsBlob"] and r4["reimportedCookLogPhotoIsBlob"] and r4["photosRemoved"] == 0,
            json.dumps(r4),
        )

        print("\n=== 5. ZIP partagé (mobile<->bureau) : photo de couverture externalisée en octets, journal de cuisine toujours en base64 dans le JSON ===")
        r5 = page.evaluate(
            """
            async (dataUrl) => {
                const blob = dataUrlToBlob(dataUrl);
                const recipe = {
                    id: 'zip1', name: 'Recette ZIP', category: 'Plat', ingredients: [],
                    photo: blob, cookLog: [{ date: '2026-01-01T00:00:00.000Z', note: '', photo: blob }],
                };
                const { json, photoFiles } = await recipeToSharedFormat(recipe);
                const hasPhotoFile = photoFiles.length === 1 && photoFiles[0].filename === 'zip1.jpg' && photoFiles[0].bytes.length > 0;
                const cookLogPhotoIsBase64 = typeof json.cook_log_full[0].photo === 'string' && json.cook_log_full[0].photo.startsWith('data:image/jpeg;base64,');
                const imageBytesByFilename = new Map(photoFiles.map((pf) => [pf.filename, pf.bytes]));
                const back = recipeFromSharedFormat(json, imageBytesByFilename);
                return {
                    hasPhotoFile,
                    cookLogPhotoIsBase64,
                    reconstructedPhotoIsBlob: back.photo instanceof Blob,
                    reconstructedPhotoType: back.photo ? back.photo.type : null,
                };
            }
            """,
            TINY_JPEG_DATA_URL,
        )
        check(
            "format ZIP externe inchangé (octets pour la couverture, base64 pour le journal), reconstruction en Blob",
            r5["hasPhotoFile"] and r5["cookLogPhotoIsBase64"] and r5["reconstructedPhotoIsBlob"] and r5["reconstructedPhotoType"] == "image/jpeg",
            json.dumps(r5),
        )

        print("\n=== 6. Export PDF avec une photo Blob ne plante pas ===")
        r6 = page.evaluate(
            """
            async (dataUrl) => {
                const blob = dataUrlToBlob(dataUrl);
                const recipe = { id: 'pdf1', name: 'Recette PDF', category: 'Plat', ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }], photo: blob, defaultPersons: 2 };
                const realConfirm = window.customConfirm;
                window.customConfirm = () => Promise.resolve(true);
                let threw = false;
                let errMsg = null;
                try {
                    await exportRecipePdf(recipe, 2);
                } catch (e) { threw = true; errMsg = e.message; }
                window.customConfirm = realConfirm;
                return { threw, errMsg };
            }
            """,
            TINY_JPEG_DATA_URL,
        )
        check("exportRecipePdf ne plante pas avec une photo Blob", r6["threw"] is False, json.dumps(r6))

        print("\n=== 7. Cycle de vie des URL d'objet : révoquées au rendu suivant, jamais de fuite ===")
        r7 = page.evaluate(
            """
            async (dataUrl) => {
                const blob = dataUrlToBlob(dataUrl);
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'life1', name: 'Cycle', category: 'Plat', ingredients: [], photo: blob });
                state.recipes = await storeAll('recipes');
                state.screen = 'recipes';
                render();
                await new Promise((r) => setTimeout(r, 50));
                const firstSrc = document.querySelector('.recipe-thumb img').src;
                let revokedFirst = false;
                const realRevoke = URL.revokeObjectURL;
                URL.revokeObjectURL = (u) => { if (u === firstSrc) revokedFirst = true; return realRevoke.call(URL, u); };
                render();
                await new Promise((r) => setTimeout(r, 50));
                URL.revokeObjectURL = realRevoke;
                const secondSrc = document.querySelector('.recipe-thumb img').src;
                return { firstSrc, secondSrc, revokedFirst, different: firstSrc !== secondSrc };
            }
            """,
            TINY_JPEG_DATA_URL,
        )
        check(
            "l'URL d'objet du rendu précédent est révoquée au rendu suivant",
            r7["revokedFirst"] and r7["different"],
            json.dumps(r7),
        )

        check("Aucune erreur JS pendant tout le parcours", not errors, str(errors))

        print("\n=== Résumé ===")
        print("TOUT CORRECT" if all_ok else "AU MOINS UN ECHEC")
        browser.close()
    httpd.shutdown()
    return all_ok


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
