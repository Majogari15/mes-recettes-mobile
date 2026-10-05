"""
Arabe — import de recette par photo (OCR « ara ») et par lien
(TESTS_NON_REGRESSION.md, entrée 167 ; intégration en cours sur une
branche, pas encore sur main).

Vérifie : modèle Tesseract ara déclaré et présent, ainsi que le modèle
latin léger de relecture des nombres (lang-digits) ; chiffres arabo-indiens
et marques invisibles (LRM/RLM) normalisés ; lignes d'ingrédients arabes
(nombre avant ou après le nom, unités غرام / مل / كوب / ملعقة كبيرة…, duel
« ملعقتان » = 2, « نصف », « كوب ونصف », « حسب الرغبة », « رشة », taille
« حبة كبيرة » et précisions gardées en note), sans prendre « سبع بهارات »
pour une quantité ; lignes françaises inchangées ; titres de section
(« المقادير », « مقادير طريقة عمل … », « طريقة التحضير لعمل … : »),
sous-titres « للصلصة: » ignorés, personnes (« لـ 4 أشخاص », « شخصين »),
durées (« 1 ساعة و 30 دقيقة »), allergènes, lignes parasites d'un site
(durée seule, « تم الحفظ ») ; mots d'une ligne arabe remis de droite à
gauche ; import par lien (données structurées et texte Jina, contenu
inventé imitant la structure de vrais sites arabes relevée le 5 octobre
2026) relié au catalogue ; puis une vraie reconnaissance OCR d'une image
de recette arabe générée dans le navigateur, nombres en tête de ligne
compris (« 200 », « 12 », « 1/2 »).
"""
import http.server
import json
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

INGREDIENT_CASES = [
    # (ligne, nom attendu, quantité, unité)
    ("4 حبات طماطم", "طماطم", 4, "pièce"),
    ("200 غرام جبن", "جبن", 200, "g"),
    ("٢٠٠ غرام زبدة", "زبدة", 200, "g"),
    ("ملعقتان كبيرتان زيت زيتون", "زيت زيتون", 2, "c. à soupe"),
    ("ملعقة كبيرة سكر", "سكر", 1, "c. à soupe"),
    ("1 ملعقة صغيرة كمون", "كمون", 1, "c. à café"),
    ("1/2 ملعقة صغيرة ملح", "ملح", 0.5, "c. à café"),
    ("نصف كوب حليب", "حليب", 12, "cl"),
    ("كوب ونصف دقيق", "دقيق", 36, "cl"),
    ("500 مل حليب", "حليب", 50, "cl"),
    ("1 لتر ماء", "ماء", 1, "L"),
    ("1 كغ لحم بقري", "لحم بقري", 1, "kg"),
    ("فصين ثوم", "ثوم", 2, "gousse"),
    ("3 فصوص ثوم مهروس", "ثوم مهروس", 3, "gousse"),
    ("علبة طماطم مقشرة", "طماطم مقشرة", 1, "boîte"),
    ("ثلاث ملاعق كبيرة طحينة", "طحينة", 3, "c. à soupe"),
    ("2 ملعقة كبيرة من السكر", "السكر", 2, "c. à soupe"),
    ("2 م.ك زيت", "زيت", 2, "c. à soupe"),
    ("معلقه ملح", "ملح", 1, "c. à soupe"),
    ("2-3 حبات خيار", "خيار", 2, "pièce"),
    ("جبن 200 غرام", "جبن", 200, "g"),
    ("دقيق: 250 غ", "دقيق", 250, "g"),
    ("البيض 5 حبات", "البيض", 5, "pièce"),
    ("بهارات مشكلة نصف ملعقة صغيرة", "بهارات مشكلة", 0.5, "c. à café"),
    ("طماطم 2 حبة متوسطة الحجم ومفرومة", "طماطم (متوسطة الحجم ومفرومة)", 2, "pièce"),
    ("حبة كبيرة طماطم مقطعة", "طماطم مقطعة (كبيرة)", 1, "pièce"),
    ("2 ملعقة صغيرة (10 مل) كمون مطحون", "كمون مطحون (10 مل)", 2, "c. à café"),
    ("4 فصوص ثوم، مفرومة", "ثوم (مفرومة)", 4, "gousse"),
    ("200 غ دقيق (منخول)", "دقيق (منخول)", 200, "g"),
    ("بيضة واحدة", "بيضة", 1, "pièce"),
    ("ملح حسب الرغبة", "ملح", None, "pièce"),
    ("رشة ملح", "ملح", None, "pièce"),
    ("ملح رشّة", "ملح", None, "pièce"),
    ("قليل من الفلفل الأسود", "الفلفل الأسود", None, "pièce"),
    ("بيض العدد حسب الرغبه", "بيض", None, "pièce"),
    # Nombre écrit en lettres sans unité : un nom (épices « sept épices »).
    ("سبع بهارات", "سبع بهارات", None, "pièce"),
    # Non-régression : lignes françaises et chinoise inchangées.
    ("200 g de farine", "farine", 200, "g"),
    ("2 oignons", "oignons", 2, "pièce"),
    ("1 c. à soupe d'huile", "huile", 1, "c. à soupe"),
    ("番茄 2个", "番茄", 2, "pièce"),
]

