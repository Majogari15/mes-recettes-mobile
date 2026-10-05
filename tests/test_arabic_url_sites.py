"""
Arabe — import par lien depuis les sites arabes proposés (TESTS_NON_REGRESSION.md,
entrée 169 ; intégration en cours sur une branche, pas encore sur main).

Pages imitant la structure réelle relevée le 5 octobre 2026 sur les sites
proposés (contenu inventé, aucune donnée réelle), servies par des réponses
réseau simulées (page.route) au vrai code d'import (fetchRecipeFromUrl) :
- أطيب طبخة par le Worker : données structurées, qualificatif placé avant
  la quantité (« بودرة  ثلث كوب كاكاو », « مذوبة  نصف كوب زبدة ») ;
- أطيب أكلة par Jina : fiche de statistiques « المكوّنات / 7 / عدد » avant
  la vraie liste, fin « اقرأ 2919 مرات » ;
- CBC Sofra par Jina : titre « # » après la recette (grille des
  programmes), ingrédients en puces « ● » sans quantité, boutons de
  partage (« فيسبوك ») et « المزيد من … » après les étapes.
Vérifie aussi que le découpage d'une page française par Jina (titre « # »
en tête) est inchangé.
"""
import http.server
import json
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

ATYAB_TABKHA_HTML = """<!doctype html><html><head><title>طريقة عمل كعكة تجريبية | موقع تجريبي</title>
<script type="application/ld+json">""" + json.dumps({
    "@context": "https://schema.org", "@type": "Recipe", "name": "طريقة عمل كعكة الكاكاو التجريبية",
    "recipeYield": "8", "prepTime": "PT15M", "cookTime": "PT30M",
    "recipeIngredient": [" كوب سكر", " 2 بيض", "بودرة  ثلث كوب كاكاو", "مذوبة  نصف كوب زبدة", " نصف كوب دقيق", " ربع ملعقة صغيرة ملح"],
    "recipeInstructions": [{"@type": "HowToStep", "text": "حمّي الفرن."}, {"@type": "HowToStep", "text": "اخلطي المكونات واخبزيها."}],
}, ensure_ascii=False) + """</script></head><body></body></html>"""

ATYAB_AKLE_JINA = """Title: دجاج بالليمون - وصفات تجريبية

URL Source: https://example-ar.test/recipes/chicken/1.html

Markdown Content:
*    المكون
*   [لحم](https://example-ar.test/meat.html)

# دجاج بالليمون

*   المكوّنات

7

عدد

المجموع في الأكلة

قريباً

وقت التحضير

45

دقيقة

### Nutrition

**القيمة الغذائيّة التقريبية**

السعرات الحراريّة قريباً

المكوّنات

*     2 صدور دجاج
*     ¼ كوب لوز مقشور
*     1 ملعقة شاي ملح

طريقة التحضير

1.   يُطهى الدجاج على نار هادئة.
2.   يُقدم مع الأرز.

اقرأ 1234 مرات

Tweet
"""

CBC_SOFRA_JINA = """Title: كفتة تجريبية - موقع تجريبي

URL Source: https://example-ar.test/wa/1/

Markdown Content:
*   [الرئيسية](https://example-ar.test/)
*   [وصفات](https://example-ar.test/wa/)

## كفتة تجريبية

*   [شيف تجريبي](https://example-ar.test/chef/1/)

## المقادير

● لحمة مفرومة

● بصل

● ملح وفلفل

● زيت للقلي

## طريقة تحضير كفتة تجريبية

*   يخلط البصل مع اللحمة المفرومة
*   تشكل الكفتة وتقلى في الزيت

فيسبوك

تويتر

المزيد من أطباق رئيسية

## [وصفة أخرى](https://example-ar.test/wa/2/)

# [برنامج تلفزيوني](https://example-ar.test/pron/1/)

## مباشر

السبت

3:30 م
"""

