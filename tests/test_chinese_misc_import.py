"""
Chinois simplifié — catégorie importée, date de péremption, code-barres
(TESTS_NON_REGRESSION.md, entrée 159 ; intégration en cours sur une
branche, pas encore sur main).

Vérifie : catégorie d'une recette importée par lien devinée depuis un mot
chinois (甜点 -> Dessert, 早餐 -> Petit-déjeuner…), mots latins inchangés ;
date de péremption « 2027年3月15日 » lue, mot-clé « 保质期至 » préféré à la
date de fabrication « 生产日期 » ; code-barres : nom chinois du produit
(product_name_zh) demandé et retenu en chinois, nom français en français,
nom principal sinon. Réseau simulé (page.route), aucun appel réel.
"""
import http.server
import json
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

CATEGORIES = [
    ("甜点", "Dessert"), ("烘焙，蛋糕", "Dessert"), ("早餐", "Petit-déjeuner"), ("饮品", "Boisson"),
    ("凉菜", "Entrée"), ("酱料", "Sauce"), ("小吃", "Apéro"), ("家常菜", "Plat"), ("汤圆", "Autre"),
    ("Dessert", "Dessert"), ("Main course", "Plat"), ("", "Autre"),
]


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
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")

        got = page.evaluate("(cases) => cases.map((c) => guessCategoryFromText(c))", [c[0] for c in CATEGORIES])
        for (text, expected), g in zip(CATEGORIES, got):
            check(f"catégorie « {text} » -> {expected}", g == expected, g)

        r = page.evaluate("""() => [
            extractExpirationDateFromOcrText('保质期至：2027年3月15日'),
            extractExpirationDateFromOcrText('生产日期：2026年9月1日\\n保质期至 2027年3月15日'),
            extractExpirationDateFromOcrText('到期日 2027.01.05'),
            extractExpirationDateFromOcrText('2027年2月30日'),
            extractExpirationDateFromOcrText('À consommer avant le 15/03/2027'),
        ]""")
        check("péremption « 2027年3月15日 »", r[0] == "2027-03-15", r[0])
        check("péremption : « 保质期至 » préféré à « 生产日期 »", r[1] == "2027-03-15", r[1])
        check("péremption « 到期日 2027.01.05 »", r[2] == "2027-01-05", r[2])
        check("date impossible (30 février) écartée", r[3] is None, r[3])
        check("format français inchangé", r[4] == "2027-03-15", r[4])

        urls = []

        def off(route):
            urls.append(route.request.url)
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"status": 1, "product": {
                "product_name": "Tomato ketchup", "product_name_fr": "Ketchup", "product_name_zh": "番茄酱", "quantity": "500 g"}}))

        page.route("**/world.openfoodfacts.org/**", off)
        r = page.evaluate("async () => { await ensureUiTranslationsLoaded('zh'); setLang('zh'); return lookupProductByBarcode('3017620422003'); }")
        check("code-barres en chinois : nom « 番茄酱 »", r["name"] == "番茄酱", r)
        check("code-barres en chinois : product_name_zh demandé", "product_name_zh" in urls[-1], urls[-1])
        r = page.evaluate("async () => { setLang('fr'); return lookupProductByBarcode('3017620422003'); }")
        check("code-barres en français : « Ketchup » (inchangé)", r["name"] == "Ketchup", r)
        check("code-barres en français : pas de champ en double", urls[-1].count("product_name_fr") == 1, urls[-1])
        r = page.evaluate("async () => { await ensureUiTranslationsLoaded('de'); setLang('de'); return lookupProductByBarcode('3017620422003'); }")
        check("code-barres sans nom dans la langue : nom principal", r["name"] == "Tomato ketchup", r)
        page.unroute("**/world.openfoodfacts.org/**")

        page.evaluate("() => setLang('fr')")
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
