"""
Chinois simplifié — export PDF (TESTS_NON_REGRESSION.md, entrée 155 ;
intégration en cours sur une branche, pas encore sur main).

La police Helvetica intégrée à jsPDF n'a aucun caractère chinois : avant,
le texte chinois sortait en signes illisibles. Vérifie que la police Noto
Sans SC (lib/fonts/noto-sans-sc-pdf.ttf, chargée seulement si besoin) est
intégrée et que le texte chinois est présent (table ToUnicode) pour la
recette, la liste de courses et le livre de recettes ; qu'un long texte
chinois sans espace est découpé en plusieurs lignes ; que le nom de
fichier garde les caractères chinois ; qu'un PDF tout en français reste
en Helvetica sans télécharger la police ; qu'une recette au nom chinois
exportée en français utilise aussi la police chinoise.
"""
import http.server
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
FONT_URL = "lib/fonts/noto-sans-sc-pdf.ttf"


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJECT_ROOT, **k)

    def log_message(self, *a):
        pass


def unicode_chars(pdf):
    """Caractères déclarés dans les tables ToUnicode (non compressées par jsPDF)."""
    chars = set()
    for block in re.findall(r"beginbfchar(.*?)endbfchar", pdf, re.S):
        for code in re.findall(r"<[0-9a-fA-F]+><([0-9a-fA-F]{4})>", block):
            chars.add(chr(int(code, 16)))
    return chars


EXPORT_JS = """async ([lang, kind]) => {
    await ensureUiTranslationsLoaded(lang);
    await ensureIngredientTranslationsLoaded(lang);
    setLang(lang);
    await loadJsPdfLib();
    let out = null, name = null, lines = 0;
    window.jspdf.jsPDF.API.save = function (n) { name = n; out = this.output(); };
    const zh = {id: 'z1', name: '番茄炒蛋', category: 'Plat', defaultPersons: 2, prepTime: 10, cookTime: 5,
        difficulty: 'Facile', createdAt: '2026-01-01', allergens: ['Œufs'],
        description: '鸡蛋打散，加少许盐。热锅倒油，先炒鸡蛋盛出；再炒番茄至出汁，加糖和盐调味，最后倒回鸡蛋翻炒均匀即可。这一段文字很长，用来检查没有空格的中文能否在PDF中自动换行而不会超出页面边缘。',
        ingredients: [{name: 'Tomate', quantity: 1.5, unit: 'pièce'}, {name: 'Sucre', quantity: 2.5, unit: 'g'}]};
    const fr = {id: 'f1', name: 'Tarte aux pommes', category: 'Dessert', defaultPersons: 4, prepTime: 20, cookTime: 30,
        difficulty: 'Facile', createdAt: '2026-01-01', allergens: [], description: 'Étaler la pâte.',
        ingredients: [{name: 'Pomme', quantity: 4, unit: 'pièce'}]};
    let maxRight = 0;
    // Mesure des lignes de texte chinois long (retour à la ligne, marge droite).
    const Orig = window.jspdf.jsPDF;
    window.jspdf.jsPDF = function (...args) {
        const doc = new Orig(...args);
        const origText = doc.text;
        doc.text = function (txt, x, y, ...rest) {
            if (typeof txt === 'string' && (txt.match(/[\u4e00-\u9fff]/g) || []).length >= 20) {
                lines++;
                maxRight = Math.max(maxRight, x + doc.getTextWidth(txt));
            }
            return origText.call(doc, txt, x, y, ...rest);
        };
        return doc;
    };
    if (kind === 'recipe') await exportRecipePdf(zh, 2);
    else if (kind === 'recipeFr') await exportRecipePdf(fr, 4);
    else if (kind === 'shopping') {
        state.shopping = [{name: 'Tomate', quantity: 3, unit: 'pièce', checked: false, rayon: 'Fruits et légumes'},
                          {name: 'Beurre', quantity: 250, unit: 'g', checked: true, rayon: 'Crèmerie'}];
        await exportShoppingListPdf();
    } else if (kind === 'cookbook') await exportCookbookPdf([zh], false);
    window.jspdf.jsPDF = Orig;
    return {name, out, lines, maxRight};
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
        font_requests = []
        page.on("request", lambda req: font_requests.append(req.url) if FONT_URL in req.url else None)
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")

        r = page.evaluate(EXPORT_JS, ["fr", "recipeFr"])
        pdf = r["out"] or ""
        check("français : PDF produit", pdf.startswith("%PDF"), r["name"])
        check("français : Helvetica seule, pas de police chinoise", "NotoSansSC" not in pdf)
        check("français : police chinoise non téléchargée", not font_requests, font_requests)
        check("français : nom de fichier inchangé", r["name"] == "Tarte aux pommes.pdf", r["name"])

        r = page.evaluate(EXPORT_JS, ["fr", "recipe"])
        pdf = r["out"] or ""
        check("recette au nom chinois exportée en français : police chinoise", "/BaseFont /NotoSansSC" in pdf)
        check("… et texte chinois présent", {"番", "茄"} <= unicode_chars(pdf))

        r = page.evaluate(EXPORT_JS, ["zh", "recipe"])
        pdf = r["out"] or ""
        chars = unicode_chars(pdf)
        check("recette : police Noto Sans SC intégrée", "/BaseFont /NotoSansSC" in pdf)
        check("recette : police intégrée une seule fois (pas de version grasse)",
              len(re.findall(r"/FontFile2", pdf)) == 1, len(re.findall(r"/FontFile2", pdf)))
        check("recette : titre, ingrédients traduits, libellés et allergène en chinois",
              set("番茄炒蛋糖食材准备分钟过敏原蛋做法") <= chars, "".join(sorted(c for c in chars if ord(c) > 0x2e80))[:60])
        check("recette : nom de fichier chinois conservé", r["name"] == "番茄炒蛋.pdf", r["name"])
        check("recette : long texte chinois sans espace découpé en plusieurs lignes", r["lines"] >= 2, r["lines"])
        check("recette : aucune ligne ne dépasse la marge droite (190 mm)", r["maxRight"] <= 190.5, round(r["maxRight"], 1))
        size = len(pdf.encode("latin-1", "replace"))
        check("recette : PDF de taille raisonnable (police sous-ensemble, < 400 Ko)", size < 400_000, size)

        r = page.evaluate(EXPORT_JS, ["zh", "shopping"])
        pdf = r["out"] or ""
        chars = unicode_chars(pdf)
        check("liste de courses : police chinoise et noms traduits (番茄, 黄油)",
              "/BaseFont /NotoSansSC" in pdf and set("番茄黄油") <= chars)

        r = page.evaluate(EXPORT_JS, ["zh", "cookbook"])
        pdf = r["out"] or ""
        chars = unicode_chars(pdf)
        check("livre de recettes : police chinoise et texte chinois",
              "/BaseFont /NotoSansSC" in pdf and set("番茄炒蛋") <= chars)
        check("police téléchargée une seule fois puis réutilisée", len(font_requests) == 1, len(font_requests))

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
