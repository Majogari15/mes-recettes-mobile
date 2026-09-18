#!/usr/bin/env python3
"""Test permanent : suite à l'examen d'un paquet de fichiers "ui-kit"
proposé par une autre IA (tabbar/FAB/icônes SVG additifs) — voir
TESTS_NON_REGRESSION.md point 109 pour le détail complet de ce qui a été
écarté (conflits réels confirmés avec la navigation et le bouton flottant
déjà existants) et de ce qui a été retenu ici.

Ce fichier couvre les points effectivement retenus :

1. **Bug réel trouvé en cours d'examen, sans rapport avec le "ui-kit"** :
   le gestionnaire de suppression d'un article du garde-manger utilisait
   `row.querySelector("button")` sans classe précise — en mode tri
   manuel, la poignée de glisser-déposer (☰) est le premier <button> de
   la ligne, avant même le vrai bouton de suppression. Cliquer sur la
   poignée supprimait donc l'article au lieu de rien faire. Reproduit
   directement avant correction.
2. **Nouvelle fonctionnalité retenue de l'audit** : un article du
   garde-manger supprimé peut être restauré via un bandeau temporaire
   ("snackbar") avec un bouton "Annuler", plutôt qu'une simple
   suppression silencieuse sans aucun filet de sécurité. La suppression
   reste immédiate (comportement inchangé, jamais de confirmation
   bloquante) ; seule la restauration est nouvelle.
3. **Grille tablette pour la liste de recettes** — appliquée directement
   sur la vraie classe déjà utilisée (`.recipe-list`), pas sur une classe
   inventée qui n'existait dans aucun fichier réel du projet.
4. **Chevauchement visuel repéré sur une capture d'écran réelle** : le
   bouton flottant (+) et le nouveau snackbar occupent le même coin de
   l'écran — le bouton se masque maintenant pendant l'affichage du
   snackbar.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pantry_delete_undo_and_polish.py

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

        print("=== Bug corrigé : cliquer sur la poignée de tri manuel ne supprime plus l'article ===\n")
        context1 = browser.new_context(viewport={"width": 390, "height": 844})
        page1 = context1.new_page()
        errors1 = []
        page1.on("pageerror", lambda exc: errors1.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(800)
        page1.evaluate("() => setLang('fr')")
        page1.evaluate(
            """
            async () => {
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'handle-test', name: 'Riz', quantity: 1, unit: 'kg' });
                state.pantry = await storeAll('pantry');
                state.pantrySortBy = 'manual';
                state.screen = 'pantry';
                render();
            }
            """
        )
        page1.wait_for_timeout(200)
        page1.click(".drag-handle")
        page1.wait_for_timeout(300)
        after_handle_click = page1.evaluate("() => storeAll('pantry')")
        check(
            "L'article est toujours présent après un clic sur la poignée ☰",
            len(after_handle_click) == 1 and after_handle_click[0]["id"] == "handle-test",
            str(after_handle_click),
        )
        context1.close()

        print("\n=== Suppression du garde-manger : bandeau 'Annuler' restaure l'article avec toutes ses données ===\n")
        context2 = browser.new_context(viewport={"width": 390, "height": 844})
        page2 = context2.new_page()
        errors2 = []
        page2.on("pageerror", lambda exc: errors2.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(800)
        page2.evaluate("() => setLang('fr')")
        page2.evaluate(
            """
            async () => {
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'undo-test', name: 'Farine', quantity: 3, unit: 'kg', expirationDate: '2026-12-25', threshold: 1 });
                state.pantry = await storeAll('pantry');
                state.pantrySortBy = 'name';
                state.screen = 'pantry';
                render();
            }
            """
        )
        page2.wait_for_timeout(200)
        page2.click(".remove-ing")
        page2.wait_for_timeout(300)
        after_delete = page2.evaluate("() => storeAll('pantry')")
        check("L'article est bien supprimé immédiatement (comportement inchangé)", after_delete == [], str(after_delete))
        check("Le snackbar apparaît avec le nom de l'article", page2.is_visible("text=Farine supprimé du garde-manger."))
        check("Le bouton 'Annuler' est visible", page2.is_visible("text=Annuler"))
        page2.click(".snackbar-action")
        page2.wait_for_timeout(300)
        after_undo = page2.evaluate("() => storeAll('pantry')")
        check(
            "Après 'Annuler', l'article est restauré avec la MÊME quantité, unité, date et seuil (pas seulement le nom)",
            after_undo == [{"id": "undo-test", "name": "Farine", "quantity": 3, "unit": "kg", "expirationDate": "2026-12-25", "threshold": 1}],
            str(after_undo),
        )
        context2.close()

        print("\n=== Le snackbar disparaît seul après son délai, sans action de l'utilisateur ===\n")
        context3 = browser.new_context(viewport={"width": 390, "height": 844})
        page3 = context3.new_page()
        errors3 = []
        page3.on("pageerror", lambda exc: errors3.append(str(exc)))
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(800)
        page3.evaluate("() => setLang('fr')")
        page3.evaluate(
            """
            async () => {
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'timeout-test', name: 'Sucre', quantity: 1, unit: 'kg' });
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                render();
                // Raccourcit le délai réel (6s) pour un test rapide, en
                // appelant directement la fonction avec un délai court —
                // vérifie le mécanisme de disparition automatique
                // lui-même, pas la durée exacte choisie en production.
                showSnackbar('Test disparition automatique', { duration: 300 });
            }
            """
        )
        page3.wait_for_timeout(100)
        visible_before = page3.is_visible("#snackbar.show")
        page3.wait_for_timeout(400)
        visible_after = page3.is_visible("#snackbar.show")
        check("Le snackbar est bien visible juste après son affichage", visible_before)
        check("Le snackbar disparaît seul une fois son délai écoulé", not visible_after, f"avant={visible_before} après={visible_after}")
        context3.close()

        print("\n=== Le bouton flottant (+) se masque pendant l'affichage du snackbar (chevauchement visuel corrigé) ===\n")
        context4 = browser.new_context(viewport={"width": 390, "height": 844})
        page4 = context4.new_page()
        errors4 = []
        page4.on("pageerror", lambda exc: errors4.append(str(exc)))
        page4.goto(base_url, timeout=8000)
        page4.wait_for_timeout(800)
        page4.evaluate("() => setLang('fr')")
        page4.evaluate(
            """
            async () => {
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                await storePut('pantry', { id: 'fab-test', name: 'Lait', quantity: 1, unit: 'L' });
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                render();
            }
            """
        )
        page4.wait_for_timeout(200)
        fab_before = page4.evaluate("() => getComputedStyle(document.querySelector('.fab')).display")
        page4.click(".remove-ing")
        page4.wait_for_timeout(300)
        fab_during = page4.evaluate("() => getComputedStyle(document.querySelector('.fab')).display")
        check("Le bouton + est bien visible avant la suppression", fab_before != "none", fab_before)
        check("Le bouton + est masqué pendant l'affichage du snackbar (ne le chevauche plus)", fab_during == "none", fab_during)
        context4.close()

        print("\n=== Liste de recettes : grille à 2 colonnes sur un écran large, colonne unique sur mobile ===\n")
        context5 = browser.new_context()
        page5 = context5.new_page()
        errors5 = []
        page5.on("pageerror", lambda exc: errors5.append(str(exc)))
        page5.set_viewport_size({"width": 390, "height": 844})
        page5.goto(base_url, timeout=8000)
        page5.wait_for_timeout(800)
        page5.evaluate("() => setLang('fr')")
        page5.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'r1', name: 'Tarte', category: 'Dessert', ingredients: [] });
                state.recipes = await storeAll('recipes');
                state.screen = 'recipes';
                render();
            }
            """
        )
        page5.wait_for_timeout(300)
        display_mobile = page5.evaluate("() => getComputedStyle(document.querySelector('.recipe-list')).display")
        page5.set_viewport_size({"width": 900, "height": 800})
        page5.wait_for_timeout(200)
        display_tablet = page5.evaluate("() => getComputedStyle(document.querySelector('.recipe-list')).display")
        check("Sur mobile (390px), la liste reste en colonne unique (flex)", display_mobile == "flex", display_mobile)
        check("Sur écran large (900px), la liste passe en grille", display_tablet == "grid", display_tablet)
        context5.close()

        errors_all = errors1 + errors2 + errors3 + errors4 + errors5
        check("Aucune erreur JS pendant tout le parcours", not errors_all, "; ".join(errors_all))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
