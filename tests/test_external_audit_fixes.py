#!/usr/bin/env python3
"""Test permanent : corrections suite à un audit externe (autre IA),
chaque point vérifié moi-même dans le code avant correction plutôt
qu'accepté tel quel (2 points de l'audit, sur les 9 soulevés, jugés
incorrects ou insuffisamment prouvés et volontairement écartés — voir
TESTS_NON_REGRESSION.md point 100) — voir aussi test_pwa_manifest.py
pour les points manifeste (orientation, captures "wide", favicon
32x32), traités séparément car déjà du ressort de ce fichier.

Couvre :
- Thème : suit la préférence système (prefers-color-scheme) au 1er
  lancement au lieu de forcer le clair, continue de la suivre en
  direct tant qu'aucun choix explicite n'a été fait, un choix explicite
  (interrupteur) prend définitivement le dessus, et la migration des
  utilisateurs déjà installés est sans surprise (un thème sombre déjà
  enregistré ne peut provenir que d'un vrai choix, jamais écrasé).
- Défilement : restauré au bouton "retour" (ex. liste de recettes ->
  fiche -> retour), jamais lors d'une navigation fraîche (barre du
  bas), qui repart toujours du haut comme avant.
- Cache du service worker : les fichiers JSON de référence
  (data/*.json) servent une version en cache immédiatement tout en la
  rafraîchissant en arrière-plan ("stale-while-revalidate"), sans
  attendre le réseau ni nécessiter de bump manuel de CACHE_NAME pour
  ces fichiers précis.
- Avertissement "économie de données" avant un téléchargement OCR
  (plusieurs Mo) si l'API Network Information le signale ET que le
  modèle de langue n'est pas déjà en cache — jamais bloquant.
- Initialisation idempotente (garde contre un double appel de init(),
  qui aurait sinon dupliqué les écouteurs globaux).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_external_audit_fixes.py

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

        print("=== Thème : 1er lancement, OS en mode sombre, aucune préférence enregistrée ===\n")
        context1 = browser.new_context(color_scheme="dark")
        page1 = context1.new_page()
        page1.on("pageerror", lambda exc: errors.append(str(exc)))
        page1.goto(base_url, timeout=8000)
        page1.wait_for_timeout(1000)
        check(
            "Le thème sombre est appliqué automatiquement (plus de clair forcé par défaut)",
            page1.evaluate("() => document.documentElement.dataset.theme") == "dark",
        )
        context1.close()

        print("\n=== Thème : 1er lancement, OS en mode clair ===\n")
        context2 = browser.new_context(color_scheme="light")
        page2 = context2.new_page()
        page2.on("pageerror", lambda exc: errors.append(str(exc)))
        page2.goto(base_url, timeout=8000)
        page2.wait_for_timeout(1000)
        check("Le thème clair est appliqué (cohérent avec l'OS)", page2.evaluate("() => document.documentElement.dataset.theme") == "light")

        print("\n=== Thème : suivi en direct d'un changement OS, sans choix explicite ===\n")
        page2.emulate_media(color_scheme="dark")
        page2.wait_for_timeout(300)
        check(
            "Le thème bascule automatiquement en sombre quand l'OS change pendant l'utilisation",
            page2.evaluate("() => document.documentElement.dataset.theme") == "dark",
        )

        print("\n=== Thème : un choix explicite (interrupteur) n'est plus jamais écrasé par l'OS ===\n")
        page2.evaluate("() => toggleTheme()")
        theme_after_toggle = page2.evaluate("() => document.documentElement.dataset.theme")
        page2.emulate_media(color_scheme="light" if theme_after_toggle == "dark" else "dark")
        page2.wait_for_timeout(300)
        check(
            "Le thème choisi explicitement reste inchangé malgré un nouveau changement de l'OS",
            page2.evaluate("() => document.documentElement.dataset.theme") == theme_after_toggle,
            f"choisi={theme_after_toggle}",
        )
        context2.close()

        print("\n=== Thème : migration — un thème 'dark' déjà enregistré (ne peut venir que d'un vrai choix) n'est jamais écrasé ===\n")
        context3 = browser.new_context(color_scheme="light")
        page3 = context3.new_page()
        page3.on("pageerror", lambda exc: errors.append(str(exc)))
        page3.add_init_script("localStorage.setItem('theme', 'dark')")
        page3.goto(base_url, timeout=8000)
        page3.wait_for_timeout(1000)
        check(
            "Reste en sombre malgré un OS en mode clair (migration sans surprise)",
            page3.evaluate("() => document.documentElement.dataset.theme") == "dark",
        )
        context3.close()

        print("\n=== Thème : migration — un thème 'light' déjà enregistré (ambigu, était le seul défaut possible) suit l'OS ===\n")
        context4 = browser.new_context(color_scheme="dark")
        page4 = context4.new_page()
        page4.on("pageerror", lambda exc: errors.append(str(exc)))
        page4.add_init_script("localStorage.setItem('theme', 'light')")
        page4.goto(base_url, timeout=8000)
        page4.wait_for_timeout(1000)
        check(
            "Bascule en sombre pour suivre l'OS (l'ancien 'light' était juste l'ancien défaut forcé, pas un choix prouvé)",
            page4.evaluate("() => document.documentElement.dataset.theme") == "dark",
        )
        context4.close()

        print("\n=== Défilement : restauré au bouton 'retour', jamais lors d'une navigation fraîche ===\n")
        context5 = browser.new_context(viewport={"width": 390, "height": 700})
        page5 = context5.new_page()
        page5.on("pageerror", lambda exc: errors.append(str(exc)))
        page5.goto(base_url, timeout=8000)
        page5.wait_for_timeout(1000)
        page5.evaluate("() => setLang('fr')")
        page5.evaluate(
            """
            async () => {
                const recipes = [];
                for (let i = 0; i < 30; i++) {
                    recipes.push({ id: 'r' + i, name: 'Recette numéro ' + String(i).padStart(2, '0'), category: 'Plat', ingredients: [{ name: 'Sel', quantity: 1, unit: 'pièce' }], createdAt: new Date().toISOString() });
                }
                for (const r of recipes) await storePut('recipes', r);
                state.recipes = await storeAll('recipes');
                state.screen = 'recipes';
                render();
            }
            """
        )
        page5.wait_for_timeout(300)
        page5.evaluate("() => window.scrollTo(0, 600)")
        page5.wait_for_timeout(200)
        page5.evaluate("() => { state.screen = 'recipe'; state.currentRecipeId = 'r15'; render(); }")
        page5.wait_for_timeout(200)
        check("La fiche recette s'ouvre toujours en haut", page5.evaluate("() => window.scrollY") == 0)
        page5.click(".back-btn")
        page5.wait_for_timeout(200)
        check(
            "Le clic sur 'retour' restaure la position de défilement de la liste quittée",
            page5.evaluate("() => window.scrollY") == 600,
            str(page5.evaluate("() => window.scrollY")),
        )
        page5.evaluate("() => { state.screen = 'recipe'; state.currentRecipeId = 'r20'; render(); }")
        page5.wait_for_timeout(200)
        page5.click("text=Recettes")
        page5.wait_for_timeout(200)
        check(
            "Une navigation fraîche (barre du bas) repart bien du haut (pas de restauration)",
            page5.evaluate("() => window.scrollY") == 0,
        )
        context5.close()

        print("\n=== Cache : les fichiers JSON de référence sont rafraîchis en arrière-plan (stale-while-revalidate) ===\n")
        context6 = browser.new_context()
        page6 = context6.new_page()
        page6.on("pageerror", lambda exc: errors.append(str(exc)))
        page6.goto(base_url, timeout=8000)
        sw_ready = False
        for _ in range(20):
            sw_ready = page6.evaluate("async () => { const r = await navigator.serviceWorker.ready; return !!r.active; }")
            if sw_ready:
                break
            page6.wait_for_timeout(300)
        check("Service worker actif avant le test de cache", sw_ready)
        swr_result = page6.evaluate(
            """
            async () => {
                const names = await caches.keys();
                let cacheName = null;
                for (const name of names) {
                    const c = await caches.open(name);
                    if (await c.match('./app.js')) { cacheName = name; break; }
                }
                if (!cacheName) return { error: 'cache introuvable' };
                const cache = await caches.open(cacheName);
                const dataUrl = './data/valeurs_nutritionnelles.json';
                // Injecte une valeur volontairement périmée, comme si le
                // vrai fichier avait changé depuis ce chargement en cache.
                await cache.put(dataUrl, new Response(JSON.stringify({ fake: 'stale-value-12345' }), { headers: { 'Content-Type': 'application/json' } }));
                const res1 = await fetch(dataUrl, { cache: 'no-store' });
                const immediate = await res1.text();
                await new Promise((r) => setTimeout(r, 800));
                const cachedAfter = await cache.match(dataUrl);
                const afterRevalidate = cachedAfter ? await cachedAfter.text() : null;
                return { immediate, afterRevalidate };
            }
            """
        )
        check(
            "La réponse immédiate est bien celle du cache (périmée), sans attendre le réseau",
            "stale-value-12345" in (swr_result.get("immediate") or ""),
            str(swr_result.get("immediate"))[:100],
        )
        check(
            "Le cache est rafraîchi en arrière-plan avec le vrai contenu (plus la valeur périmée)",
            swr_result.get("afterRevalidate") and "stale-value-12345" not in swr_result["afterRevalidate"],
            str(swr_result.get("afterRevalidate"))[:100],
        )
        context6.close()

        print("\n=== Avertissement 'économie de données' avant un téléchargement OCR ===\n")
        context7 = browser.new_context()
        page7 = context7.new_page()
        page7.on("pageerror", lambda exc: errors.append(str(exc)))
        page7.goto(base_url, timeout=8000)
        page7.wait_for_timeout(1000)
        page7.evaluate("() => setLang('fr')")
        page7.evaluate("() => { state.screen = 'importPhoto'; render(); }")
        page7.wait_for_timeout(300)
        check("Pas d'avertissement sans économie de données activée", not page7.is_visible("text=Économie de données"))
        page7.evaluate("() => { Object.defineProperty(navigator, 'connection', { value: { saveData: true }, configurable: true }); }")
        page7.evaluate("() => { state.screen = 'recipes'; render(); state.screen = 'importPhoto'; render(); }")
        page7.wait_for_timeout(400)
        check("Avertissement affiché : économie de données activée ET modèle non caché", page7.is_visible("text=Économie de données"))
        page7.evaluate(
            """
            async () => {
                const cache = await caches.open('fake-lang-cache-test');
                await cache.put('./lib/tesseract/lang/fra.traineddata.gz', new Response('fake'));
            }
            """
        )
        page7.evaluate("() => { state.screen = 'recipes'; render(); state.screen = 'importPhoto'; render(); }")
        page7.wait_for_timeout(400)
        check("Avertissement absent une fois le modèle déjà en cache", not page7.is_visible("text=Économie de données"))
        context7.close()

        print("\n=== Initialisation idempotente : un second appel à init() ne duplique aucun écouteur global ===\n")
        context8 = browser.new_context()
        page8 = context8.new_page()
        page8.on("pageerror", lambda exc: errors.append(str(exc)))
        page8.goto(base_url, timeout=8000)
        page8.wait_for_timeout(1000)
        listener_count = page8.evaluate(
            """
            async () => {
                let count = 0;
                const orig = document.addEventListener.bind(document);
                document.addEventListener = function (type, ...rest) {
                    if (type === 'visibilitychange') count++;
                    return orig(type, ...rest);
                };
                await init();
                document.addEventListener = orig;
                return count;
            }
            """
        )
        check("Aucun nouvel écouteur 'visibilitychange' posé par un second appel à init()", listener_count == 0, str(listener_count))
        context8.close()

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
