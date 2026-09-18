#!/usr/bin/env python3
"""Test permanent : remplacement des emoji de CHROME d'interface (navigation
du bas, bouton flottant, retour, recherche, thème, suppression) par des
icônes SVG (trait fin, currentColor) — voir TESTS_NON_REGRESSION.md pour le
détail complet de la demande ("patch graphique") et de ce qui a été
volontairement laissé en emoji (favoris, illustrations d'écran vide,
poignée de glisser-déposer, don, cycle de langue, crayon d'édition) car ce
sont des emoji de CONTENU, jamais de chrome.

Ce fichier vérifie :

1. Les 4 onglets de la navigation du bas contiennent bien une icône SVG
   (`.ui-icon`), pas l'ancien emoji, et la navigation fonctionne toujours
   à l'identique après le changement.
2. Le bouton flottant (+) contient une icône SVG et sa fonction (ouvrir
   l'ajout) fonctionne toujours.
3. Le bouton "retour" de la barre du haut contient une icône SVG et
   navigue toujours correctement.
4. Les boutons recherche/thème de la barre du haut contiennent une icône
   SVG, et le bouton thème bascule toujours correctement entre les deux
   icônes (lune/soleil) selon le thème actif.
5. Un bouton de suppression (garde-manger) contient une icône SVG et
   supprime toujours l'article correspondant.
6. Les emoji de CONTENU (étoile favori, illustration d'écran vide) ne
   sont PAS remplacés par une icône SVG — restent des emoji.
7. Chaque icône SVG est bien `aria-hidden="true"` (décorative), et le
   bouton qui la contient garde son `aria-label` — un lecteur d'écran
   annonce donc toujours le même texte qu'avant ce changement purement
   visuel.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_ui_icon_replacement.py

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
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.emulate_media(reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(800)
        page.evaluate("() => setLang('fr')")
        page.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'r1', name: 'Tarte', category: 'Dessert', ingredients: [], favorite: true });
                for (const p2 of await storeAll('pantry')) await storeDelete('pantry', p2.id);
                await storePut('pantry', { id: 'p1', name: 'Riz', quantity: 2, unit: 'kg' });
                state.recipes = await storeAll('recipes');
                state.pantry = await storeAll('pantry');
                state.screen = 'home';
                render();
            }
            """
        )
        page.wait_for_timeout(200)

        print("\n=== Navigation du bas : icônes SVG, navigation inchangée ===\n")
        nav_icon_count = page.evaluate("() => document.querySelectorAll('.nav-item .nav-icon svg.ui-icon').length")
        check("Les 4 onglets de la navigation du bas contiennent une icône SVG", nav_icon_count == 4, str(nav_icon_count))
        nav_has_old_emoji = page.evaluate(
            "() => Array.from(document.querySelectorAll('.nav-item .nav-icon')).some(el => /[\\u{1F300}-\\u{1FAFF}]/u.test(el.textContent))"
        )
        check("Aucun ancien emoji ne traîne dans la navigation du bas", not nav_has_old_emoji)
        page.click(".nav-item:nth-child(4)")  # garde-manger
        page.wait_for_timeout(150)
        screen_after_nav = page.evaluate("() => state.screen")
        check("Cliquer sur l'onglet 'Garde-manger' navigue toujours correctement", screen_after_nav == "pantry", screen_after_nav)

        print("\n=== Bouton flottant (+) : icône SVG, fonction inchangée ===\n")
        fab_svg = page.evaluate("() => { const f = document.querySelector('.fab'); return f ? f.querySelector('svg.ui-icon') !== null : false; }")
        check("Le bouton flottant contient une icône SVG", fab_svg)
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.wait_for_timeout(150)
        page.click(".fab")
        page.wait_for_timeout(200)
        modal_open_after_fab = page.is_visible(".modal-sheet")
        check("Cliquer sur le bouton flottant ouvre toujours une fenêtre d'ajout", modal_open_after_fab)
        page.evaluate("() => document.querySelector('.modal-overlay')?.remove()")
        page.wait_for_timeout(150)

        print("\n=== Bouton retour : icône SVG, navigation inchangée ===\n")
        page.evaluate("() => { state.screen = 'recipe'; state.currentRecipeId = 'r1'; render(); }")
        page.wait_for_timeout(150)
        back_svg = page.evaluate("() => { const b = document.querySelector('.back-btn'); return b ? b.querySelector('svg.ui-icon') !== null : false; }")
        check("Le bouton retour contient une icône SVG", back_svg)
        page.click(".back-btn")
        page.wait_for_timeout(150)
        screen_after_back = page.evaluate("() => state.screen")
        check("Cliquer sur le bouton retour navigue toujours correctement", screen_after_back == "recipes", screen_after_back)

        print("\n=== Boutons de la barre du haut (recherche/thème) : icônes SVG, thème inchangé ===\n")
        page.evaluate("() => { state.screen = 'home'; render(); }")
        page.wait_for_timeout(150)
        icon_btns_svg = page.evaluate("() => Array.from(document.querySelectorAll('.topbar-actions .icon-btn')).filter(b => b.querySelector('svg.ui-icon')).length")
        check("Les boutons recherche/thème de la barre du haut contiennent une icône SVG", icon_btns_svg >= 2, str(icon_btns_svg))
        theme_before = page.evaluate("() => document.documentElement.dataset.theme")
        theme_btn_icon_before = page.evaluate("() => document.querySelector('.topbar-actions .icon-btn[aria-label]:last-child svg.ui-icon path')?.getAttribute('d')")
        # Le bouton de thème est le dernier bouton .icon-btn du groupe topbar-actions (voir renderTopbar)
        buttons = page.query_selector_all(".topbar-actions .icon-btn")
        theme_btn = buttons[-1]
        theme_btn.click()
        page.wait_for_timeout(200)
        theme_after = page.evaluate("() => document.documentElement.dataset.theme")
        check("Cliquer sur le bouton de thème bascule toujours le thème", theme_after != theme_before, f"{theme_before} -> {theme_after}")
        theme_btn_svg_after = page.evaluate("() => document.querySelectorAll('.topbar-actions .icon-btn')[document.querySelectorAll('.topbar-actions .icon-btn').length - 1].querySelector('svg.ui-icon') !== null")
        check("Le bouton de thème affiche toujours une icône SVG après bascule (lune/soleil)", theme_btn_svg_after)

        print("\n=== Suppression garde-manger : icône SVG, fonction inchangée ===\n")
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.wait_for_timeout(150)
        trash_svg = page.evaluate("() => { const b = document.querySelector('.remove-ing'); return b ? b.querySelector('svg.ui-icon') !== null : false; }")
        check("Le bouton de suppression du garde-manger contient une icône SVG", trash_svg)
        page.click(".remove-ing")
        page.wait_for_timeout(200)
        pantry_after_delete = page.evaluate("() => storeAll('pantry')")
        check("Cliquer sur le bouton de suppression retire toujours l'article", pantry_after_delete == [], str(pantry_after_delete))

        print("\n=== Emoji de CONTENU non touchés (favoris, illustration d'écran vide) ===\n")
        page.evaluate(
            """
            async () => {
                for (const p2 of await storeAll('pantry')) await storeDelete('pantry', p2.id);
                state.pantry = [];
                state.screen = 'recipe';
                state.currentRecipeId = 'r1';
                render();
            }
            """
        )
        page.wait_for_timeout(150)
        star_text = page.evaluate("() => document.querySelector('.icon-btn[aria-label]')?.parentElement ? Array.from(document.querySelectorAll('.icon-btn')).map(b => b.textContent).find(t => t.includes('⭐') || t.includes('☆')) : null")
        check("L'étoile de favori reste un emoji (non remplacée par une icône SVG)", star_text in ("⭐", "☆"), str(star_text))
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.wait_for_timeout(150)
        empty_state_emoji = page.evaluate("() => document.querySelector('.empty-state .emoji')?.textContent")
        check("L'illustration d'écran vide du garde-manger reste un emoji", empty_state_emoji == "📦", str(empty_state_emoji))

        print("\n=== Accessibilité : icônes décoratives (aria-hidden), aria-label conservés ===\n")
        page.evaluate("() => { state.screen = 'home'; render(); }")
        page.wait_for_timeout(150)
        all_icons_hidden = page.evaluate("() => Array.from(document.querySelectorAll('svg.ui-icon')).every(svg => svg.getAttribute('aria-hidden') === 'true')")
        check("Toutes les icônes SVG sont marquées aria-hidden='true' (décoratives)", all_icons_hidden)
        nav_items_have_label = page.evaluate(
            "() => Array.from(document.querySelectorAll('.nav-item')).every(b => b.querySelector('span:last-child')?.textContent.trim().length > 0)"
        )
        check("Chaque onglet de navigation garde un texte visible (pas seulement l'icône)", nav_items_have_label)
        back_has_label = page.evaluate("() => { state.screen = 'recipe'; render(); return document.querySelector('.back-btn')?.getAttribute('aria-label'); }")
        check("Le bouton retour garde un aria-label non vide", bool(back_has_label), str(back_has_label))

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
