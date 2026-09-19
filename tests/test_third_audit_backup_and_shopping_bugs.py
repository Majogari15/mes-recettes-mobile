#!/usr/bin/env python3
"""Test permanent : 6 bugs réels confirmés suite à un audit externe détaillé
d'une autre IA sur la v257 en ligne — chaque affirmation a été vérifiée
directement dans le vrai code avant correction (2 des 9 points soulevés se
sont révélés faux ou déjà corrigés, voir TESTS_NON_REGRESSION.md pour le
détail complet des 9 points et pourquoi).

1. **CRITIQUE — ZIP partagé "remplacer" supprimait les recettes
   restaurées si leur identifiant existait déjà localement**
   (`storeWriteManyAcrossStores`, utilisée par `restoreFromSharedZip`) :
   les écritures (`store.put`) passaient avant les suppressions
   (`store.delete`) dans la même transaction — une recette du ZIP dont
   l'identifiant existait déjà était donc écrite PUIS aussitôt effacée
   par la suppression de "tous les anciens identifiants" qui suit en
   mode remplacement. Le même défaut touchait aussi les ingrédients
   personnalisés et leurs réglages (même fonction, même cause). Corrigé
   en inversant l'ordre (suppressions avant écritures).
2. **IMPORTANT — Le ZIP partagé acceptait des recettes mal formées**
   (`recipeFromSharedFormat`) : un nom non textuel (ex. un nombre) ou un
   `null` au milieu du tableau d'ingrédients étaient acceptés tels
   quels, sans passer par la même validation que l'import JSON complet
   (`sanitizeBackupItem`, qui existait déjà mais n'était pas appelée sur
   ce chemin). Le nom non textuel faisait planter le tri alphabétique de
   la liste des recettes (`a.name.localeCompare` sur un nombre).
3. **IMPORTANT — Après une restauration JSON, plusieurs listes
   affichées restaient périmées** (`importAllData`) : les données
   étaient bien réécrites dans IndexedDB, mais l'état en mémoire
   (`state.menus`, `state.planTemplates`, `state.planHistory`,
   `state.trash`, `state.savedShoppingLists`, `state.weeklyPlan`)
   n'était rechargé qu'au tout premier démarrage de l'app, jamais après
   une restauration — l'écran pouvait donc afficher des éléments déjà
   supprimés ou masquer des éléments restaurés jusqu'au rechargement
   complet de la page.
4. **IMPORTANT — Un échec d'écriture pouvait laisser une quantité
   fictive dans les courses** (`addRecipeToShopping`,
   `addRecipeToShoppingSilent`, rappel "stock bas" de l'accueil) :
   la quantité en mémoire était incrémentée AVANT confirmation de
   l'écriture — un échec (quota IndexedDB dépassé...) laissait donc
   l'écran afficher une quantité jamais réellement enregistrée. Corrigé
   en construisant une copie, en l'écrivant, puis en ne mettant à jour
   l'objet en mémoire qu'après confirmation.
5. **MOYEN — Accessibilité de la liste de courses (et du garde-manger,
   même défaut, corrigé par cohérence)** : la case à cocher de chaque
   article n'avait pas de nom accessible la reliant à l'ingrédient
   (`aria-label` manquant), et le texte cliquable ouvrant la
   modification était un `<span>` — ni focalisable ni activable au
   clavier. Corrigés (aria-label sur la case, `<span>` remplacé par un
   vrai `<button>`).
6. **RISQUE TECHNIQUE — Certaines écritures du cache du service worker
   n'étaient pas attendues** (`sw.js`) : 2 des 3 branches de
   l'écouteur "fetch" lançaient `cache.put()` sans l'envelopper dans
   `event.waitUntil()` (seule la branche "données de référence"
   l'utilisait déjà) — un navigateur pouvait donc couper le service
   worker avant la fin de l'écriture, faisant manquer une ressource lors
   du prochain usage hors ligne. Corrigé pour les 2 branches restantes.

**3 points soulevés mais NON corrigés, vérifiés faux ou hors du périmètre
d'un vrai bug** (voir TESTS_NON_REGRESSION.md pour le détail) :
- La fusion des courses "perdant" une quantité non précisée est le
  comportement voulu du point précédent (114), pas un bug — discuté avec
  l'utilisateur plutôt que re-modifié unilatéralement.
- Le convertisseur d'unités assimilant litres et kilogrammes est une
  limitation délibérée et documentée dans le code (comme la version
  bureau), pas un défaut caché.
- L'aide à la sauvegarde suggérant un bouton "Partager" absent est
  FAUSSE : le texte d'aide est déjà conditionné exactement comme le
  bouton lui-même dans le vrai code (vérifié, aucune des deux sections
  concernées ne montre le texte sans le bouton).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_third_audit_backup_and_shopping_bugs.py

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

        print("=== 1. CRITIQUE : ZIP partagé 'remplacer' avec identifiant commun ===\n")
        r1 = page.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                const existing = { id: 'shared-id-1', name: 'Tarte', category: 'Dessert', ingredients: [], defaultPersons: 4 };
                await storePut('recipes', existing);
                state.recipes = await storeAll('recipes');
                const zipRecipe = (await recipeToSharedFormat({ ...existing, name: 'Tarte (mise à jour)' })).json;
                const entries = [{ name: 'recipes.json', data: utf8Encode(JSON.stringify([zipRecipe])) }];
                const zipBuffer = await buildZipFile(entries);
                const file = new File([zipBuffer], 'partage.zip', { type: 'application/zip' });
                await restoreFromSharedZip(file, false);
                return await storeAll('recipes');
            }
            """
        )
        check(
            "La recette avec un identifiant commun survit, avec le contenu importé (pas supprimée)",
            len(r1) == 1 and r1[0]["id"] == "shared-id-1" and r1[0]["name"] == "Tarte (mise à jour)",
            str(r1),
        )

        print("\n=== 1bis. Ingrédients personnalisés : même défaut, même correctif ===\n")
        r1b = page.evaluate(
            """
            async () => {
                for (const o of await storeAll('ingredientOverrides')) await storeDelete('ingredientOverrides', o.name);
                await storePut('ingredientOverrides', { name: 'Farine T55', priceEstimate: 1.2 });
                const overridesDict = { 'Farine T55': { name: 'Farine T55', priceEstimate: 2.5 } };
                const entries = [{ name: 'ingredient_custom_data.json', data: utf8Encode(JSON.stringify(overridesDict)) }];
                const zipBuffer = await buildZipFile(entries);
                const file = new File([zipBuffer], 'partage.zip', { type: 'application/zip' });
                await restoreFromSharedZip(file, false);
                return await storeAll('ingredientOverrides');
            }
            """
        )
        check(
            "Le réglage personnalisé avec un nom commun survit, avec la valeur importée",
            len(r1b) == 1 and r1b[0]["name"] == "Farine T55" and r1b[0]["priceEstimate"] == 2.5,
            str(r1b),
        )

        print("\n=== 2. Recette mal formée dans un ZIP partagé (nom numérique + ingrédient null) ===\n")
        r2 = page.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                const badRecipe = { id: 'bad-1', name: 123, category: 'Plat', ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }, null] };
                const entries = [{ name: 'recipes.json', data: utf8Encode(JSON.stringify([badRecipe])) }];
                const zipBuffer = await buildZipFile(entries);
                const file = new File([zipBuffer], 'partage.zip', { type: 'application/zip' });
                await restoreFromSharedZip(file, true);
                state.recipes = await storeAll('recipes');
                let sortError = null;
                try {
                    state.recipes.slice().sort((a, b) => a.name.localeCompare(b.name, 'fr'));
                } catch (e) {
                    sortError = e.message;
                }
                const stored = state.recipes.find((r) => r.id === 'bad-1');
                return { sortError, nameType: typeof (stored && stored.name), ingredientCount: stored ? stored.ingredients.length : null, hasNull: !!(stored && stored.ingredients.some((i) => i === null)) };
            }
            """
        )
        check("Le tri alphabétique ne plante pas (nom coercé en chaîne)", r2["sortError"] is None and r2["nameType"] == "string", str(r2))
        check("L'ingrédient 'null' est retiré plutôt que conservé tel quel", not r2["hasNull"] and r2["ingredientCount"] == 1, str(r2))

        print("\n=== 3. Collections en mémoire rechargées après une restauration JSON ===\n")
        r3 = page.evaluate(
            """
            async () => {
                for (const m of await storeAll('menus')) await storeDelete('menus', m.id);
                state.menus = [];
                state.planTemplates = [];
                state.savedShoppingLists = [];
                state.weeklyPlan = {};
                const backupData = {
                    recipes: [], shopping: [], pantry: [], ingredients: [], ingredientOverrides: [],
                    menus: [{ id: 'm1', name: 'Menu restauré', items: [] }],
                    planTemplates: [{ id: 'pt1', name: 'Modèle restauré', plan: {} }],
                    planHistory: [], trash: [],
                    savedShoppingLists: [{ id: 'sl1', name: 'Liste restaurée', items: [] }],
                    kv: [{ key: 'weeklyPlan', value: { 'Lundi': { 'Déjeuner': [{ recipeId: 'x', persons: 4 }] } } }],
                };
                await importAllData(backupData, 'replace');
                return {
                    menus: state.menus.map((m) => m.name),
                    planTemplates: state.planTemplates.map((t) => t.name),
                    savedShoppingLists: state.savedShoppingLists.map((s) => s.name),
                    weeklyPlan: state.weeklyPlan,
                };
            }
            """
        )
        check("state.menus rechargé après restauration", r3["menus"] == ["Menu restauré"], str(r3["menus"]))
        check("state.planTemplates rechargé après restauration", r3["planTemplates"] == ["Modèle restauré"], str(r3["planTemplates"]))
        check("state.savedShoppingLists rechargé après restauration", r3["savedShoppingLists"] == ["Liste restaurée"], str(r3["savedShoppingLists"]))
        check("state.weeklyPlan rechargé après restauration", "Lundi" in r3["weeklyPlan"], str(r3["weeklyPlan"]))

        print("\n=== 4. Échec d'écriture : pas de quantité fictive dans les courses ===\n")
        r4 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 'e1', name: 'Farine', quantity: 10, unit: 'g', checked: false });
                state.shopping = await storeAll('shopping');
                // addRecipeToShoppingSilent écrit désormais via
                // storeWriteManyAcrossStores (transaction atomique, voir
                // TESTS_NON_REGRESSION.md point 118) et non plus via
                // storePut directement — c'est donc ce point d'entrée
                // qu'il faut simuler en échec pour reproduire le même
                // scénario qu'avant ce correctif.
                const realWriteMany = window.storeWriteManyAcrossStores;
                window.storeWriteManyAcrossStores = () => Promise.reject(new Error('échec simulé'));
                let threw = false;
                try {
                    await addRecipeToShoppingSilent({ ingredients: [{ name: 'Farine', quantity: 10, unit: 'g' }] }, 1);
                } catch (e) { threw = true; }
                window.storeWriteManyAcrossStores = realWriteMany;
                return { threw, memQty: state.shopping.find((i) => i.id === 'e1').quantity, dbQty: (await storeAll('shopping')).find((i) => i.id === 'e1').quantity };
            }
            """
        )
        check(
            "La quantité en mémoire n'a pas bougé après un échec d'écriture (reste 10, pas 20)",
            r4["threw"] and r4["memQty"] == 10 and r4["dbQty"] == 10,
            str(r4),
        )

        print("\n=== 5. Accessibilité : case à cocher et bouton d'édition (courses + garde-manger) ===\n")
        r5 = page.evaluate(
            """
            async () => {
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('shopping', { id: 's1', name: 'Lait', quantity: 1, unit: 'L', checked: false });
                state.shopping = await storeAll('shopping');
                state.screen = 'shopping';
                render();
                await new Promise((r) => setTimeout(r, 100));
                const checkbox = document.querySelector('.shopping-item input[type=checkbox]');
                const label = document.querySelector('.shopping-item .label');
                return { checkboxAriaLabel: checkbox ? checkbox.getAttribute('aria-label') : null, labelTag: label ? label.tagName : null };
            }
            """
        )
        check("La case à cocher d'un article de courses a un aria-label nommant l'ingrédient", r5["checkboxAriaLabel"] and "Lait" in r5["checkboxAriaLabel"], str(r5))
        check("Le texte d'édition d'un article de courses est un vrai bouton (focalisable au clavier)", r5["labelTag"] == "BUTTON", str(r5))

        r5b = page.evaluate(
            """
            async () => {
                for (const p2 of await storeAll('pantry')) await storeDelete('pantry', p2.id);
                await storePut('pantry', { id: 'p1', name: 'Riz', quantity: 1, unit: 'kg' });
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                render();
                await new Promise((r) => setTimeout(r, 100));
                const label = document.querySelector('.shopping-item .label');
                return { labelTag: label ? label.tagName : null };
            }
            """
        )
        check("Le texte d'édition d'un article du garde-manger est aussi un vrai bouton (même correctif)", r5b["labelTag"] == "BUTTON", str(r5b))

        print("\n=== 6. Écritures de cache du service worker toutes protégées par event.waitUntil() ===\n")
        with open(os.path.join(PROJECT_ROOT, "sw.js")) as f:
            sw_src = f.read()
        unwrapped = sw_src.count("      caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));")
        wrapped = sw_src.count("event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone)))")
        check("Aucune écriture de cache non enveloppée dans event.waitUntil() ne subsiste", unwrapped == 0, f"non enveloppées={unwrapped}")
        check("Les 2 branches concernées utilisent bien event.waitUntil()", wrapped == 2, f"enveloppées={wrapped}")

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
