#!/usr/bin/env python3
"""Test permanent : mesures de performance de base (démarrage, mémoire,
rendu avec un grand volume de données) — voir TESTS_NON_REGRESSION.md
point 90 (audit étendu, manque "performance/charge" identifié par
rapport à une checklist QA générique).

Ce n'est PAS un vrai test de charge ni de consommation batterie sur un
appareil réel (impossible à reproduire fidèlement dans cet
environnement) : seuils volontairement larges, pensés pour détecter une
RÉGRESSION FRANCHE (ex. un rendu qui devient accidentellement O(n²) et
prend 10x plus longtemps), pas pour certifier une performance absolue.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_performance_basic.py

Code de sortie : 0 si tous les seuils sont respectés, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading
import time

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_RECIPES = 300
N_INGREDIENTS = 500


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
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        print("=== Démarrage à froid (première ouverture, cache vide) ===\n")
        t0 = time.monotonic()
        page.goto(base_url, timeout=15000)
        page.wait_for_selector(".bottom-nav", timeout=15000)
        cold_start_s = time.monotonic() - t0
        check(
            "L'écran d'accueil et la barre de navigation s'affichent en moins de 5s",
            cold_start_s < 5,
            f"{cold_start_s:.2f}s",
        )

        page.evaluate("() => setLang('fr')")

        print("\n=== Injection d'un grand volume de données (300 recettes, 500 ingrédients) ===\n")
        seed_ms = page.evaluate(
            """
            async (n) => {
                const t0 = performance.now();
                const names = [];
                for (let i = 0; i < %d; i++) {
                    const name = `Ingrédient test ${i}`;
                    names.push(name);
                    await storePut('ingredients', { name, price: 1 + (i %% 5) });
                }
                for (let i = 0; i < n; i++) {
                    await storePut('recipes', {
                        id: `perf-${i}`,
                        name: `Recette de performance ${i}`,
                        category: ['Plat', 'Dessert', 'Apéro', 'Entrée'][i %% 4],
                        persons: 2 + (i %% 6),
                        ingredients: [
                            { name: names[i %% names.length], quantity: 2, unit: 'pièce' },
                            { name: names[(i + 1) %% names.length], quantity: 100, unit: 'g' },
                        ],
                        prepTime: 10 + (i %% 50),
                        favorite: i %% 7 === 0,
                    });
                }
                return performance.now() - t0;
            }
            """
            % N_INGREDIENTS,
            N_RECIPES,
        )
        print(f"  (Injection IndexedDB brute : {seed_ms:.0f} ms — non mesuré comme seuil, juste informatif)")

        print("\n=== Rendu de la liste de recettes avec ce volume ===\n")
        render_ms = page.evaluate(
            """
            async () => {
                state.recipes = await storeAll('recipes');
                state.ingredientNames = (await storeAll('ingredients')).map(i => i.name).sort();
                state.screen = 'recipes';
                const t0 = performance.now();
                render();
                return performance.now() - t0;
            }
            """
        )
        check(
            "Le rendu de la liste (300 recettes) prend moins de 1500 ms",
            render_ms < 1500,
            f"{render_ms:.0f} ms",
        )

        rendered_count = page.evaluate("() => document.querySelectorAll('.recipe-card, .recipe-list > *').length")
        check("Les 300 recettes sont bien présentes dans le DOM après rendu", rendered_count >= N_RECIPES - 5, f"{rendered_count} éléments")

        print("\n=== Mémoire JS après ce volume (indicatif, Chromium uniquement) ===\n")
        try:
            client = page.context.new_cdp_session(page)
            client.send("HeapProfiler.collectGarbage")
            metrics = client.send("Runtime.getHeapUsage")
            heap_mb = metrics["usedSize"] / (1024 * 1024)
            check(
                "Le tas JS utilisé reste sous 300 Mo avec ce volume de données",
                heap_mb < 300,
                f"{heap_mb:.1f} Mo",
            )
        except Exception as e:
            print(f"  (mesure mémoire indisponible dans cet environnement : {e})")

        print("\n=== Recherche/filtre sur ce volume (interaction typique) ===\n")
        filter_ms = page.evaluate(
            """
            () => {
                const t0 = performance.now();
                state.recipeCategoryFilter = 'Dessert';
                render();
                const dt = performance.now() - t0;
                state.recipeCategoryFilter = null;
                render();
                return dt;
            }
            """
        )
        check("Filtrer par catégorie sur ce volume prend moins de 800 ms", filter_ms < 800, f"{filter_ms:.0f} ms")

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
