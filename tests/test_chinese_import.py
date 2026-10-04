"""
Chinois simplifié — import de recette par photo (OCR) et par lien
(TESTS_NON_REGRESSION.md, entrée 156 ; intégration en cours sur une
branche, pas encore sur main).

Vérifie : modèle Tesseract chi_sim déclaré et présent ; espaces insérées
par Tesseract entre les caractères chinois retirées (texte latin
inchangé) ; lignes d'ingrédients chinoises (« 番茄 2个 », « 200克面粉 »,
« 两个鸡蛋 », « 盐 少许 », plage « 2-3克 », « 斤 », note entre
parenthèses), sans prendre « 三文鱼 » ou « 五花肉 » pour une quantité ;
quelques lignes françaises inchangées ; titres de section 材料/做法,
sous-titres 主料/辅料 ignorés, personnes « 2人份 », durées « 10分钟 » /
« 1小时30分钟 », allergènes « 过敏原：鸡蛋 » ; photo classée « recette
complète » ; import par lien (données structurées chinoises) relié au
catalogue (番茄 -> Tomate) ; puis une vraie reconnaissance OCR d'une image
de recette chinoise générée dans le navigateur (aucune donnée réelle).
"""
import http.server
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

INGREDIENT_CASES = [
    # (ligne, nom attendu, quantité, unité)
    ("番茄 2个", "番茄", 2, "pièce"),
    ("鸡蛋3个", "鸡蛋", 3, "pièce"),
    ("面粉：200克", "面粉", 200, "g"),
    ("200克面粉", "面粉", 200, "g"),
    ("面粉 200g", "面粉", 200, "g"),
    ("两个鸡蛋", "鸡蛋", 2, "pièce"),
    ("鸡蛋 3", "鸡蛋", 3, "pièce"),
    ("半个柠檬", "柠檬", 0.5, "pièce"),
    ("十二个虾", "虾", 12, "pièce"),
    ("牛奶 250毫升", "牛奶", 25, "cl"),
    ("酱油 1汤匙", "酱油", 1, "c. à soupe"),
    ("1/2茶匙盐", "盐", 0.5, "c. à café"),
    ("盐 2-3克", "盐", 2, "g"),
    ("五花肉 1斤", "五花肉", 500, "g"),
    ("面条二两", "面条", 100, "g"),
    ("大蒜 3瓣", "大蒜", 3, "gousse"),
    ("姜 2片", "姜", 2, "tranche"),
    ("盐 少许", "盐", None, "pièce"),
    ("适量胡椒粉", "胡椒粉", None, "pièce"),
    ("番茄 2个（约300克）", "番茄（约300克）", 2, "pièce"),
    ("三文鱼 200克", "三文鱼", 200, "g"),
    ("三文鱼", "三文鱼", None, "pièce"),
    ("五香粉", "五香粉", None, "pièce"),
    ("四季豆 300克", "四季豆", 300, "g"),
    ("柠檬 一半", "柠檬", 0.5, "pièce"),
    ("一半柠檬", "柠檬", 0.5, "pièce"),
    # Non-régression : lignes françaises inchangées.
    ("200 g de farine", "farine", 200, "g"),
    ("2 oignons", "oignons", 2, "pièce"),
    ("Grenailles 500 g", "Grenailles", 500, "g"),
    ("1 c. à soupe d'huile", "huile", 1, "c. à soupe"),
]

# Texte tel que Tesseract chi_sim le rend (espaces entre caractères).
OCR_TEXT = """番 茄 炒 蛋
2 人 份 准备 时 间 : 10 分 钟 烹 饪 时 间 : 1 小 时 30 分 钟
材料
主料
番茄 2 个
鸡蛋 3 个
辅料
白糖 1 茶匙
盐 少许
食用 油 2 汤匙
葱 1 根
过敏原：鸡蛋
做 法
鸡蛋 打 散 ， 加 少许 盐 搅 匀 。
番茄 切 块 ， 热 锅 倒 油 炒 鸡蛋 ， 盛 出 备用 。
再 炒 番茄 至 出 汁 ， 加 糖 ， 倒 回 鸡蛋 翻 炒 均匀 即 可 。
猜你喜欢
红烧肉"""

