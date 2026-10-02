"""
Reconnaissance des unités dans les 9 langues de l'application
(parseIngredientString dans app.js), utilisée par l'import de recette par
photo (OCR) et par lien.

Vérifie :
1. Les unités courantes du portugais, de l'italien, du suédois, du
   norvégien, de l'indonésien (et les manques comblés en espagnol,
   allemand et catalan) : cuillères, dl/krm, gousses, tranches, pièces,
   contenants, "colher de sopa/chá" en plusieurs mots.
2. Les lettres accentuées scandinaves/portugaises ne coupent plus un mot
   ("2 smør" donnait "sm ør").
3. Le nom est repris tel quel quand le mot n'est pas une unité (plus
   d'espace avant une virgule, point d'abréviation conservé).
4. Pièges : nom composé avec tiret ("2 pot-au-feu", "St-Amand"),
   "fette biscottate" (produit), "buah naga" (fruit du dragon) ne sont
   pas découpés à tort.
5. Non-régression français/anglais/espagnol/allemand.
"""
import http.server
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

PROJECT_ROOT = "/home/user/mes-recettes-mobile"

CASES = [
    # (texte, quantité, unité, nom)
    ("2 msk olivolja", 2, "c. à soupe", "olivolja"),
    ("1 tsk salt", 1, "c. à café", "salt"),
    ("1 dl grädde", 10, "cl", "grädde"),
    ("1 krm salt", 0.1, "cl", "salt"),
    ("1 klyfta vitlök", 1, "gousse", "vitlök"),
    ("4 skivor bröd", 4, "tranche", "bröd"),
    ("1 burk krossade tomater", 1, "boîte", "krossade tomater"),
    ("1 påse jäst", 1, "boîte", "jäst"),
    ("2 st ägg", 2, "pièce", "ägg"),
    ("2 ss smør", 2, "c. à soupe", "smør"),
    ("1 ts salt", 1, "c. à café", "salt"),
    ("2 fedd hvitløk", 2, "gousse", "hvitløk"),
    ("1 boks tomater", 1, "boîte", "tomater"),
    ("3 stk egg", 3, "pièce", "egg"),
    ("3 colheres de sopa de azeite", 3, "c. à soupe", "azeite"),
    ("2 colher de chá de sal", 2, "c. à café", "sal"),
    ("2 c. de sopa de açúcar", 2, "c. à soupe", "açúcar"),
    ("2 dentes de alho", 2, "gousse", "alho"),
    ("2 fatias de pão", 2, "tranche", "pão"),
    ("1 xícara de farinha", 24, "cl", "farinha"),
    ("1 pacote de natas", 1, "boîte", "natas"),
    ("2 cucchiai di olio", 2, "c. à soupe", "olio"),
    ("1 cucchiaino di sale", 1, "c. à café", "sale"),
    ("2 spicchi d'aglio", 2, "gousse", "aglio"),
    ("2 fette di pane", 2, "tranche", "pane"),
    ("1 vasetto di yogurt", 1, "boîte", "yogurt"),
    ("2 sdm minyak", 2, "c. à soupe", "minyak"),
    ("1 sdt garam", 1, "c. à café", "garam"),
    ("3 siung bawang putih", 3, "gousse", "bawang putih"),
    ("1 kaleng susu", 1, "boîte", "susu"),
    ("1 bungkus mie", 1, "boîte", "mie"),
    ("1 cucharadita de sal", 1, "c. à café", "sal"),
    ("2 dientes de ajo", 2, "gousse", "ajo"),
    ("1 Zehe Knoblauch", 1, "gousse", "Knoblauch"),
    ("2 Scheiben Brot", 2, "tranche", "Brot"),
    ("1 cullerada d'oli", 1, "c. à soupe", "oli"),
    # Lettres accentuées et reconstruction du nom
    ("2 smør", 2, "pièce", "smør"),
    ("2 äpplen", 2, "pièce", "äpplen"),
    ("2 oignons, émincés", 2, "pièce", "oignons, émincés"),
    # Pièges
    ("2 pot-au-feu", 2, "pièce", "pot-au-feu"),
    ("1 St-Amand", 1, "pièce", "St-Amand"),
    ("2 dente-de-leão", 2, "pièce", "dente-de-leão"),
    ("4 fette biscottate", 4, "pièce", "fette biscottate"),
    ("1 buah naga", 1, "pièce", "buah naga"),
    # Non-régression
    ("500 g farine", 500, "g", "farine"),
    ("2 c. à soupe d'huile", 2, "c. à soupe", "huile"),
    ("1 tbsp oil", 1, "c. à soupe", "oil"),
    ("2 EL Öl", 2, "c. à soupe", "Öl"),
    ("200 ml lait", 20, "cl", "lait"),
    ("1 lata de atum", 1, "boîte", "atum"),
    ("2 gousses d'ail", 2, "gousse", "ail"),
    ("1 pot de crème", 1, "boîte", "crème"),
    ("Persil 1/2 bouquet", 0.5, "pièce", "Persil"),
    ("Beurre : 40.0 Gr", 40, "g", "Beurre"),
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
    port = find_free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    all_ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(f"http://127.0.0.1:{port}/index.html", timeout=15000)
        page.evaluate("() => appReady")
        results = page.evaluate(
            "(cases) => cases.map((c) => { const r = parseIngredientString(c[0]); return [r.quantity, r.unit, r.name]; })",
            CASES,
        )
        for (text, qty, unit, name), (rq, ru, rn) in zip(CASES, results):
            ok = rq == qty and ru == unit and rn == name
            print(f"{'✅ OK' if ok else '❌ ÉCHEC'}  {text!r} -> {rq} {ru} {rn!r}" + ("" if ok else f" (attendu {qty} {unit} {name!r})"))
            all_ok = all_ok and ok
        if errors:
            print("❌ ÉCHEC  erreurs JS :", "; ".join(errors))
            all_ok = False
        browser.close()
    httpd.shutdown()
    print("\n=== Résumé ===")
    print("TOUT CORRECT" if all_ok else "ÉCHECS DÉTECTÉS")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
