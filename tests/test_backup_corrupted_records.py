"""
Restauration d'une sauvegarde contenant des enregistrements abîmés
(champs manquants ou de mauvais type). Voir TESTS_NON_REGRESSION.md,
entrée 137.

Avant la v303, un seul enregistrement de ce genre suffisait à :
- bloquer le DÉMARRAGE de l'application (deux entrées d'historique de
  planning sans date : tri au chargement -> écran « Échec du
  démarrage », données inaccessibles) ;
- faire planter des écrans (menus sans nom ni liste, liste de courses
  enregistrée sans articles, article sans nom).
Vérifie aussi qu'un identifiant de recette piégé (guillemets + balises)
n'injecte aucun élément HTML dans les écrans qui l'affichent en
attribut (comparaison, export du livre de recettes).
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

CASES = {
    "historique de planning sans date ni contenu": {"planHistory": [{"id": "h1"}, {"id": "h2"}]},
    "articles de courses sans nom": {"shopping": [{"id": "s1", "name": None}, {"id": "s2"}]},
    "garde-manger sans nom": {"pantry": [{"id": "p1"}, {"id": "p2", "name": 3}]},
    "menus sans nom ni recettes": {"menus": [{"id": "m1"}, {"id": "m2", "items": "x"}]},
    "recettes sans nom": {"recipes": [{"id": "r1"}, {"id": "r2"}]},
    "listes enregistrées sans articles": {"savedShoppingLists": [{"id": "l1"}, {"id": "l2", "items": [None, 3]}]},
    "modèles de planning vides": {"planTemplates": [{"id": "t1"}, {"id": "t2", "plan": "x"}]},
    "corbeille sans date": {"trash": [{"id": "c1", "name": "A"}, {"id": "c2", "name": "B"}]},
    "identifiant de recette piégé": {"recipes": [{"id": 'x"><b id=injected>X</b>', "name": "R", "ingredients": []}, {"id": "r2", "name": "S", "ingredients": []}]},
}
SCREENS = ["home", "recipes", "shopping", "pantry", "menus", "menu", "planning", "planningHistory",
           "trash", "savedShoppingLists", "statistics", "whatCanICook", "cookbookExport", "compare", "backup"]


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def main():
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{port}/index.html"
    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for label, data in CASES.items():
            ctx = browser.new_context(viewport={"width": 390, "height": 800})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc).split("\n")[0]))
            page.goto(base_url, timeout=15000)
            page.evaluate("() => appReady")
            imported = page.evaluate(
                """async (data) => {
                    const file = new File([JSON.stringify(data)], 'b.json');
                    try { const { data: d } = await parseBackupFile(file); await importAllData(d, 'replace'); return 'ok'; }
                    catch (e) { return 'erreur : ' + e.message; }
                }""",
                data,
            )
            page.reload()
            page.evaluate("() => appReady")
            started = page.evaluate("() => !!document.querySelector('.screen')")
            crashes = []
            injected = []
            for screen in SCREENS:
                try:
                    page.evaluate("(sc) => { state.currentMenuId = sc === 'menu' ? (state.menus[0] || {}).id : null; state.screen = sc; render(); }", screen)
                except Exception as e:
                    crashes.append(f"{screen} : {str(e).split(chr(10))[0][:80]}")
                    continue
                if page.evaluate("() => !!document.getElementById('injected')"):
                    injected.append(screen)
            ok = imported == "ok" and started and not crashes and not injected and not errors
            detail = f"import {imported}, démarrage {'ok' if started else 'BLOQUÉ'}"
            if crashes:
                detail += f", écrans plantés {crashes}"
            if injected:
                detail += f", HTML injecté sur {injected}"
            if errors:
                detail += f", erreurs JS {errors[:2]}"
            print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label} — {detail}")
            all_ok = all_ok and ok
            ctx.close()
        browser.close()
    httpd.shutdown()
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