OCR_TEXT = "\n".join([
    "‏كبة مشوية",
    "المقادير (لـ ٤ أشخاص)",
    "للعجينة:",
    "500 غرام برغل",
    "ملعقتان كبيرتان زيت زيتون",
    "للحشوة:",
    "250 غرام لحم مفروم",
    "1 بصلة مفرومة",
    "ربع كوب صنوبر",
    "ملح حسب الرغبة",
    "طريقة التحضير:",
    "1. يُنقع البرغل في الماء.",
    "2. تُخلط المكونات وتُشكل الكبة.",
    "3. تُشوى الكبة على الفحم.",
    "وقت التحضير: 30 دقيقة",
    "وقت الطهي: 1 ساعة و 15 دقيقة",
    "مسببات الحساسية: قمح، سمسم",
    "التعليقات",
    "وصفة رائعة جدا شكرا لكم على المشاركة",
])

STRUCTURED_JS = """async () => {
    return await buildRecipeFromStructuredData({
        '@type': 'Recipe', name: 'فول مدمس بالطماطم', recipeYield: 'شخصين', recipeCategory: 'وصفات فطور',
        prepTime: 'PT10M', cookTime: 'PT20M',
        recipeIngredient: ['2 كوب فول مطبوخ', 'حبة كبيرة طماطم مقطعة', 'الزيت النباتي 2 ملعقة كبيرة', 'رشة ملح', 'قليل من زيت الزيتون'],
        recipeInstructions: [{ '@type': 'HowToStep', text: 'يُسخن الفول.' }, { '@type': 'HowToStep', text: 'تُضاف الطماطم.' }],
    });
}"""

# Texte Jina imitant la structure d'un site arabe (titre « # », titres de
# section suivis du nom du plat, ingrédients « الاسم : الكمية »).
JINA_SITE_A = """Title: طريقة عمل العدس بالخضار| مطبخ تجريبي

URL Source: https://example-ar.test/node/1

Markdown Content:
[القائمة](https://example-ar.test/menu)

# طريقة عمل العدس بالخضار

وقت الطهى

## مقادير طريقة عمل العدس بالخضار

 - العدس : 2 كوب
 - الجزر : 2 حبة مقطعة مكعبات
 - الكمون : نصف ملعقة صغيرة
 - ملح : رشّة

## طريقة تحضير طريقة عمل العدس بالخضار

1.   يُغسل العدس جيداً.
2.   تُضاف الخضار ويُطهى العدس حتى ينضج.

### قد يعجبك أيضاً

###### [شوربة أخرى](https://example-ar.test/node/2)
"""

