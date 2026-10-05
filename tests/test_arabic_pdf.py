"""
Arabe — export PDF (TESTS_NON_REGRESSION.md, entrée 166 ; intégration en
cours sur une branche, pas encore sur main).

La police Helvetica intégrée à jsPDF n'a aucune lettre arabe. Vérifie que
la police Noto Sans Arabic (lib/fonts/noto-sans-arabic-pdf.ttf et sa
version grasse, chargées seulement si besoin) est intégrée ; que le texte
est écrit en lettres liées (formes de présentation arabes : initiale,
médiane, finale, ligature « لا ») et contient bien titre, ingrédients
traduits et libellés ; que chaque ligne est alignée à droite dans les
marges (page en miroir) ; que les caractères invisibles d'isolation
(FSI…PDI) ne passent pas dans le PDF ; que le nom de fichier garde les
lettres arabes ; pour la recette, la liste de courses et le livre de
recettes. Un PDF en français reste en Helvetica, aligné à gauche, sans
télécharger la police ; une recette au nom arabe exportée en français
utilise la police arabe mais reste alignée à gauche.
"""
import http.server
import re
import socket
import sys
import threading
import unicodedata

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"
FONT_URL = "lib/fonts/noto-sans-arabic"
PRESENTATION = re.compile(r"[ﭐ-﷿ﹰ-﻿]")


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


def glyph_map(pdf):
    """Code de glyphe -> caractère, d'après les tables ToUnicode."""
    m = {}
    for block in re.findall(r"beginbfchar(.*?)endbfchar", pdf, re.S):
        for code, uni in re.findall(r"<([0-9a-fA-F]+)><([0-9a-fA-F]{4})>", block):
            m[int(code, 16)] = chr(int(uni, 16))
    return m


def read_visual(visual, pdf):
    """Lignes écrites en police arabe (codes de glyphes), dans l'ordre
    visuel de gauche à droite."""
    m = glyph_map(pdf)
    return ["".join(m.get(int(v[i:i + 4], 16), "?") for i in range(0, len(v), 4))
            for v in visual if re.fullmatch(r"(?:[0-9a-f]{4})+", v or "")]


def read_rtl(visual, pdf):
    """Mêmes lignes lues de droite à gauche, formes liées ramenées aux
    lettres de base."""
    return [unicodedata.normalize("NFKC", g[::-1]) for g in read_visual(visual, pdf)]


def base_letters(chars):
    """Formes de présentation ramenées aux lettres de base (NFKC)."""
    return set("".join(unicodedata.normalize("NFKC", c) for c in chars))


EXPORT_JS = """async ([lang, kind]) => {
    await ensureUiTranslationsLoaded(lang);
    await ensureIngredientTranslationsLoaded(lang);
    setLang(lang);
    await loadJsPdfLib();
    let out = null, name = null;
    window.jspdf.jsPDF.API.save = function (n) { name = n; out = this.output(); };
    const ar = {id: 'a1', name: 'شكشوكة بالطماطم', category: 'Plat', defaultPersons: 2, prepTime: 10, cookTime: 15,
        difficulty: 'Facile', createdAt: '2026-01-01', allergens: ['Œufs'],
        description: 'يُقطّع البصل والفلفل ويُقلى في زيت الزيتون، ثم تُضاف الطماطم والتوابل وتُطهى على نار هادئة حتى تتكاثف الصلصة. تُكسر البيضات فوقها وتُغطّى المقلاة حتى ينضج البياض. هذه فقرة طويلة للتحقق من أن النص العربي يُقسَّم على عدة أسطر دون أن يتجاوز هوامش الصفحة.',
        ingredients: [{name: 'Tomate', quantity: 2, unit: 'pièce'}, {name: 'Beurre', quantity: 12.5, unit: 'g'}]};
    const fr = {id: 'f1', name: 'Tarte aux pommes', category: 'Dessert', defaultPersons: 4, prepTime: 20, cookTime: 30,
        difficulty: 'Facile', createdAt: '2026-01-01', allergens: [], description: 'Étaler la pâte.',
        ingredients: [{name: 'Pomme', quantity: 4, unit: 'pièce'}]};
    // Texte final dans l'ordre visuel (après le passage de droite à
    // gauche de jsPDF) : crochet ajouté après le sien.
    window.__visual = [];
    // Relevé de chaque ligne écrite : position, alignement, largeur.
    const calls = [];
    const Orig = window.jspdf.jsPDF;
    window.jspdf.jsPDF = function (...args) {
        const doc = new Orig(...args);
        const origText = doc.text;
        doc.internal.events.subscribe('postProcessText', (e) => {
            [].concat(e.text).forEach((x) => window.__visual.push(Array.isArray(x) ? x[0] : x));
        });
        doc.text = function (txt, x, y, opts) {
            if (typeof txt === 'string') calls.push({ txt, x, align: (opts && opts.align) || 'left', w: doc.getTextWidth(txt) });
            return origText.call(doc, txt, x, y, opts);
        };
        return doc;
    };
    if (kind === 'recipe') await exportRecipePdf(ar, 2);
    else if (kind === 'recipeFr') await exportRecipePdf(fr, 4);
    else if (kind === 'shopping') {
        state.shopping = [{name: 'Tomate', quantity: 3, unit: 'pièce', checked: false, rayon: 'Fruits et légumes'},
                          {name: 'Beurre', quantity: 250, unit: 'g', checked: true, rayon: 'Crèmerie'}];
        await exportShoppingListPdf();
    } else if (kind === 'cookbook') await exportCookbookPdf([ar], false);
    window.jspdf.jsPDF = Orig;
    return {name, out, calls, visual: window.__visual};
}"""


