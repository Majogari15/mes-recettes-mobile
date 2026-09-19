"""
Vérifie les 3 corrections apportées après relecture, par une seconde IA,
du compte rendu du point 115 (voir TESTS_NON_REGRESSION.md point 117) :

1. Le bandeau "Conserver une copie dans le cloud" de l'écran Sauvegarde
   était affiché SANS condition et renvoyait vers le bouton "Partager
   la sauvegarde" — lui-même affiché uniquement si le navigateur
   supporte le partage de fichiers (Web Share API). Sur un navigateur
   sans ce support (Firefox Android, plusieurs versions de Safari, tout
   navigateur de bureau), l'instruction renvoyait vers un bouton absent
   de l'écran. Un texte de repli est maintenant utilisé dans ce cas.
2. Le convertisseur d'unités ne signalait nulle part à l'écran que
   convertir entre masse et volume suppose une densité proche de celle
   de l'eau (1 mL ≈ 1 g) — imprécis pour un ingrédient plus léger
   (farine) ou plus lourd (miel). Un avertissement contextuel est
   maintenant affiché, uniquement quand la conversion traverse les deux
   domaines.
3. Correction de documentation (pas de code) : le point 115 généralisait
   à tort le bug critique de perte de données (ZIP partagé, mode
   "remplacer") aux 3 entrepôts concernés, alors que le garde-manger
   génère toujours un identifiant neuf à l'import et ne pouvait donc pas
   reproduire cette collision d'id précise — non testable directement,
   vérifié par relecture du texte corrigé dans ce script (recherche
   d'une chaîne).

Couvre aussi la suggestion de test de la seconde IA restée non testée :
un échec d'écriture pendant addRecipeToShopping (pas seulement la
version "silencieuse") ne doit jamais laisser de réservation de
garde-manger orpheline ni d'article de courses fictif.
"""
import http.server
import json
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

        print("=== 1. Ecran Sauvegarde sans support de partage de fichiers ===")
        r1 = page.evaluate(
            """
            () => {
                const original = navigator.canShare;
                Object.defineProperty(navigator, 'canShare', { value: undefined, configurable: true });
                state.screen = 'backup';
                render();
                const text = document.body.textContent;
                const hasShareBtn = !!document.getElementById('share-btn');
                Object.defineProperty(navigator, 'canShare', { value: original, configurable: true });
                return { mentionsShareButton: text.includes('Partager la sauvegarde'), hasShareBtn, fallbackShown: text.includes('ouvrez ce dossier') };
            }
            """
        )
        check(
            "aucune mention du bouton absent, texte de repli affiché",
            not r1["mentionsShareButton"] and not r1["hasShareBtn"] and r1["fallbackShown"],
            json.dumps(r1, ensure_ascii=False),
        )

        print("\n=== 2. Ecran Sauvegarde avec support de partage de fichiers ===")
        r2 = page.evaluate(
            """
            () => {
                const original = navigator.canShare;
                Object.defineProperty(navigator, 'canShare', { value: () => true, configurable: true });
                state.screen = 'backup';
                render();
                const text = document.body.textContent;
                const hasShareBtn = !!document.getElementById('share-btn');
                Object.defineProperty(navigator, 'canShare', { value: original, configurable: true });
                return { mentionsShareButton: text.includes('Partager la sauvegarde'), hasShareBtn };
            }
            """
        )
        check(
            "bouton présent et référencé, comportement inchangé",
            r2["mentionsShareButton"] and r2["hasShareBtn"],
            json.dumps(r2, ensure_ascii=False),
        )

        print("\n=== 3. Convertisseur d'unités : avertissement masse<->volume uniquement ===")
        r3 = page.evaluate(
            """
            () => {
                state.screen = 'unitConverter';
                render();
                const fromSel = document.getElementById('conv-from');
                const toSel = document.getElementById('conv-to');
                fromSel.value = 'unitconv_gram';
                toSel.value = 'unitconv_liter';
                document.querySelector('.btn-primary').click();
                const warnMassVolume = document.body.textContent.includes('densité');
                fromSel.value = 'unitconv_gram';
                toSel.value = 'unitconv_kilogram';
                document.querySelector('.btn-primary').click();
                const warnMassMass = document.body.textContent.includes('densité');
                return { warnMassVolume, warnMassMass };
            }
            """
        )
        check(
            "avertissement affiché masse<->volume, absent masse<->masse",
            r3["warnMassVolume"] is True and r3["warnMassMass"] is False,
            json.dumps(r3),
        )

        print("\n=== 4. addRecipeToShopping : échec d'écriture, aucune réservation orpheline ===")
        r4 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'p1', name: 'Riz', quantity: 100, unit: 'g' });
                state.pantry = await storeAll('pantry');
                state.shopping = [];
                state.pantryClaimedThisSession = [];

                // addRecipeToShopping écrit désormais l'article ET sa
                // réservation dans LA MÊME transaction
                // (storeWriteManyAcrossStores, voir
                // TESTS_NON_REGRESSION.md point 118) et non plus via
                // storePut/commitPantryClaim séparément — c'est donc ce
                // point d'entrée qu'il faut simuler en échec.
                const realWriteMany = window.storeWriteManyAcrossStores;
                window.storeWriteManyAcrossStores = () => Promise.reject(new Error('quota dépassé (simulé)'));
                const realCustomConfirm = window.customConfirm;
                window.customConfirm = () => Promise.resolve(true);
                let threw = false;
                try {
                    await addRecipeToShopping({ ingredients: [{ name: 'Riz', quantity: 500, unit: 'g' }] }, 1);
                } catch (e) {
                    threw = true;
                }
                window.storeWriteManyAcrossStores = realWriteMany;
                window.customConfirm = realCustomConfirm;
                return {
                    threw,
                    shoppingCount: state.shopping.length,
                    dbShoppingCount: (await storeAll('shopping')).length,
                    claimsCount: state.pantryClaimedThisSession.length,
                };
            }
            """
        )
        check(
            "l'échec d'écriture stoppe tout, aucun article ni réservation fictifs",
            r4["threw"] is True and r4["shoppingCount"] == 0 and r4["dbShoppingCount"] == 0 and r4["claimsCount"] == 0,
            json.dumps(r4),
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