# Sans titre « # » : titre « ## », auteur juste après, titres « … لعمل … : »,
# lien collé au mot précédent, durée et nombre de personnes seuls sous le
# titre des ingrédients, boutons du site.
JINA_SITE_B = """Title: طريقة عمل سلطة الحمص من مستخدم تجريبي

URL Source: https://example-ar.test/recipes/2

Markdown Content:
## سلطة الحمص

[مستخدم تجريبي @test_user مدينة تجريبية](https://example-ar.test/users/1)

## المكوّنات لعمل السلطة :

١٠ دقائق

شخصين

*   2 كوب حمص مسلوق
*   ملعقة صغيرة[كمون](https://example-ar.test/search/x)
*   معلقتين زيت زيتون

[تم الحفظ](https://example-ar.test/bookmark)

احفظ الوصفة لتجدها بسهولة لاحقًا

## الخطوات

1.   يُخلط الحمص مع الكمون والزيت.
2.   تُقدم السلطة باردة.

[تم الحفظ](https://example-ar.test/bookmark)
"""

IMPORT_JS = """async (url) => {
    const rec = await fetchRecipeFromUrl(url);
    return { name: rec.name, persons: rec.persons, description: rec.description,
             service: localStorage.getItem('lastImportService'),
             ingredients: rec.ingredients.map((i) => [i.name, i.quantity, i.unit]) };
}"""

PHOTO_LINES = [
    "شكشوكة بالطماطم", "المقادير (لـ 4 أشخاص)", "4 حبات طماطم", "200 غرام جبن",
    "ملعقتان كبيرتان زيت زيتون", "12 حبة زيتون", "1/2 ملعقة صغيرة كمون", "ملح حسب الرغبة",
    "طريقة التحضير", "1. يُقطّع البصل ويُقلى في الزيت.", "2. تُضاف الطماطم وتُطهى 10 دقائق.",
    "3. تُكسر البيضات فوقها وتُغطّى المقلاة.", "وقت التحضير: 15 دقيقة", "وقت الطهي: 20 دقيقة",
]

