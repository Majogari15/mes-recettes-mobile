#!/usr/bin/env python3
"""Test permanent : résistance des fonctions d'analyse de texte MAISON
de l'application (pas les bibliothèques tierces, déjà couvertes par
`test_pdf_exports_full.py`/l'audit de dépendances) à des entrées
pathologiques susceptibles de provoquer un blocage catastrophique
(ReDoS) dans une expression régulière mal formée — voir
TESTS_NON_REGRESSION.md point 93.

Fonctions ciblées, toutes exposées à du texte non fiable (ingrédient
tapé à la main, texte OCR d'une photo, ligne de QR code scanné) :
`parseIngredientString`, `parseOcrRecipeText`, `parseIsoDurationToMinutes`,
`parseRecipeFromQrText`, `parseTableRowsIngredients`,
`parseStackedIngredientColumn`.

Approche boîte noire plutôt que relecture de chaque regex : chaque
fonction reçoit plusieurs textes de forme classique pour déclencher un
retour arrière catastrophique (longues répétitions ambiguës suivies
d'un caractère ne correspondant pas), avec un budget de temps large
mais fini — un blocage réel dépasserait ce budget de plusieurs ordres
de grandeur, pas de quelques millisecondes.

Utilisation (démarre et arrête lui-même un serveur local temporaire) :

    cd /chemin/vers/recipe_pwa
    pip install -r tests/requirements.txt
    python3 -m playwright install chromium  # une seule fois
    python3 tests/test_regex_dos_resilience.py

Code de sortie : 0 si tous les cas passent, 1 sinon.
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUDGET_MS = 2000


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


def make_payloads():
    # Formes classiques de déclenchement d'un retour arrière
    # catastrophique : longues répétitions d'un même caractère ou d'un
    # motif ambigu (espaces/ponctuation/parenthèses), suivies d'un
    # caractère qui ne correspond finalement à rien — c'est cette
    # dernière étape qui force un moteur regex vulnérable à explorer
    # un nombre exponentiel de découpages avant d'abandonner.
    return {
        "chiffres_longs": "1" * 20000 + "!",
        "espaces_longs": " " * 20000 + "x",
        "parentheses_imbriquees": "(" * 8000 + "texte" + ")" * 8000,
        "ponctuation_repetee": (":,;.-" * 4000) + "!",
        "mot_unique_tres_long": "a" * 50000,
        "fractions_repetees": ("1/2 " * 8000),
        "parametres_repetes": ("(2 personnes) " * 4000),
        "unicode_accents_repetes": ("é" * 20000) + "x",
    }


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

        targets = [
            "parseIngredientString",
            "parseOcrRecipeText",
            "parseIsoDurationToMinutes",
            "parseRecipeFromQrText",
            "parseTableRowsIngredients",
            "parseStackedIngredientColumn",
        ]

        payloads = make_payloads()

        for fn_name in targets:
            print(f"\n=== {fn_name} ===\n")
            for payload_name, payload in payloads.items():
                try:
                    elapsed_ms = page.evaluate(
                        """
                        ([fnName, input]) => {
                            const fn = window[fnName];
                            const t0 = performance.now();
                            try { fn(input); } catch (e) { /* un rejet propre n'est pas un ReDoS */ }
                            return performance.now() - t0;
                        }
                        """,
                        [fn_name, payload],
                    )
                except Exception as e:
                    # Un timeout Playwright signifie que la page elle-même
                    # est restée bloquée plus longtemps que son propre
                    # délai — c'est la pire confirmation possible d'un
                    # vrai blocage catastrophique.
                    check(f"{fn_name} / {payload_name} : ne bloque pas la page", False, f"timeout Playwright : {e}")
                    continue
                ok = elapsed_ms < BUDGET_MS
                check(f"{fn_name} / {payload_name} : moins de {BUDGET_MS}ms", ok, f"{elapsed_ms:.0f}ms")

        check("Aucune erreur JS pendant tout le parcours", not errors, "; ".join(errors))
        browser.close()
    httpd.shutdown()

    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
