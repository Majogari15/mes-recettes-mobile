"""
Chinois simplifié — import par lien depuis les sites chinois
(TESTS_NON_REGRESSION.md, entrée 160 ; intégration en cours sur une
branche, pas encore sur main).

Pages imitant la structure réelle relevée le 4 octobre 2026 (contenu
inventé, aucune donnée réelle), servies par des réponses réseau simulées
(page.route) au vrai code d'import (fetchRecipeFromUrl) :
- 下厨房 par le Worker : données structurées JSON-LD avec toutes les étapes
  dans un seul texte (« 1.… 2.… ») et une coupure de ligne au milieu d'un
  mot ; catégorie « 快手菜 » ;
- 下厨房 par Jina (Worker en échec) : pas de titre « # », titre de page
  « Title: », « ## 用料 », ingrédients en liens, « ## …的做法 » ;
- 美食天下 par Jina : titre « X的做法_X怎么做_…_美食天下 », « 食材明细 »,
  sous-titres « 主料(水油皮) », fiche « 甜味口味 / 中级难度 », numéro
  d'étape seul sur sa ligne, fin « 本菜谱为作者发布于… », « 分类： ».
Vérifie aussi : découpage des étapes jamais appliqué à « 1.5 kg » ni à un
numéro isolé ; liste d'ingrédients sur une ligne (« 主料：A；调料：B，C ») ;
français inchangé (titre « # », sous-titre fusionné).
"""
import http.server
import json
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

XCF_HTML = """<!doctype html><html><head><title>手撕包菜的做法_下厨房</title>
<script type="application/ld+json">""" + json.dumps({
    "@context": "https://ziyuan.baidu.com/contexts/cambrian.jsonld", "@type": "Recipe",
    "name": "五分钟手撕包菜", "recipeCategory": "快手菜",
    "recipeIngredient": ["适量包菜", "4瓣大蒜", "5个干辣椒"],
    "recipeInstructions": "1.包菜撕小块，大蒜切末。 2.调酱汁：1勺生抽、2勺醋、1勺耗\n油，搅匀备用。 3.热油爆香蒜末和辣椒，下包菜大火翻炒。 4.出锅。",
}, ensure_ascii=False) + """</script></head><body></body></html>"""

XCF_JINA = """Title: 五分钟手撕包菜

URL Source: https://www.xiachufang.com/recipe/1/

Markdown Content:
![Image 1: 五分钟手撕包菜的做法](https://example.invalid/a.jpg)

8.1 综合评分

120 人做过这道菜

[收藏](https://www.xiachufang.com/auth/login/)

## 用料

[包菜](https://www.xiachufang.com/category/1/)适量
[大蒜](https://www.xiachufang.com/category/2/)4瓣
[干辣椒](https://www.xiachufang.com/category/3/)5个

## 五分钟手撕包菜的做法

1.   包菜撕小块，大蒜切末。

![Image 2: 步骤1](https://example.invalid/b.jpg)
2.   热油爆香蒜末和辣椒，下包菜大火翻炒。

## 小贴士

包菜用手撕更入味。
"""

MSC_JINA = """Title: 凤梨酥的做法_凤梨酥怎么做_某某的菜谱_美食天下

URL Source: https://home.meishichina.com/recipe-1.html

Markdown Content:
## [凤梨酥](https://home.meishichina.com/recipe-1.html "凤梨酥")

![Image 1: 凤梨酥的做法](https://example.invalid/a.jpg)

> “酥皮层层，内馅清甜……”

### 食材明细

主料(水油皮)

*   [**中筋面粉**](https://www.meishichina.com/YuanLiao/A/ "中筋面粉的做法")135～140克
*   [**糖**](https://www.meishichina.com/YuanLiao/B/ "糖的做法")30克

辅料(油酥)

*   **低筋面粉**120克

*   [甜味](https://home.meishichina.com/t1.html "甜味")口味
*   [烤](https://home.meishichina.com/t2.html "烤")工艺
*   [中级](https://home.meishichina.com/t3.html "中级")难度

### 凤梨酥的做法步骤

*   ![Image 2: 凤梨酥的做法步骤：1](https://example.invalid/blank.gif)

1

面粉加糖和猪油揉成面团。
*   ![Image 3: 凤梨酥的做法步骤：2](https://example.invalid/blank.gif)

2

包入凤梨馅，烤25分钟。

本菜谱为作者发布于美食天下，禁止其他平台或个人转载。

分类： [烘焙](https://home.meishichina.com/c1/ "烘焙")[下午茶](https://home.meishichina.com/c2/ "下午茶")

黑米松糕

枣泥饼
"""

FR_JINA = """Title: Tarte aux pommes - Exemple

URL Source: https://example.invalid/tarte

Markdown Content:
Menu du site

# Tarte aux pommes

à la cannelle

## Ingrédients

- 200 g de farine
- 3 pommes

## Préparation

Étaler la pâte et cuire 30 minutes au four.
"""


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


