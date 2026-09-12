#!/usr/bin/env python3
"""
Test permanent pour le rappel de sauvegarde de l'écran d'accueil —
urgence progressive (3 paliers) et partage en un clic. Voir
TESTS_NON_REGRESSION.md, point 61.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_backup_reminder.py

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


def setup_sample_recipe(page):
    page.evaluate(
        """
        async () => {
            await storePut('recipes', { id: 'r1', name: 'Test', category: 'Plat', ingredients: [], description: '', notes: '', personalRating: 0, photo: null, createdAt: '2026-01-01T00:00:00.000Z', cookLog: [], timesCooked: 0, defaultPersons: 4 });
            state.recipes = await storeAll('recipes');
        }
        """
    )


def set_days_since_backup(page, days_ago):
    page.evaluate(
        f"""
        () => {{
            const d = new Date();
            d.setDate(d.getDate() - {days_ago});
            localStorage.setItem('lastBackupAt', d.toISOString());
            reminderFileCache.file = null; reminderFileCache.builtAt = 0;
            state.screen = 'home';
            render();
        }}
        """
    )


def get_reminder(page):
    return page.evaluate(
        """
        () => {
            const els = Array.from(document.querySelectorAll('div')).filter(d => d.textContent.includes('sauvegard') && d.style.cursor === 'pointer');
            if (!els.length) return { found: false };
            return { found: true, text: els[0].textContent.trim(), border: els[0].style.border || null };
        }
        """
    )


def main():
    port = find_free_port()
    httpd = start_local_server(port)
    base_url = f"http://127.0.0.1:{port}/index.html"

    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => { setLang('fr'); }")
        setup_sample_recipe(page)
        page.wait_for_timeout(300)

        print("=== Aucun rappel avant 14 jours ===\n")
        set_days_since_backup(page, 5)
        r = get_reminder(page)
        ok = not r["found"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {r}")
        if not ok:
            all_ok = False
        print()

        print("=== Palier neutre (14-30 jours), pas de bordure ===\n")
        set_days_since_backup(page, 20)
        r = get_reminder(page)
        ok = r["found"] and not r["border"] and "Ça fait un moment" in r["text"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {r}")
        if not ok:
            all_ok = False
        print()

        print("=== Palier urgent (30-60 jours), bordure accent ===\n")
        set_days_since_backup(page, 40)
        r = get_reminder(page)
        ok = r["found"] and r["border"] and "accent" in r["border"] and "plus d'un mois" in r["text"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {r}")
        if not ok:
            all_ok = False
        print()

        print("=== Palier critique (60+ jours), bordure danger ===\n")
        set_days_since_backup(page, 75)
        r = get_reminder(page)
        ok = r["found"] and r["border"] and "danger" in r["border"] and "deux mois" in r["text"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {r}")
        if not ok:
            all_ok = False
        print()

        print("=== Fichier préparé en arrière-plan avant tout clic ===\n")
        set_days_since_backup(page, 20)
        page.wait_for_timeout(500)
        result = page.evaluate("() => ({ fileReady: reminderFileCache.file !== null })")
        ok = result["fileReady"]
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {result}")
        if not ok:
            all_ok = False
        print()

        print("=== Clic sans canShare : repli sur l'écran Sauvegarde ===\n")
        page.evaluate(
            """
            () => {
                const els = Array.from(document.querySelectorAll('div')).filter(d => d.textContent.includes('sauvegard') && d.style.cursor === 'pointer');
                els[0].click();
            }
            """
        )
        page.wait_for_timeout(300)
        result = page.evaluate("() => ({ screen: state.screen })")
        ok = result["screen"] == "backup"
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {result}")
        if not ok:
            all_ok = False
        print()

        browser.close()

    httpd.shutdown()

    print("Erreurs JS sur tout le parcours:", errors if errors else "AUCUNE")
    if errors:
        all_ok = False

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "AU MOINS UN ÉCHEC — voir le détail ci-dessus")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
