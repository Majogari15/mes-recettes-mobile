"""
Vérifie les 3 bugs "Important" confirmés par une troisième relecture
externe (voir TESTS_NON_REGRESSION.md point 118), sur l'ajout d'une
recette (ou d'un article manuel) à la liste de courses avec réservation
du garde-manger :

1. Une réservation du garde-manger pouvait rester engagée (en mémoire
   ET en base) alors qu'un ingrédient plus loin dans la même recette
   échouait à s'écrire dans la liste de courses — l'opération globale
   échouait, mais la réservation, elle, restait appliquée.
2. L'article de courses et sa réservation s'écrivaient séparément :
   rien ne garantissait qu'ils survivent ou échouent ensemble.
3. addRecipeToShoppingSilent (planning, menus) écrivait chaque
   ingrédient séparément dans une boucle : un échec sur le 2e
   ingrédient d'une recette de 2 laissait le 1er déjà écrit (recette
   ajoutée seulement en partie).

Corrigé en regroupant TOUTE l'opération (tous les articles de courses
touchés + toutes les nouvelles réservations) dans une seule transaction
IndexedDB (storeWriteManyAcrossStores, entrepôts "shopping" et "kv") —
l'état en mémoire n'est mis à jour qu'après confirmation de cette
transaction. Couvre les 3 points d'écriture concernés
(addRecipeToShoppingSilent, addRecipeToShopping, l'ajout manuel d'un
article de courses avec réduction du garde-manger dans
openAddItemModal), ainsi que la remontée d'un message d'erreur visible
à l'utilisateur (auparavant : échec totalement silencieux, aucun retour
visuel) et le chemin normal (sans échec) pour ne pas régresser sur les
3 fonctions réécrites.
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

        print("=== 1. addRecipeToShopping : aucune réservation orpheline si un ingrédient échoue ===")
        r1 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'p1', name: 'Riz', quantity: 100, unit: 'g' });
                state.pantry = await storeAll('pantry');
                state.shopping = [];
                state.pantryClaimedThisSession = [];
                await kvSet('pantryClaimedThisSession', []);

                const realWriteMany = window.storeWriteManyAcrossStores;
                window.storeWriteManyAcrossStores = () => Promise.reject(new Error('échec simulé transaction'));
                const realCustomConfirm = window.customConfirm;
                window.customConfirm = () => Promise.resolve(true);
                let threw = false;
                try {
                    await addRecipeToShopping({ ingredients: [
                        { name: 'Riz', quantity: 50, unit: 'g' },
                        { name: 'Sel', quantity: 5, unit: 'g' },
                    ] }, 1);
                } catch (e) { threw = true; }
                window.storeWriteManyAcrossStores = realWriteMany;
                window.customConfirm = realCustomConfirm;
                const dbClaims = await kvGet('pantryClaimedThisSession');
                return {
                    threw,
                    memClaims: state.pantryClaimedThisSession.length,
                    dbClaims: (dbClaims || []).length,
                    shoppingCount: state.shopping.length,
                    dbShoppingCount: (await storeAll('shopping')).length,
                };
            }
            """
        )
        check(
            "échec propagé, rien n'est écrit (ni article, ni réservation)",
            r1["threw"] is True and r1["memClaims"] == 0 and r1["dbClaims"] == 0
            and r1["shoppingCount"] == 0 and r1["dbShoppingCount"] == 0,
            json.dumps(r1),
        )

        print("\n=== 2. addRecipeToShopping : l'article ET sa réservation partent dans la même transaction ===")
        r2 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'p2', name: 'Farine', quantity: 100, unit: 'g' });
                state.pantry = await storeAll('pantry');
                state.shopping = [];
                state.pantryClaimedThisSession = [];
                await kvSet('pantryClaimedThisSession', []);

                const realWriteMany = window.storeWriteManyAcrossStores;
                let capturedOps = null;
                window.storeWriteManyAcrossStores = (ops) => { capturedOps = ops; return realWriteMany(ops); };
                const realCustomConfirm = window.customConfirm;
                window.customConfirm = () => Promise.resolve(true);
                await addRecipeToShopping({ ingredients: [{ name: 'Farine', quantity: 500, unit: 'g' }] }, 1);
                window.storeWriteManyAcrossStores = realWriteMany;
                window.customConfirm = realCustomConfirm;
                return { stores: (capturedOps || []).map((op) => op.store).sort() };
            }
            """
        )
        check("un seul appel, entrepôts 'shopping' et 'kv' ensemble", r2["stores"] == ["kv", "shopping"], json.dumps(r2))

        print("\n=== 3. addRecipeToShoppingSilent : atomique (2e ingrédient échoue -> rien n'est écrit) ===")
        r3 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                state.shopping = [];

                const realWriteMany = window.storeWriteManyAcrossStores;
                window.storeWriteManyAcrossStores = () => Promise.reject(new Error('échec simulé transaction'));
                let threw = false;
                try {
                    await addRecipeToShoppingSilent({ ingredients: [
                        { name: 'Farine', quantity: 200, unit: 'g' },
                        { name: 'Sel', quantity: 5, unit: 'g' },
                    ] }, 1);
                } catch (e) { threw = true; }
                window.storeWriteManyAcrossStores = realWriteMany;
                return { threw, memCount: state.shopping.length, dbCount: (await storeAll('shopping')).length };
            }
            """
        )
        check(
            "échec propagé, aucun ingrédient de la recette n'est écrit (ni le 1er, ni le 2e)",
            r3["threw"] is True and r3["memCount"] == 0 and r3["dbCount"] == 0,
            json.dumps(r3),
        )

        print("\n=== 4. Chemin normal (sans échec) : addRecipeToShoppingSilent inchangé ===")
        r4 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                state.shopping = [];
                await addRecipeToShoppingSilent({ ingredients: [
                    { name: 'Farine', quantity: 200, unit: 'g' },
                    { name: 'Sel', quantity: null, unit: 'pièce' },
                ] }, 1);
                const db = await storeAll('shopping');
                return { memCount: state.shopping.length, dbCount: db.length, names: db.map((i) => i.name).sort() };
            }
            """
        )
        check(
            "les 2 ingrédients sont bien ajoutés",
            r4["memCount"] == 2 and r4["dbCount"] == 2 and r4["names"] == ["Farine", "Sel"],
            json.dumps(r4, ensure_ascii=False),
        )

        print("\n=== 5. Chemin normal : addRecipeToShopping avec couverture totale + partielle ===")
        r5 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'p5a', name: 'Riz', quantity: 500, unit: 'g' });
                await storePut('pantry', { id: 'p5b', name: 'Farine', quantity: 100, unit: 'g' });
                state.pantry = await storeAll('pantry');
                state.shopping = [];
                state.pantryClaimedThisSession = [];
                await kvSet('pantryClaimedThisSession', []);
                const realCustomConfirm = window.customConfirm;
                window.customConfirm = () => Promise.resolve(true);
                await addRecipeToShopping({ ingredients: [
                    { name: 'Riz', quantity: 200, unit: 'g' },
                    { name: 'Farine', quantity: 500, unit: 'g' },
                ] }, 1);
                window.customConfirm = realCustomConfirm;
                const dbShopping = await storeAll('shopping');
                const dbClaims = await kvGet('pantryClaimedThisSession');
                return {
                    memShopping: state.shopping.map((i) => i.name),
                    dbShopping: dbShopping.map((i) => i.name),
                    memClaims: state.pantryClaimedThisSession.length,
                    dbClaims: (dbClaims || []).length,
                };
            }
            """
        )
        check(
            "riz entièrement couvert (aucun article), farine partiellement (1 article + 2 réservations)",
            r5["memShopping"] == ["Farine"] and r5["dbShopping"] == ["Farine"] and r5["memClaims"] == 2 and r5["dbClaims"] == 2,
            json.dumps(r5, ensure_ascii=False),
        )

        print("\n=== 6. Chemin normal : ajout manuel (formulaire) avec couverture partielle ===")
        r6 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'p6', name: 'Sucre', quantity: 50, unit: 'g' });
                state.pantry = await storeAll('pantry');
                state.shopping = [];
                state.pantryClaimedThisSession = [];
                await kvSet('pantryClaimedThisSession', []);
                const realCustomConfirm = window.customConfirm;
                window.customConfirm = () => Promise.resolve(true);
                openAddItemModal('shopping');
                await new Promise((r) => setTimeout(r, 100));
                document.getElementById('modal-ing-name').value = 'Sucre';
                document.getElementById('modal-ing-qty').value = 200;
                document.getElementById('modal-ing-unit').value = 'g';
                document.getElementById('modal-confirm').click();
                await new Promise((r) => setTimeout(r, 200));
                window.customConfirm = realCustomConfirm;
                const dbShopping = await storeAll('shopping');
                const dbClaims = await kvGet('pantryClaimedThisSession');
                return {
                    memShopping: state.shopping.map((i) => ({ name: i.name, qty: i.quantity })),
                    dbShopping: dbShopping.map((i) => ({ name: i.name, qty: i.quantity })),
                    memClaims: state.pantryClaimedThisSession.length,
                    dbClaims: (dbClaims || []).length,
                };
            }
            """
        )
        check(
            "article créé à 150g (500g demandés - 50g de stock), 1 réservation",
            r6["memShopping"] == [{"name": "Sucre", "qty": 150}] and r6["dbShopping"] == [{"name": "Sucre", "qty": 150}]
            and r6["memClaims"] == 1 and r6["dbClaims"] == 1,
            json.dumps(r6, ensure_ascii=False),
        )

        print("\n=== 7. Chemin normal : ajout manuel avec couverture totale (aucun article créé) ===")
        r7 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'p7', name: 'Beurre', quantity: 200, unit: 'g' });
                state.pantry = await storeAll('pantry');
                state.shopping = [];
                state.pantryClaimedThisSession = [];
                await kvSet('pantryClaimedThisSession', []);
                const realCustomConfirm = window.customConfirm;
                window.customConfirm = () => Promise.resolve(true);
                openAddItemModal('shopping');
                await new Promise((r) => setTimeout(r, 100));
                document.getElementById('modal-ing-name').value = 'Beurre';
                document.getElementById('modal-ing-qty').value = 100;
                document.getElementById('modal-ing-unit').value = 'g';
                document.getElementById('modal-confirm').click();
                await new Promise((r) => setTimeout(r, 200));
                window.customConfirm = realCustomConfirm;
                const dbShopping = await storeAll('shopping');
                const dbClaims = await kvGet('pantryClaimedThisSession');
                return {
                    memShoppingCount: state.shopping.length,
                    dbShoppingCount: dbShopping.length,
                    memClaims: state.pantryClaimedThisSession.length,
                    dbClaims: (dbClaims || []).length,
                };
            }
            """
        )
        check(
            "aucun article de courses créé, 1 réservation appliquée",
            r7["memShoppingCount"] == 0 and r7["dbShoppingCount"] == 0 and r7["memClaims"] == 1 and r7["dbClaims"] == 1,
            json.dumps(r7),
        )

        print("\n=== 8. Message d'erreur visible : bouton 'Ajouter aux courses' d'une fiche recette ===")
        r8 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                const recipe = { id: 'rcp1', name: 'Test', category: 'Plat', defaultPersons: 4, ingredients: [{ name: 'Poivre', quantity: 1, unit: 'pièce' }] };
                await storePut('recipes', recipe);
                state.recipes = await storeAll('recipes');
                state.currentRecipeId = 'rcp1';
                state.viewPersons = 4;
                state.screen = 'recipe';
                render();
                await new Promise((r) => setTimeout(r, 100));
                const realWriteMany = window.storeWriteManyAcrossStores;
                window.storeWriteManyAcrossStores = () => Promise.reject(new Error('échec simulé'));
                let alertShown = false;
                const realCustomAlert = window.customAlert;
                window.customAlert = (msg) => { alertShown = true; return realCustomAlert ? realCustomAlert(msg) : Promise.resolve(); };
                const btn = [...document.querySelectorAll('button')].find((b) => b.textContent.includes('courses'));
                if (btn) btn.click();
                await new Promise((r) => setTimeout(r, 200));
                window.storeWriteManyAcrossStores = realWriteMany;
                window.customAlert = realCustomAlert;
                return { hasBtn: !!btn, alertShown };
            }
            """
        )
        check(
            "un message d'erreur est bien affiché à l'utilisateur en cas d'échec",
            r8["hasBtn"] and r8["alertShown"],
            json.dumps(r8),
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
