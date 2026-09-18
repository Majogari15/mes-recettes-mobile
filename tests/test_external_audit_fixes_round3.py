#!/usr/bin/env python3
"""Test permanent : troisième audit externe (deux autres IA), portant
sur la vraie atomicité de la restauration ZIP et la robustesse face à
une date de péremption invalide restaurée — chaque point vérifié
moi-même dans le code avant correction (voir TESTS_NON_REGRESSION.md
point 102).

Contexte : le point 101 (round 2) avait déjà rendu l'import ZIP
"tout-ou-rien" face à une donnée invalide détectée AVANT toute
écriture (ex. une recette malformée). Ce round-ci corrige deux
lacunes réelles que cette protection ne couvrait pas encore :

1. Une donnée de MAUVAISE FORME mais syntaxiquement valide en JSON
   (ex. `ingredients.json` = `{"bad": 1}` au lieu d'un tableau)
   n'était détectée que PENDANT l'écriture d'une section suivante,
   après que des sections précédentes avaient déjà été appliquées.
2. Même sans donnée invalide, un échec survenant PENDANT l'écriture
   elle-même (quota IndexedDB dépassé, panne...) pouvait laisser
   l'import à moitié appliqué : les écritures des différentes
   sections (recettes, ingrédients, garde-manger, personnalisations)
   se faisaient encore en plusieurs transactions IndexedDB
   indépendantes plutôt qu'une seule englobant tout.

`restoreFromSharedZip()` valide maintenant la FORME de chaque section
avant toute écriture, et applique toutes les écritures de toutes les
sections dans UNE SEULE transaction IndexedDB multi-entrepôts (voir
`storeWriteManyAcrossStores()`, déjà utilisée ailleurs dans l'app pour
le même besoin) : soit l'import entier s'applique, soit rien, quelle
que soit la cause de l'échec.

Couvre aussi :
- Une date de péremption restaurée qui n'est pas une vraie date
  (chaîne quelconque, ou une date calendaire impossible comme le 31
  février) ne fait plus planter l'affichage du garde-manger, et est
  nettoyée à l'import plutôt que stockée telle quelle.
- Le rafraîchissement en arrière-plan du cache (stale-while-revalidate)
  attend maintenant réellement la fin de l'écriture dans le cache
  avant de considérer le travail protégé par `waitUntil()` terminé.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_external_audit_fixes_round3.py

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
        errors = []

        print("=== ZIP : un échec pendant l'ÉCRITURE elle-même n'applique RIEN (vraie atomicité) ===\n")
        context1 = browser.new_context()
        page1 = context1.new_page()
        page1.on("pageerror", lambda exc: errors.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(500)
        result1 = page1.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'old-1', name: 'Ancienne recette', category: 'Plat', ingredients: [] });
                const entries = [
                    { name: 'recipes.json', data: new TextEncoder().encode(JSON.stringify([
                        { id: 'new-1', name: 'Nouvelle 1', category: 'Plat', ingredients: [] },
                        { id: 'new-2', name: 'Nouvelle 2', category: 'Plat', ingredients: [] },
                    ])) },
                ];
                const zipBlob = await buildZipFile(entries);
                const zipFile = new File([zipBlob], 'test.zip', { type: 'application/zip' });
                // Simule un échec d'ÉCRITURE (aucune donnée invalide ici) —
                // scénario que la validation seule (point 101) ne couvrait pas.
                const original = window.storeWriteManyAcrossStores;
                window.storeWriteManyAcrossStores = () => Promise.reject(new Error('simulated mid-write failure'));
                let errorCaught = null;
                try {
                    await restoreFromSharedZip(zipFile, false);
                } catch (e) {
                    errorCaught = String(e);
                }
                window.storeWriteManyAcrossStores = original;
                const names = (await storeAll('recipes')).map((r) => r.name);
                return { errorCaught, names };
            }
            """
        )
        check("Une erreur est bien levée", bool(result1["errorCaught"]), str(result1["errorCaught"]))
        check(
            "Aucune écriture appliquée du tout : l'ancienne recette reste seule, aucune nouvelle recette n'apparaît",
            result1["names"] == ["Ancienne recette"],
            str(result1["names"]),
        )
        context1.close()

        print("\n=== ZIP : une section de MAUVAISE FORME (JSON valide, structure inattendue) est rejetée AVANT toute écriture ===\n")
        context2 = browser.new_context()
        page2 = context2.new_page()
        page2.on("pageerror", lambda exc: errors.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(500)
        result2 = page2.evaluate(
            """
            async () => {
                for (const r of await storeAll('recipes')) await storeDelete('recipes', r.id);
                await storePut('recipes', { id: 'keep-1', name: 'À conserver', category: 'Plat', ingredients: [] });
                const entries = [
                    { name: 'recipes.json', data: new TextEncoder().encode(JSON.stringify([
                        { id: 'should-not-appear', name: 'Ne doit jamais apparaître', category: 'Plat', ingredients: [] },
                    ])) },
                    // Objet au lieu d'un tableau — JSON.parse ne s'en plaint
                    // pas, seule une vérification de forme explicite le
                    // détecte.
                    { name: 'ingredients.json', data: new TextEncoder().encode(JSON.stringify({ bad: 1 })) },
                ];
                const zipBlob = await buildZipFile(entries);
                const zipFile = new File([zipBlob], 'test2.zip', { type: 'application/zip' });
                let errorCaught = null;
                try {
                    await restoreFromSharedZip(zipFile, false);
                } catch (e) {
                    errorCaught = String(e);
                }
                const names = (await storeAll('recipes')).map((r) => r.name);
                return { errorCaught, names };
            }
            """
        )
        check("Une erreur explicite est levée pour la section mal formée", bool(result2["errorCaught"]), str(result2["errorCaught"]))
        check(
            "Aucune recette importée malgré la recette par ailleurs valide de la même archive",
            result2["names"] == ["À conserver"],
            str(result2["names"]),
        )
        context2.close()

        print("\n=== Date de péremption restaurée invalide : nettoyée à l'import, plus de plantage à l'affichage ===\n")
        context3 = browser.new_context()
        page3 = context3.new_page()
        page3.on("pageerror", lambda exc: errors.append(str(exc)))
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(1000)
        page3.evaluate("() => setLang('fr')")
        result3 = page3.evaluate(
            """
            async () => {
                for (const p of await storeAll('pantry')) await storeDelete('pantry', p.id);
                const backup = {
                    exportedAt: new Date().toISOString(),
                    version: 1,
                    recipes: [], ingredients: [], ingredientOverrides: [], menus: [],
                    planTemplates: [], planHistory: [], trash: [], savedShoppingLists: [], kv: [],
                    shopping: [],
                    pantry: [
                        { id: 'bad-date-1', name: 'Yaourt', quantity: 1, unit: 'pièce', expirationDate: 'not-a-date' },
                        { id: 'bad-date-2', name: 'Lait', quantity: 1, unit: 'L', expirationDate: '2026-02-31' },
                    ],
                };
                const file = new File([JSON.stringify(backup)], 'backup.json', { type: 'application/json' });
                const { data, report } = await parseBackupFile(file);
                await importAllData(data, 'merge');
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                let renderError = null;
                try {
                    render();
                } catch (e) {
                    renderError = String(e);
                }
                const stored = state.pantry.map((p) => ({ name: p.name, expirationDate: p.expirationDate }));
                return { renderError, stored, structuralFixes: report.structuralFixes };
            }
            """
        )
        check("L'affichage du garde-manger ne plante plus", not result3["renderError"], str(result3["renderError"]))
        check(
            "Les deux dates invalides ('not-a-date' et le 31 février inexistant) sont nettoyées à null, pas stockées telles quelles",
            all(p["expirationDate"] is None for p in result3["stored"]),
            str(result3["stored"]),
        )
        check("Le rapport d'import signale bien 2 corrections structurelles", result3["structuralFixes"] == 2, str(result3["structuralFixes"]))
        context3.close()

        print("\n=== Une date calendaire réellement impossible (31 février) n'est plus jamais acceptée silencieusement ===\n")
        context4 = browser.new_context()
        page4 = context4.new_page()
        page4.on("pageerror", lambda exc: errors.append(str(exc)))
        page4.goto(base_url, timeout=8000)
        page4.wait_for_timeout(500)
        result4 = page4.evaluate("() => parseCalendarDateLocal('2026-02-31')")
        check(
            "parseCalendarDateLocal('2026-02-31') renvoie null (plus de bascule silencieuse sur le 3 mars)",
            result4 is None,
            str(result4),
        )
        context4.close()

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
