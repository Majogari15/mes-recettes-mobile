#!/usr/bin/env python3
"""Test permanent : ne plus dupliquer un article de la liste de courses
quand l'ingrédient ajouté (depuis une recette, un menu, ou le planning)
n'a pas de quantité précisée — bug réel signalé par l'utilisateur avec
capture d'écran, confirmé en lisant le code avant de corriger.

Cause : `addRecipeToShoppingSilent()` (utilisée par le planning et les
menus) et `addRecipeToShopping()` (bouton "Ajouter aux courses" d'une
fiche recette) recherchaient bien un article déjà présent (même nom,
même unité, pas coché), mais ne le réutilisaient QUE si les DEUX
quantités (celle déjà dans la liste ET celle de l'ingrédient ajouté)
étaient non nulles :

    if (existing && qty != null && existing.quantity != null) { ... }
    else { /* crée un nouvel article */ }

Un ingrédient sans quantité précisée dans la recette (qty === null, ex.
"sel" sans dosage) ratait cette condition même quand un article
correspondant existait déjà, et retombait dans le "else" — créant un
doublon au lieu de reconnaître l'article déjà présent. Le même défaut
existait aussi dans le rappel "stock bas" de l'accueil (jamais signalé
par l'utilisateur mais avec exactement la même cause, corrigé par
cohérence).

Ce fichier vérifie, pour les deux fonctions concernées :

1. Existant sans quantité + nouvel ajout sans quantité → aucun doublon,
   l'article existant reste tel quel.
2. Existant AVEC quantité + nouvel ajout sans quantité → aucun doublon,
   la quantité existante n'est pas perdue.
3. Existant sans quantité + nouvel ajout AVEC quantité → aucun doublon,
   la quantité existante passe de "inconnue" à la quantité ajoutée.
4. Un article déjà coché du même nom n'est PAS réutilisé (comportement
   existant, non affecté par ce correctif) — un nouvel article non
   coché est bien créé à côté.
5. Le scénario réel signalé par l'utilisateur, de bout en bout dans
   l'interface : ajouter une recette à une liste de courses déjà
   existante ne duplique aucun ingrédient sans quantité.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_shopping_no_duplicate_missing_qty.py

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
        page = browser.new_page(viewport={"width": 390, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(800)
        page.evaluate("() => setLang('fr')")

        print("=== addRecipeToShoppingSilent (planning/menus) ===\n")

        page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'e1', name: 'Sel', quantity: null, unit: 'pièce', checked: false });
                state.shopping = await storeAll('shopping');
            }
            """
        )
        r1 = page.evaluate(
            """
            async () => {
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Sel', quantity: null, unit: 'pièce' }] }, 4);
                return await storeAll('shopping');
            }
            """
        )
        check("Existant sans quantité + ajout sans quantité : aucun doublon", len(r1) == 1, str(r1))

        page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'e2', name: 'Farine', quantity: 500, unit: 'g', checked: false });
                state.shopping = await storeAll('shopping');
            }
            """
        )
        r2 = page.evaluate(
            """
            async () => {
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Farine', quantity: null, unit: 'g' }] }, 4);
                return await storeAll('shopping');
            }
            """
        )
        check(
            "Existant avec quantité + ajout sans quantité : aucun doublon, quantité existante conservée",
            len(r2) == 1 and r2[0]["quantity"] == 500,
            str(r2),
        )

        page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'e3', name: 'Poivre', quantity: null, unit: 'pièce', checked: false });
                state.shopping = await storeAll('shopping');
            }
            """
        )
        r3 = page.evaluate(
            """
            async () => {
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Poivre', quantity: 2, unit: 'pièce' }] }, 1);
                return await storeAll('shopping');
            }
            """
        )
        check(
            "Existant sans quantité + ajout avec quantité : aucun doublon, quantité mise à jour (2)",
            len(r3) == 1 and r3[0]["quantity"] == 2,
            str(r3),
        )

        page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'c1', name: 'Beurre', quantity: null, unit: 'g', checked: true });
                state.shopping = await storeAll('shopping');
            }
            """
        )
        r4 = page.evaluate(
            """
            async () => {
                await addRecipeToShoppingSilent({ ingredients: [{ name: 'Beurre', quantity: null, unit: 'g' }] }, 1);
                return await storeAll('shopping');
            }
            """
        )
        check(
            "Un article coché du même nom n'est pas réutilisé : un 2e article (non coché) est créé",
            len(r4) == 2 and any(x["checked"] for x in r4) and any(not x["checked"] for x in r4),
            str(r4),
        )

        print("\n=== addRecipeToShopping (bouton 'Ajouter aux courses' d'une fiche recette) ===\n")
        page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const p2 of await storeAll('pantry')) await storeDelete('pantry', p2.id);
                state.pantry = [];
                await storePut('shopping', { id: 'e4', name: 'Basilic', quantity: null, unit: 'pièce', checked: false });
                state.shopping = await storeAll('shopping');
            }
            """
        )
        page.evaluate(
            """
            async () => {
                await addRecipeToShopping({ ingredients: [{ name: 'Basilic', quantity: null, unit: 'pièce' }] }, 4);
            }
            """
        )
        page.wait_for_timeout(300)
        r5 = page.evaluate("() => storeAll('shopping')")
        check("Même correctif dans addRecipeToShopping : aucun doublon", len(r5) == 1, str(r5))

        print("\n=== Scénario réel de bout en bout : recette ajoutée à une liste déjà existante ===\n")
        page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('shopping', { id: 'existing-sel', name: 'Sel', quantity: null, unit: 'pièce', checked: false });
                await storePut('shopping', { id: 'existing-lait', name: 'Lait', quantity: 1, unit: 'L', checked: false });
                await storePut('recipes', {
                    id: 'r1', name: 'Gratin', category: 'Plat', defaultPersons: 4,
                    ingredients: [
                        { name: 'Sel', quantity: null, unit: 'pièce' },
                        { name: 'Lait', quantity: 0.25, unit: 'L' },
                        { name: 'Pomme de terre', quantity: 250, unit: 'g' },
                    ],
                });
                state.shopping = await storeAll('shopping');
                state.recipes = await storeAll('recipes');
                state.currentRecipeId = 'r1';
                state.viewPersons = 4;
                state.screen = 'recipe';
                render();
            }
            """
        )
        page.wait_for_timeout(300)
        page.click("text=Ajouter aux courses")
        page.wait_for_timeout(400)
        final_shopping = page.evaluate("() => storeAll('shopping')")
        names = sorted(x["name"] for x in final_shopping)
        sel_count = sum(1 for x in final_shopping if x["name"] == "Sel")
        lait_item = next((x for x in final_shopping if x["name"] == "Lait"), None)
        check("Aucun doublon de 'Sel' (sans quantité) après ajout de la recette", sel_count == 1, str(final_shopping))
        check(
            "'Lait' (avec quantité) est bien cumulé (1L existant + 1L ajouté = 2L), pas dupliqué",
            lait_item is not None and lait_item["quantity"] == 2,
            str(lait_item),
        )
        check("'Pomme de terre' (nouvel ingrédient) a bien été ajoutée", "Pomme de terre" in names, str(names))
        check("Exactement 3 articles au total (pas de doublon supplémentaire)", len(final_shopping) == 3, str(names))

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
