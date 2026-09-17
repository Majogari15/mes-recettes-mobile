#!/usr/bin/env python3
"""Test permanent pour les défauts de robustesse trouvés lors de l'audit
complet (voir TESTS_NON_REGRESSION.md point 82) :

1. `init()` n'était protégé par aucun `try/catch` : un échec d'accès à
   IndexedDB au démarrage (navigation privée stricte, quota dépassé...)
   laissait l'écran totalement blanc, sans aucun texte ni bouton.
2. `moveRecipeToTrash`/`restoreRecipeFromTrash` écrivaient dans deux
   entrepôts séparés (deux transactions distinctes, sans lien) : un échec
   entre les deux pouvait dupliquer une recette dans "recipes" ET
   "trash", ou la faire disparaître des deux.
3. `renameIngredientName`/`mergeIngredientNames` propageaient un
   renommage à travers jusqu'à 6 entrepôts avec des écritures
   séquentielles non transactionnelles, et mutaient l'état en mémoire
   avant confirmation de la persistance.
4. `saveRecipeForm` n'avait aucun `try/catch` autour de son écriture :
   un échec laissait croire à tort que la recette avait été enregistrée.
5. `storePut`/`storeDelete` (les fonctions de base utilisées à des
   dizaines d'endroits dans tout le fichier) n'écoutaient que
   `oncomplete`/`onerror` — sans `onabort`, une transaction abandonnée
   après le succès de sa seule requête laissait leur promesse bloquée
   pour toujours (voir TESTS_NON_REGRESSION.md point 85).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_data_integrity.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading
import urllib.request

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

        # === 1. init() : un IndexedDB indisponible affiche un écran de
        # secours lisible au lieu d'un écran blanc. ===
        print("=== init() : écran de secours si IndexedDB est indisponible au démarrage ===\n")
        page = browser.new_page(viewport={"width": 390, "height": 844})

        def handle_route(route):
            if route.request.url.endswith("/app.js"):
                body = route.fetch().text()
                patched = body.replace(
                    "function openDB() {",
                    "function openDB() { return Promise.reject(new Error('IndexedDB indisponible (simulation)')); }\n"
                    "function _openDB_original() {",
                    1,
                )
                route.fulfill(body=patched, content_type="application/javascript")
            else:
                route.continue_()

        page.route("**/app.js", handle_route)
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1500)
        startup_state = page.evaluate(
            """
            () => ({
                bodyText: document.body.innerText.trim(),
                hasReloadButton: !!document.getElementById('startup-error-reload'),
                screenExists: !!document.getElementById('screen'),
            })
            """
        )
        check(
            "un message d'erreur lisible est affiché (pas un écran blanc)",
            len(startup_state["bodyText"]) > 20,
            str(startup_state),
        )
        check(
            "un bouton pour réessayer est présent",
            startup_state["hasReloadButton"] is True,
            str(startup_state),
        )
        page.close()
        print()

        # === Session normale pour les cas suivants ===
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)

        print("=== moveRecipeToTrash / restoreRecipeFromTrash : une seule transaction atomique ===\n")
        result_trash = page.evaluate(
            """
            async () => {
                await storePut('recipes', { id: 'di-r1', name: 'Recette Corbeille', ingredients: [] });
                state.recipes = await storeAll('recipes');

                const originalObjectStore = IDBTransaction.prototype.objectStore;
                let aborted = false;
                IDBTransaction.prototype.objectStore = function (name) {
                    const store = originalObjectStore.call(this, name);
                    if (name === 'trash' && !aborted) {
                        aborted = true;
                        const originalPut = store.put.bind(store);
                        store.put = function (value) {
                            const req = originalPut(value);
                            req.onsuccess = () => this.transaction.abort();
                            return req;
                        }.bind(store);
                    }
                    return store;
                };
                let threw = false;
                try {
                    await moveRecipeToTrash(state.recipes.find((r) => r.id === 'di-r1'));
                } catch (e) {
                    threw = true;
                } finally {
                    IDBTransaction.prototype.objectStore = originalObjectStore;
                }

                const inRecipes = (await storeAll('recipes')).some((r) => r.id === 'di-r1');
                const inTrash = (await storeAll('trash')).some((r) => r.id === 'di-r1');
                return { threw, inRecipes, inTrash, stateStillHasRecipe: state.recipes.some((r) => r.id === 'di-r1') };
            }
            """
        )
        check(
            "moveRecipeToTrash rejette bien quand la transaction échoue",
            result_trash["threw"] is True,
            str(result_trash),
        )
        check(
            "la recette n'est dupliquée NI perdue : reste uniquement dans 'recipes'",
            result_trash["inRecipes"] is True and result_trash["inTrash"] is False,
            str(result_trash),
        )
        check(
            "l'état en mémoire n'a pas non plus été modifié avant confirmation",
            result_trash["stateStillHasRecipe"] is True,
            str(result_trash),
        )
        page.evaluate("async () => { await storeDelete('recipes', 'di-r1'); await storeDelete('trash', 'di-r1'); }")
        print()

        print("=== renameIngredientName : atomique à travers tous les entrepôts concernés ===\n")
        result_rename = page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'di-s1', name: 'Endive', quantity: 1, unit: 'pièce', checked: false });
                await storePut('ingredients', { name: 'Endive' });
                state.shopping = await storeAll('shopping');
                state.ingredientNames = (await storeAll('ingredients')).map((i) => i.name);
                const shoppingSnapshot = JSON.stringify(state.shopping);

                const originalObjectStore = IDBTransaction.prototype.objectStore;
                let aborted = false;
                IDBTransaction.prototype.objectStore = function (name) {
                    const store = originalObjectStore.call(this, name);
                    if (name === 'shopping' && !aborted) {
                        aborted = true;
                        const originalPut = store.put.bind(store);
                        store.put = function (value) {
                            const req = originalPut(value);
                            req.onsuccess = () => this.transaction.abort();
                            return req;
                        }.bind(store);
                    }
                    return store;
                };
                let threw = false;
                try {
                    await renameIngredientName('Endive', 'Endive belge');
                } catch (e) {
                    threw = true;
                } finally {
                    IDBTransaction.prototype.objectStore = originalObjectStore;
                }

                return {
                    threw,
                    dbShoppingName: (await storeAll('shopping')).find((s) => s.id === 'di-s1').name,
                    dbIngredientNames: (await storeAll('ingredients')).map((i) => i.name),
                    stateUnchanged: JSON.stringify(state.shopping) === shoppingSnapshot,
                };
            }
            """
        )
        check(
            "renameIngredientName rejette bien quand la transaction échoue",
            result_rename["threw"] is True,
            str(result_rename),
        )
        check(
            "aucun changement partiel en base (courses toujours sur l'ancien nom)",
            result_rename["dbShoppingName"] == "Endive" and "Endive" in result_rename["dbIngredientNames"],
            str(result_rename),
        )
        check(
            "l'état en mémoire n'a pas non plus été modifié avant confirmation",
            result_rename["stateUnchanged"] is True,
            str(result_rename),
        )
        page.evaluate(
            """
            async () => {
                await storeDelete('shopping', 'di-s1');
                for (const n of ['Endive', 'Endive belge']) await storeDelete('ingredients', n);
            }
            """
        )
        print()

        print("=== saveRecipeForm : un échec d'écriture ne fait pas croire à un enregistrement réussi ===\n")
        # Appelle directement la vraie fonction de production sur le vrai
        # formulaire (construit par openRecipeForm, comme le ferait un clic
        # réel sur "Ajouter une recette"), plutôt qu'une reconstruction du
        # comportement attendu — voir l'audit précédent sur ce même principe
        # (tester le code réel, jamais une copie qui pourrait diverger de lui).
        # storePut est temporairement remplacée par une version qui rejette,
        # pour simuler un échec de persistance sans dépendre du gestionnaire
        # onabort de storePut (absent — hors du périmètre corrigé ici, voir
        # TESTS_NON_REGRESSION.md).
        result_save = page.evaluate(
            """
            async () => {
                await openRecipeForm(null);
                document.getElementById('f-name').value = 'Test Save Error';
                state.formIngredients = [{ name: 'Sel', quantity: 1, unit: 'pièce' }];
                const recipesCountBefore = state.recipes.length;

                const originalStorePut = window.storePut;
                window.storePut = (storeName, value) =>
                    storeName === 'recipes' ? Promise.reject(new Error('simulated_write_failure')) : originalStorePut(storeName, value);

                const savePromise = saveRecipeForm(document, null);
                await new Promise((resolve) => {
                    const check = () => (document.getElementById('custom-alert-ok') ? resolve() : setTimeout(check, 20));
                    check();
                });
                const alertText = document.getElementById('custom-alert-message').textContent;
                document.getElementById('custom-alert-ok').click();
                await savePromise;
                window.storePut = originalStorePut;

                return {
                    alertText,
                    screenStillForm: state.screen === 'form',
                    recipesCountUnchanged: state.recipes.length === recipesCountBefore,
                    notInDb: !(await storeAll('recipes')).some((r) => r.name === 'Test Save Error'),
                };
            }
            """
        )
        check(
            "un message d'erreur clair est montré à l'utilisateur (storage_write_error)",
            "problème de stockage" in result_save["alertText"] or "storage" in result_save["alertText"].lower(),
            str(result_save),
        )
        check(
            "l'écran ne navigue PAS vers la recette comme si l'enregistrement avait réussi",
            result_save["screenStillForm"] is True,
            str(result_save),
        )
        check(
            "state.recipes n'a pas été mis à jour après l'échec",
            result_save["recipesCountUnchanged"] is True,
            str(result_save),
        )
        check(
            "la recette n'a pas non plus été écrite en base",
            result_save["notInDb"] is True,
            str(result_save),
        )
        print()

        print("=== Tri des recettes par nom : suit désormais la langue affichée (CURRENT_LANG) ===\n")
        # Vérifie directement dans le code source livré (relit app.js tel que
        # servi par le serveur de test) plutôt que dans une chaîne reconstituée
        # à la main — même principe que les audits précédents : tester le vrai
        # code de production, jamais une copie qui pourrait diverger de lui.
        app_js_source = urllib.request.urlopen(f"http://127.0.0.1:{port}/app.js").read().decode("utf-8")
        occurrences_fr_hardcoded = app_js_source.count('a.name.localeCompare(b.name, "fr")')
        occurrences_current_lang = app_js_source.count("a.name.localeCompare(b.name, CURRENT_LANG)")
        check(
            'plus aucun tri de recette figé sur "fr"',
            occurrences_fr_hardcoded == 0,
            f"occurrences restantes: {occurrences_fr_hardcoded}",
        )
        check(
            "au moins les 5 tris de recette connus suivent bien CURRENT_LANG",
            occurrences_current_lang >= 5,
            f"occurrences trouvées: {occurrences_current_lang}",
        )
        print()

        print("=== storePut / storeDelete : ne restent plus bloquées pour toujours si la transaction est abandonnée après succès ===\n")
        result_base_onabort = page.evaluate(
            """
            async () => {
                await storeDelete('shopping', 'sp-abort-1');
                const originalObjectStore = IDBTransaction.prototype.objectStore;

                let aborted = false;
                IDBTransaction.prototype.objectStore = function (name) {
                    const store = originalObjectStore.call(this, name);
                    if (!aborted) {
                        aborted = true;
                        const originalPut = store.put.bind(store);
                        store.put = function (value) {
                            const req = originalPut(value);
                            req.onsuccess = () => this.transaction.abort();
                            return req;
                        }.bind(store);
                    }
                    return store;
                };
                let putSettled = false;
                try {
                    await storePut('shopping', { id: 'sp-abort-1', name: 'Test', unit: 'boîte', quantity: 1, checked: false });
                } catch (e) {
                    putSettled = true;
                } finally {
                    IDBTransaction.prototype.objectStore = originalObjectStore;
                }

                await storePut('shopping', { id: 'sp-abort-2', name: 'Test2', unit: 'boîte', quantity: 1, checked: false });
                let aborted2 = false;
                IDBTransaction.prototype.objectStore = function (name) {
                    const store = originalObjectStore.call(this, name);
                    if (!aborted2) {
                        aborted2 = true;
                        const originalDelete = store.delete.bind(store);
                        store.delete = function (key) {
                            const req = originalDelete(key);
                            req.onsuccess = () => this.transaction.abort();
                            return req;
                        }.bind(store);
                    }
                    return store;
                };
                let delSettled = false;
                try {
                    await storeDelete('shopping', 'sp-abort-2');
                } catch (e) {
                    delSettled = true;
                } finally {
                    IDBTransaction.prototype.objectStore = originalObjectStore;
                }

                return { putSettled, delSettled };
            }
            """
        )
        check(
            "storePut() se résout/rejette (jamais bloquée) même abandonnée après succès de sa requête",
            result_base_onabort["putSettled"] is True,
            str(result_base_onabort),
        )
        check(
            "storeDelete() se résout/rejette (jamais bloquée) même abandonnée après succès de sa requête",
            result_base_onabort["delSettled"] is True,
            str(result_base_onabort),
        )
        page.evaluate("async () => { await storeDelete('shopping', 'sp-abort-1'); await storeDelete('shopping', 'sp-abort-2'); }")
        print()

        print("Erreurs JS sur tout le parcours:", "AUCUNE" if not errors else "; ".join(errors))
        if errors:
            all_ok = False
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "DES ÉCHECS SUBSISTENT")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