IMAGE_LINES = ["番茄炒蛋", "2人份  准备时间：10分钟", "材料", "番茄 2个", "鸡蛋 3个", "白糖 1茶匙",
               "盐 少许", "食用油 2汤匙", "葱 1根", "做法",
               "1. 鸡蛋打散，加少许盐搅匀。", "2. 番茄切块，热锅倒油炒鸡蛋，盛出备用。",
               "3. 再炒番茄至出汁，加糖，倒回鸡蛋翻炒均匀即可。"]


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

    model = f"{PROJECT_ROOT}/lib/tesseract/lang/chi_sim.traineddata.gz"
    check("modèle chi_sim présent (palier best_int, < 3 Mo)", os.path.exists(model) and os.path.getsize(model) < 3_000_000,
          os.path.getsize(model) if os.path.exists(model) else "absent")

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
        page.evaluate("""async () => {
            await ensureUiTranslationsLoaded('zh');
            await ensureIngredientTranslationsLoaded('zh');
            setLang('zh');
        }""")

        r = page.evaluate("""() => ({
            step: matchesIngredientTitle('把材料都准备好，切成小块'),
            heads: ['材料', '用料（2人份）', '配料：', '【食材】'].map(matchesIngredientTitle),
            fr: matchesIngredientTitle('Ingrédients pour 2 personnes'),
            onlyPeiliao: parseOcrRecipeText('凉拌黄瓜\\n配料\\n黄瓜 2根\\n蒜 3瓣\\n做法\\n黄瓜拍碎，加蒜末拌匀即可。').ingredients.map((i) => i.name),
        })""")
        check("titre d'ingrédients : pas au milieu d'une phrase d'étape", r["step"] is False, r)
        check("titres d'ingrédients chinois reconnus (材料, 用料（2人份）, 配料：, 【食材】)", r["heads"] == [True] * 4, r["heads"])
        check("titre français toujours reconnu", r["fr"] is True)
        check("« 配料 » seul comme titre de liste", r["onlyPeiliao"] == ["黄瓜", "蒜"], r["onlyPeiliao"])
        check("TESSERACT_LANG_MAP.zh = chi_sim", page.evaluate("() => TESSERACT_LANG_MAP.zh") == "chi_sim")
        r = page.evaluate("""() => [collapseCjkSpaces('番 茄 炒 蛋 ， 加 少许 盐 。'), collapseCjkSpaces('番茄 2 个'),
                                    collapseCjkSpaces('200 g de farine  et sel')]""")
        check("espaces entre caractères chinois retirées", r[0] == "番茄炒蛋，加少许盐。", r[0])
        check("espace entre un nombre et un caractère chinois gardée", r[1] == "番茄 2 个", r[1])
        check("texte latin inchangé", r[2] == "200 g de farine  et sel", r[2])

        parsed = page.evaluate("(cases) => cases.map((c) => parseIngredientString(c))", [c[0] for c in INGREDIENT_CASES])
        for (line, name, qty, unit), got in zip(INGREDIENT_CASES, parsed):
            ok = got["name"] == name and got["quantity"] == qty and got["unit"] == unit
            check(f"ingrédient « {line} »", ok, f"{got['name']} | {got['quantity']} | {got['unit']}")

        r = page.evaluate("""(text) => {
            const raw = collapseCjkSpaces(text);
            const parsed = parseOcrRecipeText(raw);
            return { parsed, section: detectPhotoSection(parsed, raw), extracted: extractIngredientsFromLines(raw) };
        }""", OCR_TEXT)
        pr = r["parsed"]
        check("nom de la recette", pr["name"] == "番茄炒蛋", pr["name"])
        names = [i["name"] for i in pr["ingredients"]]
        check("ingrédients entre 材料 et 做法, sous-titres 主料/辅料 ignorés",
              names == ["番茄", "鸡蛋", "白糖", "盐", "食用油", "葱"], names)
        check("ingrédients chinois jugés fiables (pas « à vérifier »)",
              all(i["confidence"] == "reliable" for i in pr["ingredients"]), [i["confidence"] for i in pr["ingredients"]])
        check("personnes : 2人份", pr["persons"] == 2, pr["persons"])
        check("préparation : 10分钟", pr["prepTime"] == 10, pr["prepTime"])
        check("cuisson : 1小时30分钟 -> 90", pr["cookTime"] == 90, pr["cookTime"])
        check("allergène « 过敏原：鸡蛋 » -> Œufs", pr["allergens"] == ["Œufs"], pr["allergens"])
        desc = pr["description"]
        check("étapes après 做法, arrêtées avant « 猜你喜欢 »",
              desc.startswith("鸡蛋打散") and desc.count("\n") == 2 and "红烧肉" not in desc, desc)
        check("photo classée « recette complète »", r["section"] == "mixed", r["section"])
        ex = r["extracted"]
        check("extraction par lignes (photo d'ingrédients) : mêmes 6 ingrédients",
              [i["name"] for i in ex["ingredients"]] == names and ex["persons"] == 2, [i["name"] for i in ex["ingredients"]])

        r = page.evaluate("""async () => {
            const recipe = await buildRecipeFromStructuredData({
                name: '番茄炒蛋', recipeYield: '2人份', prepTime: 'PT10M', cookTime: 'PT5M',
                recipeIngredient: ['番茄 2个', '鸡蛋 3个', '白糖 1茶匙', '盐 少许'],
                recipeInstructions: [{ '@type': 'HowToStep', text: '鸡蛋打散。' }, { '@type': 'HowToStep', text: '炒番茄。' }],
            });
            return { ...recipe, photo: null, displayed: recipe.ingredients.map((i) => translateIngredientName(i.name)) };
        }""")
        check("lien : personnes 2, temps 10/5", r["persons"] == 2 and r["prepTime"] == 10 and r["cookTime"] == 5,
              (r["persons"], r["prepTime"], r["cookTime"]))
        check("lien : quantités par personne (2个 pour 2 -> 1)", r["ingredients"][0]["quantity"] == 1 and r["ingredients"][0]["unit"] == "pièce",
              r["ingredients"][0])
        catalogue_names = [i["name"] for i in r["ingredients"]]
        check("lien : « 番茄 » relié à l'ingrédient du catalogue « Tomate »", catalogue_names[0] == "Tomate", catalogue_names)
        check("lien : noms réaffichés en chinois", r["displayed"][0] == "番茄", r["displayed"])

        # Vraie reconnaissance : image générée avec la police chinoise de
        # l'application (lib/fonts), reconnue par Tesseract chi_sim.
        r = page.evaluate("""async (lines) => {
            const font = new FontFace('TestSC', 'url(./lib/fonts/noto-sans-sc-pdf.ttf)');
            await font.load(); document.fonts.add(font);
            const c = document.createElement('canvas'); c.width = 900; c.height = 80 + lines.length * 56;
            const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.fillStyle = '#222';
            lines.forEach((l, i) => { g.font = (i === 0 ? '40px' : '28px') + ' TestSC'; g.fillText(l, 40, 70 + i * 56); });
            const blob = await new Promise((res) => c.toBlob(res, 'image/png'));
            const res = await runOcrOnImage(new File([blob], 'zh.png', { type: 'image/png' }));
            await terminateSharedTesseractWorker();
            const parsed = parseOcrRecipeText(res.rawText);
            return { raw: res.rawText, parsed, section: detectPhotoSection(parsed, res.rawText) };
        }""", IMAGE_LINES)
        pr = r["parsed"]
        check("OCR réel : aucune espace entre caractères chinois", "番 茄" not in r["raw"], r["raw"][:60])
        check("OCR réel : nom « 番茄炒蛋 »", pr["name"] == "番茄炒蛋", pr["name"])
        got = {(i["name"], i["quantity"], i["unit"]) for i in pr["ingredients"]}
        expected = {("番茄", 2, "pièce"), ("鸡蛋", 3, "pièce"), ("白糖", 1, "c. à café"), ("盐", None, "pièce"),
                    ("食用油", 2, "c. à soupe"), ("葱", 1, "pièce")}
        check("OCR réel : au moins 5 des 6 ingrédients exacts", len(got & expected) >= 5, sorted(got, key=str))
        check("OCR réel : 2 personnes, préparation 10 min", pr["persons"] == 2 and pr["prepTime"] == 10, (pr["persons"], pr["prepTime"]))
        check("OCR réel : 3 étapes", pr["description"].count("\n") == 2, pr["description"])
        check("OCR réel : photo classée « recette complète »", r["section"] == "mixed", r["section"])

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