FR_JINA = """Title: Tarte test

Markdown Content:
[Menu](https://example.test/)

# Tarte aux pommes test

## Ingrédients

*   4 pommes
*   200 g de farine

## Préparation

1.   Éplucher les pommes.
2.   Cuire 30 min.
"""

IMPORT_JS = """async (url) => {
    const rec = await fetchRecipeFromUrl(url);
    return { name: rec.name, persons: rec.persons, description: rec.description,
             service: localStorage.getItem('lastImportService'),
             ingredients: rec.ingredients.map((i) => [translateIngredientName(i.name), i.quantity, i.unit]) };
}"""


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def router(worker_body=None, jina_body=None):
    def handler(route):
        u = route.request.url
        if "127.0.0.1" in u:
            return route.continue_()
        if "workers.dev" in u:
            if worker_body is None:
                return route.fulfill(status=502, body="Upstream HTTP 500")
            return route.fulfill(status=200, content_type="text/html; charset=utf-8", body=worker_body)
        if "r.jina.ai" in u:
            if jina_body is None:
                return route.fulfill(status=500, body="indisponible")
            return route.fulfill(status=200, content_type="text/plain; charset=utf-8", body=jina_body)
        return route.abort()
    return handler


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
        page.evaluate("async () => { await ensureUiTranslationsLoaded('ar'); await ensureIngredientTranslationsLoaded('ar'); setLang('ar'); }")

        def run(url, **kw):
            page.unroute("**/*")
            page.route("**/*", router(**kw))
            return page.evaluate(IMPORT_JS, url)

        r = run("https://example-ar.test/recipe/1", worker_body=ATYAB_TABKHA_HTML)
        names = [i[0] for i in r["ingredients"]]
        check("أطيب طبخة : « بودرة  ثلث كوب كاكاو » -> « كاكاو بودرة », « مذوبة  نصف كوب زبدة » -> « زبدة مذوبة »",
              "كاكاو بودرة" in names and "زبدة مذوبة" in names, names)
        check("أطيب طبخة : 6 ingrédients, « كوب سكر » sans chiffre = 1 tasse (24 cl / 8 = 3 cl)",
              len(r["ingredients"]) == 6 and r["ingredients"][0][1:] == [3, "cl"], r["ingredients"][:2])

        r = run("https://example-ar.test/recipes/chicken/1.html", jina_body=ATYAB_AKLE_JINA)
        got = [(i[0], i[1], i[2]) for i in r["ingredients"]]
        check("أطيب أكلة : fiche « المكوّنات / 7 / عدد » ignorée, 3 vrais ingrédients",
              r["service"] == "Jina AI Reader" and len(got) == 3 and got[0][0] == "صدور دجاج", got)
        check("أطيب أكلة : étapes arrêtées à « اقرأ … مرات »",
              "يُقدم مع الأرز" in r["description"] and "اقرأ" not in r["description"] and "Tweet" not in r["description"], r["description"][-60:])

        r = run("https://example-ar.test/wa/1/", jina_body=CBC_SOFRA_JINA)
        names = [i[0] for i in r["ingredients"]]
        check("CBC Sofra : recette gardée malgré le titre « # » placé après", r["name"] == "كفتة تجريبية", r["name"])
        check("CBC Sofra : 4 ingrédients en puces « ● » (« زيت للقلي » -> زيت, quantité vague)",
              len(names) == 4 and names[0] == "لحمة مفرومة" and r["ingredients"][3][1] is None, names)
        check("CBC Sofra : étapes arrêtées aux boutons de partage, sans la grille des programmes",
              "تقلى في الزيت" in r["description"] and "فيسبوك" not in r["description"] and "مباشر" not in r["description"],
              r["description"][-60:])

        page.evaluate("() => setLang('fr')")
        r = run("https://example.test/tarte", jina_body=FR_JINA)
        check("français par Jina inchangé (titre « # », 2 ingrédients, étapes)",
              r["name"] == "Tarte aux pommes test" and len(r["ingredients"]) == 2 and "Éplucher" in r["description"],
              (r["name"], r["ingredients"]))

        page.unroute("**/*")
        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
