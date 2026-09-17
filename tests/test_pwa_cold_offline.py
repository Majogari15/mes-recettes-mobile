#!/usr/bin/env python3
"""Test permanent : navigation hors-ligne "à froid" — pas seulement une
coupure réseau PENDANT une action (déjà couvert par
test_network_interruption.py), mais une vraie fermeture/réouverture de
l'application alors que le réseau est déjà coupé, une fois le service
worker installé et le cache rempli — voir TESTS_NON_REGRESSION.md
point 92.

Ne remplace pas un vrai test avion sur téléphone (comportement du
navigateur mobile réel face à un service worker existant peut varier
légèrement) mais vérifie la partie qui dépend du CODE de l'application :
le service worker sert bien l'app depuis le cache plutôt que de laisser
échouer la navigation.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pwa_cold_offline.py

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
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        print("=== Premier chargement en ligne : installation du service worker + remplissage du cache ===\n")
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(500)
        page.evaluate("() => setLang('fr')")

        sw_ready = page.evaluate(
            """
            async () => {
                if (!('serviceWorker' in navigator)) return { supported: false };
                const reg = await navigator.serviceWorker.ready;
                return { supported: true, active: !!reg.active };
            }
            """
        )
        check("Service worker supporté et actif", sw_ready.get("supported") and sw_ready.get("active"), str(sw_ready))

        # Le cache est peuplé dans le handler "install" (event.waitUntil) ;
        # on attend qu'il contienne bien les fichiers essentiels avant de
        # couper le réseau, plutôt qu'un délai fixe arbitraire.
        cache_filled = False
        for _ in range(20):
            has_app_js = page.evaluate(
                """
                async () => {
                    const names = await caches.keys();
                    for (const name of names) {
                        const cache = await caches.open(name);
                        if (await cache.match('./app.js')) return true;
                    }
                    return false;
                }
                """
            )
            if has_app_js:
                cache_filled = True
                break
            page.wait_for_timeout(300)
        check("Le cache du service worker contient bien app.js avant la coupure réseau", cache_filled)

        # Crée une recette pour vérifier que les DONNÉES (IndexedDB, pas
        # seulement le code de l'app) survivent aussi à un rechargement
        # hors-ligne.
        page.evaluate(
            """
            async () => {
                await storePut('recipes', { id: 'cold-1', name: 'Recette hors-ligne', category: 'Plat', ingredients: [{name:'Sel', quantity:1, unit:'pièce'}] });
            }
            """
        )

        print("\n=== Coupure réseau, puis rechargement complet de la page (simule une réouverture) ===\n")
        context.set_offline(True)
        page.reload(timeout=8000)
        page.wait_for_timeout(1000)

        app_shell_loaded = page.evaluate("() => !!document.getElementById('app') && document.getElementById('app').innerHTML.length > 0")
        check("La page se recharge avec le contenu de l'application (pas une page d'erreur navigateur)", app_shell_loaded)
        check("La barre de navigation est visible après un rechargement hors-ligne", page.is_visible(".bottom-nav"))

        page.evaluate("() => setLang('fr')")
        recipe_survived = page.evaluate(
            """
            async () => {
                const r = await storeAll('recipes');
                return r.some(x => x.id === 'cold-1');
            }
            """
        )
        check("Les données créées avant la coupure (IndexedDB) sont toujours là après le rechargement hors-ligne", recipe_survived)

        # Navigation vers une URL avec un paramètre jamais visitée avant
        # (proche d'un lien profond ouvert hors-ligne) : doit retomber sur
        # l'app via le repli de navigation du service worker, pas une
        # erreur réseau.
        try:
            page.goto(f"{base_url}?openRecipe=inexistant", timeout=8000)
            page.wait_for_timeout(500)
            deep_link_ok = page.evaluate("() => !!document.getElementById('app') && document.getElementById('app').innerHTML.length > 0")
        except Exception as e:
            deep_link_ok = False
            errors.append(f"navigation profonde hors-ligne : {e}")
        check("Une navigation vers une URL avec paramètre (jamais visitée) fonctionne aussi hors-ligne", deep_link_ok)

        context.set_offline(False)
        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
