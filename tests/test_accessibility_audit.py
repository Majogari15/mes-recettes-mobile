#!/usr/bin/env python3
"""Test permanent : audit d'accessibilité automatisé (axe-core) sur les
écrans principaux de l'application (voir TESTS_NON_REGRESSION.md point
90 — audit étendu couvrant les manques identifiés par rapport à une
checklist QA générique : accessibilité, performance, compatibilité,
réseau, dépendances).

axe-core (bibliothèque MIT de Deque Systems, vendue ici uniquement pour
les tests — jamais chargée par l'application elle-même, voir
tests/vendor/axe.min.js) est injecté dans la page réelle et exécuté sur
chaque écran, dans les 2 thèmes (clair/sombre). Seules les violations de
gravité "serious" ou "critical" font échouer ce test : les violations
"moderate"/"minor" sont notées mais ne bloquent pas, pour éviter le bruit
des faux positifs fréquents d'axe-core sur des composants dynamiques.

Ceci ne remplace PAS un vrai test avec un lecteur d'écran (VoiceOver/
TalkBack) sur un appareil réel — voir la limite documentée au point 90.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_accessibility_audit.py

Code de sortie : 0 si aucune violation serious/critical, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCREENS = [
    "home", "recipes", "form", "recipe", "shopping", "pantry",
    "ingredients", "planning", "diagnostic", "backup", "statistics",
    "trash", "importUrl",
]


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
        page = browser.new_page(viewport={"width": 390, "height": 844})
        # Bug pré-existant découvert en vérifiant ce test (indépendant du
        # remplacement des icônes emoji par du SVG, confirmé en reproduisant
        # l'échec intermittent sur le code non modifié via "git stash") :
        # l'animation d'entrée des modales (modal-fade-in, 0.18s — voir
        # styles.css) entre en course avec le court délai fixe attendu
        # avant chaque appel à axe.run(), qui pouvait donc mesurer le
        # contraste couleur EN PLEIN FONDU (opacité < 1), déclenchant une
        # fausse alerte "color-contrast" un essai sur deux environ.
        # L'application respecte déjà "prefers-reduced-motion" (voir la
        # règle globale dans styles.css) — on demande donc ici la même
        # préférence pour que ce test mesure toujours le contraste final,
        # jamais un état transitoire de l'animation.
        page.emulate_media(reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")
        page.evaluate(
            """
            async () => {
                const recipe = {
                    id: 'a11y-1', name: 'Recette test', category: 'Plat',
                    persons: 2, ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }],
                    steps: 'Etape 1', prepTime: 10, cookTime: 20,
                };
                await storePut('recipes', recipe);
                state.recipes = await storeAll('recipes');
                state.viewingRecipeId = 'a11y-1';
                state.editingRecipeId = 'a11y-1';

                // Articles de garde-manger avec une date de péremption
                // proche/dépassée : sans ça, ni l'écran 'pantry' ni le
                // bandeau de rappel de l'accueil ne sont jamais exercés
                // avec de vraies données par cette boucle (voir point 94 —
                // un premier passage sur écran vide avait déjà laissé
                // passer un vrai défaut de contraste ailleurs, point 91).
                await storePut('pantry', { id: 'a11y-pantry-1', name: 'Lait', quantity: 1, unit: 'L', expirationDate: '2020-01-01' });
                await storePut('pantry', { id: 'a11y-pantry-2', name: 'Riz', quantity: 1, unit: 'kg', expirationDate: '2030-01-01' });
                state.pantry = await storeAll('pantry');
            }
            """
        )

        # add_script_tag(path=...) injecte le script en ligne (inline),
        # ce que bloque la Content-Security-Policy stricte de
        # l'application (script-src 'self', volontaire — voir point 82).
        # On le sert donc comme un vrai fichier same-origin via le
        # serveur de test local, ce que 'self' autorise.
        page.add_script_tag(url=f"http://127.0.0.1:{port}/tests/vendor/axe.min.js")

        totals = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}

        for theme in ("light", "dark"):
            page.evaluate(
                "(theme) => document.documentElement.setAttribute('data-theme', theme)",
                theme,
            )
            for screen in SCREENS:
                page.evaluate(
                    """
                    (screen) => {
                        state.screen = screen;
                        try { render(); } catch (e) { /* révélé par pageerror */ }
                    }
                    """,
                    screen,
                )
                page.wait_for_timeout(150)
                try:
                    result = page.evaluate(
                        """
                        async () => {
                            const r = await axe.run(document, {
                                resultTypes: ['violations'],
                            });
                            return r.violations.map(v => ({
                                id: v.id, impact: v.impact, nodes: v.nodes.length,
                                help: v.help,
                            }));
                        }
                        """
                    )
                except Exception as e:
                    check(f"axe.run() sur écran '{screen}' ({theme})", False, str(e))
                    continue

                blocking = [v for v in result if v["impact"] in ("critical", "serious")]
                for v in result:
                    if v["impact"] in totals:
                        totals[v["impact"]] += 1

                detail = "; ".join(f"{v['id']} ({v['impact']}, {v['nodes']} nœud(s))" for v in blocking)
                check(f"Écran '{screen}' ({theme}) : pas de violation critique/sérieuse", not blocking, detail)

            # Bandeaux transitoires (mise à jour disponible, proposition
            # d'installation) : n'apparaissent que dans des conditions
            # précises (nouvelle version détectée, événement natif
            # beforeinstallprompt) — absents du parcours écran par écran
            # ci-dessus, ce qui a permis à un vrai défaut de contraste de
            # rester invisible une première fois (voir point 90). Rendu
            # forcé ici pour ne plus jamais les manquer.
            page.evaluate("(s) => { state.screen = s; state.updateAvailable = true; render(); }", "home")
            page.wait_for_timeout(150)
            banner_result = page.evaluate(
                """
                async () => {
                    const r = await axe.run(document, { resultTypes: ['violations'] });
                    return r.violations.filter(v => v.impact === 'critical' || v.impact === 'serious')
                        .map(v => v.id);
                }
                """
            )
            check(f"Bandeau 'mise à jour disponible' ({theme}) : pas de violation critique/sérieuse", not banner_result, str(banner_result))
            page.evaluate("() => { state.updateAvailable = false; render(); }")

            page.evaluate(
                """
                () => {
                    const banner = document.createElement('div');
                    banner.className = 'install-banner';
                    banner.innerHTML = '<div class="text"><strong>Test</strong><span>desc</span></div>'
                        + '<button class="btn-install">Installer</button>'
                        + '<button class="btn-dismiss">Non merci</button>';
                    document.getElementById('app').appendChild(banner);
                }
                """
            )
            page.wait_for_timeout(150)
            install_result = page.evaluate(
                """
                async () => {
                    const r = await axe.run(document, { resultTypes: ['violations'] });
                    return r.violations.filter(v => v.impact === 'critical' || v.impact === 'serious')
                        .map(v => v.id);
                }
                """
            )
            check(f"Bandeau d'installation ({theme}) : pas de violation critique/sérieuse", not install_result, str(install_result))

            # Scan de code-barres (garde-manger, voir point 95) : sans
            # BarcodeDetector pour rester déterministe (pas de caméra
            # factice nécessaire ici, seul le rendu de la modale compte).
            page.evaluate("() => { delete window.BarcodeDetector; openBarcodeScanModal(); }")
            page.wait_for_timeout(150)
            barcode_scan_result = page.evaluate(
                """
                async () => {
                    const r = await axe.run(document, { resultTypes: ['violations'] });
                    return r.violations.filter(v => v.impact === 'critical' || v.impact === 'serious').map(v => v.id);
                }
                """
            )
            check(f"Modale de scan code-barres ({theme}) : pas de violation critique/sérieuse", not barcode_scan_result, str(barcode_scan_result))
            page.evaluate("() => { const o = document.querySelector('.modal-overlay'); if (o) o.remove(); openBarcodePasteModal(); }")
            page.wait_for_timeout(150)
            barcode_paste_result = page.evaluate(
                """
                async () => {
                    const r = await axe.run(document, { resultTypes: ['violations'] });
                    return r.violations.filter(v => v.impact === 'critical' || v.impact === 'serious').map(v => v.id);
                }
                """
            )
            check(f"Modale de saisie manuelle de code-barres ({theme}) : pas de violation critique/sérieuse", not barcode_paste_result, str(barcode_paste_result))
            page.evaluate("() => { const o = document.querySelector('.modal-overlay'); if (o) o.remove(); }")

        print(f"\nTotaux toutes gravités confondues (informatif) : {totals}")

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
