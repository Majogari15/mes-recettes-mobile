#!/usr/bin/env python3
"""
Test permanent pour la fusion des unités "sachet"/"pot" dans "boîte"
(v220), les 9 correctifs qui ont suivi (v221), et les 5 défauts de la
fusion des doublons + la préservation de containerLabel trouvés par un
second avis externe sur la v221/v222 — voir TESTS_NON_REGRESSION.md,
points 76, 77 et 79.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_units_migration.py

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
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")

        print("=== UNIT_OPTIONS : une seule entrée fusionnée ===\n")
        options = page.evaluate("() => UNIT_OPTIONS")
        check(
            "boîte présente, sachet/pot absents",
            "boîte" in options and "sachet" not in options and "pot" not in options,
            str(options),
        )
        print()

        print("=== Reconnaissance à l'import : toutes les variantes -> boîte ===\n")
        cases = [
            "2 boîtes de tomates concassées",
            "1 sachet de levure",
            "1 pot de crème fraîche",
            "1 conserve de maïs",
        ]
        for c in cases:
            res = page.evaluate("(s) => parseIngredientString(s)", c)
            check(f'"{c}" -> unit="boîte"', res["unit"] == "boîte", str(res))
        print()

        print("=== containerLabel : conserve le mot d'origine (sachet/pot/boîte) ===\n")
        sachet = page.evaluate("() => parseIngredientString('1 sachet de levure')")
        pot = page.evaluate("() => parseIngredientString('1 pot de crème fraîche')")
        conserve = page.evaluate("() => parseIngredientString('1 conserve de maïs')")
        check('containerLabel="sachet" pour "sachet"', sachet.get("containerLabel") == "sachet", str(sachet))
        check('containerLabel="pot" pour "pot"', pot.get("containerLabel") == "pot", str(pot))
        check(
            "containerLabel absent pour une variante jamais distincte (conserve)",
            conserve.get("containerLabel") is None,
            str(conserve),
        )
        print()

        print("=== Migration au démarrage : prix personnalisés, garde-manger, courses ===\n")
        page.evaluate(
            """
            async () => {
                await storePut('ingredientOverrides', { name: 'Yaourt', price: { amount: 2, unit: 'pot' } });
                await storePut('shopping', { id: 'mig-s1', name: 'Yaourt', unit: 'pot', quantity: 1, checked: false });
                await storePut('pantry', { id: 'mig-p1', name: 'Yaourt', unit: 'sachet', quantity: 3 });
                await storePut('recipes', { id: 'mig-r1', name: 'Recette migration', category: 'Autre', ingredients: [{ name: 'Yaourt', unit: 'sachet', quantity: 1 }] });
            }
            """
        )
        page.reload(timeout=8000)
        page.wait_for_function("() => document.body.innerText.trim().length > 20", timeout=15000)
        page.wait_for_timeout(800)
        result = page.evaluate(
            """
            () => {
                const price = getIngredientPrice('Yaourt');
                const shoppingItem = state.shopping.find((s) => s.id === 'mig-s1');
                const pantryItem = state.pantry.find((p) => p.id === 'mig-p1');
                const recipe = state.recipes.find((r) => r.id === 'mig-r1');
                return {
                    priceUnit: price ? price.unit : null,
                    cost: computeIngredientCost('Yaourt', shoppingItem.quantity, shoppingItem.unit),
                    shoppingUnit: shoppingItem.unit,
                    pantryUnit: pantryItem.unit,
                    recipeUnit: recipe.ingredients[0].unit,
                    recipeContainerLabel: recipe.ingredients[0].containerLabel,
                };
            }
            """
        )
        check("prix migré vers boîte", result["priceUnit"] == "boîte", str(result))
        check("coût calculable après migration (pas null)", result["cost"] == 2, str(result))
        check("garde-manger migré", result["pantryUnit"] == "boîte", str(result))
        check("courses migrées", result["shoppingUnit"] == "boîte", str(result))
        check("recette migrée", result["recipeUnit"] == "boîte", str(result))
        check(
            "containerLabel conservé lors de la migration (sachet)",
            result["recipeContainerLabel"] == "sachet",
            str(result),
        )
        print()

        print("=== Fusion des doublons de courses créés par la migration ===\n")
        page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'dup-1', name: 'Fromage blanc', unit: 'pot', quantity: 1, checked: false });
                await storePut('shopping', { id: 'dup-2', name: 'Fromage blanc', unit: 'sachet', quantity: 2, checked: false });
            }
            """
        )
        page.reload(timeout=8000)
        page.wait_for_function("() => document.body.innerText.trim().length > 20", timeout=15000)
        page.wait_for_timeout(800)
        dup_result = page.evaluate(
            "async () => (await storeAll('shopping')).filter((s) => s.name === 'Fromage blanc')"
        )
        check(
            "une seule ligne après fusion, quantités additionnées (1+2=3)",
            len(dup_result) == 1 and dup_result[0]["quantity"] == 3 and dup_result[0]["unit"] == "boîte",
            str(dup_result),
        )
        print()

        print("=== Import partagé (QR/lien ZIP bureau) migre aussi l'unité ===\n")
        shared = page.evaluate(
            """
            () => {
                const json = { id: 'shared-1', name: 'Recette partagée', ingredients: [{ name: 'Yaourt', unit: 'pot', quantity: 1 }] };
                return recipeFromSharedFormat(json, new Map());
            }
            """
        )
        check(
            "recipeFromSharedFormat migre l'unité",
            shared["ingredients"][0]["unit"] == "boîte",
            str(shared["ingredients"][0]),
        )
        print()

        print("=== Restauration de sauvegarde : select non vide dans le formulaire ===\n")
        page.evaluate(
            """
            async () => {
                const json = { id: 'shared-1', name: 'Recette partagée', ingredients: [{ name: 'Yaourt', unit: 'pot', quantity: 1 }], category: 'Autre' };
                const recipe = recipeFromSharedFormat(json, new Map());
                await storePut('recipes', recipe);
                state.recipes.push(recipe);
                openRecipeForm('shared-1');
            }
            """
        )
        page.wait_for_timeout(300)
        select_info = page.evaluate(
            """
            () => {
                const sel = document.querySelector('.ing-form-row select.ing-unit');
                return sel ? { value: sel.value, selectedIndex: sel.selectedIndex } : null;
            }
            """
        )
        check(
            "menu déroulant d'unité non vide après import partagé",
            select_info is not None and select_info["selectedIndex"] != -1 and select_info["value"] == "boîte",
            str(select_info),
        )
        print()

        print("=== Dédup après restauration : unités déjà converties par sanitizeBackupItem ===\n")
        result_dedup_restore = page.evaluate(
            """
            async () => {
                const backupData = {
                    exportedAt: new Date().toISOString(),
                    recipes: [], pantry: [], trash: [], savedShoppingLists: [], ingredients: [], ingredientOverrides: [], menus: [], planTemplates: [], planHistory: [], kv: [],
                    shopping: [
                        { id: 'dr-1', name: 'Compote de pommes', unit: 'pot', quantity: 1, checked: false },
                        { id: 'dr-2', name: 'Compote de pommes', unit: 'sachet', quantity: 1, checked: false },
                    ],
                };
                const report = { validCount: 0, ignoredCount: 0, photosRemoved: 0, numbersFixed: 0, structuralFixes: 0 };
                const cleanedData = { ...backupData };
                BACKUP_STORES.forEach((storeName) => {
                    if (!Array.isArray(backupData[storeName])) return;
                    cleanedData[storeName] = backupData[storeName].map((item) => sanitizeBackupItem(item, storeName, report));
                });
                await importAllData(cleanedData, 'merge');
                await migrateMergedContainerUnits();
                return state.shopping.filter((s) => s.name === 'Compote de pommes');
            }
            """
        )
        check(
            "une seule ligne après restauration + migration (pas 2 doublons)",
            len(result_dedup_restore) == 1 and result_dedup_restore[0]["quantity"] == 2,
            str(result_dedup_restore),
        )
        page.evaluate("async () => { for (const s of state.shopping.filter((s) => s.name === 'Fromage blanc')) await storeDelete('shopping', s.id); }")
        print()

        print("=== Fusion : ne mélange jamais un article coché avec un non coché ===\n")
        result_checked = page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'ck-1', name: 'Yaourt nature', unit: 'pot', quantity: 1, checked: true });
                await storePut('shopping', { id: 'ck-2', name: 'Yaourt nature', unit: 'sachet', quantity: 1, checked: false });
                state.shopping = await storeAll('shopping');
                await migrateMergedContainerUnits();
                return state.shopping.filter((s) => s.name === 'Yaourt nature');
            }
            """
        )
        check(
            "2 lignes distinctes conservées (une cochée, une non)",
            len(result_checked) == 2 and {i["checked"] for i in result_checked} == {True, False},
            str(result_checked),
        )
        page.evaluate("async () => { for (const s of state.shopping.filter((s) => s.name === 'Yaourt nature')) await storeDelete('shopping', s.id); }")
        print()

        print("=== Fusion : une quantité inconnue (null) ne devient jamais 0 ===\n")
        result_null_qty = page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'nq-1', name: 'Poivre', unit: 'pot', quantity: null, checked: false });
                await storePut('shopping', { id: 'nq-2', name: 'Poivre', unit: 'sachet', quantity: null, checked: false });
                state.shopping = await storeAll('shopping');
                await migrateMergedContainerUnits();
                return state.shopping.filter((s) => s.name === 'Poivre');
            }
            """
        )
        check(
            "quantité fusionnée reste null (jamais 0)",
            len(result_null_qty) == 1 and result_null_qty[0]["quantity"] is None,
            str(result_null_qty),
        )
        page.evaluate("async () => { for (const s of state.shopping.filter((s) => s.name === 'Poivre')) await storeDelete('shopping', s.id); }")
        print()

        print("=== Fusion : les réservations de garde-manger suivent la ligne conservée ===\n")
        result_claims = page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'cl-1', name: 'Beurre demi-sel', unit: 'pot', quantity: 1, checked: false });
                await storePut('shopping', { id: 'cl-2', name: 'Beurre demi-sel', unit: 'sachet', quantity: 1, checked: false });
                state.shopping = await storeAll('shopping');
                // commitPantryClaim() a été retiré (code mort, voir
                // TESTS_NON_REGRESSION.md point 118) : les 3 fonctions qui
                // posent une réservation l'écrivent désormais directement
                // dans la même transaction que l'article concerné. Ici, on
                // reproduit son effet (registre en mémoire + persistance
                // kv) pour préparer ce scénario de test.
                state.pantryClaimedThisSession.push({ id: 'claim-1', ingredientKey: 'Beurre demi-sel', amount: 0.5, sourceType: 'shopping', sourceId: 'cl-2', kind: 'weight' });
                await kvSet('pantryClaimedThisSession', state.pantryClaimedThisSession);
                await migrateMergedContainerUnits();
                const survivor = state.shopping.find((s) => s.name === 'Beurre demi-sel');
                const claims = state.pantryClaimedThisSession.filter((c) => c.ingredientKey === 'Beurre demi-sel');
                return { survivorId: survivor ? survivor.id : null, claims };
            }
            """
        )
        check(
            "la réservation référence l'id de la ligne survivante, aucune orpheline",
            len(result_claims["claims"]) == 1 and result_claims["claims"][0]["sourceId"] == result_claims["survivorId"],
            str(result_claims),
        )
        page.evaluate(
            """
            async () => {
                for (const s of state.shopping.filter((s) => s.name === 'Beurre demi-sel')) await storeDelete('shopping', s.id);
                state.pantryClaimedThisSession = state.pantryClaimedThisSession.filter((c) => c.ingredientKey !== 'Beurre demi-sel');
                await persistPantryClaims();
            }
            """
        )
        print()

        print("=== Fusion + réassignation de réservation : une seule transaction (shopping+kv), rien n'est modifié en mémoire avant confirmation ===\n")
        result_cross_store_atomic = page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'pm-1', name: 'Test Fusion Claims', unit: 'boîte', quantity: 1, checked: false });
                await storePut('shopping', { id: 'pm-2', name: 'Test Fusion Claims', unit: 'boîte', quantity: 1, checked: false });
                state.shopping = await storeAll('shopping');
                // commitPantryClaim() a été retiré (code mort, voir
                // TESTS_NON_REGRESSION.md point 118) : reproduit son effet
                // directement pour préparer ce scénario de test.
                state.pantryClaimedThisSession.push({ id: 'claim-2', ingredientKey: 'Test Fusion Claims', amount: 0.5, sourceType: 'shopping', sourceId: 'pm-2', kind: 'weight' });
                await kvSet('pantryClaimedThisSession', state.pantryClaimedThisSession);
                const shoppingSnapshotBefore = JSON.stringify(state.shopping);
                const claimsSnapshotBefore = JSON.stringify(state.pantryClaimedThisSession);

                // Force l'échec de persistShoppingMergeWithClaims (transaction
                // couvrant "shopping" ET "kv" ensemble) après que son premier
                // put ait déjà réussi -- même technique que pour
                // storePutAndDeleteMany plus haut -- pour vérifier (a) que
                // "list" (state.shopping) et state.pantryClaimedThisSession
                // ne sont mutés qu'après confirmation de la persistance, et
                // (b) que les deux entrepôts sont bien annulés ensemble.
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
                    await dedupeQuantityListAfterUnitMigration(state.shopping, 'shopping');
                } catch (e) {
                    threw = true;
                } finally {
                    IDBTransaction.prototype.objectStore = originalObjectStore;
                }

                const dbRows = (await storeAll('shopping')).filter((s) => s.name === 'Test Fusion Claims');
                const kvClaims = (await kvGet('pantryClaimedThisSession')) || [];
                const claimStillOnPm2 = kvClaims.some((c) => c.ingredientKey === 'Test Fusion Claims' && c.sourceId === 'pm-2');

                return {
                    threw,
                    shoppingUnchangedInMemory: JSON.stringify(state.shopping) === shoppingSnapshotBefore,
                    claimsUnchangedInMemory: JSON.stringify(state.pantryClaimedThisSession) === claimsSnapshotBefore,
                    dbRowCount: dbRows.length,
                    dbQuantitiesUnmerged: dbRows.every((r) => r.quantity === 1),
                    claimStillOnPm2,
                };
            }
            """
        )
        check(
            "dedupeQuantityListAfterUnitMigration rejette bien quand la persistance échoue (jamais résolu silencieusement)",
            result_cross_store_atomic["threw"] is True,
            str(result_cross_store_atomic),
        )
        check(
            "aucune mutation en mémoire de state.shopping / state.pantryClaimedThisSession avant confirmation de la persistance",
            result_cross_store_atomic["shoppingUnchangedInMemory"] and result_cross_store_atomic["claimsUnchangedInMemory"],
            str(result_cross_store_atomic),
        )
        check(
            "shopping ET kv sont annulés ensemble (aucune fusion partielle, aucune réservation orpheline)",
            result_cross_store_atomic["dbRowCount"] == 2
            and result_cross_store_atomic["dbQuantitiesUnmerged"]
            and result_cross_store_atomic["claimStillOnPm2"],
            str(result_cross_store_atomic),
        )
        page.evaluate(
            """
            async () => {
                for (const s of state.shopping.filter((s) => s.name === 'Test Fusion Claims')) await storeDelete('shopping', s.id);
                state.pantryClaimedThisSession = state.pantryClaimedThisSession.filter((c) => c.ingredientKey !== 'Test Fusion Claims');
                await persistPantryClaims();
            }
            """
        )
        print()

        print("=== Fusion : storePutAndDeleteMany() est bien une seule transaction atomique ===\n")
        result_atomic = page.evaluate(
            """
            async () => {
                await storePut('shopping', { id: 'at-1', name: 'Test Atomique', unit: 'boîte', quantity: 1, checked: false });
                await storePut('shopping', { id: 'at-2', name: 'Test Atomique', unit: 'boîte', quantity: 1, checked: false });
                // Appelle la VRAIE fonction de production utilisée par
                // dedupeQuantityListAfterUnitMigration, plutôt qu'une
                // transaction reconstruite à la main : on veut vérifier le
                // comportement réel du code exécuté par l'application, pas
                // un motif similaire écrit séparément dans le test.
                //
                // On force l'abandon depuis l'INTÉRIEUR d'une des requêtes
                // (via IDBObjectStore.getAll, injecté juste avant) plutôt que
                // depuis l'extérieur : on ne peut pas obtenir de référence à
                // "tx" hors de la fonction, donc on intercepte temporairement
                // IDBTransaction.prototype.objectStore pour abandonner la
                // transaction juste après que la requête put ait réussi
                // (aucune requête en erreur : seul onabort doit alors régir
                // le résultat), exactement le scénario du bug d'origine.
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
                let settled = false;
                let outcome = null;
                try {
                    await storePutAndDeleteMany(
                        'shopping',
                        [{ id: 'at-1', name: 'Test Atomique', unit: 'boîte', quantity: 2, checked: false }],
                        ['at-2']
                    );
                    settled = true;
                    outcome = 'resolved';
                } catch (e) {
                    settled = true;
                    outcome = 'rejected';
                } finally {
                    IDBTransaction.prototype.objectStore = originalObjectStore;
                }
                const rows = (await storeAll('shopping')).filter((s) => s.name === 'Test Atomique');
                return { settled, outcome, rows };
            }
            """
        )
        check(
            "storePutAndDeleteMany() se résout/rejette (jamais bloqué pour toujours) même quand la transaction est abandonnée après un put réussi",
            result_atomic["settled"] is True and result_atomic["outcome"] == "rejected",
            str(result_atomic),
        )
        check(
            "la transaction avortée annule le put ET le delete ensemble (aucun comptage double possible)",
            len(result_atomic["rows"]) == 2 and all(i["quantity"] == 1 for i in result_atomic["rows"]),
            str(result_atomic),
        )
        page.evaluate("async () => { for (const s of state.shopping.filter((s) => s.name === 'Test Atomique')) await storeDelete('shopping', s.id); }")
        print()

        print("=== storePutAndDeleteMany() : une erreur SYNCHRONE (enregistrement malformé) n'applique aucune écriture partielle ===\n")
        result_sync_error = page.evaluate(
            """
            async () => {
                await storeDelete('shopping', 'se-1');
                let outcome = null;
                try {
                    // Le 2e élément n'a pas d'id -> put() lève une DataError
                    // SYNCHRONE (le store 'shopping' n'a ni keyPath ni
                    // autoIncrement) avant même d'atteindre le delete.
                    await storePutAndDeleteMany('shopping', [
                        { id: 'se-1', name: 'Ecriture Valide', unit: 'boîte', quantity: 1, checked: false },
                        { name: 'Sans Id', unit: 'boîte', quantity: 1, checked: false },
                    ], []);
                    outcome = 'resolved';
                } catch (e) {
                    outcome = 'rejected';
                }
                const rows = await storeAll('shopping');
                return { outcome, se1Present: !!rows.find((r) => r.id === 'se-1') };
            }
            """
        )
        check(
            "storePutAndDeleteMany() rejette bien sur une erreur synchrone de préparation",
            result_sync_error["outcome"] == "rejected",
            str(result_sync_error),
        )
        check(
            "aucune écriture partielle : la requête déjà mise en file avant l'erreur n'est PAS appliquée",
            result_sync_error["se1Present"] is False,
            str(result_sync_error),
        )
        page.evaluate("async () => { await storeDelete('shopping', 'se-1'); }")
        print()

        print("=== persistShoppingMergeWithClaims() : même protection, entre shopping ET kv ===\n")
        result_sync_error_cross = page.evaluate(
            """
            async () => {
                await storeDelete('shopping', 'cse-1');
                const kvBefore = JSON.stringify((await kvGet('pantryClaimedThisSession')) || []);
                let outcome = null;
                try {
                    // Même défaut (2e survivor sans id) déclenché AVANT
                    // d'atteindre le put sur l'entrepôt 'kv' : les deux
                    // entrepôts doivent rester intacts, pas seulement le
                    // premier touché.
                    await persistShoppingMergeWithClaims(
                        [
                            { id: 'cse-1', name: 'Ecriture Valide Croisee', unit: 'boîte', quantity: 1, checked: false },
                            { name: 'Sans Id', unit: 'boîte', quantity: 1, checked: false },
                        ],
                        [],
                        [{ id: 'fake-claim', ingredientKey: 'X', amount: 1, sourceType: 'shopping', sourceId: 'cse-1', kind: 'weight' }]
                    );
                    outcome = 'resolved';
                } catch (e) {
                    outcome = 'rejected';
                }
                const rows = await storeAll('shopping');
                const kvAfter = JSON.stringify((await kvGet('pantryClaimedThisSession')) || []);
                return {
                    outcome,
                    cse1Present: !!rows.find((r) => r.id === 'cse-1'),
                    kvUnchanged: kvAfter === kvBefore,
                };
            }
            """
        )
        check(
            "persistShoppingMergeWithClaims() rejette bien sur une erreur synchrone de préparation",
            result_sync_error_cross["outcome"] == "rejected",
            str(result_sync_error_cross),
        )
        check(
            "aucune écriture partielle sur shopping NI sur kv (les deux entrepôts restent intacts)",
            result_sync_error_cross["cse1Present"] is False and result_sync_error_cross["kvUnchanged"] is True,
            str(result_sync_error_cross),
        )
        page.evaluate("async () => { await storeDelete('shopping', 'cse-1'); }")
        print()

        print("=== containerLabel : jamais fabriqué depuis une unité déjà \"boîte\" ===\n")
        result_no_fabrication = page.evaluate(
            """
            () => {
                const json = { id: 'nf-1', name: 'Test', ingredients: [{ name: 'Sucre', unit: 'boîte', quantity: 1 }] };
                return recipeFromSharedFormat(json, new Map()).ingredients[0];
            }
            """
        )
        check(
            'containerLabel reste absent (null) pour un ingrédient déjà "boîte" sans information d\'origine',
            result_no_fabrication.get("containerLabel") is None,
            str(result_no_fabrication),
        )
        print()

        print('=== containerLabel : survit à un export QR puis réimport ===\n')
        result_qr_roundtrip = page.evaluate(
            """
            () => {
                // Utilise les VRAIES fonctions d'encodage/décodage de
                // l'application (celles réellement appelées par
                // openQrCodeModal et par la lecture d'un QR scanné), plutôt
                // qu'une reconstruction séparée du format qui pourrait
                // diverger silencieusement du code de production.
                const recipe = { id: 'qr1', name: 'Recette QR', ingredients: [{ name: 'Levure', unit: 'boîte', quantity: 1, containerLabel: 'sachet' }], persons: 4 };
                const payload = buildCompactRecipeQrPayload(recipe, 4);
                const reparsed = parseRecipeFromQrText(JSON.stringify(payload));
                return reparsed.ingredients[0];
            }
            """
        )
        check(
            "containerLabel présent après un aller-retour complet par QR",
            result_qr_roundtrip.get("containerLabel") == "sachet",
            str(result_qr_roundtrip),
        )
        print()

        # Nettoyage
        page.evaluate(
            """
            async () => {
                for (const id of ['mig-r1', 'shared-1']) await storeDelete('recipes', id);
                for (const id of ['mig-s1', 'dup-1', 'dup-2']) await storeDelete('shopping', id);
                await storeDelete('pantry', 'mig-p1');
                await storeDelete('ingredientOverrides', 'Yaourt');
            }
            """
        )

        browser.close()

    httpd.shutdown()

    print("Erreurs JS sur tout le parcours:", errors if errors else "AUCUNE")
    if errors:
        all_ok = False

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