IMAGE_LINES = [
    "شكشوكة بالطماطم", "المقادير (لـ 4 أشخاص)", "4 حبات طماطم", "200 غرام جبن",
    "ملعقتان كبيرتان زيت زيتون", "12 حبة زيتون", "1/2 ملعقة صغيرة كمون", "ملح حسب الرغبة",
    "طريقة التحضير", "1. يُقطّع البصل ويُقلى في الزيت.", "2. تُضاف الطماطم وتُطهى 10 دقائق.",
    "3. تُكسر البيضات فوقها وتُغطّى المقلاة.", "وقت التحضير: 15 دقيقة", "مسببات الحساسية: بيض، حليب",
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

    check("modèle Tesseract ara présent (lib/tesseract/lang)",
          os.path.getsize(f"{PROJECT_ROOT}/lib/tesseract/lang/ara.traineddata.gz") > 1_000_000)
    check("modèle latin de relecture des nombres présent (lib/tesseract/lang-digits)",
          os.path.getsize(f"{PROJECT_ROOT}/lib/tesseract/lang-digits/eng.traineddata.gz") > 1_000_000)

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

        check("TESSERACT_LANG_MAP.ar = « ara »", page.evaluate("() => TESSERACT_LANG_MAP.ar") == "ara")
        r = page.evaluate("() => [normalizeArabicText('\\u200f٢٠٠ غرام ١٫٥ لـ ۳'), normalizeArabicText('Crème 200 g')]")
        check("chiffres arabo-indiens et persans, virgule décimale « ٫ », RLM et tatouil normalisés",
              r[0] == "200 غرام 1.5 ل 3", r[0])
        check("texte sans arabe inchangé", r[1] == "Crème 200 g", r[1])

        got = page.evaluate("(cases) => cases.map((c) => { const x = parseIngredientString(c); return [x.name, x.quantity, x.unit]; })",
                            [c[0] for c in INGREDIENT_CASES])
        bad = [(c[0], g) for c, g in zip(INGREDIENT_CASES, got) if g != [c[1], c[2], c[3]]]
        check(f"lignes d'ingrédients ({len(INGREDIENT_CASES)} cas, arabe + non-régression)", not bad, bad[:6])
        r = page.evaluate("() => ['ملح حسب الرغبة', 'رشة ملح', '4 حبات طماطم'].map((c) => !!parseIngredientString(c).vagueQuantity)")
        check("« حسب الرغبة » / « رشة » : quantité vague, pas une quantité oubliée", r == [True, True, False], r)

        pr = page.evaluate("(t) => { const r = parseOcrRecipeText(t); return { ...r, section: detectPhotoSection(r, t), "
                           "confidence: r.ingredients.map((i) => i.confidence) }; }", OCR_TEXT)
        check("texte : nom (marque RLM retirée)", pr["name"] == "كبة مشوية", pr["name"])
        got = [(i["name"], i["quantity"], i["unit"]) for i in pr["ingredients"]]
        check("texte : 6 ingrédients, sous-titres « للعجينة: » / « للحشوة: » ignorés",
              got == [("برغل", 500, "g"), ("زيت زيتون", 2, "c. à soupe"), ("لحم مفروم", 250, "g"), ("بصلة مفرومة", 1, "pièce"),
                      ("صنوبر", 6, "cl"), ("ملح", None, "pièce")], got)
        check("texte : noms arabes courts jugés fiables (« ملح » vague compris)", all(c == "reliable" for c in pr["confidence"]), pr["confidence"])
        check("texte : « لـ ٤ أشخاص » -> 4 personnes", pr["persons"] == 4, pr["persons"])
        check("texte : préparation 30 min, cuisson « 1 ساعة و 15 دقيقة » = 75 min",
              pr["prepTime"] == 30 and pr["cookTime"] == 75, (pr["prepTime"], pr["cookTime"]))
        check("texte : allergènes « قمح، سمسم » -> Gluten, Sésame", sorted(pr["allergens"]) == ["Gluten", "Sésame"], pr["allergens"])
        check("texte : 3 étapes, commentaires après « التعليقات » exclus",
              pr["description"].startswith("1. يُنقع") and "رائعة" not in pr["description"], pr["description"][:80])
        check("texte : photo classée « recette complète »", pr["section"] == "mixed", pr["section"])
        r = page.evaluate("""() => ['التحضير: 15 دقيقة', 'المقادير لعمل الشكشوكة :', 'مقادير طريقة عمل العدس', 'طريقة التحضير لعمل الكبة :',
                                    'يُقطّع البصل ويُقلى في الزيت.'].map((l) => [matchesIngredientTitle(l), OCR_INSTRUCTION_MARKER.test(l)])""")
        check("titres : durée « التحضير: 15 دقيقة » pas un titre ; titres suivis du nom du plat reconnus ; phrase d'étape non",
              r == [[False, False], [True, False], [True, False], [False, True], [False, False]], r)
        r = page.evaluate("() => parseOcrRecipeText('سلطة\\nالمكونات\\nشخصين\\n٤ دقائق\\n2 كوب حمص\\nتم الحفظ\\nطريقة العمل\\nيُخلط كل شيء.')")
        check("texte : « شخصين » = 2 personnes ; durée seule et « تم الحفظ » pas des ingrédients",
              r["persons"] == 2 and [i["name"] for i in r["ingredients"]] == ["حمص"], (r["persons"], [i["name"] for i in r["ingredients"]]))

        # Ligne arabe : mots remis de droite à gauche à partir des positions.
        r = page.evaluate("""() => reconstructTextFromBlocks({ width: 1000, blocks: [{ paragraphs: [{ lines: [
            { text: '200 غرام جبن', words: [{ text: 'جبن', bbox: { x0: 800, x1: 850 } }, { text: '200', bbox: { x0: 910, x1: 960 } }, { text: 'غرام', bbox: { x0: 860, x1: 900 } }] },
            { text: '200 g farine', words: [{ text: 'farine', bbox: { x0: 100, x1: 160 } }, { text: '200', bbox: { x0: 10, x1: 50 } }, { text: 'g', bbox: { x0: 60, x1: 70 } }] },
        ] }] }] })""")
        check("reconstruction : ligne arabe de droite à gauche, ligne latine inchangée", r == "200 غرام جبن\n200 g farine", r)

        # Import par lien : données structurées.
        r = page.evaluate(STRUCTURED_JS)
        names = [i["name"] for i in r["ingredients"]]
        check("lien (données structurées) : « شخصين » -> 2 personnes", r["persons"] == 2, r["persons"])
        check("lien : quantités par personne (2 كوب pour 2 -> 24 cl)", r["ingredients"][0]["quantity"] == 24 and r["ingredients"][0]["unit"] == "cl",
              r["ingredients"][0])
        check("lien : « الزيت النباتي » relié au catalogue « Huile végétale », « ملح » à « Sel », « زيت الزيتون » à « Huile d'olive »",
              "Huile végétale" in names and "Sel" in names and "Huile d'olive" in names, names)
        check("lien : catégorie « وصفات فطور » -> Petit-déjeuner", r["category"] == "Petit-déjeuner", r["category"])

        # Import par lien : texte Jina (Worker en échec).
        def route_jina(body):
            def handler(route):
                u = route.request.url
                if "127.0.0.1" in u:
                    return route.continue_()
                if "r.jina.ai" in u:
                    return route.fulfill(status=200, content_type="text/plain; charset=utf-8", body=body)
                if "workers.dev" in u:
                    return route.fulfill(status=500, body="indisponible")
                return route.abort()
            return handler

        page.route("**/*", route_jina(JINA_SITE_A))
        r = page.evaluate(IMPORT_JS, "https://example-ar.test/node/1")
        page.unroute("**/*")
        check("Jina (site A) : titre « # », ingrédients « الاسم : الكمية »",
              r["name"] == "طريقة عمل العدس بالخضار" and len(r["ingredients"]) == 4 and r["service"] == "Jina AI Reader",
              (r["name"], r["ingredients"]))
        check("Jina (site A) : étapes jusqu'à « قد يعجبك أيضاً »",
              "يُغسل العدس" in r["description"] and "شوربة أخرى" not in r["description"], r["description"][:80])
        page.route("**/*", route_jina(JINA_SITE_B))
        r = page.evaluate(IMPORT_JS, "https://example-ar.test/recipes/2")
        page.unroute("**/*")
        got = [(i[0], i[2]) for i in r["ingredients"]]
        check("Jina (site B) : titre sans l'auteur, « شخصين » -> 2 personnes", r["name"] == "سلطة الحمص" and r["persons"] == 2,
              (r["name"], r["persons"]))
        check("Jina (site B) : 3 ingrédients, lien collé séparé (« ملعقة صغيرة كمون »), boutons du site exclus",
              len(got) == 3 and got[1] == ("كمون", "c. à café"), got)

        # Vraie reconnaissance : image générée avec la police arabe de
        # l'application, lettres liées par jsPDF, lue par Tesseract ara.
        r = page.evaluate("""async (lines) => {
            await loadJsPdfLib();
            const font = new FontFace('TestAR', 'url(./lib/fonts/noto-sans-arabic-pdf.ttf)');
            await font.load(); document.fonts.add(font);
            const c = document.createElement('canvas'); c.width = 1000; c.height = 80 + lines.length * 56;
            const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.fillStyle = '#222';
            g.direction = 'rtl'; g.textAlign = 'right';
            lines.forEach((l, i) => { g.font = (i === 0 ? '40px' : '28px') + ' TestAR'; g.fillText(window.jspdf.jsPDF.API.processArabic(l), c.width - 40, 70 + i * 56); });
            const blob = await new Promise((res) => c.toBlob(res, 'image/png'));
            const res = await runOcrOnImage(new File([blob], 'ar.png', { type: 'image/png' }));
            await terminateSharedTesseractWorker();
            const parsed = parseOcrRecipeText(res.rawText);
            return { raw: res.rawText, parsed, section: detectPhotoSection(parsed, res.rawText) };
        }""", IMAGE_LINES)
        pr = r["parsed"]
        check("OCR réel : aucune marque invisible LRM/RLM", not any(ch in r["raw"] for ch in "‎‏"), repr(r["raw"][:40]))
        check("OCR réel : nom « شكشوكة بالطماطم »", pr["name"] == "شكشوكة بالطماطم", pr["name"])
        got = {(i["name"], i["quantity"], i["unit"]) for i in pr["ingredients"]}
        expected = {("طماطم", 4, "pièce"), ("جبن", 200, "g"), ("زيت زيتون", 2, "c. à soupe"), ("زيتون", 12, "pièce"),
                    ("كمون", 0.5, "c. à café"), ("ملح", None, "pièce")}
        check("OCR réel : nombres en tête de ligne relus (200, 12, 1/2) ; au moins 5 des 6 ingrédients exacts",
              len(got & expected) >= 5 and ("جبن", 200, "g") in got, sorted(got, key=str))
        check("OCR réel : 4 personnes, préparation 15 min", pr["persons"] == 4 and pr["prepTime"] == 15, (pr["persons"], pr["prepTime"]))
        check("OCR réel : allergènes œufs et lactose", sorted(pr["allergens"]) == ["Lactose", "Œufs"], pr["allergens"])
        check("OCR réel : photo classée « recette complète »", r["section"] == "mixed", r["section"])

        # Parcours complet de l'écran « importer par photo » avec une photo
        # moins nette (fond gris, rotation 1,5°, flou, JPEG compressé) : la
        # ligne « طريقة التحضير » et des chiffres au milieu d'une ligne
        # (« وقت الطهي: 20 ») y étaient perdus.
        photo = page.evaluate("""async (lines) => {
            const c = document.createElement('canvas'); c.width = 1000; c.height = 100 + lines.length * 56;
            const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.fillStyle = '#222';
            g.direction = 'rtl'; g.textAlign = 'right';
            lines.forEach((l, i) => { g.font = (i === 0 ? 'bold 40px' : '28px') + ' TestAR'; g.fillText(window.jspdf.jsPDF.API.processArabic(l), c.width - 50, 80 + i * 56); });
            const p = document.createElement('canvas'); p.width = 1200; p.height = c.height + 200;
            const q = p.getContext('2d'); q.fillStyle = '#b9b2a6'; q.fillRect(0, 0, p.width, p.height);
            q.translate(p.width / 2, p.height / 2); q.rotate(1.5 * Math.PI / 180); q.filter = 'blur(0.8px) brightness(0.92)';
            q.drawImage(c, -c.width / 2, -c.height / 2);
            const r = document.createElement('canvas'); r.width = 900; r.height = Math.round(p.height * 900 / 1200);
            r.getContext('2d').drawImage(p, 0, 0, r.width, r.height);
            return r.toDataURL('image/jpeg', 0.7);
        }""", PHOTO_LINES)
        import base64
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(base64.b64decode(photo.split(",")[1]))
        tmp.close()
        page.evaluate("() => { state.multiPhotoImport = []; state.screen = 'importPhoto'; render(); }")
        gallery = [i for i in page.query_selector_all("main input[type=file]") if i.get_attribute("capture") is None][0]
        gallery.set_input_files(tmp.name)
        page.wait_for_function("() => state.multiPhotoImport.length && state.multiPhotoImport.every((p) => p.status !== 'processing')", timeout=240000)
        os.unlink(tmp.name)
        section = page.evaluate("() => state.multiPhotoImport[0].section")
        page.click("main .btn-primary:not([disabled])")
        page.wait_for_function("() => state.screen === 'form'", timeout=30000)
        form = page.evaluate("""() => ({ name: document.querySelector('#f-name').value, persons: document.querySelector('#f-persons').value,
            prep: document.querySelector('#f-prep').value, cook: document.querySelector('#f-cook').value,
            ings: [...document.querySelectorAll('main input')].filter((i) => i.closest('[class*=ing]') || i.classList.contains('ing-qty')).map((i) => i.value) })""")
        check("photo moins nette : classée « recette complète » malgré le titre des étapes perdu", section == "mixed", section)
        check("photo moins nette : formulaire rempli (nom, 4 personnes, 15 et 20 min)",
              (form["name"], form["persons"], form["prep"], form["cook"]) == ("شكشوكة بالطماطم", "4", "15", "20"), form)
        check("photo moins nette : 6 ingrédients et quantités par personne (200 g / 4 = 50, 12 / 4 = 3, ½ / 4 = 0.125)",
              form["ings"] == ["طماطم", "1", "جبن", "50", "زيت زيتون", "0.5", "زيتون", "3", "كمون", "0.125", "ملح", ""], form["ings"])

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
