#!/usr/bin/env python3
"""Test permanent : "vague visuelle 1", 7 transformations graphiques
demandées explicitement par l'utilisateur suite au constat que le patch
graphique précédent (emoji -> icônes SVG) était quasi invisible sur
téléphone — voir TESTS_NON_REGRESSION.md pour le détail complet, y
compris les 2 écarts corrigés par rapport aux instructions transmises
(scoping de ".stat-row"/".recipe-name"/".recipe-thumb"/".recipe-info" à
".recipe-row" pour ne pas affecter la fenêtre de sélection de recette/
liste des menus/planning qui réutilisent les mêmes classes en tant que
petites icônes de liste ; badge de favori repensé en position absolue,
la mise en page en colonne l'aurait sinon repoussé sous le texte).

Ce fichier vérifie :

1. Les cartes de la liste de recettes ont bien une grande photo 16/9
   (au lieu d'une miniature 56×56), un titre en police Fraunces, et la
   grille 2 colonnes à partir de 720px reste fonctionnelle.
2. Le badge de favori reste visible et positionné sur la carte (pas
   perdu sous le texte) après le passage en mise en page colonne.
3. Les autres usages de .recipe-thumb/.recipe-info/.recipe-name (fenêtre
   de sélection de recette) ne sont PAS affectés par la transformation
   en carte — restent des miniatures compactes.
4. La barre du haut et la navigation du bas sont translucides
   (arrière-plan avec canal alpha, pas opaque) sans régression de
   contraste (voir le point ci-dessous).
5. L'onglet actif de la navigation du bas a bien un fond en pastille.
6. Le bloc de statistiques nutritionnelles (qui réutilise la même
   classe .stat-row que celui de la fiche recette, mais ailleurs sur
   l'écran) n'a PAS de marge négative — seul celui juste après
   .recipe-hero doit chevaucher la photo.
7. Les états vides ont un cercle coloré derrière l'emoji.
8. Audit d'accessibilité (axe-core) toujours au vert dans les deux
   thèmes — en particulier sur l'écran diagnostic, où un vrai bouton
   ".btn-primary" de couleur foncée se trouve juste derrière la
   navigation du bas translucide (c'est ce cas précis qui avait fait
   chuter le contraste sous le seuil AA avant l'ajustement de l'opacité
   de fond de .topbar/.bottom-nav).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_visual_wave_1.py

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
                state.recipes = await storeAll('recipes');
                state.screen = 'recipes';
                render();
            }
            """
        )
        page.wait_for_timeout(200)

        print("\n=== Cartes de recette : grande photo 16/9, titre Fraunces ===\n")
        thumb_style = page.evaluate(
            "() => { const t = document.querySelector('.recipe-row .recipe-thumb'); const cs = getComputedStyle(t); return { width: t.getBoundingClientRect().width, cardWidth: t.closest('.recipe-row').getBoundingClientRect().width, aspectRatio: cs.aspectRatio }; }"
        )
        check(
            "La photo de la carte occupe toute la largeur de la carte (pas une miniature 56px)",
            abs(thumb_style["width"] - thumb_style["cardWidth"]) <= 3,
            str(thumb_style),
        )
        name_font = page.evaluate("() => getComputedStyle(document.querySelector('.recipe-row .recipe-name')).fontFamily")
        check("Le titre de la carte utilise la police Fraunces", "Fraunces" in name_font, name_font)

        print("\n=== Badge de favori : reste visible et positionné sur la carte ===\n")
        star = page.query_selector(".recipe-star")
        star_box = star.bounding_box()
        row_box = page.query_selector(".recipe-row").bounding_box()
        check(
            "Le badge de favori reste dans les limites de la carte (pas repoussé sous le texte)",
            star_box is not None and row_box is not None and star_box["y"] >= row_box["y"] and star_box["y"] < row_box["y"] + row_box["height"],
            f"star={star_box} row={row_box}",
        )
        star_position = page.evaluate("() => getComputedStyle(document.querySelector('.recipe-star')).position")
        check("Le badge de favori est positionné en superposition (position: absolute)", star_position == "absolute", star_position)

        print("\n=== Grille 2 colonnes toujours fonctionnelle à 720px+ ===\n")
        page.set_viewport_size({"width": 900, "height": 800})
        page.wait_for_timeout(200)
        display_tablet = page.evaluate("() => getComputedStyle(document.querySelector('.recipe-list')).display")
        check("La liste passe toujours en grille à partir de 720px", display_tablet == "grid", display_tablet)
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(200)

        print("\n=== Les autres usages de .recipe-thumb (fenêtre de sélection) ne sont PAS transformés ===\n")
        page.evaluate("() => openRecipePickerModal(() => {})")
        page.wait_for_timeout(200)
        picker_thumb = page.evaluate(
            "() => { const t = document.querySelector('#picker-list .recipe-thumb'); return t ? t.getBoundingClientRect().width : null; }"
        )
        check(
            "La miniature de la fenêtre de sélection reste petite (56px), pas une grande photo",
            picker_thumb is not None and 50 <= picker_thumb <= 62,
            str(picker_thumb),
        )
        picker_name_font = page.evaluate(
            "() => { const n = document.querySelector('#picker-list .recipe-name'); return n ? getComputedStyle(n).fontFamily : null; }"
        )
        check(
            "Le nom dans la fenêtre de sélection n'utilise PAS Fraunces (police par défaut inchangée)",
            picker_name_font is not None and "Fraunces" not in picker_name_font,
            str(picker_name_font),
        )
        page.evaluate("() => document.querySelector('.modal-overlay')?.remove()")
        page.wait_for_timeout(150)

        print("\n=== Barres translucides ===\n")
        topbar_bg = page.evaluate("() => getComputedStyle(document.querySelector('.topbar')).backgroundColor")
        nav_bg = page.evaluate("() => getComputedStyle(document.querySelector('.bottom-nav')).backgroundColor")
        check("La barre du haut a un fond avec canal alpha (translucide)", "/ 0." in topbar_bg or "rgba" in topbar_bg, topbar_bg)
        check("La navigation du bas a un fond avec canal alpha (translucide)", "/ 0." in nav_bg or "rgba" in nav_bg, nav_bg)

        print("\n=== Onglet actif : pastille de fond ===\n")
        active_pill_bg = page.evaluate(
            "() => { const n = document.querySelector('.nav-item.active .nav-icon'); return n ? getComputedStyle(n).backgroundColor : null; }"
        )
        check("L'onglet actif a un fond de pastille (pas transparent)", active_pill_bg not in (None, "rgba(0, 0, 0, 0)"), str(active_pill_bg))

        print("\n=== .stat-row de la nutrition (hors fiche recette) : pas de marge négative ===\n")
        margin = page.evaluate(
            """
            () => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = '<div class="stat-row" style="margin-bottom:0;"><div class="stat-pill"><div class="value">1</div></div></div>';
                document.getElementById('app').appendChild(card);
                const sr = card.querySelector('.stat-row');
                const mt = getComputedStyle(sr).marginTop;
                card.remove();
                return mt;
            }
            """
        )
        check("Un .stat-row non précédé d'un .recipe-hero n'a pas de marge négative", margin == "0px", margin)

        print("\n=== États vides : cercle coloré derrière l'emoji ===\n")
        page.evaluate(
            """
            async () => {
                for (const p2 of await storeAll('pantry')) await storeDelete('pantry', p2.id);
                state.pantry = [];
                state.screen = 'pantry';
                render();
            }
            """
        )
        page.wait_for_timeout(150)
        emoji_style = page.evaluate(
            "() => { const e = document.querySelector('.empty-state .emoji'); const cs = getComputedStyle(e); return { borderRadius: cs.borderRadius, width: cs.width }; }"
        )
        check("L'illustration d'écran vide a un fond circulaire", emoji_style["borderRadius"] == "50%", str(emoji_style))

        print("\n=== Audit d'accessibilité : écran diagnostic (bouton foncé sous la nav translucide) ===\n")
        for theme in ("light", "dark"):
            page.evaluate("(t) => document.documentElement.setAttribute('data-theme', t)", theme)
            page.add_script_tag(url=f"http://127.0.0.1:{port}/tests/vendor/axe.min.js") if theme == "light" else None
            page.evaluate("(s) => { state.screen = s; render(); }", "diagnostic")
            page.wait_for_timeout(200)
            violations = page.evaluate(
                """
                async () => {
                    const r = await axe.run(document, { resultTypes: ['violations'] });
                    return r.violations.filter(v => v.impact === 'critical' || v.impact === 'serious').map(v => v.id);
                }
                """
            )
            check(f"Écran diagnostic ({theme}) : pas de violation critique/sérieuse (nav translucide sur bouton foncé)", not violations, str(violations))

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
