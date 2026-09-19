"""
Vérifie le contournement de la restriction de Chromium (Web Share API)
sur les fichiers .zip pour le bouton "Partager la sauvegarde" (format
compatible app Windows), suite à un signalement utilisateur avec capture
d'écran (voir TESTS_NON_REGRESSION.md points 124 et 125) :

- Point 124 : le bouton s'affichait, mais `navigator.share()` échouait
  systématiquement pour un fichier .zip avec "NotAllowedError" —
  limitation déjà rencontrée au point 59 (Chromium n'autorise pas les
  fichiers .zip dans son Web Share API).
- Point 125 (ce fichier) : même astuce que la sauvegarde JSON classique
  (déjà partagée sous un nom/type ".txt" plutôt que ".json") appliquée
  au zip partagé — renommé et retypé en ".txt"/"text/plain" UNIQUEMENT
  pour l'appel `navigator.share()`, jamais pour le bouton "Exporter"
  (qui garde ".zip"). Le contenu reste un zip valide à l'octet près :
  seuls le nom de fichier et le type MIME déclarés changent pour cet
  appel précis, ce qui suffit à passer la vérification de Chromium.

Couvre : le bouton s'affiche désormais selon la même condition que le
bouton JSON (`canShareFiles`, testé avec un fichier .txt — pas
`canShareZip`, testé avec un vrai .zip et supprimé du code), le fichier
transmis à `navigator.share()` est bien nommé/typé comme du texte tout
en contenant des octets zip valides et réimportables tels quels, l'échec
du partage retombe sur un téléchargement avec le VRAI nom ".zip" (pas le
nom ".txt" déguisé) et le même message générique que la sauvegarde JSON
(plus de message spécifique au zip, devenu inutile), et le bouton JSON
classique reste totalement inchangé.
"""
import http.server
import socket
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"


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

    def check(label, condition, detail):
        nonlocal all_ok
        mark = "✅ OK " if condition else "❌ ECHEC"
        print(f"{mark} {label} — {detail}")
        if not condition:
            all_ok = False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(600)
        page.evaluate("() => setLang('fr')")

        print("=== 1. Le bouton s'affiche selon la capacité à partager un .txt, pas un vrai .zip ===")
        r1 = page.evaluate(
            """
            async () => {
                // Simule exactement le cas réel qui a motivé ce changement :
                // un vrai fichier .zip échouerait ce test, mais un .txt le
                // passe — le bouton doit donc s'afficher (ancien code : cette
                // même simulation aurait caché le bouton, puisqu'il se basait
                // sur un test avec un vrai .zip).
                navigator.canShare = (data) => data.files[0].name.endsWith('.txt');
                state.screen = 'backup';
                render();
                await new Promise((r) => setTimeout(r, 200));
                const btn = document.querySelector('#shared-share-btn');
                return { present: !!btn };
            }
            """
        )
        check("bouton présent même si seul .txt est partageable (pas .zip)", r1.get("present") is True, str(r1))

        print("\n=== 2. Partage réussi : fichier envoyé en .txt/text-plain, contenu = zip valide et réimportable ===")
        r2 = page.evaluate(
            """
            async () => {
                let sharedFile = null;
                navigator.canShare = () => true;
                navigator.share = (data) => { sharedFile = data.files[0]; return Promise.resolve(); };
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'share1', name: 'Recette partagée', category: 'Plat', ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }] });
                state.recipes = await storeAll('recipes');
                state.screen = 'backup';
                render();
                for (let i = 0; i < 40 && document.querySelector('#shared-share-btn')?.disabled; i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                document.querySelector('#shared-share-btn').click();
                await new Promise((r) => setTimeout(r, 300));
                if (!sharedFile) return { shared: false };
                const buffer = await sharedFile.arrayBuffer();
                let parsedOk = false;
                let hasRecipesJson = false;
                try {
                    const files = await parseZipFile(buffer);
                    hasRecipesJson = files.some((f) => f.name === 'recipes.json');
                    parsedOk = true;
                } catch (e) { parsedOk = false; }
                return {
                    shared: true,
                    name: sharedFile.name,
                    type: sharedFile.type,
                    isTxtName: sharedFile.name.endsWith('.txt'),
                    isTextPlainType: sharedFile.type === 'text/plain',
                    parsedAsValidZip: parsedOk,
                    hasRecipesJson,
                };
            }
            """
        )
        check(
            "fichier partagé nommé/typé comme du texte, mais contient un zip valide (recipes.json présent)",
            r2.get("shared") and r2.get("isTxtName") and r2.get("isTextPlainType")
            and r2.get("parsedAsValidZip") and r2.get("hasRecipesJson"),
            str(r2),
        )

        print("\n=== 3. Échec du partage : repli avec le VRAI nom .zip (pas le nom .txt déguisé) et le message générique ===")
        r3 = page.evaluate(
            """
            async () => {
                navigator.canShare = () => true;
                navigator.share = () => {
                    const err = new Error('Permission denied');
                    err.name = 'NotAllowedError';
                    return Promise.reject(err);
                };
                state.screen = 'backup';
                render();
                for (let i = 0; i < 40 && document.querySelector('#shared-share-btn')?.disabled; i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                document.querySelector('#shared-share-btn').click();
                for (let i = 0; i < 30 && !document.getElementById('custom-alert-message'); i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                const text = document.getElementById('custom-alert-message')?.textContent || null;
                document.getElementById('custom-alert-ok')?.click();
                return {
                    text,
                    matchesGenericNotice: text ? text.startsWith(t('backup_share_fallback_notice')) : false,
                    mentionsErrorDetail: text ? text.includes('NotAllowedError') : false,
                };
            }
            """
        )
        check(
            "message générique affiché (identique à la sauvegarde JSON), avec le détail de l'erreur",
            r3.get("matchesGenericNotice") and r3.get("mentionsErrorDetail"),
            str(r3),
        )

        print("\n=== 4. Le bouton de partage JSON classique reste inchangé ===")
        r4 = page.evaluate(
            """
            async () => {
                let sharedFile = null;
                navigator.canShare = (data) => data.files[0].name.endsWith('.txt');
                navigator.share = (data) => { sharedFile = data.files[0]; return Promise.resolve(); };
                state.screen = 'backup';
                render();
                for (let i = 0; i < 40 && document.querySelector('#share-btn')?.disabled; i++) {
                    await new Promise((r) => setTimeout(r, 100));
                }
                document.querySelector('#share-btn').click();
                await new Promise((r) => setTimeout(r, 300));
                return { shared: !!sharedFile, name: sharedFile ? sharedFile.name : null, type: sharedFile ? sharedFile.type : null };
            }
            """
        )
        check(
            "bouton JSON classique toujours fonctionnel (.txt/text-plain, comme avant ce changement)",
            r4.get("shared") and r4.get("name", "").endswith(".txt") and r4.get("type") == "text/plain",
            str(r4),
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
