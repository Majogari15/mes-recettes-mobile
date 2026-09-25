"""
Vérifie l'avertissement d'ingrédient en double à l'enregistrement d'une
recette, demandé explicitement par l'utilisateur (voir TESTS_NON_REGRESSION.md
point 126) après avoir signalé qu'un import de recette depuis un lien externe
(exemple donné : un cassoulet Marmiton) peut produire un même ingrédient
présent deux fois dans la liste, sans aucun avertissement à l'enregistrement
— contrairement à l'application Windows, qui propose déjà "Garder tel quel"
ou "Fusionner" (quantités additionnées) dans ce cas précis.

Comportement repris à l'identique de la version Windows (voir
ask_merge_duplicate_ingredients/merge_duplicate_ingredients dans le dépôt de
l'app Windows) pour rester cohérent entre les deux applications :
- Détection insensible aux accents/casse (même fonction normalize() déjà
  utilisée ailleurs dans l'app pour comparer des noms d'ingrédients).
- La fusion ne combine que les lignes de MÊME nom ET MÊME unité — un même
  ingrédient dans deux unités différentes (ex. "Sel" en grammes et "Sel" en
  cuillères) n'est jamais fusionné automatiquement, additionner des unités
  différentes donnerait un nombre faux.
- Une quantité manquante (null) est traitée comme absente, pas comme zéro :
  la quantité connue l'emporte plutôt que d'annuler la somme.
- Annuler (Échap / clic hors de la fenêtre) n'enregistre rien, pour laisser
  revenir corriger manuellement.

Le lien Marmiton donné en exemple n'a pas pu être récupéré depuis cet
environnement (accès réseau bloqué vers ce domaine) — ce test reproduit
directement le cas via des ingrédients dupliqués injectés dans le
formulaire, ce qui suffit à vérifier le mécanisme lui-même (indépendant de
la source du duplicata, import ou saisie manuelle).
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

        def open_form_with_ingredients(ings):
            page.evaluate(
                """
                (ings) => {
                    for (const r of []) {}
                    state.screen = 'form';
                    state.editingRecipeId = null;
                    state.formIngredients = ings;
                    state.formAllergens = [];
                    state.formPhoto = null;
                    render();
                }
                """,
                ings,
            )

        def submit_and_wait_for_dialog():
            page.evaluate("() => document.querySelector('#f-name').value = 'Test doublon'")
            page.evaluate("() => document.querySelector('form').requestSubmit ? document.querySelector('form').requestSubmit() : document.querySelector('form').dispatchEvent(new Event('submit', {cancelable: true}))")

        print("=== 1. Deux lignes même nom/même unité -> la fenêtre de choix apparaît ===")
        page.evaluate("async () => { for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id); state.recipes = []; }")
        open_form_with_ingredients([
            {"name": "Oignon", "quantity": "100", "unit": "g"},
            {"name": "oignon", "quantity": "200", "unit": "g"},
        ])
        submit_and_wait_for_dialog()
        page.wait_for_timeout(300)
        r1 = page.evaluate(
            """
            () => {
                const msg = document.getElementById('custom-two-choice-message');
                return { shown: !!msg, text: msg ? msg.textContent : null };
            }
            """
        )
        check("la fenêtre de choix apparaît, mentionnant l'ingrédient en double", r1["shown"] and "ignon" in (r1["text"] or ""), json.dumps(r1, ensure_ascii=False))

        print("\n=== 2. Choisir 'Fusionner' -> quantités additionnées en une seule ligne ===")
        page.evaluate("() => document.getElementById('custom-two-choice-merge').click()")
        page.wait_for_timeout(300)
        r2 = page.evaluate(
            """
            async () => {
                const recipes = await storeAll('recipes');
                const r = recipes.find((x) => x.name === 'Test doublon');
                return r ? { count: r.ingredients.length, qty: r.ingredients[0].quantity, name: r.ingredients[0].name } : null;
            }
            """
        )
        check("fusion : une seule ligne, quantité 300", r2 and r2["count"] == 1 and r2["qty"] == 300, json.dumps(r2, ensure_ascii=False))

        print("\n=== 3. Choisir 'Garder tel quel' -> les deux lignes restent séparées ===")
        page.evaluate("async () => { for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id); state.recipes = []; }")
        open_form_with_ingredients([
            {"name": "Carotte", "quantity": "1", "unit": "pièce"},
            {"name": "Carotte", "quantity": "2", "unit": "pièce"},
        ])
        submit_and_wait_for_dialog()
        page.wait_for_timeout(300)
        page.evaluate("() => document.getElementById('custom-two-choice-keep').click()")
        page.wait_for_timeout(300)
        r3 = page.evaluate(
            """
            async () => {
                const recipes = await storeAll('recipes');
                const r = recipes.find((x) => x.name === 'Test doublon');
                return r ? { count: r.ingredients.length, quantities: r.ingredients.map((i) => i.quantity) } : null;
            }
            """
        )
        check("garder tel quel : deux lignes distinctes, quantités inchangées (1 et 2)", r3 and r3["count"] == 2 and r3["quantities"] == [1, 2], json.dumps(r3, ensure_ascii=False))

        print("\n=== 4. Annuler (Échap) -> rien n'est enregistré ===")
        page.evaluate("async () => { for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id); state.recipes = []; }")
        open_form_with_ingredients([
            {"name": "Poivron", "quantity": "1", "unit": "pièce"},
            {"name": "Poivron", "quantity": "1", "unit": "pièce"},
        ])
        submit_and_wait_for_dialog()
        page.wait_for_timeout(300)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        r4 = page.evaluate(
            """
            async () => {
                const recipes = await storeAll('recipes');
                return { count: recipes.length, dialogGone: !document.getElementById('custom-two-choice-message'), stillOnForm: state.screen === 'form' };
            }
            """
        )
        check("annulé : aucune recette enregistrée, toujours sur le formulaire", r4["count"] == 0 and r4["dialogGone"] and r4["stillOnForm"], json.dumps(r4, ensure_ascii=False))

        print("\n=== 5. Même nom, unités différentes -> fusionner ne combine PAS (unités incompatibles) ===")
        open_form_with_ingredients([
            {"name": "Sel", "quantity": "5", "unit": "g"},
            {"name": "Sel", "quantity": "1", "unit": "c. à café"},
        ])
        submit_and_wait_for_dialog()
        page.wait_for_timeout(300)
        page.evaluate("() => document.getElementById('custom-two-choice-merge').click()")
        page.wait_for_timeout(300)
        r5 = page.evaluate(
            """
            async () => {
                const recipes = await storeAll('recipes');
                const r = recipes.find((x) => x.name === 'Test doublon');
                return r ? { count: r.ingredients.length, units: r.ingredients.map((i) => i.unit) } : null;
            }
            """
        )
        check(
            "unités différentes : fusion demandée mais lignes restées séparées (jamais additionnées entre unités incompatibles)",
            r5 and r5["count"] == 2 and set(r5["units"]) == {"g", "c. à café"},
            json.dumps(r5, ensure_ascii=False),
        )

        print("\n=== 6. Quantité manquante sur une des deux lignes -> fusion garde la quantité connue ===")
        page.evaluate("async () => { for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id); state.recipes = []; }")
        open_form_with_ingredients([
            {"name": "Ail", "quantity": "", "unit": "gousse"},
            {"name": "Ail", "quantity": "3", "unit": "gousse"},
        ])
        submit_and_wait_for_dialog()
        page.wait_for_timeout(300)
        page.evaluate("() => document.getElementById('custom-two-choice-merge').click()")
        page.wait_for_timeout(300)
        r6 = page.evaluate(
            """
            async () => {
                const recipes = await storeAll('recipes');
                const r = recipes.find((x) => x.name === 'Test doublon');
                return r ? { count: r.ingredients.length, qty: r.ingredients[0].quantity } : null;
            }
            """
        )
        check("quantité manquante traitée comme absente : résultat = 3 (pas 0, pas doublé)", r6 and r6["count"] == 1 and r6["qty"] == 3, json.dumps(r6, ensure_ascii=False))

        print("\n=== 7. Aucun doublon -> enregistrement direct, pas de fenêtre ===")
        page.evaluate("async () => { for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id); state.recipes = []; }")
        open_form_with_ingredients([
            {"name": "Tomate", "quantity": "2", "unit": "pièce"},
            {"name": "Basilic", "quantity": "1", "unit": "bouquet"},
        ])
        submit_and_wait_for_dialog()
        page.wait_for_timeout(300)
        r7 = page.evaluate(
            """
            async () => {
                const recipes = await storeAll('recipes');
                return { count: recipes.length, dialogShown: !!document.getElementById('custom-two-choice-message') };
            }
            """
        )
        check("pas de doublon : enregistré directement, aucune fenêtre affichée", r7["count"] == 1 and not r7["dialogShown"], json.dumps(r7, ensure_ascii=False))

        check("Aucune erreur JS pendant tout le parcours", not errors, str(errors))

        print("\n=== Résumé ===")
        print("TOUT CORRECT" if all_ok else "AU MOINS UN ECHEC")
        browser.close()
    httpd.shutdown()
    return all_ok


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
