"""
Vérifie la fonctionnalité demandée explicitement par l'utilisateur suite
au point 115 (TESTS_NON_REGRESSION.md) : plutôt que de fusionner
silencieusement une quantité connue et une quantité non précisée pour le
même article de la liste de courses (comportement délibéré du point 114,
qui évite les doublons mais peut laisser croire à tort que le nombre
affiché est le total exact), l'article est désormais marqué
"partialQuantity" dès qu'une fusion combine une quantité connue et une
quantité inconnue — et son affichage précise alors "... + quantité non
précisée" au lieu du nombre seul.

Couvre les 3 points d'ajout à la liste de courses qui partagent la même
logique de fusion (computeShoppingMerge) : addRecipeToShoppingSilent
(planning, menus), addRecipeToShopping (bouton "Ajouter aux courses"
d'une recette) et le rappel "stock bas" de l'accueil — plus le rendu
réel (shoppingItemRow) et la modification manuelle via le formulaire
(qui doit reprendre la main sur la valeur et effacer le marqueur).
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

        print("=== 1. addRecipeToShoppingSilent : existant sans quantité + ajout avec quantité ===")
        r1 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'a1', name: 'Sel', quantity: null, unit: 'pièce', checked: false });
                state.shopping = await storeAll('shopping');
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Sel', quantity: 5, unit: 'pièce' }] }, 1);
                const mem = state.shopping.find((i) => i.id === 'a1');
                const db = (await storeAll('shopping')).find((i) => i.id === 'a1');
                return { mem, db };
            }
            """
        )
        check(
            "quantité fusionnée à 5, marquée partielle (mémoire et base)",
            r1["mem"]["quantity"] == 5 and r1["mem"]["partialQuantity"] is True
            and r1["db"]["quantity"] == 5 and r1["db"]["partialQuantity"] is True,
            json.dumps(r1),
        )

        print("\n=== 2. addRecipeToShoppingSilent : existant avec quantité + ajout sans quantité ===")
        r2 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'b1', name: 'Farine', quantity: 200, unit: 'g', checked: false });
                state.shopping = await storeAll('shopping');
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Farine', quantity: null, unit: 'g' }] }, 1);
                const mem = state.shopping.find((i) => i.id === 'b1');
                const db = (await storeAll('shopping')).find((i) => i.id === 'b1');
                return { mem, db };
            }
            """
        )
        check(
            "quantité inchangée à 200, marquée partielle (mémoire et base)",
            r2["mem"]["quantity"] == 200 and r2["mem"]["partialQuantity"] is True
            and r2["db"]["quantity"] == 200 and r2["db"]["partialQuantity"] is True,
            json.dumps(r2),
        )

        print("\n=== 3. Fusion complète (deux quantités connues) : jamais marquée partielle ===")
        r3 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'c1', name: 'Lait', quantity: 1, unit: 'L', checked: false });
                state.shopping = await storeAll('shopping');
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Lait', quantity: 1, unit: 'L' }] }, 1);
                const item = state.shopping.find((i) => i.id === 'c1');
                return { quantity: item.quantity, partial: !!item.partialQuantity };
            }
            """
        )
        check("quantité 2, jamais partielle", r3["quantity"] == 2 and r3["partial"] is False, json.dumps(r3))

        print("\n=== 4. Deux ajouts sans quantité : reste totalement sans quantité, pas de marqueur ===")
        r4 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'd1', name: 'Poivre', quantity: null, unit: 'pièce', checked: false });
                state.shopping = await storeAll('shopping');
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Poivre', quantity: null, unit: 'pièce' }] }, 1);
                const item = state.shopping.find((i) => i.id === 'd1');
                return { quantity: item.quantity, partial: !!item.partialQuantity };
            }
            """
        )
        check("quantité toujours nulle, pas de marqueur", r4["quantity"] is None and r4["partial"] is False, json.dumps(r4))

        print("\n=== 5. Le marqueur, une fois posé, survit à une fusion quantifiée ultérieure ===")
        r5 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'e1', name: 'Beurre', quantity: null, unit: 'g', checked: false });
                state.shopping = await storeAll('shopping');
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Beurre', quantity: 50, unit: 'g' }] }, 1);
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Beurre', quantity: 30, unit: 'g' }] }, 1);
                const item = state.shopping.find((i) => i.id === 'e1');
                return { quantity: item.quantity, partial: !!item.partialQuantity };
            }
            """
        )
        check("quantité cumulée à 80, toujours partielle", r5["quantity"] == 80 and r5["partial"] is True, json.dumps(r5))

        print("\n=== 6. addRecipeToShopping (bouton fiche recette) : même comportement ===")
        r6 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                state.pantry = [];
                state.pantryClaimedThisSession = [];
                await storePut('shopping', { id: 'f1', name: 'Thym', quantity: null, unit: 'pièce', checked: false });
                state.shopping = await storeAll('shopping');
                await addRecipeToShopping({ ingredients: [{ name: 'Thym', quantity: 2, unit: 'pièce' }] }, 1);
                const item = state.shopping.find((i) => i.id === 'f1');
                return { quantity: item.quantity, partial: !!item.partialQuantity };
            }
            """
        )
        check("quantité fusionnée à 2, marquée partielle", r6["quantity"] == 2 and r6["partial"] is True, json.dumps(r6))

        print("\n=== 7. Rappel 'stock bas' de l'accueil : même comportement (qty toujours connue ici, jamais partiel) ===")
        r7 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'g-pantry', name: 'Riz', quantity: 100, unit: 'g', threshold: 500 });
                state.pantry = await storeAll('pantry');
                state.recipes = [];
                state.screen = 'home';
                render();
                await new Promise((r) => setTimeout(r, 150));
                const reminder = [...document.querySelectorAll('div')].find((d) => d.textContent.includes('Riz') && d.style.cursor === 'pointer');
                if (reminder) reminder.click();
                await new Promise((r) => setTimeout(r, 150));
                const item = state.shopping.find((i) => normalize(i.name) === normalize('Riz'));
                return item ? { quantity: item.quantity, partial: !!item.partialQuantity } : null;
            }
            """
        )
        check(
            "article créé avec la quantité du seuil, jamais partiel (premier ajout)",
            r7 is not None and r7["quantity"] == 500 and r7["partial"] is False,
            json.dumps(r7),
        )

        print("\n=== 8. Affichage réel : suffixe visible uniquement sur l'article partiel ===")
        r8 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'h1', name: 'Sucre', quantity: 100, unit: 'g', partialQuantity: true, checked: false });
                await storePut('shopping', { id: 'h2', name: 'Miel', quantity: 50, unit: 'g', checked: false });
                state.shopping = await storeAll('shopping');
                state.screen = 'shopping';
                render();
                await new Promise((r) => setTimeout(r, 100));
                const rows = [...document.querySelectorAll('.shopping-item .label')];
                const sucre = rows.find((r) => r.textContent.includes('Sucre'));
                const miel = rows.find((r) => r.textContent.includes('Miel'));
                const checkbox = [...document.querySelectorAll('.shopping-item input[type=checkbox]')].find((c) =>
                    (c.getAttribute('aria-label') || '').includes('Sucre')
                );
                return {
                    sucreText: sucre ? sucre.textContent : null,
                    mielText: miel ? miel.textContent : null,
                    sucreAriaLabel: checkbox ? checkbox.getAttribute('aria-label') : null,
                };
            }
            """
        )
        check(
            "suffixe présent sur Sucre (texte ET aria-label), absent sur Miel",
            r8["sucreText"] is not None and "non précisée" in r8["sucreText"]
            and r8["sucreAriaLabel"] is not None and "non précisée" in r8["sucreAriaLabel"]
            and r8["mielText"] is not None and "non précisée" not in r8["mielText"],
            json.dumps(r8, ensure_ascii=False),
        )

        print("\n=== 9. Modification manuelle (formulaire) reprend la main : marqueur effacé ===")
        r9 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                const item = { id: 'i1', name: 'Sucre', quantity: 100, unit: 'g', partialQuantity: true, checked: false };
                await storePut('shopping', item);
                state.shopping = [item];
                state.screen = 'shopping';
                render();
                await new Promise((r) => setTimeout(r, 100));
                document.querySelector('.shopping-item .label').click();
                await new Promise((r) => setTimeout(r, 100));
                document.querySelector('#modal-ing-qty').value = 150;
                document.querySelector('#modal-confirm').click();
                await new Promise((r) => setTimeout(r, 200));
                const db = (await storeAll('shopping')).find((i) => i.id === 'i1');
                const mem = state.shopping.find((i) => i.id === 'i1');
                return { db, mem };
            }
            """
        )
        check(
            "quantité mise à 150, marqueur effacé (mémoire et base)",
            r9["db"]["quantity"] == 150 and not r9["db"].get("partialQuantity")
            and r9["mem"]["quantity"] == 150 and not r9["mem"].get("partialQuantity"),
            json.dumps(r9),
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
