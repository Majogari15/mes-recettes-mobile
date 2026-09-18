#!/usr/bin/env python3
"""Test permanent : plusieurs recettes par repas dans le planning de la
semaine (entrée + plat + dessert...), suite au retour direct de
l'utilisateur — un déjeuner ou un dîner se compose en réalité d'au moins
3 recettes, jamais d'une seule.

Chaque case jour/repas (`state.weeklyPlan[jour][repas]`) contenait
auparavant UNE SEULE assignation ({recipeId, persons}). Elle contient
désormais un TABLEAU d'assignations, via `planSlotAssignments()` qui
accepte les deux formes (tableau ou objet unique) pour ne jamais casser
un planning/modèle/historique déjà enregistré avant ce changement —
aucune migration réécrivant le stockage n'a été faite, la case se
convertit simplement en tableau dès qu'elle est modifiée à nouveau.

Ce fichier vérifie :

1. On peut assigner plusieurs recettes (au moins 3) au même repas du même
   jour, chacune affichée sur sa propre ligne avec son propre bouton de
   suppression.
2. Supprimer UNE recette d'un repas à plusieurs recettes ne touche pas
   aux autres.
3. Supprimer la DERNIÈRE recette d'un repas retire bien la case
   (`delete`), plutôt que de laisser un tableau vide — sinon
   `planHasAnyAssignment()` la compterait à tort comme remplie.
4. Un ancien planning au format hérité (une seule assignation, pas un
   tableau) s'affiche toujours correctement, et se convertit proprement
   en tableau dès qu'une seconde recette y est ajoutée.
5. "Générer la liste de courses" ajoute bien les ingrédients de TOUTES
   les recettes d'un repas à plusieurs recettes, pas seulement la
   première.
6. L'archivage automatique dans l'historique (avant effacement) conserve
   la totalité des recettes assignées à un repas, pas seulement une.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_weekly_plan_multi_recipe.py

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

        print("=== Plusieurs recettes assignées au même repas (entrée + plat + dessert) ===\n")
        context1 = browser.new_context(viewport={"width": 390, "height": 900})
        page1 = context1.new_page()
        errors1 = []
        page1.on("pageerror", lambda exc: errors1.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(800)
        page1.evaluate("() => setLang('fr')")
        page1.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'entree', name: 'Salade', category: 'Entrée', ingredients: [{name:'Salade', quantity:1, unit:'pièce'}] });
                await storePut('recipes', { id: 'plat', name: 'Poulet', category: 'Plat', ingredients: [{name:'Poulet', quantity:1, unit:'pièce'}] });
                await storePut('recipes', { id: 'dessert', name: 'Tarte', category: 'Dessert', ingredients: [{name:'Farine', quantity:200, unit:'g'}] });
                state.recipes = await storeAll('recipes');
                state.weeklyPlan = {};
                state.screen = 'planning';
                render();
            }
            """
        )
        page1.wait_for_timeout(300)
        # Ajoute les 3 recettes au créneau "Déjeuner" du lundi (2e créneau du 1er jour)
        for name in ["Salade", "Poulet", "Tarte"]:
            page1.locator("#days-holder .card").first.get_by_text("+ Ajouter").nth(1).click()
            page1.wait_for_timeout(150)
            page1.locator("#picker-list .recipe-row", has_text=name).click()
            page1.wait_for_timeout(200)
        state_after_add = page1.evaluate("() => state.weeklyPlan['Lundi']['Déjeuner']")
        check(
            "Les 3 recettes sont bien assignées au créneau (tableau de 3 éléments)",
            isinstance(state_after_add, list) and len(state_after_add) == 3,
            str(state_after_add),
        )
        visible_names = [page1.is_visible(f"text={n}") for n in ["Salade", "Poulet", "Tarte"]]
        check("Les 3 recettes sont visibles à l'écran, chacune sur sa propre ligne", all(visible_names), str(visible_names))

        print("\n=== Supprimer une recette d'un repas à plusieurs recettes n'affecte pas les autres ===\n")
        # Les boutons de suppression du créneau "Déjeuner" (2e créneau) : on retire celui du milieu
        delete_buttons = page1.locator("#days-holder .card").first.locator("button[aria-label]")
        delete_buttons.nth(1).click()
        page1.wait_for_timeout(300)
        state_after_one_removed = page1.evaluate("() => state.weeklyPlan['Lundi']['Déjeuner']")
        check(
            "Il reste 2 recettes sur 3 après en avoir supprimé une",
            isinstance(state_after_one_removed, list) and len(state_after_one_removed) == 2,
            str(state_after_one_removed),
        )

        print("\n=== Supprimer la dernière recette d'un repas retire la case (pas un tableau vide) ===\n")
        for _ in range(2):
            page1.locator("#days-holder .card").first.locator("button[aria-label]").first.click()
            page1.wait_for_timeout(200)
        state_all_removed = page1.evaluate("() => state.weeklyPlan['Lundi']")
        check("La case 'Déjeuner' du lundi est bien retirée (pas laissée en tableau vide)", "Déjeuner" not in (state_all_removed or {}), str(state_all_removed))
        has_any = page1.evaluate("() => planHasAnyAssignment(state.weeklyPlan)")
        check("planHasAnyAssignment() ne compte plus le planning comme rempli", has_any is False, str(has_any))
        context1.close()

        print("\n=== Format hérité (une seule assignation, pas un tableau) toujours affiché et convertible ===\n")
        context2 = browser.new_context(viewport={"width": 390, "height": 900})
        page2 = context2.new_page()
        errors2 = []
        page2.on("pageerror", lambda exc: errors2.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(800)
        page2.evaluate("() => setLang('fr')")
        page2.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'legacy1', name: 'Ancienne recette', category: 'Plat', ingredients: [] });
                await storePut('recipes', { id: 'legacy2', name: 'Autre recette', category: 'Plat', ingredients: [] });
                state.recipes = await storeAll('recipes');
                state.weeklyPlan = { 'Mardi': { 'Dîner': { recipeId: 'legacy1', persons: 4 } } };
                state.screen = 'planning';
                render();
            }
            """
        )
        page2.wait_for_timeout(300)
        check("La recette au format hérité (objet unique) s'affiche correctement", page2.is_visible("text=Ancienne recette"))
        # Ajoute une 2e recette au même créneau (Mardi est le 2e jour, Dîner le 3e créneau)
        page2.locator("#days-holder .card").nth(1).get_by_text("+ Ajouter").nth(2).click()
        page2.wait_for_timeout(150)
        page2.locator("#picker-list .recipe-row", has_text="Autre recette").click()
        page2.wait_for_timeout(300)
        converted = page2.evaluate("() => state.weeklyPlan['Mardi']['Dîner']")
        check(
            "La case se convertit en tableau de 2 éléments après l'ajout, sans perdre l'ancienne recette",
            isinstance(converted, list) and len(converted) == 2 and converted[0]["recipeId"] == "legacy1" and converted[1]["recipeId"] == "legacy2",
            str(converted),
        )
        context2.close()

        print("\n=== Générer la liste de courses ajoute les ingrédients de TOUTES les recettes du repas ===\n")
        context3 = browser.new_context(viewport={"width": 390, "height": 900})
        page3 = context3.new_page()
        errors3 = []
        page3.on("pageerror", lambda exc: errors3.append(str(exc)))
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(800)
        page3.evaluate("() => setLang('fr')")
        page3.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                for (const s of await storeAll('shopping')) await storeDelete('shopping', s.id);
                await storePut('recipes', { id: 'entree', name: 'Salade', category: 'Entrée', ingredients: [{name:'Salade', quantity:1, unit:'pièce'}] });
                await storePut('recipes', { id: 'plat', name: 'Poulet', category: 'Plat', ingredients: [{name:'Poulet', quantity:1, unit:'pièce'}] });
                await storePut('recipes', { id: 'dessert', name: 'Tarte', category: 'Dessert', ingredients: [{name:'Farine', quantity:200, unit:'g'}] });
                state.recipes = await storeAll('recipes');
                state.weeklyPlan = { 'Lundi': { 'Déjeuner': [
                    { recipeId: 'entree', persons: 4 },
                    { recipeId: 'plat', persons: 4 },
                    { recipeId: 'dessert', persons: 4 },
                ] } };
                state.screen = 'planning';
                render();
            }
            """
        )
        page3.wait_for_timeout(300)
        page3.click("text=Générer la liste de courses")
        page3.wait_for_timeout(400)
        shopping_names = sorted(s["name"] for s in page3.evaluate("() => storeAll('shopping')"))
        check(
            "Les 3 ingrédients (entrée/plat/dessert) sont tous dans la liste de courses",
            shopping_names == ["Farine", "Poulet", "Salade"],
            str(shopping_names),
        )

        print("\n=== L'archivage dans l'historique conserve toutes les recettes d'un repas ===\n")
        page3.evaluate("() => { state.screen = 'planning'; render(); }")
        page3.wait_for_timeout(200)
        page3.click("text=Tout effacer")
        page3.wait_for_timeout(200)
        page3.click(".modal-overlay .btn-danger, .modal-overlay .btn-primary")
        page3.wait_for_timeout(300)
        history = page3.evaluate("() => state.planHistory")
        archived_assignments = (history[0]["plan"].get("Lundi", {}).get("Déjeuner", []) if history else [])
        check(
            "L'entrée d'historique créée avant l'effacement contient bien les 3 recettes",
            len(history) == 1 and len(archived_assignments) == 3,
            str(history),
        )
        context3.close()

        errors_all = errors1 + errors2 + errors3
        check("Aucune erreur JS pendant tout le parcours", not errors_all, "; ".join(errors_all))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
