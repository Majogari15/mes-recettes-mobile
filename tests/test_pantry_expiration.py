#!/usr/bin/env python3
"""Test permanent : date de péremption sur les articles du garde-manger
(demande explicite de l'utilisateur) — voir TESTS_NON_REGRESSION.md
point 94.

Couvre : ajout/modification via le vrai formulaire, affichage
coloré selon l'urgence (expiré / bientôt / lointain / sans date),
bandeau de rappel sur l'accueil, tri par date de péremption, et
survie du champ à un aller-retour de sauvegarde locale (JSON).

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_pantry_expiration.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import datetime
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


def iso_date(days_from_today):
    return (datetime.date.today() + datetime.timedelta(days=days_from_today)).isoformat()


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
        page.goto(base_url, timeout=8000)
        page.wait_for_timeout(1000)
        page.evaluate("() => setLang('fr')")

        print("=== Ajout via le vrai formulaire (bouton, champ date, enregistrer) ===\n")
        page.evaluate("() => { state.screen = 'pantry'; render(); }")
        page.wait_for_timeout(200)
        page.evaluate("() => openPantryAddPrompt()")
        page.wait_for_timeout(200)
        page.fill("#modal-ing-name", "Thon en boîte")
        page.fill("#modal-ing-expiration", iso_date(-2))
        page.click("#modal-confirm")
        page.wait_for_timeout(300)
        saved = page.evaluate("() => state.pantry.find(i => i.name === 'Thon en boîte')")
        check("L'article est enregistré avec la date de péremption saisie", saved is not None and saved.get("expirationDate") == iso_date(-2), str(saved))

        print("\n=== Statuts : expiré / bientôt / lointain / sans date ===\n")
        page.evaluate(
            """
            async (dates) => {
                const items = [
                    { id: 'exp-expired', name: 'Lait', quantity: 1, unit: 'L', expirationDate: dates.expired },
                    { id: 'exp-soon', name: 'Yaourt', quantity: 4, unit: 'pièce', expirationDate: dates.soon },
                    { id: 'exp-future', name: 'Riz', quantity: 1, unit: 'kg', expirationDate: dates.future },
                    { id: 'exp-none', name: 'Sel', quantity: 1, unit: 'pièce' },
                ];
                for (const it of items) await storePut('pantry', it);
                state.pantry = await storeAll('pantry');
                state.screen = 'pantry';
                render();
            }
            """,
            {"expired": iso_date(-5), "soon": iso_date(2), "future": iso_date(60)},
        )
        page.wait_for_timeout(200)
        statuses = page.evaluate(
            """
            () => ({
                expired: getPantryExpirationStatus(state.pantry.find(i => i.id === 'exp-expired')),
                soon: getPantryExpirationStatus(state.pantry.find(i => i.id === 'exp-soon')),
                future: getPantryExpirationStatus(state.pantry.find(i => i.id === 'exp-future')),
                none: getPantryExpirationStatus(state.pantry.find(i => i.id === 'exp-none')),
            })
            """
        )
        check("Statut 'expired' pour une date passée", statuses["expired"] == "expired", str(statuses))
        check("Statut 'soon' pour une date à 2 jours", statuses["soon"] == "soon", str(statuses))
        check("Statut null (pas d'alerte) pour une date lointaine", statuses["future"] is None, str(statuses))
        check("Statut null pour un article sans date", statuses["none"] is None, str(statuses))

        print("\n=== Bandeau d'accueil : présent pour expiré+bientôt, absent sinon ===\n")
        page.evaluate("() => { state.screen = 'home'; render(); }")
        page.wait_for_timeout(200)
        banner_text = page.evaluate(
            """
            () => {
                const els = Array.from(document.querySelectorAll('.screen div'));
                const banner = els.find(e => e.textContent.includes('⏰'));
                return banner ? banner.textContent : null;
            }
            """
        )
        check(
            "Le bandeau liste 'Lait' et 'Yaourt' (expiré+bientôt) sans 'Riz' ni 'Sel'",
            banner_text is not None and "Lait" in banner_text and "Yaourt" in banner_text and "Riz" not in banner_text and "Sel" not in banner_text,
            banner_text,
        )

        print("\n=== Clic sur le bandeau : navigue vers le garde-manger ===\n")
        page.click("text=⏰")
        page.wait_for_timeout(200)
        check("L'écran actif devient 'pantry' après le clic", page.evaluate("() => state.screen") == "pantry")

        print("\n=== Affichage coloré dans la liste du garde-manger ===\n")
        row_texts = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.shopping-item .label')).map(e => e.innerHTML)
            """
        )
        lait_row = next((t for t in row_texts if "Lait" in t), "")
        riz_row = next((t for t in row_texts if "Riz" in t), "")
        check("La ligne 'Lait' (expiré) contient le mot 'expiré'", "expiré" in lait_row, lait_row)
        check("La ligne 'Riz' (date lointaine) contient 'consommer avant'", "consommer avant" in riz_row, riz_row)
        check("La ligne 'Sel' (sans date) n'affiche aucune mention de péremption", not any(("Sel" in t) and ("expiré" in t or "expire" in t or "consommer" in t) for t in row_texts))

        print("\n=== Tri par date de péremption : les plus urgents en tête, sans date en dernier ===\n")
        page.evaluate("() => { state.pantrySortBy = 'expiration'; render(); }")
        page.wait_for_timeout(200)
        order = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.shopping-item .label')).map(e => e.textContent)
            """
        )
        idx_lait = next((i for i, t in enumerate(order) if "Lait" in t), -1)
        idx_yaourt = next((i for i, t in enumerate(order) if "Yaourt" in t), -1)
        idx_riz = next((i for i, t in enumerate(order) if "Riz" in t), -1)
        idx_sel = next((i for i, t in enumerate(order) if "Sel" in t), -1)
        check(
            "Ordre : Lait (expiré) < Yaourt (bientôt) < Riz (lointain) < Sel (sans date, en dernier)",
            -1 not in (idx_lait, idx_yaourt, idx_riz, idx_sel) and idx_lait < idx_yaourt < idx_riz < idx_sel,
            str(order),
        )

        print("\n=== Modification : la date se pré-remplit et peut être effacée ===\n")
        page.evaluate("() => { state.pantrySortBy = 'name'; render(); }")
        page.wait_for_timeout(200)
        page.evaluate("() => openAddItemModal('pantry', state.pantry.find(i => i.id === 'exp-soon'))")
        page.wait_for_timeout(200)
        prefill = page.evaluate("() => document.getElementById('modal-ing-expiration').value")
        check("Le champ date se pré-remplit avec la date déjà enregistrée", prefill == iso_date(2), prefill)
        page.fill("#modal-ing-expiration", "")
        page.click("#modal-confirm")
        page.wait_for_timeout(300)
        cleared = page.evaluate("() => state.pantry.find(i => i.id === 'exp-soon').expirationDate")
        check("La date peut être effacée (repasse à null)", cleared is None, str(cleared))

        print("\n=== Survie à un aller-retour de sauvegarde locale (export -> import) ===\n")
        roundtrip = page.evaluate(
            """
            async () => {
                await storePut('pantry', { id: 'exp-roundtrip', name: 'Beurre', quantity: 1, unit: 'pièce', expirationDate: '2027-01-15' });
                state.pantry = await storeAll('pantry');
                const backup = await buildBackupData();
                await importAllData(backup, 'replace');
                const restored = state.pantry.find(i => i.id === 'exp-roundtrip');
                return restored ? restored.expirationDate : null;
            }
            """
        )
        check("La date de péremption survit à un export puis réimport (sauvegarde locale)", roundtrip == "2027-01-15", str(roundtrip))

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))

        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