def main():
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {label}{' — ' + str(detail) if detail != '' else ''}")

    def layout_rtl(calls):
        """Lignes hors numéro de page : alignées à droite, dans les marges 20–190 mm."""
        bad = [c for c in calls if not re.fullmatch(r"\d+", c["txt"])
               and (c["align"] != "right" or c["x"] > 190.01 or c["x"] - c["w"] < 19.99)]
        return bad

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
        check("français : Helvetica seule, pas de police arabe", "NotoSansArabic" not in pdf)
        check("français : police arabe non téléchargée", not font_requests, font_requests)
        check("français : lignes alignées à gauche", all(c["align"] == "left" for c in r["calls"]))

        r = page.evaluate(EXPORT_JS, ["fr", "recipe"])
        pdf = r["out"] or ""
        check("recette au nom arabe exportée en français : police arabe", "/BaseFont /NotoSansArabic" in pdf)
        check("… lettres liées présentes et mise en page restée à gauche",
              PRESENTATION.search("".join(unicode_chars(pdf))) and all(c["align"] == "left" for c in r["calls"]))

        r = page.evaluate(EXPORT_JS, ["ar", "recipe"])
        pdf = r["out"] or ""
        chars = unicode_chars(pdf)
        letters = base_letters(chars)
        check("recette : police Noto Sans Arabic intégrée, normale et grasse",
              "/BaseFont /NotoSansArabic" in pdf and len(re.findall(r"/FontFile2", pdf)) == 2, len(re.findall(r"/FontFile2", pdf)))
        check("recette : lettres liées (formes de présentation arabes)", len([c for c in chars if PRESENTATION.match(c)]) >= 20,
              len([c for c in chars if PRESENTATION.match(c)]))
        check("recette : ligature « لا » utilisée", any(0xFEF5 <= ord(c) <= 0xFEFC for c in chars))
        check("recette : titre, ingrédients traduits (طماطم, زبدة), libellés en arabe",
              set("شكشوةبالطمزد") <= letters, "".join(sorted(c for c in letters if "؀" <= c <= "ۿ")))
        check("recette : quantité 12.5 x2 = 25 en chiffres occidentaux", any("25" in c["txt"] for c in r["calls"]))
        check("recette : aucun caractère d'isolation (FSI…PDI) dans le PDF",
              not any(re.search(r"[⁦-⁩‎‏؜]", c["txt"]) for c in r["calls"]))
        bad = layout_rtl(r["calls"])
        check("recette : chaque ligne alignée à droite, dans les marges", not bad, bad[:3])
        long_lines = [c for c in r["calls"] if "الصفحة" in c["txt"] or "تتكاثف" in c["txt"]]
        check("recette : long paragraphe découpé en plusieurs lignes", len([c for c in r["calls"] if c["w"] > 100]) >= 2,
              len(long_lines))
        # Ordre de lecture : texte visuel lu de droite à gauche = ordre logique
        # (une ligne traitée de gauche à droite mettait « - 4 » à gauche).
        rtl_read = read_rtl(r["visual"], pdf)
        tomato = "-  4 " + page.evaluate("() => `${translateUnit('pièce')} ${translateIngredientName('Tomate')}`")
        check("recette : ligne d'ingrédient lue de droite à gauche (« - 4 قطعة طماطم »)", tomato in rtl_read,
              [x for x in rtl_read if "4" in x][:3])
        check("recette : titre lu de droite à gauche", "شكشوكة بالطماطم" in rtl_read)
        check("recette : nom de fichier arabe conservé", r["name"] == "شكشوكة بالطماطم.pdf", r["name"])
        size = len(pdf.encode("latin-1", "replace"))
        check("recette : PDF de taille raisonnable (< 200 Ko)", size < 200_000, size)

        r = page.evaluate(EXPORT_JS, ["ar", "shopping"])
        pdf = r["out"] or ""
        check("liste de courses : police arabe et noms traduits (طماطم, زبدة)",
              "/BaseFont /NotoSansArabic" in pdf and set("طمزبد") <= base_letters(unicode_chars(pdf)))
        bad = layout_rtl(r["calls"])
        check("liste de courses : alignée à droite", not bad, bad[:3])
        rtl_read = read_rtl(r["visual"], pdf)
        box = [c for c in r["calls"] if c["txt"] == "[x]"]
        check("liste de courses : case à cocher écrite à part, au début (à droite)",
              box and abs(box[0]["x"] - 190) < 0.01 and box[0]["align"] == "right"
              and not any("[" in x and re.search(r"[\u0600-\u06ff]", x) for x in rtl_read), rtl_read[:4])
        check("liste de courses : crochets de la case non retournés (« [x] » vu de gauche à droite)",
              "[x]" in read_visual(r["visual"], pdf), read_visual(r["visual"], pdf)[:4])

        r = page.evaluate(EXPORT_JS, ["ar", "cookbook"])
        pdf = r["out"] or ""
        check("livre de recettes : police arabe et texte arabe",
              "/BaseFont /NotoSansArabic" in pdf and set("شكو") <= base_letters(unicode_chars(pdf)))
        bad = layout_rtl(r["calls"])
        check("livre de recettes : aligné à droite", not bad, bad[:3])
        nums = [c for c in r["calls"] if re.fullmatch(r"\d+", c["txt"])]
        check("livre de recettes : numéro de page du sommaire à gauche (en miroir)",
              nums and all(c["align"] == "left" and abs(c["x"] - 20) < 0.01 for c in nums), nums)
        check("polices téléchargées une seule fois puis réutilisées (normale + grasse)", len(font_requests) == 2, font_requests)

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
