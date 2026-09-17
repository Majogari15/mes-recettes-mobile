#!/usr/bin/env python3
"""Test permanent pour la largeur des champs quantité/unité dans la ligne
d'ingrédient du formulaire de recette (voir audit complet, TESTS_NON_REGRESSION.md
points 82 et 84).

Point 82 : sur un écran de téléphone étroit, ces deux champs se
retrouvaient réduits à ~23px (juste la flèche du menu déroulant), rendant
la quantité et l'unité choisies invisibles à l'écran, alors même que les
valeurs étaient correctement enregistrées. Cause : `.autocomplete-wrap`
(qui enveloppe le champ nom, lui aussi flex dans la ligne) n'avait pas
`min-width: 0`, contrairement aux autres champs de la ligne — son minimum
automatique, piloté par la taille intrinsèque du <input> qu'il contient,
écrasait les voisins malgré leurs propres `min-width: 0`.

Point 84 (demande explicite) : la case quantité pouvait afficher ~7
caractères, plus que nécessaire — réduite à ~5, les décimales limitées à
3 pour l'affichage, l'icône de suppression réduite de 30 %, et l'espace
ainsi libéré donné au champ nom pour le rendre plus lisible.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_ingredient_row_layout.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Largeur minimale pour rester lisible : assez pour afficher les ~5
# caractères visés pour la quantité, et le début du libellé le plus long
# ("boîte"/"pièce"/etc., voir UNIT_OPTIONS) pour l'unité — pas besoin
# d'afficher le mot en entier (le <select> le tronque proprement), mais
# une largeur réduite à celle de la seule flèche (~20-25px, la régression
# du point 82) ne permet plus de distinguer la valeur choisie du tout.
MIN_QTY_WIDTH = 40
MIN_UNIT_WIDTH = 50
# Le bouton de suppression faisait 44px avant le point 84 (réduction de
# 30 % demandée) : 44 * 0.7 ≈ 31px. Marge de tolérance pour l'arrondi.
MAX_REMOVE_BUTTON_WIDTH = 32


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

        for width in (390, 320):
            page = browser.new_page(viewport={"width": width, "height": 844})
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(base_url, timeout=8000)
            page.wait_for_timeout(1000)
            page.evaluate("() => setLang('fr')")

            print(f"=== Ligne d'ingrédient à {width}px de large ===\n")
            page.evaluate(
                """
                async () => {
                    // Quantité à décimales longues : exerce à la fois la
                    // largeur réduite ET l'arrondi à 3 décimales pour
                    // l'affichage (point 84) dans le même cas de test.
                    const recipe = { id: 'layout-1', name: 'Test Layout', persons: 4, ingredients: [
                        { name: 'Farine de blé complet bio', quantity: 0.333333333, unit: 'c. à soupe' },
                    ] };
                    await storePut('recipes', recipe);
                    state.recipes = await storeAll('recipes');
                    await openRecipeForm('layout-1');
                    state.screen = 'form';
                    render();
                }
                """
            )
            page.wait_for_timeout(200)

            info = page.evaluate(
                """
                () => {
                    const row = document.querySelector('.ing-form-row');
                    const wrap = row.querySelector('.autocomplete-wrap');
                    const nameInput = wrap.querySelector('input');
                    const qty = row.querySelector('.ing-qty');
                    const unit = row.querySelector('.ing-unit');
                    const remove = row.querySelector('.remove-ing');
                    const qtyStyle = getComputedStyle(qty);
                    const ctx = document.createElement('canvas').getContext('2d');
                    ctx.font = `${qtyStyle.fontSize} ${qtyStyle.fontFamily}`;
                    const textWidth = ctx.measureText(qty.value).width;
                    return {
                        rowWidth: row.getBoundingClientRect().width,
                        rowScrollWidth: row.scrollWidth,
                        nameInputWidth: nameInput.getBoundingClientRect().width,
                        wrapWidth: wrap.getBoundingClientRect().width,
                        qtyWidth: qty.getBoundingClientRect().width,
                        qtyClientWidth: qty.clientWidth,
                        qtyTextWidth: textWidth,
                        unitWidth: unit.getBoundingClientRect().width,
                        removeWidth: remove.getBoundingClientRect().width,
                        qtyValue: qty.value,
                        unitValue: unit.value,
                    };
                }
                """
            )
            check(
                f"le champ quantité reste assez large pour afficher sa valeur ({MIN_QTY_WIDTH}px minimum)",
                info["qtyWidth"] >= MIN_QTY_WIDTH,
                str(info),
            )
            check(
                f"le menu déroulant d'unité reste assez large pour afficher l'unité choisie ({MIN_UNIT_WIDTH}px minimum)",
                info["unitWidth"] >= MIN_UNIT_WIDTH,
                str(info),
            )
            check(
                "le champ nom ne dépasse pas de sa propre enveloppe flex (plus de largeur intrinsèque figée)",
                abs(info["nameInputWidth"] - info["wrapWidth"]) < 1,
                str(info),
            )
            check(
                "la ligne ne déborde pas horizontalement de son propre conteneur",
                info["rowScrollWidth"] <= info["rowWidth"] + 1,
                str(info),
            )
            check(
                "la quantité affichée est bien arrondie à 3 décimales (0.333333333 -> 0.333)",
                info["qtyValue"] == "0.333",
                str(info),
            )
            check(
                "le texte affiché dans la case quantité n'est pas tronqué (les flèches natives ne volent plus de place)",
                info["qtyTextWidth"] <= info["qtyClientWidth"],
                str(info),
            )
            check(
                f"l'icône de suppression est bien réduite d'environ 30 % (<= {MAX_REMOVE_BUTTON_WIDTH}px, contre 44px avant)",
                info["removeWidth"] <= MAX_REMOVE_BUTTON_WIDTH,
                str(info),
            )
            check(
                "l'unité choisie reste correctement enregistrée (pas seulement invisible)",
                info["unitValue"] == "c. à soupe",
                str(info),
            )
            print()

            page.evaluate("async () => { await storeDelete('recipes', 'layout-1'); }")
            page.close()

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
