#!/usr/bin/env python3
"""Test permanent : second audit externe (autre IA), portant sur le mode
cuisine, la sauvegarde partagée ZIP, le cache du service worker et la
date de péremption — chaque point vérifié moi-même dans le code avant
correction (voir TESTS_NON_REGRESSION.md point 101).

Couvre :
- Mode cuisine : les quantités affichées reprennent bien le nombre de
  personnes choisi sur la fiche recette (auparavant toujours affichées
  pour 1 seule personne, quel que soit le nombre réellement
  sélectionné juste avant de cliquer sur "Mode cuisine").
- Import ZIP partagé : une entrée invalide n'applique plus RIEN (import
  tout-ou-rien plutôt que partiellement appliqué), un faux fichier ZIP
  (texte quelconque) est rejeté avec une erreur explicite au lieu d'un
  faux "0 élément importé", et le garde-manger conserve la date de
  péremption ET les articles de même nom mais d'unité différente (les
  deux étaient perdus par l'ancien format, indexé par nom seul).
- Service worker : une erreur HTTP (500) sur un fichier critique
  (app.js/i18n.js/index.html) n'empoisonne plus le cache — le cache
  existant reste servi tel quel plutôt que remplacé par la page
  d'erreur. Le nettoyage à l'activation ne supprime plus que les
  caches de CETTE application (préfixe dédié), jamais ceux d'une autre
  appli hébergée sur le même domaine.
- Date de péremption : le calcul du statut (expiré/bientôt) traite
  désormais la date comme une date calendaire locale, plutôt que de
  l'interpréter à tort comme minuit UTC (décalage d'un jour dans les
  fuseaux à l'ouest de l'UTC, ex. Amérique).
- Garde-manger : la quantité en mémoire n'est plus jamais augmentée si
  l'écriture réelle (storePut) échoue.
- Glisser-déposer : poignées désormais de vrais <button> focalisables,
  réordonnables aussi aux flèches haut/bas (pas seulement au
  glissement tactile/souris) — voir aussi test_drag_reorder.py pour le
  glissement lui-même.

Le test de "Remplacer tout" pour les recettes (bug le plus visible du
lot : les anciennes recettes restaient après un import en mode
remplacement) est couvert dans test_shared_backup.py, réécrit pour ne
plus vider lui-même la base avant le test — l'ancienne version du test
masquait justement ce bug en le faisant à sa place.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_external_audit_fixes_round2.py

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
        browser = p.chromium.launch()
        errors = []

        print("=== Mode cuisine : quantités recalculées selon le nombre de personnes ===\n")
        context1 = browser.new_context(viewport={"width": 390, "height": 844})
        page1 = context1.new_page()
        page1.on("pageerror", lambda exc: errors.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(1000)
        page1.evaluate("() => setLang('fr')")
        page1.evaluate(
            """
            async () => {
                const recipe = { id: 'ck-1', name: 'Test Cuisine', defaultPersons: 4, ingredients: [{ name: 'Farine', quantity: 100, unit: 'g' }] };
                await storePut('recipes', recipe);
                state.recipes = await storeAll('recipes');
                state.currentRecipeId = 'ck-1';
                state.viewPersons = 4;
                state.screen = 'recipe';
                render();
            }
            """
        )
        page1.wait_for_timeout(300)
        view_qty = page1.evaluate("() => document.querySelector('.ingredient-qty').textContent")
        check("La fiche recette affiche 400 g pour 4 personnes (base : 100 g/pers.)", view_qty.strip() == "400 g", view_qty)
        page1.click("text=Mode cuisine")
        page1.wait_for_timeout(300)
        cooking_qty = page1.evaluate("() => document.querySelector('.cooking-overlay .ingredient-qty').textContent")
        check("Le mode cuisine affiche AUSSI 400 g (pas 100 g comme avant le correctif)", cooking_qty.strip() == "400 g", cooking_qty)
        context1.close()

        print("\n=== Import ZIP atomique : une entrée invalide n'applique RIEN ===\n")
        context2 = browser.new_context()
        page2 = context2.new_page()
        page2.on("pageerror", lambda exc: errors.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(500)
        result2 = page2.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'keep-1', name: 'À conserver', category: 'Plat', ingredients: [] });
                const entries = [
                    { name: 'recipes.json', data: new TextEncoder().encode(JSON.stringify([
                        { id: 'valid-1', name: 'Ne doit jamais être importée', category: 'Plat', ingredients: [] },
                        null,
                    ])) },
                ];
                const zipBlob = await buildZipFile(entries);
                const zipFile = new File([zipBlob], 'bad.zip', { type: 'application/zip' });
                let errorCaught = null;
                try {
                    await restoreFromSharedZip(zipFile, false);
                } catch (e) {
                    errorCaught = String(e);
                }
                const recipesAfter = await storeAll('recipes');
                return { errorCaught, names: recipesAfter.map((r) => r.name) };
            }
            """
        )
        check("Une erreur est bien levée pour l'entrée invalide (null)", bool(result2["errorCaught"]), str(result2["errorCaught"]))
        check(
            "Aucune écriture partielle : 'À conserver' toujours présente, la recette valide jamais importée",
            result2["names"] == ["À conserver"],
            str(result2["names"]),
        )
        context2.close()

        print("\n=== Faux fichier ZIP (texte quelconque) rejeté avec une erreur explicite ===\n")
        context3 = browser.new_context()
        page3 = context3.new_page()
        page3.on("pageerror", lambda exc: errors.append(str(exc)))
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(500)
        result3 = page3.evaluate(
            """
            async () => {
                const fakeZip = new File([new TextEncoder().encode("ceci n'est pas un zip")], 'fake.zip', { type: 'application/zip' });
                let errorCaught = null;
                try {
                    await restoreFromSharedZip(fakeZip, false);
                } catch (e) {
                    errorCaught = String(e);
                }
                return { errorCaught };
            }
            """
        )
        check(
            "Une erreur explicite est levée (plus un faux rapport '0 élément importé')",
            bool(result3["errorCaught"]),
            str(result3["errorCaught"]),
        )
        context3.close()

        print("\n=== ZIP garde-manger : date de péremption conservée + articles de même nom mais unité différente ===\n")
        context4 = browser.new_context()
        page4 = context4.new_page()
        page4.on("pageerror", lambda exc: errors.append(str(exc)))
        page4.goto(base_url, timeout=8000)
        page4.wait_for_timeout(500)
        result4 = page4.evaluate(
            """
            async () => {
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'p1', name: 'Farine', quantity: 1, unit: 'kg', expirationDate: '2027-03-15' });
                await storePut('pantry', { id: 'p2', name: 'Farine', quantity: 500, unit: 'g', expirationDate: '2026-11-01' });
                const zipBlob = await buildSharedBackupZip();
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                const zipFile = new File([zipBlob], 'pantry.zip', { type: 'application/zip' });
                await restoreFromSharedZip(zipFile, false);
                const pantryAfter = await storeAll('pantry');
                return pantryAfter.map((p) => ({ name: p.name, unit: p.unit, quantity: p.quantity, expirationDate: p.expirationDate }));
            }
            """
        )
        check(
            "Les 2 articles 'Farine' (kg et g) survivent tous les deux à l'aller-retour ZIP",
            len(result4) == 2,
            str(result4),
        )
        check(
            "La date de péremption de chaque article est conservée (plus jamais perdue)",
            all(p.get("expirationDate") for p in result4),
            str(result4),
        )
        context4.close()

        print("\n=== Service worker : une erreur HTTP (500) n'empoisonne pas le cache ===\n")
        context5 = browser.new_context()
        page5 = context5.new_page()
        page5.on("pageerror", lambda exc: errors.append(str(exc)))
        page5.goto(base_url, timeout=8000)
        sw_ready = False
        for _ in range(20):
            sw_ready = page5.evaluate("async () => { const r = await navigator.serviceWorker.ready; return !!r.active; }")
            if sw_ready:
                break
            page5.wait_for_timeout(300)
        check("Service worker actif avant le test", sw_ready)
        original_app_js = page5.evaluate(
            """
            async () => {
                const names = await caches.keys();
                for (const name of names) {
                    const c = await caches.open(name);
                    const m = await c.match('./app.js');
                    if (m) return await m.text();
                }
                return null;
            }
            """
        )

        def fail_app_js(route):
            route.fulfill(status=500, body="Erreur serveur interne (simulation)")

        page5.route("**/app.js", fail_app_js)
        result5 = page5.evaluate(
            "async () => { const res = await fetch('./app.js'); return { status: res.status, ok: res.ok, body: (await res.text()).slice(0, 30) }; }"
        )
        check(
            "Pendant la panne simulée, le SW retombe sur le cache valide (pas la page d'erreur 500)",
            result5["ok"] and "Erreur serveur interne" not in result5["body"],
            str(result5),
        )
        cached_after = page5.evaluate(
            """
            async () => {
                const names = await caches.keys();
                for (const name of names) {
                    const c = await caches.open(name);
                    const m = await c.match('./app.js');
                    if (m) return await m.text();
                }
                return null;
            }
            """
        )
        check("Le cache reste inchangé après la panne (jamais remplacé par l'erreur)", cached_after == original_app_js)
        page5.unroute("**/app.js", fail_app_js)
        context5.close()

        print("\n=== Service worker : le nettoyage à l'activation ne touche pas les caches d'autres apps ===\n")
        context6 = browser.new_context()
        page6 = context6.new_page()
        page6.on("pageerror", lambda exc: errors.append(str(exc)))
        page6.goto(base_url, timeout=8000)
        for _ in range(20):
            if page6.evaluate("async () => { const r = await navigator.serviceWorker.ready; return !!r.active; }"):
                break
            page6.wait_for_timeout(300)
        page6.evaluate("async () => { const c = await caches.open('another-app-cache'); await c.put('/foo', new Response('bar')); }")
        page6.evaluate("async () => { const reg = await navigator.serviceWorker.getRegistration(); await reg.unregister(); }")
        page6.reload()
        for _ in range(20):
            if page6.evaluate("async () => { const r = await navigator.serviceWorker.ready; return !!r.active; }"):
                break
            page6.wait_for_timeout(300)
        page6.wait_for_timeout(500)
        keys = page6.evaluate("() => caches.keys()")
        check("Le cache d'une autre application ('another-app-cache') survit à la réactivation du SW", "another-app-cache" in keys, str(keys))
        context6.close()

        print("\n=== Date de péremption : traitée comme une date calendaire locale (pas minuit UTC) ===\n")
        context7 = browser.new_context(timezone_id="America/New_York")
        page7 = context7.new_page()
        page7.on("pageerror", lambda exc: errors.append(str(exc)))
        page7.goto(base_url, timeout=8000)
        page7.wait_for_timeout(1000)
        page7.evaluate("() => setLang('fr')")
        import datetime
        today_iso = datetime.date.today().isoformat()
        status7 = page7.evaluate(f"() => getPantryExpirationStatus({{ expirationDate: '{today_iso}' }})")
        check(
            "Un article expirant aujourd'hui n'est pas déjà 'expired' dans le fuseau America/New_York",
            status7 != "expired",
            f"statut={status7}",
        )
        context7.close()

        print("\n=== Garde-manger : le stock en mémoire n'augmente plus si l'écriture échoue ===\n")
        context8 = browser.new_context()
        page8 = context8.new_page()
        page8.on("pageerror", lambda exc: errors.append(str(exc)))
        page8.goto(base_url, timeout=8000)
        page8.wait_for_timeout(1000)
        result8 = page8.evaluate(
            """
            async () => {
                await storePut('pantry', { id: 'stock-1', name: 'Riz', quantity: 2, unit: 'kg' });
                state.pantry = await storeAll('pantry');
                const originalStorePut = window.storePut;
                window.storePut = () => Promise.reject(new Error('simulated write failure'));
                let errorCaught = null;
                try {
                    await addOrIncrementPantryItem('Riz', 'kg');
                } catch (e) {
                    errorCaught = String(e);
                }
                window.storePut = originalStorePut;
                const memoryItem = state.pantry.find((i) => i.id === 'stock-1');
                const dbItem = (await storeAll('pantry')).find((i) => i.id === 'stock-1');
                return { errorCaught, memoryQty: memoryItem.quantity, dbQty: dbItem.quantity };
            }
            """
        )
        check("L'échec d'écriture se propage bien (pas avalé silencieusement)", bool(result8["errorCaught"]), str(result8))
        check(
            "La quantité en mémoire ET en base reste à 2 (pas augmentée malgré l'échec)",
            result8["memoryQty"] == 2 and result8["dbQty"] == 2,
            str(result8),
        )
        context8.close()

        print("\n=== Glisser-déposer : poignée focalisable, réordonnable au clavier (flèches) ===\n")
        context9 = browser.new_context(viewport={"width": 390, "height": 844})
        page9 = context9.new_page()
        page9.on("pageerror", lambda exc: errors.append(str(exc)))
        page9.goto(base_url, timeout=8000)
        page9.wait_for_timeout(1000)
        page9.evaluate("() => setLang('fr')")
        page9.evaluate(
            """
            async () => {
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                const items = [
                    { id: 'k-a', name: 'Alpha', quantity: 1, unit: 'pièce' },
                    { id: 'k-b', name: 'Beta', quantity: 1, unit: 'pièce' },
                ];
                for (const it of items) await storePut('pantry', it);
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                render();
            }
            """
        )
        page9.wait_for_timeout(200)
        page9.select_option("#pantry-sort-select", "manual")
        page9.wait_for_timeout(200)
        tag = page9.evaluate("() => document.querySelector('.drag-handle').tagName")
        check("La poignée de glisser-déposer est un vrai <button> focalisable (pas un <span>)", tag == "BUTTON", tag)
        page9.locator(".shopping-item .drag-handle").first.focus()
        order_before = page9.evaluate("() => Array.from(document.querySelectorAll('.shopping-item .label')).map((e) => e.textContent)")
        page9.keyboard.press("ArrowDown")
        page9.wait_for_timeout(200)
        order_after = page9.evaluate("() => Array.from(document.querySelectorAll('.shopping-item .label')).map((e) => e.textContent)")
        check(
            "La flèche bas déplace bien la ligne d'une position (réordonnancement clavier fonctionnel)",
            order_after == list(reversed(order_before)),
            f"avant={order_before} après={order_after}",
        )
        context9.close()

        print("\n=== Libellé des valeurs nutritionnelles : précise 'par personne' ===\n")
        context10 = browser.new_context()
        page10 = context10.new_page()
        page10.on("pageerror", lambda exc: errors.append(str(exc)))
        page10.goto(base_url, timeout=8000)
        page10.wait_for_timeout(1000)
        page10.evaluate("() => setLang('fr')")
        nutrition_label = page10.evaluate("() => t('recipe_nutrition')")
        check("Le libellé mentionne bien 'par personne'", "par personne" in nutrition_label, nutrition_label)
        context10.close()

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