IMPORT_JS = """async (url) => {
    const rec = await fetchRecipeFromUrl(url);
    return { name: rec.name, persons: rec.persons, category: rec.category, description: rec.description,
             service: localStorage.getItem('lastImportService'),
             ingredients: rec.ingredients.map((i) => [translateIngredientName(i.name), i.quantity, i.unit]) };
}"""


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
        page.evaluate("async () => { await ensureUiTranslationsLoaded('zh'); await ensureIngredientTranslationsLoaded('zh'); setLang('zh'); }")
        # Aucun appel réel : services publics et images refusés.
        page.route("**/api.allorigins.win/**", lambda r: r.fulfill(status=503, body=""))
        page.route("**/api.codetabs.com/**", lambda r: r.fulfill(status=503, body=""))
        page.route("**/api.cors.lol/**", lambda r: r.fulfill(status=503, body=""))
        page.route("**/example.invalid/**", lambda r: r.fulfill(status=404, body=""))

        # 1. 下厨房 par le Worker (JSON-LD).
        page.route("**/*.workers.dev/**", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=XCF_HTML))
        r = page.evaluate(IMPORT_JS, "https://www.xiachufang.com/recipe/1/")
        check("下厨房 (Worker) : nom", r["name"] == "五分钟手撕包菜", r["name"])
        steps = r["description"].split("\n")
        check("下厨房 (Worker) : 4 étapes séparées, numéros non doublés", len(steps) == 4 and steps[0] == "1. 包菜撕小块，大蒜切末。", steps)
        check("下厨房 (Worker) : coupure « 耗\\n油 » recollée", "1勺耗油" in r["description"], r["description"])
        check("下厨房 (Worker) : catégorie « 快手菜 » -> Plat", r["category"] == "Plat", r["category"])
        check("下厨房 (Worker) : ingrédients", [i[0] for i in r["ingredients"]] == ["包菜", "大蒜", "干辣椒"] and r["ingredients"][1][2] == "gousse",
              r["ingredients"])
        page.unroute("**/*.workers.dev/**")

        # 2. Worker en échec (403 du site) -> Jina.
        page.route("**/*.workers.dev/**", lambda r: r.fulfill(status=502, body="Upstream HTTP 403"))
        page.route("**/r.jina.ai/**", lambda r: r.fulfill(status=200, content_type="text/plain; charset=utf-8", body=XCF_JINA))
        r = page.evaluate(IMPORT_JS, "https://www.xiachufang.com/recipe/1/")
        check("下厨房 (Jina) : nom tiré de « Title: » (pas « 8.1 综合评分 »)", r["name"] == "五分钟手撕包菜", r["name"])
        check("下厨房 (Jina) : 3 ingrédients, quantités", [(i[0], i[2]) for i in r["ingredients"]] == [("包菜", "pièce"), ("大蒜", "gousse"), ("干辣椒", "pièce")],
              r["ingredients"])
        check("下厨房 (Jina) : « …的做法 » reconnu comme titre des étapes",
              r["description"].startswith("1.") and "包菜撕小块" in r["description"] and "热油" in r["description"], r["description"])
        page.unroute("**/r.jina.ai/**")

        page.route("**/r.jina.ai/**", lambda r: r.fulfill(status=200, content_type="text/plain; charset=utf-8", body=MSC_JINA))
        r = page.evaluate(IMPORT_JS, "https://home.meishichina.com/recipe-1.html")
        check("美食天下 (Jina) : nom sans doublon ni citation", r["name"] == "凤梨酥", r["name"])
        check("美食天下 (Jina) : ingrédients sans sous-titres ni fiche technique",
              [i[0] for i in r["ingredients"]] == ["中筋面粉", "糖", "低筋面粉"], r["ingredients"])
        check("美食天下 (Jina) : « 135～140克 » -> 135 g (première valeur)", r["ingredients"][0][2] == "g", r["ingredients"][0])
        check("美食天下 (Jina) : étapes « 1. … », « 2. … », arrêtées avant « 本菜谱… »",
              r["description"] == "1. 面粉加糖和猪油揉成面团。\n2. 包入凤梨馅，烤25分钟。", r["description"])
        check("美食天下 (Jina) : catégorie lue dans « 分类： » (烘焙 -> Dessert)", r["category"] == "Dessert", r["category"])
        page.unroute("**/r.jina.ai/**")

        page.route("**/r.jina.ai/**", lambda r: r.fulfill(status=200, content_type="text/plain; charset=utf-8", body=FR_JINA))
        page.evaluate("() => setLang('fr')")
        r = page.evaluate(IMPORT_JS, "https://example.invalid/tarte")
        check("français (Jina) : titre « # » et sous-titre fusionné, inchangé", r["name"] == "Tarte aux pommes à la cannelle", r["name"])
        check("français (Jina) : catégorie « Autre » (pas de « 分类 »)", r["category"] == "Autre", r["category"])
        page.unroute("**/r.jina.ai/**")
        page.unroute("**/*.workers.dev/**")

        r = page.evaluate("""() => ({
            decimal: splitNumberedStepsText('Mélanger 1.5 kg de farine. 2. Cuire.'),
            single: splitNumberedStepsText('1. Tout mélanger et cuire.'),
            zero: splitNumberedStepsText('0.切块,1.下锅,2.出锅'),
            jumps: splitNumberedStepsText('1.切块 3.下锅'),
            inline: parseOcrRecipeText('椒麻杏鲍菇\\n主料：杏鲍菇；辅料：虾；调料：鸡精，盐。\\n做法：\\n1、杏鲍菇切片。').ingredients.map((i) => i.name),
        })""")
        check("étapes : « 1.5 kg » jamais découpé", r["decimal"] == ["Mélanger 1.5 kg de farine. 2. Cuire."], r["decimal"])
        check("étapes : un seul numéro -> texte gardé tel quel", r["single"] == ["1. Tout mélanger et cuire."], r["single"])
        check("étapes : numérotation à partir de 0, séparateur virgule", r["zero"] == ["切块", "下锅", "出锅"], r["zero"])
        check("étapes : numéros qui sautent -> pas de découpage", len(r["jumps"]) == 1, r["jumps"])
        check("ingrédients sur une ligne (« 主料：…；调料：… »)", r["inline"] == ["杏鲍菇", "虾", "鸡精", "盐"], r["inline"])

        check("aucune erreur JS", not errors, errors)
        browser.close()
    httpd.shutdown()
    ok = all(results)
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if ok else "ÉCHECS DÉTECTÉS")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
